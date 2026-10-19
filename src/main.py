"""
น้องซีที — LINE Messaging API Webhook
รับข้อความจาก LINE → ส่งให้น้องซีทีตอบ → ส่งกลับไป LINE

รัน:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

ทดสอบ:
    1. เปิด ngrok: ngrok http 8000
    2. ก๊อปปี้ HTTPS URL ไปใส่ใน LINE Developer Console
       - Messaging API → Webhook URL
       - URL ที่ใส่: https://xxx.ngrok-free.app/callback
    3. เปิดใช้ Use webhook
    4. แอด Bot เป็นเพื่อนใน LINE → ลองคุย!
"""

import re
import logging
import httpx
import asyncio

from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, PlainTextResponse

from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    QuickReply,        
    QuickReplyItem,    
    MessageAction,     
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

from src.config import (
    LINE_CHANNEL_SECRET,
    LINE_CHANNEL_ACCESS_TOKEN,
    APP_NAME,
    APP_ENV,
    N8N_WEBHOOK_LOG,
)
from src.quick_replies import quick_reply_for
from src.chat import answer, NO_ANSWER
from src.normalizer import normalize_query
from src.retriever import is_specific_unit, format_instructor

from src.database import sqlite_db
from src.database.rules import (
    is_loan_query,
    get_loan_redirect_template,
    is_calendar_query,
    get_calendar_redirect_template,
)
from src.database.memory import init_memory, prune, get_history, add_message
from src.database.chat_log import init_chat_log, log_chat

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info(f" {APP_NAME} เริ่มทำงานแล้ว")
    logger.info(f" Environment: {APP_ENV}")
    logger.info(f" LINE Secret: {'✅' if LINE_CHANNEL_SECRET else '❌'}")
    logger.info(f" LINE Token:  {'✅' if LINE_CHANNEL_ACCESS_TOKEN else '❌'}")
    logger.info("=" * 60)

    init_memory()  
    init_chat_log()
    deleted = prune()  
    logger.info(f" prune ประวัติเก่า: ลบ {deleted} แถว")

    try:
        from src.database import vector_db

        count = vector_db.count_documents()
        logger.info(f" Knowledge base: {count} chunks พร้อม")
    except Exception as e:
        logger.error(f"  ไม่สามารถโหลด vector DB: {e}")

    yield
    logger.info(" น้องซีทีปิดบริการ")

app = FastAPI(
    title=APP_NAME,
    description="LINE Chatbot สำหรับนิสิต CSIT — ม.นเรศวร",
    version="1.0.0",
    lifespan=lifespan,
)

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    logger.warning("  LINE credentials ไม่ครบใน .env — webhook จะไม่ทำงาน")

line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN or "")
parser = WebhookParser(LINE_CHANNEL_SECRET or "")

CONTACT_KEYWORDS = [
    "ติดต่อ",
    "เบอร์โทร",
    "โทรศัพท์",
    "เจ้าหน้าที่",
    "พี่เฟิร์น",
    "พี่แมว",
    "พี่โอ๊ต",
    "พี่ยุทธ",
]

LIST_ALL_KEYWORDS = [
    "ทั้งหมด", "ทุกคน", "ทุกท่าน", "รายชื่อ",
    "มีใครบ้าง", "มีอะไรบ้าง", "ทุกอัน", "ทุกรายการ",
]
GREETING_KEYWORDS = [
    "สวัสดี", "หวัดดี", "ดีครับ", "ดีค่ะ", "ดีคับ", "ดีจ้า",
    "hello", "hi", "hey", "ทักทาย", "ว่าไง",
]

GREETING_RESPONSE = (
    "สวัสดีค่ะ 😊 น้องซีทีเป็นผู้ช่วยตอบคำถามของภาควิชา CSIT ม.นเรศวรค่ะ\n"
    "ถามได้เลยนะคะ เช่น เรื่องการลงทะเบียน เกียรตินิยม ค่าปรับ "
    "หรือเลือกจากเมนูด้านล่างก็ได้ค่ะ"
)


def _is_greeting(text: str) -> bool:
    """ข้อความสั้น ๆ ที่เป็นคำทักทายล้วน ๆ (จำกัดความยาวกัน false positive)"""
    t = text.strip().lower()
    if not t or len(t) > 20:
        return False
    return any(kw in t for kw in GREETING_KEYWORDS)

def _wants_list_all(text: str) -> bool:
    return any(kw in text for kw in LIST_ALL_KEYWORDS)

def _form_no(code: str) -> int:
    m = re.search(r"(\d+)", code or "")
    return int(m.group(1)) if m else 9999

INSTRUCTOR_PATTERNS = [
    r"อาจารย์([ก-๙a-zA-Z\s]+)",
    r"อาจาร([ก-๙a-zA-Z\s]+)",
    r"จาร([ก-๙a-zA-Z\s]+)",
    r"ผศ\.?\s*ดร\.?\s*([ก-๙]+)",
    r"รศ\.?\s*ดร\.?\s*([ก-๙]+)",
    r"อ\.\s*([ก-๙]+)",
]


async def send_log_to_n8n(
    user_id: str, question: str, answer_text: str, route: str, answered: bool
):
    if not N8N_WEBHOOK_LOG:
        return
    from datetime import datetime

    payload = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "question": question,
        "answer": answer_text,
        "route": route,
        "answered": answered,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(N8N_WEBHOOK_LOG, json=payload)
    except Exception as e:
        logger.warning(f"[n8n] ส่ง log ไม่สำเร็จ: {e}")

_TEACHER_PREFIX = re.compile(r"(?:อาจารย์|อาจาร|จารย์|จาร|อ\.|ผศ|รศ|ดร|ที่ปรึกษา)")

_NAME_BOUNDARY = (
    r"(?:\s|$|อยู่|ห้อง|สอน|อีเมล|เมล|เบอร์|โทร|ใคร|เป็น|"
    r"ที่ปรึกษา|ค่ะ|ครับ|คับ)"
)


def _match_instructor_by_name(normalized: str):
    instructors = sqlite_db.list_instructors()
    if not instructors:
        return None

    m = _TEACHER_PREFIX.search(normalized)
    if m:
        rest = normalized[m.end():].lstrip(" .")  
        best = None
        for inst in instructors:
            first = (inst.get("name") or "").split()[0]
            if len(first) >= 2 and rest.startswith(first):
                if best is None or len(first) > len(best[0]):
                    best = (first, inst)
        if best:
            return best[1]
 
    best = None
    for inst in instructors:
        first = (inst.get("name") or "").split()[0]
        if len(first) < 3:
            continue
        if re.search(re.escape(first) + _NAME_BOUNDARY, normalized):
            if best is None or len(first) > len(best[0]):
                best = (first, inst)
    return best[1] if best else None

_EDUCATION_INTENT_KEYWORDS = [
    "จบจาก", "จบการศึกษา", "เรียนจบ", "สำเร็จการศึกษา",
    "วุฒิ", "วุฒิการศึกษา", "ปริญญา", "จบป.", "จบ",
]
_ROOM_INTENT_KEYWORDS = ["ห้อง", "อยู่ห้องไหน", "ห้องทำงาน", "ห้องไหน", "นั่งอยู่ไหน"]
_EMAIL_INTENT_KEYWORDS = ["อีเมล", "เมล", "email", "ติดต่อทางเมล"]


def _instructor_intent_fields(normalized: str) -> set:
    wants = set()
    if any(kw in normalized for kw in _EDUCATION_INTENT_KEYWORDS):
        wants.add("education")
    if any(kw in normalized for kw in _ROOM_INTENT_KEYWORDS):
        wants.add("office")
    if any(kw in normalized for kw in _EMAIL_INTENT_KEYWORDS):
        wants.add("email")
    return wants


def _attach_quick_reply(messages: list, route: str | None) -> None:
    if not messages or route is None:
        return
    qr = quick_reply_for(route)
    if not qr:
        return
    items = [
        QuickReplyItem(
            action=MessageAction(label=i["action"]["label"], text=i["action"]["text"])
        )
        for i in qr["items"]
    ]
    first = messages[0]
    if isinstance(first, TextMessage):
        messages[0] = TextMessage(text=first.text, quick_reply=QuickReply(items=items))


def route_message(user_message: str, history: Optional[list] = None):
    
    history = history or []
    normalized = normalize_query(user_message)

    if _is_greeting(user_message):
        logger.info(" Route: greeting")
        return [TextMessage(text=GREETING_RESPONSE)], "greeting", True
    if is_loan_query(normalized):
        logger.info(" Route: loan_text")
        template = get_loan_redirect_template()
        return [TextMessage(text=template)], "loan_redirect", True

    if is_calendar_query(normalized):
        logger.info(" Route: calendar_redirect")
        return (
            [TextMessage(text=get_calendar_redirect_template())],
            "calendar_redirect",
            True,
        )
    
    if (("คำร้อง" in normalized) or ("form" in normalized.lower())
            or ("แบบฟอร์ม" in normalized)) and _wants_list_all(normalized):
        forms = sqlite_db.list_forms()
        if forms:
            logger.info(" Route: nuform_list_all")
            forms = sorted(forms, key=lambda f: _form_no(f["code"]))
            lines = [f" รายการคำร้อง NU Forms ({len(forms)} รายการ)\n"]
            for f in forms:
                lines.append(f"• {f['code']} — {f['name_th']}")
            text = "\n".join(lines)
            if len(text) > 4900:
                text = text[:4900] + "..."
            return [TextMessage(text=text)], "nuform_list", True
        
    if ("อาจาร" in normalized) and _wants_list_all(normalized):
        instructors = sqlite_db.list_instructors()
        if instructors:
            logger.info(" Route: instructor_list_all")
            lines = [f" รายชื่ออาจารย์ภาควิชา CSIT ({len(instructors)} คน)\n"]
            for inst in instructors:
                lines.append(
                    f"• {inst['title_short']} {inst['name']}\n"
                    f"   {inst.get('office') or '-'}   {inst.get('email') or '-'}"
                )
            text = "\n".join(lines)
            if len(text) > 4900:
                text = text[:4900] + "..."
            return [TextMessage(text=text)], "instructor_list", True

    inst = _match_instructor_by_name(normalized)
    if inst:
        logger.info(f" Route: instructor_text ({inst['name']})")
        wants = _instructor_intent_fields(normalized)
        text = "👨‍🏫 " + format_instructor(inst, fields=wants or None)
        return [TextMessage(text=text)], "instructor", True

    if any(kw in user_message for kw in CONTACT_KEYWORDS) and not is_specific_unit(normalized):
        logger.info(" Route: contact_text")
        return (
            [
                TextMessage(
                    text=(
                        "📞 ติดต่อภาควิชา CSIT\n"
                        "👩‍💼 พี่เฟิร์น: 055-963262\n"
                        "📧 nutthapakornm@nu.ac.th\n"
                        "🏢 คณะวิทยาศาสตร์ อาคาร SC2\n"
                        "🌐 https://csit.nu.ac.th\n"
                        "📘 https://www.facebook.com/share/1N5QSZJYBn/?mibextid=wwXIfr"
                    )
                )
            ],
            "contact",
            True,
        )

    response = answer(user_message, verbose=False, history=history)

    if response == NO_ANSWER or not response or not response.strip():
        logger.info(" Route: no_context_text")
        return (
            [
                TextMessage(
                    text=(
                        "ขออภัยค่ะ น้องซีทียังไม่มีข้อมูลในเรื่องนี้ 😅\n"
                        "ติดต่อภาควิชาได้เลยนะคะ\n"
                        "📞 055-963262, 055-963263"
                    )
                )
            ],
            "RAG",
            False,
        )

    if len(response) > 4900:
        response = response[:4900] + "...\n\n📞 ติดต่อเพิ่มเติม: 055-963262"

    return [TextMessage(text=response)], "RAG", True


@app.get("/")
def root():
    return JSONResponse(
        content={
            "name": "nong-csit-chatbot",
            "status": "ok",
            "env": "development",
            "message": "น้องซีที พร้อมให้บริการแล้วค่ะ",
            "endpoints": {
                "/": "Health check (this page)",
                "/health": "JSON health check",
                "/callback": "LINE Webhook (POST)",
            },
        },
        media_type="application/json; charset=utf-8",
    )


@app.get("/health")
async def health():
    """Simple health check สำหรับ monitoring"""
    return {"status": "healthy", "service": APP_NAME}


@app.post("/callback")
async def line_webhook(
    request: Request,
    x_line_signature: Optional[str] = Header(None),
):

    body = await request.body()
    body_text = body.decode("utf-8")
    logger.info(f" รับ webhook จาก LINE ({len(body_text)} bytes)")

    if not x_line_signature:
        logger.error(" ไม่มี X-Line-Signature header")
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        events = parser.parse(body_text, x_line_signature)
    except InvalidSignatureError:
        logger.error(" Signature ไม่ valid")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f" Parse error: {e}")
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    with ApiClient(line_config) as api_client:
        line_bot_api = MessagingApi(api_client)

        for event in events:
            if not isinstance(event, MessageEvent):
                continue
            if not isinstance(event.message, TextMessageContent):
                continue

            user_id = event.source.user_id if event.source else "unknown"
            user_message = event.message.text
            reply_token = event.reply_token

            logger.info(f" User {user_id[:8]}...: {user_message[:50]}")

            history = get_history(user_id)

            try:
                messages, route, answered = route_message(user_message, history=history)

                if answered:
                    _attach_quick_reply(messages, route)

                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=messages,
                    )
                )

                reply_text = (
                    messages[0].text if hasattr(messages[0], "text") else "[flex]"
                )

                log_chat(user_id, user_message, reply_text, route, answered)

                asyncio.create_task(
                    send_log_to_n8n(
                        user_id=user_id,
                        question=user_message,
                        answer_text=reply_text,
                        route=route,
                        answered=answered,
                    )
                )

                add_message(user_id, "user", user_message)
                add_message(user_id, "assistant", reply_text[:500])

                logger.info(f" ส่งกลับ {len(messages)} message(s)")

            except Exception as e:
                logger.exception(f" Error ตอนตอบ: {e}")

                log_chat(user_id, user_message, "", "error", False)

                asyncio.create_task(
                    send_log_to_n8n(
                        user_id=user_id,
                        question=user_message,
                        answer_text="",
                        route="error",
                        answered=False,
                    )
                )

                try:
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[
                                TextMessage(
                                    text=(
                                        "ขออภัยค่ะ น้องซีทีมีปัญหานิดหน่อย 🥺\n"
                                        "ลองถามใหม่อีกครั้งนะคะ\n"
                                        "📞 055-963262, 055-963263"
                                    )
                                )
                            ],
                        )
                    )
                except Exception:
                    pass

    return PlainTextResponse("OK", status_code=200)
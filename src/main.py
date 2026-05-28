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
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, PlainTextResponse

from linebot.v3 import WebhookParser
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

from src.config import (
    LINE_CHANNEL_SECRET,
    LINE_CHANNEL_ACCESS_TOKEN,
    APP_NAME,
    APP_ENV,
)
from src.chat import answer
from src.normalizer import normalize_query
from collections import defaultdict, deque

# เพิ่มตรงนี้
from src.database import sqlite_db
from src.database.rules import is_loan_query, get_loan_redirect_template

# เก็บ history แยกตาม user_id
# deque(maxlen=6) = จำแค่ 3 คู่ถาม-ตอบล่าสุด
_conversation_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=6))

# ─── Logging ──────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─── FastAPI App ──────────────────────────────────
app = FastAPI(
    title=APP_NAME,
    description="LINE Chatbot สำหรับนิสิต CSIT — ม.นเรศวร",
    version="1.0.0",
)


# ─── LINE Config ──────────────────────────────────
if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    logger.warning("⚠️  LINE credentials ไม่ครบใน .env — webhook จะไม่ทำงาน")

line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN or "")
parser = WebhookParser(LINE_CHANNEL_SECRET or "")


# ─── Keywords ─────────────────────────────────────
CONTACT_KEYWORDS = [
    "ติดต่อ", "เบอร์โทร", "โทรศัพท์", "เจ้าหน้าที่",
    "พี่เฟิร์น", "พี่แมว", "พี่โอ๊ต", "พี่ยุทธ",
    "ภาควิชา", "office",
]

INSTRUCTOR_PATTERNS = [
    r"อาจารย์([ก-๙a-zA-Z\s]+)",
    r"อาจาร([ก-๙a-zA-Z\s]+)",
    r"ผศ\.?\s*ดร\.?\s*([ก-๙]+)",
    r"รศ\.?\s*ดร\.?\s*([ก-๙]+)",
    r"อ\.\s*([ก-๙]+)",
]


# ═══════════════════════════════════════════════════
# Message Router
# ═══════════════════════════════════════════════════

def route_message(user_message: str, history: list = []):
    """
    วิเคราะห์ข้อความและเลือก response ที่เหมาะสม

    คืนค่า: list ของ message objects (TextMessage)
    """
    normalized = normalize_query(user_message)

    # ── 1. กยศ. → Flex card ──────────────────────
    if is_loan_query(normalized):
        logger.info("🏦 Route: loan_text")
        template = get_loan_redirect_template()
        return [TextMessage(text=template)]

    # ── 2. ถามอาจารย์โดยตรง → Flex card ──────────
    for pattern in INSTRUCTOR_PATTERNS:
        m = re.search(pattern, normalized)
        if m:
            name = m.group(1).strip().split()[0]  # เอาแค่คำแรก
            if len(name) >= 2:
                inst = sqlite_db.find_instructor(name)
                if inst:
                    logger.info(f"👨‍🏫 Route: instructor_text ({name})")
                    text = (
                        f"👨‍🏫 {inst['title_short']} {inst['name']}\n"
                        f"🏢 ห้อง: {inst.get('office', '-')}\n"
                        f"📧 {inst.get('email', '-')}"
                    )
                    return [TextMessage(text=text)]
            break  # เจอ pattern แล้วแต่ไม่เจอในฐานข้อมูล → ไป RAG ต่อ

    # ── 3. ถามติดต่อภาควิชา → Flex card ──────────
    if any(kw in user_message for kw in CONTACT_KEYWORDS):
        logger.info("📞 Route: contact_text")
        return [TextMessage(text=(
            "📞 ติดต่อภาควิชา CSIT\n"
            "👩‍💼 พี่เฟิร์น: 055-963262\n"
            "📧 nutthapakornm@nu.ac.th\n"
            "🏢 คณะวิทยาศาสตร์ อาคาร SC2"
        ))]

    # ── 4. RAG + RAR ── ส่ง history เข้าไปด้วย
    response = answer(user_message, verbose=False, history=history)

    # ตัดความยาวถ้าเกิน LINE limit
    if len(response) > 4900:
        response = response[:4900] + "...\n\n📞 ติดต่อเพิ่มเติม: 055-963262"

    # ตอบไม่ได้ → Flex card แจ้งติดต่อ
    if not response or "ไม่มีข้อมูล" in response or len(response.strip()) == 0:
        logger.info("❓ Route: no_context_text")
        return [TextMessage(text=(
            "ขออภัยค่ะ น้องซีทียังไม่มีข้อมูลในเรื่องนี้ 😅\n"
            "ติดต่อภาควิชาได้เลยนะคะ\n"
            "📞 055-963262, 055-963263"
        ))]

    return [TextMessage(text=response)]


# ═══════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════

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
    """
    LINE Webhook Endpoint

    LINE Server จะ POST มาที่นี่ทุกครั้งที่มีข้อความใหม่
    1. Verify signature
    2. Parse events
    3. Route → ส่ง Flex หรือ Text กลับ
    """

    # ─── 1. รับ body ───
    body = await request.body()
    body_text = body.decode("utf-8")
    logger.info(f"📨 รับ webhook จาก LINE ({len(body_text)} bytes)")

    # ─── 2. Verify signature ───
    if not x_line_signature:
        logger.error("❌ ไม่มี X-Line-Signature header")
        raise HTTPException(status_code=400, detail="Missing signature")

    try:
        events = parser.parse(body_text, x_line_signature)
    except InvalidSignatureError:
        logger.error("❌ Signature ไม่ valid")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"❌ Parse error: {e}")
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    # ─── 3. Process events ───
    with ApiClient(line_config) as api_client:
        line_bot_api = MessagingApi(api_client)

        for event in events:
            if not isinstance(event, MessageEvent):
                continue
            if not isinstance(event.message, TextMessageContent):
                continue

            user_id     = event.source.user_id if event.source else "unknown"
            user_message = event.message.text
            reply_token  = event.reply_token

            logger.info(f"👤 User {user_id[:8]}...: {user_message[:50]}")

            # ดึง history ของ user คนนี้
            history = list(_conversation_history[user_id])

            try:
                messages = route_message(user_message, history=history)

                # ── ส่งกลับ LINE ── ← เพิ่มตรงนี้
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=messages,
                    )
                )
                # บันทึกลง history หลังตอบสำเร็จ
                reply_text = messages[0].text if hasattr(messages[0], "text") else "[flex]"
                _conversation_history[user_id].append({
                    "role": "user",
                    "content": user_message
                })
                _conversation_history[user_id].append({
                    "role": "assistant",
                    "content": reply_text[:200]
                })
                logger.info(f"✅ ส่งกลับ {len(messages)} message(s)")

            except Exception as e:
                logger.exception(f"❌ Error ตอนตอบ: {e}")

                # Fallback — ส่ง error message ธรรมดา
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

    # LINE ต้องการ 200 OK เสมอ
    return PlainTextResponse("OK", status_code=200)


# ─── Startup / Shutdown ──────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(f"🤖 {APP_NAME} เริ่มทำงานแล้ว")
    logger.info(f"🌍 Environment: {APP_ENV}")
    logger.info(f"🔑 LINE Secret: {'✅' if LINE_CHANNEL_SECRET else '❌'}")
    logger.info(f"🔑 LINE Token:  {'✅' if LINE_CHANNEL_ACCESS_TOKEN else '❌'}")
    logger.info("=" * 60)

    try:
        from src.database import vector_db
        count = vector_db.count_documents()
        logger.info(f"💾 Knowledge base: {count} chunks พร้อม")
    except Exception as e:
        logger.error(f"⚠️  ไม่สามารถโหลด vector DB: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("👋 น้องซีทีปิดบริการ")
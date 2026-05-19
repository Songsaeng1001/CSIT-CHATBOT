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
# ตรวจสอบว่ามี credentials
if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    logger.warning("⚠️  LINE credentials ไม่ครบใน .env — webhook จะไม่ทำงาน")

# LINE SDK clients
line_config = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN or "")
parser = WebhookParser(LINE_CHANNEL_SECRET or "")


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
                "/callback": "LINE Webhook (POST)"
            }
        },
        media_type="application/json; charset=utf-8"
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
    เราต้อง:
    1. Verify signature (ป้องกัน fake request)
    2. Parse events
    3. ตอบกลับ (reply) ผ่าน LINE API
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
            # สนใจเฉพาะ message event ที่เป็น text
            if not isinstance(event, MessageEvent):
                continue
            if not isinstance(event.message, TextMessageContent):
                continue
            
            user_message = event.message.text
            reply_token = event.reply_token
            user_id = event.source.user_id if event.source else "unknown"
            
            logger.info(f"👤 User {user_id[:8]}...: {user_message[:50]}")
            
            # ─── ตอบกลับ ───
            try:
                # เรียก RAG + RAR system
                reply_text = answer(user_message, verbose=False)
                
                # ตัดความยาวถ้าเกิน LINE limit (5000 chars)
                if len(reply_text) > 4900:
                    reply_text = reply_text[:4900] + "..."
                
                # ส่ง reply
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=reply_text)],
                    )
                )
                logger.info(f"💬 ตอบ: {reply_text[:80]}...")
                
            except Exception as e:
                logger.exception(f"❌ Error ตอนตอบ: {e}")
                
                # ส่งข้อความ error สวยๆ
                try:
                    error_msg = (
                        "ขออภัยค่ะ น้องซีทีมีปัญหานิดหน่อย 🥺\n"
                        "ลองถามใหม่อีกครั้งนะคะ หรือติดต่อภาควิชา\n"
                        "📞 055-963262, 055-963263"
                    )
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=reply_token,
                            messages=[TextMessage(text=error_msg)],
                        )
                    )
                except Exception:
                    pass  # ถ้าส่ง error message ไม่ได้ก็ปล่อย
    
    # ─── LINE ต้องการ 200 OK ───
    return PlainTextResponse("OK", status_code=200)


# ─── Startup event ───────────────────────────────
@app.on_event("startup")
async def startup_event():
    """ทำตอนเริ่ม server"""
    logger.info("=" * 60)
    logger.info(f"🤖 {APP_NAME} เริ่มทำงานแล้ว")
    logger.info(f"🌍 Environment: {APP_ENV}")
    logger.info(f"🔑 LINE Secret: {'✅' if LINE_CHANNEL_SECRET else '❌'}")
    logger.info(f"🔑 LINE Token:  {'✅' if LINE_CHANNEL_ACCESS_TOKEN else '❌'}")
    logger.info("=" * 60)
    
    # Warm-up: โหลด vector DB ไว้ล่วงหน้า
    try:
        from src.database import vector_db
        count = vector_db.count_documents()
        logger.info(f"💾 Knowledge base: {count} chunks พร้อม")
    except Exception as e:
        logger.error(f"⚠️  ไม่สามารถโหลด vector DB: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """ทำตอนปิด server"""
    logger.info("👋 น้องซีทีปิดบริการ")
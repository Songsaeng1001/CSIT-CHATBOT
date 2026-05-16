"""
FastAPI Server + LINE Webhook Handler
จุดเริ่มของระบบ Chatbot

รัน:
    uvicorn src.main:app --reload --port 8000
"""

from fastapi import FastAPI
from src.config import APP_NAME, APP_ENV

app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    description="LINE Chatbot สำหรับนิสิต CSIT ม.นเรศวร"
)


@app.get("/")
def root():
    """หน้าหลัก"""
    return {
        "message": "น้องซีที is running 🤖",
        "status": "ok",
        "env": APP_ENV
    }


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# TODO เฟส 6: เพิ่ม LINE webhook
# @app.post("/webhook/line")
# async def line_webhook(...):
#     ...
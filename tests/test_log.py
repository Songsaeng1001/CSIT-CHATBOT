import asyncio
from src.main import send_log_to_n8n

asyncio.run(send_log_to_n8n(
    user_id="U-local-test",
    question="ขอเบอร์ติดต่อภาควิชา",
    answer="📞 พี่เฟิร์น: 055-963262",
    route="contact",
    answered=True,
))
print("ยิง log แล้ว — ไปเช็ค Google Sheet")
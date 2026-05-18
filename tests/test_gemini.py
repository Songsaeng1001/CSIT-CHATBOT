"""
ทดสอบเรียก Google Gemini API ครั้งแรก
รัน: python tests/test_gemini.py
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.config import GOOGLE_API_KEY


def test_basic_call():
    """ทดสอบเรียก LLM ตอบคำถามภาษาไทยง่ายๆ"""

    print("=" * 60)
    print("🤖 ทดสอบเรียก Gemini API")
    print("=" * 60)

    # เช็คว่ามี API key
    if not GOOGLE_API_KEY:
        print("❌ ไม่พบ GOOGLE_API_KEY ใน .env")
        return

    print(f"✅ API Key: {GOOGLE_API_KEY[:10]}...{GOOGLE_API_KEY[-4:]}")
    print()

    # สร้าง LLM client
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # โมเดล Gemini ฟรีที่ดี
        temperature=0.7,
        google_api_key=GOOGLE_API_KEY,
    )

    # ─── Test 1: คำถามง่ายๆ ───
    print("📝 Test 1: ทักทาย")
    print("-" * 60)
    question1 = "สวัสดีครับ คุณคือใคร แนะนำตัวหน่อย"
    print(f"❓ ถาม: {question1}")

    response1 = llm.invoke(question1)
    print(f"💬 ตอบ: {response1.content}")
    print()

    # ─── Test 2: คำถามเชิงเทคนิค ───
    print("📝 Test 2: คำถามเชิงเทคนิค")
    print("-" * 60)
    question2 = "RAG คืออะไร อธิบายสั้นๆ ใน 2 ประโยค"
    print(f"❓ ถาม: {question2}")

    response2 = llm.invoke(question2)
    print(f"💬 ตอบ: {response2.content}")
    print()

    # ─── Test 3: ใช้ System Prompt ───
    print("📝 Test 3: ใช้ System Prompt")
    print("-" * 60)

    messages = [
        SystemMessage(
            content=(
                "คุณคือ 'น้องซีที' ผู้ช่วย AI ของภาควิชาวิทยาการคอมพิวเตอร์ "
                "และเทคโนโลยีสารสนเทศ มหาวิทยาลัยนเรศวร "
                "ตอบคำถามด้วยภาษาไทยที่สุภาพ เป็นกันเอง และให้ข้อมูลที่ถูกต้อง"
            )
        ),
        HumanMessage(content="ทักทายและแนะนำตัวเองหน่อย"),
    ]

    response3 = llm.invoke(messages)
    print(f"💬 น้องซีที: {response3.content}")
    print()

    print("=" * 60)
    print("✨ ทดสอบเสร็จสมบูรณ์!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_call()
"""
ทดสอบเรียก Google Gemini API ครั้งแรก
"""

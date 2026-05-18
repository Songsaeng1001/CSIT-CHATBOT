"""
ทดสอบ RAG Pipeline เต็มรูปแบบ
ค้น chunks → ส่งให้ Gemini → ตอบ

รัน: python -m tests.test_rag
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import GOOGLE_API_KEY
from src.database import vector_db


# ─── System Prompt ของน้องซีที ──────────────────
SYSTEM_PROMPT = """คุณคือ 'น้องซีที' ผู้ช่วย AI ของภาควิชาวิทยาการคอมพิวเตอร์
และเทคโนโลยีสารสนเทศ คณะวิทยาศาสตร์ มหาวิทยาลัยนเรศวร

หน้าที่ของคุณ:
- ตอบคำถามเกี่ยวกับหลักสูตร อาจารย์ การลงทะเบียน กยศ. และข้อมูลภาควิชา
- ตอบเป็นภาษาไทยที่สุภาพ เป็นกันเอง ใช้คำลงท้ายว่า "ค่ะ"
- ตอบจาก context ที่ให้เท่านั้น อย่าเดา
- ถ้าไม่รู้ ให้บอกตรงๆ ว่าไม่มีข้อมูล และแนะนำให้ติดต่อภาควิชา
- ตอบสั้น กระชับ ตรงประเด็น
- ถ้ามีเบอร์โทร อีเมล หรือลิงก์ ให้แสดงด้วย
"""


def build_rag_prompt(question: str, context_chunks: list) -> list:
    """สร้าง prompt สำหรับ Gemini"""
    
    # รวม context จาก chunks
    context_text = "\n\n---\n\n".join([
        f"[จากไฟล์: {chunk.metadata.get('source', '?').split('/')[-1]}]\n{chunk.page_content}"
        for chunk in context_chunks
    ])
    
    user_message = f"""ข้อมูลอ้างอิงจากเอกสารภาควิชา:

{context_text}

---

คำถามจากนิสิต: {question}

กรุณาตอบโดยอ้างอิงจากข้อมูลข้างต้นเท่านั้น"""
    
    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]


def ask(question: str, k: int = 4, verbose: bool = True) -> str:
    """
    ถามคำถาม → ค้น → ตอบ
    
    Args:
        question: คำถามจากผู้ใช้
        k: จำนวน chunks ที่ใช้ (default 4)
        verbose: แสดงรายละเอียดการค้นหา
    
    Returns:
        คำตอบจาก Gemini
    """
    
    # ─── Step 1: Retrieval ───
    if verbose:
        print(f"\n❓ คำถาม: {question}")
        print("─" * 60)
        print("🔍 กำลังค้นหา context...")
    
    results = vector_db.search(question, k=k)
    chunks = [doc for doc, score in results]
    
    if verbose:
        print(f"   ✅ เจอ {len(chunks)} chunks ที่เกี่ยวข้อง:")
        for i, (doc, score) in enumerate(results, 1):
            from pathlib import Path
            filename = Path(doc.metadata.get("source", "?")).name
            print(f"      [{i}] {filename} (distance: {score:.3f})")
    
    # ─── Step 2: Generate ───
    if verbose:
        print("\n🤖 กำลังให้ Gemini สร้างคำตอบ...")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,  # ต่ำ = ตอบตรงไปตรงมา
        google_api_key=GOOGLE_API_KEY,
    )
    
    messages = build_rag_prompt(question, chunks)
    response = llm.invoke(messages)
    
    if verbose:
        print("\n💬 น้องซีที:")
        print(response.content)
    
    return response.content


# ─── คำถามทดสอบ ──────────────────────────────────
TEST_QUESTIONS = [
    "อาจารย์เกรียงศักดิ์ห้องอะไร อีเมลอะไร",
    "ลงทะเบียนเกิน 22 หน่วยกิตทำยังไง",
    "เกียรตินิยมอันดับ 1 ต้อง GPA เท่าไร",
    "ค่าปรับลงทะเบียนช้าวันละเท่าไร",
    "เบอร์โทรภาควิชา CSIT",
]


def main():
    print("=" * 60)
    print("🧪 ทดสอบ RAG Pipeline เต็มรูปแบบ")
    print("=" * 60)
    
    # เช็คว่ามี API key
    if not GOOGLE_API_KEY:
        print("❌ ไม่พบ GOOGLE_API_KEY ใน .env")
        return
    
    # เช็คว่ามีข้อมูลใน DB
    count = vector_db.count_documents()
    print(f"\n📊 จำนวน chunks ใน Chroma: {count}")
    
    if count == 0:
        print("❌ Chroma DB ว่างเปล่า — รัน python -m src.ingest ก่อน")
        return
    
    # ทดสอบทีละคำถาม
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n\n{'='*60}")
        print(f"📝 Test {i}/{len(TEST_QUESTIONS)}")
        print(f"{'='*60}")
        ask(question)
    
    print()
    print("=" * 60)
    print("✨ ทดสอบเสร็จสมบูรณ์!")
    print("=" * 60)


if __name__ == "__main__":
    main()
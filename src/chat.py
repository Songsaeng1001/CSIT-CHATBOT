"""
Interactive Chat กับน้องซีที
คุยต่อเนื่องใน terminal ได้

รัน: python -m src.chat
ออก: พิมพ์ 'quit', 'exit', หรือ 'q' หรือกด Ctrl+C
"""

from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import GOOGLE_API_KEY
from src.database import vector_db

# ─── System Prompt ─────────────────────────────────
SYSTEM_PROMPT = """คุณคือ 'น้องซีที' ผู้ช่วย AI ของภาควิชาวิทยาการคอมพิวเตอร์
และเทคโนโลยีสารสนเทศ คณะวิทยาศาสตร์ มหาวิทยาลัยนเรศวร

กฎการตอบ:
1. ตอบเป็นภาษาไทยที่สุภาพ เป็นกันเอง ใช้คำลงท้าย "ค่ะ"
2. ตอบจาก context ที่ให้เท่านั้น ห้ามเดา
3. ถ้าไม่มีข้อมูลใน context ให้บอกตรงๆ และแนะนำให้ติดต่อภาควิชา
4. ตอบสั้น กระชับ ตรงประเด็น (1-3 ประโยค)
5. ถ้ามีเบอร์โทร อีเมล หรือลิงก์ ให้แสดงด้วย
6. สามารถใช้ emoji ได้บ้างเพื่อความเป็นมิตร แต่อย่ามากเกินไป
"""


# ─── ตัวแปร global (cache) ─────────────────────────
_llm = None


def get_llm():
    """โหลด LLM แค่ครั้งเดียว"""
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=GOOGLE_API_KEY,
        )
    return _llm


def build_prompt(question: str, context_chunks: list) -> list:
    """สร้าง prompt จาก context"""

    # รวม context จาก chunks
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        filename = Path(chunk.metadata.get("source", "?")).name
        context_parts.append(f"[เอกสาร {i}: {filename}]\n{chunk.page_content}")

    context_text = "\n\n---\n\n".join(context_parts)

    user_message = f"""ข้อมูลอ้างอิงจากเอกสารภาควิชา:

{context_text}

---

คำถามจากนิสิต: {question}

กรุณาตอบโดยอ้างอิงจากข้อมูลข้างต้นเท่านั้น"""

    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]


def answer(question: str, verbose: bool = False) -> str:
    """
    ตอบคำถาม 1 ครั้ง — RAG flow

    Args:
        question: คำถามจากผู้ใช้
        verbose: แสดงรายละเอียดการค้นหา

    Returns:
        คำตอบจาก Gemini
    """
    # 1. Retrieval
    results = vector_db.search(question, k=4)
    chunks = [doc for doc, _ in results]

    if verbose:
        print(f"\n📚 พบ context {len(chunks)} เอกสาร:")
        for i, (doc, score) in enumerate(results, 1):
            filename = Path(doc.metadata.get("source", "?")).name
            print(f"   [{i}] {filename} (dist: {score:.3f})")

    # 2. Generation
    llm = get_llm()
    messages = build_prompt(question, chunks)
    response = llm.invoke(messages)

    return response.content


def print_welcome():
    """แสดงข้อความต้อนรับ"""
    print()
    print("=" * 60)
    print("🤖 น้องซีที — ผู้ช่วย AI ภาควิชา CSIT")
    print("=" * 60)
    print("💬 ทักทายและถามคำถามได้เลยค่ะ!")
    print()
    print("📝 คำสั่งพิเศษ:")
    print("   /verbose  - เปิด/ปิดแสดงรายละเอียดการค้นหา")
    print("   /clear    - เคลียร์หน้าจอ")
    print("   /help     - แสดงคำสั่งทั้งหมด")
    print("   quit, q   - ออกจากโปรแกรม")
    print("=" * 60)


def print_help():
    """แสดงคำสั่ง"""
    print("\n📖 คำสั่งที่ใช้ได้:")
    print("   /verbose  - เปิด/ปิดแสดงรายละเอียดการค้นหา")
    print("   /clear    - เคลียร์หน้าจอ")
    print("   /help     - แสดงคำสั่งนี้")
    print("   quit, exit, q  - ออกจากโปรแกรม")
    print()


def main():
    """Loop หลัก"""

    # ─── เช็คพื้นฐาน ───
    if not GOOGLE_API_KEY:
        print("❌ ไม่พบ GOOGLE_API_KEY ใน .env")
        return

    count = vector_db.count_documents()
    if count == 0:
        print("❌ Chroma DB ว่างเปล่า")
        print("   กรุณารัน: python -m src.ingest")
        return

    # ─── Welcome ───
    print_welcome()
    print(f"\n💾 โหลด knowledge base: {count} chunks พร้อม")

    # ─── Loop ───
    verbose = False

    while True:
        try:
            # รับ input
            print()
            user_input = input("👤 คุณ: ").strip()

            # ข้าม input ว่าง
            if not user_input:
                continue

            # ─── ตรวจ command ───
            cmd = user_input.lower()

            # ออก
            if cmd in ("quit", "exit", "q", "/quit", "/exit"):
                print("\n👋 ลาก่อนค่ะ! ขอให้เป็นวันที่ดีนะคะ 💙")
                break

            # เปิด/ปิด verbose
            if cmd == "/verbose":
                verbose = not verbose
                state = "เปิด" if verbose else "ปิด"
                print(f"🔧 Verbose mode: {state}")
                continue

            # เคลียร์หน้าจอ
            if cmd == "/clear":
                import os

                os.system("clear")
                print_welcome()
                continue

            # ช่วยเหลือ
            if cmd in ("/help", "/?"):
                print_help()
                continue

            # ─── ถาม-ตอบ ───
            print("\n💭 กำลังคิด...", end="", flush=True)

            try:
                response = answer(user_input, verbose=verbose)

                # ลบข้อความ "กำลังคิด..." (เลื่อนกลับ + ลบ)
                print("\r" + " " * 20 + "\r", end="")

                # แสดงคำตอบ
                print(f"💬 น้องซีที: {response}")

            except Exception as e:
                print(f"\r❌ เกิดข้อผิดพลาด: {e}")
                print("   ลองถามใหม่อีกครั้งนะคะ")

        # ─── Ctrl+C ───
        except KeyboardInterrupt:
            print("\n\n👋 ลาก่อนค่ะ! 💙")
            break

        # ─── EOF (Ctrl+D) ───
        except EOFError:
            print("\n👋 ลาก่อนค่ะ! 💙")
            break


if __name__ == "__main__":
    main()

"""
Interactive Chat กับน้องซีที
คุยต่อเนื่องใน terminal ได้ — ใช้ RAR (RAG + Rules + SQLite)

รัน: python -m src.chat
ออก: พิมพ์ 'quit', 'exit', หรือ 'q' หรือกด Ctrl+C
"""
import datetime                                          # ← เพิ่ม
from pathlib import Path                                  # ← เพิ่ม

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import GOOGLE_API_KEY, PROJECT_ROOT      # ← เพิ่ม PROJECT_ROOT
from src.database import vector_db
import re

# ─── Logging unanswered questions ──────────────────    ← เพิ่ม block นี้
def log_unanswered_question(question: str):
    """บันทึกคำถามที่น้องซีทีตอบไม่ได้"""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "no_context.log"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {question}\n")
    except Exception as e:
        print(f"⚠️  Cannot log: {e}")

def _add_space_th_en(text: str) -> str:
    """แทรกเว้นวรรคระหว่างอังกฤษ/ตัวเลข กับไทย เช่น NU6คือ → NU6 คือ"""
    text = re.sub(r'([A-Za-z0-9])([\u0e00-\u0e7f])', r'\1 \2', text)
    text = re.sub(r'([\u0e00-\u0e7f])([A-Za-z0-9])', r'\1 \2', text)
    return text

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
7. ห้ามเดาข้อมูลที่ไม่มีใน context (เช่น ชื่อเล่น เบอร์โทร ฯลฯ)
   ถ้าไม่มีข้อมูล ให้ตอบเฉพาะข้อมูลที่มีจริง
"""


# ─── ตัวแปร global (cache) ─────────────────────────
_llm = None


def get_llm():
    """โหลด LLM แค่ครั้งเดียว"""
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.3,
            google_api_key=GOOGLE_API_KEY,
        )
    return _llm


def answer(question, verbose=False, history=None):
    history = history or []
    question = _add_space_th_en(question) 
    from src.retriever import retrieve_context

    # ส่ง history เข้าไปด้วย ← แก้จากเดิมที่ไม่ได้ส่ง
    context = retrieve_context(question, verbose=verbose, history=history)

    if not context.has_any():
        log_unanswered_question(question)
        return (
            "ขออภัยค่ะ น้องซีทียังไม่มีข้อมูลในเรื่องนี้ "
            "แนะนำให้ติดต่อภาควิชาที่ 055-963262 หรือ 055-963263 นะคะ"
        )

    context_text = context.to_prompt_text()

    # ── สร้าง history text ──
    history_text = ""
    if history:
        lines = []
        for msg in history[-6:]:  # แค่ 3 คู่ล่าสุด
            role = "นิสิต" if msg["role"] == "user" else "น้องซีที"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n".join(lines)

# ── สร้าง prompt ──
    user_message = f"""ข้อมูลอ้างอิง:\n\n{context_text}\n\n---\n"""

    if history_text:
        user_message += f"""การสนทนาก่อนหน้า:\n{history_text}\n\n---\n"""

    user_message += f"คำถามจากนิสิต: {question}"

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]
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
    from collections import deque
    _history = deque(maxlen=6)   # ← เพิ่มบรรทัดนี้ จำ 3 คู่ล่าสุด
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
                # ส่ง history เข้าไป ← แก้ตรงนี้
                response = answer(user_input, verbose=verbose, history=list(_history))
                
                # ลบข้อความ "กำลังคิด..."
                print("\r" + " " * 20 + "\r", end="")
                
                # แสดงคำตอบ
                print(f"💬 น้องซีที: {response}")
                
                # ── เก็บลง history ← เพิ่ม block นี้ ──
                _history.append({"role": "user", "content": user_input})
                _history.append({"role": "assistant", "content": response[:200]})
                
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
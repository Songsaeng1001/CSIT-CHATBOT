"""
Interactive Chat กับน้องซีที
คุยต่อเนื่องใน terminal ได้ — ใช้ RAR (RAG + Rules + SQLite)

รัน: python -m src.chat
ออก: พิมพ์ 'quit', 'exit', หรือ 'q' หรือกด Ctrl+C
"""
import re
import datetime
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import GOOGLE_API_KEY, PROJECT_ROOT
from src.database import vector_db


# ─── Logging unanswered questions ──────────────────
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
    """แทรกเว้นวรรคระหว่างอังกฤษ/ตัวเลข กับไทย เช่น NU6คือ → NU6 คือ (ฟรี ไม่ใช้ LLM)"""
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
8. ถ้าคำถามเกี่ยวกับหน่วยงาน/บริการเฉพาะ (เช่น สหกิจศึกษา ทุนการศึกษา ฝึกงาน)
   และใน context มีผู้ติดต่อของหน่วยงานนั้นโดยตรง
   ให้แสดงเฉพาะผู้ติดต่อของหน่วยงานนั้น ห้ามแสดงเจ้าหน้าที่ทั่วไปของภาควิชา
"""


# ─── Prompt สำหรับเกลาคำถาม ─────────────────────────
REWRITE_PROMPT = """คุณเป็นตัวช่วยปรับคำถามนิสิตให้เป็น "คำค้น" ที่ชัดเจน สำหรับค้นในฐานข้อมูลภาควิชา CSIT ม.นเรศวร

หน้าที่: แปลงคำถามให้พร้อมค้นหา โดย:
1. แก้คำสะกดผิด/พิมพ์เพี้ยน
2. เว้นวรรคให้ถูก โดยเฉพาะระหว่างรหัส/ตัวเลขกับคำไทย
3. ขยายตัวย่อ/คำไม่เป็นทางการเป็นคำเต็ม เช่น สหกิจ → สหกิจศึกษา, ลทบ → ลงทะเบียนเรียน
4. ถ้าคำถามอ้างถึงเรื่องก่อนหน้า ให้เติมหัวข้อจากบทสนทนาก่อนหน้าให้ครบ
5. คงความหมายเดิม ห้ามเพิ่มข้อมูลที่ไม่มี ห้ามตอบคำถาม

ตัวอย่าง:
- "Nu6คือ" → "NU6 คือ แบบฟอร์ม"
- "สหกิจติดต่อใคร" → "สหกิจศึกษา ติดต่อเจ้าหน้าที่คนไหน"
- (ก่อนหน้าคุยเรื่องลงทะเบียน) "แล้วต้องทำยังไง" → "ขั้นตอนการลงทะเบียนเรียนต้องทำอย่างไร"
- ห้ามเดา intent ที่ผู้ใช้ไม่ได้พูด เช่น ถ้าถามแค่ "สหกิจ" ห้ามเติม "ติดต่อใคร"
  ให้ขยายแค่คำ (สหกิจ → สหกิจศึกษา) ไม่ใช่เพิ่มเจตนาใหม่

ตอบกลับมาเป็นคำค้นที่ปรับแล้ว "บรรทัดเดียว" เท่านั้น ห้ามมีคำอธิบายอื่น"""


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


def _history_text(history, limit=6):
    """รวม history ล่าสุดเป็นข้อความ (3 คู่)"""
    if not history:
        return ""
    lines = []
    for msg in history[-limit:]:
        role = "นิสิต" if msg["role"] == "user" else "น้องซีที"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def rewrite_query(question, history=None):
    """เกลาคำถามด้วย LLM ให้พร้อมค้น — ถ้าพลาดคืน normalize แบบ regex แทน"""
    history = history or []

    user_content = ""
    hist = _history_text(history)
    if hist:
        user_content += f"บทสนทนาก่อนหน้า:\n{hist}\n\n"
    user_content += f"คำถามล่าสุด: {question}"

    try:
        resp = get_llm().invoke([
            SystemMessage(content=REWRITE_PROMPT),
            HumanMessage(content=user_content),
        ])
        cleaned = resp.content.strip().strip('"').strip("'").strip()
        # safety: ว่าง หรือยาวผิดปกติ (LLM หลุดไปตอบ) → ใช้ regex normalize
        if not cleaned or len(cleaned) > max(len(question) * 5, 200):
            return _add_space_th_en(question)
        return cleaned
    except Exception as e:
        print(f"⚠️  rewrite พลาด ใช้คำถามเดิม: {e}")
        return _add_space_th_en(question)


def answer(question, verbose=False, history=None):
    history = history or []
    from src.retriever import retrieve_context

    # 1) ค้นด้วยคำถามที่ normalize แบบ regex ก่อน (ฟรี ไม่เสีย LLM call)
    search_query = _add_space_th_en(question)
    context = retrieve_context(search_query, verbose=verbose, history=history)

    # 2) ถ้าค้นไม่เจอ ค่อยใช้ LLM เกลาคำถามแล้วค้นใหม่ (เสีย LLM call เฉพาะตอนจำเป็น)
    if not context.has_any():
        rewritten = rewrite_query(question, history)
        if rewritten != search_query:
            if verbose:
                print(f"🔎 rewrite: '{search_query}' → '{rewritten}'")
            context = retrieve_context(rewritten, verbose=verbose, history=history)

    # 3) ยังไม่เจออีก = ตอบไม่ได้
    if not context.has_any():
        log_unanswered_question(question)
        return (
            "ขออภัยค่ะ น้องซีทียังไม่มีข้อมูลในเรื่องนี้ "
            "แนะนำให้ติดต่อภาควิชาที่ 055-963262 หรือ 055-963263 นะคะ"
        )

    context_text = context.to_prompt_text()
    history_text = _history_text(history)

    # ── สร้าง prompt (ใช้ question เดิม ไม่ใช่คำที่เกลา) ──
    user_message = f"""ข้อมูลอ้างอิง:\n\n{context_text}\n\n---\n"""
    if history_text:
        user_message += f"""การสนทนาก่อนหน้า:\n{history_text}\n\n---\n"""
    user_message += f"คำถามจากนิสิต: {question}"

    response = get_llm().invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])
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
    if not GOOGLE_API_KEY:
        print("❌ ไม่พบ GOOGLE_API_KEY ใน .env")
        return

    count = vector_db.count_documents()
    if count == 0:
        print("❌ Chroma DB ว่างเปล่า")
        print("   กรุณารัน: python -m src.ingest")
        return

    print_welcome()
    print(f"\n💾 โหลด knowledge base: {count} chunks พร้อม")

    verbose = False
    from collections import deque
    _history = deque(maxlen=6)
    while True:
        try:
            print()
            user_input = input("👤 คุณ: ").strip()
            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in ("quit", "exit", "q", "/quit", "/exit"):
                print("\n👋 ลาก่อนค่ะ! ขอให้เป็นวันที่ดีนะคะ 💙")
                break
            if cmd == "/verbose":
                verbose = not verbose
                print(f"🔧 Verbose mode: {'เปิด' if verbose else 'ปิด'}")
                continue
            if cmd == "/clear":
                import os
                os.system("clear")
                print_welcome()
                continue
            if cmd in ("/help", "/?"):
                print_help()
                continue

            print("\n💭 กำลังคิด...", end="", flush=True)
            try:
                response = answer(user_input, verbose=verbose, history=list(_history))
                print("\r" + " " * 20 + "\r", end="")
                print(f"💬 น้องซีที: {response}")
                _history.append({"role": "user", "content": user_input})
                _history.append({"role": "assistant", "content": response[:200]})
            except Exception as e:
                print(f"\r❌ เกิดข้อผิดพลาด: {e}")
                print("   ลองถามใหม่อีกครั้งนะคะ")

        except KeyboardInterrupt:
            print("\n\n👋 ลาก่อนค่ะ! 💙")
            break
        except EOFError:
            print("\n👋 ลาก่อนค่ะ! 💙")
            break


if __name__ == "__main__":
    main()
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

from dataclasses import dataclass
from src.quick_replies import topic_from_sources

# ─── Sentinel: ตอบไม่ได้ ───────────────────────────
# answer() จะคืนค่านี้เมื่อค้น context ไม่เจอ (แทนการคืนข้อความไทยตรง ๆ)
# ผู้เรียก (CLI main / LINE webhook) เป็นคนตัดสินใจว่าจะโชว์ข้อความอะไร
# และตั้ง answered=False เอง → ไม่ต้องเดาด้วยการเช็ก substring ในคำตอบอีก
NO_ANSWER = "__NO_ANSWER__"

# ข้อความสำรองมาตรฐานตอนตอบไม่ได้ (ใช้ฝั่ง CLI; LINE มีข้อความของตัวเอง)
NO_ANSWER_MESSAGE = (
    "ขออภัยค่ะ น้องซีทียังไม่มีข้อมูลในเรื่องนี้ "
    "แนะนำให้ติดต่อภาควิชาที่ 055-963262 หรือ 055-963263 นะคะ"
)


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
    text = re.sub(r"([A-Za-z0-9])([\u0e00-\u0e7f])", r"\1 \2", text)
    text = re.sub(r"([\u0e00-\u0e7f])([A-Za-z0-9])", r"\1 \2", text)
    return text


SYSTEM_PROMPT = """คุณคือ 'น้องซีที' (CSIT) ผู้ช่วย AI อย่างเป็นทางการของภาควิชาวิทยาการคอมพิวเตอร์
และเทคโนโลยีสารสนเทศ คณะวิทยาศาสตร์ มหาวิทยาลัยนเรศวร
หน้าที่ของคุณคือช่วยตอบคำถามของนิสิต ผู้ปกครอง และผู้สนใจ เกี่ยวกับภาควิชา
ให้ถูกต้อง ครบถ้วน และเข้าใจง่าย

━━ ขอบเขตที่คุณดูแล ━━
คุณตอบเรื่องที่เกี่ยวกับภาควิชา เช่น หลักสูตร/โครงสร้างหลักสูตร รายวิชา การรับสมัคร (admission)
การลงทะเบียนเรียน คำร้องออนไลน์ (NU form / ระบบ REG) การฝึกงานและสหกิจศึกษา ทุนการศึกษา
กิจกรรมนิสิต อาจารย์และเจ้าหน้าที่ผู้ติดต่อ สถานที่/ห้อง และข้อมูลทั่วไปของภาควิชา

━━ หลักการตอบ (อ่านให้ครบทุกข้อ) ━━
1. ตอบเป็นภาษาไทยสุภาพ เป็นกันเอง ลงท้าย "ค่ะ" เสมอ
   หากผู้ใช้ถามเป็นภาษาอังกฤษ ให้ตอบเป็นภาษาอังกฤษได้

2. ยึดข้อมูลจาก context ที่ระบบส่งมาให้เป็นหลัก ห้ามแต่งข้อมูลที่ไม่มีใน context
   โดยเฉพาะ ตัวเลข ชื่อบุคคล เบอร์โทร อีเมล วัน-เวลา และลิงก์ ห้ามเดาเด็ดขาด
   ถ้าใน context มีหลายรายการที่คล้ายกัน ให้เลือกเฉพาะรายการที่ตรงกับคำถาม
   ห้ามนำข้อมูลคนละเรื่องมารวมกัน

3. ตีความคำถามให้เข้าใจก่อนตัดสินว่าตอบได้หรือไม่
   - เข้าใจคำพิมพ์ผิด คำย่อ ภาษาพูด และคำพ้องความหมาย
     (เช่น "โคออป/coop" = สหกิจศึกษา, "ลงทะเบียนเรียน" = การลงทะเบียน,
      "เกรด/ผลการเรียน", "อ." = อาจารย์)
   - ถ้าเนื้อหาใน context ตรงกับความหมายของคำถาม แม้ใช้คำไม่ตรงกันเป๊ะ
     ให้ถือว่า "ตอบได้"

4. ตอบให้ครบถ้วนตามที่ context มี
   - ถ้าคำถามมีหลายประเด็น ให้ตอบทุกประเด็นที่ context ครอบคลุม
   - ถ้า context ตอบได้เพียง "บางส่วน" ให้ตอบส่วนที่มีข้อมูลก่อน
     แล้วระบุสั้น ๆ ว่าส่วนใดยังไม่มีข้อมูล พร้อมแนะช่องทางติดต่อที่เกี่ยวข้อง
     ห้ามทิ้งทั้งคำถามเป็น __NO_ANSWER__ เพียงเพราะขาดข้อมูลบางจุด

5. ใช้ __NO_ANSWER__ เป็นทางเลือกสุดท้ายเท่านั้น
   ใช้ได้เฉพาะเมื่อ context "ไม่มีข้อมูลที่เกี่ยวข้องกับคำถามเลย"
   เมื่อจะใช้ ให้ตอบกลับด้วยข้อความเดียวว่า __NO_ANSWER__ เท่านั้น
   ห้ามมีข้อความอื่นปน (ระบบจะเติมข้อความขอโทษ + เบอร์ติดต่อให้เอง)

6. คำทักทาย ขอบคุณ หรือคุยเล่นเล็กน้อย (เช่น "สวัสดีค่ะ" "ขอบคุณค่ะ")
   ให้ตอบอย่างเป็นมิตรตามคาแรกเตอร์ ไม่ต้องใช้ __NO_ANSWER__

7. ถ้าคำถามกว้างหรือกำกวมจนอาจตอบผิดประเด็น และการถามกลับสั้น ๆ จะช่วยให้ชัดขึ้น
   ให้ถามกลับเพียง 1 คำถามเพื่อให้ผู้ใช้ระบุให้ชัด (แทนการเดา หรือ __NO_ANSWER__)

8. ถ้าคำถามอยู่นอกขอบเขตภาควิชาโดยสิ้นเชิง
   (เช่น ให้ช่วยเขียนโค้ด แปลภาษา ทำการบ้านวิชาอื่น ดูดวง)
   ให้ปฏิเสธอย่างสุภาพ และบอกสั้น ๆ ว่าคุณช่วยเรื่องใดได้บ้าง

━━ ข้อมูลติดต่อและลิงก์ (สำคัญมาก) ━━
9. ถ้า context มีเบอร์โทร อีเมล หรือ URL ที่เกี่ยวกับคำถาม
   ต้องคัดลอกมาแสดงให้ครบถ้วนทุกครั้ง ห้ามละ ห้ามย่อ ห้ามดัดแปลง URL

9.1 ห้ามใช้ข้อความยึดตำแหน่งแทนลิงก์/เบอร์/อีเมลเด็ดขาด เช่น [ลิงก์...] [เบอร์โทร...]
    ถ้าไม่มีข้อมูลจริงใน context (และไม่ใช่กรณีข้อ 11 ด้านล่างที่มีลิงก์ตายตัวให้แล้ว)
    ให้ตัดส่วนนั้นออก หรือแนะนำให้ติดต่อภาควิชาแทน ห้ามแต่งวงเล็บขึ้นมาเด็ดขาด

10. เรื่องหน่วยงาน/บริการเฉพาะ (สหกิจศึกษา ทุนการศึกษา ฝึกงาน ฯลฯ)
    ถ้ามีผู้ติดต่อของหน่วยงานนั้นโดยตรง ให้แสดงเฉพาะผู้ติดต่อของหน่วยงานนั้น
    ห้ามแสดงเจ้าหน้าที่ทั่วไปของภาควิชา

11. เมื่อตอบเรื่องโครงสร้างหลักสูตร (หลักสูตร/รายวิชาที่ต้องเรียน/แผนการเรียนแต่ละชั้นปี)
    ต้องแนบลิงก์นี้เสมอ ไม่ว่า context จะส่งลิงก์นี้มาด้วยหรือไม่ก็ตาม:
    https://csit.nu.ac.th/curriculums/

12. เมื่อตอบเรื่อง NU form / คำร้องออนไลน์ทุกครั้ง
    ต้องแนบลิงก์คู่มือการใช้งานระบบคำร้องออนไลน์ที่มีอยู่ใน context เสมอ
    ถ้า context ไม่มีลิงก์ ให้ระบุแค่ชื่อฟอร์ม (เช่น "NU3") โดยไม่ใส่วงเล็บลิงก์ปลอม
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
        resp = get_llm().invoke(
            [
                SystemMessage(content=REWRITE_PROMPT),
                HumanMessage(content=user_content),
            ]
        )
        cleaned = resp.content.strip().strip('"').strip("'").strip()
        # safety: ว่าง หรือยาวผิดปกติ (LLM หลุดไปตอบ) → ใช้ regex normalize
        if not cleaned or len(cleaned) > max(len(question) * 5, 200):
            return _add_space_th_en(question)
        return cleaned
    except Exception as e:
        print(f"⚠️  rewrite พลาด ใช้คำถามเดิม: {e}")
        return _add_space_th_en(question)


def _strip_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **ตัวหนา**
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"\1", text)  # *เอียง*
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)  # # หัวข้อ
    return text


@dataclass
class AnswerResult:
    """ผลลัพธ์การตอบแบบเต็ม (ฝั่ง LINE ใช้ topic เลือกชุด quick reply)"""
    text: str            # ข้อความพร้อมส่ง (resolve sentinel แล้ว)
    answered: bool       # True = ตอบจาก context ได้, False = ไม่มีข้อมูล
    topic: str | None    # หัวข้อสำหรับเลือกปุ่ม (None = ใช้ default)


def answer_full(question, verbose=False, history=None) -> AnswerResult:
    """เหมือน answer() แต่คืนข้อมูลครบ (text + answered + topic)
    ใช้ฝั่ง LINE webhook เพื่อแนบ quick reply ตามหมวดที่ตอบจริง
    """
    history = history or []
    from src.retriever import retrieve_context

    # 1) ค้นด้วยคำถาม normalize แบบ regex ก่อน (ฟรี)
    search_query = _add_space_th_en(question)
    context = retrieve_context(search_query, verbose=verbose, history=history)

    # 2) ค้นไม่เจอ → ใช้ LLM เกลาคำถามแล้วค้นใหม่
    if not context.has_any():
        rewritten = rewrite_query(question, history)
        if rewritten != search_query:
            if verbose:
                print(f"🔎 rewrite: '{search_query}' → '{rewritten}'")
            context = retrieve_context(rewritten, verbose=verbose, history=history)

    # 3) ยังไม่เจอ = ตอบไม่ได้
    if not context.has_any():
        log_unanswered_question(question)
        return AnswerResult(text=NO_ANSWER_MESSAGE, answered=False, topic=None)

    context_text = context.to_prompt_text()
    history_text = _history_text(history)

    user_message = f"""ข้อมูลอ้างอิง:\n\n{context_text}\n\n---\n"""
    if history_text:
        user_message += f"""การสนทนาก่อนหน้า:\n{history_text}\n\n---\n"""
    user_message += f"คำถามจากนิสิต: {question}"

    response = get_llm().invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
    )
    text = _strip_markdown(response.content)

    # LLM ตัดสินเองว่า context ไม่พอจะตอบ → คืนแบบเดียวกับเคสค้นไม่เจอ
    # (อุดช่องโหว่ "เจอ context แต่ตอบว่าไม่มีข้อมูล" ที่ทำให้ answered=True + โชว์ปุ่ม)
    if not text.strip() or NO_ANSWER in text:
        log_unanswered_question(question)
        return AnswerResult(text=NO_ANSWER_MESSAGE, answered=False, topic=None)

    topic = topic_from_sources(context.sources_used)
    return AnswerResult(text=text, answered=True, topic=topic)


def answer(question, verbose=False, history=None):
    """(คงพฤติกรรมเดิม) คืน string คำตอบ หรือ NO_ANSWER ถ้าตอบไม่ได้
    ผู้เรียกเดิม (CLI main / โค้ดอื่นที่เช็ก == NO_ANSWER) ใช้ได้เหมือนเดิม
    """
    result = answer_full(question, verbose=verbose, history=history)
    return result.text if result.answered else NO_ANSWER


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
                # แปลง sentinel เป็นข้อความที่อ่านได้ (อย่าโชว์ "__NO_ANSWER__")
                if response == NO_ANSWER:
                    response = NO_ANSWER_MESSAGE
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
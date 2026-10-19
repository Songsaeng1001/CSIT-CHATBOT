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

NO_ANSWER = "__NO_ANSWER__"

DEPT_WEBSITE = "https://csit.nu.ac.th"
DEPT_FACEBOOK = "https://www.facebook.com/share/1N5QSZJYBn/?mibextid=wwXIfr"

NO_ANSWER_MESSAGE = (
    "ขออภัยค่ะ น้องซีทียังไม่มีข้อมูลในเรื่องนี้ "
    "แนะนำให้ติดต่อภาควิชาที่ 055-963262 หรือ 055-963263 นะคะ\n"
    f"เว็บไซต์ภาควิชา: {DEPT_WEBSITE}\n"
    f"เพจเฟซบุ๊ก CSIT ภาควิชาวิทยาการคอมพิวเตอร์: {DEPT_FACEBOOK}"
)

DEPT_PHONES = "055-963262 หรือ 055-963263"

SCHOLARSHIP_KEYWORDS = ["ทุน", "scholarship"]
SCHOLARSHIP_EXCLUDE = ["กยศ", "กู้"]

SCHOLARSHIP_MESSAGE = (
    "ทุนการศึกษามีการเปิดรับและเปลี่ยนแปลงรายละเอียดทุกปีการศึกษาค่ะ "
    "น้องซีทีจึงไม่ได้เก็บรายชื่อหรือรายละเอียดทุนไว้ "
    "แนะนำให้ติดตามประกาศทุนล่าสุดจากช่องทางของภาควิชานะคะ\n\n"
    f"เว็บไซต์ภาควิชา: {DEPT_WEBSITE}\n"
    f"เพจเฟซบุ๊ก CSIT ภาควิชาวิทยาการคอมพิวเตอร์: {DEPT_FACEBOOK}\n\n"
    "หากต้องการสอบถามรายละเอียดเพิ่มเติม ติดต่อเจ้าหน้าที่ภาควิชาได้ที่\n"
    f"โทร: {DEPT_PHONES}\n"
    "สำนักงานภาควิชา คณะวิทยาศาสตร์ อาคาร SC2"
)


def is_scholarship_query(question: str) -> bool:
    q = question.lower()
    if any(kw in q for kw in SCHOLARSHIP_EXCLUDE):
        return False
    return any(kw in q for kw in SCHOLARSHIP_KEYWORDS)


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
   โดยเฉพาะ ตัวเลข ชื่อบุคคล เบอร์โทร อีเมล วัน-เวลา ลิงก์ และ "ขั้นตอน/วิธีการปฏิบัติ" ห้ามเดาเด็ดขาด
   ถ้าใน context มีหลายรายการที่คล้ายกัน ให้เลือกเฉพาะรายการที่ตรงกับคำถาม
   ห้ามนำข้อมูลคนละเรื่องมารวมกัน

2.1 ห้ามแต่งขั้นตอนย่อยหรือวิธีปฏิบัติเพิ่มเติมเองแม้จะฟังดูสมเหตุสมผลหรือคาดเดาได้
    (เช่น ชื่อหน่วยงานที่ต้องยื่นเรื่อง ขั้นตอนกลางที่ context ไม่ได้พูดถึง)
    ถ้า context ระบุขั้นตอนไว้ไม่ครบ ให้ตอบเท่าที่ context มีจริงเท่านั้น
    แล้วแนะนำให้ติดต่อภาควิชาเพื่อสอบถามรายละเอียดเพิ่มเติม แทนการเดาขั้นตอนที่เหลือเอง

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
    ถ้าไม่มีข้อมูลจริงใน context (และไม่ใช่กรณีข้อ 11–14 ด้านล่างที่มีลิงก์ตายตัวให้แล้ว)
    ให้ตัดส่วนนั้นออก หรือแนะนำให้ติดต่อภาควิชาแทน ห้ามแต่งวงเล็บขึ้นมาเด็ดขาด

10. เรื่องหน่วยงาน/บริการเฉพาะ (สหกิจศึกษา ทุนการศึกษา ฝึกงาน ฯลฯ)
    ถ้ามีผู้ติดต่อของหน่วยงานนั้นโดยตรง ให้แสดงเฉพาะผู้ติดต่อของหน่วยงานนั้น
    ห้ามแสดงเจ้าหน้าที่ทั่วไปของภาควิชา

11. กฎนี้ใช้ "เฉพาะ" คำถามเรื่องโครงสร้างหลักสูตรโดยตรงเท่านั้น
    (เช่น หลักสูตรมีวิชาอะไรบ้าง, ต้องเรียนวิชาอะไรบ้าง, แผนการเรียนแต่ละชั้นปี,
    จำนวนหน่วยกิตรวมของหลักสูตร)
    ต้องแนบลิงก์นี้เสมอ ไม่ว่า context จะส่งลิงก์นี้มาด้วยหรือไม่ก็ตาม:
    https://csit.nu.ac.th/curriculums/

    ห้ามแนบลิงก์นี้กับคำถามเรื่องอื่นเด็ดขาด แม้จะเกี่ยวกับ "การเรียน" ในความหมายกว้างก็ตาม
    เช่น การลงทะเบียนเรียน การขอลงทะเบียนเกิน/ต่ำกว่าหน่วยกิตที่กำหนด คำร้องต่าง ๆ
    เกรด/ผลการเรียน การขอเทียบโอนรายวิชา สถานภาพนิสิต การสำเร็จการศึกษา ฯลฯ
    คำถามกลุ่มนี้ให้ตอบตาม context ปกติ (ดูข้อ 12 ถ้าเป็นเรื่อง NU form)

12. เมื่อตอบเรื่อง NU form / คำร้องออนไลน์ทุกครั้ง
    ต้องแนบลิงก์คู่มือการใช้งานระบบคำร้องออนไลน์ที่มีอยู่ใน context เสมอ
    ถ้า context ไม่มีลิงก์ ให้ระบุแค่ชื่อฟอร์ม (เช่น "NU3") โดยไม่ใส่วงเล็บลิงก์ปลอม

13. กฎการแนบลิงก์คู่มือนิสิต (Student Manual)
    ใช้ "เฉพาะ" คำถามเรื่องเงินและคำร้องเอกสารต่อไปนี้เท่านั้น:
    - ค่าเล่าเรียน ค่าธรรมเนียมการศึกษา การชำระเงิน การคืนเงิน
    - ค่าปรับการลงทะเบียนล่าช้า
    - กองทุนเงินให้กู้ยืมเพื่อการศึกษา (กยศ.)
    - เอกสารคำร้องของนิสิต (NU form / คำร้องต่าง ๆ)

    เมื่อคำถามตรงกับหัวข้อข้างต้น ให้แนบลิงก์นี้ "เพิ่มเติม" ท้ายคำตอบเสมอ
    (แนบเพิ่มจากลิงก์อื่นที่มีอยู่แล้ว ไม่ใช่แทนที่ — เช่น คำถาม กยศ. ให้คงลิงก์ กยศ.
    เดิมไว้ แล้วเพิ่มลิงก์นี้ต่อท้าย):
    https://reg7.nu.ac.th/publish/studentmanual2025_b.pdf

    ห้ามแนบลิงก์นี้กับคำถามที่ไม่เกี่ยวกับเงินหรือคำร้องข้างต้นเด็ดขาด
    เช่น หลักสูตร รายวิชา อาจารย์ สถานที่ กิจกรรม ให้ตอบตาม context ปกติ
14. กฎการแนบลิงก์ปฏิทินการศึกษา
    ใช้ "เฉพาะ" คำถามเรื่องกำหนดการตามปฏิทินการศึกษาเท่านั้น เช่น
    - ช่วงเปิด-ปิดภาคการศึกษา
    - ช่วงเวลาลงทะเบียนเรียน และช่วงเพิ่ม-ถอนรายวิชาภายในกำหนด
    - กำหนดวันลงทะเบียนล่าช้า และวันสุดท้ายของการชำระเงิน
    - ช่วงถอนรายวิชาแบบติดอักษร W
    - กำหนดการสอบ (กลางภาค/ปลายภาค)
    - กำหนดวันยื่นสำเร็จการศึกษา
    - วันสำคัญหรือวันหยุดตามปฏิทินการศึกษา

    เมื่อคำถามตรงกับหัวข้อข้างต้น ให้แนบลิงก์นี้เพิ่มเติมท้ายคำตอบเสมอ:
    https://reg4.nu.ac.th/registrar/calendar.asp?schedulegroupid=1000&acadyear=2569&semester=2

    ห้ามแนบลิงก์นี้กับคำถามเรื่อง "เวลา" ที่ไม่ใช่กำหนดการตามปฏิทินการศึกษา
    เช่น เวลาทำการภาควิชา ระยะเวลาของหลักสูตร ระยะเวลาปฏิบัติงานสหกิจ
    และกำหนดการ/ระยะเวลาต่าง ๆ ของ กยศ. (ให้ตอบตาม context ปกติ)

15. ไม่ต้องแนบลิงก์เว็บไซต์ภาควิชาหรือเพจเฟซบุ๊กของภาควิชาเอง
    ระบบจะต่อท้ายลิงก์ทั้งสองให้อัตโนมัติเมื่อเหมาะสม

16. ห้ามอ้างชื่อไฟล์ ชื่อเอกสารต้นทาง หรือคำว่า "context" ในคำตอบเด็ดขาด
    (เช่น "ดูได้จากไฟล์ contact_office.md") ให้นำข้อมูลมาตอบโดยตรงแทน
"""

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

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.3,
            google_api_key=GOOGLE_API_KEY,
        )
    return _llm


def _history_text(history, limit=6):
    if not history:
        return ""
    lines = []
    for msg in history[-limit:]:
        role = "นิสิต" if msg["role"] == "user" else "น้องซีที"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def rewrite_query(question, history=None):
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
        if not cleaned or len(cleaned) > max(len(question) * 5, 200):
            return _add_space_th_en(question)
        return cleaned
    except Exception as e:
        print(f"  rewrite พลาด ใช้คำถามเดิม: {e}")
        return _add_space_th_en(question)


def _remove_file_refs(text: str) -> str:
    text = re.sub(r"^.*\b[\w\-]+\.md\b.*\n?", "", text, flags=re.MULTILINE)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^(\s*)\*\s+", r"\1• ", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    return text


DEPT_LINK_KEYWORDS = [
    "ติดต่อ", "เบอร์", "โทร", "อีเมล", "ที่ตั้ง", "ตึก", "อาคาร", "อยู่ที่ไหน", "อยู่ไหน",
    "เวลาทำการ", "เปิดกี่โมง", "ปิดกี่โมง", "ข่าว", "ประกาศ", "กิจกรรม",
    "รับสมัคร", "สมัครเรียน", "เว็บ", "เพจ", "facebook", "เฟซบุ๊ก", "เฟสบุ๊ค",
]


def append_dept_links(question: str, text: str) -> str:
    q = question.lower()
    if not any(kw in q for kw in DEPT_LINK_KEYWORDS):
        return text

    lines = []
    if not re.search(r"https?://csit\.nu\.ac\.th/?(?:\s|$)", text):
        lines.append(f"เว็บไซต์ภาควิชา: {DEPT_WEBSITE}")
    if "facebook.com/share/1N5QSZJYBn" not in text:
        lines.append(f"เพจเฟซบุ๊ก CSIT ภาควิชาวิทยาการคอมพิวเตอร์: {DEPT_FACEBOOK}")

    if not lines:
        return text
    return text.rstrip() + "\n\n" + "\n".join(lines)


@dataclass
class AnswerResult:
    text: str            
    answered: bool       
    topic: str | None    


def answer_full(question, verbose=False, history=None) -> AnswerResult:
    history = history or []

    if is_scholarship_query(question):
        return AnswerResult(text=SCHOLARSHIP_MESSAGE, answered=True, topic=None)

    from src.retriever import retrieve_context

    search_query = _add_space_th_en(question)
    context = retrieve_context(search_query, verbose=verbose, history=history)

    if not context.has_any():
        rewritten = rewrite_query(question, history)
        if rewritten != search_query:
            if verbose:
                print(f"rewrite: '{search_query}' → '{rewritten}'")
            context = retrieve_context(rewritten, verbose=verbose, history=history)

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
    text = _remove_file_refs(_strip_markdown(response.content))

    if not text.strip() or NO_ANSWER in text:
        log_unanswered_question(question)
        return AnswerResult(text=NO_ANSWER_MESSAGE, answered=False, topic=None)

    text = append_dept_links(question, text)

    topic = topic_from_sources(context.sources_used)
    return AnswerResult(text=text, answered=True, topic=topic)


def answer(question, verbose=False, history=None):
    result = answer_full(question, verbose=verbose, history=history)
    return result.text if result.answered else NO_ANSWER


def print_welcome():
    print()
    print("=" * 60)
    print(" น้องซีที — ผู้ช่วย AI ภาควิชา CSIT")
    print("=" * 60)
    print(" ทักทายและถามคำถามได้เลยค่ะ!")
    print()
    print(" คำสั่งพิเศษ:")
    print("   /verbose  - เปิด/ปิดแสดงรายละเอียดการค้นหา")
    print("   /clear    - เคลียร์หน้าจอ")
    print("   /help     - แสดงคำสั่งทั้งหมด")
    print("   quit, q   - ออกจากโปรแกรม")
    print("=" * 60)


def print_help():
    print("\n คำสั่งที่ใช้ได้:")
    print("   /verbose  - เปิด/ปิดแสดงรายละเอียดการค้นหา")
    print("   /clear    - เคลียร์หน้าจอ")
    print("   /help     - แสดงคำสั่งนี้")
    print("   quit, exit, q  - ออกจากโปรแกรม")
    print()


def main():
    if not GOOGLE_API_KEY:
        print(" ไม่พบ GOOGLE_API_KEY ใน .env")
        return

    count = vector_db.count_documents()
    if count == 0:
        print(" Chroma DB ว่างเปล่า")
        print("   กรุณารัน: python -m src.ingest")
        return

    print_welcome()
    print(f"\n โหลด knowledge base: {count} chunks พร้อม")

    verbose = False
    from collections import deque

    _history = deque(maxlen=6)
    while True:
        try:
            print()
            user_input = input(" คุณ: ").strip()
            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in ("quit", "exit", "q", "/quit", "/exit"):
                print("\n ลาก่อนค่ะ! ขอให้เป็นวันที่ดีนะคะ ")
                break
            if cmd == "/verbose":
                verbose = not verbose
                print(f" Verbose mode: {'เปิด' if verbose else 'ปิด'}")
                continue
            if cmd == "/clear":
                import os

                os.system("clear")
                print_welcome()
                continue
            if cmd in ("/help", "/?"):
                print_help()
                continue

            print("\n กำลังคิด...", end="", flush=True)
            try:
                response = answer(user_input, verbose=verbose, history=list(_history))
                if response == NO_ANSWER:
                    response = NO_ANSWER_MESSAGE
                print("\r" + " " * 20 + "\r", end="")
                print(f" น้องซีที: {response}")
                _history.append({"role": "user", "content": user_input})
                _history.append({"role": "assistant", "content": response[:200]})
            except Exception as e:
                print(f"\r เกิดข้อผิดพลาด: {e}")
                print("   ลองถามใหม่อีกครั้งนะคะ")

        except KeyboardInterrupt:
            print("\n\n ลาก่อนค่ะ! ")
            break
        except EOFError:
            print("\n ลาก่อนค่ะ! ")
            break


if __name__ == "__main__":
    main()
"""
Quick Reply — ปุ่มแนะนำ "คำถามต่อ" ใต้คำตอบใน LINE

หลักการ:
  - ปุ่มทั้งหมดเป็น string ตายตัว → 0 token ฝั่ง LLM
  - เลือกชุดปุ่มจาก `route` ที่ route_message() ใน main.py คืนมาอยู่แล้ว
  - ปุ่มแบบ action=message: กดแล้วส่ง `text` กลับเข้า webhook เหมือนพิมพ์เอง

สำคัญ: ปุ่มเหล่านี้ "ตั้งใจไม่ซ้ำ" กับ rich menu
  (rich menu มี: หลักสูตร / อาจารย์ / ติดต่อภาควิชา / ยื่นจบ / กยศ. / คำร้อง)
  จึงเป็นคำถามย่อยที่ลึกกว่าเมนู เพื่อไม่ให้ผู้ใช้เห็นตัวเลือกซ้ำ
"""
QR_LIMIT = 13      
LABEL_MAX = 20     


def _qr(label: str, text: str) -> dict:
    """สร้าง 1 ปุ่ม (action=message). label จะถูกตัดให้ไม่เกิน 20 ตัวอักษร"""
    return {
        "type": "action",
        "action": {"type": "message", "label": label[:LABEL_MAX], "text": text},
    }

QUICK_REPLIES: dict[str, list[dict]] = {
    "forms": [
        _qr("ขั้นตอนการยื่น", "ขั้นตอนการยื่นคำร้องนี้ทำยังไง"),
        _qr("ยื่นออนไลน์ที่ไหน", "ยื่นคำร้องออนไลน์ที่ไหน"),
        _qr("ค่าธรรมเนียม", "ค่าธรรมเนียมคำร้องเท่าไร"),
    ],
    "instructors": [
        _qr("ห้องทำงาน", "ห้องทำงานอาจารย์อยู่ที่ไหน"),
        _qr("อีเมลอาจารย์", "ขออีเมลอาจารย์"),
        
    ],
    "staff": [
        _qr("เวลาทำการ", "ภาควิชาเปิดทำการกี่โมง"),
        _qr("ที่ตั้งภาควิชา", "ภาควิชาอยู่ตึกไหน"),
        _qr("อีเมลภาควิชา", "อีเมลภาควิชา"),
    ],
    "honor": [
        _qr("เงื่อนไขเกียรตินิยม", "เงื่อนไขการได้เกียรตินิยมมีอะไรบ้าง"),
        _qr("คำนวณ GPA", "คำนวณเกรดเฉลี่ยยังไง"),
    ],
    "late_fee": [
        _qr("ค่าปรับลงช้า", "ลงทะเบียนช้าค่าปรับเท่าไร"),
        _qr("ลงช้ากี่วันพ้นสภาพ", "ลงทะเบียนช้ากี่วันถึงพ้นสภาพ"),
    ],
    "credit": [
        _qr("ลงเกินหน่วยกิต", "ลงเกินหน่วยกิตทำยังไง"),
        _qr("หน่วยกิตขั้นต่ำ", "ลงทะเบียนขั้นต่ำกี่หน่วยกิต"),
    ],
    "status": [
        _qr("เกณฑ์พ้นสภาพ", "เกณฑ์การพ้นสภาพนิสิต"),
        _qr("รอพินิจคืออะไร", "สถานภาพรอพินิจคืออะไร"),
    ],
}

DEFAULT_QR: list[dict] = [
    _qr("ปฏิทินการศึกษา", "ขอปฏิทินการศึกษา"),
    _qr("ลงทะเบียนกี่หน่วยกิต", "ลงทะเบียนได้กี่หน่วยกิต"),
    _qr("ค่าปรับลงช้า", "ลงทะเบียนช้าค่าปรับเท่าไร"),
]

_ALIASES: dict[str, str | None] = {
    "greeting": None,            
    "loan_redirect": None,       
    "calendar_redirect": None,
    "nuform_list": "forms",
    "instructor_list": "instructors",
    "instructor": "instructors",
    "contact": "staff",
    "RAG": None,
    "error": None,
    "SQLite/nu_forms": "forms",
    "SQLite/instructors": "instructors",
    "SQLite/staff": "staff",
    "Rule/honor": "honor",
    "Rule/late_fee": "late_fee",
    "Rule/credit": "credit",
    "Rule/status": "status",
    "Rule/calendar_redirect": None,
    "Rule/loan_redirect": None,
    "Chroma": None,
}


def _resolve_topic(key: str | None) -> str | None:
    if key is None:
        return None
    if key in QUICK_REPLIES:   
        return key
    return _ALIASES.get(key)   


def quick_reply_for(key: str | None) -> dict | None:
    """รับ route (จาก main.py) หรือ topic แล้วคืน dict quickReply"""
    topic = _resolve_topic(key)
    items = QUICK_REPLIES.get(topic, DEFAULT_QR)
    return {"items": items[:QR_LIMIT]} if items else None

_SOURCE_PRIORITY = [
    "SQLite/nu_forms", "SQLite/instructors", "SQLite/staff",
    "Rule/honor", "Rule/late_fee", "Rule/credit", "Rule/status",
]


def topic_from_sources(sources_used: list[str]) -> str | None:
    for source in _SOURCE_PRIORITY:
        if source in sources_used:
            return _ALIASES[source]
    return None
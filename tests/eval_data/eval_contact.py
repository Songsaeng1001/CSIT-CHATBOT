"""20 คำถามหมวดติดต่อ + ลิงก์"""

CATEGORY = "contact"
CATEGORY_TH = "ติดต่อ"

QUESTIONS = [
    # ─── เบอร์โทรภาควิชา (5 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "เบอร์โทรภาควิชา CSIT",
        "expected_keywords": [],
        "alt_keywords": ["055-963262", "055-963263"],
        "ground_truth": "055-963262, 055-963263",
        "is_oos": False,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "โทรภาควิชาเบอร์อะไร",
        "expected_keywords": [],
        "alt_keywords": ["055-963262", "055-963263"],
        "ground_truth": "055-963262, 055-963263",
        "is_oos": False,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "เบอร์งานทะเบียน",
        "expected_keywords": [],
        "alt_keywords": ["055-968300", "0-5596-8300"],
        "ground_truth": "0-5596-8300",
        "is_oos": False,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "เบอร์พี่เฟิร์น",
        "expected_keywords": ["055-963262"],
        "alt_keywords": [],
        "ground_truth": "055-963262",
        "is_oos": False,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "เบอร์พี่แมว",
        "expected_keywords": ["055-963263"],
        "alt_keywords": [],
        "ground_truth": "055-963263",
        "is_oos": False,
    },

    # ─── ที่อยู่ + ห้อง (4 ข้อ) ───
    {
        "id": 6, "category": CATEGORY,
        "question": "ที่อยู่ภาควิชา CSIT",
        "expected_keywords": [],
        "alt_keywords": ["พิษณุโลก", "99", "ท่าโพธิ์"],
        "ground_truth": "99 หมู่ 9 ต.ท่าโพธิ์ อ.เมือง จ.พิษณุโลก",
        "is_oos": False,
    },
    {
        "id": 7, "category": CATEGORY,
        "question": "ภาควิชาตั้งอยู่ที่ไหน",
        "expected_keywords": [],
        "alt_keywords": ["พิษณุโลก", "นเรศวร"],
        "ground_truth": "ม.นเรศวร พิษณุโลก",
        "is_oos": False,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "รหัสไปรษณีย์มหาวิทยาลัยนเรศวร",
        "expected_keywords": ["65000"],
        "alt_keywords": [],
        "ground_truth": "65000",
        "is_oos": False,
    },
    {
        "id": 9, "category": CATEGORY,
        "question": "อาคาร SC2 อยู่ที่ไหน",
        "expected_keywords": [],
        "alt_keywords": ["ภาควิชา", "CSIT", "วิทยาศาสตร์"],
        "ground_truth": "ภาควิชา CSIT คณะวิทยาศาสตร์",
        "is_oos": False,
    },

    # ─── ลิงก์/เว็บไซต์ (6 ข้อ) ───
    {
        "id": 10, "category": CATEGORY,
        "question": "เว็บไซต์ระบบทะเบียน",
        "expected_keywords": [],
        "alt_keywords": ["reg.nu.ac.th", "reg"],
        "ground_truth": "reg.nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 11, "category": CATEGORY,
        "question": "ระบบลงทะเบียนออนไลน์",
        "expected_keywords": [],
        "alt_keywords": ["reg.nu.ac.th"],
        "ground_truth": "reg.nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "ดูปฏิทินการศึกษาที่ไหน",
        "expected_keywords": [],
        "alt_keywords": ["reg4", "calendar", "ปฏิทิน"],
        "ground_truth": "reg4.nu.ac.th/registrar/calendar.asp",
        "is_oos": False,
    },
    {
        "id": 13, "category": CATEGORY,
        "question": "คู่มือนิสิตอยู่ที่ไหน",
        "expected_keywords": [],
        "alt_keywords": ["studentmanual", "reg4", "คู่มือ"],
        "ground_truth": "reg4.nu.ac.th/publish/studentmanual",
        "is_oos": False,
    },
    {
        "id": 14, "category": CATEGORY,
        "question": "เปลี่ยนรหัสผ่านระบบทะเบียน",
        "expected_keywords": [],
        "alt_keywords": ["password.nu.ac.th", "password"],
        "ground_truth": "password.nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "เว็บกองบริการการศึกษา",
        "expected_keywords": [],
        "alt_keywords": ["acad.nu.ac.th", "acad"],
        "ground_truth": "acad.nu.ac.th",
        "is_oos": False,
    },

    # ─── ติดต่อหน่วยงานย่อย (5 ข้อ) ───
    {
        "id": 16, "category": CATEGORY,
        "question": "ติดต่อเรื่องตารางเรียนที่ไหน",
        "expected_keywords": [],
        "alt_keywords": ["055-968312", "หน่วยตาราง"],
        "ground_truth": "หน่วยตารางเรียน 0-5596-8312",
        "is_oos": False,
    },
    {
        "id": 17, "category": CATEGORY,
        "question": "เบอร์งานพัฒนาหลักสูตร",
        "expected_keywords": [],
        "alt_keywords": ["055-968318", "055-968306", "055-968307"],
        "ground_truth": "0-5596-8318",
        "is_oos": False,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "ติดต่องานรับเข้าศึกษา",
        "expected_keywords": [],
        "alt_keywords": ["055-968304", "055-968309", "รับเข้า"],
        "ground_truth": "0-5596-8304, 0-5596-8309",
        "is_oos": False,
    },
    {
        "id": 19, "category": CATEGORY,
        "question": "ติดต่อหน่วยทะเบียนนิสิต",
        "expected_keywords": [],
        "alt_keywords": ["055-968300", "ทะเบียน"],
        "ground_truth": "งานทะเบียนนิสิต 0-5596-8300",
        "is_oos": False,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "ติดต่อภาควิชาทางไหนได้บ้าง",
        "expected_keywords": [],
        "alt_keywords": ["055-963262", "055-963263", "โทร", "อีเมล"],
        "ground_truth": "โทร 055-963262, 055-963263",
        "is_oos": False,
    },
]
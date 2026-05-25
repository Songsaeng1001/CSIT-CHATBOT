"""20 คำถามหมวด กยศ."""

CATEGORY = "loan"
CATEGORY_TH = "กยศ."

QUESTIONS = [
    # ─── ชั่วโมงจิตอาสา (5 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "กยศ. ต้องทำจิตอาสากี่ชั่วโมง",
        "expected_keywords": ["36"],
        "alt_keywords": ["ชั่วโมง"],
        "ground_truth": "อย่างน้อย 36 ชั่วโมง/ปี",
        "is_oos": False,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "ชั่วโมงจิตอาสากยศ.ต่อปีเท่าไร",
        "expected_keywords": ["36"],
        "alt_keywords": ["ชั่วโมง", "ปี"],
        "ground_truth": "36 ชั่วโมงต่อปี",
        "is_oos": False,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "ช่วงเวลานับชั่วโมงจิตอาสา",
        "expected_keywords": [],
        "alt_keywords": ["พฤษภาคม", "เมษายน"],
        "ground_truth": "1 พฤษภาคม - 30 เมษายนของปีถัดไป",
        "is_oos": False,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "ทำจิตอาสาน้อยกว่า 36 ชั่วโมงได้ไหม",
        "expected_keywords": [],
        "alt_keywords": ["ไม่ได้", "อย่างน้อย", "ต้อง"],
        "ground_truth": "ไม่ได้ ต้องอย่างน้อย 36 ชั่วโมง",
        "is_oos": False,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "จิตอาสาเริ่มนับเมื่อไหร่",
        "expected_keywords": [],
        "alt_keywords": ["1 พฤษภาคม", "พฤษภาคม"],
        "ground_truth": "1 พฤษภาคม",
        "is_oos": False,
    },

    # ─── ขั้นตอนสมัคร (5 ข้อ) ───
    {
        "id": 6, "category": CATEGORY,
        "question": "ขั้นตอนสมัครกยศ.",
        "expected_keywords": [],
        "alt_keywords": ["ลงทะเบียน", "ยื่น", "DSL", "เอกสาร"],
        "ground_truth": "ลงทะเบียนระบบ DSL + ยื่นเอกสาร",
        "is_oos": False,
    },
    {
        "id": 7, "category": CATEGORY,
        "question": "ระบบ DSL คืออะไร",
        "expected_keywords": [],
        "alt_keywords": ["กู้ยืม", "ระบบ", "ออนไลน์"],
        "ground_truth": "ระบบกู้ยืมกยศ.ออนไลน์",
        "is_oos": False,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "สมัครกยศ.ที่ไหน",
        "expected_keywords": [],
        "alt_keywords": ["DSL", "studentloan", "ออนไลน์", "ระบบ"],
        "ground_truth": "ระบบ DSL ออนไลน์",
        "is_oos": False,
    },
    {
        "id": 9, "category": CATEGORY,
        "question": "เว็บกยศ.กลางคืออะไร",
        "expected_keywords": [],
        "alt_keywords": ["wsa.dsl", "studentloan"],
        "ground_truth": "wsa.dsl.studentloan.or.th",
        "is_oos": False,
    },
    {
        "id": 10, "category": CATEGORY,
        "question": "เอกสารสมัครกยศ.มีอะไรบ้าง",
        "expected_keywords": [],
        "alt_keywords": ["เอกสาร", "บัตร", "หลักฐาน"],
        "ground_truth": "เอกสารหลักฐาน + ใบสมัคร",
        "is_oos": False,
    },

    # ─── เงื่อนไข + ระเบียบ (5 ข้อ) ───
    {
        "id": 11, "category": CATEGORY,
        "question": "ใครมีสิทธิ์กู้กยศ.",
        "expected_keywords": [],
        "alt_keywords": ["รายได้", "เกณฑ์", "นิสิต"],
        "ground_truth": "นิสิตที่มีรายได้ครอบครัวตามเกณฑ์",
        "is_oos": False,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "กยศ.ผิดนัดทำยังไง",
        "expected_keywords": [],
        "alt_keywords": ["ค่าปรับ", "ติดต่อ", "ผ่อน", "ดอกเบี้ย"],
        "ground_truth": "อาจมีค่าปรับ ติดต่อกยศ.",
        "is_oos": False,
    },
    {
        "id": 13, "category": CATEGORY,
        "question": "ดอกเบี้ยกยศ.เท่าไร",
        "expected_keywords": [],
        "alt_keywords": ["ดอกเบี้ย", "ต่ำ", "%"],
        "ground_truth": "ดอกเบี้ยต่ำตามที่กยศ.กำหนด",
        "is_oos": False,
    },
    {
        "id": 14, "category": CATEGORY,
        "question": "กยศ.กู้ได้กี่บาท",
        "expected_keywords": [],
        "alt_keywords": ["กู้", "เพดาน", "วงเงิน", "บาท"],
        "ground_truth": "ตามวงเงินที่กยศ.กำหนด",
        "is_oos": False,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "ใช้คืนกยศ.เมื่อไหร่",
        "expected_keywords": [],
        "alt_keywords": ["จบ", "ทำงาน", "หลัง"],
        "ground_truth": "หลังจบการศึกษา 2 ปี",
        "is_oos": False,
    },

    # ─── เว็บไซต์ + ติดต่อ (5 ข้อ) ───
    {
        "id": 16, "category": CATEGORY,
        "question": "เว็บไซต์กยศ.มหาวิทยาลัยนเรศวร",
        "expected_keywords": [],
        "alt_keywords": ["acad.nu.ac.th", "studentloan"],
        "ground_truth": "acad.nu.ac.th/studentloan",
        "is_oos": False,
    },
    {
        "id": 17, "category": CATEGORY,
        "question": "ติดต่อกยศ.มหาวิทยาลัยที่ไหน",
        "expected_keywords": [],
        "alt_keywords": ["กองบริการ", "ม.นเรศวร", "acad"],
        "ground_truth": "กองบริการการศึกษา ม.นเรศวร",
        "is_oos": False,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "ถามเรื่องกยศ.ติดต่อใคร",
        "expected_keywords": [],
        "alt_keywords": ["กองบริการ", "acad", "กยศ"],
        "ground_truth": "กองบริการการศึกษา หรือเว็บกยศ.",
        "is_oos": False,
    },
    {
        "id": 19, "category": CATEGORY,
        "question": "ลืมรหัสเข้าระบบ DSL ทำยังไง",
        "expected_keywords": [],
        "alt_keywords": ["ติดต่อ", "รีเซ็ต", "DSL"],
        "ground_truth": "ติดต่อกยศ.หรือรีเซ็ตรหัส",
        "is_oos": False,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "กยศ.ใช้คืนช้าทำไง",
        "expected_keywords": [],
        "alt_keywords": ["ติดต่อ", "ผ่อน", "ค่าปรับ"],
        "ground_truth": "ติดต่อกยศ.เพื่อขอผ่อนผัน",
        "is_oos": False,
    },
]
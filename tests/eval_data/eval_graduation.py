"""20 คำถามหมวดสำเร็จการศึกษา + เกียรตินิยม"""

CATEGORY = "graduation"
CATEGORY_TH = "สำเร็จการศึกษา"

QUESTIONS = [
    # ─── เกียรตินิยม (8 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "เกียรตินิยมอันดับ 1 ต้อง GPA เท่าไร",
        "expected_keywords": ["3.50"],
        "alt_keywords": [],
        "ground_truth": "GPA 3.50 ขึ้นไป",
        "is_oos": False,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "เกียรตินิยมอันดับ 2 ต้อง GPA เท่าไร",
        "expected_keywords": ["3.25"],
        "alt_keywords": ["3.49"],
        "ground_truth": "GPA 3.25-3.49",
        "is_oos": False,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "GPA 3.55 ได้เกียรตินิยมอะไร",
        "expected_keywords": ["เกียรตินิยมอันดับหนึ่ง"],
        "alt_keywords": [],
        "ground_truth": "เกียรตินิยมอันดับหนึ่ง",
        "is_oos": False,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "GPA 3.30 ได้เกียรตินิยมอะไร",
        "expected_keywords": ["เกียรตินิยมอันดับสอง"],
        "alt_keywords": [],
        "ground_truth": "เกียรตินิยมอันดับสอง",
        "is_oos": False,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "GPA 3.75 ได้เกียรตินิยมไหม",
        "expected_keywords": ["เกียรตินิยมอันดับหนึ่ง"],
        "alt_keywords": [],
        "ground_truth": "เกียรตินิยมอันดับหนึ่ง",
        "is_oos": False,
    },
    {
        "id": 6, "category": CATEGORY,
        "question": "GPA 3.20 ได้เกียรตินิยมไหม",
        "expected_keywords": [],
        "alt_keywords": ["ไม่ได้", "ไม่ถึง"],
        "ground_truth": "ไม่ได้ ต้อง ≥ 3.25",
        "is_oos": False,
    },
    {
        "id": 7, "category": CATEGORY,
        "question": "เงื่อนไขเกียรตินิยมอันดับ 1 มีอะไรบ้าง",
        "expected_keywords": [],
        "alt_keywords": ["3.50", "F", "U", "ซ้ำ"],
        "ground_truth": "GPA 3.50+ ไม่เคยได้ F/U ไม่เคยซ้ำชั้น",
        "is_oos": False,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "เคยได้ F ได้เกียรตินิยมไหม",
        "expected_keywords": [],
        "alt_keywords": ["ไม่ได้", "ไม่"],
        "ground_truth": "ไม่ได้ เกียรตินิยมต้องไม่เคยได้ F/U",
        "is_oos": False,
    },

    # ─── ค่าธรรมเนียมจบ (4 ข้อ) ───
    {
        "id": 9, "category": CATEGORY,
        "question": "ค่ายื่นจบกี่บาท",
        "expected_keywords": ["2,000"],
        "alt_keywords": ["ป.ตรี"],
        "ground_truth": "ป.ตรี 2,000 บาท",
        "is_oos": False,
    },
    {
        "id": 10, "category": CATEGORY,
        "question": "ค่าธรรมเนียมขึ้นทะเบียนปริญญาบัตรเท่าไร",
        "expected_keywords": ["2,000"],
        "alt_keywords": ["ปริญญาบัตร"],
        "ground_truth": "ป.ตรี 2,000 บาท",
        "is_oos": False,
    },
    {
        "id": 11, "category": CATEGORY,
        "question": "ค่าจบบัณฑิตศึกษาเท่าไร",
        "expected_keywords": ["2,500"],
        "alt_keywords": [],
        "ground_truth": "2,500 บาท",
        "is_oos": False,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "ยื่นสำเร็จการศึกษาช้าค่าปรับเท่าไร",
        "expected_keywords": ["50"],
        "alt_keywords": ["บาท", "วัน"],
        "ground_truth": "50 บาท/วันทำการ",
        "is_oos": False,
    },

    # ─── NU forms จบ (4 ข้อ) ───
    {
        "id": 13, "category": CATEGORY,
        "question": "NU25 ใช้ทำอะไร",
        "expected_keywords": ["สำเร็จการศึกษา"],
        "alt_keywords": [],
        "ground_truth": "แบบขอสำเร็จการศึกษา",
        "is_oos": False,
    },
    {
        "id": 14, "category": CATEGORY,
        "question": "NU9 ใช้ทำอะไร",
        "expected_keywords": [],
        "alt_keywords": ["สำเร็จการศึกษา", "ล่าช้า"],
        "ground_truth": "ยื่นสำเร็จการศึกษาล่าช้า",
        "is_oos": False,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "ฟอร์มยื่นจบคืออะไร",
        "expected_keywords": ["NU25"],
        "alt_keywords": [],
        "ground_truth": "NU25",
        "is_oos": False,
    },
    {
        "id": 16, "category": CATEGORY,
        "question": "ยื่นจบช้าใช้ฟอร์มอะไร",
        "expected_keywords": ["NU9"],
        "alt_keywords": [],
        "ground_truth": "NU9",
        "is_oos": False,
    },

    # ─── เงื่อนไขจบการศึกษา (4 ข้อ) ───
    {
        "id": 17, "category": CATEGORY,
        "question": "GPA ขั้นต่ำจบการศึกษาเท่าไร",
        "expected_keywords": ["2.00"],
        "alt_keywords": [],
        "ground_truth": "GPA ≥ 2.00",
        "is_oos": False,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "ต้องยื่นจบก่อนเปิดเทอมกี่สัปดาห์",
        "expected_keywords": ["4"],
        "alt_keywords": ["สัปดาห์"],
        "ground_truth": "ภายใน 4 สัปดาห์หลังเปิดเทอม",
        "is_oos": False,
    },
    {
        "id": 19, "category": CATEGORY,
        "question": "GPA 1.65 หลังเรียน 3 ภาคเป็นยังไง",
        "expected_keywords": [],
        "alt_keywords": ["พ้นสภาพ", "ต่ำ", "ไม่ถึง"],
        "ground_truth": "พ้นสภาพ GPA < 1.75",
        "is_oos": False,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "เงื่อนไขจบหลักสูตรปริญญาตรีคืออะไร",
        "expected_keywords": [],
        "alt_keywords": ["2.00", "หน่วยกิต", "ครบ"],
        "ground_truth": "เรียนครบหน่วยกิต + GPA ≥ 2.00",
        "is_oos": False,
    },
]
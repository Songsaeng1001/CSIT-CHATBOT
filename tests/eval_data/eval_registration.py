"""20 คำถามหมวดการลงทะเบียน"""

CATEGORY = "registration"
CATEGORY_TH = "ลงทะเบียน"

QUESTIONS = [
    # ─── ค่าปรับลงทะเบียนช้า (6 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "ค่าปรับลงทะเบียนช้าวันละเท่าไร",
        "expected_keywords": ["25"],
        "alt_keywords": ["บาท"],
        "ground_truth": "วันละ 25 บาท",
        "is_oos": False,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "ลงทะเบียนช้า 5 วัน เสียเท่าไร",
        "expected_keywords": ["125"],
        "alt_keywords": [],
        "ground_truth": "125 บาท (5 × 25)",
        "is_oos": False,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "ลงทะเบียนช้า 7 วัน ต้องจ่ายเท่าไร",
        "expected_keywords": ["175"],
        "alt_keywords": [],
        "ground_truth": "175 บาท (7 × 25)",
        "is_oos": False,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "ลงทะเบียนช้า 10 วัน เสียเท่าไร",
        "expected_keywords": ["250"],
        "alt_keywords": [],
        "ground_truth": "250 บาท (10 × 25)",
        "is_oos": False,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "ลงทะเบียนช้า 14 วันได้ไหม",
        "expected_keywords": [],
        "alt_keywords": ["350", "ครบ", "ใกล้", "พ้นสภาพ"],
        "ground_truth": "350 บาท ใกล้ครบ 14 วัน",
        "is_oos": False,
    },
    {
        "id": 6, "category": CATEGORY,
        "question": "ลงทะเบียนช้า 20 วันทำยังไง",
        "expected_keywords": [],
        "alt_keywords": ["พ้นสภาพ", "NU7", "คืนสภาพ"],
        "ground_truth": "พ้นสภาพ ต้องยื่น NU7",
        "is_oos": False,
    },

    # ─── หน่วยกิตเกินกำหนด (4 ข้อ) ───
    {
        "id": 7, "category": CATEGORY,
        "question": "ลง 24 หน่วยกิตได้ไหม",
        "expected_keywords": ["NU18"],
        "alt_keywords": ["เกิน"],
        "ground_truth": "เกิน 22 ต้องยื่น NU18",
        "is_oos": False,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "ลง 18 หน่วยกิตได้ไหม",
        "expected_keywords": [],
        "alt_keywords": ["ลงได้", "ปกติ"],
        "ground_truth": "ลงได้ปกติ",
        "is_oos": False,
    },
    {
        "id": 9, "category": CATEGORY,
        "question": "ลงทะเบียนเกิน 22 หน่วยกิตทำยังไง",
        "expected_keywords": ["NU18"],
        "alt_keywords": ["คำร้อง"],
        "ground_truth": "ยื่น NU18 ผ่านอาจารย์ที่ปรึกษา",
        "is_oos": False,
    },
    {
        "id": 10, "category": CATEGORY,
        "question": "ภาคฤดูร้อนลงเกิน 9 หน่วยกิตได้ไหม",
        "expected_keywords": [],
        "alt_keywords": ["NU18", "ไม่ได้", "เกิน"],
        "ground_truth": "ต้องยื่น NU18",
        "is_oos": False,
    },

    # ─── NU forms ลงทะเบียน (5 ข้อ) ───
    {
        "id": 11, "category": CATEGORY,
        "question": "NU11 ใช้ทำอะไร",
        "expected_keywords": [],
        "alt_keywords": ["ถอน", "W"],
        "ground_truth": "ถอนรายวิชา (ติด W)",
        "is_oos": False,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "NU18 ใช้ทำอะไร",
        "expected_keywords": [],
        "alt_keywords": ["คำร้องทั่วไป", "เกิน", "หน่วยกิต"],
        "ground_truth": "คำร้องทั่วไป ขอลงเกินหน่วยกิต",
        "is_oos": False,
    },
    {
        "id": 13, "category": CATEGORY,
        "question": "NU8 ใช้ทำอะไร",
        "expected_keywords": [],
        "alt_keywords": ["เพิ่ม", "รายวิชา", "ล่าช้า"],
        "ground_truth": "เพิ่มรายวิชาหลังกำหนด",
        "is_oos": False,
    },
    {
        "id": 14, "category": CATEGORY,
        "question": "NU14 ใช้ทำอะไร",
        "expected_keywords": [],
        "alt_keywords": ["เทียบโอน", "รายวิชา"],
        "ground_truth": "เทียบโอนรายวิชา",
        "is_oos": False,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "ฟอร์มที่ใช้ขอเทียบโอนคืออะไร",
        "expected_keywords": ["NU14"],
        "alt_keywords": [],
        "ground_truth": "NU14",
        "is_oos": False,
    },

    # ─── ขั้นตอน + ระยะเวลา (5 ข้อ) ───
    {
        "id": 16, "category": CATEGORY,
        "question": "ระยะเวลาลงทะเบียนล่าช้าได้กี่สัปดาห์",
        "expected_keywords": ["2"],
        "alt_keywords": ["สัปดาห์"],
        "ground_truth": "2 สัปดาห์แรกของภาคปกติ",
        "is_oos": False,
    },
    {
        "id": 17, "category": CATEGORY,
        "question": "ลงทะเบียนล่าช้าภาคฤดูร้อนได้กี่สัปดาห์",
        "expected_keywords": ["1"],
        "alt_keywords": ["สัปดาห์"],
        "ground_truth": "1 สัปดาห์",
        "is_oos": False,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "ลงทะเบียนเรียนผ่านระบบไหน",
        "expected_keywords": [],
        "alt_keywords": ["reg.nu.ac.th", "ออนไลน์", "ทะเบียน"],
        "ground_truth": "ระบบทะเบียนออนไลน์ reg.nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 19, "category": CATEGORY,
        "question": "ถอนรายวิชาล่าช้าได้ถึงสัปดาห์ที่เท่าไร",
        "expected_keywords": [],
        "alt_keywords": ["12", "สัปดาห์"],
        "ground_truth": "ไม่เกินสัปดาห์ที่ 12",
        "is_oos": False,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "ลงทะเบียนเรียนเพิ่มเติมทำยังไง",
        "expected_keywords": [],
        "alt_keywords": ["NU8", "เพิ่ม", "รายวิชา"],
        "ground_truth": "ยื่น NU8 เพิ่มรายวิชา",
        "is_oos": False,
    },
]
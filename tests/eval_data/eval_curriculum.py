"""20 คำถามหมวดหลักสูตร CS/IT"""

CATEGORY = "curriculum"
CATEGORY_TH = "หลักสูตร"

QUESTIONS = [
    # ─── หน่วยกิตและโครงสร้างหลักสูตร (8 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "หลักสูตร CS เรียนกี่หน่วยกิต",
        "expected_keywords": ["123"],
        "alt_keywords": ["หน่วยกิต"],
        "ground_truth": "หลักสูตร CS เรียน 123 หน่วยกิต",
        "is_oos": False,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "หลักสูตร IT เรียนกี่หน่วยกิต",
        "expected_keywords": ["126"],
        "alt_keywords": ["หน่วยกิต"],
        "ground_truth": "หลักสูตร IT เรียน 126 หน่วยกิต",
        "is_oos": False,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "วิทยาการคอมพิวเตอร์เรียนกี่หน่วยกิต",
        "expected_keywords": ["123"],
        "alt_keywords": ["CS"],
        "ground_truth": "วิทยาการคอมพิวเตอร์ (CS) เรียน 123 หน่วยกิต",
        "is_oos": False,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "เทคโนโลยีสารสนเทศเรียนกี่หน่วยกิต",
        "expected_keywords": ["126"],
        "alt_keywords": ["IT"],
        "ground_truth": "เทคโนโลยีสารสนเทศ (IT) เรียน 126 หน่วยกิต",
        "is_oos": False,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "หลักสูตร CS กับ IT ต่างกันยังไง",
        "expected_keywords": [],
        "alt_keywords": ["ทฤษฎี", "ซอฟต์แวร์", "เทคโนโลยี", "ระบบ"],
        "ground_truth": "CS เน้นทฤษฎี+ซอฟต์แวร์เชิงลึก IT เน้นประยุกต์เทคโนโลยี",
        "is_oos": False,
    },
    {
        "id": 6, "category": CATEGORY,
        "question": "ระดับปริญญาตรีลงได้สูงสุดกี่หน่วยกิตต่อภาค",
        "expected_keywords": ["22"],
        "alt_keywords": ["หน่วยกิต"],
        "ground_truth": "22 หน่วยกิตต่อภาคปกติ",
        "is_oos": False,
    },
    {
        "id": 7, "category": CATEGORY,
        "question": "ภาคฤดูร้อนลงได้กี่หน่วยกิต",
        "expected_keywords": ["9"],
        "alt_keywords": ["หน่วยกิต", "ฤดูร้อน"],
        "ground_truth": "9 หน่วยกิตต่อภาคฤดูร้อน",
        "is_oos": False,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "หลักสูตรใช้ระบบการเรียนแบบไหน",
        "expected_keywords": ["ทวิภาค"],
        "alt_keywords": ["2 ภาค"],
        "ground_truth": "ใช้ระบบทวิภาค ปีละ 2 ภาคการศึกษา",
        "is_oos": False,
    },

    # ─── ปฏิทินการศึกษา (4 ข้อ) ───
    {
        "id": 9, "category": CATEGORY,
        "question": "ภาคต้นเปิดเรียนเดือนไหน",
        "expected_keywords": [],
        "alt_keywords": ["มิถุนายน", "ตุลาคม"],
        "ground_truth": "ภาคต้นเปิดมิถุนายน-ตุลาคม",
        "is_oos": False,
    },
    {
        "id": 10, "category": CATEGORY,
        "question": "ภาคปลายเรียนช่วงไหน",
        "expected_keywords": [],
        "alt_keywords": ["พฤศจิกายน", "มีนาคม"],
        "ground_truth": "ภาคปลายเรียนพฤศจิกายน-มีนาคม",
        "is_oos": False,
    },
    {
        "id": 11, "category": CATEGORY,
        "question": "1 ปีการศึกษามีกี่ภาค",
        "expected_keywords": ["2"],
        "alt_keywords": ["ภาค"],
        "ground_truth": "2 ภาคการศึกษาต่อปี (ระบบทวิภาค)",
        "is_oos": False,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "ภาคฤดูร้อนคืออะไร",
        "expected_keywords": [],
        "alt_keywords": ["ฤดูร้อน", "ภาคพิเศษ", "9 หน่วยกิต"],
        "ground_truth": "ภาคพิเศษ ลงได้สูงสุด 9 หน่วยกิต",
        "is_oos": False,
    },

    # ─── หน่วยกิตและเกรด (4 ข้อ) ───
    {
        "id": 13, "category": CATEGORY,
        "question": "ลง 18 หน่วยกิตได้ไหม",
        "expected_keywords": [],
        "alt_keywords": ["ลงได้", "ปกติ", "ภายในเกณฑ์"],
        "ground_truth": "ลงได้ปกติ ขีดจำกัด 22 หน่วยกิต",
        "is_oos": False,
    },
    {
        "id": 14, "category": CATEGORY,
        "question": "ลง 24 หน่วยกิตได้ไหม",
        "expected_keywords": ["NU18"],
        "alt_keywords": ["เกิน", "มากกว่า"],
        "ground_truth": "เกิน 22 หน่วยกิต ต้องยื่น NU18",
        "is_oos": False,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "ลงเรียน 23 หน่วยกิตได้ไหม",
        "expected_keywords": ["NU18"],
        "alt_keywords": ["เกิน"],
        "ground_truth": "เกิน 22 หน่วยกิต ต้องยื่น NU18",
        "is_oos": False,
    },
    {
        "id": 16, "category": CATEGORY,
        "question": "ลง 20 หน่วยกิตได้ไหม",
        "expected_keywords": [],
        "alt_keywords": ["ลงได้", "ปกติ", "ภายในเกณฑ์"],
        "ground_truth": "ลงได้ปกติ ภายในเกณฑ์ 22 หน่วยกิต",
        "is_oos": False,
    },

    # ─── ความรู้ทั่วไปเกี่ยวกับหลักสูตร (4 ข้อ) ───
    {
        "id": 17, "category": CATEGORY,
        "question": "ภาควิชา CSIT อยู่คณะอะไร",
        "expected_keywords": [],
        "alt_keywords": ["วิทยาศาสตร์", "คณะ"],
        "ground_truth": "คณะวิทยาศาสตร์ มหาวิทยาลัยนเรศวร",
        "is_oos": False,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "หลักสูตรของภาควิชาเป็นภาษาอะไร",
        "expected_keywords": [],
        "alt_keywords": ["ไทย", "ภาษาไทย"],
        "ground_truth": "ภาษาไทย",
        "is_oos": False,
    },
    {
        "id": 19, "category": CATEGORY,
        "question": "เรียน CS หรือ IT ดีกว่ากัน",
        "expected_keywords": [],
        "alt_keywords": ["CS", "IT", "ทฤษฎี", "เทคโนโลยี", "ความสนใจ"],
        "ground_truth": "ขึ้นกับความสนใจ CS=ทฤษฎี IT=ประยุกต์",
        "is_oos": False,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "หลักสูตร CSIT มีคำว่าอะไรย่อมาจาก",
        "expected_keywords": [],
        "alt_keywords": ["Computer Science", "Information Technology", "วิทยาการคอมพิวเตอร์"],
        "ground_truth": "Computer Science และ Information Technology",
        "is_oos": False,
    },
]
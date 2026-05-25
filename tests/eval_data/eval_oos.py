"""20 คำถาม Out-of-Scope (ต้องปฏิเสธทั้งหมด)"""

CATEGORY = "oos"
CATEGORY_TH = "Out-of-Scope"

# คำถามเหล่านี้ทุกข้อ — น้องซีทีต้องตอบ "ไม่มีข้อมูล"
# is_oos = True ทุกข้อ
QUESTIONS = [
    # ─── อาหารและไลฟ์สไตล์ (5 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "ขนมจีนน้ำยาราคาเท่าไร",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย", "ติดต่อ"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "วิธีทำผัดไทย",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "ร้านอาหารใกล้มหาลัย",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "วันนี้กินอะไรดี",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "หนังเรื่องไหนน่าดู",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },

    # ─── เทคโนโลยี/สินค้า (5 ข้อ) ───
    {
        "id": 6, "category": CATEGORY,
        "question": "ราคา iPhone 15",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 7, "category": CATEGORY,
        "question": "MacBook กับ Windows ดีกว่ากัน",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "ราคา Notebook gaming",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 9, "category": CATEGORY,
        "question": "วิธีเขียนเรซูเม่",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 10, "category": CATEGORY,
        "question": "สมัครงานยังไง",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },

    # ─── ทั่วไป (5 ข้อ) ───
    {
        "id": 11, "category": CATEGORY,
        "question": "พรุ่งนี้อากาศเป็นยังไง",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "วิธีลดน้ำหนัก",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 13, "category": CATEGORY,
        "question": "ทำไมแมวชอบกล่อง",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 14, "category": CATEGORY,
        "question": "เพลงที่ฮิตที่สุดปีนี้",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "ที่เที่ยวพิษณุโลก",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },

    # ─── ภาษา/แปล (3 ข้อ) ───
    {
        "id": 16, "category": CATEGORY,
        "question": "สอนภาษาอังกฤษพื้นฐาน",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 17, "category": CATEGORY,
        "question": "แปลคำว่า love เป็นไทย",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "พูดญี่ปุ่นสวัสดียังไง",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },

    # ─── คณะอื่น (2 ข้อ) ───
    {
        "id": 19, "category": CATEGORY,
        "question": "คณะแพทย์เรียนกี่ปี",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "คณะวิศวกรรมศาสตร์ดีไหม",
        "expected_keywords": [], "alt_keywords": ["ไม่มีข้อมูล", "ขออภัย"],
        "ground_truth": "ปฏิเสธ - นอก scope",
        "is_oos": True,
    },
]
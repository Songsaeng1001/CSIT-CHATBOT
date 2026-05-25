"""20 คำถามหมวดอาจารย์ + เจ้าหน้าที่"""

CATEGORY = "staff"
CATEGORY_TH = "อาจารย์/เจ้าหน้าที่"

QUESTIONS = [
    # ─── ห้องทำงานอาจารย์ (8 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "อาจารย์เกรียงศักดิ์ห้องอะไร",
        "expected_keywords": ["SC2-401"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-401",
        "is_oos": False,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "อาจารย์จักรกฤษณ์อยู่ห้องไหน",
        "expected_keywords": ["SC2-301"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-301",
        "is_oos": False,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "อาจารย์ไกรศักดิ์ห้องอะไร",
        "expected_keywords": ["SC2-401"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-401",
        "is_oos": False,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "อาจารย์สัญญาห้องอะไร",
        "expected_keywords": ["SC2-306"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-306",
        "is_oos": False,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "อาจารย์จันทร์จิราห้องอะไร",
        "expected_keywords": ["SC2-217"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-217",
        "is_oos": False,
    },
    {
        "id": 6, "category": CATEGORY,
        "question": "อาจารย์อนงค์พรห้องอะไร",
        "expected_keywords": ["SC2-406"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-406",
        "is_oos": False,
    },
    {
        "id": 7, "category": CATEGORY,
        "question": "อาจารย์อดิเรกห้องอะไร",
        "expected_keywords": ["SC2-401"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-401",
        "is_oos": False,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "อาจารย์เทวินห้องอะไร",
        "expected_keywords": ["SC2-406"],
        "alt_keywords": [],
        "ground_truth": "ห้อง SC2-406",
        "is_oos": False,
    },

    # ─── อีเมล + ติดต่อ (5 ข้อ) ───
    {
        "id": 9, "category": CATEGORY,
        "question": "อีเมลอาจารย์เกรียงศักดิ์",
        "expected_keywords": ["kreangsakt"],
        "alt_keywords": ["nu.ac.th"],
        "ground_truth": "kreangsakt@nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 10, "category": CATEGORY,
        "question": "อีเมลอาจารย์สัญญา",
        "expected_keywords": ["sanyak"],
        "alt_keywords": ["nu.ac.th"],
        "ground_truth": "sanyak@nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 11, "category": CATEGORY,
        "question": "อีเมลอาจารย์อดิเรก",
        "expected_keywords": ["adirekr"],
        "alt_keywords": ["nu.ac.th"],
        "ground_truth": "adirekr@nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "อีเมลอาจารย์ไกรศักดิ์",
        "expected_keywords": ["kraisakk"],
        "alt_keywords": ["nu.ac.th"],
        "ground_truth": "kraisakk@nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 13, "category": CATEGORY,
        "question": "ใครเป็นที่ปรึกษาวิทยานิพนธ์น้องซีที",
        "expected_keywords": ["เกรียงศักดิ์"],
        "alt_keywords": [],
        "ground_truth": "ผศ.ดร.เกรียงศักดิ์ เตมีย์",
        "is_oos": False,
    },

    # ─── เจ้าหน้าที่ภาควิชา (5 ข้อ) ───
    {
        "id": 14, "category": CATEGORY,
        "question": "พี่เฟิร์นเบอร์อะไร",
        "expected_keywords": ["055-963262"],
        "alt_keywords": [],
        "ground_truth": "พี่เฟิร์น 055-963262",
        "is_oos": False,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "พี่แมวตำแหน่งอะไร",
        "expected_keywords": [],
        "alt_keywords": ["พัสดุ", "นักวิชาการ"],
        "ground_truth": "นักวิชาการพัสดุ",
        "is_oos": False,
    },
    {
        "id": 16, "category": CATEGORY,
        "question": "เจ้าหน้าที่ภาควิชา CSIT มีใครบ้าง",
        "expected_keywords": [],
        "alt_keywords": ["พี่เฟิร์น", "พี่แมว", "พี่โอ๊ต", "พี่ยุทธ"],
        "ground_truth": "พี่เฟิร์น พี่แมว พี่โอ๊ต พี่ยุทธ",
        "is_oos": False,
    },
    {
        "id": 17, "category": CATEGORY,
        "question": "พี่โอ๊ตทำหน้าที่อะไร",
        "expected_keywords": [],
        "alt_keywords": ["คอมพิวเตอร์", "นักวิชาการ"],
        "ground_truth": "นักวิชาการคอมพิวเตอร์",
        "is_oos": False,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "พี่ยุทธทำหน้าที่อะไร",
        "expected_keywords": [],
        "alt_keywords": ["ช่าง", "เทคนิค"],
        "ground_truth": "นายช่างเทคนิค",
        "is_oos": False,
    },

    # ─── รายชื่ออาจารย์ทั่วไป (2 ข้อ) ───
    {
        "id": 19, "category": CATEGORY,
        "question": "รายชื่ออาจารย์ภาควิชา CSIT ทั้งหมด",
        "expected_keywords": [],
        "alt_keywords": ["20", "อาจารย์"],
        "ground_truth": "อาจารย์ภาควิชา CSIT มีทั้งหมด 20 ท่าน",
        "is_oos": False,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "อาจารย์ในภาควิชา CSIT มีกี่ท่าน",
        "expected_keywords": ["20"],
        "alt_keywords": [],
        "ground_truth": "20 ท่าน",
        "is_oos": False,
    },
]
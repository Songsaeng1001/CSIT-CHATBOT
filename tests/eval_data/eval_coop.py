"""20 คำถามหมวดสหกิจศึกษา (Co-op Education)"""

CATEGORY = "coop"
CATEGORY_TH = "สหกิจศึกษา"

QUESTIONS = [
    # ─── Coop01 + ขั้นตอนสมัคร (6 ข้อ) ───
    {
        "id": 1, "category": CATEGORY,
        "question": "Coop01 คืออะไร",
        "expected_keywords": [],
        "alt_keywords": ["ใบสมัคร", "สหกิจ", "ฟอร์ม"],
        "ground_truth": "ใบสมัครปฏิบัติสหกิจศึกษาของคณะวิทยาศาสตร์",
        "is_oos": False,
    },
    {
        "id": 2, "category": CATEGORY,
        "question": "รหัสฟอร์ม Coop01 คืออะไร",
        "expected_keywords": [],
        "alt_keywords": ["SC_Co-op 01", "SC", "Co-op"],
        "ground_truth": "SC_Co-op 01",
        "is_oos": False,
    },
    {
        "id": 3, "category": CATEGORY,
        "question": "ระยะเวลาปฏิบัติสหกิจกี่เดือน",
        "expected_keywords": ["4"],
        "alt_keywords": ["เดือน"],
        "ground_truth": "4 เดือน",
        "is_oos": False,
    },
    {
        "id": 4, "category": CATEGORY,
        "question": "ขนาดรูปถ่ายใน Coop01",
        "expected_keywords": ["1"],
        "alt_keywords": ["นิ้ว", "ชุดนิสิต"],
        "ground_truth": "1 นิ้ว ชุดนิสิต",
        "is_oos": False,
    },
    {
        "id": 5, "category": CATEGORY,
        "question": "อบรมสหกิจกี่ชั่วโมง",
        "expected_keywords": ["30"],
        "alt_keywords": ["ชั่วโมง"],
        "ground_truth": "30 ชั่วโมง",
        "is_oos": False,
    },
    {
        "id": 6, "category": CATEGORY,
        "question": "สมัครสหกิจที่เว็บไหน",
        "expected_keywords": [],
        "alt_keywords": ["sci.nu.ac.th", "coop", "MIS"],
        "ground_truth": "https://www.sci.nu.ac.th/coop/",
        "is_oos": False,
    },
    
    # ─── เอกสารที่ต้องแนบ (4 ข้อ) ───
    {
        "id": 7, "category": CATEGORY,
        "question": "เอกสารที่ต้องแนบกับ Coop01",
        "expected_keywords": [],
        "alt_keywords": ["Resume", "Transcript", "Activity"],
        "ground_truth": "Resume, Transcript, Activity Transcript",
        "is_oos": False,
    },
    {
        "id": 8, "category": CATEGORY,
        "question": "ต้องแนบ Resume กับ Coop01 ไหม",
        "expected_keywords": [],
        "alt_keywords": ["ต้อง", "Resume", "ใช่"],
        "ground_truth": "ต้องแนบ Resume",
        "is_oos": False,
    },
    {
        "id": 9, "category": CATEGORY,
        "question": "ถ้าเอกสารไม่ครบจะเป็นยังไง",
        "expected_keywords": [],
        "alt_keywords": ["ไม่จัดทำ", "ไม่ดำเนินการ", "ไม่อนุเคราะห์"],
        "ground_truth": "คณะจะไม่จัดทำหนังสือขอความอนุเคราะห์ให้",
        "is_oos": False,
    },
    {
        "id": 10, "category": CATEGORY,
        "question": "Activity Transcript คืออะไร",
        "expected_keywords": [],
        "alt_keywords": ["กิจกรรม", "ผลการเข้าร่วม"],
        "ground_truth": "ใบแสดงผลการเข้าร่วมกิจกรรม",
        "is_oos": False,
    },
    
    # ─── Resume (6 ข้อ) ───
    {
        "id": 11, "category": CATEGORY,
        "question": "Resume ควรมีอะไรบ้าง",
        "expected_keywords": [],
        "alt_keywords": ["รูปถ่าย", "ข้อมูลส่วนตัว", "การศึกษา", "ทักษะ", "ประสบการณ์"],
        "ground_truth": "รูปถ่าย ข้อมูลส่วนตัว การศึกษา ทักษะ ประสบการณ์ จุดมุ่งหมาย บุคคลอ้างอิง",
        "is_oos": False,
    },
    {
        "id": 12, "category": CATEGORY,
        "question": "Resume กี่หน้า",
        "expected_keywords": ["2"],
        "alt_keywords": ["หน้า", "ไม่เกิน"],
        "ground_truth": "ไม่ควรเกิน 2 หน้า",
        "is_oos": False,
    },
    {
        "id": 13, "category": CATEGORY,
        "question": "รูปถ่ายใน Resume อายุไม่เกินกี่เดือน",
        "expected_keywords": ["6"],
        "alt_keywords": ["เดือน"],
        "ground_truth": "ไม่เกิน 6 เดือน",
        "is_oos": False,
    },
    {
        "id": 14, "category": CATEGORY,
        "question": "Resume ควรเป็นภาษาอะไร",
        "expected_keywords": [],
        "alt_keywords": ["อังกฤษ", "English"],
        "ground_truth": "ภาษาอังกฤษ",
        "is_oos": False,
    },
    {
        "id": 15, "category": CATEGORY,
        "question": "CV ย่อมาจากอะไร",
        "expected_keywords": [],
        "alt_keywords": ["Curriculum", "Vitae"],
        "ground_truth": "Curriculum Vitae",
        "is_oos": False,
    },
    {
        "id": 16, "category": CATEGORY,
        "question": "ก่อนส่ง Resume ต้องตรวจอะไร",
        "expected_keywords": [],
        "alt_keywords": ["สะกด", "วรรค", "เยื้อง", "ตัดคำ"],
        "ground_truth": "ตรวจการสะกดคำ การเว้นวรรค การเยื้อง การตัดคำ",
        "is_oos": False,
    },
    
    # ─── ติดต่อหน่วยสหกิจ (4 ข้อ) ───
    {
        "id": 17, "category": CATEGORY,
        "question": "เบอร์หน่วยสหกิจคืออะไร",
        "expected_keywords": ["055-963141"],
        "alt_keywords": [],
        "ground_truth": "055-963141",
        "is_oos": False,
    },
    {
        "id": 18, "category": CATEGORY,
        "question": "อีเมลหน่วยสหกิจ",
        "expected_keywords": ["CoopSC"],
        "alt_keywords": ["nu.ac.th"],
        "ground_truth": "CoopSC@nu.ac.th",
        "is_oos": False,
    },
    {
        "id": 19, "category": CATEGORY,
        "question": "ผู้ติดต่อหน่วยสหกิจชื่ออะไร",
        "expected_keywords": [],
        "alt_keywords": ["นิพิฐทภัทร", "ทัดหล่อ"],
        "ground_truth": "นายนิพิฐทภัทร ทัดหล่อ",
        "is_oos": False,
    },
    {
        "id": 20, "category": CATEGORY,
        "question": "ใครพิจารณาฟอร์ม Coop01",
        "expected_keywords": [],
        "alt_keywords": ["กรรมการ", "หัวหน้าภาควิชา", "คณบดี"],
        "ground_truth": "กรรมการสหกิจประจำภาควิชา หัวหน้าภาควิชา และคณบดี",
        "is_oos": False,
    },
]
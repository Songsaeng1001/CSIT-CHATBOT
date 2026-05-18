"""
Query Normalizer & Spell Corrector
จัดการคำถามที่มี typo, ตัวเลขภาษาต่างๆ, รูปแบบไม่ standard

ใช้:
    from src.normalizer import normalize_query
    clean = normalize_query("อาจารเกรียงศัก หองไหน")
    # → "อาจารย์เกรียงศัก ห้องไหน"
"""

import re


# ════════════════════════════════════════════════════════
# 1. คำที่สะกดผิดบ่อย — แก้แบบ Dictionary
# ════════════════════════════════════════════════════════

# Key = คำที่ผิด, Value = คำที่ถูก
COMMON_TYPOS = {
    # ─── เกียรตินิยม ───
    "เกียดนิยม": "เกียรตินิยม",
    "เกียดติยม": "เกียรตินิยม",
    "เกียรติ์นิยม": "เกียรตินิยม",
    "เกรียตินิยม": "เกียรตินิยม",
    "เกียร์ตินิยม": "เกียรตินิยม",
    "เกียรตินยม": "เกียรตินิยม",
    "เกียติยม": "เกียรตินิยม",
    "เกียดติย": "เกียรตินิยม",
    "เกียดนิย": "เกียรตินิยม",
    
    # ─── หน่วยกิต ───
    "หน่วยกิจ": "หน่วยกิต",
    "หนว่ยกิต": "หน่วยกิต",
    "หน่วยกีต": "หน่วยกิต",
    "หน่วยกฺิต": "หน่วยกิต",
    "หนวยกิต": "หน่วยกิต",
    
    # ─── อาจารย์ ───
    "อาจาร": "อาจารย์",
    "อาจาน": "อาจารย์",
    "อาจรย์": "อาจารย์",
    "อาจรา": "อาจารย์",
    
    # ─── ห้อง ───
    "หอง": "ห้อง",
    "หอ้ง": "ห้อง",
    "หง้อ": "ห้อง",
    
    # ─── ลงทะเบียน ───
    "ลงทะเบยน": "ลงทะเบียน",
    "ลงทะบียน": "ลงทะเบียน",
    "ลงทเบียน": "ลงทะเบียน",
    "ลงทะเบีน": "ลงทะเบียน",
    
   # ─── ค่าปรับ / ปรับ ───
    "ค่าปลับ": "ค่าปรับ",
    "คาปรับ": "ค่าปรับ",
    "ค่าปลาบ": "ค่าปรับ",
    "ปลับ": "ปรับ",          # ← เพิ่มตัวนี้
    "ปลาบ": "ปรับ",          # ← เพิ่ม variant 
    
    # ─── สำเร็จการศึกษา ───
    "สำเรจ": "สำเร็จ",
    "สำเรจ็": "สำเร็จ",
    "สำเร็ด": "สำเร็จ",
    "การศกษา": "การศึกษา",
    "การสึกษา": "การศึกษา",
    "การสึกษ": "การศึกษา",
    "การะศึกษา": "การศึกษา",
    
    # ─── เกรด ───
    "เกร็ด": "เกรด",
    "เกรท": "เกรด",
    
    # ─── พ้นสภาพ ───
    "พนสภาพ": "พ้นสภาพ",
    "พ้นสภาพ์": "พ้นสภาพ",
    "พ้นสะภาพ": "พ้นสภาพ",
    
    # ─── ที่ปรึกษา ───
    "ทีปรึกษา": "ที่ปรึกษา",
    "ที่ปลึกษา": "ที่ปรึกษา",
    "ทีปลึกษา": "ที่ปรึกษา",
    
    # ─── ภาควิชา ───
    "ภากวิชา": "ภาควิชา",
    "ภาคะวิชา": "ภาควิชา",
    "ภาคะวิชา": "ภาควิชา",
    "ภากะวิชา": "ภาควิชา",
    
    # ─── ติดต่อ ───
    "ติดตอ่": "ติดต่อ",
    "ตืดต่อ": "ติดต่อ",
    
    # ─── คำถามทั่วไป ───
    "อยุ": "อยู่",
    "หรือป่าว": "หรือเปล่า",
    "ป่ะ": "ไหม",
    "ปะ": "ไหม",
    "มัย": "ไหม",
    "ใหม่": "ไหม",  # อันนี้ระวัง! บางครั้งอาจตั้งใจ
    
    # ─── ภาษาอังกฤษทับศัพท์ ───
    "อีเมล์": "อีเมล",
    "อีเมลล์": "อีเมล",
    "เมล์": "อีเมล",
    "อีเมลล": "อีเมล",
    "email": "อีเมล",
    "Email": "อีเมล",
}


# ════════════════════════════════════════════════════════
# 2. ตัวเลข — แปลงให้เป็น standard
# ════════════════════════════════════════════════════════

# ตัวเลขภาษาไทย → อารบิก
THAI_NUMBERS = {
    "๐": "0", "๑": "1", "๒": "2", "๓": "3", "๔": "4",
    "๕": "5", "๖": "6", "๗": "7", "๘": "8", "๙": "9",
}

# คำที่หมายถึงตัวเลข
NUMBER_WORDS = {
    "ศูนย์": "0",
    "หนึ่ง": "1",
    "สอง": "2",
    "สาม": "3",
    "สี่": "4",
    "ห้า": "5",
    "หก": "6",
    "เจ็ด": "7",
    "แปด": "8",
    "เก้า": "9",
    "สิบ": "10",
    "ยี่สิบ": "20",
    "สามสิบ": "30",
}


# ════════════════════════════════════════════════════════
# 3. คำพ้องความหมาย (Synonyms)
# ════════════════════════════════════════════════════════

# ใช้เพื่อขยายคำถาม — ช่วยให้ vector search เจอ
SYNONYMS = {
    "เท่าไร": ["เท่าไหร่", "กี่บาท", "ค่าใช้จ่าย"],
    "ทำยังไง": ["ทำไง", "ต้องทำอะไร", "ขั้นตอน", "วิธี"],
    "ห้องไหน": ["ห้องอะไร", "อยู่ที่ไหน", "office", "ห้อง"],
    "อีเมล": ["email", "อีเมล์", "mail"],
}


# ════════════════════════════════════════════════════════
# 4. Functions
# ════════════════════════════════════════════════════════

def normalize_thai_numbers(text: str) -> str:
    """แปลงตัวเลขไทยเป็นอารบิก: ๒๒ → 22"""
    for thai, arabic in THAI_NUMBERS.items():
        text = text.replace(thai, arabic)
    return text


def normalize_spacing(text: str) -> str:
    """จัดการช่องว่าง: ลบช่องว่างซ้ำ, ตัด whitespace ขอบ"""
    # ลบ whitespace ซ้ำ
    text = re.sub(r"\s+", " ", text)
    # ตัด whitespace ขอบ
    text = text.strip()
    return text


def fix_common_typos(text: str) -> str:
    """แก้คำที่สะกดผิดบ่อย ตาม dictionary"""
    for typo, correct in COMMON_TYPOS.items():
        # case-insensitive replacement
        pattern = re.compile(re.escape(typo), re.IGNORECASE)
        text = pattern.sub(correct, text)
    return text

def normalize_query(text: str, verbose: bool = False) -> str:
    """..."""
    original = text
    
    # 1. Spacing
    text = normalize_spacing(text)
    
    # 2. Thai numbers
    text = normalize_thai_numbers(text)
    
    # 3. Typos
    text = fix_common_typos(text)
    
    # 4. Decimal words (สาม จุด ห้า → 3.5)  ← เพิ่มตรงนี้!
    text = normalize_decimal_words(text)
    
    # 5. Number words (สาม วัน → 3 วัน)
    text = normalize_number_words(text)
    
    if verbose and text != original:
        print(f"   🔧 Normalize: '{original}' → '{text}'")
    
    return text

def normalize_number_words(text: str) -> str:
    """แปลงคำตัวเลข (เฉพาะที่ตามด้วย 'วัน', 'หน่วยกิต' ฯลฯ)"""
    # เช็คคำตัวเลขที่ตามด้วย unit
    units = ["วัน", "หน่วยกิต", "ภาค", "ปี", "เทอม", "เดือน", "บาท"]
    
    for word, num in NUMBER_WORDS.items():
        for unit in units:
            pattern = f"{word}{unit}"
            replacement = f"{num} {unit}"
            text = text.replace(pattern, replacement)
            
            # มีช่องว่างคั่นด้วย
            pattern_with_space = f"{word} {unit}"
            text = text.replace(pattern_with_space, f"{num} {unit}")
    
    return text

def normalize_decimal_words(text: str) -> str:
    """
    แปลงคำตัวเลข + "จุด" + คำตัวเลข → เลขทศนิยม
    
    Examples:
        "สาม จุด ห้า" → "3.5"
        "สาม จุด ห้า ห้า" → "3.55"
        "หนึ่ง จุด หก ห้า" → "1.65"
        "GPA สาม จุด ห้า ห้า" → "GPA 3.55"
    """
    # สร้าง pattern ที่หา: คำตัวเลข + (จุด|.) + คำตัวเลข + คำตัวเลข?
    number_pattern = "|".join(NUMBER_WORDS.keys())
    
    # Pattern: (เลข) จุด (เลข) (เลข)?
    pattern = rf"({number_pattern})\s*(?:จุด|\.)\s*({number_pattern})\s*({number_pattern})?"
    
    def replace_match(match):
        whole = NUMBER_WORDS[match.group(1)]      # ก่อนจุด
        dec1 = NUMBER_WORDS[match.group(2)]       # หลังจุดตัวที่ 1
        dec2_word = match.group(3)
        
        if dec2_word:
            dec2 = NUMBER_WORDS[dec2_word]         # หลังจุดตัวที่ 2
            return f"{whole}.{dec1}{dec2}"
        else:
            return f"{whole}.{dec1}"
    
    return re.sub(pattern, replace_match, text)



def normalize_query(text: str, verbose: bool = False) -> str:
    """
    ทำความสะอาดคำถาม:
    1. ลบช่องว่างเกิน
    2. แปลงตัวเลขไทย
    3. แก้คำที่สะกดผิด
    4. แปลงคำตัวเลขเป็นเลข
    
    Returns: คำถามที่ normalize แล้ว
    """
    original = text
    
    # 1. Spacing
    text = normalize_spacing(text)
    
    # 2. Thai numbers
    text = normalize_thai_numbers(text)
    
    # 3. Typos
    text = fix_common_typos(text)
    
    # 4. Number words
    text = normalize_number_words(text)
    
    if verbose and text != original:
        print(f"   🔧 Normalize: '{original}' → '{text}'")
    
    return text


# ════════════════════════════════════════════════════════
# 5. Fuzzy Keyword Match
# ════════════════════════════════════════════════════════

def fuzzy_contains(text: str, keywords: list[str], 
                   min_match_ratio: float = 0.7,
                   normalize: bool = True) -> bool:
    """
    เช็คว่า text มี keyword ใด keyword หนึ่งไหม
    
    Args:
        text: ข้อความที่จะค้น
        keywords: list ของ keyword
        min_match_ratio: 0-1 ความใกล้เคียงขั้นต่ำ
        normalize: True = normalize text ก่อน (default True)
    """
    # ─── 1. Normalize ก่อน (ถ้าระบุ) ───
    if normalize:
        text = normalize_query(text)
    
    text_lower = text.lower()
    
    # ─── 2. Exact / substring match (เร็ว) ───
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    
    # ─── 3. Fuzzy match (ช้ากว่า) ───
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        for kw in keywords:
            if len(word) < 3:
                continue
            ratio = similarity_ratio(word, kw.lower())
            if ratio >= min_match_ratio:
                return True
    
    return False


def similarity_ratio(a: str, b: str) -> float:
    """
    คืนค่า similarity ratio (0-1) ระหว่าง 2 strings
    ใช้ Levenshtein distance แบบง่าย
    """
    if not a or not b:
        return 0.0
    
    if a == b:
        return 1.0
    
    # คำนวณ Levenshtein distance
    if len(a) < len(b):
        a, b = b, a
    
    distances = range(len(b) + 1)
    for i, ca in enumerate(a):
        new_distances = [i + 1]
        for j, cb in enumerate(b):
            if ca == cb:
                new_distances.append(distances[j])
            else:
                new_distances.append(
                    1 + min(distances[j], distances[j + 1], new_distances[-1])
                )
        distances = new_distances
    
    distance = distances[-1]
    max_len = max(len(a), len(b))
    return 1.0 - (distance / max_len)


# ════════════════════════════════════════════════════════
# Test
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_cases = [
        # Spell errors
        "เกียดนิยม อันดับ 1 เท่าไร",
        "อาจารเกรียงศัก อยุห้องไหน",
        "หน่วยกิจรวม CS เรียนกี่หน่วย",
        "ลงทะเบยนช้า ๗ วัน เสียเท่าไร",  # มีเลขไทย
        "ปลับลงทะเบียนช้าเท่าไหร่",
        
        # Mixed
        "GPA เก้า ภาค เกียดนิยม",  # คำตัวเลข + typo
        "หา้อง อาจารทีปรึกษา",
        
        # Normal (ไม่ควรเปลี่ยน)
        "ลงทะเบียนเกิน 22 หน่วยกิตทำยังไง",

        # 🆕 Decimal words
        "GPA สาม จุด ห้า ห้า",
        "GPA หนึ่ง จุด หก ห้า หลังเรียนสามภาค",
        "เกรดเฉลี่ย สอง จุด แปด",
    ]
    
    print("=" * 70)
    print("🧪 ทดสอบ Normalizer")
    print("=" * 70)
    
    for original in test_cases:
        normalized = normalize_query(original)
        if original != normalized:
            print(f"\n✏️  Original:   {original}")
            print(f"   Normalized: {normalized}")
        else:
            print(f"\n✓ Unchanged:  {original}")
    
    # ทดสอบ fuzzy match
    print("\n" + "=" * 70)
    print("🔍 ทดสอบ Fuzzy Match")
    print("=" * 70)
    
    keywords = ["เกียรตินิยม", "GPA", "เกรด"]
    test_queries = [
        "เกียดนิยม อันดับ 1",   # ผิด
        "GPA 3.5",              # ถูก
        "เกรดเฉลี่ย",            # ถูก
        "ข้าวผัดกุ้ง",          # ไม่เกี่ยว
    ]
    
    for q in test_queries:
        match = fuzzy_contains(q, keywords, min_match_ratio=0.7)
        icon = "✅" if match else "❌"
        print(f"   {icon} '{q}' → match: {match}")
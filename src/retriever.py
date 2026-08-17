"""
Query Router — วิเคราะห์คำถามและดึง context จาก source ที่เหมาะสม

ใช้:
    from src.retriever import retrieve_context
    context = retrieve_context("ลงทะเบียนช้า 7 วันเท่าไร")

หมายเหตุ (เปลี่ยนแปลง):
    เดิมมี resolve_vague_query() ที่เอา "คำถามก่อนหน้า" จาก history มาต่อท้าย
    คำถามคลุมเครือแบบดื้อ ๆ ซึ่งตีกับตัวเกลาคำถาม LLM (rewrite_query) ใน chat.py
    จนคำค้นเพี้ยน (เช่น "Nu6คือ สหกิจติดต่อใคร")

    ตอนนี้ย้ายหน้าที่ "ใช้ history เพื่อค้น" ไปไว้ที่ rewrite_query ใน chat.py
    เป็นตัวเดียว retriever จึงรับ "คำถามที่เกลาเสร็จแล้ว" เข้ามาตรง ๆ
    ไม่ยุ่งกับ history ในการสร้างคำค้นอีก
    (history สำหรับ "ใช้ตอบ" ยังอยู่ที่ answer() ใน chat.py เหมือนเดิม)

หมายเหตุ (RAG+KG comparison — เพิ่มใหม่):
    เพิ่ม source "sqlite_kg_foreign_phd" สำหรับคำถาม multi-hop แบบกวาดอาจารย์
    ทั้งหมดแล้วกรองด้วยคุณสมบัติ (ตัวอย่าง motivating case: id13 ใน eval_dataset —
    "อาจารย์ที่ปรึกษาที่จบปริญญาเอกจากต่างประเทศมีใครบ้าง") ซึ่ง RAG อย่างเดียว
    (vector search top-k) ทำได้ไม่ดีเพราะต้องรวมข้อมูลจากอาจารย์ทั้งหมด ไม่ใช่แค่
    chunk ที่ similarity สูงสุดไม่กี่อัน — จุดนี้คือ "KG" query แบบง่าย ๆ
    (structured attribute filter บน SQLite แทนที่จะเป็น dense retrieval)

    ควบคุมด้วย ENABLE_KG (อ่านจาก env var CSIT_ENABLE_KG) เพื่อให้รัน eval
    เทียบ RAG-only (CSIT_ENABLE_KG=0) vs RAG+KG (ปกติ/ไม่ตั้งอะไร = เปิด) ได้
    โดยไม่ต้องแก้โค้ด — ดู compare_stats.py workflow ใน session summary ข้อ 3.5
"""

import os
import re
from typing import Optional
from dataclasses import dataclass, field

from src.database import sqlite_db, rules, vector_db
from src.normalizer import normalize_query, fuzzy_contains

# ═══════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════


@dataclass
class QueryAnalysis:
    """ผลการวิเคราะห์คำถาม"""

    original_query: str
    entities: dict = field(default_factory=dict)
    sources_to_use: list[str] = field(default_factory=list)


@dataclass
class RetrievedContext:
    """Context ที่ดึงมาจาก sources ต่างๆ"""

    sqlite_data: list[str] = field(default_factory=list)
    rule_results: list[str] = field(default_factory=list)
    rag_chunks: list[str] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)

    def has_any(self) -> bool:
        return bool(self.sqlite_data or self.rule_results or self.rag_chunks)

    def to_prompt_text(self) -> str:
        """แปลงเป็นข้อความสำหรับใส่ใน prompt"""
        sections = []

        if self.rule_results:
            sections.append("🧮 ผลการคำนวณจากกฎ:\n" + "\n".join(self.rule_results))

        if self.sqlite_data:
            sections.append("📊 ข้อมูลจากฐานข้อมูล:\n" + "\n".join(self.sqlite_data))

        if self.rag_chunks:
            sections.append(
                "📚 ข้อมูลจากเอกสารภาควิชา:\n" + "\n\n".join(self.rag_chunks)
            )

        return "\n\n---\n\n".join(sections)


# ═══════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════

# เปิด/ปิด source แบบ KG (structured query) — เปิดโดย default
# ปิดด้วย env var: CSIT_ENABLE_KG=0  (ใช้ตอนรัน eval baseline "RAG-only" เทียบ "RAG+KG")
ENABLE_KG = os.getenv("CSIT_ENABLE_KG", "1") != "0"

# ═══════════════════════════════════════════════════════
# Keywords / Patterns
# ═══════════════════════════════════════════════════════

INSTRUCTOR_KEYWORDS = [
    "อาจารย์",
    "อาจาร",
    "อาจาน",
    "ผศ",
    "รศ",
    "ดร.",
    "ดร",
    "ที่ปรึกษา",
    "ทีปรึกษา",
    "อ.",
]

LATE_KEYWORDS = [
    "ค่าปรับ",
    "ปรับ",
    "ปลับ",
    "ล่าช้า",
    "ช้า",
    "เลย",
    "เสียค่า",
    "ค่าเสีย",
]

CREDIT_KEYWORDS = [
    "หน่วยกิต",
    "หน่วยกิจ",
    "ลงทะเบียน",
    "ลงทะเบยน",
    "ลง",
    "ลงเรียน",
    "เรียน",
]

GPA_KEYWORDS = [
    "gpa",
    "GPA",
    "เกรด",
    "เกรดเฉลี่ย",
    "เกียรตินิยม",
    "เกียร",
    "เกียดนิยม",
    "เกียรติ์นิยม",
    "เกียดติยม",
    "เกรียตินิยม",
    "เกียร์ตินิยม",
]

STATUS_KEYWORDS = [
    "พ้นสภาพ",
    "พนสภาพ",
    "พ้นสะภาพ",
    "รอพินิจ",
    "สถานภาพ",
    "สถาน",
]

STAFF_KEYWORDS = [
    "เจ้าหน้าที่",
    "พี่เฟิร์น",
    "พี่แมว",
    "พี่โอ๊ต",
    "พี่ยุทธ",
    "ติดต่อ",
    "เบอร์โทร",
    "โทรศัพท์",
    "อีเมล",
    "อีเมลภาควิชา",
    "ภาควิชา",
    "office",
]

NUMBER_QUERY_KEYWORDS = [
    "เท่าไร",
    "เท่าไหร่",
    "กี่",
    "เท่าใด",
    "จำนวน",
    "ราคา",
    "ค่า",
]

# รหัสวิชา 6 หลัก ขึ้นต้นด้วยรหัสสาขาที่ภาควิชานี้ใช้จริง (001/002=ศึกษาทั่วไป, 254=CS, 273=IT)
# ใช้แยกจากตัวเลขอื่น ๆ เช่นเบอร์โทร/รหัสไปรษณีย์ที่ไม่ได้ขึ้นต้นด้วยรหัสพวกนี้
COURSE_CODE_PATTERN = re.compile(r"\b(?:001|002|254|273)\d{3}\b")

# คำที่บ่งบอกว่าถามขั้นตอน/วิธีการ
STEP_KEYWORDS = [
    "ขั้นตอน",
    "วิธี",
    "ทำยังไง",
    "ทำอย่างไร",
    "ทำไง",
    "ดำเนินการ",
    "ยื่นยังไง",
    "ยื่นอย่างไร",
    "ยื่นทำไง",
    "ต้องทำ",
    "ต้องยื่น",
    "จะทำ",
    "จะยื่น",
]

# หน่วยงาน/บริการเฉพาะที่มีผู้ติดต่อของตัวเอง (ไม่ใช่เจ้าหน้าที่ทั่วไปของภาควิชา)
# ใช้กันเคส "สหกิจติดต่อใคร" ไปดึงเจ้าหน้าที่ทั่วไป (เฟิร์น/โอ๊ต) มาผิด ๆ
SPECIFIC_UNIT_KEYWORDS = [
    "สหกิจ",
    "สหกิจศึกษา",
    "ฝึกงาน",
    "ทุน",
    "ทุนการศึกษา",
]

# ─── KG: คำถาม multi-hop "อาจารย์จบเอกจากต่างประเทศมีใครบ้าง" ───
# ต้องมีทั้ง "พูดถึงปริญญาเอก" และ "พูดถึงต่างประเทศ (หรือขอเป็นรายชื่อ/ทั้งหมด)"
# ร่วมกับคำอาจารย์ ถึงจะ trigger — กันไม่ให้คำถามอื่นที่พูดถึงปริญญาเอกเฉย ๆ
# (เช่น "ต้องจบปริญญาเอกไหมถึงจะเป็นอาจารย์ได้") มาเข้า source นี้ผิด ๆ
# แบ่งคำบอกวุฒิเอกเป็น 2 ระดับตามความชัดเจน (แก้ 2026-07-23):
#   STRONG = ระบุปริญญาเอกชัดเจน ไม่กำกวม
#   WEAK   = สื่อถึงปริญญาเอกได้ แต่ในภาษาไทยอาจหมายถึง "วิชาเอก" ก็ได้
#            เช่น "อาจารย์จบเอกคอมพิวเตอร์มีใครบ้าง" = จบสาขาวิชาเอกคอมฯ
#            ไม่ได้ถามเรื่องปริญญาเอกเลย
#
# ที่ต้องแยกเพราะพบว่า "จบเอก" เป็นวิธีพูดที่ใช้บ่อยมากแต่เดิมไม่มีในลิสต์
# ทำให้ "อาจารย์ที่จบเอกต่างประเทศมีกี่ท่าน" หลุดไปเข้า sqlite_instructors แทน KG
# (ตรวจพบจาก routing_eval — KG recall = 0.67)
PHD_QUERY_KEYWORDS = [
    "ปริญญาเอก",
    "ปร.ด",
    "ป.เอก",
    "ดุษฎีบัณฑิต",
    "phd",
    "ph.d",
    "doctorate",
    "doctoral",
]
PHD_WEAK_KEYWORDS = ["จบเอก", "วุฒิเอก", "ระดับเอก", "จบ ป.เอก"]
FOREIGN_EDU_KEYWORDS = ["ต่างประเทศ", "เมืองนอก", "นอกประเทศ", "abroad"]
LIST_INTENT_KEYWORDS = ["มีใครบ้าง", "มีกี่คน", "ทุกคน", "รายชื่อ", "กี่ท่าน", "กี่คน"]


def is_specific_unit(text: str) -> bool:
    """True ถ้าข้อความเกี่ยวกับหน่วยงาน/บริการเฉพาะ (สหกิจ/ทุน/ฝึกงาน)
    คาดหวังว่า `text` ผ่าน normalize_query มาแล้ว (ตรงกับที่ classify_query ใช้)
    ใช้ร่วมกันทั้ง retriever (staff gate) และ main.py (กัน route contact ลัดวงจร)
    """
    return any(kw in text for kw in SPECIFIC_UNIT_KEYWORDS)


# ─── Bare-name fallback (ไม่มีคำนำหน้า "อาจารย์/ดร./จาร") ───────────────
# เคส "จรัสศรีจบจากไหน" ไม่มี keyword คำนำหน้าเลย แต่พิมพ์ชื่อจริงอาจารย์ตรง ๆ
# แคช list ชื่ออาจารย์จาก SQLite ไว้ในตัว process กันยิง DB ทุกคำถาม
_INSTRUCTOR_FIRST_NAMES_CACHE: Optional[list[str]] = None


def _get_instructor_first_names() -> list[str]:
    """คืนลิสต์ 'ชื่อจริง' (คำแรกของ name) ของอาจารย์ทุกคน — โหลดครั้งเดียวแล้ว cache ไว้"""
    global _INSTRUCTOR_FIRST_NAMES_CACHE
    if _INSTRUCTOR_FIRST_NAMES_CACHE is None:
        try:
            all_inst = sqlite_db.list_instructors()
            names = []
            for inst in all_inst:
                first = (inst.get("name") or "").split()[0] if inst.get("name") else ""
                if len(first) >= 3:
                    names.append(first)
            _INSTRUCTOR_FIRST_NAMES_CACHE = names
        except Exception:
            _INSTRUCTOR_FIRST_NAMES_CACHE = []
    return _INSTRUCTOR_FIRST_NAMES_CACHE


def match_bare_instructor_name(normalized: str) -> Optional[str]:
    """เช็คว่าในคำถาม (normalize แล้ว) มีชื่อจริงอาจารย์คนไหนโผล่มาตรง ๆ ไหม
    ใช้เป็น fallback เมื่อไม่มีคำนำหน้า อาจารย์/ดร./ผศ./จาร เลย
    คืนชื่อจริงที่เจอ (ตัวแรกที่แมตช์) หรือ None
    """
    for first_name in _get_instructor_first_names():
        if first_name in normalized:
            return first_name
    return None


# ═══════════════════════════════════════════════════════
# 0. Query Resolvers (ก่อน classify)
# ═══════════════════════════════════════════════════════
#
# NOTE: resolve_vague_query() ถูกถอดออกแล้ว
# หน้าที่ "เอา history มาเกลาคำถามเพื่อค้น" ย้ายไปอยู่ที่ rewrite_query() ใน chat.py
# retriever จะรับคำถามที่เกลาเสร็จแล้วเข้ามาตรง ๆ ไม่ยุ่งกับ history อีก
#
# (เหลือเฉพาะ resolve_step_query() ที่ enrich คำถาม "ขั้นตอน NU__"
#  ด้วยข้อมูลจาก SQLite ซึ่งไม่เกี่ยวกับ history)


def resolve_step_query(question: str) -> str:
    """
    ถ้าคำถามมีคำว่า "ขั้นตอน / วิธี / ทำยังไง" + NU Form
    → ดึงชื่อ NU Form จาก SQLite มา enrich query
    เพื่อไม่ให้ Chroma ดึง chunk สหกิจมาแทน

    ตัวอย่าง:
      "ขั้นตอน nu18 ทำไง"
      → "NU18 คำร้องทั่วไป ขั้นตอนการยื่น"

      "วิธีทำ nu6"
      → "NU6 แบบขอเปลี่ยนแปลงการสอนรายวิชา ขั้นตอน"

      "nu25 ทำยังไง"
      → "NU25 แบบขอสำเร็จการศึกษา ขั้นตอน"

      "ขั้นตอนสหกิจ" (ไม่มี NU)
      → คืนเดิม ไม่แตะ
    """
    normalized = normalize_query(question)

    # ตรวจว่ามีคำ step keyword ไหม
    has_step_kw = any(kw in normalized for kw in STEP_KEYWORDS)
    if not has_step_kw:
        return question  # ไม่มี → คืนเดิม

    # ดึง NU Form จากคำถาม
    nu_match = re.search(r"\bnu\s?(\d+)\b", normalized, re.IGNORECASE)
    if not nu_match:
        return question  # ไม่มี NU → คืนเดิม

    form_code = f"NU{nu_match.group(1)}"

    # ค้นหาชื่อ NU Form ใน SQLite
    form = sqlite_db.find_form(form_code)
    if not form:
        return question  # ไม่เจอใน SQLite → คืนเดิม

    # สร้าง query ใหม่ที่ชัดขึ้น
    enriched = f"{form_code} {form['name_th']} ขั้นตอนการยื่น"
    return enriched


# ═══════════════════════════════════════════════════════
# 1. Query Classifier
# ═══════════════════════════════════════════════════════


def classify_query(question: str) -> QueryAnalysis:
    """
    วิเคราะห์คำถาม
    - Normalize คำถามก่อน (แก้ typo, ตัวเลขไทย)
    - ใช้ fuzzy matching แทน exact match
    """
    normalized = normalize_query(question)

    analysis = QueryAnalysis(original_query=question)
    q = normalized.lower()

    # ─── 1. NU Form code ───
    form_match = re.search(r"\bnu\s?(\d+)\b", normalized, re.IGNORECASE)
    if form_match:
        analysis.entities["form_code"] = f"NU{form_match.group(1)}"
        analysis.sources_to_use.append("sqlite_forms")
        analysis.sources_to_use.append("chroma")  # ← มีบรรทัดนี้แล้ว ดี
        return analysis

    # ─── 2. Instructor detection ───
    has_instructor_kw = fuzzy_contains(
        normalized, INSTRUCTOR_KEYWORDS, min_match_ratio=0.75
    )
    colloquial_teacher = re.search(r"จาร(?:ย์)?[ก-๙]", normalized)

    # ลองจับชื่อจริงอาจารย์จาก SQLite ก่อนเสมอ (แม่นกว่า regex เพราะไม่โดนคำ
    # ต่อท้ายเช่น "จบจากที่ไหน"/"สำเร็จการศึกษาจาก" ทำให้ capture เพี้ยน)
    #
    # NOTE: บั๊กเดิม — regex [ก-๙a-zA-Z]+ เป็น greedy และ split() มีแค่
    # "ห้อง/อีเมล/เบอร์/รหัส" เป็น boundary จึงตัดคำท้ายพวก "จบจากที่ไหน"
    # ไม่ออก ทำให้ name กลายเป็น "เทวินจบจากที่ไหน" ทั้งท่อน แล้ว find_instructor()
    # หาไม่เจอ (fallback ไปโชว์ list รวมทุกคนแทน ซึ่งไม่มีวุฒิการศึกษา)
    # → แก้โดยลองจับจากชื่อจริงที่มีอยู่จริงใน DB ก่อนเสมอ ไม่พึ่ง regex capture
    name_hit = match_bare_instructor_name(normalized)

    # ─── 2.1 KG: อาจารย์จบเอกจากต่างประเทศ (multi-hop, ไม่มีชื่อเจาะจง) ───
    # ต้องเช็คก่อนเคส single-name เพราะคำถามนี้ไม่มีชื่อคนเจาะจง แต่ถามกวาดทุกคน
    # ปิด/เปิดด้วย ENABLE_KG (env var CSIT_ENABLE_KG) เพื่อรัน eval เทียบ RAG-only
    # vs RAG+KG ได้โดยไม่ต้องแก้โค้ด — ดูหมายเหตุหัวไฟล์
    # สัญญาณ 2 ระดับ — คำที่กำกวม ("จบเอก") ต้องมีคำว่าต่างประเทศมายืนยันด้วย
    # ไม่รับแค่เจตนาขอรายชื่อ ("มีกี่คน") เพราะ "จบเอกคอมพิวเตอร์มีกี่คน"
    # ไม่ได้ถามเรื่องปริญญาเอก
    has_strong_phd = fuzzy_contains(
        normalized, PHD_QUERY_KEYWORDS, min_match_ratio=0.75
    )
    has_weak_phd = fuzzy_contains(normalized, PHD_WEAK_KEYWORDS, min_match_ratio=0.75)
    has_foreign_edu = fuzzy_contains(
        normalized, FOREIGN_EDU_KEYWORDS, min_match_ratio=0.75
    )
    has_list_intent = fuzzy_contains(
        normalized, LIST_INTENT_KEYWORDS, min_match_ratio=0.75
    )

    is_foreign_phd_query = (
        (has_instructor_kw or colloquial_teacher)
        and not name_hit
        and (
            (has_strong_phd and (has_foreign_edu or has_list_intent))
            or (has_weak_phd and has_foreign_edu)
        )
    )

    if is_foreign_phd_query and ENABLE_KG:
        analysis.sources_to_use.append("sqlite_kg_foreign_phd")
    elif has_instructor_kw or colloquial_teacher or name_hit:
        if name_hit:
            analysis.entities["instructor_name"] = name_hit
        else:
            # DB match ไม่เจอ (เช่นชื่อพิมพ์เพี้ยนมาก หรือถามรวม ๆ ไม่มีชื่อ)
            # → fallback ไป regex เดิม ยังดีกว่าไม่มีอะไรเลย
            name_patterns = [
                r"อาจารย์([ก-๙a-zA-Z]+)",
                r"อาจาร([ก-๙a-zA-Z]+)",
                r"จารย์([ก-๙a-zA-Z]+)",
                r"จาร([ก-๙a-zA-Z]+)",
                r"ผศ\.?\s*ดร\.?\s*([ก-๙]+)",
                r"รศ\.?\s*ดร\.?\s*([ก-๙]+)",
                r"อ\.\s*([ก-๙]+)",
            ]
            for pattern in name_patterns:
                m = re.search(pattern, normalized)
                if m:
                    name = m.group(1)
                    name = re.split(
                        r"[\s,]|ห้อง|อีเมล|เบอร์|รหัส|จบ|สำเร็จ|วุฒิ|ปริญญา|สอน",
                        name,
                    )[0]
                    if len(name) >= 2:
                        analysis.entities["instructor_name"] = name
                    break
        analysis.sources_to_use.append("sqlite_instructors")

    # ─── 2.5 Staff detection ───
    # ถ้าเป็นหน่วยงานเฉพาะ (สหกิจ/ทุน/ฝึกงาน) ที่มีผู้ติดต่อของตัวเอง
    # → ไม่ดึงเจ้าหน้าที่ทั่วไป (เฟิร์น/โอ๊ต) ปล่อยให้ Chroma ดึงผู้ติดต่อเฉพาะมาแทน
    has_staff_kw = fuzzy_contains(normalized, STAFF_KEYWORDS, min_match_ratio=0.75)
    if has_staff_kw and not is_specific_unit(normalized):
        analysis.sources_to_use.append("sqlite_staff")

    # ─── 3. ตรวจหาตัวเลข + บริบทคำนวณ ───

    gpa_match = re.search(r"\b(\d\.\d{1,2})\b", normalized)
    has_gpa_kw = fuzzy_contains(normalized, GPA_KEYWORDS, min_match_ratio=0.75)
    if gpa_match and has_gpa_kw:
        analysis.entities["gpa"] = float(gpa_match.group(1))
        analysis.sources_to_use.append("rule_honor")

    days_match = re.search(r"(\d+)\s*วัน", normalized)
    has_late_kw = fuzzy_contains(normalized, LATE_KEYWORDS, min_match_ratio=0.75)
    if days_match and has_late_kw:
        analysis.entities["days_late"] = int(days_match.group(1))
        analysis.sources_to_use.append("rule_late_fee")

    credits_match = re.search(r"(\d+)\s*(?:หน่วยกิต|หน่วยกิจ|หน่วย)", normalized)
    has_credit_kw = fuzzy_contains(normalized, CREDIT_KEYWORDS, min_match_ratio=0.75)
    if credits_match and has_credit_kw:
        analysis.entities["credits"] = int(credits_match.group(1))
        analysis.sources_to_use.append("rule_credit")

    has_status_kw = fuzzy_contains(normalized, STATUS_KEYWORDS, min_match_ratio=0.75)
    if gpa_match and has_status_kw:
        sem_match = re.search(r"(\d+)\s*ภาค", normalized)
        if sem_match:
            analysis.entities["gpa_status"] = float(gpa_match.group(1))
            analysis.entities["semesters"] = int(sem_match.group(1))
            analysis.sources_to_use.append("rule_status")

    # ─── 3.5 รหัสวิชา 6 หลัก (254xxx / 273xxx / 001xxx / 002xxx) ───
    # bge-m3 (และ dense embedding ทั่วไป) แยกแยะรหัสตัวเลขล้วน ๆ ได้ไม่ดี
    # ทำให้ similarity score ของ chunk ที่ถูกต้องมักไม่ผ่านเกณฑ์ปกติใน
    # fetch_from_chroma (score < 0.8) ทั้งที่ chunk นั้นอยู่ใน top-k อยู่แล้ว
    # → ทำเครื่องหมายไว้ให้ retrieve_context สั่ง fetch_from_chroma
    #   ผ่อนเกณฑ์ score เฉพาะกรณีนี้ (ดู relax_score ด้านล่าง)
    course_code_match = COURSE_CODE_PATTERN.search(normalized)
    if course_code_match:
        analysis.entities["course_code"] = course_code_match.group(0)

    # ─── 3.8 ปฏิทินการศึกษา redirect ───
    if rules.is_calendar_query(normalized):
        analysis.sources_to_use.append("calendar_redirect")
        return analysis  # หยุดทันที

    # ─── 3.9 กยศ. redirect ───
    if rules.is_loan_query(normalized):
        analysis.sources_to_use.append("loan_redirect")
        return analysis  # หยุดทันที

    # ─── 4. Chroma (always) ───
    analysis.entities["normalized_query"] = normalized
    analysis.sources_to_use.append("chroma")

    return analysis


# ═══════════════════════════════════════════════════════
# 2. Source Handlers
# ═══════════════════════════════════════════════════════


def fetch_from_sqlite_staff() -> list[str]:
    """ดึงข้อมูลเจ้าหน้าที่ภาควิชา"""
    staff_list = sqlite_db.list_staff()
    if not staff_list:
        return []

    summary = "เจ้าหน้าที่ภาควิชา CSIT:\n"
    for s in staff_list:
        summary += f"\n• {s['name']}"
        if s.get("nickname"):
            summary += f" ({s['nickname']})"
        summary += f"\n  ตำแหน่ง: {s['position']}"
        if s.get("phone"):
            summary += f"\n  โทร: {s['phone']}"
        if s.get("email"):
            summary += f"\n  อีเมล: {s['email']}"
        summary += "\n"

    return [summary]


def fetch_from_sqlite_instructors(name: Optional[str]) -> list[str]:
    """ดึงข้อมูลอาจารย์จาก SQLite"""
    results = []

    if name:
        inst = sqlite_db.find_instructor(name)
        if inst:
            results.append(format_instructor(inst))

    if not results:
        all_inst = sqlite_db.list_instructors()
        if all_inst:
            total = len(all_inst)
            show_count = 20
            summary = f"รายชื่ออาจารย์ภาควิชา CSIT (มีทั้งหมด {total} ท่าน):\n"
            for inst in all_inst[:show_count]:
                summary += (
                    f"- {inst['title_short']} {inst['name']} ห้อง {inst['office']}\n"
                )
            if total > show_count:
                summary += f"\n... และอีก {total - show_count} ท่านค่ะ"
            results.append(summary)

    return results


def fetch_from_sqlite_kg_foreign_phd() -> list[str]:
    """ดึงรายชื่ออาจารย์ที่จบปริญญาเอกจากต่างประเทศ (KG-style structured query)

    ต่างจาก fetch_from_sqlite_instructors ตรงที่ไม่ได้ค้นด้วยชื่อคนเดียว แต่กวาด
    อาจารย์ "ทั้งหมด" แล้วกรองด้วยคุณสมบัติ (education) — งานที่ RAG แบบ vector
    search top-k ทำได้ไม่ดี เพราะต้องรวมข้อมูลจากทุก entity ไม่ใช่แค่ chunk
    ที่ similarity สูงสุดไม่กี่อัน (ดู session summary ข้อ 1.5 ปัญหา C)

    ใช้ format_instructor(fields={"education"}) เพื่อโชว์เฉพาะวุฒิ ไม่ยัดข้อมูล
    อื่นที่ไม่เกี่ยวกับคำถามนี้เข้าไปให้ LLM
    """
    matches = sqlite_db.find_foreign_phd_instructors()
    if not matches:
        return []

    # ระบุจำนวนไว้ในบรรทัดแรกเสมอ — คำถามกลุ่มนี้มักถามพ่วง "มีกี่คน"
    # ถ้าไม่บอกจำนวนตรง ๆ LLM ต้องนับเองจากรายชื่อ ซึ่งพลาดได้
    #
    # (แก้ 2026-07-24) เดิมข้อความนี้เตือนว่า "heuristic ... อาจไม่ครบ 100%"
    # ซึ่งตอนนี้ไม่จริงแล้ว เพราะ find_foreign_phd_instructors() เปลี่ยนไปใช้
    # SQL query บนตาราง instructor_education ที่ seed ครบ 20 ท่านแล้ว
    # ข้อความเตือนนี้ถูกส่งเข้า context ให้ LLM อ่าน ทำให้บอทตอบแบบออกตัว
    # ("อาจไม่ครบ") ทั้งที่ข้อมูลครบ — ฉุด Faithfulness ของคำถามกลุ่ม KG โดยตรง
    summary = (
        f"อาจารย์ที่ปรึกษาที่จบปริญญาเอกจากต่างประเทศ มีทั้งหมด {len(matches)} ท่าน "
        f"(กรองจากฐานข้อมูลโครงสร้างของภาควิชา):\n"
    )
    for inst in matches:
        summary += "\n" + format_instructor(inst, fields={"education"})

    return [summary]


def format_instructor(inst: dict, fields: Optional[set] = None) -> str:
    """จัดรูปแบบข้อมูลอาจารย์

    fields: ถ้าระบุ (เช่น {'education'}) จะโชว์ "เฉพาะ" ฟิลด์ที่ขอ (ชื่อโชว์เสมอ)
            ใช้ตอนรู้ intent ชัดเจนแล้วว่าถามอะไร (เช่น main.py เดาจากคำถามว่า
            ถามห้อง/อีเมล/วุฒิ) กันการ์ดยัดข้อมูลที่ไม่ได้ถามมาให้
            None (default) = โชว์ทุกฟิลด์ที่มีข้อมูล (พฤติกรรมเดิม — ใช้ตอนส่งเข้า
            context ให้ LLM เพราะ LLM เองเลือกสิ่งที่จะพูดจาก context อีกทีอยู่แล้ว)

    วุฒิการศึกษาเก็บใน DB เป็น string เดียวคั่นด้วย " | " ต่อ 1 ใบปริญญา
    (ดู populate_instructor_education.py) — ตรงนี้แตกเป็นบรรทัด/บูลเลตให้ก่อน
    ส่งเข้า context เลย เพื่อให้ LLM "คัดลอก" โครงสร้างที่จัดไว้แล้วตามกฎ 2/13
    ใน chat.py แทนที่จะต้องเดาว่าจะเรียงบรรทัดยังไงเอง (เดิมมันเอาไปเรียบเรียง
    เป็นพารากราฟยาวก้อนเดียว อ่านยาก)
    """
    show_all = fields is None
    fields = fields or set()

    text = f"{inst['title_short']} {inst['name']}"
    if (show_all or "office" in fields) and inst.get("office"):
        text += f"\n  ห้องทำงาน: {inst['office']}"
    if (show_all or "email" in fields) and inst.get("email"):
        text += f"\n  อีเมล: {inst['email']}"
    if (show_all or "education" in fields) and inst.get("education"):
        degrees = [d.strip() for d in inst["education"].split("|") if d.strip()]
        # ตัดคำซ้ำ "สำเร็จการศึกษาจาก" หน้าทุกบูลเลตออก กันอ่านซ้ำซาก
        degrees = [re.sub(r"^สำเร็จการศึกษาจาก\s*", "", d) for d in degrees]
        if len(degrees) > 1:
            bullet_lines = "\n".join(f"    • {d}" for d in degrees)
            text += f"\n  วุฒิการศึกษา:\n{bullet_lines}"
        else:
            text += f"\n  วุฒิการศึกษา: {degrees[0]}"
    if (show_all or "specialization" in fields) and inst.get("specialization"):
        text += f"\n  หมายเหตุ: {inst['specialization']}"
    return text


def fetch_from_sqlite_forms(code: Optional[str]) -> list[str]:
    """ดึงข้อมูล NU form จาก SQLite"""
    if not code:
        return []

    form = sqlite_db.find_form(code)
    if not form:
        return [f"ไม่พบฟอร์ม {code}"]

    text = f"{form['code']}: {form['name_th']}"
    text += f"\n  หมวด: {form['category']}"
    if form.get("purpose"):
        text += f"\n  ใช้สำหรับ: {form['purpose']}"
    if form.get("fee"):
        text += f"\n  ค่าธรรมเนียม: {form['fee']}"
    # ── เพิ่ม: แนบลิงก์ระบบคำร้องออนไลน์เข้า context ทุกครั้งที่เจอฟอร์ม ──
    text += "\n  ยื่นคำร้องออนไลน์ที่ระบบคำร้อง REG: https://reg4.nu.ac.th/manual/1.man-user/2.web/MAN_UW-NU67-REG-1-7.RequestOnline-Dorm.pdf"

    return [text]


# ═══════════════════════════════════════════════════════
# 3. Rule Engine Handlers
# ═══════════════════════════════════════════════════════


def calculate_honor(gpa: float) -> list[str]:
    honor = rules.calculate_honor(gpa)
    if honor:
        return [
            f"GPA {gpa} ได้ {honor}\n"
            f"  เงื่อนไขเพิ่มเติม: ต้องไม่เคยได้ F หรือ U "
            f"และไม่เคยลงทะเบียนเรียนซ้ำ"
        ]
    if gpa >= 2.0:
        return [
            f"GPA {gpa} ไม่ถึงเกณฑ์เกียรตินิยม (ต้อง ≥ 3.25)\n"
            f"  แต่ยังคงสำเร็จการศึกษาได้ตามปกติ"
        ]
    return [f"GPA {gpa} ต่ำกว่า 2.00 — ยังไม่สำเร็จการศึกษา"]


def calculate_late_fee(days: int) -> list[str]:
    result = rules.calculate_late_fee(days)
    if result["status"] == "พ้นสภาพ":
        return [
            f"ลงทะเบียนช้า {days} วัน — {result['message']}\n"
            f"  ค่าคืนสภาพ: {result['reinstatement_fee']} บาท"
        ]
    return [
        f"ลงทะเบียนช้า {days} วัน\n"
        f"  ค่าปรับ: {days} × {result['fee_per_day']} = {result['total_fee']} บาท\n"
        f"  ยังลงได้ปกติ เหลือเวลาอีก {result['remaining_days']} วัน "
        f"ก่อนพ้นสภาพ (เกิน 14 วันจะพ้นสภาพ)"
    ]


def check_credit_limit(credits: int) -> list[str]:
    result = rules.check_credit_limit(credits)
    if not result["allowed"]:
        return [
            f"ลง {credits} หน่วยกิต — เกินกำหนด!\n"
            f"  ขีดจำกัดภาคปกติ: {result['limit']} หน่วยกิต\n"
            f"  เกิน {result['over']} หน่วยกิต — ต้องยื่นคำร้อง NU18 "
            f"ผ่านอาจารย์ที่ปรึกษาและคณบดี"
        ]
    return [
        f"ลง {credits} หน่วยกิต — ลงได้ปกติ\n"
        f"  ขีดจำกัดภาคปกติคือ {result['limit']} หน่วยกิต"
    ]


def check_status(gpa: float, semesters: int) -> list[str]:
    result = rules.check_academic_status(gpa, semesters)
    text = f"GPA {gpa} หลังเรียน {semesters} ภาค: {result['status']}"
    if "reason" in result:
        text += f"\n  เหตุผล: {result['reason']}"
    return [text]


# ═══════════════════════════════════════════════════════
# 4. RAG Handler
# ═══════════════════════════════════════════════════════


def fetch_from_chroma(query: str, k: int = 5, relax_score: bool = False) -> list[str]:
    """ดึง chunks จาก Chroma

    relax_score: ถ้า True จะไม่กรองด้วย score threshold เลย (เอา top-k ทั้งหมด)
        ใช้กับคำถามรหัสวิชา 6 หลัก (254xxx/273xxx/001xxx/002xxx) เพราะ dense
        embedding อย่าง bge-m3 แยกแยะรหัสตัวเลขล้วน ๆ ได้ไม่ดี ทำให้ similarity
        score ของ chunk ที่ถูกต้องมักไม่ผ่านเกณฑ์ปกติ ทั้งที่ chunk นั้น
        อยู่ใน top-k อยู่แล้ว (ดู classify_query ส่วน 3.5)
    """
    normalized = normalize_query(query)
    results = vector_db.search(normalized, k=k)

    chunks = []
    for doc, score in results:
        if relax_score or score < 0.8:  # เข้มขึ้นจาก 1.5 → 0.8 ลด false positive
            chunks.append(doc.page_content.strip())

    return chunks


# ═══════════════════════════════════════════════════════
# 5. Main Retrieval Function
# ═══════════════════════════════════════════════════════


def retrieve_context(
    question: str, verbose: bool = False, history: list = []
) -> RetrievedContext:
    """ฟังก์ชันหลัก: รับคำถาม → คืน context

    NOTE: พารามิเตอร์ `history` ยังคงไว้เพื่อความเข้ากันได้กับ call site เดิม
    แต่ "ไม่ได้ใช้" ในการสร้างคำค้นแล้ว — การเกลาคำถามด้วย history
    ย้ายไปทำที่ rewrite_query() ใน chat.py ก่อนจะเรียก retrieve_context
    (กันบั๊กตัวเกลาซ้อนกัน 2 ตัว) ทำให้ retriever รับคำถามที่เกลาเสร็จแล้วตรง ๆ
    """

    # ── Step 1: Resolve "ขั้นตอน NU" ให้ชัดขึ้น ─────────
    resolved_question = resolve_step_query(question)
    if verbose:
        print(f"🔍 Final query: {resolved_question}")

    # ── Step 2: Classify ──────────────────────────────────
    analysis = classify_query(resolved_question)
    context = RetrievedContext()

    if verbose:
        print(f"📋 Sources to use: {analysis.sources_to_use}")
        print(f"📌 Entities: {analysis.entities}")

    # ── Step 3: ดึงข้อมูลจากแต่ละ source ─────────────────

    # SQLite — instructors
    if "sqlite_instructors" in analysis.sources_to_use:
        data = fetch_from_sqlite_instructors(analysis.entities.get("instructor_name"))
        if data:
            context.sqlite_data.extend(data)
            context.sources_used.append("SQLite/instructors")

    # SQLite — KG: อาจารย์จบเอกต่างประเทศ (multi-hop structured query)
    if "sqlite_kg_foreign_phd" in analysis.sources_to_use:
        data = fetch_from_sqlite_kg_foreign_phd()
        if data:
            context.sqlite_data.extend(data)
            context.sources_used.append("SQLite/KG_foreign_phd")

    # SQLite — forms
    if "sqlite_forms" in analysis.sources_to_use:
        data = fetch_from_sqlite_forms(analysis.entities.get("form_code"))
        if data:
            context.sqlite_data.extend(data)
            context.sources_used.append("SQLite/nu_forms")

            # ── เช็คว่าเป็นคำถามขั้นตอนไหม ──
            is_step_question = any(
                kw in normalize_query(resolved_question) for kw in STEP_KEYWORDS
            )

            # ถ้าถามแค่ "NU17 คืออะไร" → ไม่ต้อง Chroma (SQLite พอ)
            # ถ้าถาม "ขั้นตอน NU17" → ต้อง Chroma ด้วย (SQLite ไม่มีขั้นตอน)
            if not is_step_question and "chroma" in analysis.sources_to_use:
                analysis.sources_to_use.remove("chroma")

    # SQLite — staff
    if "sqlite_staff" in analysis.sources_to_use:
        data = fetch_from_sqlite_staff()
        if data:
            context.sqlite_data.extend(data)
            context.sources_used.append("SQLite/staff")

    # Rule Engine — honor
    if "rule_honor" in analysis.sources_to_use:
        result = calculate_honor(analysis.entities["gpa"])
        context.rule_results.extend(result)
        context.sources_used.append("Rule/honor")

    # Rule Engine — late fee
    if "rule_late_fee" in analysis.sources_to_use:
        result = calculate_late_fee(analysis.entities["days_late"])
        context.rule_results.extend(result)
        context.sources_used.append("Rule/late_fee")

    # Rule Engine — credit
    if "rule_credit" in analysis.sources_to_use:
        result = check_credit_limit(analysis.entities["credits"])
        context.rule_results.extend(result)
        context.sources_used.append("Rule/credit")

    # Rule Engine — status
    if "rule_status" in analysis.sources_to_use:
        result = check_status(
            analysis.entities["gpa_status"], analysis.entities["semesters"]
        )
        context.rule_results.extend(result)
        context.sources_used.append("Rule/status")

    # Calendar redirect → return ทันที
    if "calendar_redirect" in analysis.sources_to_use:
        context.rule_results.append(rules.get_calendar_redirect_template())
        context.sources_used.append("Rule/calendar_redirect")
        return context

    # Loan redirect → return ทันที
    if "loan_redirect" in analysis.sources_to_use:
        template = rules.get_loan_redirect_template()
        context.rule_results.append(template)
        context.sources_used.append("Rule/loan_redirect")
        return context

    # Chroma — RAG (ใช้ resolved_question ที่ enrich แล้ว)
    if "chroma" in analysis.sources_to_use:
        relax = "course_code" in analysis.entities
        chunks = fetch_from_chroma(resolved_question, k=5, relax_score=relax)
        if chunks:
            context.rag_chunks.extend(chunks)
            context.sources_used.append("Chroma")

    return context


# ═══════════════════════════════════════════════════════
# Test
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":

    print("=" * 70)
    print("🧪 ทดสอบ resolve_step_query")
    print("=" * 70)
    step_tests = [
        "ขั้นตอน nu18 ทำไง",
        "วิธีทำ nu6",
        "nu25 ทำยังไง",
        "ขั้นตอนสหกิจ",  # ไม่มี NU → คืนเดิม
        "nu18 ใช้ทำอะไร",  # ไม่มี step keyword → คืนเดิม
        "ต้องยื่น nu7 ยังไง",
        "nu17 ดำเนินการอย่างไร",
    ]
    for q in step_tests:
        result = resolve_step_query(q)
        changed = "✅ เปลี่ยน" if result != q else "➡️  คงเดิม"
        print(f"{changed} | '{q}' → '{result}'")

    print("\n" + "=" * 70)
    print("🧪 ตรวจว่า history ไม่ถูกเอามาเกลาคำถามใน retriever อีกแล้ว")
    print("=" * 70)
    print("(การเกลาด้วย history ย้ายไปที่ rewrite_query ใน chat.py)")
    # คำถามคลุมเครือ + ส่ง history เข้ามา — retriever ต้อง 'ไม่' เอา history มาต่อท้าย
    history_test = [
        {"role": "user", "content": "nu18 ใช้ทำอะไร"},
        {"role": "assistant", "content": "NU18 คือคำร้องทั่วไป"},
    ]
    ctx = retrieve_context("แล้วมีขั้นตอนยังไง", verbose=True, history=history_test)
    print(f"📦 Sources: {ctx.sources_used}")
    print("☝️  Final query ควรเป็น 'แล้วมีขั้นตอนยังไง' ล้วน ๆ (ไม่มี 'nu18' มาต่อ)")

    print("\n" + "=" * 70)
    print("🧪 ทดสอบ Query Router ปกติ")
    print("=" * 70)
    normal_tests = [
        "อาจารย์เกรียงศักดิ์ห้องอะไร",
        "NU25 ใช้ทำอะไร",
        "ขั้นตอน nu25 ทำยังไง",
        "GPA 3.55 ได้เกียรตินิยมอะไร",
        "ลงทะเบียนช้า 7 วัน ต้องจ่ายเท่าไร",
        "ลง 24 หน่วยกิตได้ไหม",
        "พี่เฟิร์นเบอร์โทรอะไร",
        "Resume กี่หน้า",
        "กยศ. ต้องทำยังไง",
        "จารสัญญาอยู่ไหน",
        "จารย์วินัยห้องอะไร",
    ]
    for q in normal_tests:
        print(f"\n❓ {q}")
        print("-" * 70)
        ctx = retrieve_context(q, verbose=True)
        print(f"📦 Sources: {ctx.sources_used}")
        preview = ctx.to_prompt_text()[:200]
        print(preview if preview else "⚠️  ไม่มี context")
        print("=" * 70)

    print("\n" + "=" * 70)
    print("🧪 ทดสอบ Staff gate (กันพี่เฟิร์นโผล่ในคำถามหน่วยงานเฉพาะ)")
    print("=" * 70)
    # (query, ควรมี sqlite_staff ไหม)
    staff_gate_tests = [
        ("ติดต่อภาควิชา", True),  # ทั่วไป → ต้องมีเจ้าหน้าที่
        ("เจ้าหน้าที่ภาควิชาเบอร์อะไร", True),  # ทั่วไป → ต้องมี
        ("พี่เฟิร์นเบอร์โทรอะไร", True),  # ถามชื่อตรง ๆ → ต้องมี
        ("สหกิจติดต่อใคร", False),  # หน่วยงานเฉพาะ → ห้ามมี
        ("ติดต่อสหกิจศึกษา", False),  # หน่วยงานเฉพาะ → ห้ามมี
        ("ฝึกงานติดต่อเจ้าหน้าที่คนไหน", False),  # หน่วยงานเฉพาะ → ห้ามมี
        ("ทุนการศึกษาติดต่อใคร", False),  # หน่วยงานเฉพาะ → ห้ามมี
    ]
    all_pass = True
    for q, expect in staff_gate_tests:
        analysis = classify_query(q)
        got = "sqlite_staff" in analysis.sources_to_use
        ok = got == expect
        all_pass = all_pass and ok
        mark = "✅" if ok else "❌"
        print(f"{mark} '{q}' → sqlite_staff={got} " f"(คาดหวัง {expect})")
    print("-" * 70)
    print("🎉 ผ่านทั้งหมด" if all_pass else "⚠️  มีเคสไม่ผ่าน เช็ก keyword list")

    print("\n" + "=" * 70)
    print("🧪 ทดสอบ Calendar redirect (วัน/กำหนดการ → ปฏิทินการศึกษา)")
    print("=" * 70)
    # (query, ควร redirect ไปปฏิทินไหม)
    calendar_tests = [
        ("เปิดเทอมวันไหน", True),  # ปฏิทินตรง ๆ
        ("ปิดเทอมเมื่อไหร่", True),  # ปฏิทินตรง ๆ
        ("ปฏิทินการศึกษา", True),  # ปฏิทินตรง ๆ
        ("ลงทะเบียนเรียนวันไหน", True),  # หัวข้อ + เวลา
        ("สอบปลายภาควันไหน", True),  # หัวข้อ + เวลา
        ("จ่ายค่าเทอมภายในวันไหน", True),  # หัวข้อ + เวลา (เดดไลน์)
        ("ลงทะเบียนเรียนยังไง", False),  # หัวข้อแต่ถามวิธี → ปล่อยไป RAG
        ("จ่ายค่าเทอมยังไง", False),  # หัวข้อแต่ถามวิธี → ปล่อยไป RAG
        ("nu7 คืออะไร", False),  # คนละเรื่อง
    ]
    cal_pass = True
    for q, expect in calendar_tests:
        got = rules.is_calendar_query(normalize_query(q))
        ok = got == expect
        cal_pass = cal_pass and ok
        mark = "✅" if ok else "❌"
        print(f"{mark} '{q}' → calendar={got} (คาดหวัง {expect})")
    print("-" * 70)
    print("🎉 ผ่านทั้งหมด" if cal_pass else "⚠️  มีเคสไม่ผ่าน เช็ก keyword list")

    print("\n" + "=" * 70)
    print("🧪 ทดสอบรหัสวิชา 6 หลัก (แก้บั๊ก answered=False กับคำถามรหัสวิชา)")
    print("=" * 70)
    # (query, ควรมี course_code entity ไหม)
    course_code_tests = [
        ("รหัสรายวิชา 254171 หมายถึงอะไร", True),
        ("273252 คือวิชาอะไร", True),
        ("001101 เรียนเรื่องอะไร", True),
        ("เบอร์โทร 055-963262 ติดต่อใคร", False),  # เบอร์โทร ไม่ใช่รหัสวิชา
        ("GPA 3.55 ได้เกียรตินิยมอะไร", False),  # ไม่มีรหัสวิชา
    ]
    cc_pass = True
    for q, expect in course_code_tests:
        analysis = classify_query(q)
        got = "course_code" in analysis.entities
        ok = got == expect
        cc_pass = cc_pass and ok
        mark = "✅" if ok else "❌"
        print(f"{mark} '{q}' → course_code detected={got} (คาดหวัง {expect})")
    print("-" * 70)
    print("🎉 ผ่านทั้งหมด" if cc_pass else "⚠️  มีเคสไม่ผ่าน เช็ก COURSE_CODE_PATTERN")

    print("\n" + "=" * 70)
    print("🧪 ทดสอบ KG: อาจารย์จบเอกจากต่างประเทศ (RAG+KG comparison, id13)")
    print("=" * 70)
    print(f"ENABLE_KG = {ENABLE_KG} (ตั้งด้วย env var CSIT_ENABLE_KG=0/1)")
    # (query, ควร trigger sqlite_kg_foreign_phd ไหม เมื่อ ENABLE_KG=True)
    kg_tests = [
        ("อาจารย์ที่ปรึกษาที่จบปริญญาเอกจากต่างประเทศมีใครบ้าง", True),
        ("มีอาจารย์ที่จบปริญญาเอกต่างประเทศกี่คน", True),
        ("อาจารย์สัญญาจบปริญญาเอกจากที่ไหน", False),  # มีชื่อเจาะจง → ไม่ใช่ KG
        (
            "ต้องจบปริญญาเอกไหมถึงจะเป็นอาจารย์ที่ปรึกษาได้",
            False,
        ),  # ไม่มี list intent/ต่างประเทศ
        ("อาจารย์วินัยอยู่ห้องไหน", False),  # คนละเรื่อง
    ]
    kg_pass = True
    for q, expect in kg_tests:
        analysis = classify_query(q)
        got = "sqlite_kg_foreign_phd" in analysis.sources_to_use
        ok = got == expect if ENABLE_KG else got is False
        kg_pass = kg_pass and ok
        mark = "✅" if ok else "❌"
        print(
            f"{mark} '{q}' → sqlite_kg_foreign_phd={got} (คาดหวัง {expect if ENABLE_KG else False})"
        )
    print("-" * 70)
    print(
        "🎉 ผ่านทั้งหมด"
        if kg_pass
        else "⚠️  มีเคสไม่ผ่าน เช็ก PHD/FOREIGN/LIST keyword list"
    )

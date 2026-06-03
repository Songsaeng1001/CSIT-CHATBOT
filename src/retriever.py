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
"""

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
    if has_instructor_kw:
        name_patterns = [
            r"อาจารย์([ก-๙a-zA-Z]+)",
            r"อาจาร([ก-๙a-zA-Z]+)",
            r"ผศ\.?\s*ดร\.?\s*([ก-๙]+)",
            r"รศ\.?\s*ดร\.?\s*([ก-๙]+)",
            r"อ\.\s*([ก-๙]+)",
        ]
        for pattern in name_patterns:
            m = re.search(pattern, normalized)
            if m:
                name = m.group(1)
                name = re.split(r"[\s,]|ห้อง|อีเมล|เบอร์|รหัส", name)[0]
                if len(name) >= 2:
                    analysis.entities["instructor_name"] = name
                break
        analysis.sources_to_use.append("sqlite_instructors")

    # ─── 2.5 Staff detection ───
    # ถ้าเป็นหน่วยงานเฉพาะ (สหกิจ/ทุน/ฝึกงาน) ที่มีผู้ติดต่อของตัวเอง
    # → ไม่ดึงเจ้าหน้าที่ทั่วไป (เฟิร์น/โอ๊ต) ปล่อยให้ Chroma ดึงผู้ติดต่อเฉพาะมาแทน
    has_staff_kw = fuzzy_contains(normalized, STAFF_KEYWORDS, min_match_ratio=0.75)
    is_specific_unit = any(kw in normalized for kw in SPECIFIC_UNIT_KEYWORDS)
    if has_staff_kw and not is_specific_unit:
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


def format_instructor(inst: dict) -> str:
    """จัดรูปแบบข้อมูลอาจารย์"""
    text = f"{inst['title_short']} {inst['name']}"
    if inst.get("office"):
        text += f"\n  ห้องทำงาน: {inst['office']}"
    if inst.get("email"):
        text += f"\n  อีเมล: {inst['email']}"
    if inst.get("specialization"):
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


def fetch_from_chroma(query: str, k: int = 3) -> list[str]:
    """ดึง chunks จาก Chroma"""
    normalized = normalize_query(query)
    results = vector_db.search(normalized, k=k)

    chunks = []
    for doc, score in results:
        if score < 0.8:  # เข้มขึ้นจาก 1.5 → 0.8 ลด false positive
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

    # Loan redirect → return ทันที
    if "loan_redirect" in analysis.sources_to_use:
        template = rules.get_loan_redirect_template()
        context.rule_results.append(template)
        context.sources_used.append("Rule/loan_redirect")
        return context

    # Chroma — RAG (ใช้ resolved_question ที่ enrich แล้ว)
    if "chroma" in analysis.sources_to_use:
        chunks = fetch_from_chroma(resolved_question, k=3)
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
        print(
            f"{mark} '{q}' → sqlite_staff={got} "
            f"(คาดหวัง {expect})"
        )
    print("-" * 70)
    print("🎉 ผ่านทั้งหมด" if all_pass else "⚠️  มีเคสไม่ผ่าน เช็ก keyword list")
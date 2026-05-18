"""
Query Router — วิเคราะห์คำถามและดึง context จาก source ที่เหมาะสม

ใช้:
    from src.retriever import retrieve_context
    context = retrieve_context("ลงทะเบียนช้า 7 วันเท่าไร")
"""

import re
from typing import Optional
from dataclasses import dataclass, field

from src.database import sqlite_db, rules, vector_db


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
        
        # ผลการคำนวณจากกฎ (สำคัญที่สุด — ใส่ก่อน)
        if self.rule_results:
            sections.append("🧮 ผลการคำนวณจากกฎ:\n" + "\n".join(self.rule_results))
        
        # ข้อมูลจาก SQLite (ข้อมูลเป๊ะ)
        if self.sqlite_data:
            sections.append("📊 ข้อมูลจากฐานข้อมูล:\n" + "\n".join(self.sqlite_data))
        
        # Context จาก RAG (ข้อมูลรายละเอียด)
        if self.rag_chunks:
            sections.append("📚 ข้อมูลจากเอกสารภาควิชา:\n" + "\n\n".join(self.rag_chunks))
        
        return "\n\n---\n\n".join(sections)


# ═══════════════════════════════════════════════════════
# 1. Query Classifier
# ═══════════════════════════════════════════════════════

# Patterns ที่ใช้บ่อย
INSTRUCTOR_KEYWORDS = ["อาจารย์", "ผศ", "รศ", "ดร.", "ที่ปรึกษา", "อ."]
LATE_KEYWORDS = ["ค่าปรับ", "ปรับ", "ล่าช้า", "ช้า", "เสียค่า"]
CREDIT_KEYWORDS = ["หน่วยกิต", "ลงทะเบียน", "ลง"]
GPA_KEYWORDS = ["gpa", "เกรด", "เกียรตินิยม", "เกรดเฉลี่ย"]
STATUS_KEYWORDS = ["พ้นสภาพ", "รอพินิจ", "สถานภาพ"]


def classify_query(question: str) -> QueryAnalysis:
    """วิเคราะห์คำถาม"""
    analysis = QueryAnalysis(original_query=question)
    q = question.lower()
    
    # ─── 1. ตรวจหา NU Form code ───
    form_match = re.search(r"\bnu\s?(\d+)\b", question, re.IGNORECASE)
    if form_match:
        analysis.entities["form_code"] = f"NU{form_match.group(1)}"
        analysis.sources_to_use.append("sqlite_forms")
    
    # ─── 2. ตรวจหาชื่ออาจารย์ ───
    has_instructor_kw = any(kw in question for kw in INSTRUCTOR_KEYWORDS)
    if has_instructor_kw:
        # พยายามดึงชื่อจริง — เช่น "อาจารย์เกรียงศักดิ์" → "เกรียงศักดิ์"
        name_patterns = [
            r"อาจารย์([ก-๙a-zA-Z]+)",
            r"ผศ\.?\s*ดร\.?\s*([ก-๙]+)",
            r"รศ\.?\s*ดร\.?\s*([ก-๙]+)",
            r"อ\.\s*([ก-๙]+)",
        ]
        for pattern in name_patterns:
            m = re.search(pattern, question)
            if m:
                analysis.entities["instructor_name"] = m.group(1)
                break
        
        analysis.sources_to_use.append("sqlite_instructors")
    
    # ─── 3. ตรวจหาตัวเลข + บริบทคำนวณ ───
    
    # GPA pattern (เช่น 3.55, 1.65)
    gpa_match = re.search(r"\b(\d\.\d{1,2})\b", question)
    if gpa_match and any(kw in q for kw in GPA_KEYWORDS):
        analysis.entities["gpa"] = float(gpa_match.group(1))
        analysis.sources_to_use.append("rule_honor")
    
    # จำนวนวัน + late
    days_match = re.search(r"(\d+)\s*วัน", question)
    if days_match and any(kw in q for kw in LATE_KEYWORDS):
        analysis.entities["days_late"] = int(days_match.group(1))
        analysis.sources_to_use.append("rule_late_fee")
    
    # หน่วยกิต
    credits_match = re.search(r"(\d+)\s*หน่วยกิต", question)
    if credits_match and any(kw in q for kw in CREDIT_KEYWORDS):
        analysis.entities["credits"] = int(credits_match.group(1))
        analysis.sources_to_use.append("rule_credit")
    
    # GPA + ภาค (เช็คพ้นสภาพ)
    if gpa_match and any(kw in q for kw in STATUS_KEYWORDS):
        sem_match = re.search(r"(\d+)\s*ภาค", question)
        if sem_match:
            analysis.entities["gpa_status"] = float(gpa_match.group(1))
            analysis.entities["semesters"] = int(sem_match.group(1))
            analysis.sources_to_use.append("rule_status")
    
    # ─── 4. Default: ใช้ Chroma ───
    # เพิ่ม Chroma เสมอเพื่อเป็น context เสริม (ยกเว้นกรณีที่มีคำตอบจาก SQL/Rule แน่นอน)
    analysis.sources_to_use.append("chroma")
    
    return analysis


# ═══════════════════════════════════════════════════════
# 2. Source Handlers
# ═══════════════════════════════════════════════════════

def fetch_from_sqlite_instructors(name: Optional[str]) -> list[str]:
    """ดึงข้อมูลอาจารย์จาก SQLite"""
    results = []
    
    if name:
        # ค้นด้วยชื่อ
        inst = sqlite_db.find_instructor(name)
        if inst:
            text = format_instructor(inst)
            results.append(text)
    
    # ถ้าไม่เจอด้วยชื่อ — แสดงรายชื่อทั้งหมด (ย่อ)
    if not results:
        all_inst = sqlite_db.list_instructors()
        if all_inst:
            summary = "รายชื่ออาจารย์ภาควิชา CSIT ทั้งหมด:\n"
            for inst in all_inst[:5]:  # แสดง 5 คน
                summary += f"- {inst['title_short']} {inst['name']} ห้อง {inst['office']}\n"
            summary += f"... และอีก {len(all_inst) - 5} ท่าน"
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
    """คำนวณเกียรตินิยมจาก GPA"""
    honor = rules.calculate_honor(gpa)
    
    if honor:
        return [
            f"GPA {gpa} ได้ {honor}\n"
            f"  เงื่อนไขเพิ่มเติม: ต้องไม่เคยได้ F หรือ U "
            f"และไม่เคยลงทะเบียนเรียนซ้ำ"
        ]
    else:
        if gpa >= 2.0:
            return [f"GPA {gpa} ไม่ถึงเกณฑ์เกียรตินิยม (ต้อง ≥ 3.25)\n"
                    f"  แต่ยังคงสำเร็จการศึกษาได้ตามปกติ"]
        else:
            return [f"GPA {gpa} ต่ำกว่า 2.00 — ยังไม่สำเร็จการศึกษา"]


def calculate_late_fee(days: int) -> list[str]:
    """คำนวณค่าปรับลงทะเบียนช้า"""
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
    """ตรวจหน่วยกิตที่ลง"""
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
    """ตรวจสถานภาพนิสิต"""
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
    results = vector_db.search(query, k=k)
    
    chunks = []
    for doc, score in results:
        # กรอง chunks ที่ไม่ค่อย relevant ออก
        if score < 1.0:  # distance ต่ำ = relevant
            chunks.append(doc.page_content.strip())
    
    return chunks


# ═══════════════════════════════════════════════════════
# 5. Main Retrieval Function
# ═══════════════════════════════════════════════════════

def retrieve_context(question: str, verbose: bool = False) -> RetrievedContext:
    """
    ฟังก์ชันหลัก: รับคำถาม → คืน context ที่รวมจากทุก source
    """
    # 1. วิเคราะห์คำถาม
    analysis = classify_query(question)
    context = RetrievedContext()
    
    if verbose:
        print(f"🔍 Sources to use: {analysis.sources_to_use}")
        print(f"📌 Entities: {analysis.entities}")
    
    # 2. ดึงข้อมูลจากแต่ละ source
    
    # SQLite — instructors
    if "sqlite_instructors" in analysis.sources_to_use:
        data = fetch_from_sqlite_instructors(
            analysis.entities.get("instructor_name")
        )
        if data:
            context.sqlite_data.extend(data)
            context.sources_used.append("SQLite/instructors")
    
    # SQLite — forms
    if "sqlite_forms" in analysis.sources_to_use:
        data = fetch_from_sqlite_forms(analysis.entities.get("form_code"))
        if data:
            context.sqlite_data.extend(data)
            context.sources_used.append("SQLite/nu_forms")
    
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
            analysis.entities["gpa_status"],
            analysis.entities["semesters"]
        )
        context.rule_results.extend(result)
        context.sources_used.append("Rule/status")
    
    # Chroma — RAG (always)
    if "chroma" in analysis.sources_to_use:
        chunks = fetch_from_chroma(question, k=3)
        if chunks:
            context.rag_chunks.extend(chunks)
            context.sources_used.append("Chroma")
    
    return context


# ═══════════════════════════════════════════════════════
# Test
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    test_queries = [
        "อาจารย์เกรียงศักดิ์ห้องอะไร",
        "NU25 ใช้ทำอะไร",
        "GPA 3.55 ได้เกียรตินิยมอะไร",
        "ลงทะเบียนช้า 7 วัน ต้องจ่ายเท่าไร",
        "ลง 24 หน่วยกิตได้ไหม",
        "GPA 1.65 หลังเรียน 3 ภาค",
        "เบอร์โทรภาควิชา",
    ]
    
    print("=" * 70)
    print("🧪 ทดสอบ Query Router")
    print("=" * 70)
    
    for q in test_queries:
        print(f"\n❓ {q}")
        print("-" * 70)
        ctx = retrieve_context(q, verbose=True)
        print(f"\n📦 Sources used: {ctx.sources_used}")
        print(f"\n--- Context ---")
        print(ctx.to_prompt_text()[:500])
        if len(ctx.to_prompt_text()) > 500:
            print("...")
        print("=" * 70)
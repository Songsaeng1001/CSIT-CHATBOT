"""
routing_eval.py — วัดความแม่นของ "ตัวจัดเส้นทาง" (rule-based router)

รัน:  python -m src.eval.routing_eval

⚡ ไม่เรียก LLM เลย ไม่เสียโควตา — เรียกแค่ classify_query() กับ SQLite

─────────────────────────────────────────────────────────────────────
ทำไมต้องวัดแยก: RAGAS มองไม่เห็นความผิดพลาดของ router
─────────────────────────────────────────────────────────────────────
Faithfulness นิยามว่า "คำตอบมีหลักฐานรองรับใน context ที่ดึงมา" ถ้า router
เลือก source ผิด แล้ว LLM ตอบตาม context ผิดนั้นอย่างซื่อสัตย์
→ Faithfulness = 1.00 แต่คำตอบผิด

บั๊ก id 18 (Session 8) เป็นเคสนี้พอดี: บอทแนบลิงก์หลักสูตรกับคำถามเรื่อง
ลงทะเบียน ซึ่ง RAGAS ไม่ได้จับได้ ผู้ทำวิจัยจับได้เองจากการอ่านคำตอบ
การวัด routing แยกจึงเป็นการอุดช่องโหว่ของวิธีประเมินโดยตรง

─────────────────────────────────────────────────────────────────────
รูปแบบเฉลย: require / forbid (แก้ 2026-07-23)
─────────────────────────────────────────────────────────────────────
เวอร์ชันแรกของไฟล์นี้เขียนเฉลยเป็น "เซตที่ต้องตรงเป๊ะ" แล้ววัดได้ 28.6%
ซึ่ง "ผิดที่เฉลย ไม่ใช่ผิดที่ระบบ" — classify_query() ใส่ chroma เข้าไปใน
ทุกคำถามโดยตั้งใจ (retriever.py: "─── 4. Chroma (always) ───") เพื่อให้ LLM
มีบริบทสำรองเสมอ เฉลยที่ไม่นับ chroma จึงทำให้เคสที่ระบบทำถูกถูกนับว่าผิด

เวอร์ชันนี้แยกเป็น 2 ฝั่งซึ่งตรงกับสิ่งที่อยากรู้จริง:

    require : source ที่ "ต้องมี" — ไม่มีคือพลาดของจริง (วัด recall)
    forbid  : source ที่ "ห้ามมี" — มีคือ trigger เหวี่ยงแห (วัด precision)

chroma ถือเป็น source กลาง ไม่นับทั้งสองฝั่ง เว้นแต่ระบุใน forbid เอง
ตัวชี้วัดหลักคือ require-recall กับ forbid-respected ส่วนจำนวน source
ส่วนเกินรายงานแยกไว้ให้เห็นว่ามี noise เข้า context มากแค่ไหน

อ้างอิงนิยามตัวชี้วัด: Manning, Raghavan & Schütze (2008),
Introduction to Information Retrieval, บทที่ 8

─────────────────────────────────────────────────────────────────────
วิธีเพิ่มเคสทดสอบ
─────────────────────────────────────────────────────────────────────
เพิ่ม dict ใน ROUTING_CASES โดยระบุ require และ/หรือ forbid
ควรมีทั้ง positive case และ negative case — negative case สำคัญกว่า
เพราะเป็นตัววัด precision ของ trigger ซึ่งเป็นจุดที่ rule-based พังบ่อยที่สุด
"""

import os
from collections import defaultdict

# เคสทดสอบ KG ต้องการให้ KG เปิด (ค่า default ของ retriever คือเปิดอยู่แล้ว)
os.environ.setdefault("CSIT_ENABLE_KG", "1")

from src.retriever import classify_query  # noqa: E402

# source ที่ระบบใส่ให้ทุกคำถามโดยตั้งใจ — ไม่นับเป็นความผิดถ้าโผล่มา
NEUTRAL_SOURCES = {"chroma"}


ROUTING_CASES = [
    # ── Rule engine: เกียรตินิยม ────────────────────────────
    {"q": "GPA 3.30 ได้เกียรตินิยมไหม", "require": {"rule_honor"}},
    {"q": "เกรดเฉลี่ย 3.55 ได้เกียรตินิยมอันดับอะไร", "require": {"rule_honor"}},
    # ถามเกณฑ์ลอย ๆ ไม่มีตัวเลข → ไม่ควรปลุก rule engine
    {"q": "เกณฑ์เกียรตินิยมของมหาวิทยาลัยเป็นยังไง", "forbid": {"rule_honor"}},

    # ── Rule engine: ค่าปรับล่าช้า ──────────────────────────
    {"q": "ลงทะเบียนช้า 5 วัน เสียค่าปรับเท่าไร", "require": {"rule_late_fee"}},
    {"q": "ลงทะเบียนช้าไป 20 วันแล้วจะเป็นยังไง", "require": {"rule_late_fee"}},
    {"q": "ลงทะเบียนล่าช้ามีค่าปรับไหม", "forbid": {"rule_late_fee"}},

    # ── Rule engine: หน่วยกิต ───────────────────────────────
    {"q": "ลง 25 หน่วยกิตได้ไหม", "require": {"rule_credit"}},
    {"q": "อยากลงทะเบียนเกิน 22 หน่วยกิตต่อภาคต้องทำยังไง", "require": {"rule_credit"}},

    # ── Rule engine: สถานภาพนิสิต ───────────────────────────
    # ⚠️ รู้อยู่แล้วว่าเคสนี้ปลุก rule_honor ตามมาด้วย (ตัวเลข GPA ไปเข้าเงื่อนไข
    #    เกียรตินิยม) จึงยังไม่ใส่ rule_honor ใน forbid — ถ้าแก้ให้แยกเจตนาได้
    #    เมื่อไหร่ ค่อยเพิ่ม forbid แล้วเคสนี้จะฟ้องให้รู้
    {"q": "GPA 1.65 เรียนมา 3 ภาค สถานภาพเป็นยังไง", "require": {"rule_status"}},

    # ── KG: กวาดทุกคนแล้วกรองคุณสมบัติ ──────────────────────
    {"q": "อาจารย์ที่ปรึกษาที่จบปริญญาเอกจากต่างประเทศมีใครบ้าง",
     "require": {"sqlite_kg_foreign_phd"}},
    {"q": "อาจารย์ที่จบเอกต่างประเทศมีกี่ท่าน",
     "require": {"sqlite_kg_foreign_phd"}, "forbid": {"sqlite_instructors"}},
    {"q": "อาจารย์คนไหนจบ ป.เอก จากเมืองนอกบ้าง",
     "require": {"sqlite_kg_foreign_phd"}},
    {"q": "อาจารย์ที่จบปริญญาเอกมีกี่ท่าน", "require": {"sqlite_kg_foreign_phd"}},

    # negative ของ KG — สำคัญที่สุด เพราะวัดว่า trigger ไม่เหวี่ยงแห
    {"q": "ต้องจบปริญญาเอกไหมถึงจะเป็นอาจารย์ได้",
     "forbid": {"sqlite_kg_foreign_phd"}},
    # "จบเอก" ที่หมายถึงวิชาเอก ไม่ใช่ปริญญาเอก
    {"q": "อาจารย์จบเอกคอมพิวเตอร์มีใครบ้าง", "forbid": {"sqlite_kg_foreign_phd"}},
    {"q": "อาจารย์ที่จบเอกมีกี่คน", "forbid": {"sqlite_kg_foreign_phd"}},
    # มีชื่อคนเจาะจง → ต้องไปรายบุคคล ไม่ใช่กวาดทั้งภาควิชา
    {"q": "อาจารย์สัญญาจบปริญญาเอกจากที่ไหน",
     "require": {"sqlite_instructors"}, "forbid": {"sqlite_kg_foreign_phd"}},

    # ── SQLite: อาจารย์รายบุคคล ─────────────────────────────
    {"q": "อาจารย์เทวินจบจากที่ไหน", "require": {"sqlite_instructors"}},
    {"q": "อีเมลอาจารย์จักรกฤษณ์คืออะไร", "require": {"sqlite_instructors"}},
    {"q": "จรัสศรีอยู่ห้องไหน", "require": {"sqlite_instructors"}},

    # ── NU form ─────────────────────────────────────────────
    {"q": "NU18 คือแบบฟอร์มอะไร", "require": {"sqlite_forms"}},
    {"q": "ขั้นตอนการยื่น NU7 ทำยังไง", "require": {"sqlite_forms"}},

    # ── RAG ล้วน — ไม่ควรปลุก rule/sqlite ใด ๆ ──────────────
    {"q": "หลักสูตร CS ต้องเรียนกี่หน่วยกิตจึงจะจบ",
     "forbid": {"rule_credit", "sqlite_instructors"}},
    {"q": "สหกิจศึกษาต้องเตรียมตัวยังไง",
     "forbid": {"sqlite_staff", "sqlite_instructors"}},
]


def evaluate():
    req_hit = req_total = 0
    forbid_ok = forbid_total = 0
    clean_cases = 0            # ไม่พลาด require และไม่ละเมิด forbid
    exact_cases = 0            # เหมือนข้างบน + ไม่มี source ส่วนเกินเลย
    extra_counter = defaultdict(int)
    problems = []

    for case in ROUTING_CASES:
        got = set(classify_query(case["q"]).sources_to_use)
        require = case.get("require", set())
        forbid = case.get("forbid", set())

        missing = require - got
        violated = forbid & got
        extra = got - require - NEUTRAL_SOURCES - forbid

        req_hit += len(require & got)
        req_total += len(require)
        forbid_ok += len(forbid - got)
        forbid_total += len(forbid)

        if not missing and not violated:
            clean_cases += 1
            if not extra:
                exact_cases += 1
        else:
            problems.append((case["q"], sorted(missing), sorted(violated), sorted(got)))

        for s in extra:
            extra_counter[s] += 1

    n = len(ROUTING_CASES)
    print("🧭 ประเมินความแม่นของตัวจัดเส้นทาง (rule-based router)")
    print("=" * 68)
    print(f"\nเคสที่ผ่าน (ไม่พลาด require + ไม่ละเมิด forbid): "
          f"{clean_cases}/{n} = {clean_cases/n:.1%}")
    print(f"   ในจำนวนนี้ ไม่มี source ส่วนเกินเลย: {exact_cases}/{n}")
    if req_total:
        print(f"\nRequire recall  : {req_hit}/{req_total} = {req_hit/req_total:.1%}"
              "   (ดึง source ที่ต้องใช้มาครบไหม)")
    if forbid_total:
        print(f"Forbid respected: {forbid_ok}/{forbid_total} = "
              f"{forbid_ok/forbid_total:.1%}   (เว้น source ที่ไม่ควรแตะได้ไหม)")

    if extra_counter:
        print("\nsource ส่วนเกินที่โผล่บ่อย (ไม่ถือว่าผิด แต่เพิ่ม noise ใน context):")
        for s, c in sorted(extra_counter.items(), key=lambda x: -x[1]):
            print(f"   {s}: {c} เคส")

    if problems:
        print(f"\n❌ เคสที่มีปัญหา {len(problems)} ข้อ:")
        for q, missing, violated, got in problems:
            print(f"\n   {q}")
            if missing:
                print(f"      ขาด source ที่ต้องมี: {missing}")
            if violated:
                print(f"      มี source ที่ห้ามมี:  {violated}")
            print(f"      ได้จริง: {got}")
    else:
        print("\n✅ ผ่านทุกเคส")

    return clean_cases / n


if __name__ == "__main__":
    evaluate()
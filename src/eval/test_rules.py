"""
test_rules.py — ชุดทดสอบ Rule Engine (RAR) ด้วย Boundary Value Analysis

รัน:  python -m src.eval.test_rules

⚡ ไม่เรียก LLM เลย ไม่เสียโควตา รันซ้ำได้ไม่จำกัด เหมาะเป็น regression test
   ทุกครั้งที่แก้ rules.yaml หรือ rules.py

─────────────────────────────────────────────────────────────────────
ทำไมต้องทดสอบแยกจาก RAGAS
─────────────────────────────────────────────────────────────────────
RAGAS ใช้ LLM เป็นกรรมการตัดสิน ซึ่งตัวกรรมการเองก็ตัดสินผิดได้ (พบ false
negative จริงใน Session 8 id 18) การเอากรรมการที่ไม่แน่นอนมาตัดสินฟังก์ชัน
ที่ deterministic 100% คือการเพิ่ม noise เปล่า ๆ

Rule engine เป็นฟังก์ชันบริสุทธิ์ input เดิม → output เดิมเสมอ จึงวัดด้วย
exact-match ได้ตรง ๆ ผลลัพธ์ควรผ่าน 100% ทุกครั้ง ถ้าไม่ผ่าน = มีบั๊กจริง
ไม่ใช่ความคลาดเคลื่อนของการวัด

─────────────────────────────────────────────────────────────────────
วิธีออกแบบเคสทดสอบ: Boundary Value Analysis
─────────────────────────────────────────────────────────────────────
บั๊กของ rule engine เกือบทั้งหมดซ่อนอยู่ที่ "เส้นแบ่ง" (ใช้ > แทน >= เป็นต้น)
จึงทดสอบ 3 จุดรอบทุกเส้นแบ่ง: ต่ำกว่าเส้น / บนเส้นพอดี / เหนือเส้น
พร้อมกับ equivalence partitioning (ตัวแทนของแต่ละช่วงค่า)

อ้างอิง: Myers, G. J., Badgett, T., & Sandler, C. (2011).
         The Art of Software Testing (3rd ed.). Wiley. บทที่ 4-5
"""

import sys

from src.database.rules import (
    load_rules,
    calculate_honor,
    calculate_late_fee,
    check_credit_limit,
    check_academic_status,
    is_loan_query,
    is_calendar_query,
)

_passed = 0
_failed: list[str] = []


def check_raises(label: str, fn, *args, exc=ValueError) -> None:
    """เคสที่ต้องโยน exception — ใช้กับการตรวจ input ที่เพิ่มเข้ามา"""
    global _passed
    try:
        result = fn(*args)
    except exc:
        _passed += 1
        print(f"  ✅ {label}")
    except Exception as e:
        _failed.append(label)
        print(f"  ❌ {label}\n       โยน {type(e).__name__} แทน {exc.__name__}")
    else:
        _failed.append(label)
        print(f"  ❌ {label}\n       ไม่โยน exception เลย — คืน {result!r}")


def check(label: str, got, want) -> None:
    global _passed
    if got == want:
        _passed += 1
        print(f"  ✅ {label}")
    else:
        _failed.append(label)
        print(f"  ❌ {label}\n       ได้: {got!r}\n       ควรได้: {want!r}")

def test_honor():
    r = load_rules()["graduation"]["honors"]
    first = r["first_class"]["name"]
    second = r["second_class"]["name"]
    print("\n── 1. เกียรตินิยม (เส้นแบ่ง 3.25 / 3.50) ──")
    check("GPA 3.24 → ไม่ได้เกียรตินิยม", calculate_honor(3.24), None)
    check("GPA 3.25 → อันดับสอง (บนเส้นพอดี)", calculate_honor(3.25), second)
    check("GPA 3.26 → อันดับสอง", calculate_honor(3.26), second)
    check("GPA 3.49 → อันดับสอง", calculate_honor(3.49), second)
    check("GPA 3.50 → อันดับหนึ่ง (บนเส้นพอดี)", calculate_honor(3.50), first)
    check("GPA 3.51 → อันดับหนึ่ง", calculate_honor(3.51), first)
    check("GPA 2.00 → ไม่ได้เกียรตินิยม", calculate_honor(2.00), None)
    check("GPA 4.00 → อันดับหนึ่ง", calculate_honor(4.00), first)
    check("GPA 3.495 → อันดับสอง (เดิมตกร่องคืน None)", calculate_honor(3.495), second)
    check("GPA 3.499 → อันดับสอง", calculate_honor(3.499), second)
    check("GPA 5.00 (นอกช่วง) → None", calculate_honor(5.00), None)
    check("GPA -1.00 (นอกช่วง) → None", calculate_honor(-1.00), None)


def test_late_fee():
    r = load_rules()["registration"]["late_registration"]
    per_day = r["penalty_per_day"]
    max_days = r["max_late_weeks_before_dismissed"] * 7
    print(f"\n── 2. ค่าปรับล่าช้า (เส้นแบ่ง {max_days} วัน, {per_day} บาท/วัน) ──")

    check("ช้า 1 วัน → ยังลงได้", calculate_late_fee(1)["status"], "ยังลงได้")
    check("ช้า 1 วัน → ค่าปรับถูกต้อง", calculate_late_fee(1)["total_fee"], per_day)

    check(
        f"ช้า {max_days-1} วัน → ยังลงได้",
        calculate_late_fee(max_days - 1)["status"],
        "ยังลงได้",
    )
    check(
        f"ช้า {max_days} วัน → ยังลงได้ (บนเส้นพอดี)",
        calculate_late_fee(max_days)["status"],
        "ยังลงได้",
    )
    check(
        f"ช้า {max_days} วัน → เหลือ 0 วัน",
        calculate_late_fee(max_days)["remaining_days"],
        0,
    )
    check(
        f"ช้า {max_days+1} วัน → พ้นสภาพ",
        calculate_late_fee(max_days + 1)["status"],
        "พ้นสภาพ",
    )

    check(
        "ช้า 5 วัน → ค่าปรับ = 5 × per_day",
        calculate_late_fee(5)["total_fee"],
        5 * per_day,
    )

    check(
        "ช้า 0 วัน → ค่าปรับ 0 (ควรเป็นเคส 'ไม่ล่าช้า' ต่างหาก)",
        calculate_late_fee(0)["total_fee"],
        0,
    )
    check_raises("ช้า -3 วัน → raise ValueError", calculate_late_fee, -3)

def test_credit_limit():
    r = load_rules()["registration"]["credit_limits"]["undergraduate"]
    normal, summer = r["normal_semester_max"], r["summer_max"]
    print(f"\n── 3. หน่วยกิต (ภาคปกติ {normal} / ฤดูร้อน {summer}) ──")

    check(f"ลง {normal-1} → ได้", check_credit_limit(normal - 1)["allowed"], True)
    check(
        f"ลง {normal} → ได้ (บนเส้นพอดี)", check_credit_limit(normal)["allowed"], True
    )
    check(f"ลง {normal+1} → ไม่ได้", check_credit_limit(normal + 1)["allowed"], False)
    check(f"ลง {normal+1} → เกิน 1 หน่วยกิต", check_credit_limit(normal + 1)["over"], 1)

    check(
        f"ฤดูร้อน {summer} → ได้", check_credit_limit(summer, "summer")["allowed"], True
    )
    check(
        f"ฤดูร้อน {summer+1} → ไม่ได้",
        check_credit_limit(summer + 1, "summer")["allowed"],
        False,
    )

    check_raises(
        "semester='ภาคต้น' → raise ValueError (เดิมมองเป็นฤดูร้อนเงียบ ๆ)",
        check_credit_limit,
        15,
        "ภาคต้น",
    )
    check_raises(
        "semester='Normal' (ตัวใหญ่) → raise ValueError",
        check_credit_limit,
        15,
        "Normal",
    )
    check_raises("ลง -5 หน่วยกิต → raise ValueError", check_credit_limit, -5)


def test_academic_status():
    r = load_rules()["academic_status"]["dismissal_by_gpa"]
    t2 = r["after_2_semesters"]["threshold"]
    t4 = r["after_4_or_more_semesters"]["threshold"]
    print(f"\n── 4. สถานภาพนิสิต (2 ภาค <{t2} / 4 ภาค <{t4} / รอพินิจ <2.00) ──")

    st = lambda g, s: check_academic_status(g, s)["status"]

    check(f"GPA {t2-0.01}, 2 ภาค → พ้นสภาพ", st(t2 - 0.01, 2), "พ้นสภาพ")
    check(f"GPA {t2}, 2 ภาค → ไม่พ้นสภาพ (บนเส้นพอดี)", st(t2, 2), "รอพินิจ")

    check(f"GPA {t4-0.01}, 4 ภาค → พ้นสภาพ", st(t4 - 0.01, 4), "พ้นสภาพ")
    check(f"GPA {t4}, 4 ภาค → ไม่พ้นสภาพ (บนเส้นพอดี)", st(t4, 4), "รอพินิจ")
    check(f"GPA {t4-0.01}, 6 ภาค → พ้นสภาพ", st(t4 - 0.01, 6), "พ้นสภาพ")

    check("GPA 1.99, 1 ภาค → รอพินิจ", st(1.99, 1), "รอพินิจ")
    check("GPA 2.00, 1 ภาค → ปกติ (บนเส้นพอดี)", st(2.00, 1), "ปกติ")
    check("GPA 3.50, 8 ภาค → ปกติ", st(3.50, 8), "ปกติ")

    check(
        f"GPA {t2-0.1}, 3 ภาค → พ้นสภาพ (ต้องยืนยันกับข้อบังคับ)",
        st(t2 - 0.1, 3),
        "พ้นสภาพ",
    )

def test_redirects():
    print("\n── 5. Redirect (กยศ. / ปฏิทินการศึกษา) ──")
    check("'อยากกู้ยืม กยศ' → loan", is_loan_query("อยากกู้ยืม กยศ"), True)
    check("'ดอกเบี้ยเท่าไร' → loan", is_loan_query("ดอกเบี้ยเท่าไร"), True)
    check(
        "'ลงทะเบียนช้า 5 วัน' → ไม่ใช่ loan", is_loan_query("ลงทะเบียนช้า 5 วัน"), False
    )
    check(
        "'ขอทุนการศึกษาภาควิชา' → ไม่ใช่ loan",
        is_loan_query("ขอทุนการศึกษาภาควิชา"),
        False,
    )

    check("'เปิดเทอมวันไหน' → calendar", is_calendar_query("เปิดเทอมวันไหน"), True)
    check(
        "'ปฏิทินการศึกษาดูที่ไหน' → calendar",
        is_calendar_query("ปฏิทินการศึกษาดูที่ไหน"),
        True,
    )
    check("'ลงทะเบียนวันไหน' → calendar", is_calendar_query("ลงทะเบียนวันไหน"), True)
    check(
        "'สอบปลายภาคเมื่อไหร่' → calendar",
        is_calendar_query("สอบปลายภาคเมื่อไหร่"),
        True,
    )
    check(
        "'ลงทะเบียนยังไง' → ไม่ใช่ calendar", is_calendar_query("ลงทะเบียนยังไง"), False
    )
    check(
        "'ค่าเทอมเท่าไร' → ไม่ใช่ calendar", is_calendar_query("ค่าเทอมเท่าไร"), False
    )


def test_no_hardcoded_thresholds():
    print("\n── 6. ค่าเกณฑ์อ่านจาก rules.yaml จริงไหม ──")
    rules = load_rules()

    original = rules["registration"]["credit_limits"]["undergraduate"][
        "normal_semester_max"
    ]
    try:
        rules["registration"]["credit_limits"]["undergraduate"][
            "normal_semester_max"
        ] = 18
        check(
            "แก้ normal_semester_max เป็น 18 → ลง 20 ต้องไม่ผ่าน",
            check_credit_limit(20)["allowed"],
            False,
        )
    finally:
        rules["registration"]["credit_limits"]["undergraduate"][
            "normal_semester_max"
        ] = original

    prob = rules["academic_status"]["definitions"]["probation"]
    original_p = prob.get("threshold")
    if original_p is None:
        _failed.append("rules.yaml ยังไม่มี probation.threshold")
        print(
            "   rules.yaml ยังไม่มี academic_status.definitions.probation.threshold"
        )
    else:
        try:
            prob["threshold"] = 1.90
            check(
                "แก้ probation.threshold เป็น 1.90 → GPA 1.95 ต้องเป็น 'ปกติ'",
                check_academic_status(1.95, 1)["status"],
                "ปกติ",
            )
        finally:
            prob["threshold"] = original_p

    original_h = rules["graduation"]["honors"]["first_class"]["min_gpa"]
    try:
        rules["graduation"]["honors"]["first_class"]["min_gpa"] = 3.75
        check(
            "แก้ first_class.min_gpa เป็น 3.75 → GPA 3.60 ต้องได้อันดับสอง หรือ None",
            calculate_honor(3.60)
            != rules["graduation"]["honors"]["first_class"]["name"],
            True,
        )
    finally:
        rules["graduation"]["honors"]["first_class"]["min_gpa"] = original_h


def main():
    print(" ทดสอบ Rule Engine ด้วย Boundary Value Analysis")
    print("=" * 62)

    test_honor()
    test_late_fee()
    test_credit_limit()
    test_academic_status()
    test_redirects()
    test_no_hardcoded_thresholds()

    total = _passed + len(_failed)
    print("\n" + "=" * 62)
    print(f"ผลรวม: ผ่าน {_passed}/{total}")
    if _failed:
        print(f"\n ไม่ผ่าน {len(_failed)} เคส:")
        for name in _failed:
            print(f"   - {name}")
        sys.exit(1)
    print("ผ่านทั้งหมด")


if __name__ == "__main__":
    main()

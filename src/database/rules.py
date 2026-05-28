"""
Rule Engine - Rule-Augmented Reasoning (RAR)
โหลดและใช้งาน rules.yaml

Path mapping (rules.yaml ใหม่):
  honors         → graduation.honors
  penalties      → registration.late_registration + registration.add_drop
  registration_credits → registration.credit_limits
  academic_status      → academic_status
  student_loan         → student_loan (ใหม่: redirect policy)
"""

import yaml
from typing import Optional
from src.config import RULES_PATH


# ══════════════════════════════════════════════════════════════
# Loader (cache ไว้ในหน่วยความจำ — reload ได้เสมอ)
# ══════════════════════════════════════════════════════════════

_rules_cache: Optional[dict] = None


def load_rules(force_reload: bool = False) -> dict:
    """โหลดกฎจาก rules.yaml (cache หลังโหลดครั้งแรก)"""
    global _rules_cache
    if _rules_cache is None or force_reload:
        if not RULES_PATH.exists():
            raise FileNotFoundError(f"ไม่พบ {RULES_PATH}")
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            _rules_cache = yaml.safe_load(f)
    return _rules_cache


# ══════════════════════════════════════════════════════════════
# 1. เกียรตินิยม
# path: graduation.honors
# ══════════════════════════════════════════════════════════════

def calculate_honor(gpa: float) -> Optional[str]:
    """คำนวณเกียรตินิยมจาก GPA"""
    honors = load_rules()["graduation"]["honors"]

    if gpa >= honors["first_class"]["min_gpa"]:
        return honors["first_class"]["name"]
    elif honors["second_class"]["min_gpa"] <= gpa <= honors["second_class"]["max_gpa"]:
        return honors["second_class"]["name"]
    return None


# ══════════════════════════════════════════════════════════════
# 2. ค่าปรับลงทะเบียนล่าช้า
# path: registration.late_registration
# ══════════════════════════════════════════════════════════════

def calculate_late_fee(days_late: int) -> dict:
    """คำนวณค่าปรับลงทะเบียนล่าช้า"""
    r = load_rules()["registration"]["late_registration"]

    per_day      = r["penalty_per_day"]               # 25 บาท/วัน
    max_weeks    = r["max_late_weeks_before_dismissed"] # 2 สัปดาห์
    max_days     = max_weeks * 7                        # = 14 วัน
    fee_ug       = r["reinstatement_fee_undergraduate"] # 1000 บาท
    form         = r["reinstatement_form"]              # NU7

    if days_late > max_days:
        return {
            "status": "พ้นสภาพ",
            "message": f"เกิน {max_days} วันแล้ว ต้องยื่นคำร้อง {form}",
            "reinstatement_fee": fee_ug,
        }

    return {
        "status": "ยังลงได้",
        "days_late": days_late,
        "fee_per_day": per_day,
        "total_fee": days_late * per_day,
        "remaining_days": max_days - days_late,
    }


# ══════════════════════════════════════════════════════════════
# 3. หน่วยกิตที่ลงได้
# path: registration.credit_limits
# ══════════════════════════════════════════════════════════════

def check_credit_limit(credits: int, semester: str = "normal") -> dict:
    """ตรวจสอบหน่วยกิตที่ลงได้ต่อภาค"""
    r = load_rules()["registration"]["credit_limits"]["undergraduate"]

    max_credits = (
        r["normal_semester_max"] if semester == "normal" else r["summer_max"]
    )

    if credits > max_credits:
        return {
            "allowed": False,
            "limit": max_credits,
            "requested": credits,
            "over": credits - max_credits,
            "message": f"ลงเกิน {credits - max_credits} หน่วยกิต ต้องยื่น NU18",
        }

    return {
        "allowed": True,
        "limit": max_credits,
        "requested": credits,
    }


# ══════════════════════════════════════════════════════════════
# 4. สถานภาพนิสิต
# path: academic_status
# ══════════════════════════════════════════════════════════════

def check_academic_status(gpa: float, semesters_completed: int) -> dict:
    """ตรวจสอบสถานภาพนิสิตจาก GPA และจำนวนภาคที่เรียน"""
    r = load_rules()["academic_status"]

    threshold_4 = r["dismissal_by_gpa"]["after_4_or_more_semesters"]["threshold"]
    threshold_2 = r["dismissal_by_gpa"]["after_2_semesters"]["threshold"]
    probation   = r["definitions"]["probation"]["condition"]  # "GPA สะสม < 2.00"
    # ดึงตัวเลข 2.00 จาก condition string
    probation_threshold = 2.00

    if semesters_completed >= 4 and gpa < threshold_4:
        return {
            "status": "พ้นสภาพ",
            "reason": f"GPA {gpa} ต่ำกว่า {threshold_4} หลัง {semesters_completed} ภาค",
        }
    if semesters_completed >= 2 and gpa < threshold_2:
        return {
            "status": "พ้นสภาพ",
            "reason": f"GPA {gpa} ต่ำกว่า {threshold_2} หลัง {semesters_completed} ภาค",
        }
    if gpa < probation_threshold:
        return {
            "status": "รอพินิจ",
            "reason": f"GPA {gpa} ต่ำกว่า {probation_threshold}",
        }

    return {"status": "ปกติ", "gpa": gpa}


# ══════════════════════════════════════════════════════════════
# 5. กยศ. Redirect  (ใหม่)
# path: student_loan
# ══════════════════════════════════════════════════════════════

def get_loan_keywords() -> list[str]:
    """ดึง keywords ที่ใช้ detect คำถามเรื่อง กยศ."""
    return load_rules()["student_loan"]["bot_policy"]["keywords_to_detect"]


def get_loan_redirect_template() -> str:
    """ดึง response template สำหรับ redirect กยศ."""
    return load_rules()["student_loan"]["response_template"]


def is_loan_query(question: str) -> bool:
    """ตรวจว่าคำถามเกี่ยวกับ กยศ. หรือไม่"""
    q = question.lower()
    return any(kw.lower() in q for kw in get_loan_keywords())


# ══════════════════════════════════════════════════════════════
# Self-test
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧪 ทดสอบ Rules Engine (rules.yaml ใหม่)\n")

    print("── เกียรตินิยม ──")
    print(f"  GPA 3.55 → {calculate_honor(3.55)}")
    print(f"  GPA 3.30 → {calculate_honor(3.30)}")
    print(f"  GPA 2.80 → {calculate_honor(2.80)}")

    print("\n── ค่าปรับลงทะเบียนล่าช้า ──")
    print(f"  ช้า 5 วัน  → {calculate_late_fee(5)}")
    print(f"  ช้า 14 วัน → {calculate_late_fee(14)}")
    print(f"  ช้า 15 วัน → {calculate_late_fee(15)}")

    print("\n── หน่วยกิต ──")
    print(f"  20 หน่วย (ปกติ) → {check_credit_limit(20)}")
    print(f"  24 หน่วย (ปกติ) → {check_credit_limit(24)}")
    print(f"  9 หน่วย (ฤดูร้อน) → {check_credit_limit(9, 'summer')}")
    print(f"  10 หน่วย (ฤดูร้อน) → {check_credit_limit(10, 'summer')}")

    print("\n── สถานภาพนิสิต ──")
    print(f"  GPA 1.65, 3 ภาค → {check_academic_status(1.65, 3)}")
    print(f"  GPA 1.40, 2 ภาค → {check_academic_status(1.40, 2)}")
    print(f"  GPA 1.70, 4 ภาค → {check_academic_status(1.70, 4)}")
    print(f"  GPA 1.90, 4 ภาค → {check_academic_status(1.90, 4)}")
    print(f"  GPA 2.50, 4 ภาค → {check_academic_status(2.50, 4)}")

    print("\n── กยศ. Redirect ──")
    print(f"  'อยากกู้ กยศ.'       → is_loan: {is_loan_query('อยากกู้ กยศ.')}")
    print(f"  'ดอกเบี้ยเท่าไร'     → is_loan: {is_loan_query('ดอกเบี้ยเท่าไร')}")
    print(f"  'ลงทะเบียนช้า 5 วัน' → is_loan: {is_loan_query('ลงทะเบียนช้า 5 วัน')}")
    print(f"\n  Template:\n{get_loan_redirect_template()}")
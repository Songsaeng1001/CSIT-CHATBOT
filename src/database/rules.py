"""
ทดสอบทั้งหมดด้วย:  python -m src.eval.test_rules
"""

import yaml
from typing import Optional
from src.config import RULES_PATH

GPA_MIN = 0.00
GPA_MAX = 4.00

_PROBATION_FALLBACK = 2.00
_warned_probation = False
_rules_cache: Optional[dict] = None
_rules_loaded = False


def load_rules(force_reload: bool = False) -> dict:
    global _rules_cache, _rules_loaded
    if not _rules_loaded or force_reload:
        if not RULES_PATH.exists():
            raise FileNotFoundError(f"ไม่พบ {RULES_PATH}")
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            _rules_cache = yaml.safe_load(f)
        if not _rules_cache:
            raise ValueError(f"{RULES_PATH} ว่างเปล่าหรืออ่านไม่ได้")
        _rules_loaded = True
    return _rules_cache


def calculate_honor(gpa: float) -> Optional[str]:
    if not (GPA_MIN <= gpa <= GPA_MAX):
        return None

    honors = load_rules()["graduation"]["honors"]

    if gpa >= honors["first_class"]["min_gpa"]:
        return honors["first_class"]["name"]
    if gpa >= honors["second_class"]["min_gpa"]:
        return honors["second_class"]["name"]
    return None


def get_honor_min_gpa() -> float:
    return load_rules()["graduation"]["honors"]["second_class"]["min_gpa"]

def get_max_late_days() -> int:
    r = load_rules()["registration"]["late_registration"]
    return r["max_late_weeks_before_dismissed"] * 7


def calculate_late_fee(days_late: int) -> dict:
    if days_late < 0:
        raise ValueError(f"days_late ต้องไม่ติดลบ (ได้ {days_late})")

    r = load_rules()["registration"]["late_registration"]

    per_day  = r["penalty_per_day"]                   
    max_days = r["max_late_weeks_before_dismissed"] * 7  
    fee_ug   = r["reinstatement_fee_undergraduate"]     
    form     = r["reinstatement_form"]                  

    if days_late > max_days:
        return {
            "status": "พ้นสภาพ",
            "message": f"เกิน {max_days} วันแล้ว ต้องยื่นคำร้อง {form}",
            "reinstatement_fee": fee_ug,
            "max_days": max_days,
        }

    return {
        "status": "ยังลงได้",
        "days_late": days_late,
        "fee_per_day": per_day,
        "total_fee": days_late * per_day,
        "remaining_days": max_days - days_late,
        "max_days": max_days,
    }

VALID_SEMESTERS = ("normal", "summer")


def check_credit_limit(credits: int, semester: str = "normal") -> dict:
    if credits < 0:
        raise ValueError(f"credits ต้องไม่ติดลบ (ได้ {credits})")
    if semester not in VALID_SEMESTERS:
        raise ValueError(
            f"semester ต้องเป็นหนึ่งใน {VALID_SEMESTERS} (ได้ {semester!r})"
        )

    r = load_rules()["registration"]["credit_limits"]["undergraduate"]
    max_credits = (
        r["normal_semester_max"] if semester == "normal" else r["summer_max"]
    )
    over_form = r.get("over_limit_form", "NU18")

    if credits > max_credits:
        return {
            "allowed": False,
            "limit": max_credits,
            "requested": credits,
            "semester": semester,
            "over": credits - max_credits,
            "message": f"ลงเกิน {credits - max_credits} หน่วยกิต ต้องยื่น {over_form}",
        }

    return {
        "allowed": True,
        "limit": max_credits,
        "requested": credits,
        "semester": semester,
    }

def get_probation_threshold() -> float:
    global _warned_probation
    probation = load_rules()["academic_status"]["definitions"]["probation"]
    threshold = probation.get("threshold")

    if threshold is None:
        if not _warned_probation:
            print(
                " rules.yaml ยังไม่มี academic_status.definitions.probation.threshold "
                f"— ใช้ค่าสำรอง {_PROBATION_FALLBACK:.2f} ไปก่อน"
            )
            _warned_probation = True
        return _PROBATION_FALLBACK

    return float(threshold)


def check_academic_status(gpa: float, semesters_completed: int) -> dict:
    if semesters_completed < 0:
        raise ValueError(
            f"semesters_completed ต้องไม่ติดลบ (ได้ {semesters_completed})"
        )

    r = load_rules()["academic_status"]
    threshold_4 = r["dismissal_by_gpa"]["after_4_or_more_semesters"]["threshold"]
    threshold_2 = r["dismissal_by_gpa"]["after_2_semesters"]["threshold"]
    probation_threshold = get_probation_threshold()

    if semesters_completed >= 4 and gpa < threshold_4:
        return {
            "status": "พ้นสภาพ",
            "reason": f"GPA {gpa} ต่ำกว่า {threshold_4} หลัง {semesters_completed} ภาค",
            "threshold": threshold_4,
        }

    if semesters_completed >= 2 and gpa < threshold_2:
        return {
            "status": "พ้นสภาพ",
            "reason": f"GPA {gpa} ต่ำกว่า {threshold_2} หลัง {semesters_completed} ภาค",
            "threshold": threshold_2,
        }

    if gpa < probation_threshold:
        return {
            "status": "รอพินิจ",
            "reason": f"GPA {gpa} ต่ำกว่า {probation_threshold}",
            "threshold": probation_threshold,
        }

    return {"status": "ปกติ", "gpa": gpa}

def get_loan_keywords() -> list[str]:
    return load_rules()["student_loan"]["bot_policy"]["keywords_to_detect"]


def get_loan_redirect_template() -> str:
    return load_rules()["student_loan"]["response_template"]


def is_loan_query(question: str) -> bool:
    q = question.lower()
    return any(kw.lower() in q for kw in get_loan_keywords())

_CALENDAR_FALLBACK_TEMPLATE = (
    "เรื่องวันเปิด-ปิดเทอม วันลงทะเบียน หรือกำหนดการต่าง ๆ "
    "แนะนำให้ดูจากปฏิทินการศึกษาของมหาวิทยาลัยโดยตรงนะคะ "
    "เพราะวันที่จะเปลี่ยนทุกภาคเรียนค่ะ \n\n"
    "ปฏิทินการศึกษา: https://reg4.nu.ac.th/registrar/calendar.asp?avs727811069=1\n"
    "ภาควิชา CSIT 055-963262, 055-963263"
)


def _calendar_policy() -> dict:
    return load_rules().get("academic_calendar", {}).get("bot_policy", {})


def get_calendar_redirect_template() -> str:
    return load_rules().get("academic_calendar", {}).get(
        "response_template", _CALENDAR_FALLBACK_TEMPLATE
    )


def is_calendar_query(question: str) -> bool:
    q = question.lower()
    pol = _calendar_policy()

    if any(kw.lower() in q for kw in pol.get("direct_keywords", [])):
        return True

    has_topic = any(kw.lower() in q for kw in pol.get("topic_keywords", []))
    has_when = any(kw.lower() in q for kw in pol.get("when_keywords", []))
    return has_topic and has_when

if __name__ == "__main__":
    print("ทดสอบ Rules Engine\n")

    print("── เกียรตินิยม ──")
    for g in (3.55, 3.50, 3.495, 3.30, 3.25, 3.24, 2.80):
        print(f"  GPA {g:<6} → {calculate_honor(g)}")
    print(f"  GPA 5.00 (นอกช่วง) → {calculate_honor(5.00)}")

    print("\n── ค่าปรับลงทะเบียนล่าช้า ──")
    for d in (5, 14, 15):
        print(f"  ช้า {d} วัน → {calculate_late_fee(d)}")
    try:
        calculate_late_fee(-3)
    except ValueError as e:
        print(f"  ช้า -3 วัน → ValueError: {e}")

    print("\n── หน่วยกิต ──")
    print(f"  20 หน่วย (ปกติ)    → {check_credit_limit(20)}")
    print(f"  24 หน่วย (ปกติ)    → {check_credit_limit(24)}")
    print(f"  9 หน่วย (ฤดูร้อน)  → {check_credit_limit(9, 'summer')}")
    print(f"  10 หน่วย (ฤดูร้อน) → {check_credit_limit(10, 'summer')}")
    try:
        check_credit_limit(15, "ภาคต้น")
    except ValueError as e:
        print(f"  semester ไม่รู้จัก → ValueError: {e}")

    print("\n── สถานภาพนิสิต ──")
    for g, s in ((1.65, 3), (1.40, 2), (1.70, 4), (1.90, 4), (2.50, 4)):
        print(f"  GPA {g}, {s} ภาค → {check_academic_status(g, s)}")

    print("\n── กยศ. Redirect ──")
    for q in ("อยากกู้ยืม กยศ", "ดอกเบี้ยเท่าไร", "ลงทะเบียนช้า 5 วัน"):
        print(f"  {q!r:28} → {is_loan_query(q)}")

    print("\n── ปฏิทินการศึกษา Redirect ──")
    for q in ("เปิดเทอมวันไหน", "ลงทะเบียนวันไหน", "สอบปลายภาควันไหน",
              "ลงทะเบียนยังไง", "จ่ายค่าเทอมยังไง"):
        print(f"  {q!r:28} → {is_calendar_query(q)}")
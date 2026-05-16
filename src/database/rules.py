"""
Rule Engine - Rule-Augmented Reasoning
โหลดและใช้งาน rules.yaml
"""

import yaml
from typing import Optional
from src.config import RULES_PATH


def load_rules() -> dict:
    """โหลดกฎจาก rules.yaml"""
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"ไม่พบ {RULES_PATH}")
    
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ═══ Rule Functions ═══

def calculate_honor(gpa: float) -> Optional[str]:
    """คำนวณเกียรตินิยมจาก GPA"""
    rules = load_rules()["honors"]
    
    if gpa >= rules["first_class"]["min_gpa"]:
        return "เกียรตินิยมอันดับหนึ่ง"
    elif rules["second_class"]["min_gpa"] <= gpa <= rules["second_class"]["max_gpa"]:
        return "เกียรตินิยมอันดับสอง"
    return None


def calculate_late_fee(days_late: int) -> dict:
    """คำนวณค่าปรับลงทะเบียนล่าช้า"""
    rules = load_rules()["penalties"]
    per_day = rules["late_registration_per_day"]
    max_days = rules["late_registration_max_days"]
    
    if days_late > max_days:
        return {
            "status": "พ้นสภาพ",
            "message": f"เกิน {max_days} วันแล้ว ต้องยื่นคำร้อง NU7",
            "reinstatement_fee": rules["reinstatement_fee"]["undergraduate"]
        }
    
    return {
        "status": "ยังลงได้",
        "days_late": days_late,
        "fee_per_day": per_day,
        "total_fee": days_late * per_day,
        "remaining_days": max_days - days_late
    }


def check_credit_limit(credits: int, semester: str = "normal") -> dict:
    """ตรวจสอบหน่วยกิตที่ลงได้"""
    rules = load_rules()["registration_credits"]["undergraduate"]
    
    if semester == "normal":
        max_credits = rules["normal_semester_max"]
    else:
        max_credits = rules["summer_max"]
    
    if credits > max_credits:
        return {
            "allowed": False,
            "limit": max_credits,
            "requested": credits,
            "over": credits - max_credits,
            "message": f"ลงเกิน {credits - max_credits} หน่วยกิต ต้องยื่น NU18"
        }
    
    return {
        "allowed": True,
        "limit": max_credits,
        "requested": credits
    }


def check_academic_status(gpa: float, semesters_completed: int) -> dict:
    """ตรวจสอบสถานภาพนิสิต"""
    rules = load_rules()["academic_status"]
    
    if semesters_completed >= 4:
        threshold = rules["dismissal"]["after_4_semesters"]
        if gpa < threshold:
            return {
                "status": "พ้นสภาพ",
                "reason": f"GPA {gpa} ต่ำกว่า {threshold} หลัง {semesters_completed} ภาค"
            }
    elif semesters_completed >= 2:
        threshold = rules["dismissal"]["after_2_semesters"]
        if gpa < threshold:
            return {
                "status": "พ้นสภาพ",
                "reason": f"GPA {gpa} ต่ำกว่า {threshold} หลัง {semesters_completed} ภาค"
            }
    
    if gpa < rules["probation_threshold"]:
        return {
            "status": "รอพินิจ",
            "reason": f"GPA {gpa} ต่ำกว่า {rules['probation_threshold']}"
        }
    
    return {
        "status": "ปกติ",
        "gpa": gpa
    }


if __name__ == "__main__":
    print("🧪 ทดสอบ Rules:")
    print(f"   GPA 3.55 → {calculate_honor(3.55)}")
    print(f"   GPA 3.30 → {calculate_honor(3.30)}")
    print(f"   ลงทะเบียนช้า 5 วัน → {calculate_late_fee(5)}")
    print(f"   ลง 24 หน่วยกิต → {check_credit_limit(24)}")
    print(f"   GPA 1.65 หลัง 3 ภาค → {check_academic_status(1.65, 3)}")
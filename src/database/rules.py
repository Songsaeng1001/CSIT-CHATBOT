"""
Rule Engine - Rule-Augmented Reasoning (RAR)
โหลดและใช้งาน rules.yaml

Path mapping (rules.yaml ใหม่):
  honors         → graduation.honors
  penalties      → registration.late_registration + registration.add_drop
  registration_credits → registration.credit_limits
  academic_status      → academic_status
  student_loan         → student_loan (redirect policy)
  academic_calendar    → academic_calendar (redirect ปฏิทินการศึกษา)

═══════════════════════════════════════════════════════════════════
สรุปการแก้ 2026-07-23
═══════════════════════════════════════════════════════════════════
1. ปิดช่องโหว่เกียรตินิยมระหว่าง 3.49 กับ 3.50 (ค่าอย่าง 3.495 เคยตกร่อง
   ทั้งสองเงื่อนไขแล้วคืน None)
2. เกณฑ์ "รอพินิจ" อ่านจาก rules.yaml แทนการ hardcode 2.00 ไว้ในโค้ด
   ⚠️ ต้องเพิ่ม `threshold: 2.00` ใต้ academic_status.definitions.probation
      ใน rules.yaml ด้วย (ถ้ายังไม่เพิ่ม โค้ดจะเตือนแล้วใช้ 2.00 ไปก่อน)
3. เพิ่มการตรวจ input — เดิม calculate_late_fee(-3) คืนค่าปรับติดลบ
   และ check_credit_limit(-5) คืน allowed=True
4. semester ที่ไม่รู้จักเคยถูกมองเป็นภาคฤดูร้อนเงียบ ๆ ตอนนี้ raise แทน
5. ลบตัวแปร `probation` ที่อ่าน yaml มาแล้วไม่ได้ใช้

ทดสอบทั้งหมดด้วย:  python -m src.eval.test_rules
"""

import yaml
from typing import Optional
from src.config import RULES_PATH


# ช่วง GPA ที่เป็นไปได้ตามระบบของมหาวิทยาลัย
GPA_MIN = 0.00
GPA_MAX = 4.00

# ค่าสำรองของเกณฑ์รอพินิจ ใช้เฉพาะกรณี rules.yaml ยังไม่มีฟิลด์ threshold
# (จะพิมพ์เตือน 1 ครั้ง เพื่อไม่ให้เงียบหาย)
_PROBATION_FALLBACK = 2.00
_warned_probation = False


# ══════════════════════════════════════════════════════════════
# Loader (cache ไว้ในหน่วยความจำ — reload ได้เสมอ)
# ══════════════════════════════════════════════════════════════

_rules_cache: Optional[dict] = None
_rules_loaded = False


def load_rules(force_reload: bool = False) -> dict:
    """โหลดกฎจาก rules.yaml (cache หลังโหลดครั้งแรก)

    ใช้ธง _rules_loaded แยกจากตัว cache เพราะถ้า yaml ว่างเปล่า
    safe_load() จะคืน None ทำให้เงื่อนไข `_rules_cache is None` เดิม
    สั่งอ่านไฟล์ใหม่ทุกครั้งที่เรียก (cache ไม่ทำงาน)
    """
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


# ══════════════════════════════════════════════════════════════
# 1. เกียรตินิยม
# path: graduation.honors
# ══════════════════════════════════════════════════════════════

def calculate_honor(gpa: float) -> Optional[str]:
    """คำนวณเกียรตินิยมจาก GPA — คืน None ถ้าไม่เข้าเกณฑ์ใดเลย

    ⚠️ ตรวจเฉพาะเกณฑ์ GPA เท่านั้น เงื่อนไขอื่น (ไม่เคยได้ F/U, ไม่เคยเรียนซ้ำ,
       เทียบโอนไม่เกิน 1/6) ระบบไม่มีข้อมูลจึงตรวจไม่ได้ ผู้เรียกต้องแจ้งเงื่อนไข
       เหล่านี้ให้ผู้ใช้ทราบเสมอ

    (แก้ 2026-07-23) เดิมเงื่อนไขอันดับสองใช้ช่วงปิด min_gpa <= gpa <= max_gpa
    ซึ่ง yaml กำหนด max_gpa = 3.49 ส่วนอันดับหนึ่ง min_gpa = 3.50 ทำให้ค่าที่อยู่
    ระหว่างสองเลขนี้ (เช่น 3.495 จากการปัดเศษภายใน) ตกร่องทั้งคู่แล้วคืน None
    ทั้งที่ควรได้อันดับสอง ตอนนี้เทียบด้วยขอบล่างอย่างเดียว ช่องว่างจึงหายไป
    (ฟิลด์ max_gpa ใน yaml ยังอยู่ในฐานะเอกสารประกอบ ไม่ได้ใช้คำนวณแล้ว)
    """
    if not (GPA_MIN <= gpa <= GPA_MAX):
        # ไม่ raise เพราะค่านี้อาจมาจากที่ผู้ใช้พิมพ์เอง (เช่น "GPA 5.00")
        # การ raise จะทำให้บอทล่มกลางบทสนทนา คืน None ปลอดภัยกว่า
        return None

    honors = load_rules()["graduation"]["honors"]

    if gpa >= honors["first_class"]["min_gpa"]:
        return honors["first_class"]["name"]
    if gpa >= honors["second_class"]["min_gpa"]:
        return honors["second_class"]["name"]
    return None


def get_honor_min_gpa() -> float:
    """เกณฑ์ GPA ต่ำสุดที่ยังได้เกียรตินิยม (ใช้ในข้อความตอบ จะได้ไม่ hardcode ซ้ำ)"""
    return load_rules()["graduation"]["honors"]["second_class"]["min_gpa"]


# ══════════════════════════════════════════════════════════════
# 2. ค่าปรับลงทะเบียนล่าช้า
# path: registration.late_registration
# ══════════════════════════════════════════════════════════════

def get_max_late_days() -> int:
    """จำนวนวันสูงสุดที่ยังลงทะเบียนได้ก่อนพ้นสภาพ (ใช้ในข้อความตอบ)"""
    r = load_rules()["registration"]["late_registration"]
    return r["max_late_weeks_before_dismissed"] * 7


def calculate_late_fee(days_late: int) -> dict:
    """คำนวณค่าปรับลงทะเบียนล่าช้า

    Raises:
        ValueError: ถ้า days_late ติดลบ (เดิมคืนค่าปรับติดลบเงียบ ๆ)
    """
    if days_late < 0:
        raise ValueError(f"days_late ต้องไม่ติดลบ (ได้ {days_late})")

    r = load_rules()["registration"]["late_registration"]

    per_day  = r["penalty_per_day"]                    # 25 บาท/วัน
    max_days = r["max_late_weeks_before_dismissed"] * 7  # 2 สัปดาห์ = 14 วัน
    fee_ug   = r["reinstatement_fee_undergraduate"]     # 1000 บาท
    form     = r["reinstatement_form"]                  # NU7

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


# ══════════════════════════════════════════════════════════════
# 3. หน่วยกิตที่ลงได้
# path: registration.credit_limits
# ══════════════════════════════════════════════════════════════

VALID_SEMESTERS = ("normal", "summer")


def check_credit_limit(credits: int, semester: str = "normal") -> dict:
    """ตรวจสอบหน่วยกิตที่ลงได้ต่อภาค

    Args:
        semester: "normal" (ภาคปกติ) หรือ "summer" (ภาคฤดูร้อน)

    Raises:
        ValueError: ถ้า credits ติดลบ หรือ semester ไม่ใช่ค่าที่รู้จัก

    (แก้ 2026-07-23) เดิมใช้ `if semester == "normal" else summer` แปลว่าค่าอะไร
    ก็ตามที่ไม่ใช่ "normal" เป๊ะ ๆ — รวมถึงคำที่พิมพ์ผิดอย่าง "ภาคต้น" หรือ
    "Normal" ตัวใหญ่ — จะถูกมองเป็นภาคฤดูร้อนทันทีโดยไม่มีอะไรเตือน ทำให้ตอบ
    ขีดจำกัดผิดจาก 22 เป็น 9 หน่วยกิต
    """
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


# ══════════════════════════════════════════════════════════════
# 4. สถานภาพนิสิต
# path: academic_status
# ══════════════════════════════════════════════════════════════

def get_probation_threshold() -> float:
    """เกณฑ์ GPA ของสถานภาพ 'รอพินิจ' — อ่านจาก rules.yaml

    (แก้ 2026-07-23) เดิม check_academic_status() อ่าน
    definitions.probation.condition (สตริง "GPA สะสม < 2.00") มาเก็บไว้ในตัวแปร
    แล้วไม่ได้ใช้ จากนั้น hardcode 2.00 ลงไปตรง ๆ แปลว่าแก้ rules.yaml แล้ว
    เกณฑ์นี้ไม่เปลี่ยนตาม ขัดกับหลักการของ rule engine ที่กฎต้องอยู่ในไฟล์ config

    yaml เก็บ condition เป็นข้อความอ่านง่ายสำหรับคน ไม่ใช่ตัวเลขที่คำนวณได้
    จึงต้องเพิ่มฟิลด์ตัวเลขแยกต่างหาก:

        academic_status:
          definitions:
            probation:
              label: "นิสิตรอพินิจ"
              condition: "GPA สะสม < 2.00"
              threshold: 2.00        # ← เพิ่มบรรทัดนี้

    ระหว่างที่ยังไม่ได้เพิ่ม ฟังก์ชันจะเตือน 1 ครั้งแล้วใช้ค่าสำรอง 2.00 ไปก่อน
    เพื่อไม่ให้บอทล่ม
    """
    global _warned_probation
    probation = load_rules()["academic_status"]["definitions"]["probation"]
    threshold = probation.get("threshold")

    if threshold is None:
        if not _warned_probation:
            print(
                "⚠️  rules.yaml ยังไม่มี academic_status.definitions.probation.threshold "
                f"— ใช้ค่าสำรอง {_PROBATION_FALLBACK:.2f} ไปก่อน"
            )
            _warned_probation = True
        return _PROBATION_FALLBACK

    return float(threshold)


def check_academic_status(gpa: float, semesters_completed: int) -> dict:
    """ตรวจสอบสถานภาพนิสิตจาก GPA และจำนวนภาคที่เรียน

    Raises:
        ValueError: ถ้า semesters_completed ติดลบ

    ⚠️ ประเด็นที่ยังต้องยืนยันกับข้อบังคับมหาวิทยาลัย (คงพฤติกรรมเดิมไว้ก่อน):
       เงื่อนไข after_2_semesters ใช้ `>= 2` ไม่ใช่ `== 2` แปลว่านิสิตที่เรียน
       ครบ 3 ภาคแล้วมี GPA 1.40 จะถูกตัดสินว่าพ้นสภาพทันที แต่ข้อบังคับ
       มหาวิทยาลัยมักตรวจสถานภาพ "ปลายปีการศึกษา" (ภาคที่ 2, 4, 6) ไม่ใช่ทุกภาค
       ถ้าตรวจข้อบังคับแล้วพบว่าต้องเป็น `== 2` ให้แก้บรรทัดที่มีคอมเมนต์
       [REG-CHECK] ด้านล่าง แล้วอัปเดตเคสใน test_rules.py ให้ตรงกัน
    """
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

    # [REG-CHECK] ดูคำเตือนใน docstring ก่อนเปลี่ยน >= เป็น ==
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


# ══════════════════════════════════════════════════════════════
# 5. กยศ. Redirect
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
# 6. ปฏิทินการศึกษา Redirect
# path: academic_calendar
# ══════════════════════════════════════════════════════════════
# วันเปิด/ปิดเทอม วันลงทะเบียน วันสอบ ฯลฯ เปลี่ยนทุกภาคเรียน
# ไม่เก็บใน KB (เสี่ยงข้อมูลเก่า) → redirect ไปแหล่งทางการ เหมือน student_loan
#
# ต่างจาก loan ตรงที่ใช้ 2 ชั้นเพื่อความแม่น:
#   - direct_keywords  → เป็นปฏิทินแน่ ๆ (เปิดเทอม/ปฏิทินการศึกษา) → redirect ทันที
#   - topic_keywords + when_keywords → "ลงทะเบียนวันไหน" = ปฏิทิน
#     แต่ "ลงทะเบียนยังไง" (ไม่มีคำถามเวลา) → ปล่อยไป RAG
#
# หมายเหตุ: ต้องมี section `academic_calendar` ใน rules.yaml ก่อน
# ถ้ายังไม่มี ฟังก์ชันจะคืน False / ข้อความ default แบบไม่ crash
# (ต่างจาก loan ที่อ่าน key ตรง ๆ — ทำ defensive ไว้กัน deploy ไม่พร้อมกัน)

_CALENDAR_FALLBACK_TEMPLATE = (
    "📅 เรื่องวันเปิด-ปิดเทอม วันลงทะเบียน หรือกำหนดการต่าง ๆ "
    "แนะนำให้ดูจากปฏิทินการศึกษาของมหาวิทยาลัยโดยตรงนะคะ "
    "เพราะวันที่จะเปลี่ยนทุกภาคเรียนค่ะ 😊\n\n"
    "🗓️ ปฏิทินการศึกษา: https://reg4.nu.ac.th/registrar/calendar.asp?avs727811069=1\n"
    "📞 ภาควิชา CSIT 055-963262, 055-963263"
)


def _calendar_policy() -> dict:
    """ดึง bot_policy ของปฏิทิน (คืน {} ถ้ายังไม่มี section ใน yaml)"""
    return load_rules().get("academic_calendar", {}).get("bot_policy", {})


def get_calendar_redirect_template() -> str:
    """ดึง response template สำหรับ redirect ปฏิทิน (มี fallback กัน crash)"""
    return load_rules().get("academic_calendar", {}).get(
        "response_template", _CALENDAR_FALLBACK_TEMPLATE
    )


def is_calendar_query(question: str) -> bool:
    """ตรวจว่าคำถามเกี่ยวกับวัน/กำหนดการตามปฏิทินการศึกษาหรือไม่
    - เจอคำปฏิทินตรง ๆ (direct_keywords) → True
    - หัวข้อ (topic_keywords) + คำถามเวลา (when_keywords) → True
    - มีแค่หัวข้อแต่ไม่ถามเวลา (เช่น "ลงทะเบียนยังไง") → False (ปล่อยไป RAG)
    """
    q = question.lower()
    pol = _calendar_policy()

    if any(kw.lower() in q for kw in pol.get("direct_keywords", [])):
        return True

    has_topic = any(kw.lower() in q for kw in pol.get("topic_keywords", []))
    has_when = any(kw.lower() in q for kw in pol.get("when_keywords", []))
    return has_topic and has_when


# ══════════════════════════════════════════════════════════════
# Self-test  (ชุดทดสอบเต็มอยู่ที่ src/eval/test_rules.py)
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🧪 ทดสอบ Rules Engine\n")

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
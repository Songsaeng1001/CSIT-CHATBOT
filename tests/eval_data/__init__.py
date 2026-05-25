"""Eval data — รวม import ทั้งหมด"""

from tests.eval_data import (
    eval_curriculum,
    eval_staff,
    eval_registration,
    eval_graduation,
    eval_loan,
    eval_contact,
    eval_oos,
)

# Map category name → module
ALL_CATEGORIES = {
    "curriculum": eval_curriculum,
    "staff": eval_staff,
    "registration": eval_registration,
    "graduation": eval_graduation,
    "loan": eval_loan,
    "contact": eval_contact,
    "oos": eval_oos,
}


def get_questions(category: str):
    """ดึงคำถามจากหมวด"""
    if category not in ALL_CATEGORIES:
        raise ValueError(f"Unknown category: {category}. Available: {list(ALL_CATEGORIES.keys())}")
    return ALL_CATEGORIES[category].QUESTIONS


def get_category_th(category: str):
    """ดึงชื่อไทยของหมวด"""
    if category not in ALL_CATEGORIES:
        return category
    return ALL_CATEGORIES[category].CATEGORY_TH


def get_all_questions():
    """ดึงคำถามทุกหมวด"""
    all_questions = []
    for module in ALL_CATEGORIES.values():
        all_questions.extend(module.QUESTIONS)
    return all_questions


if __name__ == "__main__":
    print("=" * 60)
    print("📋 Eval Categories Summary")
    print("=" * 60)
    
    total = 0
    for cat_name, module in ALL_CATEGORIES.items():
        count = len(module.QUESTIONS)
        oos_count = sum(1 for q in module.QUESTIONS if q.get("is_oos"))
        total += count
        oos_note = f" (OOS)" if oos_count > 0 else ""
        print(f"   {module.CATEGORY_TH:25s}: {count:3d} ข้อ{oos_note}")
    
    print(f"\n📊 Total: {total} คำถามทั้งหมด")
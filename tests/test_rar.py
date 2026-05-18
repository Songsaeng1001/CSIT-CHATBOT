"""
ทดสอบ Rule-Augmented Reasoning
เปรียบเทียบกับ RAG ปกติ

รัน: python -m tests.test_rar
"""

from src.chat import answer


# คำถามที่ต้องใช้ RAR (มีคำนวณ/lookup)
RAR_TEST_CASES = [
    {
        "question": "อาจารย์เกรียงศักดิ์ห้องอะไร อีเมลอะไร",
        "expected_keywords": ["SC2-401", "kreangsakt@nu.ac.th"],
        "category": "SQLite/instructors",
    },
    {
        "question": "NU25 ใช้ทำอะไร",
        "expected_keywords": ["สำเร็จการศึกษา"],
        "category": "SQLite/nu_forms",
    },
    {
        "question": "GPA 3.55 ได้เกียรตินิยมอะไร",
        "expected_keywords": ["เกียรตินิยมอันดับหนึ่ง"],
        "category": "Rule/honor",
    },
    {
        "question": "GPA 3.30 ได้เกียรตินิยมอะไร",
        "expected_keywords": ["เกียรตินิยมอันดับสอง"],
        "category": "Rule/honor",
    },
    {
        "question": "ลงทะเบียนช้า 7 วัน ต้องจ่ายเท่าไร",
        "expected_keywords": ["175"],  # 7 × 25 = 175
        "category": "Rule/late_fee",
    },
    {
        "question": "ลงทะเบียนช้า 20 วัน ทำยังไง",
        "expected_keywords": ["พ้นสภาพ", "NU7"],
        "category": "Rule/late_fee",
    },
    {
        "question": "ลง 24 หน่วยกิตได้ไหม",
        "expected_keywords": ["NU18", "เกิน"],
        "category": "Rule/credit",
    },
    {
        "question": "ลง 18 หน่วยกิตได้ไหม",
        "expected_keywords": ["ได้", "ปกติ"],
        "category": "Rule/credit",
    },
    {
        "question": "GPA 1.65 หลังเรียน 3 ภาค",
        "expected_keywords": ["พ้นสภาพ"],
        "category": "Rule/status",
    },
]


def test_one(case: dict) -> dict:
    """ทดสอบ 1 case"""
    question = case["question"]
    expected = case["expected_keywords"]
    category = case["category"]
    
    print(f"\n❓ {question}")
    print(f"   📌 Category: {category}")
    print(f"   🎯 Expected: {expected}")
    
    try:
        response = answer(question, verbose=False)
        print(f"   💬 Got: {response[:150]}...")
        
        # เช็คว่ามี keyword ครบไหม
        missing = [kw for kw in expected if kw.lower() not in response.lower()]
        
        if not missing:
            print(f"   ✅ PASS")
            return {"status": "pass", "case": case}
        else:
            print(f"   ❌ FAIL - missing: {missing}")
            return {"status": "fail", "case": case, "missing": missing}
    
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return {"status": "error", "case": case, "error": str(e)}


def main():
    print("=" * 70)
    print("🧪 ทดสอบ Rule-Augmented Reasoning (RAR)")
    print("=" * 70)
    
    results = []
    for case in RAR_TEST_CASES:
        result = test_one(case)
        results.append(result)
    
    # ─── สรุปผล ───
    print()
    print("=" * 70)
    print("📊 สรุปผลทดสอบ")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    errors = sum(1 for r in results if r["status"] == "error")
    
    print(f"   ✅ Pass:   {passed}/{len(RAR_TEST_CASES)}")
    print(f"   ❌ Fail:   {failed}/{len(RAR_TEST_CASES)}")
    print(f"   ⚠️  Error: {errors}/{len(RAR_TEST_CASES)}")
    print(f"   📈 Accuracy: {passed/len(RAR_TEST_CASES)*100:.1f}%")


if __name__ == "__main__":
    main()
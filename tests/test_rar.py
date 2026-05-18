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
        "must_have": ["SC2-401", "kreangsakt"],
        "category": "SQLite/instructors",
    },
    {
        "question": "NU25 ใช้ทำอะไร",
        "must_have": ["สำเร็จการศึกษา"],
        "category": "SQLite/nu_forms",
    },
    {
        "question": "GPA 3.55 ได้เกียรตินิยมอะไร",
        "must_have": ["เกียรตินิยมอันดับหนึ่ง"],
        "category": "Rule/honor",
    },
    {
        "question": "GPA 3.30 ได้เกียรตินิยมอะไร",
        "must_have": ["เกียรตินิยมอันดับสอง"],
        "category": "Rule/honor",
    },
    {
        "question": "ลงทะเบียนช้า 7 วัน ต้องจ่ายเท่าไร",
        "must_have": ["175"],
        "category": "Rule/late_fee",
    },
    {
        "question": "ลงทะเบียนช้า 20 วัน ทำยังไง",
        "must_have": ["NU7"],
        "must_have_any": ["พ้นสภาพ", "คืนสภาพ", "เกินกำหนด"],
        "category": "Rule/late_fee",
    },
    {
        "question": "ลง 24 หน่วยกิตได้ไหม",
        "must_have": ["NU18"],
        "must_have_any": ["เกิน", "มากกว่า", "เกินกำหนด"],
        "category": "Rule/credit",
    },
    {
        "question": "ลง 18 หน่วยกิตได้ไหม",
        "must_have_any": ["ลงได้", "ลงทะเบียนได้", "ปกติ", "ภายในเกณฑ์"],
        "category": "Rule/credit",
    },
    {
        "question": "GPA 1.65 หลังเรียน 3 ภาค",
        "must_have_any": ["พ้นสภาพ", "คืนสภาพ", "ยังไม่จบ", "ต่ำกว่าเกณฑ์"],
        "category": "Rule/status",
    },
]

def test_one(case: dict, max_retries: int = 2) -> dict:
    """ทดสอบ 1 case — มี retry สำหรับ transient errors"""
    import time
    
    question = case["question"]
    must_have = case.get("must_have", [])
    must_have_any = case.get("must_have_any", [])
    category = case["category"]
    
    print(f"\n❓ {question}")
    print(f"   📌 Category: {category}")
    if must_have:
        print(f"   🎯 Must have ALL: {must_have}")
    if must_have_any:
        print(f"   🎯 Must have ANY: {must_have_any}")
    
    # ─── Retry loop ───
    for attempt in range(max_retries + 1):
        try:
            response = answer(question, verbose=False)
            
            # ─── สำเร็จ ───
            print(f"   💬 Got: {response[:150]}...")
            response_lower = response.lower()
            
            missing = [kw for kw in must_have if kw.lower() not in response_lower]
            has_any = True
            if must_have_any:
                has_any = any(kw.lower() in response_lower for kw in must_have_any)
            
            if not missing and has_any:
                print(f"   ✅ PASS")
                return {"status": "pass", "case": case}
            else:
                reasons = []
                if missing:
                    reasons.append(f"missing all: {missing}")
                if not has_any:
                    reasons.append(f"missing any of: {must_have_any}")
                print(f"   ❌ FAIL - {', '.join(reasons)}")
                return {"status": "fail", "case": case, "reasons": reasons}
        
        except Exception as e:
            error_msg = str(e)
            
            # ตรวจ transient errors (retry ได้)
            is_transient = any([
                "503" in error_msg,
                "UNAVAILABLE" in error_msg,
                "429" in error_msg,
                "RESOURCE_EXHAUSTED" in error_msg,
                "high demand" in error_msg,
            ])
            
            if is_transient and attempt < max_retries:
                wait_sec = 30 * (attempt + 1)  # 30, 60 วินาที
                print(f"   ⏸️  Transient error (attempt {attempt+1}/{max_retries+1}) — รอ {wait_sec}s แล้ว retry")
                time.sleep(wait_sec)
                continue
            
            # Error ถาวร
            print(f"   ❌ ERROR: {error_msg[:200]}")
            return {"status": "error", "case": case, "error": error_msg}
    
    # ใช้ retry หมดแล้วยังไม่ผ่าน
    print(f"   ⏭️  Gave up after {max_retries + 1} attempts")
    return {"status": "skip", "case": case, "error": "max retries"}


def main():
    import time
    
    print("=" * 70)
    print("🧪 ทดสอบ Rule-Augmented Reasoning (RAR)")
    print("=" * 70)
    print(f"⏱️  หน่วงเวลา 20 วินาทีระหว่าง test (anti rate-limit)")
    print(f"🔄 Auto retry สำหรับ 503/429 errors")
    print()
    
    results = []
    total = len(RAR_TEST_CASES)
    
    for i, case in enumerate(RAR_TEST_CASES, 1):
        print(f"\n{'='*70}")
        print(f"📝 Test {i}/{total}")
        print(f"{'='*70}")
        
        result = test_one(case, max_retries=2)
        results.append(result)
        
        # หน่วงเวลาก่อน test ถัดไป (ไม่ต้องหน่วงตัวสุดท้าย)
        if i < total:
            print(f"   ⏳ รอ 20 วินาที ก่อน test ถัดไป...")
            time.sleep(20)
    
    # ─── สรุปผล ───
    print()
    print("=" * 70)
    print("📊 สรุปผลทดสอบ")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["status"] == "pass")
    failed = sum(1 for r in results if r["status"] == "fail")
    errors = sum(1 for r in results if r["status"] == "error")
    skipped = sum(1 for r in results if r["status"] == "skip")
    
    actual_total = total - skipped
    
    print(f"   ✅ Pass:    {passed}/{actual_total}")
    print(f"   ❌ Fail:    {failed}/{actual_total}")
    print(f"   ⚠️  Error:  {errors}/{actual_total}")
    if skipped > 0:
        print(f"   ⏸️  Skipped: {skipped} (max retries หรือ rate limit)")
    
    if actual_total > 0:
        accuracy = passed / actual_total * 100
        print(f"   📈 Accuracy: {accuracy:.1f}%")
        
        if accuracy >= 80:
            print(f"\n🎉 ผลลัพธ์ดีมาก!")
        elif accuracy >= 60:
            print(f"\n👍 ผ่านเกณฑ์")
        else:
            print(f"\n⚠️  ควรปรับปรุงเพิ่มเติม")

if __name__ == "__main__":
    main()
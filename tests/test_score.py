from src.database import vector_db

should_answer = [
    "อาจารย์ที่ปรึกษาภาควิชามีใครบ้าง",
    "NU18 ใช้ทำอะไร",
    # ... คำถามที่ในฐานมีคำตอบ
]
should_reject = [
    "สูตรต้มยำกุ้ง",
    "ราคาทองวันนี้",
    # ... คำถามนอกเรื่องที่ควรปฏิเสธ
]

def show(label, qs):
    print(f"\n===== {label} =====")
    for q in qs:
        results = vector_db.search(q, k=3)
        best = results[0][1] if results else None
        print(f"  best={best:.3f} | {q}")

show("ควรตอบได้ (คาดว่า score ต่ำ)", should_answer)
show("ควรปฏิเสธ (คาดว่า score สูง)", should_reject)
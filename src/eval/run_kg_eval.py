"""
run_kg_eval.py — รัน eval ชุดเดียวกับ run_baseline_eval.py แต่ "เปิด KG"
(Vector RAG + SQLite KG query) แล้วบันทึกผลเป็น kg_results.json

จุดประสงค์: สร้าง arm B ของ A/B comparison คู่กับ baseline_results.json (arm A)
เพื่อให้ compare_stats.py เอาไปเทียบสถิติได้:

    python -m src.eval.compare_stats \
        src/eval/results/baseline_results.json \
        src/eval/results/kg_results.json --by-type

── ทำไมเป็น wrapper บาง ๆ ไม่ก็อปโค้ดทั้งไฟล์ ─────────────────────────────
run_baseline_eval.py มี logic จัดการโควตา Gemini (RPM retry / RPD หยุดทันที /
auto-resume) ที่ผ่านการทดสอบมาแล้วอย่างละเอียด ถ้าก็อปมาทั้งไฟล์แล้วแก้
จะต้องคอย sync 2 ไฟล์ให้ตรงกันตลอด เสี่ยง logic เพี้ยนเงียบ ๆ ในอนาคต
ไฟล์นี้จึง reuse ฟังก์ชัน run() ตัวเดิม 100% เปลี่ยนแค่ 2 อย่าง:

    1) ตั้ง CSIT_ENABLE_KG=1 "ก่อน" import src.* ทุกตัว
       (src/retriever.py อ่าน env var นี้ตอน import ระดับ module — ตั้งทีหลัง
        retriever จะ freeze ค่า default ไปแล้ว แก้ไม่ทัน)
    2) ชี้ RESULTS_PATH ไปที่ kg_results.json แทน baseline_results.json

run_baseline_eval.py ตั้ง CSIT_ENABLE_KG ด้วย os.environ.setdefault ไว้แล้ว
"โดยเจตนา" เพื่อให้ไฟล์นี้ที่ hard-set "1" ไว้ก่อน ไม่ถูกเขียนทับกลับเป็น "0"
และมี guard ใน run() เช็ค ENABLE_KG != expected_kg ที่จะ raise ทันทีถ้า
import order ผิด — กันข้อมูล 2 ระบบปนกันโดยไม่มีใครเตือน

── ใช้ (รันจาก root ของ repo เหมือน baseline) ────────────────────────────
    python -m src.eval.run_kg_eval [limit] [n_questions]

    limit       จำนวนคำถามที่ "ยังไม่เคยทำ" ที่จะรันในครั้งนี้
                (ไม่ใส่ = รันทุกข้อที่เหลือ; ใส่ 4 เพื่อจำกัดโควตาต่อวัน)
    n_questions จำนวนคำถามย้อนสร้างสำหรับ Answer Relevance
                (default 3 ตามเปเปอร์ RAGAS; ลดเป็น 1 เพื่อประหยัดโควตา)

ผลลัพธ์:
    src/eval/results/kg_results.json

หมายเหตุ auto-resume: ไฟล์ผลของ KG แยกคนละไฟล์กับ baseline (kg_results.json)
ดังนั้น done_ids ของ 2 รอบไม่กวนกัน — จะรัน baseline ให้ครบก่อนแล้วค่อยเริ่ม KG
หรือสลับกันก็ได้ ไม่ปนกัน
"""

import os
os.environ["CSIT_ENABLE_KG"] = "1"
import sys
import src.eval.run_baseline_eval as base
base.RESULTS_PATH = base.RESULTS_DIR / "kg_results.json"


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    n_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    base.run(limit=limit, n_questions=n_questions)
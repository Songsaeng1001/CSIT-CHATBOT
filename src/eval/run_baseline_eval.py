"""
run_baseline_eval.py — รันชุดคำถามทดสอบ (eval_dataset.json) ผ่านระบบปัจจุบัน
(Vector RAG + SQLite + Rule engine ตัวเดียวกับที่ตอบผู้ใช้จริง) แล้วคำนวณ:

    1) RAGAS 3 ตัวชี้วัด (Faithfulness, Answer Relevance, Context Relevance)
       — ทุกคำถามที่มี context (ข้ามเคส redirect เช่นปฏิทิน/กยศ. ที่ไม่มี context จริง)
    2) Retrieval metrics (Precision@K, Reciprocal Rank)
       — เฉพาะคำถามที่ระบุ expected_source_file ไว้ใน eval_dataset.json

ใช้ (รันจาก root ของ repo, ระดับเดียวกับ venv/ requirements.txt):
    python -m src.eval.run_baseline_eval [limit] [n_questions]

    limit       จำนวนคำถามที่ยังไม่เคยทำ ที่จะรันในครั้งนี้ (ไม่ใส่ = รันทุกข้อที่เหลือ)
    n_questions จำนวนคำถามย้อนสร้างสำหรับ Answer Relevance (ดู ragas_metrics.py)
                ค่าเริ่มต้น 3 ตามเปเปอร์ RAGAS แต่ลดเหลือ 1 ได้ถ้าอยากประหยัดโควตา

หมายเหตุ (แก้ 2026-07-18): ตรวจพบว่าไฟล์เวอร์ชันก่อนหน้าไม่มีการตรวจจับโควตาหมดเลย —
วิ่งชน RESOURCE_EXHAUSTED แล้วแค่ print แจ้งเตือนแล้ว "รันต่อ" ทุกครั้ง (entry["ragas"]=None)
ไม่มี auto-resume ด้วย (รันใหม่ทุกครั้งจะทำทั้ง 50 ข้อซ้ำจากศูนย์) เวอร์ชันนี้แก้ทั้งคู่ และ
เพิ่มการแยกโควตา 2 ชั้นของ Gemini free tier ให้จัดการต่างกัน:
    - RPM (ต่อนาที, error message มี "PerMinute" เช่น limit: 10)
      ชั่วคราว หายเองใน ~30 วินาที — สคริปต์จะ "รอแล้วลองใหม่อัตโนมัติ" (สูงสุด 3 ครั้ง
      ต่อ 1 การเรียก API) ไม่ต้องหยุดทั้งสคริปต์
    - RPD (ต่อวัน, error message มี "PerDay" เช่น limit: 20)
      หมดแล้วจริงสำหรับวันนี้ รอสั้น ๆ ไม่มีประโยชน์ — สคริปต์จะหยุดทันที บันทึกผลที่ทำ
      ไปแล้วสะสมไว้ (auto-resume) แล้วรันคำสั่งเดิมซ้ำวันถัดไปเพื่อทำต่อจากที่ค้าง
    - ถ้าเจอ quota error ที่ไม่ตรงทั้ง 2 รูปแบบข้างต้น (Google อาจเปลี่ยนข้อความในอนาคต)
      จะ print debug (ชนิด exception + ข้อความเต็ม) แล้วหยุดแบบระมัดระวังไว้ก่อนเหมือน RPD
    - ถ้าอยากรันใหม่หมดตั้งแต่ต้น ให้ลบไฟล์ src/eval/results/baseline_results.json ก่อน

ผลลัพธ์:
    src/eval/results/baseline_results.json
"""

import os

# ⚠️ ต้องตั้งก่อน import src.* ทุกตัว — src/retriever.py อ่าน CSIT_ENABLE_KG
#    ตอน import (ระดับ module) ถ้าตั้งทีหลังจะไม่มีผลเลย
#
# ใช้ setdefault ไม่ใช่กำหนดตรง ๆ เพื่อให้ run_kg_eval.py ที่ตั้งเป็น "1" ไว้ก่อน
# แล้วค่อย import ไฟล์นี้ ไม่ถูกเขียนทับ
#
# (แก้ 2026-07-23: เดิมไฟล์นี้ไม่ตั้ง env var เลย → retriever ใช้ค่า default ของ
#  ตัวเอง = "1" ผลที่ได้จึงเป็น RAG+KG ไม่ใช่ RAG-only ตามชื่อ "baseline"
#  ถ้าเอาไปเทียบกับ kg_results.json จะกลายเป็นเทียบ KG กับ KG ได้ผลต่างเป็นศูนย์
#  โดยไม่มีอะไรเตือน)
os.environ.setdefault("CSIT_ENABLE_KG", "0")

import re
import sys
import json
import time
from pathlib import Path

from src.chat import answer_full
from src.retriever import retrieve_context
from src.normalizer import normalize_query
from src.database import vector_db
from src.eval.ragas_metrics import evaluate_single
from src.eval.retrieval_metrics import precision_at_k, reciprocal_rank
from src.retriever import ENABLE_KG

DATASET_PATH = Path(__file__).parent / "eval_dataset.json"
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "baseline_results.json"

# ─── ตรวจจับโควตาหมด แยกชนิด RPM (ชั่วคราว) กับ RPD (รายวัน) ────────────
QUOTA_ERROR_MARKERS = ("RESOURCE_EXHAUSTED", "429", "quota")
RPM_MARKERS = ("PerMinute", "RequestsPerMinute")
RPD_MARKERS = ("PerDay", "RequestsPerDay")
MAX_RPM_RETRIES = 3
DEFAULT_RPM_WAIT = 30.0


def is_quota_error(e: Exception) -> bool:
    return any(marker in str(e) for marker in QUOTA_ERROR_MARKERS)


def is_daily_quota_error(e: Exception) -> bool:
    """โควตา 'ต่อวัน' (RPD) — หมดแล้วจริง รอสั้น ๆ ไม่มีประโยชน์ ต้องหยุดทั้งสคริปต์"""
    return any(marker in str(e) for marker in RPD_MARKERS)


def is_per_minute_quota_error(e: Exception) -> bool:
    """โควตา 'ต่อนาที' (RPM) — ชั่วคราว รอสั้น ๆ (ตาม retryDelay ถ้ามี) แล้ว retry เองได้"""
    return any(marker in str(e) for marker in RPM_MARKERS)


def extract_retry_delay_seconds(e: Exception, default: float = DEFAULT_RPM_WAIT) -> float:
    """ดึงจำนวนวินาทีที่ต้องรอจาก error message (Google มักส่ง 'retryDelay': '29s'
    หรือ 'retry in 29.7s' มาให้) ถ้าดึงไม่ได้ใช้ default แทน
    """
    text = str(e)
    match = re.search(r"retryDelay['\"]?\s*:\s*['\"](\d+(?:\.\d+)?)s", text)
    if match:
        return float(match.group(1))
    match = re.search(r"retry in (\d+(?:\.\d+)?)s", text)
    if match:
        return float(match.group(1))
    return default


def _call_with_rpm_retry(fn, *args, max_retries: int = MAX_RPM_RETRIES, **kwargs):
    """เรียกฟังก์ชันที่ยิง Gemini API ข้างใน พร้อม retry อัตโนมัติเฉพาะตอนชนโควตา
    'ต่อนาที' (RPM) เพราะเป็นข้อจำกัดชั่วคราว รอสั้น ๆ แล้วลองใหม่ได้จริง

    ถ้าชนโควตา 'ต่อวัน' (RPD) จะปล่อย exception หลุดออกไปทันที (retry ไม่มีประโยชน์)
    ให้ผู้เรียก (run()) หยุดทั้งสคริปต์ตามเดิม

    ถ้าชน quota error ที่จับรูปแบบ RPM/RPD ไม่ได้เลย (ข้อความอาจเปลี่ยนไปจาก Google ในอนาคต)
    จะ print debug ข้อมูล exception เต็ม ๆ ก่อนปล่อยให้หลุดออกไปเหมือน RPD (ระมัดระวังไว้ก่อน
    ดีกว่าเดามั่ว ๆ ว่า retry ได้)
    """
    for attempt in range(1, max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if is_daily_quota_error(e):
                raise
            if is_per_minute_quota_error(e) and attempt < max_retries:
                delay = extract_retry_delay_seconds(e) + 2  # กันเหนียวเผื่อ clock ไม่ตรงเป๊ะ
                print(f"   ⏳ ชนโควตาต่อนาที (RPM) รอ {delay:.0f} วินาที แล้วลองใหม่ (ครั้งที่ {attempt}/{max_retries})")
                time.sleep(delay)
                continue
            if is_quota_error(e) and not is_per_minute_quota_error(e) and not is_daily_quota_error(e):
                print("   🐛 debug: เจอ quota error ที่ไม่ตรงทั้ง RPM/RPD pattern")
                print(f"      ชนิด exception: {type(e).__name__}")
                print(f"      ข้อความเต็ม: {e}")
            raise
    raise RuntimeError("unreachable: _call_with_rpm_retry ควร return หรือ raise เสมอในลูป")


def load_dataset() -> list[dict]:
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_existing_results() -> list[dict]:
    if not RESULTS_PATH.exists():
        return []
    try:
        with open(RESULTS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print("   ⚠️  อ่านผลเดิมไม่สำเร็จ (ไฟล์อาจเสีย) จะเริ่มนับใหม่จากศูนย์")
        return []


def save_results(all_results: list[dict]) -> None:
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)


def retrieval_eval_for_question(question: str, expected_source: str | None, k: int = 5):
    """ดึง chunk จาก Chroma โดยตรง (bypass retrieve_context เพราะต้องการ metadata['source']
    ซึ่ง fetch_from_chroma ใน retriever.py ทิ้งไปตอนสร้าง context — ดึงใหม่ตรง ๆ ที่นี่แทน)
    """
    if not expected_source:
        return None
    results = vector_db.search(normalize_query(question), k=k)
    retrieved_ids = [doc.metadata.get("source", "") for doc, score in results]
    # metadata['source'] มักเป็น path เต็ม (เช่น knowledge_base/curriculum_cs.md)
    # ตัดให้เหลือแค่ชื่อไฟล์ กันเทียบไม่ตรงเพราะ path ต่างกัน
    retrieved_names = [Path(r).name if r else r for r in retrieved_ids]
    relevant_ids = {expected_source}
    return {
        "precision_at_k": precision_at_k(retrieved_names, relevant_ids, k),
        "reciprocal_rank": reciprocal_rank(retrieved_names, relevant_ids),
        "retrieved_sources": retrieved_names,
    }


def run(limit: int | None = None, n_questions: int = 3):
    """
    limit: จำนวนคำถามที่ "ยังไม่เคยทำ" ที่จะรันในครั้งนี้ (ใช้ตอนอยากจำกัดโควตาต่อวัน)
    n_questions: จำนวนคำถามที่ย้อนสร้างสำหรับ Answer Relevance (ดู ragas_metrics.py)
    """
    expected_kg = os.environ.get("CSIT_ENABLE_KG") == "1"
    if ENABLE_KG != expected_kg:
        raise RuntimeError(
            f"CSIT_ENABLE_KG={os.environ.get('CSIT_ENABLE_KG')!r} "
            f"แต่ retriever.ENABLE_KG={ENABLE_KG} — แปลว่า src.retriever ถูก import "
            "ไปก่อนที่ env var จะถูกตั้ง ผลลัพธ์จะไม่ตรงกับชื่อไฟล์ "
            "หยุดไว้ก่อนเพื่อกันข้อมูล 2 ระบบปนกัน"
        )
    mode = "RAG+KG" if ENABLE_KG else "RAG-only (ปิด KG)"
    print(f"⚙️  โหมด: {mode}  |  ENABLE_KG={ENABLE_KG}  |  บันทึกที่ {RESULTS_PATH.name}\n")

    dataset = load_dataset()
    all_results = load_existing_results()
    done_ids = {r.get("id") for r in all_results}

    remaining = [
        item for i, item in enumerate(dataset, start=1) if item.get("id", i) not in done_ids
    ]
    if not remaining:
        print(f"✅ ทำครบทุกคำถามแล้ว ({len(all_results)}/{len(dataset)}) — ดูผลได้ที่ {RESULTS_PATH}")
        return
    if limit:
        remaining = remaining[:limit]

    print(f"📂 ทำไปแล้ว {len(done_ids)}/{len(dataset)} คำถาม จะรันเพิ่ม {len(remaining)} คำถามในรอบนี้\n")

    for i, item in enumerate(remaining, start=1):
        idx_in_dataset = dataset.index(item) + 1
        qid = item.get("id", idx_in_dataset)
        question = item["question"]
        print(f"[{i}/{len(remaining)}] (id={qid}) {question}")

        # 1) ตอบจริงผ่านระบบปัจจุบัน (เหมือนที่ผู้ใช้ LINE ได้รับเป๊ะ ๆ) — retry RPM อัตโนมัติ
        try:
            result = _call_with_rpm_retry(answer_full, question, verbose=False, history=[])
        except Exception as e:
            if is_quota_error(e):
                print(f"   ⛔ โควตา API หมดสำหรับวันนี้ หยุดรันไว้ก่อน (บันทึกผลที่ทำไปแล้ว {len(all_results)} คำถามสะสม)")
                print("      พรุ่งนี้รันคำสั่งเดิมซ้ำได้เลย ระบบจะทำต่อจากคำถามที่ยังไม่เสร็จให้อัตโนมัติ")
                break
            print(f"   ❌ ตอบคำถามไม่สำเร็จ (ข้ามคำถามนี้ ครั้งหน้าจะลองใหม่): {e}")
            continue

        # 2) ดึง context ที่ระบบใช้จริงตอนตอบ (สำหรับคำนวณ RAGAS)
        try:
            ctx = retrieve_context(question)
            context_text = ctx.to_prompt_text()
        except Exception as e:
            print(f"   ⚠️  ดึง context ไม่สำเร็จ: {e}")
            context_text = ""

        entry = {
            "id": qid,
            "question": question,
            "type": item.get("type"),
            "gold_answer": item.get("gold_answer"),
            "system_answer": result.text,
            "answered": result.answered,
        }

        # 3) RAGAS — ข้ามถ้าไม่มี context เลย (เคส redirect ปฏิทิน/กยศ./greeting) — retry RPM อัตโนมัติ
        if context_text.strip():
            try:
                entry["ragas"] = _call_with_rpm_retry(
                    evaluate_single, question, result.text, context_text, n_questions=n_questions
                )
            except Exception as e:
                if is_quota_error(e):
                    print(f"   ⛔ โควตา API หมดระหว่างคำนวณ RAGAS หยุดรันไว้ก่อน (บันทึกผลที่ทำไปแล้ว {len(all_results)} คำถามสะสม)")
                    print("      พรุ่งนี้รันคำสั่งเดิมซ้ำได้เลย ระบบจะทำต่อจากคำถามที่ยังไม่เสร็จให้อัตโนมัติ")
                    break
                print(f"   ⚠️  RAGAS พลาด: {e}")
                entry["ragas"] = None
        else:
            entry["ragas"] = None

        # 4) retrieval metrics เฉพาะที่ระบุ expected_source_file ไว้
        entry["retrieval"] = retrieval_eval_for_question(
            question, item.get("expected_source_file")
        )

        all_results.append(entry)
        # บันทึกทันทีทุกครั้งที่ทำเสร็จ 1 คำถาม — กันโควตาหมดกลางทางแล้วผลหาย
        save_results(all_results)

    print(f"\n✅ บันทึกผลแล้วที่ {RESULTS_PATH} ({len(all_results)}/{len(dataset)} คำถามสะสม)")

    # สรุปคะแนนเฉลี่ยคร่าว ๆ ให้ดูตอนจบเลย (ไม่ต้องรอ compare_stats.py)
    faith = [r["ragas"]["faithfulness"]["score"] for r in all_results if r["ragas"] and r["ragas"]["faithfulness"]["score"] is not None]
    rel = [r["ragas"]["answer_relevance"]["score"] for r in all_results if r["ragas"] and r["ragas"]["answer_relevance"]["score"] is not None]
    ctx_rel = [r["ragas"]["context_relevance"]["score"] for r in all_results if r["ragas"] and r["ragas"]["context_relevance"]["score"] is not None]
    if faith:
        print(f"   Faithfulness เฉลี่ย:      {sum(faith)/len(faith):.3f}  (n={len(faith)})")
    if rel:
        print(f"   Answer Relevance เฉลี่ย:  {sum(rel)/len(rel):.3f}  (n={len(rel)})")
    if ctx_rel:
        print(f"   Context Relevance เฉลี่ย: {sum(ctx_rel)/len(ctx_rel):.3f}  (n={len(ctx_rel)})")

    if len(all_results) < len(dataset):
        print(f"\n   ℹ️  ยังเหลืออีก {len(dataset) - len(all_results)} คำถาม รันคำสั่งเดิมซ้ำวันพรุ่งนี้เพื่อทำต่อ")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    n_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    run(limit=limit, n_questions=n_questions)
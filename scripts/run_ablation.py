"""
scripts/run_ablation.py — การทดลองถอดองค์ประกอบ (Ablation Study) ของน้องซีที

เปรียบเทียบ 6 แบบ ด้วยคำถามชุดเดียวกัน
  1  llm_only        LLM อย่างเดียว (ไม่มีบริบทใด ๆ)
  2  rag_only        RAG อย่างเดียว (ค้น Chroma แล้วคืนส่วนเอกสารอันดับ 1 — ไม่มี LLM)
  3  rule_only       Rule-Based อย่างเดียว (Layer 1 + Rule Engine + SQLite — ไม่มี LLM, ไม่มี Chroma)
  4  llm_rag         LLM + RAG (ค้น Chroma แล้วให้ LLM ตอบ — ไม่มี Layer 1 / Rule / SQLite)
  5  llm_rule        LLM + Rule-Based (ระบบเต็มแต่ปิด Chroma)
  6  full            LLM + RAG + Rule-Based (ระบบปัจจุบันทั้งหมด)

ความปลอดภัยต่อระบบเดิม
  - ไม่แก้ไฟล์ใดในโปรเจกต์ ใช้การ "แทนฟังก์ชันชั่วคราวในหน่วยความจำ" (unittest.mock.patch)
    ซึ่งคืนค่าเดิมทันทีเมื่อจบแต่ละแบบ และมีผลเฉพาะ process ของสคริปต์นี้
  - อ่าน Chroma / SQLite / rules.yaml อย่างเดียว ไม่เขียนลงฐานข้อมูล
  - ไม่เรียก LINE, ไม่ส่ง log ไป n8n, ไม่บันทึก chat_logs / conversation_memory
  - ปิดการเขียน logs/no_context.log ระหว่างทดลอง
  - ผลลัพธ์เขียนลงโฟลเดอร์ใหม่ ablation_results/ เท่านั้น

รัน (จากโฟลเดอร์รากของโปรเจกต์):
    python -m scripts.run_ablation
    python -m scripts.run_ablation --runs 3            # รันซ้ำข้อละ 3 รอบ
    python -m scripts.run_ablation --temperature 0.3   # ใช้ temperature เท่าระบบจริง
    python -m scripts.run_ablation --only 1,6          # รันเฉพาะบางแบบ
"""

import os

# แบบที่ 6 ใช้ระบบปัจจุบัน (เปิด KG) — ต้องตั้งก่อน import retriever
os.environ.setdefault("CSIT_ENABLE_KG", "1")

import csv
import json
import time
import logging
import argparse
import datetime
from pathlib import Path
from unittest.mock import patch

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import GOOGLE_API_KEY, PROJECT_ROOT
from src import chat
from src import retriever
from src import main as line_main          # สร้าง FastAPI app object เฉย ๆ ไม่ได้เปิด server
from src.retriever import QueryAnalysis

logging.getLogger().setLevel(logging.WARNING)   # ปิด log INFO ของ main.py ให้หน้าจอไม่รก


# ─────────────────────────────────────────────────────────────
# ชุดคำถาม — แก้ / เพิ่มได้ที่นี่
# expected = คำตอบอ้างอิงสำหรับตรวจผล (อ้างอิง rules.yaml / ข้อมูลภาควิชา)
# ─────────────────────────────────────────────────────────────
QUESTIONS = [
    {
        "id": "Q1",
        "question": "ลงทะเบียนช้า 7 วัน ต้องจ่ายเท่าไร",
        "tests": "การคำนวณตามระเบียบ",
        "expected": "ค่าปรับ 7 × 25 = 175 บาท ยังลงทะเบียนได้ เหลืออีก 7 วันก่อนพ้นสภาพ (เกิน 14 วันพ้นสภาพ)",
    },
    {
        "id": "Q2",
        "question": "ขั้นตอนยื่นขอสำเร็จการศึกษาทำยังไง",
        "tests": "ข้อมูลเชิงเอกสาร / ขั้นตอน",
        "expected": "แจ้งจบที่ reg.nu.ac.th → พิมพ์ NU25 ลงชื่อ → ชำระค่าขึ้นทะเบียนปริญญาบัตร (ป.ตรี 2,000 บาท) "
                    "→ ยื่นเอกสาร + รูปชุดครุย 2 รูป → ลงชื่อในสมุดคุม; ยื่นภายใน 4 สัปดาห์หลังเปิดภาคสุดท้าย",
    },
    {
        "id": "Q3",
        "question": "พี่เฟิร์นเบอร์โทรอะไร",
        "tests": "ข้อมูลเฉพาะที่ต้องถูกตรงตัว",
        "expected": "055-963262 (nutthapakornm@nu.ac.th)",
    },
    {
        "id": "Q4",
        "question": "เปิดเทอมวันไหน",
        "tests": "ข้อมูลที่เปลี่ยนทุกภาคเรียน",
        "expected": "ไม่ระบุวันที่เอง แนะนำปฏิทินการศึกษา https://reg4.nu.ac.th/registrar/calendar.asp?avs727811069=1",
    },
    {
        "id": "Q5",
        "question": "GPA 3.55 ได้เกียรตินิยมไหม ต้องมีเงื่อนไขอะไรอีก",
        "tests": "ต้องใช้ทั้งการคำนวณและเอกสาร",
        "expected": "เกียรตินิยมอันดับหนึ่ง (≥ 3.50) เงื่อนไข: ไม่เคยได้ F หรือ U, ไม่เคยเรียนซ้ำ, "
                    "เทียบโอนไม่เกิน 1/6 ของหน่วยกิตรวม",
    },
    {
        "id": "Q6",
        "question": "NU18 ใช้ทำอะไร",
        "tests": "ข้อมูลเชิงโครงสร้าง (แบบฟอร์ม)",
        "expected": "NU18 คำร้องทั่วไป เช่น ขอลงทะเบียนเกินเกณฑ์หน่วยกิต, ขอเทียบรายวิชา",
    },
]

CONFIGS = {
    1: ("llm_only",  "LLM อย่างเดียว"),
    2: ("rag_only",  "RAG อย่างเดียว"),
    3: ("rule_only", "Rule-Based อย่างเดียว"),
    4: ("llm_rag",   "LLM + RAG"),
    5: ("llm_rule",  "LLM + Rule-Based"),
    6: ("full",      "LLM + RAG + Rule-Based"),
}

# prompt สำหรับแบบ LLM อย่างเดียว — ตั้งใจไม่ใส่กฎ "ตอบจากบริบทเท่านั้น"
# เพราะ SYSTEM_PROMPT เดิมจะสั่งให้ตอบ __NO_ANSWER__ เมื่อไม่มีบริบท ทำให้ไม่เห็นพฤติกรรมของ LLM จริง
LLM_ONLY_PROMPT = (
    "คุณคือ 'น้องซีที' ผู้ช่วย AI ของภาควิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ "
    "คณะวิทยาศาสตร์ มหาวิทยาลัยนเรศวร ตอบคำถามของนิสิตเป็นภาษาไทยสุภาพ ลงท้ายด้วย \"ค่ะ\""
)

NO_RULE_MATCH = "[ไม่ตรงกับกฎใด — ระบบแบบนี้ตอบไม่ได้]"
NO_DOC_MATCH = "[ไม่พบเอกสารที่ผ่านเกณฑ์ความคล้าย]"


# ─────────────────────────────────────────────────────────────
# ตัวช่วยบันทึกว่าแต่ละคำตอบใช้แหล่งข้อมูลอะไร
# ─────────────────────────────────────────────────────────────
_trace = {}
_orig_retrieve = retriever.retrieve_context


def _traced_retrieve(question, verbose=False, history=None):
    ctx = _orig_retrieve(question, verbose=verbose, history=history or [])
    _trace.setdefault("sources", []).extend(ctx.sources_used)
    return ctx


def _text_of(messages):
    return messages[0].text if messages and hasattr(messages[0], "text") else ""


# ─────────────────────────────────────────────────────────────
# ระบบทั้ง 6 แบบ
# ─────────────────────────────────────────────────────────────
def run_llm_only(q):
    resp = chat.get_llm().invoke([SystemMessage(content=LLM_ONLY_PROMPT), HumanMessage(content=q)])
    return chat._strip_markdown(resp.content).strip(), "llm"


def run_rag_only(q):
    chunks = retriever.fetch_from_chroma(q, k=5)
    _trace["sources"] = [f"Chroma ({len(chunks)} chunks ผ่านเกณฑ์)"]
    return (chunks[0] if chunks else NO_DOC_MATCH), "chroma_top1"


def _rule_answer(question, verbose=False, history=None):
    """แทน answer() ใน main.py — ตอบจากกฎ/SQLite ตรง ๆ โดยไม่เรียก LLM"""
    if chat.is_scholarship_query(question):
        _trace.setdefault("sources", []).append("Rule/scholarship")
        return chat.SCHOLARSHIP_MESSAGE
    ctx = retriever.retrieve_context(question, history=history or [])
    return ctx.to_prompt_text() if ctx.has_any() else chat.NO_ANSWER


def run_rule_only(q):
    with patch.object(retriever, "fetch_from_chroma", lambda *a, **k: []), \
         patch.object(line_main, "answer", _rule_answer):
        msgs, route, answered = line_main.route_message(q, history=[])
    text = _text_of(msgs)
    if not answered:
        text = NO_RULE_MATCH
    return text, route


def run_llm_rag(q):
    chroma_only = lambda question: QueryAnalysis(
        original_query=question, entities={}, sources_to_use=["chroma"]
    )
    with patch.object(retriever, "classify_query", chroma_only), \
         patch.object(chat, "is_scholarship_query", lambda question: False):
        result = chat.answer_full(q, history=[])
    return result.text, "answer_full(chroma_only)"


def run_llm_rule(q):
    with patch.object(retriever, "fetch_from_chroma", lambda *a, **k: []):
        msgs, route, answered = line_main.route_message(q, history=[])
    return _text_of(msgs), route


def run_full(q):
    msgs, route, answered = line_main.route_message(q, history=[])
    return _text_of(msgs), route


RUNNERS = {1: run_llm_only, 2: run_rag_only, 3: run_rule_only,
           4: run_llm_rag, 5: run_llm_rule, 6: run_full}


# ─────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1, help="จำนวนรอบต่อคำถาม (default 1)")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="temperature ของ LLM ระหว่างทดลอง (default 0 เพื่อให้ผลซ้ำได้)")
    ap.add_argument("--only", type=str, default="", help="เลือกแบบ เช่น 1,4,6")
    ap.add_argument("--sleep", type=float, default=1.0, help="หน่วงเวลาระหว่างคำขอ (วินาที)")
    args = ap.parse_args()

    if not GOOGLE_API_KEY:
        raise SystemExit("ไม่พบ GOOGLE_API_KEY ใน .env")

    selected = [int(x) for x in args.only.split(",") if x.strip()] or list(CONFIGS)

    # ใช้ LLM ตัวเดียวกันทุกแบบ (เปลี่ยนเฉพาะในหน่วยความจำของสคริปต์นี้)
    chat._llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        temperature=args.temperature,
        google_api_key=GOOGLE_API_KEY,
    )

    out_dir = PROJECT_ROOT / "ablation_results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"KG = {retriever.ENABLE_KG} | temperature = {args.temperature} | runs = {args.runs}")
    print(f"แบบที่รัน: {', '.join(CONFIGS[c][1] for c in selected)}\n")

    rows = []
    # ปิดการเขียน logs/no_context.log + บันทึกแหล่งข้อมูลที่ใช้ ตลอดการทดลอง
    with patch.object(chat, "log_unanswered_question", lambda q: None), \
         patch.object(retriever, "retrieve_context", _traced_retrieve):
        for item in QUESTIONS:
            for cid in selected:
                key, label = CONFIGS[cid]
                for run in range(1, args.runs + 1):
                    _trace.clear()
                    t0 = time.time()
                    try:
                        answer, route = RUNNERS[cid](item["question"])
                        error = ""
                    except Exception as e:
                        answer, route, error = "", "", f"{type(e).__name__}: {e}"
                    rows.append({
                        "id": item["id"],
                        "question": item["question"],
                        "tests": item["tests"],
                        "config_no": cid,
                        "config": label,
                        "run": run,
                        "answer": answer,
                        "route": route,
                        "sources": ", ".join(dict.fromkeys(_trace.get("sources", []))),
                        "seconds": round(time.time() - t0, 2),
                        "error": error,
                        "expected": item["expected"],
                        "score": "",          # ใส่เอง: ✓ / ◐ / ✗ / –
                    })
                    status = "ERROR" if error else "ok"
                    print(f"[{item['id']}] {cid}. {label:<24} run {run}  {status}")
                    if cid not in (2, 3):
                        time.sleep(args.sleep)

    meta = {
        "created_at": stamp,
        "model": "gemini-2.5-flash-lite",
        "temperature": args.temperature,
        "enable_kg": retriever.ENABLE_KG,
        "runs": args.runs,
        "configs": {cid: CONFIGS[cid][1] for cid in selected},
    }
    json_path = out_dir / f"results_{stamp}.json"
    json_path.write_text(json.dumps({"meta": meta, "results": rows}, ensure_ascii=False, indent=2),
                         encoding="utf-8")

    csv_path = out_dir / f"results_{stamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig เปิดใน Excel ได้ภาษาไทยถูก
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    errors = sum(1 for r in rows if r["error"])
    print(f"\nเสร็จแล้ว {len(rows)} คำตอบ (error {errors})")
    print(f"  {json_path}\n  {csv_path}")


if __name__ == "__main__":
    main()
"""
scripts/run_compare3.py — เปรียบเทียบ 3 แบบด้วยคำถามชุดเดียวกัน พร้อมประเมินผล

  A  llm_only   LLM อย่างเดียว (ไม่มีบริบท)
  B  llm_rag    LLM + RAG (ค้น Chroma แล้วให้ LLM ตอบ — ไม่มี Layer 1 / Rule / SQLite)
  C  full       LLM + RAG + Rule-Based (answer_full ชั้นที่ 2 เปิด KG — วิธีเดียวกับ run_kg_eval)

ชุดคำถามมี 2 กลุ่ม
  answerable    คำถามที่ฐานความรู้มีคำตอบ   → วัดว่าตอบ "ถูก" หรือไม่
  unanswerable  คำถามที่ฐานความรู้ไม่มีคำตอบ → วัดว่า "ปฏิเสธได้ถูกต้อง" หรือแต่งคำตอบขึ้นเอง

วิธีวัด (ดูรายละเอียดใน evaluate())
  1. Key-fact Accuracy   : คำตอบต้องมีข้อเท็จจริงสำคัญครบทุกข้อ และไม่มีข้อความต้องห้าม
                           (ตรวจด้วย regular expression เทียบกับคำตอบอ้างอิง — ทำซ้ำได้ ไม่ใช้ดุลยพินิจ)
  2. Fact Recall         : สัดส่วนข้อเท็จจริงสำคัญที่พบในคำตอบ (0–1)
  3. False Refusal Rate  : สัดส่วนคำถามที่ตอบได้ แต่ระบบปฏิเสธ
  4. Negative Rejection Rate : สัดส่วนคำถามที่ตอบไม่ได้ ที่ระบบปฏิเสธได้ถูกต้อง
                           (ตามแนวทาง Chen et al., 2024, AAAI — RGB benchmark)
  5. Hallucination Rate (unanswerable) = 1 − Negative Rejection Rate
  6. Latency             : เวลาตอบเฉลี่ย (วินาที)

การตัดสินว่า "ปฏิเสธ" ทำ 2 ขั้น
  - ขั้นอัตโนมัติ: ตรวจวลีปฏิเสธ (REFUSAL_PATTERNS) → auto_label = refused / answered / review
  - ขั้นตรวจทาน: ผู้วิจัยกรอกคอลัมน์ final_label ในไฟล์ review CSV (ถ้าต้องการแก้)
    แล้วรัน --evaluate <ไฟล์ csv> เพื่อคำนวณผลใหม่

ความปลอดภัยต่อระบบเดิม: เหมือน run_ablation.py — ไม่แก้ไฟล์ในโปรเจกต์, ไม่เขียนฐานข้อมูล,
ไม่ส่ง LINE / n8n, ปิดการเขียน logs/no_context.log, ผลลัพธ์อยู่ใน ablation_results/ เท่านั้น

ตัวชี้วัด RAGAS (ชุดเดียวกับการทดสอบระบบใหญ่ — ใช้ src.eval.ragas_metrics.evaluate_single)
  Faithfulness, Answer Relevance, Context Relevance
  แบบ A ไม่มีการค้นคืน จึงรายงานได้เฉพาะ Answer Relevance (อีก 2 ค่าเป็น N/A)

รัน:
    python -m scripts.run_compare3                       # ขั้น 1: สร้างคำตอบ 3 แบบ + key-fact
                                                         #   (โควตาหมด → รันซ้ำ ทำต่อจากข้อที่ค้าง)
    python -m scripts.run_compare3 --ragas ablation_results/compare3_xxx.json
                                                         # ขั้น 2: คำนวณ RAGAS (ทำต่อได้ถ้าโควตาหมด)
    python -m scripts.run_compare3 --runs 3              # รันซ้ำข้อละ 3 รอบ
    python -m scripts.run_compare3 --evaluate ablation_results/compare3_xxx_review.csv
                                                         # คำนวณผลใหม่หลังตรวจทาน final_label
"""

import os
os.environ.setdefault("CSIT_ENABLE_KG", "1")

import re
import csv
import json
import time
import logging
import argparse
import datetime
from pathlib import Path
from statistics import mean
from unittest.mock import patch


# ─────────────────────────────────────────────────────────────
# ชุดคำถาม
#   facts      : ข้อเท็จจริงที่คำตอบ "ต้องมี" (regex; ใช้ | แทน "หรือ")
#   forbidden  : ข้อความที่ "ต้องไม่มี" (ถ้าพบ = แต่งข้อมูล / ขัดกับนโยบาย)
#   unanswerable ไม่มี facts — คำตอบที่ถูกคือการปฏิเสธ
# ─────────────────────────────────────────────────────────────
THAI_MONTHS = r"(มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม|ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)"

QUESTIONS = [
    # ---------- answerable ----------
    {"id": "A1", "type": "answerable", "question": "ลงทะเบียนช้า 7 วัน ต้องจ่ายเท่าไร",
     "reference": "ค่าปรับ 7 × 25 = 175 บาท (เกิน 2 สัปดาห์พ้นสภาพ)",
     "facts": [r"175"], "forbidden": []},
    {"id": "A2", "type": "answerable", "question": "ขั้นตอนยื่นขอสำเร็จการศึกษาทำยังไง",
     "reference": "แจ้งจบในระบบ reg.nu.ac.th เมนูตรวจสอบจบ, ใช้แบบ NU25, รูปชุดครุย 2 รูป",
     "facts": [r"reg\.nu\.ac\.th|ระบบทะเบียน", r"ตรวจสอบจบ|แจ้งจบ", r"nu\s?25", r"ครุย"], "forbidden": []},
    {"id": "A3", "type": "answerable", "question": "พี่เฟิร์นเบอร์โทรอะไร",
     "reference": "055-963262",
     "facts": [r"055[-\s]?963262"], "forbidden": []},
    {"id": "A4", "type": "answerable", "question": "เปิดเทอมวันไหน",
     "reference": "ไม่ระบุวันที่เอง แนะนำปฏิทินการศึกษาของมหาวิทยาลัย",
     "facts": [r"calendar\.asp|ปฏิทินการศึกษา"],
     "forbidden": [r"\d{1,2}\s*" + THAI_MONTHS]},          # ระบุวันที่เอง = แต่งข้อมูล
    {"id": "A5", "type": "answerable", "question": "GPA 3.55 ได้เกียรตินิยมไหม ต้องมีเงื่อนไขอะไรอีก",
     "reference": "อันดับหนึ่ง; ไม่เคยได้ F/U, ไม่เคยเรียนซ้ำ, เทียบโอนไม่เกิน 1/6",
     "facts": [r"อันดับ\s?(หนึ่ง|1)", r"\bF\b", r"ซ้ำ", r"1\s?/\s?6|1\s?ใน\s?6|หนึ่งในหก"], "forbidden": []},
    {"id": "A6", "type": "answerable", "question": "NU18 ใช้ทำอะไร",
     "reference": "คำร้องทั่วไป เช่น ขอลงทะเบียนเกินหน่วยกิต / ขอเทียบรายวิชา",
     "facts": [r"คำร้องทั่วไป", r"หน่วยกิต|เทียบรายวิชา"], "forbidden": [r"รหัสประจำตัวนิสิต"]},

    # ---------- unanswerable (ต้องตรวจก่อนว่าไม่มีในฐานความรู้จริง) ----------
    {"id": "U1", "type": "unanswerable", "question": "ค่าจอดรถรายเดือนในมหาวิทยาลัยเท่าไร",
     "reference": "ไม่มีในฐานความรู้ → ต้องปฏิเสธ", "facts": [], "forbidden": []},
    {"id": "U2", "type": "unanswerable", "question": "ร้านถ่ายเอกสารในตึก SC2 อยู่ชั้นไหน",
     "reference": "ไม่มีในฐานความรู้ → ต้องปฏิเสธ", "facts": [], "forbidden": []},
    {"id": "U3", "type": "unanswerable", "question": "โรงอาหารคณะวิทยาศาสตร์มีเมนูอะไรแนะนำบ้าง",
     "reference": "ไม่มีในฐานความรู้ → ต้องปฏิเสธ", "facts": [], "forbidden": []},
    {"id": "U4", "type": "unanswerable", "question": "วิชาเลือกเสรีตัวไหนได้เกรด A ง่ายที่สุด",
     "reference": "ไม่มีในฐานความรู้ → ต้องปฏิเสธ", "facts": [], "forbidden": []},
]

CONFIGS = {
    "A": "LLM อย่างเดียว",
    "B": "LLM + RAG",
    "C": "LLM + RAG + Rule-Based",
}

# วลีที่แสดงว่าระบบปฏิเสธ / ไม่มีข้อมูล
REFUSAL_PATTERNS = [
    r"ยังไม่มีข้อมูล", r"ไม่มีข้อมูล", r"ไม่พบข้อมูล", r"ไม่มีรายละเอียด",
    r"ไม่สามารถ(ให้|ตอบ|ระบุ|แนะนำ)", r"ไม่ทราบ", r"ไม่แน่ใจ", r"ขออภัย",
]
SHORT_REFUSAL_MAX = 350   # ปฏิเสธ + สั้น = refused ; ปฏิเสธ + ยาว = review (อาจปฏิเสธแล้วแต่งต่อ)

LLM_ONLY_PROMPT = (
    "คุณคือ 'น้องซีที' ผู้ช่วย AI ของภาควิชาวิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ "
    "คณะวิทยาศาสตร์ มหาวิทยาลัยนเรศวร ตอบคำถามของนิสิตเป็นภาษาไทยสุภาพ ลงท้ายด้วย \"ค่ะ\""
)


# ─────────────────────────────────────────────────────────────
# การประเมิน (ไม่ต้องใช้ LLM / ฐานข้อมูล — รันแยกได้)
# ─────────────────────────────────────────────────────────────
def _norm(text: str) -> str:
    return (text or "").replace(",", "").lower()


def auto_label(answer: str) -> str:
    t = answer or ""
    if not t.strip():
        return "refused"
    if any(re.search(p, t) for p in REFUSAL_PATTERNS):
        return "refused" if len(t) <= SHORT_REFUSAL_MAX else "review"
    return "answered"


def fact_check(answer: str, facts: list, forbidden: list):
    t = _norm(answer)
    found = [bool(re.search(f, t, re.IGNORECASE)) for f in facts]
    bad = [f for f in forbidden if re.search(f, t, re.IGNORECASE)]
    recall = sum(found) / len(found) if found else 0.0
    return recall, found, bad


def score_row(row: dict, q: dict) -> dict:
    label = (row.get("final_label") or "").strip() or row["auto_label"]
    out = {"label_used": label}
    if q["type"] == "answerable":
        recall, found, bad = fact_check(row["answer"], q["facts"], q["forbidden"])
        refused = label == "refused"
        correct = (not refused) and all(found) and not bad
        out.update(fact_recall=0.0 if refused else round(recall, 3),
                   facts_missing="; ".join(f for f, ok in zip(q["facts"], found) if not ok),
                   forbidden_found="; ".join(bad),
                   false_refusal=refused, correct=correct)
    else:
        rejected = label == "refused"
        out.update(fact_recall="", facts_missing="", forbidden_found="",
                   false_refusal="", correct=rejected)
    return out


def evaluate(rows: list) -> dict:
    qmap = {q["id"]: q for q in QUESTIONS}
    pending = [r for r in rows
               if ((r.get("final_label") or "").strip() or r["auto_label"]) == "review"]
    for r in rows:
        r.update(score_row(r, qmap[r["id"]]))

    summary = {}
    for cid, label in CONFIGS.items():
        rs = [r for r in rows if r["config"] == cid]
        ans = [r for r in rs if qmap[r["id"]]["type"] == "answerable"]
        una = [r for r in rs if qmap[r["id"]]["type"] == "unanswerable"]
        rej = mean(1.0 if r["correct"] else 0.0 for r in una) if una else None
        summary[cid] = {
            "name": label,
            "n_answerable": len(ans),
            "n_unanswerable": len(una),
            "key_fact_accuracy": round(mean(1.0 if r["correct"] else 0.0 for r in ans), 3) if ans else None,
            "mean_fact_recall": round(mean(float(r["fact_recall"]) for r in ans), 3) if ans else None,
            "false_refusal_rate": round(mean(1.0 if r["false_refusal"] else 0.0 for r in ans), 3) if ans else None,
            "forbidden_hits": sum(1 for r in ans if r["forbidden_found"]),
            "negative_rejection_rate": round(rej, 3) if rej is not None else None,
            "hallucination_rate_unanswerable": round(1 - rej, 3) if rej is not None else None,
            "overall_correct_behavior": round(mean(1.0 if r["correct"] else 0.0 for r in rs), 3),
            "mean_latency_s": round(mean(float(r["seconds"]) for r in rs), 2),
        }
    return {"summary": summary, "pending_review": [(r["id"], r["config"], r["run"]) for r in pending]}


def write_outputs(rows: list, meta: dict, base: Path):
    result = evaluate(rows)
    fields = ["id", "type", "question", "config", "config_name", "run", "answer", "route", "sources",
              "seconds", "error", "reference", "auto_label", "final_label", "label_used",
              "correct", "fact_recall", "facts_missing", "forbidden_found", "false_refusal"]
    review_csv = base.with_name(base.name + "_review.csv")
    with open(review_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    s = result["summary"]
    lines = [
        "| ตัวชี้วัด | " + " | ".join(f"{c}. {s[c]['name']}" for c in CONFIGS) + " |",
        "|---|" + "---|" * len(CONFIGS),
    ]
    def pct(v):
        return "-" if v is None else f"{v*100:.1f}%"
    for key, name, fmt in [
        ("key_fact_accuracy", "Key-fact Accuracy (คำถามที่ตอบได้)", pct),
        ("mean_fact_recall", "Fact Recall เฉลี่ย", lambda v: "-" if v is None else f"{v:.3f}"),
        ("false_refusal_rate", "False Refusal Rate", pct),
        ("forbidden_hits", "จำนวนคำตอบที่มีข้อความต้องห้าม", str),
        ("negative_rejection_rate", "Negative Rejection Rate (คำถามที่ตอบไม่ได้)", pct),
        ("hallucination_rate_unanswerable", "Hallucination Rate (คำถามที่ตอบไม่ได้)", pct),
        ("overall_correct_behavior", "พฤติกรรมถูกต้องโดยรวม", pct),
        ("mean_latency_s", "เวลาตอบเฉลี่ย (วินาที)", str),
    ]:
        lines.append(f"| {name} | " + " | ".join(fmt(s[c][key]) for c in CONFIGS) + " |")
    table = "\n".join(lines)

    summary_path = base.with_name(base.name + "_summary.json")
    summary_path.write_text(json.dumps({"meta": meta, **result, "table_markdown": table},
                                       ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = base.with_name(base.name + "_summary.md")
    md_path.write_text(table + "\n", encoding="utf-8")

    print("\n" + table)
    if result["pending_review"]:
        print(f"\n⚠️  มี {len(result['pending_review'])} คำตอบที่ต้องตรวจทาน (auto_label = review):")
        for i, c, r in result["pending_review"]:
            print(f"   {i} แบบ {c} รอบ {r}")
        print("   กรอก final_label (refused / answered) ใน review CSV แล้วรัน --evaluate ไฟล์นั้นอีกครั้ง")
        print("   ระหว่างนี้คำตอบที่ยังเป็น review จะไม่นับว่าเป็นการปฏิเสธ")
    print(f"\nไฟล์ผล:\n  {review_csv}\n  {summary_path}\n  {md_path}")


def evaluate_only(csv_path: str):
    path = Path(csv_path)
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    base = path.with_name(path.stem.replace("_review", "") + "_reeval")
    write_outputs(rows, {"evaluated_from": str(path)}, base)


# ─────────────────────────────────────────────────────────────
# ระบบ 3 แบบ
#   C ใช้ answer_full (ชั้นที่ 2 เปิด KG) — วิธีเดียวกับ run_kg_eval / run_baseline_eval
#   เพื่อให้ทุกคำตอบมีบริบทให้คำนวณ RAGAS ได้ และเทียบกับผลระบบใหญ่ได้ตรงกัน
# ─────────────────────────────────────────────────────────────
def build_runners(temperature: float):
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_google_genai import ChatGoogleGenerativeAI
    from src.config import GOOGLE_API_KEY
    from src import chat, retriever
    from src.retriever import QueryAnalysis

    logging.getLogger().setLevel(logging.WARNING)
    if not GOOGLE_API_KEY:
        raise SystemExit("ไม่พบ GOOGLE_API_KEY ใน .env")
    trace = {}

    class _QuotaAwareLLM:
        """ห่อ LLM เพื่อจับ error โควตา — rewrite_query ใน chat.py ดัก exception ทุกชนิดไว้เอง
        ถ้าไม่จับตรงนี้ ข้อที่โควตาหมดจะถูกบันทึกผิดเป็น "ตอบไม่ได้" """
        def __init__(self, inner):
            self.inner = inner

        def invoke(self, *a, **k):
            try:
                return self.inner.invoke(*a, **k)
            except Exception as e:
                if any(m in str(e) for m in ("RESOURCE_EXHAUSTED", "429", "quota")):
                    trace["quota_error"] = e
                raise

    chat._llm = _QuotaAwareLLM(ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite",
                                                      temperature=temperature,
                                                      google_api_key=GOOGLE_API_KEY))

    orig_retrieve = retriever.retrieve_context

    def traced_retrieve(question, verbose=False, history=None):
        ctx = orig_retrieve(question, verbose=verbose, history=history or [])
        trace.setdefault("sources", []).extend(ctx.sources_used)
        trace["last_ctx"] = ctx          # บริบทชุดสุดท้าย = ชุดที่ส่งให้ LLM สร้างคำตอบจริง
        return ctx

    def run_llm_only(q):
        resp = chat.get_llm().invoke([SystemMessage(content=LLM_ONLY_PROMPT), HumanMessage(content=q)])
        return chat._strip_markdown(resp.content).strip(), "llm"

    def run_llm_rag(q):
        chroma_only = lambda question: QueryAnalysis(original_query=question, entities={},
                                                     sources_to_use=["chroma"])
        with patch.object(retriever, "classify_query", chroma_only), \
             patch.object(chat, "is_scholarship_query", lambda question: False):
            result = chat.answer_full(q, history=[])
        return result.text, "answer_full(chroma_only)"

    def run_full(q):
        result = chat.answer_full(q, history=[])
        return result.text, "answer_full(full)"

    guards = [patch.object(chat, "log_unanswered_question", lambda q: None),
              patch.object(retriever, "retrieve_context", traced_retrieve)]
    return {"A": run_llm_only, "B": run_llm_rag, "C": run_full}, trace, guards


PROGRESS_NAME = "compare3_progress.json"


def generate(args):
    """สร้างคำตอบ — บันทึกทีละข้อลง ablation_results/compare3_progress.json
    ถ้าโควตาหมด รันคำสั่งเดิมซ้ำได้ จะทำต่อจากข้อที่ค้าง (ใช้ --fresh ถ้าจะเริ่มใหม่หมด)"""
    from src.config import PROJECT_ROOT
    from src.eval.run_baseline_eval import _call_with_rpm_retry, is_quota_error, is_daily_quota_error
    runners, trace, guards = build_runners(args.temperature)

    out_dir = PROJECT_ROOT / "ablation_results"
    out_dir.mkdir(exist_ok=True)
    prog_path = out_dir / PROGRESS_NAME
    if args.fresh and prog_path.exists():
        prog_path.unlink()

    from src.retriever import ENABLE_KG
    if prog_path.exists():
        data = json.loads(prog_path.read_text(encoding="utf-8"))
        if data["meta"]["temperature"] != args.temperature or data["meta"]["runs"] != args.runs:
            raise SystemExit("ค่า --temperature / --runs ไม่ตรงกับไฟล์ที่ค้างไว้ — ใช้ค่าเดิม หรือเพิ่ม --fresh เพื่อเริ่มใหม่")
    else:
        data = {"meta": {"started_at": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                         "model": "gemini-2.5-flash-lite", "temperature": args.temperature,
                         "enable_kg": ENABLE_KG, "runs": args.runs},
                "questions": QUESTIONS, "results": []}
    rows = data["results"]
    done = {(r["id"], r["config"], r["run"]) for r in rows}
    total = len(QUESTIONS) * len(CONFIGS) * args.runs
    print(f"ทำแล้ว {len(done)}/{total} คำตอบ\n")

    stopped = False
    for g in guards:
        g.start()
    try:
        for q in QUESTIONS:
            for cid, cname in CONFIGS.items():
                for run in range(1, args.runs + 1):
                    if (q["id"], cid, run) in done:
                        continue
                    trace.clear()
                    t0 = time.time()
                    try:
                        answer, route = _call_with_rpm_retry(runners[cid], q["question"])
                        err = ""
                    except Exception as e:
                        if is_quota_error(e):
                            trace["quota_error"] = e
                            answer, route, err = "", "", ""
                        else:
                            answer, route, err = "", "", f"{type(e).__name__}: {e}"
                    qe = trace.get("quota_error")
                    if qe is not None:
                        # โควตาหมดระหว่างข้อนี้ (รวมกรณี rewrite_query กลืน error ไว้) — ไม่บันทึกข้อนี้
                        kind = "รายวัน (RPD)" if is_daily_quota_error(qe) else "ต่อนาที/อื่น ๆ"
                        print(f"\nโควตา API หมด [{kind}] ที่ {q['id']} แบบ {cid}")
                        print(f"  ข้อความ: {str(qe)[:300]}")
                        stopped = True
                        break
                    ctx = trace.get("last_ctx")
                    context_text = ctx.to_prompt_text() if (ctx is not None and ctx.has_any()) else ""
                    rows.append({
                        "id": q["id"], "type": q["type"], "question": q["question"],
                        "config": cid, "config_name": cname, "run": run,
                        "answer": answer, "route": route,
                        "sources": ", ".join(dict.fromkeys(trace.get("sources", []))),
                        "context": context_text,
                        "seconds": round(time.time() - t0, 2), "error": err,
                        "reference": q["reference"],
                        "auto_label": auto_label(answer), "final_label": "",
                    })
                    prog_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"[{q['id']}] {cid}. {cname:<24} run {run}  {'ERROR' if err else 'ok'}")
                    time.sleep(args.sleep)
                if stopped:
                    break
            if stopped:
                break
    finally:
        for g in guards:
            g.stop()

    if stopped:
        print(f"บันทึกแล้ว {len(rows)}/{total} คำตอบที่ {prog_path}")
        print("รอโควตากลับมาแล้วรันคำสั่งเดิมซ้ำ: python -m scripts.run_compare3")
        return

    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    data["meta"]["finished_at"] = stamp
    json_path = out_dir / f"compare3_{stamp}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    prog_path.unlink()
    write_outputs(rows, data["meta"], out_dir / f"compare3_{stamp}")
    print(f"\nขั้นต่อไป (RAGAS):\n  python -m scripts.run_compare3 --ragas {json_path}")


# ─────────────────────────────────────────────────────────────
# RAGAS — ใช้ evaluate_single ตัวเดียวกับ run_baseline_eval / run_kg_eval
#   B, C : Faithfulness, Answer Relevance, Context Relevance (เมื่อมีบริบท)
#   A    : Answer Relevance เท่านั้น — ไม่มีบริบท จึงไม่นิยาม Faithfulness / Context Relevance (N/A)
#   บันทึกผลทีละข้อ ถ้าโควตาหมดรันคำสั่งเดิมซ้ำได้ จะทำต่อจากข้อที่ค้าง
# ─────────────────────────────────────────────────────────────
NO_CONTEXT_PLACEHOLDER = "(ไม่มีบริบท — ใช้คำนวณ Answer Relevance เท่านั้น)"


def run_ragas(json_path: str, n_questions: int):
    from src.eval.ragas_metrics import evaluate_single
    from src.eval.run_baseline_eval import _call_with_rpm_retry, is_quota_error

    path = Path(json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["results"]
    todo = [r for r in rows if "ragas" not in r and not r.get("error")]
    print(f"ต้องคำนวณ RAGAS อีก {len(todo)} จาก {len(rows)} คำตอบ (n_questions={n_questions})\n")

    for k, r in enumerate(todo, 1):
        has_ctx = bool(r.get("context", "").strip())
        if r["config"] != "A" and not has_ctx:
            r["ragas"] = None            # ไม่มีบริบท (เช่น ตอบไม่ได้แล้วไม่พบเอกสาร) — ข้ามเหมือน baseline
            r["ragas_note"] = "no_context"
        else:
            ctx = r["context"] if has_ctx else NO_CONTEXT_PLACEHOLDER
            try:
                res = _call_with_rpm_retry(evaluate_single, r["question"], r["answer"], ctx,
                                           n_questions=n_questions)
            except Exception as e:
                if is_quota_error(e):
                    print("โควตา API หมด — บันทึกผลที่ทำแล้ว รันคำสั่งเดิมซ้ำเพื่อทำต่อ")
                    break
                print(f"  RAGAS พลาด ({r['id']} {r['config']}): {e}")
                res = None
            if res is not None and r["config"] == "A":
                # เก็บเฉพาะ Answer Relevance — อีก 2 ค่าไม่มีความหมายเมื่อไม่มีบริบท
                res = {"answer_relevance": res.get("answer_relevance"),
                       "faithfulness": {"score": None, "note": "N/A (no retrieval)"},
                       "context_relevance": {"score": None, "note": "N/A (no retrieval)"}}
            r["ragas"] = res
        print(f"[{k}/{len(todo)}] {r['id']} {r['config']}  {'ok' if r.get('ragas') else r.get('ragas_note', 'skip')}")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    summarize_ragas(data, path)


def summarize_ragas(data: dict, path: Path):
    rows = data["results"]
    metrics = [("faithfulness", "Faithfulness"),
               ("answer_relevance", "Answer Relevance"),
               ("context_relevance", "Context Relevance")]

    def score(r, m):
        g = r.get("ragas") or {}
        v = (g.get(m) or {}).get("score")
        return None if v is None else float(v)

    out = {}
    lines = []
    for subset, label in [("answerable", "คำถามที่ตอบได้"), ("all", "ทุกคำถาม")]:
        lines += [f"\n**RAGAS — {label}** (ค่าเฉลี่ย, n = จำนวนคำตอบที่คำนวณได้)\n",
                  "| ตัวชี้วัด | " + " | ".join(f"{c}. {n}" for c, n in CONFIGS.items()) + " |",
                  "|---|" + "---|" * len(CONFIGS)]
        out[subset] = {}
        for m, mname in metrics:
            cells = []
            for c in CONFIGS:
                vals = [score(r, m) for r in rows if r["config"] == c
                        and (subset == "all" or r["type"] == "answerable")]
                vals = [v for v in vals if v is not None]
                if c == "A" and m != "answer_relevance":
                    cells.append("N/A")
                    out[subset].setdefault(c, {})[m] = None
                elif vals:
                    cells.append(f"{mean(vals):.3f} (n={len(vals)})")
                    out[subset].setdefault(c, {})[m] = {"mean": round(mean(vals), 3), "n": len(vals)}
                else:
                    cells.append("-")
                    out[subset].setdefault(c, {})[m] = None
            lines.append(f"| {mname} | " + " | ".join(cells) + " |")
    table = "\n".join(lines)
    print(table)
    base = path.with_suffix("")
    base.with_name(base.name + "_ragas_summary.md").write_text(table + "\n", encoding="utf-8")
    base.with_name(base.name + "_ragas_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nไฟล์ผล RAGAS:\n  {base.name}_ragas_summary.md\n  {base.name}_ragas_summary.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--fresh", action="store_true", help="ลบไฟล์ที่ค้างแล้วเริ่มสร้างคำตอบใหม่หมด")
    ap.add_argument("--evaluate", type=str, default="", help="คำนวณ key-fact ใหม่จาก review CSV")
    ap.add_argument("--ragas", type=str, default="", help="คำนวณ RAGAS จากไฟล์ compare3_*.json")
    ap.add_argument("--n-questions", type=int, default=3, help="จำนวนคำถามย้อนสร้างของ Answer Relevance")
    args = ap.parse_args()

    if args.evaluate:
        evaluate_only(args.evaluate)
    elif args.ragas:
        run_ragas(args.ragas, args.n_questions)
    else:
        generate(args)


if __name__ == "__main__":
    main()
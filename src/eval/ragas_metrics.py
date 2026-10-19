import re
import json
import numpy as np

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

from src.config import GOOGLE_API_KEY

_judge_llm = None
_embed_model = None


def get_judge_llm():
    global _judge_llm
    if _judge_llm is None:
        _judge_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            google_api_key=GOOGLE_API_KEY,
        )
    return _judge_llm


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=GOOGLE_API_KEY,
        )
    return _embed_model


def _ask_judge(system_prompt: str, user_prompt: str) -> str:
    resp = get_judge_llm().invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return resp.content.strip()


def _strip_code_fence(raw: str) -> str:
    """LLM บางทีตอบ JSON ห่อด้วย ```json ... ``` — ตัดออกก่อน parse"""
    return re.sub(r"^```(json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE).strip()

STATEMENT_EXTRACT_PROMPT = """คุณเป็นผู้ช่วยแตกคำตอบให้เป็น "ข้อความย่อย" (statement)
แต่ละข้อความย่อยต้องเป็นข้อเท็จจริงเดี่ยว ๆ ที่ตรวจสอบได้ทีละอัน
ตอบเป็น JSON list ของ string เท่านั้น เช่น ["ข้อความย่อยที่ 1", "ข้อความย่อยที่ 2"]
ห้ามมีคำอธิบายอื่นปนมา"""

VERIFY_PROMPT = """พิจารณา context และข้อความย่อยต่อไปนี้ ตอบว่าข้อความย่อยนี้
"มีหลักฐานรองรับอยู่ใน context" หรือไม่
ตอบเป็น JSON บรรทัดเดียวเท่านั้น: {"verdict": "yes"} หรือ {"verdict": "no"}
ห้ามมีคำอธิบายอื่นปนมา"""

BATCH_VERIFY_PROMPT = """พิจารณา context และรายการข้อความย่อยที่มีหมายเลขกำกับต่อไปนี้
สำหรับแต่ละข้อความย่อย ตัดสินว่า "มีหลักฐานรองรับอยู่ใน context" หรือไม่
ตอบเป็น JSON list ของ true/false เท่านั้น เรียงลำดับตรงกับหมายเลขข้อความย่อย
เช่น ถ้ามี 3 ข้อความย่อย และข้อ 1,3 มีหลักฐาน ข้อ 2 ไม่มี ให้ตอบ [true, false, true]
ห้ามมีคำอธิบายอื่นปนมา ห้ามมีข้อความอื่นนอกจาก JSON list"""


def extract_statements(question: str, answer: str) -> list[str]:
    prompt = f"คำถาม: {question}\nคำตอบ: {answer}"
    raw = _strip_code_fence(_ask_judge(STATEMENT_EXTRACT_PROMPT, prompt))
    try:
        statements = json.loads(raw)
        if isinstance(statements, list) and statements:
            return [str(s) for s in statements]
    except Exception:
        pass
    return [s.strip() for s in re.split(r"[.\n]", answer) if s.strip()]


def verify_statement(statement: str, context: str) -> bool:
    """ตรวจทีละ statement (1 เรียก LLM ต่อ 1 statement) — เก็บไว้เป็น fallback
    ตอนนี้ faithfulness_score() ใช้ verify_statements_batch() แทนเป็นค่าเริ่มต้น
    เพื่อประหยัดโควตา (สำคัญมากตอนใช้ Gemini free tier ที่จำกัดแค่ 20 คำขอ/วัน/โมเดล)"""
    prompt = f"context:\n{context}\n\nข้อความย่อย: {statement}"
    raw = _strip_code_fence(_ask_judge(VERIFY_PROMPT, prompt))
    try:
        data = json.loads(raw)
        return str(data.get("verdict", "")).lower().startswith("y")
    except Exception:
        return "yes" in raw.lower()


def verify_statements_batch(statements: list[str], context: str) -> list[bool]:
    """ตรวจ statement ทั้งหมดในคำขอ LLM เดียว แทนที่จะเรียกทีละอัน
    ลดจาก N ครั้ง เหลือ 1 ครั้งต่อคำถาม — ประหยัดโควตาได้มากสุดในทั้งไฟล์นี้
    ถ้า LLM ตอบ JSON ไม่ตรงจำนวน/parse ไม่ได้ จะ fallback ไปเรียกทีละอันแทน (กันพลาด)"""
    if not statements:
        return []

    numbered = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(statements))
    prompt = f"context:\n{context}\n\nข้อความย่อย ({len(statements)} ข้อ):\n{numbered}"
    raw = _strip_code_fence(_ask_judge(BATCH_VERIFY_PROMPT, prompt))
    try:
        data = json.loads(raw)
        if isinstance(data, list) and len(data) == len(statements):
            return [
                v if isinstance(v, bool) else str(v).lower().startswith("y")
                for v in data
            ]
    except Exception:
        pass
    return [verify_statement(s, context) for s in statements]


def faithfulness_score(question: str, answer: str, context: str) -> dict:
    """F = |V| / |S|  (V = statement ที่มีหลักฐานรองรับ, S = statement ทั้งหมด)"""
    statements = extract_statements(question, answer)
    if not statements:
        return {"score": None, "num_statements": 0, "num_supported": 0, "details": []}

    verdicts = verify_statements_batch(statements, context)
    details = [{"statement": s, "supported": v} for s, v in zip(statements, verdicts)]
    supported = sum(1 for v in verdicts if v)

    return {
        "score": supported / len(statements),
        "num_statements": len(statements),
        "num_supported": supported,
        "details": details,
    }

QUESTION_GEN_PROMPT = """จากคำตอบต่อไปนี้ ให้สร้างคำถามที่เป็นไปได้ 1 ข้อ
ที่คำตอบนี้น่าจะเป็นคำตอบของคำถามนั้น
ตอบเป็นคำถามเดียว บรรทัดเดียวเท่านั้น ห้ามมีคำอธิบายอื่นปนมา"""


def generate_question_from_answer(answer: str) -> str:
    return _ask_judge(QUESTION_GEN_PROMPT, f"คำตอบ: {answer}")


def _cosine(a, b) -> float:
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def answer_relevance_score(question: str, answer: str, n: int = 3) -> dict:
    generated_qs = [generate_question_from_answer(answer) for _ in range(n)]
    embed = get_embed_model()
    q_vec = embed.embed_query(question)

    sims = []
    for gq in generated_qs:
        gq_vec = embed.embed_query(gq)
        sims.append(_cosine(q_vec, gq_vec))

    return {
        "score": sum(sims) / len(sims) if sims else None,
        "generated_questions": generated_qs,
        "similarities": sims,
    }

EXTRACT_RELEVANT_PROMPT = """จาก context ต่อไปนี้ ให้คัดลอกเฉพาะประโยค/บรรทัดที่
"จำเป็นต่อการตอบคำถามนี้จริง ๆ" มาเท่านั้น (คัดลอกคำต่อคำ ห้ามแต่งใหม่)
ตอบเป็น JSON list ของ string เท่านั้น ถ้าไม่มีประโยคใดเกี่ยวข้องเลยให้ตอบ []
ห้ามมีคำอธิบายอื่นปนมา"""


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"[\n]|(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def context_relevance_score(question: str, context: str) -> dict:
    """CR = จำนวนประโยคที่ LLM คัดว่าเกี่ยวข้อง / จำนวนประโยคทั้งหมดใน context"""
    total_sentences = _split_sentences(context)
    if not total_sentences:
        return {"score": None, "num_relevant": 0, "num_total": 0, "relevant_sentences": []}

    prompt = f"คำถาม: {question}\n\ncontext:\n{context}"
    raw = _strip_code_fence(_ask_judge(EXTRACT_RELEVANT_PROMPT, prompt))
    try:
        relevant = json.loads(raw)
        if not isinstance(relevant, list):
            relevant = []
    except Exception:
        relevant = []

    return {
        "score": len(relevant) / len(total_sentences),
        "num_relevant": len(relevant),
        "num_total": len(total_sentences),
        "relevant_sentences": relevant,
    }

def evaluate_single(question: str, answer: str, context: str, n_questions: int = 3) -> dict:
    return {
        "question": question,
        "answer": answer,
        "faithfulness": faithfulness_score(question, answer, context),
        "answer_relevance": answer_relevance_score(question, answer, n=n_questions),
        "context_relevance": context_relevance_score(question, context),
    }
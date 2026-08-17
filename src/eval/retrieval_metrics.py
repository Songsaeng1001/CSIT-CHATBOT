"""
retrieval_metrics.py — ตัวชี้วัดฝั่ง "ตัวค้นหา" (retriever) ล้วน ๆ
แยกขาดจากคุณภาพการตอบของ LLM ใช้ debug ว่าปัญหาอยู่ที่ค้นข้อมูลผิด หรือ LLM เอาข้อมูล
ถูกไปตอบผิด

อ้างอิง: Manning, C. D., Raghavan, P., & Schütze, H. (2008).
Introduction to Information Retrieval. Cambridge University Press.

การใช้งาน:
    retrieved_ids = list ของ id/source ที่ retriever คืนมา เรียงตามอันดับ (อันดับ 1 ก่อน)
    relevant_ids  = set ของ id/source ที่ "ถูกต้องจริง" ตามเฉลยที่มนุษย์ทำไว้ล่วงหน้า

    ในโปรเจกต์นี้แนะนำใช้ doc.metadata["source"] (ชื่อไฟล์ .md ใน knowledge_base/)
    ที่ได้จาก src.database.vector_db.search() เป็น id — ดูตัวอย่างการเรียกใช้จริงใน
    src/eval/run_baseline_eval.py ฟังก์ชัน retrieval_eval_for_question()
"""

import math


def precision_at_k(retrieved_ids: list, relevant_ids: set, k: int) -> float:
    """Precision@K = (จำนวนที่เกี่ยวข้องใน K อันดับแรก) / K"""
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for x in top_k if x in relevant_ids)
    return hits / len(top_k)


def recall_at_k(retrieved_ids: list, relevant_ids: set, k: int):
    """Recall@K = (จำนวนที่เกี่ยวข้องใน K อันดับแรก) / (จำนวนที่เกี่ยวข้องทั้งหมดที่มีจริง)"""
    if not relevant_ids:
        return None
    top_k = retrieved_ids[:k]
    hits = sum(1 for x in top_k if x in relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(retrieved_ids: list, relevant_ids: set) -> float:
    """1 / อันดับของ item ที่ถูกต้องตัวแรกที่เจอ (0 ถ้าไม่เจอเลย)"""
    for i, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / i
    return 0.0


def mrr(list_of_retrieved: list, list_of_relevant: list) -> float:
    """MRR = (1/|Q|) * sum(1/rank_i) — รับ list ของหลายคำถามพร้อมกัน
    list_of_retrieved[i] = retrieved_ids ของคำถามที่ i
    list_of_relevant[i]  = relevant_ids (set) ของคำถามที่ i
    """
    rrs = [
        reciprocal_rank(r, rel)
        for r, rel in zip(list_of_retrieved, list_of_relevant)
    ]
    return sum(rrs) / len(rrs) if rrs else 0.0


def hit_rate_at_k(list_of_retrieved: list, list_of_relevant: list, k: int) -> float:
    """สัดส่วนคำถามที่มี item ถูกต้องอย่างน้อย 1 ตัวอยู่ใน top-K"""
    if not list_of_retrieved:
        return 0.0
    hits = 0
    for r, rel in zip(list_of_retrieved, list_of_relevant):
        if any(x in rel for x in r[:k]):
            hits += 1
    return hits / len(list_of_retrieved)


def dcg_at_k(retrieved_ids: list, relevance_scores: dict, k: int) -> float:
    """DCG@K = sum(relevance_i / log2(i+1))
    relevance_scores: dict {id: ระดับความเกี่ยวข้อง} เช่น {"a.md": 2, "b.md": 1}
    (0 = ไม่เกี่ยวข้อง, ยิ่งมากยิ่งเกี่ยวข้องมาก)
    """
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k], start=1):
        rel = relevance_scores.get(doc_id, 0)
        dcg += rel / math.log2(i + 1)
    return dcg


def ndcg_at_k(retrieved_ids: list, relevance_scores: dict, k: int) -> float:
    """NDCG@K = DCG@K / IDCG@K (IDCG = DCG ของการจัดอันดับที่ดีที่สุดเท่าที่เป็นไปได้)"""
    dcg = dcg_at_k(retrieved_ids, relevance_scores, k)
    ideal_order = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = sum(rel / math.log2(i + 1) for i, rel in enumerate(ideal_order, start=1))
    return dcg / idcg if idcg > 0 else 0.0


if __name__ == "__main__":
    # ── ตัวอย่างทดสอบด้วยข้อมูลจำลอง (mock) ให้เห็นว่าใช้งานยังไง ──
    retrieved = ["curriculum_cs.md", "instructors_staff.md", "curriculum_it.md"]
    relevant = {"curriculum_cs.md"}

    print("Precision@3:", precision_at_k(retrieved, relevant, 3))
    print("Recall@3:", recall_at_k(retrieved, relevant, 3))
    print("Reciprocal rank:", reciprocal_rank(retrieved, relevant))

    list_retrieved = [
        ["curriculum_cs.md", "instructors_staff.md"],
        ["instructors_staff.md", "curriculum_it.md"],
    ]
    list_relevant = [{"curriculum_cs.md"}, {"instructors_staff.md"}]
    print("MRR:", mrr(list_retrieved, list_relevant))
    print("Hit Rate@2:", hit_rate_at_k(list_retrieved, list_relevant, 2))

    rel_scores = {"curriculum_cs.md": 2, "instructors_staff.md": 1, "curriculum_it.md": 0}
    print("NDCG@3:", ndcg_at_k(retrieved, rel_scores, 3))

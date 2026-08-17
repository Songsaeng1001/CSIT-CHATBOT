#!/usr/bin/env python3
"""
verify_stats.py — ตรวจสอบ A/B comparison อิสระ + คำนวณ Benjamini-Hochberg ใหม่ให้ถูกต้อง
อ่านจากไฟล์ผล 2 ไฟล์ที่มีอยู่แล้ว ไม่เรียก LLM ไม่กินโควตา

จุดที่แก้จากของเดิม:
  1) คัดการทดสอบที่ p เป็น nan (เกิดจาก zero-variance / diff=0 ทั้งกลุ่ม หรือ n<3)
     ออกจาก "ครอบครัว BH" ก่อน correction — ไม่ให้ nan ไปทำให้ q ทั้งชุดเพี้ยน
  2) รับประกัน q >= p เสมอ (คุณสมบัติพื้นฐานของ BH) มี assert กันพลาด

ใช้:
    python3 verify_stats.py baseline_results.json kg_results.json
"""
import sys, json, math
from collections import defaultdict
from scipy import stats

METRICS = [("faithfulness","Faithfulness"),
           ("answer_relevance","Answer Relevance"),
           ("context_relevance","Context Relevance")]
MIN_N = 3

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def score(entry, key):
    r = entry.get("ragas")
    if not r or r.get(key) is None:
        return None
    return r[key].get("score")

def bh_correct(pairs):
    """pairs = list of (label, p). คืน dict label->q.
    รับเฉพาะ p ที่เป็นเลขจริง (ไม่ nan/None). q >= p เสมอ."""
    valid = [(lbl, p) for lbl, p in pairs if p is not None and not math.isnan(p)]
    m = len(valid)
    out = {}
    if m == 0:
        return out
    valid.sort(key=lambda x: x[1])
    # q_raw ตาม rank
    q_raw = [(lbl, p * m / (rank+1)) for rank, (lbl, p) in enumerate(valid)]
    # step-up: บังคับ monotonic จากท้ายมาหน้า + cap ที่ 1.0
    running = 1.0
    q_final = {}
    for rank in range(m-1, -1, -1):
        lbl, q = q_raw[rank]
        running = min(running, q)
        q_final[lbl] = min(running, 1.0)
    # sanity: q >= p เสมอ
    pmap = dict(valid)
    for lbl, q in q_final.items():
        assert q >= pmap[lbl] - 1e-9, f"BH ผิด: q={q} < p={pmap[lbl]} ที่ {lbl}"
    return q_final

def main():
    base = load(sys.argv[1]); kg = load(sys.argv[2])
    bd = {e["id"]: e for e in base}
    matched = [(bd[e["id"]], e) for e in kg if e["id"] in bd]
    print(f"🔗 จับคู่ด้วย id ได้ {len(matched)} ข้อ\n")

    by_type = defaultdict(list)
    for a, b in matched:
        by_type[a.get("type") or b.get("type")].append((a, b))

    # เก็บผลทุก cell (type x metric) ก่อน แล้วค่อยทำ BH ทีเดียวทั้ง family
    cells = []   # (type, metric_label, n, mean_a, mean_b, diff, t_p, w_p, note)
    t_family, w_family = [], []

    for typ in sorted(by_type):
        for mkey, mlabel in METRICS:
            a_scores, b_scores = [], []
            for a, b in by_type[typ]:
                sa, sb = score(a, mkey), score(b, mkey)
                if sa is not None and sb is not None:
                    a_scores.append(sa); b_scores.append(sb)
            n = len(a_scores)
            label = f"{typ}|{mlabel}"
            if n < MIN_N:
                cells.append((typ, mlabel, n, None, None, None, None, None, "n<3 ข้ามการทดสอบ"))
                continue
            diffs = [x-y for x,y in zip(b_scores, a_scores)]
            mean_a = sum(a_scores)/n; mean_b = sum(b_scores)/n
            diff = mean_b - mean_a
            if all(abs(d) < 1e-12 for d in diffs):
                # diff=0 ทุกคู่ → ไม่มีอะไรให้ทดสอบ (KG ไม่เปลี่ยนคำตอบกลุ่มนี้)
                cells.append((typ, mlabel, n, mean_a, mean_b, diff, None, None, "diff=0 ทุกคู่ ไม่ทดสอบ"))
                continue
            # paired t-test
            try:
                t_stat, t_p = stats.ttest_rel(b_scores, a_scores)
                if math.isnan(t_p): t_p = None
            except Exception:
                t_p = None
            # Wilcoxon (drop zeros ตาม default)
            try:
                w_stat, w_p = stats.wilcoxon(b_scores, a_scores)
                if math.isnan(w_p): w_p = None
            except Exception:
                w_p = None
            cells.append((typ, mlabel, n, mean_a, mean_b, diff, t_p, w_p, ""))
            if t_p is not None: t_family.append((label, t_p))
            if w_p is not None: w_family.append((label, w_p))

    t_q = bh_correct(t_family)
    w_q = bh_correct(w_family)

    print(f"📊 ครอบครัว BH: t-test {len(t_family)} การทดสอบ, Wilcoxon {len(w_family)} การทดสอบ")
    print(f"   (คัดเคย nan/zero-variance/n<3 ออกก่อนแล้ว)\n")

    cur = None
    for typ, mlabel, n, ma, mb, diff, tp, wp, note in cells:
        if typ != cur:
            print("="*56); print(f"กลุ่ม: {typ}"); print("="*56); cur = typ
        label = f"{typ}|{mlabel}"
        print(f"\n=== {mlabel} (n={n}) ===")
        if note and ma is None:
            print(f"  {note}"); continue
        print(f"  A={ma:.4f}  B={mb:.4f}  diff(B-A)={diff:+.4f}")
        if note:
            print(f"  {note}"); continue
        def fmt(p, q):
            if p is None: return "p=nan (ข้าม)"
            star = " ✅<.05" if p < 0.05 else ""
            qs = f"q={q:.4f}" if q is not None else "q=—"
            qstar = " ✅<.05" if (q is not None and q < 0.05) else ""
            return f"p={p:.4f}{star}  {qs}{qstar}"
        print(f"  t-test:   {fmt(tp, t_q.get(label))}")
        print(f"  Wilcoxon: {fmt(wp, w_q.get(label))}")

    # สรุปเฉพาะ cell ที่ผ่าน q<.05
    print("\n" + "="*56)
    print("สรุป: cell ที่มีนัยสำคัญหลัง BH correction (q<.05)")
    print("="*56)
    hits = False
    for typ, mlabel, n, ma, mb, diff, tp, wp, note in cells:
        label = f"{typ}|{mlabel}"
        tq, wq = t_q.get(label), w_q.get(label)
        if (tq is not None and tq < 0.05) or (wq is not None and wq < 0.05):
            hits = True
            tqs = f"{tq:.4f}" if tq is not None else "—"
            wqs = f"{wq:.4f}" if wq is not None else "—"
            print(f"  {typ} / {mlabel}: diff={diff:+.4f}  |  t-test q={tqs}  Wilcoxon q={wqs}")
    if not hits:
        print("  (ไม่มี cell ไหนผ่าน q<.05 — ปกติสำหรับ n เล็กต่อ subgroup)")

if __name__ == "__main__":
    main()
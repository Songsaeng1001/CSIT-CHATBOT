"""
compare_stats.py — เทียบผลการวัด (RAGAS scores) ระหว่าง 2 ระบบ แบบ paired
(รันคำถาม "ชุดเดียวกัน" ผ่านทั้ง 2 ระบบ เช่น baseline vector-RAG vs RAG+KG)

ใช้ paired t-test (สมมติข้อมูลกระจายใกล้ปกติ) คู่กับ Wilcoxon signed-rank test
(robust กว่า ไม่ต้องอิงการแจกแจงปกติ) — วิธีเปรียบเทียบระบบค้นคืน/RAG แบบ per-query
paired ตามที่ Smucker, Allan & Carterette (2007) เปรียบเทียบไว้โดยตรงสำหรับงาน IR
evaluation:
    Smucker, M. D., Allan, J., & Carterette, B. (2007). A comparison of
    statistical significance tests for information retrieval evaluation.
    Proceedings of CIKM 2007, 623-632. DOI: 10.1145/1321440.1321528

(แก้ 2026-07-17: เดิมอ้างว่า Edge et al. (2024) GraphRAG (arXiv:2404.16130) ใช้วิธี
เดียวกันนี้รายงาน p-value — ตรวจสอบซ้ำแล้วพบว่า "ไม่ถูกต้อง" เปเปอร์ GraphRAG ตัวจริง
ใช้ LLM-as-judge แบบ win-rate (ให้ GPT-4 เทียบคำตอบคู่ ๆ ตัดสินว่าอันไหนดีกว่าในมิติ
comprehensiveness/diversity/empowerment) ไม่ได้ใช้ paired t-test/Wilcoxon กับคะแนน
ตัวเลขแบบไฟล์นี้เลย จึงเปลี่ยนไปอ้างอิง Smucker et al. (2007) แทน เพราะตรงกับวิธี
ที่ไฟล์นี้ใช้จริง 100%)

⚠️ Multiple comparisons: ไฟล์นี้ทดสอบสถิติหลายครั้งในการรันครั้งเดียว (3 metric ตอน
เรียกแบบภาพรวม, มากถึง 3 x จำนวนกลุ่มคำถามตอนใช้ --by-type) ยิ่งทดสอบหลายครั้ง
ยิ่งเสี่ยงเจอนัยสำคัญปลอม (false discovery) จึงแก้ไขด้วย Benjamini-Hochberg (BH)
correction คำนวณ q-value (adjusted p-value) เพิ่มจาก p-value ดิบ:
    Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate:
    A Practical and Powerful Approach to Multiple Testing. Journal of the Royal
    Statistical Society: Series B, 57(1), 289-300.
แก้แยก "ครอบครัว" การทดสอบระหว่าง t-test กับ Wilcoxon (คนละสมมติฐาน ไม่ควรปนกัน)
ให้ดู q-value เป็นหลักตอนสรุปว่า "มีนัยสำคัญจริง" ไม่ใช่ p-value ดิบ

────────────────────────────────────────────────────────────────────────────
แก้ 2026-08-14 (บั๊ก q-value เพี้ยน + เพิ่มโหมด planned):

  บั๊กเดิม: เมื่อ KG ไม่เปลี่ยนคำตอบของกลุ่มคำถามหนึ่งเลย (ผลต่างทุกคู่ = 0
  เช่นคำถามทั่วไปที่ KG ไม่ทำงาน) stats.ttest_rel() จะคืน t_p = "nan" (ไม่ใช่ None)
  แล้ว nan เล็ดลอดเข้า _bh_correct() เพราะเดิมกรองแค่ None → sorted() ด้วย nan ให้
  ลำดับที่ไม่นิยาม + min(running_min, nan) เพี้ยนตามลำดับ argument → q-value ปลอม
  กระจายไปทุก cell (เห็นเป็น q=0.0203 ซ้ำ ๆ ทั้งที่ p ดิบ = 0.57 หรือ nan)
  ซึ่งเป็นไปไม่ได้ทางคณิตศาสตร์ (BH ต้องได้ q >= p เสมอ)

  แก้ 3 จุด:
    1) paired_compare(): ตรวจ "ผลต่างทุกคู่ = 0" (zero-variance) ที่ต้นทาง ถ้าใช่
       ทำเครื่องหมาย zero_variance=True และไม่เรียก t-test/Wilcoxon เลย (ไม่มีอะไร
       ให้ทดสอบ) — กันทั้ง nan และ RuntimeWarning จาก scipy
    2) paired_compare(): เผื่อกรณี t-test/Wilcoxon คืน nan ด้วยเหตุอื่น → แปลงเป็น
       None ทันที ไม่ปล่อยให้ nan ไหลต่อ
    3) _bh_correct(): กรองทั้ง None และ nan ออกจากครอบครัว BH (safety net ชั้นสอง)
    + เพิ่ม assert q >= p กันบั๊กชนิดนี้ไม่ให้กลับมาเงียบ ๆ อีก

  เพิ่มโหมด --planned <type>: correct BH เฉพาะภายใน 3 metrics ของกลุ่มคำถามที่เป็น
  "สมมติฐานหลักที่ตั้งไว้ล่วงหน้า" (เช่น multi_hop_kg ที่ KG ถูกออกแบบมาให้ช่วย)
  แยกออกจากการทดสอบ exploratory กลุ่มอื่น — เพราะการเอา planned hypothesis ไป
  correct รวมกับ exploratory อีกหลายสิบตัวเป็นการลงโทษที่เข้มเกินไป (over-conservative)
────────────────────────────────────────────────────────────────────────────

ใช้ (รันจาก root ของ repo):
    python -m src.eval.compare_stats src/eval/results/baseline_results.json src/eval/results/kg_results.json
    python -m src.eval.compare_stats <baseline.json> <kg.json> --by-type
    python -m src.eval.compare_stats <baseline.json> <kg.json> --planned multi_hop_kg

ข้อกำหนด: ทั้ง 2 ไฟล์ต้องมาจากการรัน eval_dataset.json ชุดเดียวกัน โดย
    baseline_results.json = RAG-only (CSIT_ENABLE_KG=0, รันด้วย run_baseline_eval.py)
    kg_results.json       = RAG+KG   (CSIT_ENABLE_KG=1, รันด้วย run_kg_eval.py)

การจับคู่ใช้ฟิลด์ "id" ของคำถาม ไม่ใช่ตำแหน่งในลิสต์ — ข้อที่มีอยู่แค่ไฟล์เดียว
จะถูกตัดออกจากการเทียบพร้อมแจ้งเตือน (ดู align_by_id)
"""

import sys
import json
import math
from pathlib import Path

try:
    from scipy import stats
except ImportError:
    print("❌ ต้องติดตั้ง scipy ก่อน: pip install scipy --break-system-packages")
    sys.exit(1)


def load_results(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_score(item: dict, metric_path: list[str]):
    """เดินตาม path เช่น ["ragas","faithfulness","score"] — คืน None ถ้าไม่มี"""
    val = item
    for key in metric_path:
        val = val.get(key) if isinstance(val, dict) else None
        if val is None:
            return None
    return val


def align_by_id(a_data: list[dict], b_data: list[dict]) -> list[tuple]:
    """จับคู่ผลลัพธ์ 2 ไฟล์ด้วย "id" ของคำถาม — คืน [(id, a_item, b_item), ...]
    เรียงตาม id

    (แก้ 2026-07-23: เดิมจับคู่ด้วย "ตำแหน่งในลิสต์" ซึ่งอันตรายมาก เพราะ
    run_baseline_eval.py มี auto-resume และ "ข้ามคำถามที่ตอบไม่สำเร็จ"
    (continue) ได้ ทำให้ 2 ไฟล์อาจมีจำนวน/ลำดับข้อไม่ตรงกัน แล้ว paired test
    จะจับคู่ผิดคำถามแบบเงียบ ๆ ผลสถิติที่ได้จะไม่มีความหมายเลยโดยไม่มีอะไรเตือน)
    """
    a_map = {item.get("id"): item for item in a_data if item.get("id") is not None}
    b_map = {item.get("id"): item for item in b_data if item.get("id") is not None}

    common = sorted(set(a_map) & set(b_map))
    only_a = sorted(set(a_map) - set(b_map))
    only_b = sorted(set(b_map) - set(a_map))

    if only_a or only_b:
        print("⚠️  สองไฟล์มีคำถามไม่ตรงกัน — จะเทียบเฉพาะข้อที่มีครบทั้งคู่")
        if only_a:
            print(f"    มีเฉพาะในไฟล์ A ({len(only_a)} ข้อ): {only_a}")
        if only_b:
            print(f"    มีเฉพาะในไฟล์ B ({len(only_b)} ข้อ): {only_b}")
        print()

    if not common:
        print("❌ ไม่มีคำถามที่ตรงกันเลยระหว่าง 2 ไฟล์ — เทียบไม่ได้")
        sys.exit(1)

    return [(qid, a_map[qid], b_map[qid]) for qid in common]


def _clean_p(p):
    """คืน None ถ้า p เป็น None หรือ nan — ไม่งั้นคืน p ตามเดิม (แปลงเป็น float)"""
    if p is None:
        return None
    p = float(p)
    return None if math.isnan(p) else p


def paired_compare(name: str, a_scores: list, b_scores: list) -> dict:
    """คำนวณ paired t-test + Wilcoxon signed-rank สำหรับ 1 metric — คืนค่าเป็น dict
    แทนการ print ตรง ๆ (ต่างจากเดิม) เพื่อให้ผู้เรียกเก็บ p-value ของหลายการทดสอบ
    ไปทำ Benjamini-Hochberg correction รวมกันได้ก่อนค่อยแสดงผลจริง

    (แก้ 2026-08-14) ตรวจ zero-variance ที่ต้นทาง: ถ้าผลต่างทุกคู่ = 0 (KG ไม่เปลี่ยน
    คำตอบกลุ่มนี้เลย) จะไม่เรียก t-test/Wilcoxon เพราะไม่มีอะไรให้ทดสอบ และ scipy
    จะคืน nan + ขึ้น RuntimeWarning — ทำเครื่องหมาย zero_variance=True แทน
    """
    pairs = [(a, b) for a, b in zip(a_scores, b_scores) if a is not None and b is not None]
    if len(pairs) < 3:
        return {"name": name, "n": len(pairs), "insufficient": True, "zero_variance": False}

    a = [p[0] for p in pairs]
    b = [p[1] for p in pairs]
    mean_a, mean_b = sum(a) / len(a), sum(b) / len(b)

    # ── ตรวจ zero-variance: ผลต่างทุกคู่ = 0 → ไม่มีอะไรให้ทดสอบ ──
    diffs = [x - y for x, y in zip(a, b)]
    if all(abs(d) < 1e-12 for d in diffs):
        return {
            "name": name, "n": len(pairs), "insufficient": False, "zero_variance": True,
            "mean_a": mean_a, "mean_b": mean_b,
            "t_stat": None, "t_p": None, "w_stat": None, "w_p": None,
        }

    # paired t-test (เผื่อ nan ด้วยเหตุอื่น → แปลงเป็น None ทันที ไม่ปล่อยให้ไหลต่อ)
    t_stat, t_p = stats.ttest_rel(a, b)
    t_p = _clean_p(t_p)
    if t_p is None:
        t_stat = None

    # Wilcoxon signed-rank
    try:
        w_stat, w_p = stats.wilcoxon(a, b)
        w_p = _clean_p(w_p)
        if w_p is None:
            w_stat = None
    except ValueError:
        # Wilcoxon พังถ้าผลต่างทุกคู่เป็น 0 หมด (ดักด้วย zero-variance ข้างบนแล้ว
        # แต่คงไว้กันเหนียวเผื่อ scipy บางเวอร์ชัน raise ก่อนถึงตรงนี้)
        w_stat, w_p = None, None

    return {
        "name": name,
        "n": len(pairs),
        "insufficient": False,
        "zero_variance": False,
        "mean_a": mean_a,
        "mean_b": mean_b,
        "t_stat": t_stat,
        "t_p": t_p,
        "w_stat": w_stat,
        "w_p": w_p,
    }


def _bh_correct(p_values: list) -> list:
    """Benjamini-Hochberg correction — คืน q-value (adjusted p-value) เรียงตรงตำแหน่ง
    เดิมกับ p_values ที่ส่งเข้ามา ค่า None หรือ nan (เช่น Wilcoxon ที่ข้ามเพราะผลต่าง
    เท่ากันหมด หรือ t-test ที่เจอ zero-variance) จะไม่ถูกนับรวมในการ correct และคืน
    เป็น None เหมือนเดิม

    (แก้ 2026-08-14) เดิมกรองแค่ None → nan เล็ดลอดเข้ามาทำให้ sort/min เพี้ยนทั้งชุด
    ตอนนี้กรองทั้ง None และ nan และมี assert q >= p กันบั๊กชนิดนี้กลับมาเงียบ ๆ

    ขั้นตอน (Benjamini & Hochberg, 1995):
    1. เรียง p-value จากน้อยไปมาก อันดับ i = 1..m
    2. q_(i) เริ่มต้น = p_(i) * m / i
    3. บังคับ monotonicity โดยเดินจากอันดับมากสุดย้อนกลับมาอันดับ 1 แล้วเก็บค่า
       ต่ำสุดสะสม (เพราะ q ต้องไม่ลดลงเมื่อ p มากขึ้น)
    4. ตัด cap ที่ 1.0
    """
    idx_p = [
        (i, float(p))
        for i, p in enumerate(p_values)
        if p is not None and not math.isnan(float(p))
    ]
    if not idx_p:
        return [None] * len(p_values)

    m = len(idx_p)
    ranked = sorted(idx_p, key=lambda t: t[1])  # (original_index, p) เรียงจาก p น้อย->มาก

    raw_q = [p * m / (rank + 1) for rank, (_, p) in enumerate(ranked)]

    adjusted = [0.0] * m
    running_min = 1.0
    for rank in range(m - 1, -1, -1):
        running_min = min(running_min, raw_q[rank])
        adjusted[rank] = running_min

    result = [None] * len(p_values)
    for (orig_idx, p), q in zip(ranked, adjusted):
        q_capped = min(q, 1.0)
        # BH ต้องได้ q >= p เสมอ — ถ้าไม่ใช่ แปลว่ามีบั๊กในการคำนวณ
        assert q_capped >= p - 1e-9, f"BH ผิดพลาด: q={q_capped} < p={p} (idx={orig_idx})"
        result[orig_idx] = q_capped
    return result


def _print_result(r: dict, t_q: float | None = None, w_q: float | None = None) -> None:
    """แสดงผล 1 การเปรียบเทียบ — ถ้ามี q-value (หลัง BH correction) ส่งมาด้วย
    จะโชว์คู่กับ p-value ดิบ ให้เห็นทั้งสองค่า
    """
    if r["insufficient"]:
        print(f"\n[{r['name']}] ข้อมูลไม่พอสำหรับทดสอบสถิติ (n={r['n']}, ต้องการอย่างน้อย 3)")
        return

    print(f"\n=== {r['name']} (n={r['n']}) ===")
    print(f"  ค่าเฉลี่ยระบบ A (baseline): {r['mean_a']:.4f}")
    print(f"  ค่าเฉลี่ยระบบ B (เทียบ):     {r['mean_b']:.4f}")
    print(f"  ผลต่าง (B - A):            {r['mean_b'] - r['mean_a']:+.4f}")

    # (แก้ 2026-08-14) กลุ่มที่ KG ไม่เปลี่ยนคำตอบเลย → ไม่ทดสอบสถิติ
    if r.get("zero_variance"):
        print("  ผลต่างทุกคู่ = 0 (ระบบให้คะแนนเท่ากันทุกข้อ) — ไม่ต้องทดสอบสถิติ")
        return

    sig_t_raw = " ← p<.05 (ดิบ)" if r["t_p"] < 0.05 else ""
    t_disp = "±inf (ผลต่างคงที่ทุกคู่)" if (r["t_stat"] is not None and math.isinf(r["t_stat"])) else f"{r['t_stat']:.4f}"
    print(f"  paired t-test:        t={t_disp}, p={r['t_p']:.4f}{sig_t_raw}")
    if t_q is not None:
        sig_t_q = " ← ยังมีนัยสำคัญหลังแก้ multiple comparisons (q<.05)" if t_q < 0.05 else " (ไม่ผ่านหลังแก้ multiple comparisons)"
        print(f"                        q={t_q:.4f}{sig_t_q}")

    if r["w_p"] is not None:
        sig_w_raw = " ← p<.05 (ดิบ)" if r["w_p"] < 0.05 else ""
        print(f"  Wilcoxon signed-rank: W={r['w_stat']:.4f}, p={r['w_p']:.4f}{sig_w_raw}")
        if w_q is not None:
            sig_w_q = " ← ยังมีนัยสำคัญหลังแก้ multiple comparisons (q<.05)" if w_q < 0.05 else " (ไม่ผ่านหลังแก้ multiple comparisons)"
            print(f"                        q={w_q:.4f}{sig_w_q}")
    else:
        print("  Wilcoxon signed-rank: ข้ามไป (ผลต่างทุกคู่เท่ากันหมด)")


def _tests_entering_bh(valid: list[dict]) -> tuple[int, int]:
    """นับจำนวนการทดสอบที่ "เข้าครอบครัว BH จริง" (p ไม่ใช่ None/nan)
    แยก t-test กับ Wilcoxon — ใช้แสดงจำนวนที่ถูกต้อง (ไม่รวม zero-variance)
    """
    n_t = sum(1 for r in valid if _clean_p(r.get("t_p")) is not None)
    n_w = sum(1 for r in valid if _clean_p(r.get("w_p")) is not None)
    return n_t, n_w


def _report_with_correction(results: list[dict]) -> None:
    """แสดงผลของหลายการทดสอบพร้อมกัน + คำนวณ q-value ด้วย BH correction
    แก้แยก 'ครอบครัว' ระหว่าง t-test กับ Wilcoxon (คนละสมมติฐานทางสถิติ ไม่ปนกัน)
    """
    valid = [r for r in results if not r["insufficient"]]
    t_q_list = _bh_correct([r.get("t_p") for r in valid])
    w_q_list = _bh_correct([r.get("w_p") for r in valid])

    vi = 0
    for r in results:
        if r["insufficient"]:
            _print_result(r)
            continue
        _print_result(r, t_q_list[vi], w_q_list[vi])
        vi += 1

    n_t, n_w = _tests_entering_bh(valid)
    if n_t + n_w > 0:
        print(f"\n  ℹ️  แก้ปัญหา multiple comparisons ด้วย Benjamini-Hochberg correction")
        print(f"     (t-test {n_t} ครั้ง, Wilcoxon {n_w} ครั้ง — ดู q-value เป็นหลัก ไม่ใช่ p-value ดิบ)")
        print(f"     * กลุ่มที่ผลต่างทุกคู่ = 0 ไม่นับเข้าการทดสอบ (KG ไม่เปลี่ยนคำตอบ)")


METRICS = {
    "Faithfulness": ["ragas", "faithfulness", "score"],
    "Answer Relevance": ["ragas", "answer_relevance", "score"],
    "Context Relevance": ["ragas", "context_relevance", "score"],
}


def split_by_type(baseline_path: str, kg_path: str, type_key: str = "type"):
    """แยกผลตามกลุ่มคำถาม — ดูว่า KG ช่วยเฉพาะกลุ่ม multi-hop จริงไหม

    ⚠️ โหมดนี้ทดสอบสถิติ (จำนวนกลุ่มคำถาม x 3 metric) ครั้ง พร้อมกัน ความเสี่ยงเจอ
    นัยสำคัญปลอมสูงกว่าโหมดภาพรวมมาก จึงรวม BH correction ข้าม "ทุกกลุ่มคำถาม x
    ทุก metric" เป็นชุดเดียวกัน ก่อนสรุปผล

    หมายเหตุ: การ correct รวมทุกกลุ่มแบบนี้เป็น exploratory ที่ conservative มาก
    ถ้ามีสมมติฐานหลักที่ตั้งไว้ล่วงหน้า (เช่น multi_hop_kg) แนะนำดูโหมด --planned
    ควบคู่ด้วย (correct เฉพาะภายในกลุ่มนั้น ไม่ถูกกลุ่ม exploratory เจือจาง)
    """
    pairs = align_by_id(load_results(baseline_path), load_results(kg_path))
    print(f"🔗 จับคู่คำถามด้วย id ได้ {len(pairs)} ข้อ\n")

    types = sorted({a.get(type_key) for _, a, _ in pairs if a.get(type_key)})

    all_entries = []  # list ของ (type, result_dict) เรียงตามลำดับที่จะแสดงผล
    for t in types:
        subset = [(a, b) for _, a, b in pairs if a.get(type_key) == t]
        for name, path_keys in METRICS.items():
            a_sub = [_get_score(a, path_keys) for a, _ in subset]
            b_sub = [_get_score(b, path_keys) for _, b in subset]
            r = paired_compare(name, a_sub, b_sub)
            all_entries.append((t, r))

    valid = [r for _, r in all_entries if not r["insufficient"]]
    t_q_list = _bh_correct([r.get("t_p") for r in valid])
    w_q_list = _bh_correct([r.get("w_p") for r in valid])

    vi = 0
    current_type = None
    for t, r in all_entries:
        if t != current_type:
            print(f"\n{'='*60}\nกลุ่มคำถาม: {t}\n{'='*60}")
            current_type = t
        if r["insufficient"]:
            _print_result(r)
            continue
        _print_result(r, t_q_list[vi], w_q_list[vi])
        vi += 1

    n_t, n_w = _tests_entering_bh(valid)
    if n_t + n_w > 0:
        print(f"\nℹ️  แก้ปัญหา multiple comparisons ด้วย Benjamini-Hochberg correction")
        print(f"   ครอบคลุม {n_t} การทดสอบ t-test และ {n_w} การทดสอบ Wilcoxon")
        print(f"   (ทุกกลุ่มคำถาม x ทุก metric ที่มีผลต่างจริง รวมกันเป็นชุดเดียว) — ดู q-value เป็นหลัก")
        print(f"   * กลุ่มที่ผลต่างทุกคู่ = 0 ไม่นับเข้าการทดสอบ")
        print(f"\n💡 สำหรับสมมติฐานหลักที่ตั้งไว้ล่วงหน้า ดูโหมด planned เพิ่ม:")
        print(f"   python -m src.eval.compare_stats {baseline_path} {kg_path} --planned multi_hop_kg")


def planned_family(baseline_path: str, kg_path: str, target_type: str, type_key: str = "type"):
    """โหมด planned comparison — correct BH เฉพาะภายใน 3 metrics ของกลุ่มคำถามเดียว
    ที่เป็นสมมติฐานหลักตั้งไว้ล่วงหน้า (เช่น multi_hop_kg ที่ KG ถูกออกแบบมาให้ช่วย)

    เหตุผล: การเอา planned hypothesis ไป correct รวมกับการทดสอบ exploratory อีก
    หลายสิบตัว (โหมด --by-type) เป็นการลงโทษที่เข้มเกินไป (over-conservative)
    มาตรฐานสถิติแยกการทดสอบที่ตั้งไว้ล่วงหน้าออกจาก exploratory และ correct แยกครอบครัว
    """
    pairs = align_by_id(load_results(baseline_path), load_results(kg_path))
    subset = [(a, b) for _, a, b in pairs if a.get(type_key) == target_type]

    print(f"🎯 planned comparison: กลุ่ม '{target_type}'  (n={len(subset)} ข้อ)")
    print(f"   correct BH เฉพาะภายใน 3 metrics ของกลุ่มนี้ (แยกจาก exploratory กลุ่มอื่น)\n")

    if not subset:
        avail = sorted({a.get(type_key) for _, a, _ in pairs if a.get(type_key)})
        print(f"❌ ไม่พบคำถาม type='{target_type}'")
        print(f"   type ที่มีให้เลือก: {avail}")
        sys.exit(1)

    results = []
    for name, path_keys in METRICS.items():
        a_sub = [_get_score(a, path_keys) for a, _ in subset]
        b_sub = [_get_score(b, path_keys) for _, b in subset]
        results.append(paired_compare(name, a_sub, b_sub))

    _report_with_correction(results)


def main():
    if len(sys.argv) < 3:
        print("usage: python -m src.eval.compare_stats <baseline.json> <kg.json> "
              "[--by-type | --planned <type>]")
        sys.exit(1)

    baseline_path, kg_path = sys.argv[1], sys.argv[2]
    if not Path(baseline_path).exists() or not Path(kg_path).exists():
        print("❌ ไม่พบไฟล์ผลลัพธ์ — ต้องรัน run_baseline_eval.py และ run_kg_eval.py ก่อน")
        sys.exit(1)

    if "--planned" in sys.argv:
        i = sys.argv.index("--planned")
        if i + 1 >= len(sys.argv):
            print("❌ --planned ต้องตามด้วยชื่อ type เช่น --planned multi_hop_kg")
            sys.exit(1)
        planned_family(baseline_path, kg_path, sys.argv[i + 1])
        return

    if "--by-type" in sys.argv:
        split_by_type(baseline_path, kg_path)
        return

    print("=" * 60)
    print("เปรียบเทียบภาพรวมทั้งชุดทดสอบ")
    print("=" * 60)

    pairs = align_by_id(load_results(baseline_path), load_results(kg_path))
    print(f"🔗 จับคู่คำถามด้วย id ได้ {len(pairs)} ข้อ")

    results = []
    for name, path_keys in METRICS.items():
        a = [_get_score(item_a, path_keys) for _, item_a, _ in pairs]
        b = [_get_score(item_b, path_keys) for _, _, item_b in pairs]
        results.append(paired_compare(name, a, b))

    _report_with_correction(results)

    print("\n💡 อยากดูแยกตามกลุ่มคำถาม รันเพิ่ม:")
    print(f"   python -m src.eval.compare_stats {baseline_path} {kg_path} --by-type")


if __name__ == "__main__":
    main()
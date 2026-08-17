"""
Seed ข้อมูลวุฒิการศึกษาแบบ structured เข้าตาราง instructor_education

ที่มาของข้อมูล: knowledge_base/staff_csit.md (คัดลอกมาตรงตัว ไม่ได้เดาเพิ่ม)
รันครั้งเดียวหลังอัปเดต sqlite_db.py:

    python -m src.database.seed_education

รันซ้ำได้ปลอดภัย (idempotent) — set_instructor_education() ลบแถวเดิมของ
อาจารย์คนนั้นทิ้งก่อนใส่ชุดใหม่ทุกครั้ง

⚠️ ข้อมูลนี้แก้ปัญหาที่พบใน Session 8: KG ตอบ "อาจารย์จบเอกต่างประเทศ" ได้แค่
   7 คนจาก 9 คน เพราะ ผศ.ดร.วินัย และ ดร.เอกสิทธิ์ ไม่เคยถูก sync เข้า SQLite
   (Session 6 sync ไปแค่ 8 คน ไม่ใช่ 15 คนที่มีวุฒิ ดร.)
"""

from src.database.sqlite_db import (
    init_database,
    set_instructor_education,
    education_coverage,
    find_foreign_phd_instructors,
    find_thai_phd_instructors,
)

TH = "ไทย"

# key = รหัสบุคลากร (staff_id) — UNIQUE จึงแม่นกว่าชื่อ
# value = (ชื่อสำหรับ fallback ถ้าหา staff_id ไม่เจอ, [ใบปริญญาเรียงจากสูงไปต่ำ])
EDUCATION_DATA: dict[str, tuple[str, list[dict]]] = {
    # ── จบปริญญาเอกต่างประเทศ (9 ท่าน) ──────────────────────────────
    "F05003": ("จักรกฤษณ์", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Computer Science",
         "institution": "University of Liverpool", "country": "UK"},
        {"level": "master", "degree": "M.Sc.", "field": "Computer Science",
         "institution": "University of Newcastle Upon Tyne", "country": "UK"},
        {"level": "bachelor", "degree": "วท.บ.", "field": "คณิตศาสตร์",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
    ]),
    "F05018": ("ไกรศักดิ์", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Electronic Engineering",
         "institution": "Queen Mary University", "country": "UK"},
        {"level": "master", "degree": "วท.ม.", "field": "เทคโนโลยีสารสนเทศ",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยเชียงใหม่", "country": TH},
    ]),
    "F05015": ("จรัสศรี", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Computer Science",
         "institution": "Warwick University", "country": "UK"},
        {"level": "master", "degree": "M.Sc.",
         "field": "Parallel Computers and Computation",
         "institution": "Warwick University", "country": "UK"},
        {"level": "bachelor", "degree": "B.Eng.", "field": "Computing",
         "institution": "Imperial College", "country": "UK"},
    ]),
    "F05010": ("จันทร์จิรา", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Information Technology",
         "institution": "Murdoch University", "country": "Australia"},
        {"level": "master", "degree": "M.Sc.", "field": "Computer Science",
         "institution": "University of Wollongong", "country": "Australia"},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
    ]),
    "F05012": ("อนงค์พร", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Computer Science",
         "institution": "University of Birmingham", "country": "UK"},
        {"level": "master", "degree": "วท.ม.", "field": "วิทยาศาสตร์คอมพิวเตอร์",
         "institution": "จุฬาลงกรณ์มหาวิทยาลัย", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยอัสสัมชัญ", "country": TH},
    ]),
    "F05016": ("วินัย", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Computer Science",
         "institution": "University of Newcastle Upon Tyne", "country": "UK"},
        {"level": "master", "degree": "M.Sc.",
         "field": "System Design for Internet Applications",
         "institution": "University of Newcastle Upon Tyne", "country": "UK"},
        # ⚠️ AIT อยู่ในไทย แม้ชื่อเป็นภาษาอังกฤษล้วน
        {"level": "master", "degree": "M.Sc.", "field": "Computer Science",
         "institution": "Asian Institute of Technology", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
    ]),
    "F05019": ("สัญญา", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Computer Systems",
         "institution": "University of Technology Sydney", "country": "Australia"},
        {"level": "master", "degree": "วท.ม.", "field": "เทคโนโลยีสารสนเทศ",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาศาสตร์คอมพิวเตอร์",
         "institution": "มหาวิทยาลัยราชภัฏพิบูลสงคราม", "country": TH},
    ]),
    "F05021": ("วันสุรีย์", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "Electrical Engineering",
         "institution": "University of Hawaii at Manoa", "country": "USA"},
        {"level": "master", "degree": "M.Sc.",
         "field": "Electrical and Computer Engineering",
         "institution": "Carnegie Mellon University", "country": "USA"},
        {"level": "bachelor", "degree": "B.Eng.",
         "field": "Electrical and Computer Engineering",
         "institution": "Carnegie Mellon University", "country": "USA"},
    ]),
    "F05007": ("เอกสิทธิ์", [
        {"level": "doctorate", "degree": "Ph.D.",
         "field": "Computer Science and Engineering",
         "institution": "University of Nevada Reno", "country": "USA"},
        {"level": "master", "degree": "M.Sc.",
         "field": "Electrical and Computer Engineering",
         "institution": "Carnegie Mellon University", "country": "USA"},
        {"level": "bachelor", "degree": "วศ.บ.", "field": "วิศวกรรมคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี", "country": TH},
    ]),

    # ── จบปริญญาเอกในประเทศไทย (6 ท่าน) ──────────────────────────────
    # ⚠️ กลุ่มนี้คือกับดัก false positive: 2 ท่านล่างเขียนวุฒิว่า "Ph.D."
    #    แต่จบในไทย ถ้าใช้ heuristic ที่ดูแค่คำว่า Ph.D. จะถูกนับผิดทันที
    "F05014": ("เกรียงศักดิ์", [
        {"level": "doctorate", "degree": "วศ.ด.", "field": "วิศวกรรมไฟฟ้า",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "country": TH},
        {"level": "master", "degree": "วศ.ม.", "field": "วิศวกรรมไฟฟ้า",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "ฟิสิกส์",
         "institution": "มหาวิทยาลัยเชียงใหม่", "country": TH},
    ]),
    "F05020": ("สุธาสินี", [
        {"level": "doctorate", "degree": "วศ.ด.", "field": "วิศวกรรมคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยเกษตรศาสตร์", "country": TH},
        {"level": "master", "degree": "วท.ม.", "field": "เทคโนโลยีสารสนเทศ",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าพระนครเหนือ", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยเชียงใหม่", "country": TH},
    ]),
    "F05024": ("ธนะธร", [
        {"level": "doctorate", "degree": "วศ.ด.", "field": "วิศวกรรมคอมพิวเตอร์",
         "institution": "จุฬาลงกรณ์มหาวิทยาลัย", "country": TH},
        {"level": "master", "degree": "วศ.ม.", "field": "วิศวกรรมคอมพิวเตอร์",
         "institution": "จุฬาลงกรณ์มหาวิทยาลัย", "country": TH},
        {"level": "bachelor", "degree": "วศ.บ.", "field": "วิศวกรรมคอมพิวเตอร์",
         "institution": "จุฬาลงกรณ์มหาวิทยาลัย", "country": TH},
    ]),
    "F05026": ("ณัฐพล", [
        {"level": "doctorate", "degree": "ปร.ด.", "field": "เทคโนโลยีสารสนเทศ",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
        {"level": "master", "degree": "วท.ม.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
    ]),
    "F05027": ("พัชรี", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "เศรษฐศาสตร์",
         "institution": "จุฬาลงกรณ์มหาวิทยาลัย", "country": TH},
    ]),
    "F01085": ("ลิมปพัทธ์", [
        {"level": "doctorate", "degree": "Ph.D.", "field": "คณิตศาสตร์",
         "institution": "มหาวิทยาลัยเชียงใหม่", "country": TH},
        {"level": "master", "degree": "M.Sc.", "field": "คณิตศาสตร์",
         "institution": "มหาวิทยาลัยเชียงใหม่", "country": TH},
        {"level": "bachelor", "degree": "B.Sc.", "field": "คณิตศาสตร์",
         "institution": "มหาวิทยาลัยเชียงใหม่", "country": TH},
    ]),

    # ── ยังไม่มีวุฒิปริญญาเอก (5 ท่าน) ────────────────────────────────
    "F05013": ("เทวิน", [
        {"level": "bachelor", "degree": "วศ.บ.", "field": "วิศวกรรมไฟฟ้า",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "สถิติ",
         "institution": "มหาวิทยาลัยเชียงใหม่", "country": TH},
    ]),
    "F05008": ("ณัฐวดี", [
        {"level": "master", "degree": "วท.ม.", "field": "เทคโนโลยีสารสนเทศ",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
    ]),
    "F05011": ("อดิเรก", [
        {"level": "master", "degree": "M.Sc.", "field": "Computing",
         "institution": "Griffith University", "country": "Australia"},
        {"level": "bachelor", "degree": "วท.บ.", "field": "สัตวศาสตร์",
         "institution": "สถาบันเทคโนโลยีราชมงคลบางพระ", "country": TH},
    ]),
    "F05009": ("วุฒิพงษ์", [
        {"level": "master", "degree": "วท.ม.",
         "field": "วิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
         "institution": "จุฬาลงกรณ์มหาวิทยาลัย", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "วิทยาการคอมพิวเตอร์",
         "institution": "มหาวิทยาลัยนเรศวร", "country": TH},
    ]),
    "F05022": ("พิเศษพงศ์", [
        {"level": "master", "degree": "วท.ม.",
         "field": "วิทยาการคอมพิวเตอร์และเทคโนโลยีสารสนเทศ",
         "institution": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง", "country": TH},
        {"level": "bachelor", "degree": "วท.บ.", "field": "สถิติ",
         "institution": "มหาวิทยาลัยศรีนครินทรวิโรฒ", "country": TH},
    ]),
}

# จำนวนที่คาดหวัง — นับด้วยมือจาก staff_csit.md ใช้เป็น assertion กันข้อมูลเพี้ยน
EXPECTED_FOREIGN_PHD = 9
EXPECTED_THAI_PHD = 6


def seed(verbose: bool = True) -> tuple[int, list[str]]:
    """เขียนข้อมูลลง instructor_education — คืน (จำนวนที่สำเร็จ, รายชื่อที่หาไม่เจอ)"""
    init_database()
    ok = 0
    not_found = []
    for staff_id, (name, degrees) in EDUCATION_DATA.items():
        if set_instructor_education(staff_id, degrees):
            ok += 1
            if verbose:
                print(f"   ✅ {name} ({staff_id}) — {len(degrees)} ใบ")
        elif set_instructor_education(name, degrees):
            ok += 1
            if verbose:
                print(f"   ✅ {name} (จับด้วยชื่อ — ไม่พบ staff_id {staff_id})")
        else:
            not_found.append(f"{name} ({staff_id})")
            if verbose:
                print(f"   ❌ ไม่พบอาจารย์: {name} ({staff_id})")
    return ok, not_found


def main():
    print("🌱 กำลัง seed ข้อมูลวุฒิการศึกษาแบบ structured...\n")
    ok, not_found = seed()

    print(f"\n📊 บันทึกสำเร็จ {ok}/{len(EDUCATION_DATA)} ท่าน")
    if not_found:
        print("⚠️  หาไม่เจอในตาราง instructors (ต้องรัน ingest ก่อน):")
        for n in not_found:
            print(f"      - {n}")

    cov = education_coverage()
    print(
        f"\n📈 ความครบของข้อมูล: {cov['with_education_rows']}/"
        f"{cov['total_instructors']} ท่านมีข้อมูลวุฒิแล้ว"
    )
    if cov["missing_education"]:
        print("   ยังไม่มีข้อมูลวุฒิ:")
        for inst in cov["missing_education"]:
            print(f"      - {inst['name']}")

    foreign = find_foreign_phd_instructors()
    thai = find_thai_phd_instructors()

    print(f"\n🌍 จบเอกต่างประเทศ: {len(foreign)} ท่าน")
    for inst in foreign:
        print(f"      - {inst.get('title_short') or ''} {inst['name']}")
    print(f"\n🇹🇭 จบเอกในไทย: {len(thai)} ท่าน")
    for inst in thai:
        print(f"      - {inst.get('title_short') or ''} {inst['name']}")

    print()
    if len(foreign) == EXPECTED_FOREIGN_PHD and len(thai) == EXPECTED_THAI_PHD:
        print(f"✅ ตรงกับที่คาดหวัง (ต่างประเทศ {EXPECTED_FOREIGN_PHD}, "
              f"ไทย {EXPECTED_THAI_PHD})")
    else:
        print(f"⚠️  ไม่ตรงกับที่คาดหวัง — ควรได้ต่างประเทศ {EXPECTED_FOREIGN_PHD} "
              f"และไทย {EXPECTED_THAI_PHD} ท่าน")
        print("   สาเหตุที่พบบ่อย: ตาราง instructors ยังไม่มีอาจารย์ครบ 20 ท่าน")


if __name__ == "__main__":
    main()
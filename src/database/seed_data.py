"""
Seed Data Script — ใส่ข้อมูลพื้นฐานลง SQLite
รันครั้งเดียวหลัง init_database()

รัน: python -m src.database.seed_data
"""

from src.database.sqlite_db import init_database, db_session


# ─── ข้อมูลอาจารย์ภาควิชา CSIT 20 ท่าน ─────────────
INSTRUCTORS = [
    # ─── รองศาสตราจารย์ ───
    {
        "name": "จักรกฤษณ์ เสน่ห์ นมะหุต",
        "title": "รองศาสตราจารย์",
        "title_short": "รศ.ดร.",
        "staff_id": "F05003",
        "email": "chakkrits@nu.ac.th",
        "office": "SC2-301",
        "specialization": None,
    },
    {
        "name": "ไกรศักดิ์ เกษร",
        "title": "รองศาสตราจารย์",
        "title_short": "รศ.ดร.",
        "staff_id": "F05018",
        "email": "kraisakk@nu.ac.th",
        "office": "SC2-401",
        "specialization": None,
    },
    {
        "name": "จรัสศรี รุ่งรัตนาอุบล",
        "title": "รองศาสตราจารย์",
        "title_short": "รศ.ดร.",
        "staff_id": "F05015",
        "email": "jaratsrir@nu.ac.th",
        "office": "SC2-317",
        "specialization": None,
    },
    {
        "name": "จันทร์จิรา พยัคฆ์เพศ",
        "title": "รองศาสตราจารย์",
        "title_short": "รศ.ดร.",
        "staff_id": "F05010",
        "email": "janjirap@nu.ac.th",
        "office": "SC2-217",
        "specialization": None,
    },
    
    # ─── ผู้ช่วยศาสตราจารย์ ───
    {
        "name": "อนงค์พร ไศลวรากุล",
        "title": "ผู้ช่วยศาสตราจารย์",
        "title_short": "ผศ.ดร.",
        "staff_id": "F05012",
        "email": "anongporns@nu.ac.th",
        "office": "SC2-406",
        "specialization": None,
    },
    {
        "name": "เกรียงศักดิ์ เตมีย์",
        "title": "ผู้ช่วยศาสตราจารย์",
        "title_short": "ผศ.ดร.",
        "staff_id": "F05014",
        "email": "kreangsakt@nu.ac.th",
        "office": "SC2-401",
        "specialization": "AI, NLP (ที่ปรึกษาวิทยานิพนธ์น้องซีที)",
    },
    {
        "name": "วินัย วงษ์ไทย",
        "title": "ผู้ช่วยศาสตราจารย์",
        "title_short": "ผศ.ดร.",
        "staff_id": "F05016",
        "email": "winaiw@nu.ac.th",
        "office": "SC2-417",
        "specialization": None,
    },
    {
        "name": "สุธาสินี จิตต์อนันต์",
        "title": "ผู้ช่วยศาสตราจารย์",
        "title_short": "ผศ.ดร.",
        "staff_id": "F05020",
        "email": "sutasineec@nu.ac.th",
        "office": "SC2-406",
        "specialization": None,
    },
    {
        "name": "สัญญา เครือหงษ์",
        "title": "ผู้ช่วยศาสตราจารย์",
        "title_short": "ผศ.ดร.",
        "staff_id": "F05019",
        "email": "sanyak@nu.ac.th",
        "office": "SC2-306",
        "specialization": "กรรมการประเมินวิทยานิพนธ์น้องซีที",
    },
    {
        "name": "ธนะธร พ่อค้า",
        "title": "ผู้ช่วยศาสตราจารย์",
        "title_short": "ผศ.ดร.",
        "staff_id": "F05024",
        "email": "thanathornp@nu.ac.th",
        "office": "SC2-417",
        "specialization": None,
    },
    {
        "name": "วันสุรีย์ มาศกรัม",
        "title": "ผู้ช่วยศาสตราจารย์",
        "title_short": "ผศ.ดร.",
        "staff_id": "F05021",
        "email": "wansureem@nu.ac.th",
        "office": "SC2-306",
        "specialization": None,
    },
    
    # ─── อาจารย์ ───
    {
        "name": "เอกสิทธิ์ เทียมแก้ว",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05007",
        "email": "ekkasitt@nu.ac.th",
        "office": "SC2-301",
        "specialization": None,
    },
    {
        "name": "ณัฐพล คุ้มใหญ่โต",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05026",
        "email": "nattaponk@nu.ac.th",
        "office": "SC2-417",
        "specialization": None,
    },
    {
        "name": "เทวิน ธนะวงษ์",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05013",
        "email": "tawint@nu.ac.th",
        "office": "SC2-406",
        "specialization": None,
    },
    {
        "name": "ณัฐวดี หงษ์บุญมี",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05008",
        "email": "nattavadeeho@nu.ac.th",
        "office": "SC2-317",
        "specialization": None,
    },
    {
        "name": "อดิเรก รุ่งรังษี",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05011",
        "email": "adirekr@nu.ac.th",
        "office": "SC2-401",
        "specialization": "กรรมการประเมินวิทยานิพนธ์น้องซีที",
    },
    {
        "name": "วุฒิพงษ์ เรือนทอง",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05009",
        "email": "wuttipongr@nu.ac.th",
        "office": "SC2-401",
        "specialization": None,
    },
    {
        "name": "พิเศษพงศ์ สุธาพันธ์",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05022",
        "email": "phisetphongs@nu.ac.th",
        "office": "SC2-306",
        "specialization": None,
    },
    {
        "name": "พัชรี ดุลนิมิตร",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F05027",
        "email": "patchareed@nu.ac.th",
        "office": "SC2-406",
        "specialization": None,
    },
    {
        "name": "ลิมปพัทธ์ บุษบัน",
        "title": "อาจารย์",
        "title_short": "อ.",
        "staff_id": "F01085",
        "email": "impapatb@nu.ac.th",
        "office": "SC2-301",
        "specialization": None,
    },
]


# ─── เจ้าหน้าที่ภาควิชา ─────────────────────────────
STAFF = [
    {
        "name": "ปทุมา แก้วแดง",
        "nickname": "พี่แมว",
        "position": "นักวิชาการพัสดุ",
        "phone": "055-963263",
        "email": "patumak@nu.ac.th",
        "office": "CSIT Department",
    },
    {
        "name": "ณัฐปกรณ์ ทูลแก้วธัญธร",
        "nickname": "พี่เฟิร์น",
        "position": "เจ้าหน้าที่บริหารงานทั่วไป",
        "phone": "055-963262",
        "email": "nutthapakornm@nu.ac.th",
        "office": "CSIT Department",
    },
    {
        "name": "ธราศักดิ์ ชุนกองฮอ",
        "nickname": "พี่โอ๊ต",
        "position": "นักวิชาการคอมพิวเตอร์",
        "phone": "055-963230",
        "email": "tharasukc@nu.ac.th",
        "office": "SC2-110",
    },
    {
        "name": "ยุทธพงษ์ คงถาวร",
        "nickname": "พี่ยุทธ",
        "position": "นายช่างเทคนิค",
        "phone": "055-963230",
        "email": "yuthapongk@nu.ac.th",
        "office": "SC2-110",
    },
]


# ─── คำร้อง NU Forms ─────────────────────────────────
NU_FORMS = [
    {"code": "NU1", "name_th": "ระเบียนประวัตินิสิต", "category": "ข้อมูลนิสิตใหม่",
     "purpose": "เก็บข้อมูลประวัตินิสิตใหม่ตอนรายงานตัว", "fee": None},
    {"code": "NU6", "name_th": "แบบขอเปลี่ยนแปลงการสอนรายวิชา", "category": "ลงทะเบียน",
     "purpose": "ใช้เมื่อต้องการสำรองที่นั่งในรายวิชาที่ไม่ได้สำรองไว้", "fee": None},
    {"code": "NU7", "name_th": "คำร้องขอคืนสภาพการเป็นนิสิต", "category": "ลงทะเบียน",
     "purpose": "ใช้เมื่อพ้นสภาพและต้องการกลับมาเป็นนิสิต", "fee": "1,000 บาท"},
    {"code": "NU8", "name_th": "คำร้องขอเพิ่มรายวิชาหลังกำหนด", "category": "ลงทะเบียน",
     "purpose": "ใช้เพิ่มรายวิชาหลังพ้น 2 สัปดาห์แรก", "fee": "100 บาท/สัปดาห์"},
    {"code": "NU9", "name_th": "คำร้องขอยื่นสำเร็จการศึกษาล่าช้ากว่ากำหนด", "category": "สำเร็จการศึกษา",
     "purpose": "ใช้เมื่อยื่นจบหลังพ้นกำหนด 4 สัปดาห์", "fee": "50 บาท/วันทำการ"},
    {"code": "NU11", "name_th": "แบบขอถอนรายวิชา (ติด W)", "category": "ลงทะเบียน",
     "purpose": "ใช้ถอนรายวิชาหลัง 2 สัปดาห์ (ต้องไม่เกินสัปดาห์ที่ 12)", "fee": None},
    {"code": "NU13", "name_th": "คำร้องขอย้ายคณะ/สาขาวิชา", "category": "ระเบียนประวัติ",
     "purpose": "ใช้ย้ายคณะหรือสาขาภายในมหาวิทยาลัย", "fee": None},
    {"code": "NU14", "name_th": "คำร้องขอเทียบโอนรายวิชา", "category": "ลงทะเบียน",
     "purpose": "ใช้เทียบโอนรายวิชาที่เคยเรียนมาแล้ว", "fee": "100 บาท/ครั้ง"},
    {"code": "NU15", "name_th": "คำร้องขอใบแสดงผลการเรียน (Transcript)", "category": "เอกสารสำคัญ",
     "purpose": "ขอ Transcript ไทย/อังกฤษ", "fee": None},
    {"code": "NU16", "name_th": "คำร้องขอเปลี่ยนชื่อ ชื่อสกุล ยศ", "category": "ระเบียนประวัติ",
     "purpose": "ใช้เมื่อเปลี่ยนชื่อ-สกุลหรือยศ", "fee": None},
    {"code": "NU17", "name_th": "คำร้องขอลาพักการศึกษา", "category": "ระเบียนประวัติ",
     "purpose": "ใช้ลาพักการศึกษา (ผู้ปกครองต้องเซ็น)", "fee": None},
    {"code": "NU18", "name_th": "คำร้องทั่วไป", "category": "ลงทะเบียน",
     "purpose": "ใช้สำหรับขอลงทะเบียนเกินหน่วยกิตที่กำหนด หรือกรณีอื่นๆ", "fee": None},
    {"code": "NU19", "name_th": "คำร้องขอลาออกจากการศึกษา", "category": "ระเบียนประวัติ",
     "purpose": "ใช้ลาออกจากการเป็นนิสิต (ผู้ปกครองต้องเซ็น)", "fee": None},
    {"code": "NU21", "name_th": "คำร้องขอใบรับรอง", "category": "เอกสารสำคัญ",
     "purpose": "ขอใบรับรองการเป็นนิสิต/กำลังเรียน/เรียนครบหลักสูตร", "fee": None},
    {"code": "NU25", "name_th": "แบบขอสำเร็จการศึกษา", "category": "สำเร็จการศึกษา",
     "purpose": "ยื่นในภาคที่คาดว่าจะจบ (ภายใน 4 สัปดาห์หลังเปิดเทอม)",
     "fee": "ป.ตรี 2,000 บาท / บัณฑิตศึกษา 2,500 บาท"},
    {"code": "NU33", "name_th": "แบบแก้ไขผลการเรียนรายวิชา", "category": "ประมวลผลข้อมูล",
     "purpose": "ใช้แก้อักษร I หรือ P", "fee": None},
]


# ─── ลิงก์สำคัญ ──────────────────────────────────────
IMPORTANT_LINKS = [
    {"title": "ระบบทะเบียนออนไลน์", "url": "https://www.reg.nu.ac.th",
     "category": "ทั่วไป", "description": "ลงทะเบียน เพิ่ม-ถอนวิชา ดูเกรด ขอเอกสาร"},
    {"title": "ปฏิทินการศึกษา", "url": "https://reg4.nu.ac.th/registrar/calendar.asp",
     "category": "ทั่วไป", "description": "ดูกำหนดการลงทะเบียน สอบ เปิด-ปิดเทอม"},
    {"title": "คู่มือนิสิตปริญญาตรี", "url": "https://reg4.nu.ac.th/publish/studentmanual2025_b.pdf",
     "category": "ทั่วไป", "description": "คู่มือฉบับเต็มสำหรับนิสิต"},
    {"title": "กยศ. มหาวิทยาลัยนเรศวร", "url": "https://www.acad.nu.ac.th/studentloan/",
     "category": "กยศ.", "description": "ข้อมูลและขั้นตอนการกู้ยืม กยศ."},
    {"title": "ระบบ DSL (กยศ. กลาง)", "url": "https://wsa.dsl.studentloan.or.th",
     "category": "กยศ.", "description": "ระบบยื่นกู้ยืม กยศ. ส่วนกลาง"},
    {"title": "เปลี่ยนรหัสผ่านระบบทะเบียน", "url": "https://password.nu.ac.th",
     "category": "ทั่วไป", "description": "เปลี่ยนรหัสผ่านระบบทะเบียนออนไลน์"},
    {"title": "กองบริการการศึกษา", "url": "https://www.acad.nu.ac.th",
     "category": "ทั่วไป", "description": "เว็บไซต์กองบริการการศึกษา ม.นเรศวร"},
]


def seed_instructors(conn):
    """ใส่ข้อมูลอาจารย์"""
    print("👨‍🏫 Seed อาจารย์...")
    
    # ลบของเก่าก่อน (idempotent)
    conn.execute("DELETE FROM instructors")
    
    for inst in INSTRUCTORS:
        conn.execute(
            """INSERT INTO instructors 
               (name, title, title_short, staff_id, email, office, specialization)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (inst["name"], inst["title"], inst["title_short"], 
             inst["staff_id"], inst["email"], inst["office"], inst["specialization"])
        )
    
    print(f"   ✅ เพิ่ม {len(INSTRUCTORS)} อาจารย์")


def seed_staff(conn):
    """ใส่ข้อมูลเจ้าหน้าที่"""
    print("👥 Seed เจ้าหน้าที่...")
    
    conn.execute("DELETE FROM staff")
    
    for s in STAFF:
        conn.execute(
            """INSERT INTO staff (name, nickname, position, phone, email, office)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (s["name"], s["nickname"], s["position"], s["phone"], s["email"], s["office"])
        )
    
    print(f"   ✅ เพิ่ม {len(STAFF)} เจ้าหน้าที่")


def seed_nu_forms(conn):
    """ใส่ข้อมูล NU forms"""
    print("📋 Seed NU forms...")
    
    conn.execute("DELETE FROM nu_forms")
    
    for f in NU_FORMS:
        conn.execute(
            """INSERT INTO nu_forms (code, name_th, category, purpose, fee)
               VALUES (?, ?, ?, ?, ?)""",
            (f["code"], f["name_th"], f["category"], f["purpose"], f["fee"])
        )
    
    print(f"   ✅ เพิ่ม {len(NU_FORMS)} forms")


def seed_links(conn):
    """ใส่ข้อมูลลิงก์สำคัญ"""
    print("🔗 Seed important links...")
    
    conn.execute("DELETE FROM important_links")
    
    for link in IMPORTANT_LINKS:
        conn.execute(
            """INSERT INTO important_links (title, url, category, description)
               VALUES (?, ?, ?, ?)""",
            (link["title"], link["url"], link["category"], link["description"])
        )
    
    print(f"   ✅ เพิ่ม {len(IMPORTANT_LINKS)} ลิงก์")


def main():
    print("=" * 60)
    print("🌱 Seed Data ลง SQLite")
    print("=" * 60)
    
    # สร้าง tables ก่อน (ถ้ายังไม่มี)
    init_database()
    
    # Seed ทุกตาราง
    with db_session() as conn:
        seed_instructors(conn)
        seed_staff(conn)
        seed_nu_forms(conn)
        seed_links(conn)
    
    # ─── สรุป ───
    print()
    print("=" * 60)
    print("📊 สรุป SQLite Database")
    print("=" * 60)
    
    with db_session() as conn:
        for table in ["instructors", "staff", "nu_forms", "important_links"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"   {table:25s}: {count} records")
    
    print()
    print("✅ Seed สำเร็จ! พร้อมใช้งาน RAR")


if __name__ == "__main__":
    main()
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


# ─── เจ้าหน้าที่ภาควิชา 4 ท่าน ───────────────────────
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

# ─── เจ้าหน้าที่หน่วยสหกิจศึกษา คณะวิทยาศาสตร์ 1 ท่าน ────────
COOP_STAFF = [
    {
        "name": "นิพิฐทภัทร ทัดหล่อ",
        "nickname": "พี่ไกร",
        "position": "นักวิชาการศึกษา (หน่วยสหกิจศึกษา)",
        "phone": "055-963141, 086-587-6293",
        "email": "CoopSC@nu.ac.th",
        "office": "หน่วยสหกิจศึกษา คณะวิทยาศาสตร์",
    },
]
# ─── เจ้าหน้าที่กยศ. คณะวิทยาศาสตร์ 1 ท่าน ────────
LOANSCI_STAFF = [
    {
        "name": "ปิยารมณ์ ครองราช",
        "nickname": "พี่มะนาว",
        "position": "เจ้าหน้าที่บริหารงานทั่วไป (กยศ.คณะวิทยาศาสตร์)",
        "phone": "055-963152",
        "email": "piyaromk@nu.ac.th",
        "office": "SC1 ห้องกิจการนิสิตและศิษย์เก่าสัมพันธ์",
    },
]


# ─── เจ้าหน้าที่งานทะเบียนนิสิตประจำคณะ 6 ท่าน ────────
REGISTRAR_STAFF = [
    {
        "name": "พชรพรรณ ปลื้มวงศ์",
        "phone": "055-968315",
        "faculties": "คณะวิทยาศาสตร์การแพทย์, คณะวิทยาศาสตร์ (รวม CSIT), คณะศึกษาศาสตร์",
    },
    {
        "name": "เริงจีรา กลั่นดี",
        "phone": "055-968310",
        "faculties": "คณะเกษตรศาสตร์, คณะนิติศาสตร์, คณะพยาบาลศาสตร์, คณะเภสัชศาสตร์, คณะโลจิสติกส์และดิจิทัลซัพพลายเชน",
    },
    {
        "name": "สุณีย์ พาสพิษณุ",
        "phone": "055-968300",
        "faculties": "คณะทันตแพทยศาสตร์, คณะวิศวกรรมศาสตร์, คณะสถาปัตยกรรมศาสตร์ ศิลปะและการออกแบบ, คณะสาธารณสุขศาสตร์, คณะสหเวชศาสตร์",
    },
    {
        "name": "กิติวรา เมฆมงคล",
        "phone": "055-968314",
        "faculties": "คณะแพทยศาสตร์, คณะบริหารธุรกิจ เศรษฐศาสตร์และการสื่อสาร, คณะมนุษยศาสตร์, วิทยาลัยนานาชาติ",
    },
    {
        "name": "พรชนก สวนอภัย",
        "phone": "055-968324",
        "faculties": "คณะสังคมศาสตร์",
    },
    {
        "name": "พงษ์พิทักษ์ สุคำ",
        "phone": "055-968315",
        "faculties": "ระดับบัณฑิตศึกษา",
    },
]


# ─── หน่วยงาน/เบอร์ติดต่อในมหาวิทยาลัย ────────────────
OFFICE_CONTACTS = [
    # ── ภาควิชา ──
    {
        "unit": "ภาควิชา CSIT",
        "phone": "055-963262, 055-963263",
        "location": "คณะวิทยาศาสตร์ อาคาร SC2",
        "email": None,
        "note": "สอบถามข้อมูลนิสิต งานภาควิชา",
        "category": "ภาควิชา",
    },
    # ── ทะเบียน / กองบริการการศึกษา ──
    {
        "unit": "กองบริการการศึกษา (เคาน์เตอร์)",
        "phone": "055-968324",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": "acad@nu.ac.th",
        "note": "ลงทะเบียน ดรอป ลาออก ยื่นจบ",
        "category": "ทะเบียน",
    },
    {
        "unit": "งานทะเบียนนิสิตและประมวลผล",
        "phone": "055-968300, 055-968314, 055-968315, 055-968324",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "ทะเบียนนิสิต คำร้องต่าง ๆ Transcript ใบรับรอง",
        "category": "ทะเบียน",
    },
    {
        "unit": "หน่วยสนับสนุนการเรียนการสอน",
        "phone": "055-968310, 055-968311",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "ระบบทะเบียนออนไลน์ ขอเปิด/ปิดรายวิชา",
        "category": "ทะเบียน",
    },
    {
        "unit": "หน่วยตารางเรียน/ตารางสอน",
        "phone": "055-968312",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "จัดตารางเรียน/สอบ",
        "category": "ทะเบียน",
    },
    {
        "unit": "หน่วยรับเข้าศึกษา",
        "phone": "055-968304, 055-968309",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "รับเข้าศึกษา (TCAS ฯลฯ)",
        "category": "ทะเบียน",
    },
    {
        "unit": "งานพัฒนาหลักสูตร",
        "phone": "055-968306, 055-968307, 055-968318",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "พัฒนา/ปรับปรุงหลักสูตร",
        "category": "ทะเบียน",
    },
    {
        "unit": "งานจัดการวิชาศึกษาทั่วไป (GE)",
        "phone": "055-968330, 055-968331, 055-968332",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "วิชาที่ขึ้นต้นด้วย 002xxx",
        "category": "ทะเบียน",
    },
    {
        "unit": "งานอำนวยการ กองบริการการศึกษา",
        "phone": "055-968303, 055-968322",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "ธุรการของกองบริการการศึกษา",
        "category": "ทะเบียน",
    },
    {
        "unit": "ผู้อำนวยการกองบริการการศึกษา",
        "phone": "055-968301",
        "location": "กองบริการการศึกษา",
        "email": "acad@nu.ac.th",
        "note": "ร้องเรียน/ข้อเสนอแนะ",
        "category": "ทะเบียน",
    },
    # ── กยศ. / การเงิน ──
    {
        "unit": "งานส่งเสริมการจัดการศึกษา / กยศ.",
        "phone": "055-968316, 055-968319",
        "location": "อาคารเรียนรวม QS ชั้น 1",
        "email": None,
        "note": "กระบวนการกู้ยืม กยศ. ของมหาวิทยาลัย",
        "category": "กยศ.",
    },
    {
        "unit": "กองคลัง",
        "phone": "055-961135",
        "location": "อาคารมิ่งขวัญ ชั้น 1",
        "email": None,
        "note": "ชำระค่าเทอม ใบเสร็จ",
        "category": "การเงิน",
    },
    # ── IT / ภาษา / หอสมุด ──
    {
        "unit": "งานระบบเครือข่าย (CITCOMS)",
        "phone": "055-961512, 055-961524",
        "location": "อาคาร CITCOMS ชั้น 2",
        "email": None,
        "note": "ลืมรหัสผ่าน internet/reg/nu-mail, ICT Exam, ติดตั้งโปรแกรมลิขสิทธิ์ฟรี",
        "category": "IT",
    },
    {
        "unit": "กองพัฒนาภาษาและกิจการต่างประเทศ",
        "phone": "055-961610",
        "location": "อาคาร CITCOMS ชั้น 5",
        "email": None,
        "note": "อบรม/สอบวัดความรู้ภาษาอังกฤษ CEPT",
        "category": "ภาษา",
    },
    {
        "unit": "สำนักหอสมุด",
        "phone": "055-962555",
        "location": "สำนักหอสมุด",
        "email": None,
        "note": "ยืม-คืนหนังสือ พื้นที่อ่าน 24 ชม. ห้องติว",
        "category": "บริการ",
    },
    # ── กิจการนิสิต (อาคารขวัญเมือง) ──
    {
        "unit": "กองกิจการนิสิต (บริการนิสิต)",
        "phone": "055-961216, 055-961287",
        "location": "อาคารขวัญเมือง ชั้น 1 ห้อง 1",
        "email": None,
        "note": "ทุน จัดหางาน นักศึกษาวิชาทหาร ผ่อนผันทหาร",
        "category": "กิจการนิสิต",
    },
    {
        "unit": "หอพักนิสิต",
        "phone": "055-961289, 055-961290",
        "location": "อาคารขวัญเมือง ชั้น 1 ห้อง 1 และ 4",
        "email": None,
        "note": "จองหอ แจ้งซ่อม ค่าไฟ บริการไปรษณีย์",
        "category": "กิจการนิสิต",
    },
    {
        "unit": "ประกันอุบัติเหตุ",
        "phone": "055-961215",
        "location": "อาคารขวัญเมือง ชั้น 1 ห้อง 1",
        "email": None,
        "note": "เบิกค่ารักษากรณีอุบัติเหตุ/เสียชีวิต",
        "category": "กิจการนิสิต",
    },
    {
        "unit": "กิจกรรมนิสิต / ทรานสคริปต์กิจกรรม",
        "phone": "055-961210, 055-961213",
        "location": "อาคารขวัญเมือง ชั้น 1 ห้อง 5",
        "email": None,
        "note": "ส่งเสริม/บันทึกกิจกรรมนิสิต",
        "category": "กิจการนิสิต",
    },
    {
        "unit": "ศูนย์นิสิตจิตอาสา",
        "phone": "055-961213",
        "location": "อาคารขวัญเมือง ชั้น 1 ห้อง 5",
        "email": None,
        "note": "บันทึกชั่วโมงจิตสาธารณะ (ส่วนกลาง)",
        "category": "กิจการนิสิต",
    },
    {
        "unit": "วินัยนิสิต",
        "phone": "055-961150",
        "location": "อาคารขวัญเมือง ชั้น 1 ห้อง 5",
        "email": None,
        "note": "ใบรับรองความประพฤติ ร้องทุกข์ วินัยนิสิต",
        "category": "กิจการนิสิต",
    },
    # ── สหกิจศึกษา (คณะวิทย์) ──
    {
        "unit": "หน่วยสหกิจศึกษา คณะวิทยาศาสตร์",
        "phone": "055-963141, 086-587-6293",
        "location": "คณะวิทยาศาสตร์",
        "email": "CoopSC@nu.ac.th",
        "note": "ติดต่อพี่ไกร (นิพิฐทภัทร ทัดหล่อ) สมัครสหกิจที่ https://www.sci.nu.ac.th/coop/",
        "category": "สหกิจ",
    },
    # ── ความปลอดภัย ──
    {
        "unit": "สถานีตำรวจชุมชน",
        "phone": "055-261800",
        "location": "บริเวณประตู 5 ม.นเรศวร",
        "email": None,
        "note": "แจ้งความเอกสารหาย แจ้งเหตุอุบัติเหตุ/คดี",
        "category": "บริการ",
    },
]


# ─── คำร้อง NU Forms 24 รายการ ────────────────────────
NU_FORMS = [
    # ── ข้อมูลนิสิตใหม่ ──
    {
        "code": "NU1",
        "name_th": "ระเบียนประวัตินิสิต",
        "category": "ข้อมูลนิสิตใหม่",
        "purpose": "เก็บข้อมูลประวัตินิสิตใหม่ตอนรายงานตัว",
        "fee": None,
    },
    # ── ลงทะเบียน ──
    {
        "code": "NU3",
        "name_th": "คู่มือลงทะเบียนเรียน",
        "category": "ลงทะเบียน",
        "purpose": "คู่มืออธิบายขั้นตอนการลงทะเบียนเรียนผ่านระบบออนไลน์",
        "fee": None,
    },
    {
        "code": "NU4",
        "name_th": "แบบขอเปิดรายวิชา/หมู่เรียน (เพิ่ม)",
        "category": "ลงทะเบียน",
        "purpose": "ใช้เมื่อต้องการขอเปิดรายวิชาหรือหมู่เรียนเพิ่มเติม",
        "fee": None,
    },
    {
        "code": "NU5",
        "name_th": "แบบขอปิดรายวิชา/หมู่เรียน",
        "category": "ลงทะเบียน",
        "purpose": "ใช้เมื่อต้องการขอปิดรายวิชาหรือหมู่เรียน",
        "fee": None,
    },
    {
        "code": "NU6",
        "name_th": "แบบขอเปลี่ยนแปลงการสอนรายวิชา",
        "category": "ลงทะเบียน",
        "purpose": "ใช้เมื่อต้องการสำรองที่นั่งในรายวิชาที่ไม่ได้สำรองไว้ให้หลักสูตร",
        "fee": None,
    },
    {
        "code": "NU7",
        "name_th": "คำร้องขอคืนสภาพการเป็นนิสิต",
        "category": "ลงทะเบียน",
        "purpose": "ใช้เมื่อพ้นสภาพและต้องการกลับมาเป็นนิสิต",
        "fee": "1,000 บาท (ป.ตรี) / 2,000 บาท (บัณฑิตศึกษา)",
    },
    {
        "code": "NU8",
        "name_th": "คำร้องขอเพิ่มรายวิชาหลังกำหนด",
        "category": "ลงทะเบียน",
        "purpose": "ใช้เพิ่มรายวิชาหลังพ้น 2 สัปดาห์แรกของภาค (ไม่เกิน 5 สัปดาห์)",
        "fee": "100 บาท/สัปดาห์",
    },
    {
        "code": "NU9",
        "name_th": "คำร้องขอยื่นสำเร็จการศึกษาล่าช้ากว่ากำหนด",
        "category": "สำเร็จการศึกษา",
        "purpose": "ใช้เมื่อยื่นจบหลังพ้นกำหนด 4 สัปดาห์",
        "fee": "50 บาท/วันทำการ",
    },
    {
        "code": "NU11",
        "name_th": "แบบขอถอนรายวิชา (ติด W)",
        "category": "ลงทะเบียน",
        "purpose": "ใช้ถอนรายวิชาหลัง 2 สัปดาห์แรก จะติด W ในทรานสคริปต์ (ไม่เกินสัปดาห์ที่ 12)",
        "fee": None,
    },
    {
        "code": "NU14",
        "name_th": "คำร้องขอเทียบโอนรายวิชา",
        "category": "ลงทะเบียน",
        "purpose": "ใช้เทียบโอนรายวิชาที่เคยเรียนมาแล้ว (ต้องได้เกรด C ขึ้นไป)",
        "fee": "100 บาท/ครั้ง",
    },
    {
        "code": "NU18",
        "name_th": "คำร้องทั่วไป",
        "category": "ลงทะเบียน",
        "purpose": "ใช้สำหรับขอลงทะเบียนเกินหน่วยกิตที่กำหนด หรือขอเทียบรายวิชากรณีหลักสูตรปรับปรุง",
        "fee": None,
    },
    {
        "code": "NU20",
        "name_th": "ใบแจ้งยอดชำระเงิน",
        "category": "ลงทะเบียน",
        "purpose": "ใบแจ้งหนี้สำหรับชำระค่าลงทะเบียนที่ธนาคารหรือเคาน์เตอร์เซอร์วิส",
        "fee": None,
    },
    {
        "code": "NU24",
        "name_th": "ใบมอบฉันทะ",
        "category": "ลงทะเบียน",
        "purpose": "ใช้เมื่อมอบอำนาจให้ผู้อื่นดำเนินการแทน",
        "fee": None,
    },
    # ── เอกสารสำคัญ ──
    {
        "code": "NU15",
        "name_th": "คำร้องขอใบแสดงผลการเรียน (Transcript)",
        "category": "เอกสารสำคัญ",
        "purpose": "ขอ Transcript ภาษาไทย/อังกฤษ ขอผ่านระบบออนไลน์ ชำระด้วย K PLUS",
        "fee": None,
    },
    {
        "code": "NU21",
        "name_th": "คำร้องขอใบรับรอง",
        "category": "เอกสารสำคัญ",
        "purpose": "ขอใบรับรองการเป็นนิสิต/กำลังเรียน/เรียนครบหลักสูตร",
        "fee": None,
    },
    {
        "code": "NU25",
        "name_th": "แบบขอสำเร็จการศึกษา",
        "category": "สำเร็จการศึกษา",
        "purpose": "ยื่นในภาคที่คาดว่าจะจบ ภายใน 4 สัปดาห์หลังเปิดเทอม",
        "fee": "ป.ตรี 2,000 บาท / บัณฑิตศึกษา 2,500 บาท",
    },
    # ── ระเบียนประวัติ ──
    {
        "code": "NU13",
        "name_th": "คำร้องขอย้ายคณะ/สาขาวิชา",
        "category": "ระเบียนประวัติ",
        "purpose": "ใช้ย้ายคณะหรือสาขาภายในมหาวิทยาลัย ควรยื่นก่อนลงทะเบียน 4 สัปดาห์",
        "fee": None,
    },
    {
        "code": "NU16",
        "name_th": "คำร้องขอเปลี่ยนชื่อ ชื่อสกุล ยศ",
        "category": "ระเบียนประวัติ",
        "purpose": "ใช้เมื่อเปลี่ยนชื่อ-สกุล หรือยศ พร้อมแนบหลักฐานราชการ",
        "fee": None,
    },
    {
        "code": "NU17",
        "name_th": "คำร้องขอลาพักการศึกษา",
        "category": "ระเบียนประวัติ",
        "purpose": "ใช้ลาพักการศึกษา ผู้ปกครองต้องลงนามยินยอม (ป.ตรี)",
        "fee": None,
    },
    {
        "code": "NU19",
        "name_th": "คำร้องขอลาออกจากการศึกษา",
        "category": "ระเบียนประวัติ",
        "purpose": "ใช้ลาออกจากการเป็นนิสิต ผู้ปกครองต้องลงนามยินยอม (ป.ตรี)",
        "fee": None,
    },
    # ── ประมวลผลข้อมูล ──
    {
        "code": "NU32",
        "name_th": "แบบรายงานผลการเรียนรายวิชา",
        "category": "ประมวลผลข้อมูล",
        "purpose": "อาจารย์ผู้สอนใช้ส่งผลการเรียนให้งานทะเบียนฯ",
        "fee": None,
    },
    {
        "code": "NU33",
        "name_th": "แบบแก้ไขผลการเรียนรายวิชา",
        "category": "ประมวลผลข้อมูล",
        "purpose": "อาจารย์ผู้สอนใช้แก้อักษร I หรือ P (นิสิตไม่ได้ยื่นเอง)",
        "fee": None,
    },
    # ── สารนิเทศ ──
    {
        "code": "NU22",
        "name_th": "รายงานสถิติจำนวนนิสิตที่ลงทะเบียนเรียน",
        "category": "สารนิเทศ",
        "purpose": "รายงานสถิติการลงทะเบียนเรียนของนิสิต",
        "fee": None,
    },
    {
        "code": "NU26",
        "name_th": "ปฏิทินการศึกษา",
        "category": "สารนิเทศ",
        "purpose": "ปฏิทินกำหนดการลงทะเบียน สอบ เปิด-ปิดภาคการศึกษา",
        "fee": None,
    },
]


# ─── ลิงก์สำคัญ (ครบทุกหมวด) ─────────────────────────
IMPORTANT_LINKS = [
    # ── ระบบ ──
    {
        "title": "ระบบทะเบียนออนไลน์ (e-Registrar)",
        "url": "https://www.reg.nu.ac.th",
        "category": "ระบบ",
        "description": "ลงทะเบียน เพิ่ม-ถอนวิชา ดูเกรด ขอเอกสาร ยื่นคำร้องออนไลน์",
    },
    {
        "title": "เปลี่ยนรหัสผ่านระบบทะเบียน",
        "url": "https://password.nu.ac.th",
        "category": "ระบบ",
        "description": "เปลี่ยนรหัสผ่าน (ขึ้นต้นด้วยตัวอักษร ความยาวรวม >= 6)",
    },
    {
        "title": "ทรานสคริปต์กิจกรรม",
        "url": "https://acttrans.nu.ac.th/UI/ActTrans-Main-Login.aspx",
        "category": "ระบบ",
        "description": "ระบบบันทึก/ตรวจสอบกิจกรรมนิสิต",
    },
    # ── เอกสาร ──
    {
        "title": "ปฏิทินการศึกษา",
        "url": "https://reg4.nu.ac.th/registrar/calendar.asp?avs727811069=1",
        "category": "เอกสาร",
        "description": "ดูกำหนดการลงทะเบียน สอบ เปิด-ปิดเทอม",
    },
    {
        "title": "คู่มือนิสิตปริญญาตรี",
        "url": "https://reg4.nu.ac.th/publish/studentmanual2025_b.pdf",
        "category": "เอกสาร",
        "description": "คู่มือฉบับเต็มสำหรับนิสิต ปีการศึกษา 2568",
    },
    {
        "title": "คำแนะนำการลงทะเบียน",
        "url": "https://reg4.nu.ac.th/enrollguide.html",
        "category": "เอกสาร",
        "description": "คำแนะนำขั้นตอนการลงทะเบียนเรียน",
    },
    {
        "title": "คู่มือ NU App สำหรับนิสิต",
        "url": "https://reg.nu.ac.th/manual/1.man-user/3.Mobile/MAN_MB-NU67-REG-1-9.STU-Mobile.pdf",
        "category": "เอกสาร",
        "description": "วิธีใช้แอปพลิเคชัน NU สำหรับนิสิต",
    },
    {
        "title": "คู่มือ NU App สำหรับผู้สอน",
        "url": "https://reg.nu.ac.th/manual/1.man-user/3.Mobile/MAN_MB-NU67-REG-1-10.Ins-Mobile.pdf",
        "category": "เอกสาร",
        "description": "วิธีใช้แอปพลิเคชัน NU สำหรับผู้สอน",
    },
    # ── กยศ. ──
    {
        "title": "กยศ. มหาวิทยาลัยนเรศวร",
        "url": "https://www.acad.nu.ac.th/studentloan/",
        "category": "กยศ.",
        "description": "ข้อมูลและขั้นตอนการกู้ยืม กยศ. ของ ม.นเรศวร",
    },
    {
        "title": "ระบบ DSL (กยศ. ส่วนกลาง)",
        "url": "https://wsa.dsl.studentloan.or.th/#/rms/rms-login",
        "category": "กยศ.",
        "description": "ระบบยื่นกู้/ยืนยันการกู้ กยศ. ส่วนกลาง",
    },
    # ── หน่วยงาน ──
    {
        "title": "กองบริการการศึกษา",
        "url": "https://www.acad.nu.ac.th",
        "category": "หน่วยงาน",
        "description": "เว็บไซต์กองบริการการศึกษา ม.นเรศวร",
    },
    {
        "title": "คณะวิทยาศาสตร์",
        "url": "https://www.sci.nu.ac.th/science/",
        "category": "หน่วยงาน",
        "description": "เว็บไซต์คณะวิทยาศาสตร์",
    },
    {
        "title": "สมัครสหกิจศึกษา (คณะวิทย์)",
        "url": "https://www.sci.nu.ac.th/coop/",
        "category": "หน่วยงาน",
        "description": "ระบบสมัครสหกิจศึกษา MIS",
    },
    # ── ติดต่อ ──
    {
        "title": "แผนที่ภาควิชา CSIT",
        "url": "https://maps.app.goo.gl/wjmiv9KBu8Q1ScmA9",
        "category": "ติดต่อ",
        "description": "Google Maps พิกัดภาควิชา CSIT",
    },
    # ── Facebook ──
    {
        "title": "เพจ CSIT",
        "url": "https://www.facebook.com/share/1N5QSZJYBn/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กภาควิชาวิทยาการคอมพิวเตอร์ฯ",
    },
    {
        "title": "เพจคณะวิทยาศาสตร์",
        "url": "https://www.facebook.com/share/1GmCQJDB71/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กคณะวิทยาศาสตร์ ม.นเรศวร",
    },
    {
        "title": "เพจสโมสรนิสิตคณะวิทยาศาสตร์",
        "url": "https://www.facebook.com/share/19Rkw2W3Ks/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กสโมสรนิสิตคณะวิทย์",
    },
    {
        "title": "เพจ กยศ. คณะวิทยาศาสตร์",
        "url": "https://www.facebook.com/share/g/1HGs7F7ozY/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กกลุ่ม กยศ. คณะวิทย์",
    },
    {
        "title": "เพจมหาวิทยาลัยนเรศวร",
        "url": "https://www.facebook.com/share/18qTsne12Y/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กมหาวิทยาลัยนเรศวร",
    },
    {
        "title": "เพจกองกิจการนิสิต",
        "url": "https://www.facebook.com/share/18vAHnWSSS/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กกองกิจการนิสิต",
    },
    {
        "title": "เพจกองบริการการศึกษา",
        "url": "https://www.facebook.com/share/17fMvyfQuo/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กกองบริการการศึกษา",
    },
    {
        "title": "เพจ กยศ. มหาวิทยาลัยนเรศวร",
        "url": "https://www.facebook.com/share/1DD7YLvzZL/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊ก กยศ. ส่วนของมหาวิทยาลัย",
    },
    {
        "title": "เพจ CITCOMS",
        "url": "https://www.facebook.com/share/1HTeA9j5PN/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กศูนย์เทคโนโลยีสารสนเทศและการสื่อสาร",
    },
    {
        "title": "เพจกองพัฒนาภาษาและกิจการต่างประเทศ",
        "url": "https://www.facebook.com/share/1EB3FWdQux/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กกองพัฒนาภาษาฯ (CEPT)",
    },
    {
        "title": "เพจสำนักหอสมุด",
        "url": "https://www.facebook.com/share/18WRLExScW/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กสำนักหอสมุด",
    },
    {
        "title": "เพจหอพักนิสิต",
        "url": "https://www.facebook.com/share/18XT2fKrjY/?mibextid=wwXIfr",
        "category": "Facebook",
        "description": "เฟซบุ๊กหอพักนิสิต ม.นเรศวร",
    },
]


# ═══════════════════════════════════════════════════════
# Seed Functions
# ═══════════════════════════════════════════════════════


def seed_instructors(conn):
    """ใส่ข้อมูลอาจารย์"""
    print("👨‍🏫 Seed อาจารย์...")
    conn.execute("DELETE FROM instructors")
    for inst in INSTRUCTORS:
        conn.execute(
            """INSERT INTO instructors
               (name, title, title_short, staff_id, email, office, specialization)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                inst["name"],
                inst["title"],
                inst["title_short"],
                inst["staff_id"],
                inst["email"],
                inst["office"],
                inst["specialization"],
            ),
        )
    print(f"   ✅ เพิ่ม {len(INSTRUCTORS)} อาจารย์")


def seed_staff(conn):
    """ใส่ข้อมูลเจ้าหน้าที่ภาควิชา"""
    print("👥 Seed เจ้าหน้าที่ภาควิชา...")
    conn.execute("DELETE FROM staff")
    for s in STAFF:
        conn.execute(
            """INSERT INTO staff (name, nickname, position, phone, email, office)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                s["name"],
                s["nickname"],
                s["position"],
                s["phone"],
                s["email"],
                s["office"],
            ),
        )
    print(f"   ✅ เพิ่ม {len(STAFF)} เจ้าหน้าที่")


def seed_coop_staff(conn):
    """ใส่ข้อมูลเจ้าหน้าที่หน่วยสหกิจศึกษา"""
    print("🎓 Seed เจ้าหน้าที่หน่วยสหกิจ...")
    conn.execute("DELETE FROM coop_staff")
    for c in COOP_STAFF:
        conn.execute(
            """INSERT INTO coop_staff (name, nickname, position, phone, email, office)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                c["name"],
                c["nickname"],
                c["position"],
                c["phone"],
                c["email"],
                c["office"],
            ),
        )
    print(f"   ✅ เพิ่ม {len(COOP_STAFF)} ท่าน")


def seed_loansci_staff(conn):
    """ใส่ข้อมูลเจ้าหน้าที่กยศ.คณะวิทยาศาสตร์"""
    print("🎓 Seed เจ้าหน้ากยศ.คณะวิทยาศาสตร์")
    conn.execute("DELETE FROM loansci_staff")
    for l in LOANSCI_STAFF:
        conn.execute(
            """INSERT INTO loansci_staff (name, nickname, position, phone, email, office)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                l["name"],
                l["nickname"],
                l["position"],
                l["phone"],
                l["email"],
                l["office"],
            ),
        )
    print(f"   ✅ เพิ่ม {len(LOANSCI_STAFF)} ท่าน")


def seed_registrar(conn):
    """ใส่ข้อมูลเจ้าหน้าที่งานทะเบียนนิสิตประจำคณะ"""
    print("🗂  Seed เจ้าหน้าที่งานทะเบียนประจำคณะ...")
    conn.execute("DELETE FROM registrar_staff")
    for r in REGISTRAR_STAFF:
        conn.execute(
            """INSERT INTO registrar_staff (name, phone, faculties)
               VALUES (?, ?, ?)""",
            (r["name"], r["phone"], r["faculties"]),
        )
    print(f"   ✅ เพิ่ม {len(REGISTRAR_STAFF)} ท่าน")


def seed_offices(conn):
    """ใส่ข้อมูลหน่วยงาน/เบอร์ติดต่อในมหาวิทยาลัย"""
    print("🏢 Seed หน่วยงาน/เบอร์ติดต่อ...")
    conn.execute("DELETE FROM office_contacts")
    for o in OFFICE_CONTACTS:
        conn.execute(
            """INSERT INTO office_contacts
               (unit, phone, location, email, note, category)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                o["unit"],
                o["phone"],
                o["location"],
                o["email"],
                o["note"],
                o["category"],
            ),
        )
    print(f"   ✅ เพิ่ม {len(OFFICE_CONTACTS)} หน่วยงาน")


def seed_nu_forms(conn):
    """ใส่ข้อมูล NU forms (ครบทุกรายการ)"""
    print("📋 Seed NU forms...")
    conn.execute("DELETE FROM nu_forms")
    for f in NU_FORMS:
        conn.execute(
            """INSERT INTO nu_forms (code, name_th, category, purpose, fee)
               VALUES (?, ?, ?, ?, ?)""",
            (f["code"], f["name_th"], f["category"], f["purpose"], f["fee"]),
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
            (link["title"], link["url"], link["category"], link["description"]),
        )
    print(f"   ✅ เพิ่ม {len(IMPORTANT_LINKS)} ลิงก์")


def main():
    print("=" * 60)
    print("🌱 Seed Data ลง SQLite")
    print("=" * 60)

    init_database()

    with db_session() as conn:
        seed_instructors(conn)
        seed_staff(conn)
        seed_coop_staff(conn)
        seed_loansci_staff(conn)
        seed_registrar(conn)
        seed_offices(conn)
        seed_nu_forms(conn)
        seed_links(conn)

    print()
    print("=" * 60)
    print("📊 สรุป SQLite Database")
    print("=" * 60)

    with db_session() as conn:
        for table in [
            "instructors",
            "staff",
            "coop_staff",
            "loansci_staff",
            "registrar_staff",
            "office_contacts",
            "nu_forms",
            "important_links",
        ]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"   {table:25s}: {count} records")

    print()
    print("✅ Seed สำเร็จ! พร้อมใช้งาน RAR")


if __name__ == "__main__":
    main()

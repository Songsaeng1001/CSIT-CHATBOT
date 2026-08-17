"""
SQLite Database Manager
สำหรับเก็บข้อมูลโครงสร้าง (อาจารย์, รายวิชา, NU forms)
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional
from src.config import SQLITE_PATH


def get_connection() -> sqlite3.Connection:
    """สร้าง connection พร้อม optimization"""
    # สร้างโฟลเดอร์ถ้าไม่มี
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Optimization สำหรับ Mac
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB
    conn.execute("PRAGMA foreign_keys=ON")

    return conn


@contextmanager
def db_session():
    """Context manager สำหรับใช้ db แบบปลอดภัย"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _add_column_if_missing(cur, table: str, column: str, col_type: str):
    """เพิ่มคอลัมน์ให้ตารางที่มีอยู่แล้ว (migration แบบเบา ๆ)
    ใช้เผื่อ DB เก่าที่สร้างมาก่อนจะมีคอลัมน์นี้ — CREATE TABLE IF NOT EXISTS
    เฉย ๆ จะไม่เพิ่มคอลัมน์ใหม่ให้ตารางที่มีอยู่แล้ว จึงต้อง ALTER TABLE เอง
    """
    existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def init_database():
    """สร้างตารางทั้งหมด"""
    with db_session() as conn:
        cur = conn.cursor()

        # ─── instructors ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS instructors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                title TEXT,
                title_short TEXT,
                staff_id TEXT UNIQUE,
                email TEXT,
                office TEXT,
                specialization TEXT,
                education TEXT,
                is_advisor BOOLEAN DEFAULT 1,
                department TEXT DEFAULT 'CSIT'
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_instructor_name ON instructors(name)"
        )
        _add_column_if_missing(cur, "instructors", "education", "TEXT")

        # ─── instructor_education (structured: 1 แถว = 1 ใบปริญญา) ───
        # เดิมเก็บวุฒิเป็นข้อความยาวก้อนเดียวในคอลัมน์ instructors.education แล้ว
        # "เดา" ระดับปริญญา/ประเทศ ด้วย heuristic เทียบสตริง ซึ่งเปราะมาก
        # ตารางนี้แยกเป็นคอลัมน์จริง → คำถามแบบ "ใครจบเอกจากต่างประเทศ"
        # กลายเป็น SQL query ตรง ๆ ไม่ต้องเดาอีกต่อไป
        #   level: 'doctorate' | 'master' | 'bachelor'
        #   is_thailand: 1 = สถาบันในไทย, 0 = ต่างประเทศ (คำนวณจาก country ตอนบันทึก)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS instructor_education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instructor_id INTEGER NOT NULL,
                level TEXT NOT NULL,
                degree TEXT,
                field TEXT,
                institution TEXT,
                country TEXT,
                is_thailand INTEGER NOT NULL DEFAULT 0,
                seq INTEGER DEFAULT 0,
                FOREIGN KEY (instructor_id) REFERENCES instructors(id)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_edu_instructor "
            "ON instructor_education(instructor_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_edu_level_country "
            "ON instructor_education(level, is_thailand)"
        )

        # ─── courses ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name_th TEXT NOT NULL,
                name_en TEXT,
                credits TEXT,
                program TEXT,
                category TEXT,
                year INTEGER,
                description TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_course_code ON courses(code)")

        # ─── course_instructors (ใครสอนวิชาอะไร — สำหรับเปรียบเทียบ RAG vs RAG+KG) ───
        # NOTE: ยังไม่มีข้อมูลจริง (ณ วันที่สร้างตารางนี้) — schema พร้อมใช้ก่อน
        # กรอกข้อมูลทีหลังด้วย add_teaching_assignment() ด้านล่าง
        cur.execute("""
            CREATE TABLE IF NOT EXISTS course_instructors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                instructor_id INTEGER NOT NULL,
                semester TEXT,
                academic_year TEXT,
                role TEXT DEFAULT 'ผู้สอน',
                FOREIGN KEY (course_code) REFERENCES courses(code),
                FOREIGN KEY (instructor_id) REFERENCES instructors(id)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_ci_course ON course_instructors(course_code)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_ci_instructor ON course_instructors(instructor_id)"
        )

        # ─── staff ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                nickname TEXT,
                position TEXT,
                phone TEXT,
                email TEXT,
                office TEXT
            )
        """)

        # ─── nu_forms ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nu_forms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name_th TEXT NOT NULL,
                purpose TEXT,
                category TEXT,
                process TEXT,
                fee TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_form_code ON nu_forms(code)")

        # ─── important_links ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS important_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT,
                description TEXT
            )
        """)

        # ─── faq_quick ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS faq_quick (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                keywords TEXT,
                category TEXT
            )
        """)

        # ─── conversations (สำหรับ log) ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                question TEXT,
                answer TEXT,
                sources TEXT,
                confidence REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ─── registrar_staff (เจ้าหน้าที่งานทะเบียนนิสิตประจำคณะ) ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS registrar_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                faculties TEXT
            )
        """)

        # ─── coop_staff (เจ้าหน้าที่หน่วยสหกิจศึกษา) ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS coop_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                nickname TEXT,
                position TEXT,
                phone TEXT,
                email TEXT,
                office TEXT
            )
        """)

                # ─── loansci_staff (เจ้าหน้าที่ กยศ. คณะวิทยาศาสตร์) ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS loansci_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                nickname TEXT,
                position TEXT,
                phone TEXT,
                email TEXT,
                office TEXT
            )
        """)


        # ─── office_contacts (เบอร์/ที่ตั้งหน่วยงานในมหาวิทยาลัย) ───
        cur.execute("""
            CREATE TABLE IF NOT EXISTS office_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit TEXT NOT NULL,
                phone TEXT,
                location TEXT,
                email TEXT,
                note TEXT,
                category TEXT
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_office_category ON office_contacts(category)")

    print(f"✅ สร้าง SQLite tables ที่: {SQLITE_PATH}")


# ═══ Query Functions ═══


def find_instructor(name: str) -> Optional[dict]:
    """ค้นหาอาจารย์ด้วยชื่อ"""
    with db_session() as conn:
        cur = conn.execute(
            "SELECT * FROM instructors WHERE name LIKE ? LIMIT 1", (f"%{name}%",)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_instructors() -> list[dict]:
    """รายชื่ออาจารย์ทั้งหมด"""
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM instructors ORDER BY title, name")
        return [dict(r) for r in cur.fetchall()]


def update_instructor_education(name: str, education: str) -> bool:
    """กรอก/แก้ไขวุฒิการศึกษาของอาจารย์ (ค้นด้วยชื่อแบบ LIKE เหมือน find_instructor)
    ใช้ตอนกรอกข้อมูลจริงทีหลัง เช่น:
        from src.database.sqlite_db import update_instructor_education
        update_instructor_education("สัญญา", "ปร.ด. วิทยาการคอมพิวเตอร์ มหาวิทยาลัยนเรศวร")
    คืน True ถ้าอัปเดตสำเร็จ (เจอแถวที่ตรง), False ถ้าไม่เจอชื่อนั้น
    """
    with db_session() as conn:
        cur = conn.execute(
            "UPDATE instructors SET education = ? WHERE name LIKE ?",
            (education, f"%{name}%"),
        )
        return cur.rowcount > 0


def list_instructors_with_education() -> list[dict]:
    """คืนอาจารย์ทุกคนที่มีข้อมูล education กรอกแล้ว (ไม่ว่าง)
    ใช้เป็นฐานให้ query แบบ 'กวาดทุกคนแล้วกรองด้วยคุณสมบัติ' (KG-style structured query)
    """
    with db_session() as conn:
        cur = conn.execute(
            "SELECT * FROM instructors "
            "WHERE education IS NOT NULL AND TRIM(education) != '' "
            "ORDER BY name"
        )
        return [dict(r) for r in cur.fetchall()]


# ═══ instructor_education: ข้อมูลวุฒิแบบ structured (ชั้นที่เชื่อถือได้) ═══
# ชั้นนี้คือ "แหล่งความจริง" ของคำถามแบบกรองคุณสมบัติ (KG-style query)
# ถ้าตารางนี้มีข้อมูล → ใช้ SQL ตรง ๆ ไม่แตะ heuristic เลย
# ถ้ายังว่าง (DB เก่าที่ยังไม่ได้ seed) → ถอยไปใช้ heuristic เดิมอัตโนมัติ

LEVEL_DOCTORATE = "doctorate"
LEVEL_MASTER = "master"
LEVEL_BACHELOR = "bachelor"
VALID_LEVELS = {LEVEL_DOCTORATE, LEVEL_MASTER, LEVEL_BACHELOR}

# ค่าที่ถือว่า "ประเทศไทย" (เทียบแบบ normalize ตัวพิมพ์/ช่องว่างแล้ว)
_THAILAND_VALUES = {"ไทย", "ประเทศไทย", "thailand", "th", "tha"}

_LEVEL_LABEL_TH = {
    LEVEL_DOCTORATE: "ปริญญาเอก",
    LEVEL_MASTER: "ปริญญาโท",
    LEVEL_BACHELOR: "ปริญญาตรี",
}


def is_thailand_country(country: Optional[str]) -> bool:
    """True ถ้าค่า country หมายถึงประเทศไทย

    ⚠️ ตั้งใจเทียบแบบ "ทั้งค่า" ไม่ใช่ substring — ถ้าเทียบ substring ด้วยคำว่า
    "ไทย" เฉย ๆ นามสกุลอาจารย์อย่าง "วงษ์ไทย" จะทำให้จัดประเทศผิดทันที
    """
    if not country:
        return False
    return country.strip().lower() in _THAILAND_VALUES


def set_instructor_education(name_or_staff_id: str, degrees: list[dict]) -> bool:
    """บันทึกวุฒิการศึกษาแบบ structured ของอาจารย์ 1 ท่าน (ลบของเดิมแล้วใส่ชุดใหม่)

    degrees = [{"level","degree","field","institution","country"}, ...]
    หา instructor ด้วย staff_id ก่อน (UNIQUE — แม่นสุด) ถ้าไม่เจอค่อย fallback
    ไปหาด้วยชื่อแบบ LIKE เหมือนฟังก์ชันอื่น

    นอกจากเขียนตาราง structured แล้ว ยัง "ประกอบสตริงกลับ" ไปใส่คอลัมน์
    instructors.education ให้ด้วย เพื่อให้โค้ดเดิมที่อ่านคอลัมน์นั้น
    (format_instructor ใน retriever.py) ทำงานได้เหมือนเดิม ไม่ต้องแก้ตาม

    คืน True ถ้าเจออาจารย์และบันทึกสำเร็จ, False ถ้าหาไม่เจอ
    """
    for d in degrees:
        if d.get("level") not in VALID_LEVELS:
            raise ValueError(
                f"level ไม่ถูกต้อง: {d.get('level')!r} "
                f"(ต้องเป็นหนึ่งใน {sorted(VALID_LEVELS)})"
            )

    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM instructors WHERE staff_id = ? LIMIT 1",
            (name_or_staff_id,),
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT * FROM instructors WHERE name LIKE ? LIMIT 1",
                (f"%{name_or_staff_id}%",),
            ).fetchone()
        if row is None:
            return False

        inst_id = row["id"]
        conn.execute(
            "DELETE FROM instructor_education WHERE instructor_id = ?", (inst_id,)
        )
        for seq, d in enumerate(degrees):
            conn.execute(
                """INSERT INTO instructor_education
                   (instructor_id, level, degree, field, institution,
                    country, is_thailand, seq)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    inst_id,
                    d["level"],
                    d.get("degree"),
                    d.get("field"),
                    d.get("institution"),
                    d.get("country"),
                    1 if is_thailand_country(d.get("country")) else 0,
                    seq,
                ),
            )

        conn.execute(
            "UPDATE instructors SET education = ? WHERE id = ?",
            (_format_education_text(degrees), inst_id),
        )
    return True


def _format_education_text(degrees: list[dict]) -> str:
    """ประกอบวุฒิ structured กลับเป็นสตริงเดิม (คั่นด้วย ' | ')

    จงใจใส่ทั้งชื่อสถาบันและคำว่า 'ประเทศ...' ครบทุกใบ เพื่อให้ heuristic เดิม
    (ที่ยังใช้เป็น fallback) ตัดสินใจถูกด้วยถ้าตาราง structured หายไป
    """
    parts = []
    for d in degrees:
        country = (d.get("country") or "").strip()
        country_text = "ประเทศไทย" if is_thailand_country(country) else f"ประเทศ {country}"
        parts.append(
            f"คุณวุฒิ {d.get('degree') or ''} "
            f"สาขาวิชา {d.get('field') or ''} "
            f"จาก {d.get('institution') or ''} {country_text}".strip()
        )
    return " | ".join(parts)


def count_education_rows() -> int:
    """จำนวนแถวในตาราง instructor_education (ใช้ตัดสินว่าจะใช้ structured หรือ heuristic)"""
    with db_session() as conn:
        return conn.execute("SELECT COUNT(*) FROM instructor_education").fetchone()[0]


def list_education_rows(instructor_id: Optional[int] = None) -> list[dict]:
    """ดึงแถววุฒิการศึกษาทั้งหมด (หรือของอาจารย์คนเดียวถ้าระบุ instructor_id)"""
    sql = (
        "SELECT e.*, i.name AS instructor_name FROM instructor_education e "
        "JOIN instructors i ON i.id = e.instructor_id "
    )
    params: tuple = ()
    if instructor_id is not None:
        sql += "WHERE e.instructor_id = ? "
        params = (instructor_id,)
    sql += "ORDER BY i.name, e.seq"
    with db_session() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _query_instructors_by_doctorate(is_thailand: int) -> list[dict]:
    """อาจารย์ที่มีใบปริญญาเอกจากไทย (1) หรือต่างประเทศ (0) — SQL ล้วน ไม่มี heuristic"""
    with db_session() as conn:
        cur = conn.execute(
            """SELECT DISTINCT i.* FROM instructors i
               JOIN instructor_education e ON e.instructor_id = i.id
               WHERE e.level = ? AND e.is_thailand = ?
               ORDER BY i.name""",
            (LEVEL_DOCTORATE, is_thailand),
        )
        return [dict(r) for r in cur.fetchall()]


def find_thai_phd_instructors() -> list[dict]:
    """อาจารย์ที่จบปริญญาเอกในประเทศไทย (ต้อง seed structured ก่อน ไม่งั้นคืนลิสต์ว่าง)"""
    return _query_instructors_by_doctorate(1)


def find_instructors_without_doctorate() -> list[dict]:
    """อาจารย์ที่ยังไม่มีใบปริญญาเอกในฐานข้อมูล (ใช้ตรวจความครบของข้อมูล)"""
    with db_session() as conn:
        cur = conn.execute(
            """SELECT i.* FROM instructors i
               WHERE NOT EXISTS (
                   SELECT 1 FROM instructor_education e
                   WHERE e.instructor_id = i.id AND e.level = ?
               )
               ORDER BY i.name""",
            (LEVEL_DOCTORATE,),
        )
        return [dict(r) for r in cur.fetchall()]


def education_coverage() -> dict:
    """สรุปความครบของข้อมูล — ใช้ตรวจก่อนเชื่อผลลัพธ์ KG ทุกครั้ง

    คืน dict: total_instructors, with_education_rows, doctorate_foreign,
              doctorate_thai, no_doctorate, missing_education (รายชื่อ)
    """
    with db_session() as conn:
        total = conn.execute("SELECT COUNT(*) FROM instructors").fetchone()[0]
        with_rows = conn.execute(
            "SELECT COUNT(DISTINCT instructor_id) FROM instructor_education"
        ).fetchone()[0]
        missing = [
            dict(r)
            for r in conn.execute(
                """SELECT * FROM instructors i
                   WHERE NOT EXISTS (
                       SELECT 1 FROM instructor_education e
                       WHERE e.instructor_id = i.id
                   ) ORDER BY name"""
            ).fetchall()
        ]
    return {
        "total_instructors": total,
        "with_education_rows": with_rows,
        "doctorate_foreign": len(_query_instructors_by_doctorate(0)),
        "doctorate_thai": len(_query_instructors_by_doctorate(1)),
        "no_doctorate": len(find_instructors_without_doctorate()),
        "missing_education": missing,
    }


# ─── heuristic (fallback เท่านั้น): กรองอาจารย์ที่จบปริญญาเอกจากต่างประเทศ ─────
# ยังไม่มีคอลัมน์ structured แยก "ประเทศ" ในตาราง instructors การกรอง "ต่างประเทศ"
# จึงทำแบบ heuristic: ถ้า education มีคำระบุปริญญาเอก (ปร.ด./Ph.D./ดุษฎีบัณฑิต)
# และ "ไม่มี" ชื่อมหาวิทยาลัยไทยในรายการด้านล่างปรากฏอยู่เลย → ถือว่าจบต่างประเทศ
# ⚠️ นี่คือ heuristic ล้วน ๆ ไม่ใช่ข้อมูลที่ยืนยันจริง — ควรตรวจสอบผลลัพธ์ทุกครั้ง
#    หลังกรอก/แก้ไขข้อมูล education และเพิ่มชื่อมหาวิทยาลัยไทยที่ตกหล่นในลิสต์นี้
THAI_UNIVERSITY_KEYWORDS = [
    "มหาวิทยาลัยนเรศวร", "นเรศวร",
    "จุฬาลงกรณ์", "จุฬาฯ",
    "มหาวิทยาลัยเกษตรศาสตร์", "เกษตรศาสตร์",
    "มหาวิทยาลัยธรรมศาสตร์", "ธรรมศาสตร์",
    "มหาวิทยาลัยมหิดล", "มหิดล",
    "มหาวิทยาลัยเชียงใหม่",
    "มหาวิทยาลัยขอนแก่น",
    "สถาบันเทคโนโลยีพระจอมเกล้า",
    "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้า",
    "มหาวิทยาลัยศรีนครินทรวิโรฒ",
    "มหาวิทยาลัยบูรพา",
    "มหาวิทยาลัยสงขลานครินทร์",
    "มหาวิทยาลัยศิลปากร",
    "สถาบันบัณฑิตพัฒนบริหารศาสตร์",
    "มหาวิทยาลัยรามคำแหง",
    # กลุ่มที่ตกหล่นและพบจริงในข้อมูลภาควิชา
    "ราชภัฏ",           # ม.ราชภัฏพิบูลสงคราม (วุฒิ ป.ตรี อ.สัญญา)
    "ราชมงคล",          # สถาบันเทคโนโลยีราชมงคลบางพระ (อ.อดิเรก)
    "อัสสัมชัญ",         # ม.อัสสัมชัญ (อ.อนงค์พร)
    "พระจอมเกล้า",       # ครอบคลุมทั้ง สจล./สจพ./มจธ. ที่เขียนหลายรูปแบบ
    "ศรีนครินทรวิโรฒ",
    # ⚠️ สถาบันในไทยที่ชื่อเป็นภาษาอังกฤษล้วน — ถ้าไม่ดักไว้จะถูกนับเป็น
    #    "ต่างประเทศ" ทันทีเพราะไม่มีคำไทยสักคำในบรรทัด
    "Asian Institute of Technology",
    "Asia Institute of Technology",
    "Chulalongkorn",
    "Mahidol",
    "Naresuan",
    "Chiang Mai University",
    "Kasetsart",
    "Thammasat",
    "King Mongkut",
    "ประเทศไทย",
]
# ⚠️ ห้ามใส่คำว่า "ไทย" เดี่ยว ๆ ในลิสต์นี้เด็ดขาด — จะไปแมตช์นามสกุลอาจารย์
#    เช่น "วินัย วงษ์ไทย" ทำให้วุฒิจากอังกฤษถูกจัดเป็นของไทยผิด ๆ
# คำย่อวุฒิปริญญาเอกภาษาไทยมีหลายแบบตามสาขาวิชา ไม่ใช่แค่ "ปร.ด." (Ph.D. ทั่วไป)
# เช่น วศ.ด. (Doctor of Engineering), วท.ด. (Doctor of Science), ค.ด. (Ed.D.)
PHD_KEYWORDS = [
    "ปริญญาเอก", "ปร.ด", "Ph.D", "PhD", "ดุษฎีบัณฑิต", "ระดับปริญญาเอก",
    "วศ.ด", "วท.ด", "ค.ด", "ทล.ด", "รป.ด", "บธ.ด",
    "ศศ.ด", "สศ.ด", "พย.ด", "กศ.ด", "นบ.ด",
    "D.Eng", "Sc.D", "Ed.D", "DBA", "Doctor of",
    # หมายเหตุ: จงใจไม่ใส่ตัวย่อสั้นกว่า 3 ตัวอักษร (เช่น "น.ด") เพราะเสี่ยง
    # แมตช์กลางคำอื่นโดยไม่ตั้งใจ — ชั้น structured เป็นตัวตัดสินจริงอยู่แล้ว
]


def find_foreign_phd_instructors() -> list[dict]:
    """อาจารย์ที่มีวุฒิปริญญาเอกจากมหาวิทยาลัยต่างประเทศ

    ทำงาน 2 ชั้น:
      1) ถ้าตาราง `instructor_education` มีข้อมูลแล้ว → ใช้ SQL query ตรง ๆ
         (level='doctorate' AND is_thailand=0) ผลลัพธ์แน่นอน ไม่มีการเดา
      2) ถ้าตารางยังว่าง (DB เก่าที่ยังไม่ได้รัน seed_education) → ถอยไปใช้
         heuristic เดิมด้านล่าง เพื่อไม่ให้พฤติกรรมเก่าพังระหว่างย้ายข้อมูล

    seed ข้อมูลชั้นที่ 1 ด้วย:  python -m src.database.seed_education
    """
    if count_education_rows() > 0:
        return _query_instructors_by_doctorate(0)
    return _find_foreign_phd_by_heuristic()


def _find_foreign_phd_by_heuristic() -> list[dict]:
    """(fallback เดิม) เดาจากสตริง education — ใช้เมื่อยังไม่มีข้อมูล structured

    ใช้แทน 'graph query' แบบง่าย ๆ — filter บน structured attribute (title + education)
    ข้ามทุก entity แทนที่จะพึ่ง similarity search แบบ RAG (ดู retriever.py: fetch_from_sqlite_kg_foreign_phd)

    วิธีตัดสิน (เรียงตามความมั่นใจจากมากไปน้อย):
    1) กรองด้วย title/title_short ก่อนว่ามีคำ "ดร" ไหม (ธรรมเนียมวิชาการไทย —
       คนที่ไม่ได้ถือปริญญาเอกจะไม่มี "ดร." นำหน้าชื่อ) คนที่ title ไม่มี "ดร"
       จะไม่ถูกนับเลย ไม่ว่า education จะเขียนยังไง
    2) ในบรรดาคนที่ผ่านข้อ 1 — แยก education เป็นใบ ๆ ด้วย "|" (พบจากข้อมูลจริงว่า
       ลำดับใบในสตริงไม่คงที่ บางคนเรียงเอก→โท→ตรี บางคนเรียงตรี→โท→เอก
       จึง 'เดาจากตำแหน่งใบ' ไม่ได้เลย ต้องหา marker จริง)
       - ถ้ามีใบที่ระบุระดับปริญญาเอกชัดเจน (มี PHD_KEYWORDS) → ดูว่าใบนั้นมีชื่อ
         มหาวิทยาลัยไทยไหม ไม่มี = ต่างประเทศ
       - ถ้าไม่มีใบไหนระบุระดับเลย (พบบ่อยในข้อมูลจริง) → เดาได้เฉพาะกรณีชัวร์สุด:
         ทุกใบเป็นมหาวิทยาลัยต่างประเทศล้วน ๆ (ไม่มีมหาวิทยาลัยไทยปนเลยสักใบ)
         → ถือว่าเอกต่างประเทศ ถ้าทุกใบเป็นไทยล้วน → ถือว่าเอกไทย
         ถ้า "ผสม" (มีทั้งไทยและนอก) แต่ไม่มี marker บอกระดับ → เข้าข่าย "ไม่แน่ใจ"
         ไม่เดา ไม่ใส่ในผลลัพธ์ (ดู find_ambiguous_phd_origin() สำหรับดูรายชื่อกลุ่มนี้)

    ตัวอย่างคำถามที่ใช้ฟังก์ชันนี้: 'อาจารย์ที่ปรึกษาที่จบปริญญาเอกจากต่างประเทศมีใครบ้าง'
    """
    result = []
    for inst in list_instructors_with_education():
        title_text = f"{inst.get('title') or ''} {inst.get('title_short') or ''}"
        if "ดร" not in title_text:
            continue  # ไม่มีคำนำหน้า ดร. → ไม่ถือว่ามีปริญญาเอก ไม่ต้องเช็คต่อ

        edu = inst.get("education") or ""
        degrees = [d.strip() for d in edu.split("|") if d.strip()]
        if not degrees:
            continue

        phd_entries = [d for d in degrees if any(kw in d for kw in PHD_KEYWORDS)]
        if phd_entries:
            # มี marker ชัดเจน → เช็คเฉพาะใบที่เป็นปริญญาเอกจริง ๆ
            is_foreign = any(
                not any(t in d for t in THAI_UNIVERSITY_KEYWORDS)
                for d in phd_entries
            )
            if is_foreign:
                result.append(inst)
            continue

        # ไม่มี marker เลยสักใบ → เดาได้เฉพาะกรณีชัวร์สุด (ทุกใบไปทางเดียวกัน)
        all_foreign = all(
            not any(t in d for t in THAI_UNIVERSITY_KEYWORDS) for d in degrees
        )
        if all_foreign:
            result.append(inst)
        # ทุกใบเป็นไทยล้วน หรือผสมโดยไม่มี marker → ไม่นับ (กรณีผสมไปดูที่
        # find_ambiguous_phd_origin() แทน)

    return result


def find_ambiguous_phd_origin() -> list[dict]:
    """อาจารย์ที่ title มี 'ดร' (ถือปริญญาเอกแน่ ๆ) แต่ education มีทั้งใบไทย+นอกปน
    กันโดยไม่มี marker ระบุระดับปริญญาเลยสักใบ — เดาไม่ได้ว่าใบไหนคือปริญญาเอก
    ใช้ debug/ตรวจสอบด้วยตา ไม่ได้ถูกเรียกใช้จริงใน retriever.py
    (คนกลุ่มนี้ "ไม่ถูกนับ" อยู่ใน find_foreign_phd_instructors() เพื่อกันฟันธงผิด)
    """
    result = []
    for inst in list_instructors_with_education():
        title_text = f"{inst.get('title') or ''} {inst.get('title_short') or ''}"
        if "ดร" not in title_text:
            continue
        edu = inst.get("education") or ""
        degrees = [d.strip() for d in edu.split("|") if d.strip()]
        if not degrees:
            continue
        if any(any(kw in d for kw in PHD_KEYWORDS) for d in degrees):
            continue  # มี marker ชัดเจนแล้ว ไม่ใช่กรณีคลุมเครือ
        has_foreign = any(
            not any(t in d for t in THAI_UNIVERSITY_KEYWORDS) for d in degrees
        )
        has_thai = any(any(t in d for t in THAI_UNIVERSITY_KEYWORDS) for d in degrees)
        if has_foreign and has_thai:
            result.append(inst)
    return result


def find_course(code: str) -> Optional[dict]:
    """ค้นหารายวิชาด้วยรหัส"""
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM courses WHERE code = ?", (code,))
        row = cur.fetchone()
        return dict(row) if row else None


def find_form(code: str) -> Optional[dict]:
    """ค้นหา NU form"""
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM nu_forms WHERE code = ?", (code.upper(),))
        row = cur.fetchone()
        return dict(row) if row else None

def list_forms() -> list[dict]:
    """รายการ NU forms ทั้งหมด"""
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM nu_forms ORDER BY code")
        return [dict(r) for r in cur.fetchall()]

def log_conversation(
    user_id: str, question: str, answer: str, sources: str = "", confidence: float = 0.0
):
    """บันทึก conversation log"""
    with db_session() as conn:
        conn.execute(
            """INSERT INTO conversations
               (user_id, question, answer, sources, confidence)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, question, answer, sources, confidence),
        )


def list_staff() -> list[dict]:
    """ดึงรายชื่อเจ้าหน้าที่ทั้งหมด"""
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM staff ORDER BY id").fetchall()
        return [dict(row) for row in rows]


# ─── course_instructors: ใครสอนวิชาอะไร (schema พร้อม ยังไม่มีข้อมูลจริง) ───


def add_teaching_assignment(
    course_code: str,
    instructor_name: str,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    role: str = "ผู้สอน",
) -> bool:
    """เพิ่มข้อมูล 'อาจารย์คนนี้สอนวิชานี้' — ยังไม่มีข้อมูลจริงตอนสร้าง schema นี้
    ใช้ตอนกรอกข้อมูลจริงทีหลัง เช่น:
        from src.database.sqlite_db import add_teaching_assignment
        add_teaching_assignment("254171", "สัญญา", semester="1", academic_year="2568")

    ค้นหา instructor_name ด้วย find_instructor() (LIKE match) เหมือนฟังก์ชันอื่น ๆ
    คืน True ถ้าเพิ่มสำเร็จ, False ถ้าหาชื่ออาจารย์ไม่เจอ
    (ไม่เช็คว่า course_code มีอยู่ใน courses จริงไหม — เพิ่มได้แม้ course ยังไม่ได้กรอก
    เพื่อความยืดหยุ่นตอนทยอยกรอกข้อมูล)
    """
    inst = find_instructor(instructor_name)
    if not inst:
        return False
    with db_session() as conn:
        conn.execute(
            """INSERT INTO course_instructors
               (course_code, instructor_id, semester, academic_year, role)
               VALUES (?, ?, ?, ?, ?)""",
            (course_code, inst["id"], semester, academic_year, role),
        )
        return True


def find_instructors_by_course(course_code: str) -> list[dict]:
    """หาว่าอาจารย์คนไหนสอนวิชานี้บ้าง (join course_instructors + instructors)"""
    with db_session() as conn:
        cur = conn.execute(
            """SELECT i.*, ci.semester, ci.academic_year, ci.role
               FROM course_instructors ci
               JOIN instructors i ON i.id = ci.instructor_id
               WHERE ci.course_code = ?
               ORDER BY ci.academic_year DESC, ci.semester""",
            (course_code,),
        )
        return [dict(r) for r in cur.fetchall()]


def find_courses_by_instructor(instructor_name: str) -> list[dict]:
    """หาว่าอาจารย์คนนี้สอนวิชาอะไรบ้าง (join course_instructors + courses)"""
    inst = find_instructor(instructor_name)
    if not inst:
        return []
    with db_session() as conn:
        cur = conn.execute(
            """SELECT c.*, ci.semester, ci.academic_year, ci.role
               FROM course_instructors ci
               JOIN courses c ON c.code = ci.course_code
               WHERE ci.instructor_id = ?
               ORDER BY ci.academic_year DESC, ci.semester""",
            (inst["id"],),
        )
        return [dict(r) for r in cur.fetchall()]


if __name__ == "__main__":
    init_database()
    print("\n📊 ทดสอบ functions:")
    print(f"   instructors: {len(list_instructors())} คน")
    print(f"   instructors ที่มี education: {len(list_instructors_with_education())} คน")

    print("\n🌍 heuristic: อาจารย์จบเอกต่างประเทศ (มั่นใจ):")
    foreign = find_foreign_phd_instructors()
    print(f"   พบ {len(foreign)} คน")
    for inst in foreign:
        print(f"      - {inst['title_short']} {inst['name']}")

    ambiguous = find_ambiguous_phd_origin()
    if ambiguous:
        print(f"\n⚠️  ไม่แน่ใจ (มี ดร. แต่ education มีทั้งไทย+นอกปน ไม่มี marker บอกระดับ): {len(ambiguous)} คน")
        print("   ตรวจด้วยตาว่าใบไหนคือปริญญาเอกจริง แล้วเติมคำเช่น 'คุณวุฒิ ปร.ด.' ในใบนั้น")
        print("   ในฐานข้อมูล (ผ่าน update_instructor_education) เพื่อให้ระบบจัดกลุ่มถูกอัตโนมัติ")
        for inst in ambiguous:
            print(f"      - {inst['title_short']} {inst['name']}")
            print(f"        education: {inst['education']}")
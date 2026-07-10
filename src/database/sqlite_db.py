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


if __name__ == "__main__":
    init_database()
    print("\n📊 ทดสอบ functions:")
    print(f"   instructors: {len(list_instructors())} คน")
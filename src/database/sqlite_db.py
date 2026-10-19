import sqlite3
from contextlib import contextmanager
from typing import Optional
from src.config import SQLITE_PATH


def get_connection() -> sqlite3.Connection:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000") 
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
    existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def init_database():
    with db_session() as conn:
        cur = conn.cursor()

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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS important_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT,
                description TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS faq_quick (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                keywords TEXT,
                category TEXT
            )
        """)

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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS registrar_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                faculties TEXT
            )
        """)

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

    print(f"สร้าง SQLite tables ที่: {SQLITE_PATH}")


def find_instructor(name: str) -> Optional[dict]:
    with db_session() as conn:
        cur = conn.execute(
            "SELECT * FROM instructors WHERE name LIKE ? LIMIT 1", (f"%{name}%",)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def list_instructors() -> list[dict]:
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM instructors ORDER BY title, name")
        return [dict(r) for r in cur.fetchall()]


def update_instructor_education(name: str, education: str) -> bool:
    with db_session() as conn:
        cur = conn.execute(
            "UPDATE instructors SET education = ? WHERE name LIKE ?",
            (education, f"%{name}%"),
        )
        return cur.rowcount > 0


def list_instructors_with_education() -> list[dict]:
    with db_session() as conn:
        cur = conn.execute(
            "SELECT * FROM instructors "
            "WHERE education IS NOT NULL AND TRIM(education) != '' "
            "ORDER BY name"
        )
        return [dict(r) for r in cur.fetchall()]

LEVEL_DOCTORATE = "doctorate"
LEVEL_MASTER = "master"
LEVEL_BACHELOR = "bachelor"
VALID_LEVELS = {LEVEL_DOCTORATE, LEVEL_MASTER, LEVEL_BACHELOR}

_THAILAND_VALUES = {"ไทย", "ประเทศไทย", "thailand", "th", "tha"}

_LEVEL_LABEL_TH = {
    LEVEL_DOCTORATE: "ปริญญาเอก",
    LEVEL_MASTER: "ปริญญาโท",
    LEVEL_BACHELOR: "ปริญญาตรี",
}


def is_thailand_country(country: Optional[str]) -> bool:
    if not country:
        return False
    return country.strip().lower() in _THAILAND_VALUES


def set_instructor_education(name_or_staff_id: str, degrees: list[dict]) -> bool:
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
    with db_session() as conn:
        return conn.execute("SELECT COUNT(*) FROM instructor_education").fetchone()[0]


def list_education_rows(instructor_id: Optional[int] = None) -> list[dict]:
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
    return _query_instructors_by_doctorate(1)


def find_instructors_without_doctorate() -> list[dict]:
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
    "ราชภัฏ",           
    "ราชมงคล",          
    "อัสสัมชัญ",         
    "พระจอมเกล้า",       
    "ศรีนครินทรวิโรฒ",
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
PHD_KEYWORDS = [
    "ปริญญาเอก", "ปร.ด", "Ph.D", "PhD", "ดุษฎีบัณฑิต", "ระดับปริญญาเอก",
    "วศ.ด", "วท.ด", "ค.ด", "ทล.ด", "รป.ด", "บธ.ด",
    "ศศ.ด", "สศ.ด", "พย.ด", "กศ.ด", "นบ.ด",
    "D.Eng", "Sc.D", "Ed.D", "DBA", "Doctor of",
]


def find_foreign_phd_instructors() -> list[dict]:
    if count_education_rows() > 0:
        return _query_instructors_by_doctorate(0)
    return _find_foreign_phd_by_heuristic()


def _find_foreign_phd_by_heuristic() -> list[dict]:
    result = []
    for inst in list_instructors_with_education():
        title_text = f"{inst.get('title') or ''} {inst.get('title_short') or ''}"
        if "ดร" not in title_text:
            continue  

        edu = inst.get("education") or ""
        degrees = [d.strip() for d in edu.split("|") if d.strip()]
        if not degrees:
            continue

        phd_entries = [d for d in degrees if any(kw in d for kw in PHD_KEYWORDS)]
        if phd_entries:
            is_foreign = any(
                not any(t in d for t in THAI_UNIVERSITY_KEYWORDS)
                for d in phd_entries
            )
            if is_foreign:
                result.append(inst)
            continue
        all_foreign = all(
            not any(t in d for t in THAI_UNIVERSITY_KEYWORDS) for d in degrees
        )
        if all_foreign:
            result.append(inst)

    return result


def find_ambiguous_phd_origin() -> list[dict]:
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
            continue  
        has_foreign = any(
            not any(t in d for t in THAI_UNIVERSITY_KEYWORDS) for d in degrees
        )
        has_thai = any(any(t in d for t in THAI_UNIVERSITY_KEYWORDS) for d in degrees)
        if has_foreign and has_thai:
            result.append(inst)
    return result


def find_course(code: str) -> Optional[dict]:
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM courses WHERE code = ?", (code,))
        row = cur.fetchone()
        return dict(row) if row else None


def find_form(code: str) -> Optional[dict]:
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM nu_forms WHERE code = ?", (code.upper(),))
        row = cur.fetchone()
        return dict(row) if row else None

def list_forms() -> list[dict]:
    with db_session() as conn:
        cur = conn.execute("SELECT * FROM nu_forms ORDER BY code")
        return [dict(r) for r in cur.fetchall()]

def log_conversation(
    user_id: str, question: str, answer: str, sources: str = "", confidence: float = 0.0
):
    with db_session() as conn:
        conn.execute(
            """INSERT INTO conversations
               (user_id, question, answer, sources, confidence)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, question, answer, sources, confidence),
        )


def list_staff() -> list[dict]:
    with db_session() as conn:
        rows = conn.execute("SELECT * FROM staff ORDER BY id").fetchall()
        return [dict(row) for row in rows]

def add_teaching_assignment(
    course_code: str,
    instructor_name: str,
    semester: Optional[str] = None,
    academic_year: Optional[str] = None,
    role: str = "ผู้สอน",
) -> bool:
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
    print("\n ทดสอบ functions:")
    print(f"   instructors: {len(list_instructors())} คน")
    print(f"   instructors ที่มี education: {len(list_instructors_with_education())} คน")

    print("\n heuristic: อาจารย์จบเอกต่างประเทศ (มั่นใจ):")
    foreign = find_foreign_phd_instructors()
    print(f"   พบ {len(foreign)} คน")
    for inst in foreign:
        print(f"      - {inst['title_short']} {inst['name']}")

    ambiguous = find_ambiguous_phd_origin()
    if ambiguous:
        print(f"\n  ไม่แน่ใจ (มี ดร. แต่ education มีทั้งไทย+นอกปน ไม่มี marker บอกระดับ): {len(ambiguous)} คน")
        print("   ตรวจด้วยตาว่าใบไหนคือปริญญาเอกจริง แล้วเติมคำเช่น 'คุณวุฒิ ปร.ด.' ในใบนั้น")
        print("   ในฐานข้อมูล (ผ่าน update_instructor_education) เพื่อให้ระบบจัดกลุ่มถูกอัตโนมัติ")
        for inst in ambiguous:
            print(f"      - {inst['title_short']} {inst['name']}")
            print(f"        education: {inst['education']}")
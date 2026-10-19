import sqlite3
import time
import contextlib
from pathlib import Path
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "csit.db"  


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_chat_log() -> None:
    with contextlib.closing(_connect()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS chat_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT    NOT NULL,
                question    TEXT    NOT NULL,
                answer      TEXT,
                route       TEXT,                        -- loan_redirect/instructor/contact/RAG/error
                answered    INTEGER NOT NULL DEFAULT 0,  -- 0 = ตอบไม่ได้, 1 = ตอบได้ (SQLite ไม่มี bool)
                created_at  REAL    NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_logs_answered ON chat_logs (answered);
            CREATE INDEX IF NOT EXISTS idx_logs_time     ON chat_logs (created_at);
            """
        )
        conn.commit()


def log_chat(user_id: str, question: str, answer: str,
             route: str, answered: bool) -> None:
    with contextlib.closing(_connect()) as conn:
        conn.execute(
            "INSERT INTO chat_logs (user_id, question, answer, route, answered, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, question, answer, route, int(answered), time.time()),
        )
        conn.commit()

def unanswered_questions(limit: int = 50) -> list[dict]:
    cols = ["id", "user_id", "question", "route", "at"]
    with contextlib.closing(_connect()) as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, question, route,
                   datetime(created_at, 'unixepoch', 'localtime') AS at
            FROM chat_logs
            WHERE answered = 0
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(zip(cols, r)) for r in rows]


def answer_rate() -> dict:
    with contextlib.closing(_connect()) as conn:
        total, answered = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(answered), 0) FROM chat_logs"
        ).fetchone()
    rate = (answered / total * 100) if total else 0.0
    return {
        "total": total,
        "answered": answered,
        "unanswered": total - answered,
        "rate_percent": round(rate, 1),
    }

if __name__ == "__main__":
    init_chat_log()
    print("answer rate:", answer_rate())
    print("unanswered:", unanswered_questions(10))
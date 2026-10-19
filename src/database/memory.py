"""
src/database/memory.py

"""

import sqlite3
import time
import contextlib
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "csit.db"

MAX_MESSAGES = 6              
SESSION_WINDOW = 30 * 60     
RETENTION_DAYS = 30        


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")   
    conn.execute("PRAGMA busy_timeout=5000;")  
    return conn


def init_memory() -> None:
    with contextlib.closing(_connect()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT    NOT NULL,
                role        TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
                content     TEXT    NOT NULL,
                created_at  REAL    NOT NULL          -- unix timestamp
            );
            CREATE INDEX IF NOT EXISTS idx_conv_user_time
                ON conversation_memory (user_id, created_at);
            """
        )
        conn.commit()


def add_message(user_id: str, role: str, content: str) -> None:
    with contextlib.closing(_connect()) as conn:
        conn.execute(
            "INSERT INTO conversation_memory (user_id, role, content, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, role, content, time.time()),
        )
        conn.commit()


def get_history(user_id: str) -> list[dict]:
    cutoff = time.time() - SESSION_WINDOW
    with contextlib.closing(_connect()) as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM conversation_memory
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, cutoff, MAX_MESSAGES),
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def clear_history(user_id: str) -> None:
    with contextlib.closing(_connect()) as conn:
        conn.execute("DELETE FROM conversation_memory WHERE user_id = ?", (user_id,))
        conn.commit()


def prune(retention_days: int = RETENTION_DAYS) -> int:
    cutoff = time.time() - retention_days * 86400
    with contextlib.closing(_connect()) as conn:
        cur = conn.execute(
            "DELETE FROM conversation_memory WHERE created_at < ?", (cutoff,)
        )
        conn.commit()
        return cur.rowcount

if __name__ == "__main__":
    init_memory()
    uid = "test_user"
    clear_history(uid)
    add_message(uid, "user", "NU18 คืออะไร")
    add_message(uid, "assistant", "NU18 คือคำร้องทั่วไป")
    add_message(uid, "user", "แล้วยื่นยังไง")
    print(get_history(uid))
    print("pruned:", prune())
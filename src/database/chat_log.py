"""
src/database/chat_log.py

บันทึกบทสนทนาแบบถาวรเพื่อ "วิเคราะห์" — คนละวัตถุประสงค์กับ conversation_memory
- 1 แถว = 1 เทิร์น: เก็บ question / answer แยกคอลัมน์ + route + ธง answered
- ใช้ดูว่าคำถามไหน "ตอบไม่ได้" และคำนวณ answer rate ได้ด้วย SQL
- ไม่ถูก prune (เก็บถาวรสำหรับสถิติ/รายงาน)

หมายเหตุ: ตารางนี้เป็น log ฝั่ง local คู่ขนานกับที่ส่งไป n8n/Google Sheets
ข้อดีคือ query ได้ทันที และรอดแม้ n8n ล่ม (send_log_to_n8n เป็น fire-and-forget)
"""

import sqlite3
import time
import contextlib
from pathlib import Path

# ใช้ path เดียวกับ memory.py (ชี้ data/csit.db)
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "csit.db"  # ใช้ไฟล์เดียวกับ memory/seed_data


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_chat_log() -> None:
    """เรียกครั้งเดียวตอนสตาร์ทแอป (สร้างตาราง + index ถ้ายังไม่มี)"""
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
    """บันทึก 1 เทิร์น (เรียกหลังตอบ LINE เสร็จ)"""
    with contextlib.closing(_connect()) as conn:
        conn.execute(
            "INSERT INTO chat_logs (user_id, question, answer, route, answered, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, question, answer, route, int(answered), time.time()),
        )
        conn.commit()


# ── ฟังก์ชันวิเคราะห์ (ตอบโจทย์ "ดูว่าคำถามไหนตอบไม่ได้") ──

def unanswered_questions(limit: int = 50) -> list[dict]:
    """ดึงคำถามที่บอทตอบไม่ได้ (answered = 0) ล่าสุด"""
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
    """คำนวณ answer rate รวม (ตอบได้กี่ %)"""
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


# ทดสอบเร็ว ๆ: python -m src.database.chat_log
if __name__ == "__main__":
    init_chat_log()
    print("answer rate:", answer_rate())
    print("unanswered:", unanswered_questions(10))
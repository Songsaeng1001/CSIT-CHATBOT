"""
src/database/memory.py

Conversation memory แบบ persist ด้วย SQLite (แทน deque ใน RAM)
- แยกประวัติตาม user_id
- เก็บไว้ "6 ข้อความล่าสุด" (3 เทิร์น) เหมือน deque(maxlen=6) เดิม
- มี session window 30 นาที: ข้อความที่เก่ากว่านั้นถือว่าเป็นบริบทค้าง ไม่ดึงมาใช้
- มี prune() สำหรับ retention (PDPA) ลบประวัติที่เก่ามาก

ใช้ไฟล์ .db เดียวกับ seed_data ได้เลย แค่ชี้ DB_PATH ให้ตรง
"""

import sqlite3
import time
import contextlib
from pathlib import Path

# ── ปรับให้ตรงกับ DB เดิมของคุณ (ตัวเดียวกับ NU form / อาจารย์ ก็ได้) ──
DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "csit.db"

MAX_MESSAGES = 6              # เก็บ 6 ข้อความล่าสุด = 3 เทิร์น (เท่ากับ maxlen เดิม)
SESSION_WINDOW = 30 * 60     # 30 นาที (วินาที) — เก่ากว่านี้ถือว่า session ใหม่
RETENTION_DAYS = 30          # ลบประวัติที่เก่ากว่านี้ (PDPA)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")   # อ่าน/เขียนพร้อมกันไม่ล็อกทั้งไฟล์
    conn.execute("PRAGMA busy_timeout=5000;")  # รอ lock ได้สูงสุด 5 วิ
    return conn


def init_memory() -> None:
    """เรียกครั้งเดียวตอนสตาร์ทแอป (สร้างตาราง + index ถ้ายังไม่มี)"""
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
    """บันทึก 1 ข้อความ (role = 'user' หรือ 'assistant')"""
    with contextlib.closing(_connect()) as conn:
        conn.execute(
            "INSERT INTO conversation_memory (user_id, role, content, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, role, content, time.time()),
        )
        conn.commit()


def get_history(user_id: str) -> list[dict]:
    """
    คืนประวัติล่าสุดของ user (ไม่เกิน MAX_MESSAGES ข้อความ และอยู่ใน SESSION_WINDOW)
    เรียงจากเก่า -> ใหม่ พร้อมส่งให้ retriever/Gemini ต่อได้เลย
    รูปแบบ: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
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
    # ดึงมาแบบใหม่->เก่า แล้วพลิกกลับให้เป็นเก่า->ใหม่
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def clear_history(user_id: str) -> None:
    """ลบประวัติของ user คนเดียว (เช่นผู้ใช้พิมพ์ /reset หรือ 'เริ่มใหม่')"""
    with contextlib.closing(_connect()) as conn:
        conn.execute("DELETE FROM conversation_memory WHERE user_id = ?", (user_id,))
        conn.commit()


def prune(retention_days: int = RETENTION_DAYS) -> int:
    """
    ลบประวัติที่เก่ากว่า retention_days (housekeeping / PDPA)
    คืนจำนวนแถวที่ถูกลบ — เรียกตอนสตาร์ท หรือให้ n8n ยิงตามเวลาก็ได้
    """
    cutoff = time.time() - retention_days * 86400
    with contextlib.closing(_connect()) as conn:
        cur = conn.execute(
            "DELETE FROM conversation_memory WHERE created_at < ?", (cutoff,)
        )
        conn.commit()
        return cur.rowcount


# ทดสอบเร็ว ๆ: python -m src.database.memory
if __name__ == "__main__":
    init_memory()
    uid = "test_user"
    clear_history(uid)
    add_message(uid, "user", "NU18 คืออะไร")
    add_message(uid, "assistant", "NU18 คือคำร้องทั่วไป")
    add_message(uid, "user", "แล้วยื่นยังไง")
    print(get_history(uid))
    print("pruned:", prune())
"""
Configuration Manager
โหลด config จาก .env แล้วใช้ได้ทั่วโปรเจค
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# โหลด .env
load_dotenv()

# ─── Project Paths ─────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"
LOGS_DIR = PROJECT_ROOT / "logs"
RULES_PATH = PROJECT_ROOT / "rules.yaml"

# ─── LLM Provider ──────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── LINE ──────────────────────────────────
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

# ─── Vector DB ─────────────────────────────
CHROMA_DIR = PROJECT_ROOT / os.getenv("CHROMA_DIR", "chroma_db").lstrip("./")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "csit_knowledge")

# ─── SQLite ────────────────────────────────
SQLITE_PATH = PROJECT_ROOT / os.getenv("SQLITE_PATH", "data/csit.db").lstrip("./")

# ─── Embedding ─────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")

# ─── App ───────────────────────────────────
APP_ENV = os.getenv("APP_ENV", "development")
APP_NAME = os.getenv("APP_NAME", "nong-csit-chatbot")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PORT = int(os.getenv("PORT", "8000"))

# ─── n8n (optional) ────────────────────────
N8N_WEBHOOK_LOG = os.getenv("N8N_WEBHOOK_LOG", "")
N8N_WEBHOOK_ALERT = os.getenv("N8N_WEBHOOK_ALERT", "")


def validate_config() -> bool:
    """ตรวจสอบว่ามี config จำเป็นครบไหม"""
    issues = []
    
    if not GOOGLE_API_KEY and not OPENAI_API_KEY:
        issues.append("❌ ต้องมี GOOGLE_API_KEY หรือ OPENAI_API_KEY")
    
    if not LINE_CHANNEL_SECRET and APP_ENV == "production":
        issues.append("⚠️  LINE_CHANNEL_SECRET ยังไม่ตั้ง (จำเป็นใน production)")
    
    if issues:
        print("\n".join(issues))
        return False
    
    return True


def print_config():
    """แสดง config ปัจจุบัน (ซ่อน secret)"""
    print("=" * 60)
    print(f"🤖 {APP_NAME}")
    print("=" * 60)
    print(f"📂 PROJECT_ROOT  : {PROJECT_ROOT}")
    print(f"📂 KNOWLEDGE_DIR : {KNOWLEDGE_DIR}")
    print(f"💾 CHROMA_DIR    : {CHROMA_DIR}")
    print(f"💾 SQLITE_PATH   : {SQLITE_PATH}")
    print(f"🧠 EMBEDDING     : {EMBEDDING_MODEL}")
    print(f"🌍 ENV           : {APP_ENV}")
    print(f"🔑 GOOGLE_KEY    : {'✅ มี' if GOOGLE_API_KEY else '❌ ไม่มี'}")
    print(f"🔑 OPENAI_KEY    : {'✅ มี' if OPENAI_API_KEY else '❌ ไม่มี'}")
    print(f"🔑 LINE_TOKEN    : {'✅ มี' if LINE_CHANNEL_ACCESS_TOKEN else '❌ ไม่มี'}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
    if validate_config():
        print("\n✅ Config พร้อมใช้งาน")
    else:
        print("\n⚠️  ต้องตั้งค่าเพิ่ม")
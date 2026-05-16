"""
ตรวจสอบว่าติดตั้งครบและพร้อมใช้
"""

import sys
import platform

print("=" * 60)
print(f"🐍 Python: {sys.version}")
print(f"🍎 Platform: {platform.platform()}")
print(f"💻 Machine: {platform.machine()}")
print("=" * 60)

packages = [
    ("langchain", "LangChain core"),
    ("langchain_community", "LangChain community"),
    ("langchain_chroma", "Chroma integration"),
    ("langchain_huggingface", "HuggingFace integration"),
    ("langchain_google_genai", "Google Gemini"),
    ("chromadb", "ChromaDB"),
    ("sentence_transformers", "Sentence Transformers"),
    ("linebot", "LINE SDK"),
    ("fastapi", "FastAPI"),
    ("uvicorn", "Uvicorn"),
    ("docx", "python-docx"),
    ("pypdf", "pypdf"),
    ("dotenv", "python-dotenv"),
    ("yaml", "PyYAML"),
    ("tqdm", "tqdm"),
    ("loguru", "Loguru"),
]

success, fail = 0, 0

for pkg, desc in packages:
    try:
        mod = __import__(pkg)
        version = getattr(mod, "__version__", "?")
        print(f"✅ {pkg:30s} {version:15s} — {desc}")
        success += 1
    except ImportError:
        print(f"❌ {pkg:30s} {'(ไม่พบ)':15s} — {desc}")
        fail += 1

print("=" * 60)
print(f"📊 สำเร็จ {success}/{len(packages)}  |  ผิดพลาด {fail}")
print("=" * 60)

if fail > 0:
    print("\n💡 ติดตั้งเพิ่ม: pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n🎉 พร้อมเริ่มเขียนโค้ดแล้ว!")
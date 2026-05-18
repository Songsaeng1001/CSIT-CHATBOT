"""
สคริปต์สร้าง Vector Database จากเอกสารใน knowledge_base/

รันครั้งเดียวก่อนใช้ chatbot:
    python -m src.ingest

ถ้าอยากสร้างใหม่ทั้งหมด (ลบของเก่า):
    python -m src.ingest --reset
"""

import sys
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import KNOWLEDGE_DIR
from src.database import vector_db


# ─── ตั้งค่าการ Split ─────────────────────────
CHUNK_SIZE = 500        # ตัวอักษรต่อ chunk
CHUNK_OVERLAP = 80      # ส่วนซ้อนทับกัน

# Separators ที่เหมาะกับภาษาไทย
SEPARATORS = [
    "\n## ",       # หัวข้อใหญ่
    "\n### ",      # หัวข้อย่อย
    "\n\n",        # paragraph
    "\n",          # บรรทัด
    "。",          # จุดญี่ปุ่น (เผื่อ)
    " ",           # ช่องว่าง
    "",            # ตัวอักษร (fallback)
]


def load_documents():
    """โหลดไฟล์ .md ทั้งหมดใน knowledge_base/"""
    print("=" * 60)
    print(f"📂 โหลดเอกสารจาก: {KNOWLEDGE_DIR}")
    print("=" * 60)
    
    if not KNOWLEDGE_DIR.exists():
        print(f"❌ ไม่พบโฟลเดอร์: {KNOWLEDGE_DIR}")
        sys.exit(1)
    
    loader = DirectoryLoader(
        str(KNOWLEDGE_DIR),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    
    documents = loader.load()
    
    if not documents:
        print("❌ ไม่พบไฟล์ .md ในโฟลเดอร์")
        sys.exit(1)
    
    # แสดงรายการไฟล์
    print(f"\n✅ โหลดสำเร็จ {len(documents)} ไฟล์:")
    for doc in documents:
        filename = Path(doc.metadata["source"]).name
        chars = len(doc.page_content)
        print(f"   📄 {filename:30s} {chars:>6,} ตัวอักษร")
    
    return documents


def split_documents(documents):
    """แบ่งเอกสารเป็น chunks เล็กๆ"""
    print()
    print("=" * 60)
    print(f"✂️  ตัด chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print("=" * 60)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = splitter.split_documents(documents)
    
    print(f"✅ ได้ทั้งหมด {len(chunks)} chunks")
    
    # สถิติขนาด chunk
    sizes = [len(c.page_content) for c in chunks]
    avg = sum(sizes) // len(sizes)
    print(f"   ขนาดเฉลี่ย: {avg} ตัวอักษร")
    print(f"   เล็กสุด: {min(sizes)} | ใหญ่สุด: {max(sizes)}")
    
    # นับ chunks ต่อไฟล์
    from collections import Counter
    file_counts = Counter(
        Path(c.metadata["source"]).name for c in chunks
    )
    print("\n   📊 จำนวน chunks ต่อไฟล์:")
    for filename, count in sorted(file_counts.items()):
        print(f"      {filename:30s} {count} chunks")
    
    return chunks


def ingest(reset: bool = False):
    """กระบวนการ ingest หลัก"""
    
    # ─── Step 0: Reset ถ้าระบุ ───
    if reset:
        print("⚠️  Reset mode: ลบ collection เก่าก่อน")
        vector_db.reset_collection()
        print()
    
    # ─── Step 1: Load ───
    documents = load_documents()
    
    # ─── Step 2: Split ───
    chunks = split_documents(documents)
    
    # ─── Step 3: Embed + Save ───
    print()
    print("=" * 60)
    print("💾 สร้าง embeddings + บันทึก Chroma")
    print("=" * 60)
    
    added = vector_db.add_documents(chunks)
    
    # ─── Step 4: Verify ───
    total = vector_db.count_documents()
    
    print(f"\n✅ เพิ่ม {added} chunks เข้า Chroma")
    print(f"   รวมทั้งหมดใน collection: {total} chunks")
    
    print()
    print("=" * 60)
    print("🎉 Ingest สำเร็จ! พร้อมใช้งานแล้ว")
    print("=" * 60)
    print()
    print("ทดสอบต่อด้วย:")
    print("   python -m tests.test_retrieval")
    print("   python -m tests.test_rag")


def main():
    """Entry point"""
    reset = "--reset" in sys.argv
    ingest(reset=reset)


if __name__ == "__main__":
    main()
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


from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

CHUNK_SIZE = 1000        
CHUNK_OVERLAP = 120

HEADERS_TO_SPLIT_ON = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

SEPARATORS = ["\n\n", "\n", "。", " ", ""]


def load_documents():
    print("=" * 60)
    print(f" โหลดเอกสารจาก: {KNOWLEDGE_DIR}")
    print("=" * 60)
    
    if not KNOWLEDGE_DIR.exists():
        print(f" ไม่พบโฟลเดอร์: {KNOWLEDGE_DIR}")
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
        print(" ไม่พบไฟล์ .md ในโฟลเดอร์")
        sys.exit(1)
    
    print(f"\n โหลดสำเร็จ {len(documents)} ไฟล์:")
    for doc in documents:
        filename = Path(doc.metadata["source"]).name
        chars = len(doc.page_content)
        print(f"    {filename:30s} {chars:>6,} ตัวอักษร")
    
    return documents


def split_documents(documents):
    print()
    print("=" * 60)
    print(f"  ตัด chunks แบบ header-aware (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print("=" * 60)

    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=HEADERS_TO_SPLIT_ON,
        strip_headers=False,   
    )
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        length_function=len,
    )

    chunks = []
    for doc in documents:
        source = doc.metadata.get("source", "?")
        sections = md_splitter.split_text(doc.page_content)
        for s in sections:
            s.metadata["source"] = source   
        sized = char_splitter.split_documents(sections)
        for c in sized:
            path = " > ".join(
                c.metadata[k] for k in ("h1", "h2", "h3") if c.metadata.get(k)
            )
            if path and path not in c.page_content[:len(path) + 5]:
                c.page_content = f"[{path}]\n{c.page_content}"
        chunks.extend(sized)

    sizes = [len(c.page_content) for c in chunks]
    print(f" ได้ทั้งหมด {len(chunks)} chunks")
    print(f"   ขนาดเฉลี่ย: {sum(sizes)//len(sizes)} | เล็กสุด {min(sizes)} | ใหญ่สุด {max(sizes)}")

    from collections import Counter
    file_counts = Counter(Path(c.metadata["source"]).name for c in chunks)
    print("\n    chunks ต่อไฟล์:")
    for fn, ct in sorted(file_counts.items()):
        print(f"      {fn:30s} {ct} chunks")

    return chunks


def ingest(reset: bool = False):
    if reset:
        print(" Reset mode: ลบ collection เก่าก่อน")
        vector_db.reset_collection()
        print()
    
    documents = load_documents()
 
    chunks = split_documents(documents)

    print()
    print("=" * 60)
    print(" สร้าง embeddings + บันทึก Chroma")
    print("=" * 60)
    
    added = vector_db.add_documents(chunks)
    total = vector_db.count_documents()
    
    print(f"\n เพิ่ม {added} chunks เข้า Chroma")
    print(f"   รวมทั้งหมดใน collection: {total} chunks")
    
    print()
    print("=" * 60)
    print(" Ingest สำเร็จ! พร้อมใช้งานแล้ว")
    print("=" * 60)
    print()
    print("ทดสอบต่อด้วย:")
    print("   python -m tests.test_retrieval")
    print("   python -m tests.test_rag")


def main():
    reset = "--reset" in sys.argv
    ingest(reset=reset)


if __name__ == "__main__":
    main()
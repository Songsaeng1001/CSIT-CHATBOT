"""
สคริปต์สร้าง Vector Database จากเอกสารใน knowledge_base/
รันครั้งเดียวก่อนเริ่มใช้ chatbot
"""

from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ─── ตั้งค่า ─────────────────────────────────────────────
KNOWLEDGE_DIR = "knowledge_base"
CHROMA_DIR = "chroma_db"           # โฟลเดอร์เก็บ DB
COLLECTION_NAME = "csit_knowledge"

# โมเดล embedding ที่รองรับภาษาไทย
EMBEDDING_MODEL = "BAAI/bge-m3"     # ดีที่สุดสำหรับไทย
# ทางเลือก: "intfloat/multilingual-e5-large"

CHUNK_SIZE = 500       # ขนาดแต่ละ chunk (ตัวอักษร)
CHUNK_OVERLAP = 80     # ซ้อนทับกัน (ป้องกันข้อมูลขาด)


def load_documents():
    """โหลดไฟล์ .md และ .txt ทั้งหมดในโฟลเดอร์"""
    print(f"📂 โหลดเอกสารจาก: {KNOWLEDGE_DIR}")
    
    loader = DirectoryLoader(
        KNOWLEDGE_DIR,
        glob="**/*.md",                     # อ่านทุกไฟล์ .md
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"} # สำคัญสำหรับภาษาไทย!
    )
    documents = loader.load()
    print(f"   ✅ โหลดได้ {len(documents)} ไฟล์")
    return documents


def split_documents(documents):
    """แบ่งเอกสารเป็น chunks เล็กๆ"""
    print(f"✂️  แบ่งเอกสารเป็น chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # ลำดับ separator: ลองตัดที่ \n\n ก่อน ถ้าไม่ได้ค่อย \n ค่อยช่องว่าง
        separators=["\n\n", "\n", "。", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f"   ✅ ได้ทั้งหมด {len(chunks)} chunks")
    return chunks


def create_vector_store(chunks):
    """สร้าง embeddings และเก็บลง Chroma"""
    print(f"🧠 โหลด embedding model: {EMBEDDING_MODEL}")
    print("   (ครั้งแรกจะดาวน์โหลดประมาณ 2GB ใช้เวลาสักครู่...)")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},          # ถ้ามี GPU เปลี่ยนเป็น "cuda"
        encode_kwargs={"normalize_embeddings": True},
    )
    
    print(f"💾 สร้าง Vector Store ที่: {CHROMA_DIR}")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=CHROMA_DIR,            # บันทึกลง disk
    )
    
    print(f"   ✅ บันทึก {len(chunks)} vectors สำเร็จ")
    return vector_store


def main():
    print("=" * 60)
    print("🚀 เริ่มสร้าง Vector Database สำหรับน้องซีที")
    print("=" * 60)
    
    if not Path(KNOWLEDGE_DIR).exists():
        print(f"❌ ไม่พบโฟลเดอร์ {KNOWLEDGE_DIR}")
        return
    
    docs = load_documents()
    if not docs:
        print("❌ ไม่พบเอกสารในโฟลเดอร์")
        return
    
    chunks = split_documents(docs)
    vector_store = create_vector_store(chunks)
    
    print("=" * 60)
    print("✨ เสร็จสมบูรณ์! พร้อมใช้งานได้แล้ว")
    print("=" * 60)


if __name__ == "__main__":
    main()
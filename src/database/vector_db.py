"""
Vector Database Manager
จัดการ ChromaDB + Embedding model สำหรับ semantic search

โครงสร้าง:
- get_embedding_model()  : โหลดโมเดล embedding (bge-m3)
- get_vector_store()     : เปิด/สร้าง Chroma collection
- search()               : ค้นหา top-k chunks
"""

from typing import Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)

# ─── Singleton (cache โมเดลให้ใช้ซ้ำ) ──────────────
_embedding_model: Optional[HuggingFaceEmbeddings] = None
_vector_store: Optional[Chroma] = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    โหลด Embedding model (BAAI/bge-m3)
    Cache ไว้ใช้ซ้ำ ไม่ต้องโหลดทุกครั้ง

    ครั้งแรก: ดาวน์โหลด ~2.3GB (15-20 นาที)
    ครั้งต่อไป: โหลดจาก cache (10 วินาที)
    """
    global _embedding_model

    if _embedding_model is None:
        print(f"🧠 กำลังโหลด embedding model: {EMBEDDING_MODEL}")
        print("   (ครั้งแรกจะดาวน์โหลด ~2.3GB ใช้เวลาสักครู่...)")

        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},  # Mac M1+ ใช้ cpu ก็เร็ว
            encode_kwargs={
                "normalize_embeddings": True,  # ทำให้คะแนน cosine ใช้ง่าย
            },
        )
        print(f"   ✅ โหลดสำเร็จ")

    return _embedding_model


def get_vector_store() -> Chroma:
    """
    เปิด Chroma collection ที่บันทึกไว้บน disk
    ถ้ายังไม่มี จะสร้างใหม่
    """
    global _vector_store

    if _vector_store is None:
        embeddings = get_embedding_model()

        # สร้างโฟลเดอร์ถ้ายังไม่มี
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR),
        )

    return _vector_store


def add_documents(documents: list[Document]) -> int:
    """
    เพิ่ม documents เข้า Chroma
    คืน: จำนวนเอกสารที่เพิ่ม
    """
    vs = get_vector_store()
    vs.add_documents(documents)
    return len(documents)


def search(query: str, k: int = 4) -> list[tuple[Document, float]]:
    """
    ค้นหา top-k chunks ที่เกี่ยวข้องกับ query

    Args:
        query: คำถามภาษาธรรมชาติ
        k: จำนวน chunks ที่ต้องการ (default 4)

    Returns:
        List ของ (Document, similarity_score)
        score ต่ำ = ใกล้เคียงมาก (cosine distance)
    """
    vs = get_vector_store()
    return vs.similarity_search_with_score(query, k=k)


def count_documents() -> int:
    """นับจำนวน chunks ทั้งหมดใน Chroma"""
    vs = get_vector_store()
    return vs._collection.count()


def reset_collection():
    """
    ลบ collection ทั้งหมด (ใช้ตอน re-ingest)
    ⚠️ ลบข้อมูลทั้งหมด — ระวัง!
    """
    global _vector_store

    vs = get_vector_store()

    # ลบ collection
    try:
        vs._client.delete_collection(COLLECTION_NAME)
        print(f"🗑️  ลบ collection '{COLLECTION_NAME}' แล้ว")
    except Exception as e:
        print(f"⚠️  ไม่สามารถลบได้: {e}")

    # Reset singleton
    _vector_store = None


if __name__ == "__main__":
    # ทดสอบ
    print("🧪 ทดสอบ Vector DB:")
    count = count_documents()
    print(f"   จำนวน chunks ปัจจุบัน: {count}")

    if count > 0:
        print("\n🔍 ทดสอบค้นหา:")
        results = search("อาจารย์ที่ปรึกษาภาควิชา", k=2)
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n   [{i}] score: {score:.4f}")
            print(f"       source: {doc.metadata.get('source', '?')}")
            print(f"       text: {doc.page_content[:100]}...")

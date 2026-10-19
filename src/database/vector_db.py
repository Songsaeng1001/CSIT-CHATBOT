from typing import Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from src.config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)

_embedding_model: Optional[HuggingFaceEmbeddings] = None
_vector_store: Optional[Chroma] = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding_model

    if _embedding_model is None:
        print(f" กำลังโหลด embedding model: {EMBEDDING_MODEL}")
        print("   (ครั้งแรกจะดาวน์โหลด ~2.3GB ใช้เวลาสักครู่...)")

        _embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},  
            encode_kwargs={
                "normalize_embeddings": True, 
            },
        )
        print(f" โหลดสำเร็จ")

    return _embedding_model


def get_vector_store() -> Chroma:
    global _vector_store

    if _vector_store is None:
        embeddings = get_embedding_model()

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        _vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(CHROMA_DIR),
        )

    return _vector_store


def add_documents(documents: list[Document]) -> int:
    vs = get_vector_store()
    vs.add_documents(documents)
    return len(documents)


def search(query: str, k: int = 4) -> list[tuple[Document, float]]:
    vs = get_vector_store()
    return vs.similarity_search_with_score(query, k=k)


def count_documents() -> int:
    vs = get_vector_store()
    return vs._collection.count()


def reset_collection():
    global _vector_store

    vs = get_vector_store()

    try:
        vs._client.delete_collection(COLLECTION_NAME)
        print(f"🗑️  ลบ collection '{COLLECTION_NAME}' แล้ว")
    except Exception as e:
        print(f"  ไม่สามารถลบได้: {e}")
    _vector_store = None


if __name__ == "__main__":
    print("ทดสอบ Vector DB:")
    count = count_documents()
    print(f"   จำนวน chunks ปัจจุบัน: {count}")

    if count > 0:
        print("\n ทดสอบค้นหา:")
        results = search("อาจารย์ที่ปรึกษาภาควิชา", k=2)
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n   [{i}] score: {score:.4f}")
            print(f"       source: {doc.metadata.get('source', '?')}")
            print(f"       text: {doc.page_content[:100]}...")

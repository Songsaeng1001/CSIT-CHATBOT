"""
ทดสอบว่า Vector DB ค้นข้อมูลถูกต้องไหม
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "csit_knowledge"
EMBEDDING_MODEL = "BAAI/bge-m3"


def load_vector_store():
    """โหลด vector store ที่สร้างไว้แล้ว"""
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )


def search(query, k=3):
    """ค้นหา top-k chunks ที่เกี่ยวข้อง"""
    vs = load_vector_store()
    
    # similarity_search_with_score คืนค่าพร้อมคะแนน
    results = vs.similarity_search_with_score(query, k=k)
    
    print(f"\n❓ คำถาม: {query}")
    print("─" * 60)
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n📄 ผลลัพธ์ที่ {i} (คะแนนระยะห่าง: {score:.4f})")
        print(f"   ที่มา: {doc.metadata.get('source', 'ไม่ทราบ')}")
        print(f"   เนื้อหา:")
        print(f"   {doc.page_content[:300]}...")


if __name__ == "__main__":
    # ทดสอบคำถามจริง
    test_queries = [
        "ลงทะเบียนเกิน 22 หน่วยกิตได้ไหม",
        "ปรับลงทะเบียนช้าวันละเท่าไร",
        "เกียรตินิยมอันดับ 1 ต้อง GPA เท่าไร",
    ]
    
    for q in test_queries:
        search(q, k=2)
        print("\n" + "=" * 60)
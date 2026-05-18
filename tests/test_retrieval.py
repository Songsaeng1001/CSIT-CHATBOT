"""
ทดสอบ Vector DB Retrieval (ไม่เรียก LLM)
ดูว่าค้นหา chunk ที่เกี่ยวข้องเจอไหม

รัน: python -m tests.test_retrieval
"""

from src.database import vector_db


# คำถามทดสอบ — ครอบคลุมทุกหมวด
TEST_QUERIES = [
    # ─── อาจารย์ ───
    "อาจารย์เกรียงศักดิ์ห้องอะไร",
    "ใครเป็นที่ปรึกษาวิทยานิพนธ์น้องซีที",
    
    # ─── ลงทะเบียน ───
    "ลงทะเบียนเกิน 22 หน่วยกิตทำยังไง",
    "ค่าปรับลงทะเบียนช้าเท่าไร",
    
    # ─── หลักสูตร ───
    "หลักสูตร CS เรียนกี่หน่วยกิต",
    "ความต่างระหว่าง CS กับ IT",
    
    # ─── สำเร็จการศึกษา ───
    "เกียรตินิยมอันดับ 1 ต้อง GPA เท่าไร",
    "ค่ายื่นจบกี่บาท",
    
    # ─── กยศ. ───
    "กยศ. ต้องทำจิตอาสากี่ชั่วโมง",
    
    # ─── ติดต่อ ───
    "เบอร์โทรภาควิชา",
]


def test_single_query(query: str, k: int = 3):
    """ทดสอบ 1 คำถาม"""
    print(f"\n❓ คำถาม: {query}")
    print("─" * 60)
    
    results = vector_db.search(query, k=k)
    
    if not results:
        print("   ❌ ไม่เจอ chunk ที่เกี่ยวข้อง")
        return
    
    for i, (doc, score) in enumerate(results, 1):
        source = doc.metadata.get("source", "?")
        # เอาเฉพาะชื่อไฟล์
        from pathlib import Path
        filename = Path(source).name
        
        # ตัดเนื้อหาให้สั้น
        preview = doc.page_content.replace("\n", " ")[:150]
        
        print(f"\n   [{i}] 📄 {filename}  (distance: {score:.4f})")
        print(f"       {preview}...")


def main():
    print("=" * 60)
    print("🧪 ทดสอบ Vector DB Retrieval")
    print("=" * 60)
    
    # เช็คว่ามีข้อมูลใน DB
    count = vector_db.count_documents()
    print(f"\n📊 จำนวน chunks ใน Chroma: {count}")
    
    if count == 0:
        print("\n❌ Chroma DB ว่างเปล่า!")
        print("   กรุณารัน: python -m src.ingest")
        return
    
    # ทดสอบทีละคำถาม
    for query in TEST_QUERIES:
        test_single_query(query, k=2)
    
    print()
    print("=" * 60)
    print("✨ ทดสอบเสร็จสมบูรณ์")
    print("=" * 60)


if __name__ == "__main__":
    main()
# 🤖 น้องซีที — LINE Chatbot CSIT

ระบบแชตบอทเพื่อสนับสนุนการบริการข้อมูลนิสิต ภาควิชาวิทยาการคอมพิวเตอร์
และเทคโนโลยีสารสนเทศ คณะวิทยาศาสตร์ มหาวิทยาลัยนเรศวร

## 🛠️ Tech Stack

- **Language:** Python 3.11
- **LLM Framework:** LangChain
- **LLM Provider:** Google Gemini
- **Vector DB:** ChromaDB (semantic search)
- **Structured DB:** SQLite (exact match)
- **Rules:** YAML (Rule-Augmented Reasoning)
- **Embedding:** BAAI/bge-m3
- **Backend:** FastAPI
- **Platform:** LINE Messaging API
- **Automation:** n8n (workflows)

## 📁 โครงสร้าง

\`\`\`
csit-chatbot/
├── data/
│   ├── raw/              # เอกสารดิบ
│   └── csit.db           # SQLite database
├── knowledge_base/       # เอกสารสำหรับ RAG
├── src/
│   ├── config.py
│   ├── database/
│   │   ├── sqlite_db.py
│   │   └── rules.py
│   └── main.py
├── tests/
├── n8n-workflows/
├── rules.yaml            # Rule definitions
└── requirements.txt
\`\`\`

## 🚀 เริ่มต้น

\`\`\`bash
# 1. Setup venv
python3.11 -m venv venv
source venv/bin/activate

# 2. ติดตั้ง dependencies
pip install -r requirements.txt

# 3. ตั้งค่า .env
cp .env.example .env
# แก้ไข .env ใส่ API keys

# 4. สร้าง database
python src/database/sqlite_db.py

# 5. รันระบบ
uvicorn src.main:app --reload
\`\`\`

## 👥 ทีมพัฒนา

- นายธนารักษ์ เงินฉ่ำ (66312381)
- นางสาวส่องแสง ประทุมศรี (66315214)

## 👨‍🏫 อาจารย์ที่ปรึกษา

ผศ. ดร.เกรียงศักดิ์ เตมีย์
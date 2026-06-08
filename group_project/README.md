# Bài Tập Nhóm — RAG Chatbot

## Yêu cầu 1: Sản phẩm nhóm RAG Chatbot ✅

Chatbot trả lời câu hỏi về **pháp luật ma túy** và **tin tức liên quan**, tích hợp pipeline từ Task 9 + Task 10.

### Tính năng

| Yêu cầu | Trạng thái |
|---------|-----------|
| Giao diện chat | ✅ Streamlit + React frontend |
| Trả lời có citation | ✅ Task 10 |
| Follow-up questions (conversation memory) | ✅ Lưu 6 turn gần nhất |
| Hiển thị source documents | ✅ Sidebar + expander |

---

## Kiến Trúc Hệ Thống

```
User (Streamlit / React UI)
        │
        ▼
group_project/chatbot/rag_service.py
        │
        ├─→ Task 9: retrieve() — hybrid search + rerank + PageIndex fallback
        │
        └─→ Task 10: reorder + format context + LLM (OpenRouter)
                │
                ▼
        Answer + Citations + Source chunks
```

**Dữ liệu:**
- `data/standardized/` — 3 legal MD + 6 news MD
- `data/index/chunks.pkl` — 2,138 chunks (all-MiniLM-L6-v2)

---

## Hướng Dẫn Chạy

### 1. Cài dependencies

```bash
pip install -r requirements.txt
```

Đảm bảo `.env` có:
```
OPENROUTER_API_KEY=sk-or-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=openai/gpt-4o-mini
```

### 2A. Streamlit (khuyến nghị cho demo)

```bash
streamlit run app.py
```

Hoặc:
```bash
streamlit run group_project/chatbot/app.py
```

### 2B. React UI + FastAPI backend

Terminal 1 — Backend:
```bash
uvicorn group_project.chatbot.api:app --reload --port 8000
```

Terminal 2 — Frontend:
```bash
cd src/frontend
npm run dev
```

Mở http://localhost:5173 (hoặc port Vite hiển thị).

---

## Cấu Trúc File

```
group_project/
├── chatbot/
│   ├── rag_service.py   # Core: retrieval + generation + memory
│   ├── app.py           # Streamlit UI
│   └── api.py           # FastAPI cho React frontend
├── evaluation/          # Yêu cầu 2 (chưa làm)
└── README.md
```

---

## Phân Công Công Việc

| Thành viên | MSSV | Nhiệm vụ | Trạng thái |
|-----------|------|----------|------------|
| | | Task 1-4: Data + Indexing | ✅ |
| | | Task 5-9: Retrieval Pipeline | ✅ |
| | | Task 10: Generation + Citation | ✅ |
| | | Group: RAG Chatbot UI | ✅ |

---

## Demo Queries

- "Hình phạt cho tội tàng trữ trái phép chất ma túy là gì?"
- "Luật Phòng chống ma túy 2021 quy định gì về cai nghiện?"
- "Những nghệ sĩ nào đã bị bắt vì ma túy?"
- Follow-up: "Họ bị phạt bao nhiêu năm tù?"

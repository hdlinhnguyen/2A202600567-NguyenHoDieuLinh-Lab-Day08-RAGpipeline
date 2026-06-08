"""
FastAPI backend cho React frontend.

Chạy:
    uvicorn group_project.chatbot.api:app --reload --port 8000
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

from group_project.chatbot.ingest_service import ingest_uploaded_file  # noqa: E402
from group_project.chatbot.rag_service import (  # noqa: E402
    chat_with_citation,
    get_knowledge_base_info,
)

app = FastAPI(title="Drug Law RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:5173", "http://localhost:8080",
        "http://127.0.0.1:3000", "http://127.0.0.1:5173", "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    retrieval_source: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/knowledge-base")
def knowledge_base():
    return get_knowledge_base_info()


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    history = [{"role": m.role, "content": m.content} for m in request.history]
    result = chat_with_citation(request.message, history=history)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        retrieval_source=result["retrieval_source"],
    )


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload file vào Knowledge Base (PDF, DOCX, MD, TXT)."""
    if not file.filename:
        return {"success": False, "error": "Tên file không hợp lệ"}

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        return {"success": False, "error": "File quá lớn (tối đa 20MB)"}

    result = ingest_uploaded_file(file.filename, content)
    if result.get("success"):
        result["knowledge_base"] = get_knowledge_base_info()
    return result

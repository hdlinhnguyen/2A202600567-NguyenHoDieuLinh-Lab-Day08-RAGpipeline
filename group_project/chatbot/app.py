"""
Yêu cầu 1 — RAG Chatbot (Streamlit).

Chạy:
    streamlit run group_project/chatbot/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

CHATBOT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CHATBOT_DIR.parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from group_project.chatbot.ingest_service import ingest_uploaded_file  # noqa: E402
from group_project.chatbot.rag_service import (  # noqa: E402
    chat_with_citation,
    get_knowledge_base_info,
)

st.set_page_config(
    page_title="RAG Chatbot — Pháp luật Ma túy",
    page_icon="⚖️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .source-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }
    .source-title { font-weight: 600; font-size: 0.9rem; }
    .source-meta { color: #64748b; font-size: 0.75rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

kb = get_knowledge_base_info()

with st.sidebar:
    st.title("⚖️ RAG Chatbot")
    st.caption("Pháp luật ma túy & tin tức liên quan")
    st.divider()

    st.subheader("Knowledge Base")
    st.metric("Tài liệu", kb["total_documents"])
    st.metric("Chunks đã index", kb["total_chunks"])
    upload_count = kb.get("upload_count", 0)
    st.caption(f"📜 Legal: {kb['legal_count']} · 📰 News: {kb['news_count']} · 📤 Upload: {upload_count}")

    uploaded = st.file_uploader(
        "Thêm tài liệu vào Knowledge Base",
        type=["pdf", "docx", "doc", "md", "txt"],
        help="PDF, DOCX, MD, TXT — tối đa 20MB",
    )
    if uploaded is not None:
        with st.spinner("Đang convert & index..."):
            result = ingest_uploaded_file(uploaded.name, uploaded.getvalue())
        if result.get("success"):
            st.success(f"Đã thêm {result['filename']} — {result['total_chunks']} chunks")
            st.rerun()
        else:
            st.error(result.get("error", "Upload thất bại"))

    with st.expander("Danh sách tài liệu", expanded=False):
        for doc in kb["documents"]:
            icon = {"legal": "📜", "upload": "📤"}.get(doc["type"], "📰")
            st.markdown(
                f"{icon} **{doc['name']}**  \n"
                f"<span class='source-meta'>{doc['size_kb']} KB · {doc['chars']:,} ký tự</span>",
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Nguồn truy vấn gần nhất")
    if st.session_state.last_sources:
        for i, src in enumerate(st.session_state.last_sources, 1):
            st.markdown(
                f"<div class='source-card'>"
                f"<div class='source-title'>{i}. {src['title']}</div>"
                f"<div class='source-meta'>{src['type']} · score {src['score']} · {src['retrieval']}</div>"
                f"<div style='font-size:0.8rem;margin-top:6px;'>{src['snippet']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("Chưa có nguồn nào. Hãy đặt câu hỏi!")

    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_sources = []
        st.rerun()

st.title("Chatbot Pháp luật Ma túy")
st.markdown(
    "Hỏi về **luật pháp**, **hình phạt**, **cai nghiện** hoặc **tin tức nghệ sĩ** — "
    "mọi câu trả lời đều kèm **citation** từ nguồn đã index."
)

suggestions = [
    "Hình phạt cho tội tàng trữ trái phép chất ma túy là gì?",
    "Luật Phòng chống ma túy 2021 quy định gì về cai nghiện?",
    "Những nghệ sĩ nào đã bị bắt vì ma túy?",
    "Ma túy loại nào bị cấm theo thông tư liên tịch?",
]

cols = st.columns(len(suggestions))
for col, suggestion in zip(cols, suggestions):
    if col.button(suggestion, use_container_width=True):
        st.session_state.pending_query = suggestion

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("sources"):
            with st.expander(f"📚 {len(message['sources'])} nguồn được sử dụng"):
                for i, src in enumerate(message["sources"], 1):
                    st.markdown(f"**{i}. {src['title']}** ({src['type']}, score {src['score']})")
                    st.caption(src["snippet"])
                    st.text(src["excerpt"][:500] + ("..." if len(src["excerpt"]) > 500 else ""))

query = st.chat_input("Nhập câu hỏi của bạn...")
if hasattr(st.session_state, "pending_query"):
    query = st.session_state.pending_query
    del st.session_state.pending_query

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
        if m["role"] in ("user", "assistant")
    ]

    with st.chat_message("assistant"):
        with st.status("Đang xử lý...", expanded=True) as status:
            status.write("🔍 Đang phân tích câu hỏi...")
            status.write("📚 Đang tra cứu knowledge base...")
            status.write("🔗 Đang tìm kiếm semantic + BM25...")
            status.write("⚖️ Đang rerank nguồn...")
            status.write("🧠 Đang suy luận và tổng hợp...")
            try:
                result = chat_with_citation(query, history=history)
                answer = result["answer"]
                sources = result["sources"]
                status.update(label="Hoàn thành", state="complete")
            except Exception as exc:
                answer = f"❌ Lỗi khi xử lý: {exc}"
                sources = []
                status.update(label="Lỗi", state="error")

        st.markdown(answer)
        if sources:
            with st.expander(f"📚 {len(sources)} nguồn được sử dụng"):
                for i, src in enumerate(sources, 1):
                    st.markdown(f"**{i}. {src['title']}** ({src['type']}, score {src['score']})")
                    st.caption(src["snippet"])
                    st.text(src["excerpt"][:500] + ("..." if len(src["excerpt"]) > 500 else ""))

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
    st.session_state.last_sources = sources

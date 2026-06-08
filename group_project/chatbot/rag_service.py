"""
RAG Chat Service — tích hợp Task 9 (retrieval) + Task 10 (generation).

Hỗ trợ:
- Trả lời có citation
- Conversation memory (follow-up questions)
- Hiển thị source documents
"""

from __future__ import annotations

import os
import pickle
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")

from src.doc_metadata import extract_chunk_links, resolve_doc_url  # noqa: E402
from src.local_index import ensure_local_index  # noqa: E402
from src.llm_guardrails import build_system_prompt  # noqa: E402
from src.task10_generation import (  # noqa: E402
    TOP_K,
    TOP_P,
    TEMPERATURE,
    LLM_MODEL,
    format_context,
    reorder_for_llm,
)
from src.task6_lexical_search import _get_bm25, _tokenize, lexical_search  # noqa: E402
from src.task9_retrieval_pipeline import retrieve  # noqa: E402

STANDARDIZED_DIR = ROOT_DIR / "data" / "standardized"
INDEX_PATH = ROOT_DIR / "data" / "index" / "chunks.pkl"
MAX_HISTORY_TURNS = 6
MAX_EXTRA_CHUNKS = TOP_K

CHAT_SYSTEM_PROMPT = build_system_prompt(for_chat=True)
VIETNAM_TZ = timezone(timedelta(hours=7))

LEGAL_HINTS = (
    "luật", "luat", "ma túy", "ma tuy", "phạt", "phat", "điều", "dieu",
    "tội", "toi", "cai nghiện", "cai nghien", "hình sự", "hinh su",
    "nghị định", "nghi dinh", "thông tư", "thong tu", "tàng trữ", "tang tru",
    "vận chuyển", "van chuyen", "cai nghiện",
)

NEWS_HINTS = (
    "nghệ sĩ", "nghe si", "ca sĩ", "ca si", "diễn viên", "dien vien",
    "rapper", "người mẫu", "nguoi mau", "showbiz", "bị bắt", "bi bat",
    "khởi tố", "khoi to", "tin tức", "tin tuc", "bài báo", "bai bao",
    "báo chí", "bao chi", "miu lê", "miu le", "long nhật", "long nhat",
    "sao việt", "sao viet", "nghệ sĩ nào", "nghe si nao", "ai đã", "ai da",
    "vụ bắt", "vu bat", "vụ án", "vu an", "gần đây", "gan day",
    "đáng chú ý", "dang chu y", "chấn động", "chan dong", "triệt phá", "triet pha",
    "bắt giữ", "bat giu", "đường dây", "duong day", "vụ lớn", "vu lon",
)

NEWS_JUNK_MARKERS = (
    "about:blank",
    "404",
    "không tìm thấy",
    "khong tim thay",
    "trang thông báo lỗi",
    "tin tức đáng chú ý: vi phạm hành chính",
)

NEWS_CASE_KEYWORDS = (
    "khởi tố", "khoi to", "bị bắt", "bi bat", "miu lê", "miu le",
    "long nhật", "long nhat", "sơn ngọc minh", "son ngoc minh",
    "bình gold", "binh gold", "đường dây", "duong day", "triệt phá", "triet pha",
    "ma túy", "ma tuy", "showbiz", "cát bà", "cat ba",
)

NEWS_SCORING_QUERY = (
    "khởi tố bị bắt ma túy nghệ sĩ ca sĩ Miu Lê Long Nhật Sơn Ngọc Minh "
    "Bình Gold đường dây triệt phá Cát Bà TPHCM showbiz"
)

LEGAL_ONLY_HINTS = (
    "hình phạt", "hinh phat", "mức phạt", "muc phat", "phạt tù", "phat tu",
    "điều ", "dieu ", "luật ", "luat ", "nghị định", "nghi dinh", "thông tư", "thong tu",
    "tội ", "toi ", "cai nghiện", "cai nghien", "tàng trữ", "tang tru",
    "vận chuyển", "van chuyen", "bộ luật", "bo luat",
)

TIME_PATTERNS = (
    r"mấy giờ", r"may gio", r"bây giờ", r"bay gio", r"mấy h\b", r"may h\b",
    r"giờ hiện tại", r"gio hien tai", r"thời gian", r"thoi gian",
)

DATE_PATTERNS = (
    r"ngày mấy", r"ngay may", r"hôm nay", r"hom nay", r"ngày nào", r"ngay nao",
    r"thứ mấy", r"thu may",
)

CHITCHAT_PATTERNS = (
    r"xin chào", r"xin chao", r"chào\b", r"chao\b", r"hello", r"\bhi\b",
    r"bạn là ai", r"ban la ai", r"who are you", r"bạn là gì", r"ban la gi",
    r"cảm ơn", r"cam on", r"thank",
)

# Tên người dùng hay gõ nhầm / khác chính tả so với tài liệu
NAME_ALIASES: dict[str, str] = {
    "bình vàng": "Bình Gold Vũ Xuân Bình rapper",
    "binh vang": "Bình Gold Vũ Xuân Bình rapper",
    "bình gold": "Bình Gold Vũ Xuân Bình rapper",
}


def _call_llm(messages: list[dict]) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )
    return response.choices[0].message.content or ""


def _enrich_chunks(chunks: list[dict]) -> list[dict]:
    """Bổ sung url gốc và links trong chunk vào metadata."""
    enriched: list[dict] = []
    for chunk in chunks:
        metadata = dict(chunk.get("metadata", {}))
        source_name = metadata.get("source", "unknown")
        doc_type = metadata.get("type", "unknown")

        if not metadata.get("url"):
            doc_url = resolve_doc_url(source_name, doc_type, STANDARDIZED_DIR)
            if doc_url:
                metadata["url"] = doc_url

        chunk_links = extract_chunk_links(chunk.get("content", ""))
        if chunk_links:
            metadata["links"] = chunk_links

        enriched.append({**chunk, "metadata": metadata})
    return enriched


def _format_sources(chunks: list[dict]) -> list[dict]:
    sources = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        source_name = metadata.get("source", "unknown")
        doc_type = metadata.get("type", "unknown")
        url = metadata.get("url")
        links = metadata.get("links") or []

        entry: dict = {
            "title": source_name,
            "snippet": chunk["content"][:120].replace("\n", " ") + "...",
            "excerpt": chunk["content"][:800],
            "type": doc_type,
            "score": round(float(chunk.get("score", 0)), 3),
            "retrieval": chunk.get("source", "hybrid"),
        }
        if url:
            entry["url"] = url
        if links:
            entry["links"] = links

        sources.append(entry)
    return sources


def get_knowledge_base_info() -> dict:
    """Thông tin knowledge base cho sidebar."""
    legal_files = list((STANDARDIZED_DIR / "legal").glob("*.md")) if (STANDARDIZED_DIR / "legal").exists() else []
    news_files = list((STANDARDIZED_DIR / "news").glob("*.md")) if (STANDARDIZED_DIR / "news").exists() else []
    upload_files = list((STANDARDIZED_DIR / "uploads").glob("*.md")) if (STANDARDIZED_DIR / "uploads").exists() else []

    chunk_count = 0
    if INDEX_PATH.exists():
        with INDEX_PATH.open("rb") as f:
            chunks = pickle.load(f)
            chunk_count = len(chunks)

    documents = []
    for md_file in sorted(legal_files + news_files + upload_files):
        content = md_file.read_text(encoding="utf-8")
        if "legal" in md_file.parts:
            doc_type = "legal"
        elif "uploads" in md_file.parts:
            doc_type = "upload"
        else:
            doc_type = "news"
        documents.append({
            "name": md_file.name,
            "size_kb": round(md_file.stat().st_size / 1024, 1),
            "type": doc_type,
            "chars": len(content),
            "status": "ready",
        })

    return {
        "total_documents": len(documents),
        "total_chunks": chunk_count,
        "legal_count": len(legal_files),
        "news_count": len(news_files),
        "upload_count": len(upload_files),
        "documents": documents,
    }


def _has_news_intent(query: str) -> bool:
    q = query.lower()
    if any(h in q for h in NEWS_HINTS):
        return True
    return ("ma túy" in q or "ma tuy" in q) and any(
        h in q for h in ("vụ", "vu ", "bắt", "bat", "gần đây", "gan day", "đáng chú ý", "dang chu y")
    )


def _is_news_junk(content: str) -> bool:
    c = content.lower()
    return any(marker in c for marker in NEWS_JUNK_MARKERS)


def _news_scoring_query(query: str) -> str:
    return f"{query} {NEWS_SCORING_QUERY}"


def _has_legal_only_intent(query: str) -> bool:
    q = query.lower()
    return any(h in q for h in LEGAL_ONLY_HINTS)


def _detect_intent(query: str) -> str:
    """Phân loại: news / legal / mixed."""
    news = _has_news_intent(query)
    legal = _has_legal_only_intent(query)
    if news and not legal:
        return "news"
    if legal and not news:
        return "legal"
    if news and legal:
        return "mixed"
    return "general"


def _expand_query_terms(query: str) -> str:
    """Mở rộng query theo intent — pháp luật hoặc tin tức."""
    q = query.lower()
    intent = _detect_intent(query)
    extras: list[str] = []

    if intent in ("legal", "mixed", "general"):
        if any(k in q for k in ["hình phạt", "hinh phat", "mức phạt", "muc phat", "phạt tù", "phat tu"]):
            extras.append("Điều 249 phạt tù Bộ luật Hình sự")
        if any(k in q for k in ["tàng trữ", "tang tru", "tội tàng trữ", "toi tang tru"]):
            extras.append("tội tàng trữ trái phép chất ma túy")
        if any(k in q for k in ["vận chuyển", "van chuyen"]):
            extras.append("Điều 250 vận chuyển trái phép")
        if intent != "news" and any(k in q for k in ["sử dụng trái phép", "su dung trai phep"]):
            extras.append("Điều 254 sử dụng trái phép chất ma túy")
        if any(k in q for k in ["cai nghiện", "cai nghien"]):
            extras.append("Luật Phòng chống ma túy 2021 cai nghiện")

    if intent in ("news", "mixed") or _has_news_intent(query):
        extras.append("nghệ sĩ ca sĩ ma túy bị bắt khởi tố showbiz Việt Nam")

    if any(k in q for k in ["vụ bắt", "vu bat", "vụ án", "vu an", "gần đây", "gan day",
                            "đáng chú ý", "dang chu y", "chấn động", "chan dong", "triệt phá"]):
        extras.append(
            "Miu Lê Cát Bà Long Nhật Sơn Ngọc Minh Bình Gold khởi tố đường dây ma túy TPHCM"
        )

    for alias, canonical in NAME_ALIASES.items():
        if alias in q:
            extras.append(canonical)

    if extras:
        return f"{query} {' '.join(extras)}"
    return query


def _list_required_sources() -> list[str]:
    """Danh sách mọi file .md trong data/standardized/ (luật + báo + upload)."""
    if not STANDARDIZED_DIR.exists():
        return []
    return [md_file.name for md_file in sorted(STANDARDIZED_DIR.rglob("*.md"))]


def _chunk_key(chunk: dict) -> tuple:
    meta = chunk.get("metadata", {})
    return (meta.get("source"), meta.get("chunk_index"))


def _chunk_relevance_score(
    idx: int,
    doc: dict,
    user_scores,
    news_scores,
) -> float:
    """Điểm chunk — bài báo dùng news query, tránh chunk rác crawl."""
    content = doc.get("content", "")
    if _is_news_junk(content):
        return -1.0

    doc_type = doc.get("metadata", {}).get("type", "")
    if doc_type == "news":
        score = float(news_scores[idx])
        c = content.lower()
        for kw in NEWS_CASE_KEYWORDS:
            if kw in c:
                score += 1.0
        return score

    return float(user_scores[idx])


def _best_chunk_per_source(query: str) -> dict[str, dict]:
    """Chunk liên quan nhất cho từng nguồn — bài báo ưu tiên vụ án ma túy thực tế."""
    bm25, corpus = _get_bm25()
    if not corpus:
        return {}

    user_scores = bm25.get_scores(_tokenize(query))
    news_scores = bm25.get_scores(_tokenize(_news_scoring_query(query)))

    best_by_source: dict[str, tuple[int, float]] = {}

    for idx, doc in enumerate(corpus):
        src = doc.get("metadata", {}).get("source", "")
        if not src:
            continue
        score = _chunk_relevance_score(idx, doc, user_scores, news_scores)
        if score < 0:
            continue
        if src not in best_by_source or score > best_by_source[src][1]:
            best_by_source[src] = (idx, score)

    result: dict[str, dict] = {}
    for src, (idx, score) in best_by_source.items():
        doc = corpus[idx]
        result[src] = {
            "content": doc["content"],
            "score": score,
            "metadata": dict(doc.get("metadata", {})),
            "source": "full_coverage",
        }
    return result


def _fallback_chunk_for_source(source_name: str) -> dict | None:
    """Lấy chunk đầu tiên của nguồn nếu BM25 không có điểm."""
    for doc in ensure_local_index():
        if doc.get("metadata", {}).get("source") == source_name:
            return {
                "content": doc["content"],
                "score": 0.0,
                "metadata": dict(doc.get("metadata", {})),
                "source": "full_coverage",
            }
    return None


def _ensure_full_source_coverage(chunks: list[dict], query: str) -> list[dict]:
    """
    Bắt buộc đưa ít nhất 1 chunk từ MỌI nguồn trong data/standardized/
    (văn bản luật + bài báo + upload), rồi bổ sung thêm chunk liên quan query.
    """
    required_sources = _list_required_sources()
    per_source = _best_chunk_per_source(query)

    seen: set[tuple] = set()
    result: list[dict] = []

    for src in required_sources:
        chunk = per_source.get(src) or _fallback_chunk_for_source(src)
        if not chunk:
            continue
        key = _chunk_key(chunk)
        if key in seen:
            continue
        seen.add(key)
        result.append(chunk)

    extra_added = 0
    for chunk in sorted(chunks, key=lambda c: float(c.get("score", 0)), reverse=True):
        if extra_added >= MAX_EXTRA_CHUNKS:
            break
        key = _chunk_key(chunk)
        if key in seen:
            continue
        seen.add(key)
        result.append(chunk)
        extra_added += 1

    return result


def _has_legal_intent(query: str) -> bool:
    q = query.lower()
    return any(hint in q for hint in LEGAL_HINTS)


def _matches_any(query: str, patterns: tuple[str, ...]) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in patterns)


def _general_query_hint(query: str) -> str | None:
    """Gợi ý cho LLM khi câu hỏi là chào hỏi / giờ / ngày — vẫn đọc toàn bộ nguồn."""
    if _has_legal_intent(query):
        return None

    now = datetime.now(VIETNAM_TZ)
    weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

    if _matches_any(query, TIME_PATTERNS):
        return (
            f"Câu hỏi về giờ — trả lời ngắn, tự nhiên: hiện tại {now.strftime('%H:%M')} "
            f"ngày {now.strftime('%d/%m/%Y')} (UTC+7). Không cần trích dẫn tài liệu."
        )
    if _matches_any(query, DATE_PATTERNS):
        return (
            f"Câu hỏi về ngày — trả lời ngắn, tự nhiên: {weekdays[now.weekday()]}, "
            f"{now.strftime('%d/%m/%Y')} (UTC+7). Không cần trích dẫn tài liệu."
        )
    if _matches_any(query, CHITCHAT_PATTERNS):
        return (
            "Câu chào hỏi — giới thiệu ngắn Arionear, hướng dẫn hỏi về pháp luật/tin tức ma túy. "
            "Không cần trích dẫn tài liệu."
        )
    return None


def _build_retrieval_query(query: str, history: list[dict]) -> str:
    """Ghép ngữ cảnh hội thoại + mở rộng từ khóa pháp lý."""
    parts = [query]

    if history:
        recent_user = [m["content"] for m in history if m["role"] == "user"][-2:]
        if recent_user:
            parts = recent_user + parts

    combined = " ".join(parts)
    return _expand_query_terms(combined)


def chat_with_citation(
    query: str,
    history: list[dict] | None = None,
    top_k: int = TOP_K,
) -> dict:
    """
    RAG chat với conversation memory.

    history: [{"role": "user"|"assistant", "content": "..."}]
    """
    history = history or []

    retrieval_query = _build_retrieval_query(query, history)
    chunks = retrieve(retrieval_query, top_k=top_k * 2)

    q_lower = query.lower()
    if any(k in q_lower for k in ["hình phạt", "hinh phat", "tàng trữ", "tang tru"]):
        extra = lexical_search("Điều 249 tàng trữ trái phép phạt tù", top_k=3)
        for item in extra:
            item["source"] = "hybrid"
        chunks = extra + chunks

    if _has_news_intent(query):
        news_extra = lexical_search(_news_scoring_query(query), top_k=10)
        news_extra = [
            c for c in news_extra
            if c.get("metadata", {}).get("type") == "news" and not _is_news_junk(c.get("content", ""))
        ]
        for item in news_extra:
            item["source"] = "hybrid"
        chunks = news_extra + chunks

    chunks = _enrich_chunks(_ensure_full_source_coverage(chunks, query))
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)

    required_sources = _list_required_sources()
    covered_sources = {c.get("metadata", {}).get("source") for c in chunks}

    notes: list[str] = [
        f"Đã cung cấp đại diện từ tất cả {len(required_sources)} nguồn (luật + báo + upload). "
        "Xem xét cả văn bản pháp luật lẫn bài báo. Trả lời tự nhiên, không dùng từ 'Context'.",
    ]
    if history:
        notes.append(
            "Có thể là câu hỏi follow-up — dùng lịch sử chat để hiểu ngữ cảnh."
        )
    if _has_news_intent(query):
        notes.append(
            "Ưu tiên thông tin từ bài báo; trích dẫn [tên bài, năm]. "
            "Kiểm tra tên gần đúng (vd. Bình Vàng ↔ Bình Gold). "
            "Nếu hỏi vụ bắt/vụ án gần đây — liệt kê các vụ có trong bài báo "
            "(vd. Miu Lê Cát Bà, Long Nhật/Sơn Ngọc Minh TPHCM, Bình Gold...)."
        )
    if _has_legal_only_intent(query):
        notes.append("Ưu tiên điều khoản từ văn bản pháp luật.")

    general_hint = _general_query_hint(query)
    if general_hint:
        notes.append(general_hint)

    if len(covered_sources) < len(required_sources):
        missing = sorted(set(required_sources) - covered_sources)
        notes.append(f"Cảnh báo: thiếu nguồn trong context: {', '.join(missing)}")

    followup_note = f"\n\nLưu ý: {' '.join(notes)}" if notes else ""

    user_message = (
        f"Tài liệu tham khảo:\n{context}\n\n---\n\n"
        f"Câu hỏi: {query}{followup_note}"
    )

    messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
    messages.extend(history[-MAX_HISTORY_TURNS:])
    messages.append({"role": "user", "content": user_message})

    answer = _call_llm(messages)

    return {
        "answer": answer,
        "sources": _format_sources(chunks),
        "raw_chunks": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none",
    }

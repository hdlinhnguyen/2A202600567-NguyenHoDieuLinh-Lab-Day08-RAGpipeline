"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

import json
import math
import re
from pathlib import Path

VECTORSTORE_INDEX = Path(__file__).parent.parent / "data" / "standardized" / "vectorstore" / "vectorstore_fallback.json"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed_text(text: str) -> list[float]:
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(EMBEDDING_MODEL)
        return model.encode(_normalize_text(text)).tolist()
    except Exception:
        tokens = re.findall(r"\w+", text.lower())
        vector = [0.0] * EMBEDDING_DIM
        for term in tokens[: EMBEDDING_DIM * 2]:
            idx = abs(hash(term)) % EMBEDDING_DIM
            vector[idx] += 1.0
        return [float(x) for x in vector]


def _load_index() -> list[dict]:
    if not VECTORSTORE_INDEX.exists():
        return []
    try:
        with VECTORSTORE_INDEX.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return [item for item in data if "embedding" in item and "content" in item]
    except Exception:
        return []


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict
        }
        Sorted by score descending.
    """
    if not query or not query.strip():
        return []

    index = _load_index()
    if not index:
        return []

    query_embedding = _embed_text(query)
    results = []
    for item in index:
        score = _cosine_similarity(query_embedding, item["embedding"])
        results.append({
            "content": item.get("content", ""),
            "score": float(score),
            "metadata": item.get("metadata", {}),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[: max(0, top_k)]


if __name__ == "__main__":
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

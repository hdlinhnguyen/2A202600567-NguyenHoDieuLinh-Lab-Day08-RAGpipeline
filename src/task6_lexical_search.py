"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import math
import re
from pathlib import Path
from typing import List

CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict}
_BM25_INDEX = None
_CHUNKS_CORPUS = None


def _get_bm25():
    global _BM25_INDEX, _CHUNKS_CORPUS
    if _BM25_INDEX is not None and _CHUNKS_CORPUS is not None:
        return _BM25_INDEX, _CHUNKS_CORPUS

    from src.local_index import ensure_local_index
    _CHUNKS_CORPUS = ensure_local_index()
    _BM25_INDEX = build_bm25_index(_CHUNKS_CORPUS)
    return _BM25_INDEX, _CHUNKS_CORPUS


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
    return [token for token in tokens if token]


def _load_corpus() -> list[dict]:
    global CORPUS
    if CORPUS:
        return CORPUS

    standardized_dir = Path(__file__).parent.parent / "data" / "standardized"
    if not standardized_dir.exists():
        return []

    corpus = []
    for md_file in sorted(standardized_dir.rglob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8").strip()
        except Exception:
            continue

        if not content:
            continue

        metadata = {
            "source": md_file.name,
            "path": str(md_file),
            "type": md_file.parent.name,
        }
        corpus.append({"content": content, "metadata": metadata})

    CORPUS = corpus
    return CORPUS


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        return None

    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def _build_simple_index(corpus: list[dict]) -> dict:
    """Fallback index based on term frequency and inverse document frequency."""
    df = {}
    tokenized_docs = []
    for doc in corpus:
        tokens = _tokenize(doc["content"])
        tokenized_docs.append(tokens)
        for token in set(tokens):
            df[token] = df.get(token, 0) + 1

    total_docs = len(corpus)
    return {
        "total_docs": total_docs,
        "df": df,
        "tokenized_docs": tokenized_docs,
    }


def _simple_bm25_scores(index: dict, query_tokens: list[str]) -> list[float]:
    k1 = 1.5
    b = 0.75
    avgdl = sum(len(doc) for doc in index["tokenized_docs"]) / max(1, index["total_docs"])
    scores = []

    for tokens in index["tokenized_docs"]:
        freq = {}
        for token in tokens:
            freq[token] = freq.get(token, 0) + 1

        doc_len = len(tokens)
        score = 0.0
        for token in query_tokens:
            if token not in index["df"]:
                continue
            idf = max(0.1, math.log((index["total_docs"] - index["df"][token] + 0.5) / (index["df"][token] + 0.5) + 1))
            tf = freq.get(token, 0)
            score += idf * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avgdl)))
        scores.append(score)
    return scores


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if not query or not query.strip():
        return []

    corpus = _load_corpus()
    if not corpus:
        return []

    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    bm25 = build_bm25_index(corpus)
    if bm25 is not None:
        scores = bm25.get_scores(tokenized_query)
    else:
        index = _build_simple_index(corpus)
        scores = _simple_bm25_scores(index, tokenized_query)

    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:max(0, top_k)]

    results = []
    for idx in top_indices:
        results.append({
            "content": corpus[idx]["content"],
            "score": float(scores[idx]),
            "metadata": corpus[idx]["metadata"],
        })

    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

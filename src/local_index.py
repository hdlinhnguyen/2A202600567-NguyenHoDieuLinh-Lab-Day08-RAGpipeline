"""Local vector index fallback khi Weaviate không khả dụng."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
INDEX_PATH = INDEX_DIR / "chunks.pkl"


def save_local_index(chunks: list[dict]) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("wb") as f:
        pickle.dump(chunks, f)


def load_local_index() -> list[dict] | None:
    if not INDEX_PATH.exists():
        return None
    with INDEX_PATH.open("rb") as f:
        return pickle.load(f)


def ensure_local_index() -> list[dict]:
    cached = load_local_index()
    if cached:
        return cached

    from src.task4_chunking_indexing import (
        chunk_documents,
        embed_chunks,
        load_documents,
    )

    docs = load_documents()
    chunks = chunk_documents(docs)
    chunks = embed_chunks(chunks)
    save_local_index(chunks)
    return chunks


def search_local_index(query_embedding: list[float], top_k: int = 10) -> list[dict]:
    chunks = ensure_local_index()
    if not chunks:
        return []

    matrix = np.array([c["embedding"] for c in chunks], dtype=np.float32)
    query = np.array(query_embedding, dtype=np.float32)
    scores = matrix @ query

    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        chunk = chunks[int(idx)]
        results.append({
            "content": chunk["content"],
            "score": float(scores[idx]),
            "metadata": chunk.get("metadata", {}),
        })
    return results

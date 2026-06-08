"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _load_standardized_documents() -> list[Path]:
    if not STANDARDIZED_DIR.exists():
        return []
    return sorted(STANDARDIZED_DIR.rglob("*.md"))


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    if not PAGEINDEX_API_KEY:
        raise ValueError("PAGEINDEX_API_KEY không được cấu hình.")

    try:
        from pageindex import PageIndex
    except ImportError as exc:
        raise ImportError(
            "pageindex package chưa được cài đặt. "
            "Install with `pip install pageindex`."
        ) from exc

    documents = _load_standardized_documents()
    if not documents:
        raise FileNotFoundError("Không tìm thấy file markdown trong data/standardized/.")

    pi = PageIndex(api_key=PAGEINDEX_API_KEY)
    for md_file in documents:
        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue
        metadata = {"filename": md_file.name, "type": md_file.parent.name}
        pi.upload(content=content, metadata=metadata)
        print(f"  ✓ Uploaded: {md_file.name}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not query or not query.strip():
        return []

    if not PAGEINDEX_API_KEY:
        return []

    try:
        from pageindex import PageIndex
    except ImportError:
        return []

    try:
        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        results = pi.query(query=query, top_k=top_k)
    except Exception:
        return []

    output = []
    for item in results:
        if isinstance(item, dict):
            text = item.get("text") or item.get("content") or ""
            score = float(item.get("score", 0.0))
            metadata = item.get("metadata", {}) or {}
        else:
            text = getattr(item, "text", None) or getattr(item, "content", "")
            score = float(getattr(item, "score", 0.0))
            metadata = getattr(item, "metadata", {}) or {}

        output.append({
            "content": text,
            "score": score,
            "metadata": metadata,
            "source": "pageindex",
        })

    return output


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")

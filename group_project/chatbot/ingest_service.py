"""
Ingest uploaded files vào Knowledge Base.

Flow: upload → convert markdown → re-chunk → re-embed → update local index
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

LANDING_UPLOADS = ROOT_DIR / "data" / "landing" / "uploads"
STANDARDIZED_UPLOADS = ROOT_DIR / "data" / "standardized" / "uploads"

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".md", ".txt"}


def _convert_to_markdown(source_path: Path) -> tuple[Path | None, str | None]:
    """Convert file sang markdown trong standardized/uploads/."""
    STANDARDIZED_UPLOADS.mkdir(parents=True, exist_ok=True)
    output_path = STANDARDIZED_UPLOADS / f"{source_path.stem}.md"
    suffix = source_path.suffix.lower()

    try:
        if suffix == ".md":
            text = source_path.read_text(encoding="utf-8").strip()
        elif suffix == ".txt":
            text = source_path.read_text(encoding="utf-8").strip()
        else:
            from markitdown import MarkItDown

            result = MarkItDown().convert(str(source_path))
            text = (result.text_content or "").strip()

        if len(text) < 50:
            return None, "Không trích xuất được nội dung (file rỗng hoặc PDF scan ảnh)"

        header = (
            f"# {source_path.stem}\n\n"
            f"**Source:** upload\n"
            f"**File:** {source_path.name}\n\n---\n\n"
        )
        output_path.write_text(header + text, encoding="utf-8")
        return output_path, None
    except Exception as exc:
        return None, str(exc)


def _rebuild_index() -> int:
    """Rebuild toàn bộ local index từ standardized/."""
    from src.task4_chunking_indexing import (
        chunk_documents,
        embed_chunks,
        index_to_vectorstore,
        load_documents,
    )

    docs = load_documents()
    chunks = chunk_documents(docs)
    chunks = embed_chunks(chunks)
    index_to_vectorstore(chunks)
    return len(chunks)


def ingest_uploaded_file(filename: str, file_bytes: bytes) -> dict:
    """Nhận file upload, convert, re-index."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "error": f"Định dạng không hỗ trợ. Chấp nhận: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        }

    LANDING_UPLOADS.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name.replace("..", "_")
    landing_path = LANDING_UPLOADS / safe_name
    landing_path.write_bytes(file_bytes)

    md_path, error = _convert_to_markdown(landing_path)
    if error:
        landing_path.unlink(missing_ok=True)
        return {"success": False, "error": error}

    total_chunks = _rebuild_index()

    return {
        "success": True,
        "filename": safe_name,
        "markdown_path": str(md_path.relative_to(ROOT_DIR)) if md_path else None,
        "chars": md_path.stat().st_size if md_path else 0,
        "total_chunks": total_chunks,
    }

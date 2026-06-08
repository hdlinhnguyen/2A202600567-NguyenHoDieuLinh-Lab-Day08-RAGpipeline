"""Trích xuất URL và link từ markdown documents."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE_URL_RE = re.compile(r"\*\*Source:\*\*\s*(https?://\S+)", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^\)]+)\)")
PLAIN_URL_RE = re.compile(r"https?://[^\s\)\]\"'<>]+")

_DOC_URL_CACHE: dict[str, str | None] = {}


def extract_doc_url(content: str) -> str | None:
    """Lấy URL gốc từ header markdown (**Source:** ...)."""
    match = SOURCE_URL_RE.search(content[:4000])
    if not match:
        return None
    return match.group(1).rstrip(").,;")


def extract_chunk_links(content: str, max_links: int = 6) -> list[str]:
    """Lấy các hyperlink có trong nội dung chunk."""
    seen: set[str] = set()
    links: list[str] = []

    for match in MARKDOWN_LINK_RE.finditer(content):
        url = match.group(1).strip()
        if url not in seen:
            seen.add(url)
            links.append(url)

    for match in PLAIN_URL_RE.finditer(content):
        url = match.group(0).rstrip(").,;")
        if len(url) > 400 or url in seen:
            continue
        seen.add(url)
        links.append(url)
        if len(links) >= max_links:
            break

    return links[:max_links]


def resolve_doc_url(source_name: str, doc_type: str, standardized_dir: Path) -> str | None:
    """Đọc URL gốc từ file markdown (có cache)."""
    cache_key = f"{doc_type}:{source_name}"
    if cache_key in _DOC_URL_CACHE:
        return _DOC_URL_CACHE[cache_key]

    subdirs = {
        "news": standardized_dir / "news",
        "legal": standardized_dir / "legal",
        "upload": standardized_dir / "uploads",
    }
    candidates = [subdirs.get(doc_type)]
    candidates.append(standardized_dir)

    url: str | None = None
    for base in candidates:
        if base is None or not base.exists():
            continue
        direct = base / source_name
        if direct.exists():
            url = extract_doc_url(direct.read_text(encoding="utf-8"))
            break
        for found in base.rglob(source_name):
            if found.is_file():
                url = extract_doc_url(found.read_text(encoding="utf-8"))
                break
        if url:
            break

    _DOC_URL_CACHE[cache_key] = url
    return url

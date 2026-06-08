"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# TODO: Điền danh sách URL bài báo cần crawl
ARTICLE_URLS = [
    "https://tuoitre.vn/khoi-to-3-bi-can-trong-vu-ca-si-miu-le-su-dung-ma-tuy-o-cat-ba-20260514230349573.htm",
    "https://kenh14.vn/toan-canh-be-boi-ma-tuy-cua-miu-le-su-sup-do-cua-nghe-si-dang-co-moi-thu-trong-tay-215260517071721899",
    "https://vov.vn/giai-tri/chua-day-1-thang-3-nghe-si-viet-bi-khoi-to-vi-lien-quan-ma-tuy-gay-chan-dong-post1293496",
    "https://tienphong.vn/nghe-si-dinh-ma-tuy-khoang-trong-sau-nhung-cu-truot-nga-post1845503",
    "https://congan.phutho.gov.vn/article/An-phat-tu-cho-hanh-vi-tai-su-dung-ma-tuy-Chinh-18660-48",
    "https://sotp.langson.gov.vn/tin-tuc-su-kien/quy-dinh-xu-ly-hanh-vi-su-dung-va-to-chuc-su-dung-trai-phep-chat-ma-tuy.html",
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "source_url": str,
            "date_crawled": str (ISO format),
            "content_markdown": str,
            "raw_text": str,
        }
    """
    import requests

    def build_jina_endpoint(source_url: str) -> str:
        normalized = source_url.strip()
        if normalized.startswith("https://"):
            normalized = normalized[len("https://") :]
        elif normalized.startswith("http://"):
            normalized = normalized[len("http://") :]
        return f"https://r.jina.ai/http://{normalized}"

    def parse_jina_response(text: str) -> dict:
        title = "Unknown"
        source = url
        published_time = None
        content = ""

        if "Title:" in text:
            for line in text.splitlines():
                if line.startswith("Title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("URL Source:"):
                    source = line.split(":", 1)[1].strip()
                elif line.startswith("Published Time:"):
                    published_time = line.split(":", 1)[1].strip()

        if "Markdown Content:" in text:
            content = text.split("Markdown Content:", 1)[1].strip()
        else:
            content = text.strip()

        return {
            "title": title,
            "source_url": source,
            "published_time": published_time,
            "content_markdown": content,
        }

    endpoint = build_jina_endpoint(url)
    response = requests.get(endpoint, timeout=60)
    response.raise_for_status()

    parsed = parse_jina_response(response.text)
    return {
        "url": url,
        "title": parsed["title"],
        "source_url": parsed["source_url"],
        "published_time": parsed["published_time"],
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": parsed["content_markdown"],
        "raw_text": response.text,
    }


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        try:
            article = await crawl_article(url)
        except Exception as exc:
            article = {
                "url": url,
                "title": "Failed to crawl",
                "source_url": url,
                "date_crawled": datetime.now().isoformat(),
                "content_markdown": "",
                "raw_text": str(exc),
                "error": str(exc),
            }
            print(f"  ⚠ Failed: {exc}")

        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())

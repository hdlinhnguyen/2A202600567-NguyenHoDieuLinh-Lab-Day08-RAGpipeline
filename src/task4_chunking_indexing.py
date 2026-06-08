"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho tiếng Việt)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - Weaviate (khuyến cáo: hỗ trợ hybrid search built-in)
    - ChromaDB (đơn giản, local)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers weaviate-client
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
VECTORSTORE_DIR = STANDARDIZED_DIR / "vectorstore"
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

CHUNK_SIZE = 500        #Vì sao chọn 500? Đủ ngữ cảnh nhưng không quá dài để embedding bị loãng
CHUNK_OVERLAP = 50      #Vì sao chọn 50? Giữ lại thông tin ranh giới giữa các chunk.
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  #Vì sao? Nhẹ, phổ biến, dễ chạy local và hỗ trợ tiếng Việt.
EMBEDDING_DIM = 384

VECTOR_STORE = "chromadb"  # "weaviate" | "chromadb" | "faiss" —> ChromaDB dễ setup local, hỗ trợ persist, và có hiệu năng tốt cho dataset nhỏ đến trung bình. Weaviate mạnh về hybrid search nhưng cần server riêng. FAISS chỉ dense search và không hỗ trợ metadata tốt. 


# =============================================================================
# HELPERS
# =============================================================================

def is_markdown_file(filepath: Path) -> bool:
    return filepath.suffix.lower() == ".md"


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def recursive_split(text: str, chunk_size: int, overlap: int) -> List[str]:
    separators = ["\n\n", "\n", ". ", " ", ""]

    def split_with_separator(value: str, separator: str) -> List[str]:
        if separator == "":
            return [value[i : i + chunk_size] for i in range(0, len(value), chunk_size)]

        chunks = []
        current = ""
        parts = value.split(separator)
        for part in parts:
            candidate = part if not current else f"{current}{separator}{part}"
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = part
        if current:
            chunks.append(current)
        return chunks

    def merge_overlap(chunks: List[str], overlap_size: int) -> List[str]:
        merged = []
        for i, chunk in enumerate(chunks):
            chunk_text = chunk.strip()
            if not chunk_text:
                continue
            if i == 0:
                merged.append(chunk_text)
                continue
            prev = merged[-1]
            max_allowed = chunk_size + overlap_size
            if overlap_size and len(prev) > overlap_size:
                overlap_text = prev[-overlap_size:]
            else:
                overlap_text = prev

            if overlap_text:
                separator = " " if not overlap_text.endswith(" ") and not chunk_text.startswith(" ") else ""
                combined = f"{overlap_text}{separator}{chunk_text}".strip()
            else:
                combined = chunk_text

            if len(combined) > max_allowed:
                allowed_overlap = max(0, max_allowed - len(chunk_text) - 1)
                if allowed_overlap <= 0:
                    combined = chunk_text
                else:
                    overlap_text = prev[-allowed_overlap:]
                    separator = " " if not overlap_text.endswith(" ") and not chunk_text.startswith(" ") else ""
                    combined = f"{overlap_text}{separator}{chunk_text}".strip()
            merged.append(combined)
        return [c for c in merged if c]

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    for separator in separators:
        pieces = split_with_separator(text, separator)
        if all(len(piece) <= chunk_size for piece in pieces):
            return merge_overlap(pieces, overlap)

    return merge_overlap([text[i : i + chunk_size] for i in range(0, len(text), chunk_size)], overlap)


def split_on_markdown_headers(text: str, chunk_size: int, overlap: int) -> List[str]:
    header_pattern = re.compile(r"(?m)^#{1,6} .+")
    positions = [m.start() for m in header_pattern.finditer(text)]
    if not positions:
        return recursive_split(text, chunk_size, overlap)

    positions.append(len(text))
    blocks = [text[start:end].strip() for start, end in zip(positions, positions[1:])]
    chunks = []
    for block in blocks:
        if len(block) <= chunk_size:
            chunks.append(block)
        else:
            chunks.extend(recursive_split(block, chunk_size, overlap))
    return chunks


def semantic_split(text: str, chunk_size: int, overlap: int) -> List[str]:
    return recursive_split(text, chunk_size, overlap)


def chunk_text(text: str) -> List[str]:
    if CHUNKING_METHOD == "markdown_header":
        return split_on_markdown_headers(text, CHUNK_SIZE, CHUNK_OVERLAP)
    if CHUNKING_METHOD == "semantic":
        return semantic_split(text, CHUNK_SIZE, CHUNK_OVERLAP)
    return recursive_split(text, CHUNK_SIZE, CHUNK_OVERLAP)


def create_chunk_id(metadata: dict, index: int) -> str:
    source = metadata.get("source", "unknown")
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:8]
    return f"{digest}_{index:04d}"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        raise FileNotFoundError(f"Standardized directory not found: {STANDARDIZED_DIR}")

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if not is_markdown_file(md_file):
            continue
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        doc_type = "legal" if "/legal" in str(md_file).replace("\\", "/") else "news"
        documents.append({
            "content": normalize_text(content),
            "metadata": {
                "source": md_file.name,
                "path": str(md_file),
                "doc_type": doc_type,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    chunks = []
    for doc_index, doc in enumerate(documents):
        split_texts = chunk_text(doc["content"])
        for chunk_index, text_chunk in enumerate(split_texts):
            chunks.append({
                "content": text_chunk.strip(),
                "metadata": {
                    **doc["metadata"],
                    "chunk_index": chunk_index,
                    "doc_index": doc_index,
                },
            })
    return [chunk for chunk in chunks if chunk["content"]]


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        texts = [chunk["content"] for chunk in chunks]
        embeddings = model.encode(texts, show_progress_bar=True)
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb.tolist()
        return chunks
    except ImportError:
        print("WARNING: sentence-transformers chưa được cài. Sử dụng fallback embedding đơn giản.")
    except Exception as exc:
        print(f"WARNING: Lỗi khi load embedding model: {exc}. Sử dụng fallback.")

    for chunk in chunks:
        tokens = re.findall(r"\w+", chunk["content"].lower())
        vector = [0.0] * EMBEDDING_DIM
        for term in tokens[: EMBEDDING_DIM * 2]:
            idx = abs(hash(term)) % EMBEDDING_DIM
            vector[idx] += 1.0
        chunk["embedding"] = [float(x) for x in vector]
    return chunks


def save_fallback_index(chunks: list[dict]):
    fallback_path = VECTORSTORE_DIR / "vectorstore_fallback.json"
    with fallback_path.open("w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"✓ Fallback vectorstore saved: {fallback_path}")


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    if VECTOR_STORE == "chromadb":
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            print("WARNING: chromadb chưa được cài. Lưu index vào JSON thay thế.")
            save_fallback_index(chunks)
            return
        else:
            client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=str(VECTORSTORE_DIR)))
            collection = client.get_or_create_collection(name="drug_law_chunks")
            ids = [create_chunk_id(chunk["metadata"], i) for i, chunk in enumerate(chunks)]
            documents = [chunk["content"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            embeddings = [chunk["embedding"] for chunk in chunks]
            collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
            client.persist()
            print(f"✓ ChromaDB index persisted: {VECTORSTORE_DIR}")
            return
    elif VECTOR_STORE == "weaviate":
        try:
            import weaviate
        except ImportError:
            print("WARNING: weaviate-client chưa được cài. Lưu index vào JSON thay thế.")
            save_fallback_index(chunks)
            return
        else:
            client = weaviate.Client("http://localhost:8080")
            class_name = "DrugLawChunk"
            if not client.schema.contains({"class": class_name}):
                class_obj = {
                    "class": class_name,
                    "vectorizer": "none",
                    "properties": [
                        {"name": "content", "dataType": ["text"]},
                        {"name": "source", "dataType": ["text"]},
                        {"name": "doc_type", "dataType": ["text"]},
                        {"name": "chunk_index", "dataType": ["int"]},
                    ],
                }
                client.schema.create_class(class_obj)
            with client.batch as batch:
                for chunk in chunks:
                    batch.add_data_object(
                        {
                            "content": chunk["content"],
                            "source": chunk["metadata"].get("source"),
                            "doc_type": chunk["metadata"].get("doc_type"),
                            "chunk_index": chunk["metadata"].get("chunk_index"),
                        },
                        class_name=class_name,
                        vector=chunk["embedding"],
                    )
            print("✓ Weaviate index created")
            return
    else:
        print(f"WARNING: VECTOR_STORE '{VECTOR_STORE}' không được hỗ trợ. Lưu index vào JSON thay thế.")

    local_index_path = VECTORSTORE_DIR / "vectorstore_fallback.json"
    with open(local_index_path, "w", encoding="utf-8") as out_file:
        json.dump(
            [
                {
                    "id": create_chunk_id(chunk["metadata"], i),
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "embedding": chunk["embedding"],
                }
                for i, chunk in enumerate(chunks)
            ],
            out_file,
            ensure_ascii=False,
            indent=2,
        )
    print(f"✓ Stored fallback vector index: {local_index_path}")


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()

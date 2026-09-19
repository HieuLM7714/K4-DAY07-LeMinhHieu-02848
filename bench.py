#!/usr/bin/env python3
"""
Benchmark tool for evaluating chunking strategies and retrieval quality (Lab 7 / Checkpoint 5).

4 Core Tasks:
1. Parse .md files, extracting YAML frontmatter to metadata and body to content.
2. Chunk content outside the store:
   Document(id=f"{path.stem}#{i}", content=chunk, metadata={**frontmatter, "doc_id": path.stem, ...})
3. Load into EmbeddingStore, run 5 benchmark queries through search_with_filter().
4. Output total loaded chunks and top-3 results per query (score, doc_id, chunk id, snippet).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    MockEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore


# ==============================================================================
# CUSTOM CHUNKER: HeadingChunker (R3)
# ==============================================================================
class HeadingChunker:
    """
    Split markdown text by section headings.
    Each section is a natural semantic unit. If a section exceeds max_chunk_size,
    it falls back to RecursiveChunker and prepends the heading to each sub-chunk
    so subsequent chunks never lose the section context.
    """

    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size
        self.fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split before markdown headings (#, ##, ...) or major section titles
        pattern = r"(?m)(?=^(?:#{1,6}\s+|Bước\s+\d+|Giai đoạn\s+\d+|HƯỚNG DẪN|Chuẩn bị trước khi bắt đầu))"
        raw_sections = re.split(pattern, text.strip())
        sections = [s.strip() for s in raw_sections if s.strip()]

        chunks: list[str] = []
        for sec in sections:
            if len(sec) <= self.max_chunk_size:
                chunks.append(sec)
            else:
                lines = sec.split("\n", 1)
                heading = lines[0].strip()
                body = lines[1].strip() if len(lines) > 1 else ""

                if not body:
                    chunks.append(sec)
                    continue

                sub_pieces = self.fallback.chunk(body)
                for i, piece in enumerate(sub_pieces):
                    if i == 0:
                        chunks.append(f"{heading}\n\n{piece}")
                    else:
                        chunks.append(f"[{heading}]\n\n{piece}")

        return chunks


# ==============================================================================
# CHỌN CHIẾN LƯỢC CHUNKER Ở ĐÂY (Mỗi thành viên chỉ đổi 1 dòng này để so sánh)
# ==============================================================================
# Chiến lược A: FixedSizeChunker(chunk_size=500, overlap=50)
# Chiến lược B: SentenceChunker(max_sentences_per_chunk=3)
# Chiến lược C: RecursiveChunker(chunk_size=500)
# Chiến lược D (Custom): HeadingChunker(max_chunk_size=500)

CHUNKER = HeadingChunker(max_chunk_size=500)
CHUNKER_NAME = "HeadingChunker (custom section + heading context preservation)"


# ==============================================================================
# 5 BENCHMARK QUERIES & GOLD ANSWERS (R2 chủ trì)
# ==============================================================================
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "type": "Hỏi điều kiện (Cần metadata_filter)",
        "query": "Thời gian ở nội trú bao lâu thì bắt buộc phải hoàn thành khảo sát trước khi gửi yêu cầu trả phòng?",
        "filter": {"audience": "student"},
        "gold_answer": "Sinh viên đã ở nội trú từ 5 tháng trở lên phải hoàn thành khảo sát trả phòng trước khi gửi được yêu cầu.",
        "target_doc": "huong-dan-tra-phong-ktx",
    },
    {
        "id": 2,
        "type": "Tra cứu số liệu & quy chuẩn",
        "query": "Tân sinh viên đăng ký ở Ký túc xá cần chuẩn bị ảnh chân dung kích thước bao nhiêu và mới chụp trong thời gian bao lâu?",
        "filter": None,
        "gold_answer": "Ảnh chân dung kích thước 4 x 6, mới chụp không quá 6 tháng, khuôn mặt chiếm khoảng 75% diện tích ảnh.",
        "target_doc": "dang-ky-ktx-tan-sinh-vien",
    },
    {
        "id": 3,
        "type": "Liệt kê thông tin",
        "query": "Sinh viên cần cung cấp những thông tin tài khoản ngân hàng nào để nhận lại tiền thế chân tài sản khi trả phòng Ký túc xá?",
        "filter": None,
        "gold_answer": "Thông tin tài khoản ngân hàng gồm: số tài khoản, tên chủ tài khoản và tên ngân hàng.",
        "target_doc": "huong-dan-tra-phong-ktx",
    },
    {
        "id": 4,
        "type": "Liệt kê phương thức",
        "query": "Có những cách nào để tra cứu thông tin và thời hạn sử dụng của thẻ Bảo hiểm y tế (BHYT)?",
        "filter": None,
        "gold_answer": "Có 3 cách: (1) Cổng thông tin Bảo hiểm xã hội Việt Nam, (2) Ứng dụng VssID, (3) Ứng dụng VNeID.",
        "target_doc": "tra-cuu-thong-tin-bhyt",
    },
    {
        "id": 5,
        "type": "Hỏi quy trình & website",
        "query": "Quy trình đăng ký hoạt động tại Ký túc xá gồm mấy bước và thực hiện trên website nào?",
        "filter": None,
        "gold_answer": "Quy trình gồm 4 bước, thực hiện trực tuyến tại website hoatdong.ktxhcm.edu.vn.",
        "target_doc": "dang-ky-hoat-dong-noi-tru",
    },
]


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================
def parse_markdown_with_frontmatter(file_path: Path) -> tuple[dict[str, str], str]:
    """Parse frontmatter from Markdown file into dict and return content body."""
    text = file_path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    content = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            content = parts[2].strip()
            for line in fm_text.splitlines():
                line = line.strip()
                if ":" in line and not line.startswith("#"):
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    metadata[key] = val

    return metadata, content


class CachedEmbedder:
    """Caching wrapper for API-based embedders (e.g. OpenAI) to avoid duplicate costs."""

    def __init__(self, base_embedder, cache_file: Path = Path(".embedding_cache.json")) -> None:
        self.base_embedder = base_embedder
        self.cache_file = cache_file
        self.cache: dict[str, list[float]] = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                self.cache = {}

    def __call__(self, text: str) -> list[float]:
        key = hashlib.md5(text.encode("utf-8")).hexdigest()
        if key in self.cache:
            return self.cache[key]
        emb = self.base_embedder(text)
        self.cache[key] = emb
        try:
            self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")
        except Exception:
            pass
        return emb


def get_embedder():
    """Load embedder based on environment configuration, defaulting to MockEmbedder."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()

    if provider == "openai":
        try:
            base = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
            return CachedEmbedder(base)
        except Exception as e:
            print(f"Warning: OpenAI embedder failed ({e}), falling back to mock.")
            return _mock_embed
    elif provider == "gemini":
        try:
            return GeminiEmbedder(model_name=os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL))
        except Exception as e:
            print(f"Warning: Gemini embedder failed ({e}), falling back to mock.")
            return _mock_embed
    elif provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as e:
            print(f"Warning: Local embedder failed ({e}), falling back to mock.")
            return _mock_embed
    return _mock_embed


# ==============================================================================
# MAIN BENCHMARK RUNNER
# ==============================================================================
def run_benchmark(corpus_dir: str = "data/tra-cuu-dao-tao-dich-vu") -> int:
    path_corpus = Path(corpus_dir)
    if not path_corpus.exists() or not path_corpus.is_dir():
        print(f"Lỗi: Không tìm thấy thư mục dữ liệu {corpus_dir}", file=sys.stderr)
        return 1

    md_files = sorted(path_corpus.glob("*.md"))
    if not md_files:
        print(f"Lỗi: Không có file .md nào trong {corpus_dir}", file=sys.stderr)
        return 1

    print("=" * 80)
    print("           CHƯƠNG TRÌNH ĐÁNH GIÁ TRUY XUẤT (BENCHMARK - CHECKPOINT 5)")
    print("=" * 80)
    print(f"Thư mục tài liệu : {corpus_dir} ({len(md_files)} files)")
    print(f"Chiến lược chọn  : {CHUNKER_NAME}")

    # 1 & 2: Đọc file, tách frontmatter, chunk ngoài store, tạo Documents
    all_chunks: list[Document] = []
    file_chunk_stats: dict[str, int] = {}

    for md_path in md_files:
        frontmatter, content_body = parse_markdown_with_frontmatter(md_path)
        doc_id = frontmatter.get("doc_id") or md_path.stem
        raw_chunks = CHUNKER.chunk(content_body)

        file_chunk_stats[doc_id] = len(raw_chunks)
        for i, chunk_text in enumerate(raw_chunks):
            chunk_doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk_text,
                metadata={
                    **frontmatter,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "source_file": md_path.as_posix(),
                },
            )
            all_chunks.append(chunk_doc)

    print(f"\n[1] Thống kê Chunking theo từng tài liệu:")
    for doc_id, count in file_chunk_stats.items():
        print(f"    - {doc_id:30}: {count:2} chunks")
    print(f"    --> Tổng số chunks nạp vào Store: {len(all_chunks)} chunks")

    # 3: Nạp vào EmbeddingStore
    embedder = get_embedder()
    store = EmbeddingStore(collection_name="benchmark_collection", embedding_fn=embedder)
    store.add_documents(all_chunks)

    # 4: Chạy 5 benchmark query
    print("\n" + "=" * 80)
    print("                  KẾT QUẢ TRUY XUẤT 5 CÂU HỎI BENCHMARK")
    print("=" * 80)

    for q in BENCHMARK_QUERIES:
        qid = q["id"]
        query = q["query"]
        q_filter = q["filter"]
        gold = q["gold_answer"]
        target = q["target_doc"]
        qtype = q["type"]

        print(f"\n--------------------------------------------------------------------------------")
        print(f"CÂU HỎI #{qid} [{qtype}]")
        print(f"Query       : {query}")
        print(f"Filter áp dụng: {q_filter}")
        print(f"Target Doc  : {target}")
        print(f"Gold Answer : {gold}")
        print(f"\nTop-3 kết quả truy xuất:")

        if q_filter:
            results = store.search_with_filter(query, metadata_filter=q_filter, top_k=3)
        else:
            results = store.search(query, top_k=3)

        if not results:
            print("   [KHÔNG TÌM THẤY KẾT QUẢ NÀO]")
            continue

        for rank, res in enumerate(results, start=1):
            score = res["score"]
            meta = res.get("metadata", {})
            res_doc_id = meta.get("doc_id", "N/A")
            chunk_idx = meta.get("chunk_index", "N/A")
            audience = meta.get("audience", "N/A")
            content_preview = res["content"].strip().replace("\n", " ")
            if len(content_preview) > 140:
                content_preview = content_preview[:140] + "..."

            is_match = "MATCH" if res_doc_id == target else "OTHER"
            print(f"   [{rank}] Score: {score:.4f} | Doc: {res_doc_id}#{chunk_idx} | Aud: {audience} | [{is_match}]")
            print(f"       Snippet: {content_preview}")

    print("\n" + "=" * 80)
    print("Hoàn tất chạy Benchmark Checkpoint 5!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_benchmark())


"""Indexer: PDF, MD, HTML, DOCX, TXT → chunks → embeddings → SQLite-vec + FTS5. Block 5.4."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import structlog

try:
    import sqlite_vec
except ImportError:
    sqlite_vec = None  # type: ignore[assignment]

from voiceforge.rag.embedder import MiniLMEmbedder, get_default_model_dir
from voiceforge.rag.incremental import (
    NewChunk,
    content_hash,
    get_existing_chunks,
    has_content_hash_column,
    plan_diff,
)
from voiceforge.rag.incremental import (
    delete_chunk as incremental_delete_chunk,
)
from voiceforge.rag.incremental import (
    delete_sources_not_in as incremental_delete_sources,
)
from voiceforge.rag.parsers import (
    parse_docx,
    parse_html,
    parse_markdown,
    parse_pdf,
    parse_txt,
)

log = structlog.get_logger()

_INSERT_FTS_CHUNKS = "INSERT INTO fts_chunks(content, chunk_id) VALUES (?,?)"
CHUNK_TOKENS = 400
CHUNK_OVERLAP_RATIO = 0.10

# Block 5.4: extensions and parser dispatch
_SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".html", ".htm", ".docx", ".txt"}
_PARSERS = {
    ".pdf": parse_pdf,
    ".md": parse_markdown,
    ".markdown": parse_markdown,
    ".html": parse_html,
    ".htm": parse_html,
    ".docx": parse_docx,
    ".txt": parse_txt,
}


@dataclass
class ChunkMeta:
    source: str
    page: int
    chunk_index: int
    timestamp: str


def _chunk_text(text: str, token_approx: int = CHUNK_TOKENS, overlap_ratio: float = CHUNK_OVERLAP_RATIO) -> list[str]:
    """Split text into ~token_approx words per chunk with overlap (by words, ~1 word ≈ 1 token)."""
    words = text.split()
    if not words:
        return []
    step = max(1, int(token_approx * (1 - overlap_ratio)))
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + token_approx, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = start + step
    return chunks


def _sections_to_new_chunks(sections: list[str]) -> list[NewChunk]:
    """Build NewChunk list from section texts (skips empty)."""
    new_chunks: list[NewChunk] = []
    for section_no, page_text in enumerate(sections, start=1):
        if not (page_text or "").strip():
            continue
        for idx, content in enumerate(_chunk_text(page_text)):
            if not content.strip():
                continue
            new_chunks.append(
                NewChunk(
                    page=section_no,
                    chunk_index=idx,
                    content=content,
                    content_hash=content_hash(content),
                )
            )
    return new_chunks


def _add_texts_legacy_reindex(
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    source: str,
    new_chunks: list,
    embedder: object,
    ts: str,
    dup_threshold: float,
) -> tuple[int, int, int]:
    """Backward compat: old DB without content_hash → full re-index for this source."""
    cursor.execute("SELECT id FROM chunks WHERE source = ?", (source,))
    for (cid,) in cursor.fetchall():
        incremental_delete_chunk(cursor, cid)
    added = 0
    for n in new_chunks:
        emb = embedder.encode([n.content])[0]
        if _is_duplicate_via_vec(cursor, emb, dup_threshold):
            continue
        cursor.execute(
            "INSERT INTO chunks(source, page, chunk_index, timestamp, content, content_hash) VALUES (?,?,?,?,?,?)",
            (source, n.page, n.chunk_index, ts, n.content, n.content_hash),
        )
        chunk_id = cursor.lastrowid
        if chunk_id is None:
            raise RuntimeError("Failed to get chunk id after insert")
        _insert_vec(cursor, chunk_id, emb)
        cursor.execute(_INSERT_FTS_CHUNKS, (n.content, chunk_id))
        added += 1
    conn.commit()
    log.info(
        "incremental.full_reindex",
        source=source,
        chunks_added=added,
        chunks_updated=0,
        chunks_deleted=0,
    )
    return (added, 0, 0)


def _init_db(conn: sqlite3.Connection) -> None:
    if sqlite_vec is None:
        raise ImportError("Install [rag]: uv sync --extra rag (sqlite-vec)")
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            page INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
            embedding float[384] distance_metric=cosine
        );
    """)
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts_chunks USING fts5(content, chunk_id UNINDEXED)")
    conn.commit()
    # Block 10.3: migration — add content_hash to existing DBs (backward compat)
    try:
        conn.execute("ALTER TABLE chunks ADD COLUMN content_hash TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass


class KnowledgeIndexer:
    """Index PDFs into SQLite-vec + FTS5 with ONNX embeddings; skip duplicates (cosine > 0.95)."""

    def __init__(
        self,
        db_path: str | Path,
        model_dir: str | Path | None = None,
        cosine_dup_threshold: float = 0.95,
    ) -> None:
        self.db_path = Path(db_path)
        self.model_dir = Path(model_dir or get_default_model_dir())
        self.dup_threshold = cosine_dup_threshold
        self._embedder: MiniLMEmbedder | None = None
        self._conn: sqlite3.Connection | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            _init_db(self._conn)
        return self._conn

    def _get_embedder(self) -> MiniLMEmbedder:
        if self._embedder is None:
            self._embedder = MiniLMEmbedder(self.model_dir)
        return self._embedder

    def _add_texts(self, source: str, sections: list[str]) -> tuple[int, int, int]:
        """Index text sections; incremental by content_hash. Return (added, updated, deleted). Block 10.3."""
        if not sections:
            return (0, 0, 0)
        conn = self._get_conn()
        embedder = self._get_embedder()
        cursor = conn.cursor()
        ts = datetime.now(UTC).isoformat()
        new_chunks = _sections_to_new_chunks(sections)

        if not has_content_hash_column(cursor):
            return _add_texts_legacy_reindex(cursor, conn, source, new_chunks, embedder, ts, self.dup_threshold)

        existing = get_existing_chunks(cursor, source)
        to_add, to_update, to_delete_ids = plan_diff(existing, new_chunks)

        for cid in to_delete_ids:
            incremental_delete_chunk(cursor, cid)
        deleted = len(to_delete_ids)

        for _id, n in to_update:
            emb = embedder.encode([n.content])[0]
            cursor.execute(
                "UPDATE chunks SET content = ?, content_hash = ?, timestamp = ? WHERE id = ?",
                (n.content, n.content_hash, ts, _id),
            )
            cursor.execute("DELETE FROM vec_chunks WHERE rowid = ?", (_id,))
            _insert_vec(cursor, _id, emb)
            cursor.execute("DELETE FROM fts_chunks WHERE chunk_id = ?", (_id,))
            cursor.execute(_INSERT_FTS_CHUNKS, (n.content, _id))
        updated_count = len(to_update)

        added = 0
        for n in to_add:
            emb = embedder.encode([n.content])[0]
            if _is_duplicate_via_vec(cursor, emb, self.dup_threshold):
                continue
            cursor.execute(
                "INSERT INTO chunks(source, page, chunk_index, timestamp, content, content_hash) VALUES (?,?,?,?,?,?)",
                (source, n.page, n.chunk_index, ts, n.content, n.content_hash),
            )
            chunk_id = cursor.lastrowid
            if chunk_id is None:
                raise RuntimeError("Failed to get chunk id after insert")
            _insert_vec(cursor, chunk_id, emb)
            cursor.execute(_INSERT_FTS_CHUNKS, (n.content, chunk_id))
            added += 1

        conn.commit()
        log.info(
            "incremental.diff",
            source=source,
            chunks_added=added,
            chunks_updated=updated_count,
            chunks_deleted=deleted,
        )
        return (added, updated_count, deleted)

    def add_file(self, path: str | Path) -> int:
        """Index one file by extension (PDF, MD, HTML, DOCX, TXT). Return chunks added."""
        path = Path(path).resolve()
        if not path.is_file():
            raise FileNotFoundError(str(path))
        suffix = path.suffix.lower()
        if suffix not in _PARSERS:
            raise ValueError(f"Unsupported format: {suffix}. Use one of {sorted(_SUPPORTED_EXTENSIONS)}")
        parser = _PARSERS[suffix]
        sections = parser(path)
        added, updated, deleted = self._add_texts(str(path), sections)
        log.info(
            "indexer.add_file",
            path=str(path),
            ext=suffix,
            chunks_added=added,
            chunks_updated=updated,
            chunks_deleted=deleted,
        )
        return added + updated

    def add_pdf(self, path: str | Path) -> int:
        """Index a PDF file; return number of chunks added. Prefer add_file() for multi-format."""
        return self.add_file(path)

    def prune_sources_not_in(
        self,
        keep_sources: set[str],
        only_under_prefix: str | None = None,
    ) -> int:
        """Block 10.3: delete chunks whose source not in keep_sources (e.g. deleted files). If only_under_prefix, only under that path."""
        conn = self._get_conn()
        cursor = conn.cursor()
        deleted = incremental_delete_sources(cursor, keep_sources, only_under_prefix)
        conn.commit()
        if deleted:
            log.info("incremental.prune", chunks_deleted=deleted, keep_sources=len(keep_sources))
        return deleted

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None


def _is_duplicate_via_vec(cursor: sqlite3.Cursor, embedding: np.ndarray, threshold: float) -> bool:
    """True if vec_chunks has a row with cosine sim >= threshold (cosine dist <= 1 - threshold)."""
    from sqlite_vec import serialize_float32

    blob = serialize_float32(embedding.astype(np.float32).tolist())
    row = cursor.execute(
        "SELECT distance FROM vec_chunks WHERE embedding MATCH ? AND k = 1",
        [blob],
    ).fetchone()
    if row is None:
        return False
    dist = row[0]
    return dist <= (1.0 - threshold)


def _insert_vec(cursor: sqlite3.Cursor, rowid: int, embedding: np.ndarray) -> None:
    from sqlite_vec import serialize_float32

    blob = serialize_float32(embedding.astype(np.float32).tolist())
    cursor.execute("INSERT INTO vec_chunks(rowid, embedding) VALUES (?,?)", (rowid, blob))

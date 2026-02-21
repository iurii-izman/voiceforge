"""Block 10.3: Incremental RAG — hash per chunk, update only changed, delete removed, prune deleted files."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass

import structlog

log = structlog.get_logger()


def content_hash(content: str) -> str:
    """SHA256 hash of chunk content for change detection."""
    return hashlib.sha256((content or "").strip().encode("utf-8")).hexdigest()


@dataclass
class NewChunk:
    page: int
    chunk_index: int
    content: str
    content_hash: str


@dataclass
class ExistingChunk:
    id: int
    page: int
    chunk_index: int
    content_hash: str | None


def get_existing_chunks(cursor: sqlite3.Cursor, source: str) -> list[ExistingChunk]:
    """Return existing chunks for source (id, page, chunk_index, content_hash). content_hash is None if column missing."""
    try:
        cursor.execute(
            "SELECT id, page, chunk_index, content_hash FROM chunks WHERE source = ? ORDER BY page, chunk_index",
            (source,),
        )
        # SELECT always fetches 4 columns; content_hash is None when the column value is NULL
        return [
            ExistingChunk(
                id=row[0],
                page=row[1],
                chunk_index=row[2],
                content_hash=row[3],
            )
            for row in cursor.fetchall()
        ]
    except sqlite3.OperationalError as e:
        err = str(e).lower()
        # Expected on old schema without content_hash column or fresh DB — treat as empty
        if "no such column" in err or "no such table" in err:
            return []
        # Unexpected errors (lock, disk I/O) should be visible — caller can decide
        log.warning("rag.get_existing_chunks_failed", source=source, error=str(e))
        return []


def plan_diff(
    existing: list[ExistingChunk],
    new_chunks: list[NewChunk],
) -> tuple[list[NewChunk], list[tuple[int, NewChunk]], list[int]]:
    """Return (to_add, to_update, to_delete). to_update = (existing_id, NewChunk)."""
    by_key = {(e.page, e.chunk_index): e for e in existing}
    new_by_key = {(n.page, n.chunk_index): n for n in new_chunks}
    to_add: list[NewChunk] = []
    to_update: list[tuple[int, NewChunk]] = []
    to_delete: list[int] = []
    for key, e in by_key.items():
        if key not in new_by_key:
            to_delete.append(e.id)
        else:
            n = new_by_key[key]
            if e.content_hash is None or e.content_hash != n.content_hash:
                to_update.append((e.id, n))
    for key, n in new_by_key.items():
        if key not in by_key:
            to_add.append(n)
    return (to_add, to_update, to_delete)


def has_content_hash_column(cursor: sqlite3.Cursor) -> bool:
    """True if chunks table has content_hash column (Block 10.3)."""
    cursor.execute("PRAGMA table_info(chunks)")
    cols = [row[1] for row in cursor.fetchall()]
    return "content_hash" in cols


def delete_sources_not_in(
    cursor: sqlite3.Cursor,
    keep_sources: set[str],
    only_under_prefix: str | None = None,
) -> int:
    """Delete chunks whose source is not in keep_sources. If only_under_prefix, only consider sources under that path. Return number deleted."""
    cursor.execute("SELECT DISTINCT source FROM chunks")
    all_sources = {row[0] for row in cursor.fetchall()}
    to_remove = all_sources - keep_sources
    if only_under_prefix:
        to_remove = {s for s in to_remove if s.startswith(only_under_prefix)}
    if not to_remove:
        return 0
    deleted = 0
    for source in to_remove:
        cursor.execute("SELECT id FROM chunks WHERE source = ?", (source,))
        ids = [row[0] for row in cursor.fetchall()]
        for cid in ids:
            delete_chunk(cursor, cid)
            deleted += 1
    return deleted


def delete_chunk(cursor: sqlite3.Cursor, chunk_id: int) -> None:
    """Delete one chunk from chunks, vec_chunks (by rowid), fts_chunks (by chunk_id)."""
    cursor.execute("DELETE FROM vec_chunks WHERE rowid = ?", (chunk_id,))
    cursor.execute("DELETE FROM fts_chunks WHERE chunk_id = ?", (chunk_id,))
    cursor.execute("DELETE FROM chunks WHERE id = ?", (chunk_id,))

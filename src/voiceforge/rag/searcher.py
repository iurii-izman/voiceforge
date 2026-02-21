"""Hybrid search: BM25 (FTS5) + cosine (sqlite-vec), Reciprocal Rank Fusion."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import numpy as np
import structlog

try:
    import sqlite_vec
except ImportError:
    sqlite_vec = None  # type: ignore[assignment]

from voiceforge.rag.embedder import MiniLMEmbedder, get_default_model_dir

log = structlog.get_logger()

RRF_K = 60


def _sanitize_fts5_query(query: str) -> str:
    """Escape FTS5 special chars to prevent OperationalError from operators like OR/AND/"/(/).
    Wraps entire query in double-quotes (phrase search), escaping any internal double-quotes."""
    safe = query.replace('"', '""')
    return f'"{safe}"'


@dataclass
class SearchResult:
    """One search hit."""

    chunk_id: int
    content: str
    source: str
    page: int
    chunk_index: int
    timestamp: str
    score: float


def _reciprocal_rank_fusion(
    fts_ranked: list[tuple[int, float]],
    vec_ranked: list[tuple[int, float]],
    k: int = RRF_K,
) -> list[tuple[int, float]]:
    """Merge two (id, rank_or_score) lists by RRF; return (id, rrf_score) sorted by score desc."""
    scores: dict[int, float] = {}
    for rank, (cid, _) in enumerate(fts_ranked, start=1):
        scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank)
    for rank, (cid, _) in enumerate(vec_ranked, start=1):
        scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


class HybridSearcher:
    """BM25 (FTS5) + cosine (sqlite-vec), RRF fusion."""

    def __init__(
        self,
        db_path: str,
        model_dir: str | None = None,
    ) -> None:
        self.db_path = db_path
        self.model_dir = model_dir or get_default_model_dir()
        self._conn: sqlite3.Connection | None = None
        self._embedder: MiniLMEmbedder | None = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            if sqlite_vec:
                self._conn.enable_load_extension(True)
                sqlite_vec.load(self._conn)
                self._conn.enable_load_extension(False)
        return self._conn

    def _get_embedder(self) -> MiniLMEmbedder:
        if self._embedder is None:
            self._embedder = MiniLMEmbedder(self.model_dir)
        return self._embedder

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Hybrid search: FTS5 + vec, RRF; return top_k SearchResults."""
        conn = self._get_conn()
        cursor = conn.cursor()
        # FTS5: phrase search, get chunk_id and bm25 score
        fts_ids: list[tuple[int, float]] = []
        try:
            fts_sql = (
                "SELECT chunk_id, bm25(fts_chunks) FROM fts_chunks WHERE fts_chunks MATCH ? ORDER BY bm25(fts_chunks) LIMIT ?"
            )
            for row in cursor.execute(fts_sql, (_sanitize_fts5_query(query), top_k * 3)):
                fts_ids.append((row[0], row[1]))
        except sqlite3.OperationalError as e:
            log.warning("rag.fts_fallback_to_vector", error=str(e))
        # Vec: embed query, k-NN
        vec_ids: list[tuple[int, float]] = []
        if sqlite_vec:
            embedder = self._get_embedder()
            q_emb = embedder.encode([query])[0]
            from sqlite_vec import serialize_float32

            blob = serialize_float32(q_emb.astype(np.float32).tolist())
            k_vec = top_k * 3
            vec_sql = "SELECT rowid, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ? ORDER BY distance"
            for row in cursor.execute(vec_sql, [blob, k_vec]):
                vec_ids.append((row[0], row[1]))
        # RRF
        merged = _reciprocal_rank_fusion(fts_ids, vec_ids, k=RRF_K)[:top_k]
        if not merged:
            return []
        ids = [m[0] for m in merged]
        ids_json = "[" + ",".join(str(int(i)) for i in ids) + "]"
        cursor.execute(
            "SELECT id, content, source, page, chunk_index, timestamp FROM chunks WHERE id IN (SELECT value FROM json_each(?))",
            (ids_json,),
        )
        rows = {r[0]: r for r in cursor.fetchall()}
        results: list[SearchResult] = []
        for cid, rrf_score in merged:
            r = rows.get(cid)
            if not r:
                continue
            results.append(
                SearchResult(
                    chunk_id=r[0],
                    content=r[1],
                    source=r[2],
                    page=r[3],
                    chunk_index=r[4],
                    timestamp=r[5],
                    score=rrf_score,
                )
            )
        return results

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

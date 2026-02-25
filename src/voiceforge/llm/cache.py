"""LLM response cache: content-hash key, SQLite, TTL. C4 (#44)."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

TABLE_DDL = """
CREATE TABLE IF NOT EXISTS response_cache (
    key_hash TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    response_model_name TEXT NOT NULL,
    result_json TEXT NOT NULL,
    cost_usd REAL NOT NULL,
    created_at TEXT NOT NULL
);
"""

_init_done_paths: set[str] = set()
_init_lock = threading.Lock()


def _cache_db_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "voiceforge" / "llm_response_cache.db"


def _get_conn() -> sqlite3.Connection:
    path = _cache_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db_str = str(path)
    conn = sqlite3.connect(db_str)
    if db_str not in _init_done_paths:
        with _init_lock:
            if db_str not in _init_done_paths:
                conn.execute(TABLE_DDL)
                conn.commit()
                _init_done_paths.add(db_str)
    return conn


def cache_key(prompt: list[dict[str, Any]], model_id: str, response_model_name: str) -> str:
    """Stable hash for (prompt, model, schema). Same input → same key."""
    payload = json.dumps(
        {"messages": prompt, "model": model_id, "schema": response_model_name},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get(
    key_hash: str,
    response_model: type[T],
    ttl_seconds: int,
) -> tuple[T, float] | None:
    """Return (parsed instance, cost_usd) if cached and not expired; else None."""
    if ttl_seconds <= 0:
        return None
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT result_json, cost_usd, created_at FROM response_cache WHERE key_hash = ?",
            (key_hash,),
        ).fetchone()
        if not row:
            return None
        result_json, cost_usd, created_at_str = row
        created = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        if (datetime.now(UTC) - created).total_seconds() > ttl_seconds:
            conn.execute("DELETE FROM response_cache WHERE key_hash = ?", (key_hash,))
            conn.commit()
            return None
        data = json.loads(result_json)
        return (response_model.model_validate(data), float(cost_usd))
    finally:
        conn.close()


def set(
    key_hash: str,
    model_id: str,
    response_model_name: str,
    result: BaseModel,
    cost_usd: float,
    ttl_seconds: int,
) -> None:
    """Store result in cache. TTL is enforced on get; optionally purge expired rows."""
    if ttl_seconds <= 0:
        return
    conn = _get_conn()
    try:
        created_at = datetime.now(UTC).isoformat()
        result_json = result.model_dump_json()
        conn.execute(
            "INSERT OR REPLACE INTO response_cache (key_hash, model_id, response_model_name, result_json, cost_usd, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (key_hash, model_id, response_model_name, result_json, cost_usd, created_at),
        )
        conn.commit()
        _purge_expired(conn, ttl_seconds)
    finally:
        conn.close()


def _purge_expired(conn: sqlite3.Connection, ttl_seconds: int) -> None:
    """Remove entries older than ttl_seconds. Call after set to limit DB size."""
    try:
        cutoff = (datetime.now(UTC).timestamp() - ttl_seconds) * 1000
        # SQLite stores ISO text; compare as string for simplicity (ISO sortable)
        cutoff_iso = datetime.fromtimestamp(cutoff / 1000.0, tz=UTC).isoformat()
        conn.execute("DELETE FROM response_cache WHERE created_at < ?", (cutoff_iso,))
        conn.commit()
    except sqlite3.OperationalError:
        conn.rollback()

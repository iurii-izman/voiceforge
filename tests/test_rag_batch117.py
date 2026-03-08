"""Reproducible RAG lifecycle confidence batch (#117)."""

from __future__ import annotations

import sqlite3
import sys
import types
from pathlib import Path

from typer.testing import CliRunner

from voiceforge import main as main_mod
from voiceforge.rag import incremental, searcher

runner = CliRunner()


def test_index_directory_skips_excluded_and_collects_indexed_paths(tmp_path: Path, monkeypatch) -> None:
    included = tmp_path / "keep.txt"
    excluded = tmp_path / "skip.tmp.txt"
    nested = tmp_path / "nested" / "note.md"
    nested.parent.mkdir()
    included.write_text("keep", encoding="utf-8")
    excluded.write_text("skip", encoding="utf-8")
    nested.write_text("nested", encoding="utf-8")

    added: list[Path] = []

    class FakeIndexer:
        def add_file(self, path: Path) -> int:
            added.append(path)
            return 2

    total, indexed_paths = main_mod._index_directory(FakeIndexer(), tmp_path, ["*.tmp.txt"])

    assert total == 4
    assert sorted(path.name for path in added) == ["keep.txt", "note.md"]
    assert indexed_paths == {str(included.resolve()), str(nested.resolve())}


def test_index_command_directory_prunes_removed_sources_with_fake_indexer(monkeypatch, tmp_path: Path) -> None:
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    (kb_dir / "keep.txt").write_text("keep", encoding="utf-8")
    (kb_dir / "skip.md").write_text("skip", encoding="utf-8")
    rag_db = tmp_path / "rag.db"

    records: dict[str, object] = {"init": [], "added": [], "pruned": []}

    class FakeKnowledgeIndexer:
        def __init__(self, db_path: str) -> None:
            records["init"].append(db_path)  # type: ignore[index]

        def add_file(self, path: Path) -> int:
            records["added"].append(path.name)  # type: ignore[index]
            return 3

        def prune_sources_not_in(self, keep_sources: set[str], only_under_prefix: str | None = None) -> int:
            records["pruned"].append((sorted(keep_sources), only_under_prefix))  # type: ignore[index]
            return 2

        def close(self) -> None:
            records["closed"] = True

    fake_indexer_module = types.ModuleType("voiceforge.rag.indexer")
    fake_indexer_module.KnowledgeIndexer = FakeKnowledgeIndexer
    monkeypatch.setitem(sys.modules, "voiceforge.rag.indexer", fake_indexer_module)
    monkeypatch.setattr(
        main_mod,
        "_get_config",
        lambda: types.SimpleNamespace(get_rag_db_path=lambda: str(rag_db), rag_exclude_patterns=["skip.md"]),
    )

    result = runner.invoke(main_mod.app, ["index", str(kb_dir)])

    assert result.exit_code == 0, result.stdout
    assert records["init"] == [str(rag_db)]
    assert records["added"] == ["keep.txt"]
    assert records["pruned"] == [([str((kb_dir / "keep.txt").resolve())], str(kb_dir.resolve()))]
    assert "Удалено чанков (файлы удалены): 2" in result.stdout
    assert "Добавлено чанков: 3" in result.stdout


def test_rag_export_writes_backup_metadata_with_optional_content(monkeypatch, tmp_path: Path) -> None:
    rag_db = tmp_path / "rag.db"
    conn = sqlite3.connect(rag_db)
    conn.execute(
        "CREATE TABLE chunks (id INTEGER PRIMARY KEY, source TEXT, page INTEGER, chunk_index INTEGER, timestamp TEXT, content TEXT)"
    )
    conn.executemany(
        "INSERT INTO chunks(id, source, page, chunk_index, timestamp, content) VALUES (?,?,?,?,?,?)",
        [
            (1, "/docs/a.md", 1, 0, "2026-03-08T10:00:00+00:00", "Chunk A"),
            (2, "/docs/b.md", 2, 1, "2026-03-08T11:00:00+00:00", "Chunk B"),
        ],
    )
    conn.commit()
    conn.close()

    monkeypatch.setattr(main_mod, "_get_config", lambda: types.SimpleNamespace(get_rag_db_path=lambda: str(rag_db)))

    out_json = tmp_path / "rag-export.json"
    result = runner.invoke(main_mod.app, ["rag-export", "--output", str(out_json)])
    assert result.exit_code == 0, result.stdout
    payload = __import__("json").loads(out_json.read_text(encoding="utf-8"))
    assert payload["sources"] == ["/docs/a.md", "/docs/b.md"]
    assert payload["chunks_count"] == 2
    assert "content" not in payload["chunks"][0]

    out_json_with_content = tmp_path / "rag-export-content.json"
    result_with_content = runner.invoke(
        main_mod.app,
        ["rag-export", "--output", str(out_json_with_content), "--content"],
    )
    assert result_with_content.exit_code == 0, result_with_content.stdout
    payload_with_content = __import__("json").loads(out_json_with_content.read_text(encoding="utf-8"))
    assert payload_with_content["chunks"][0]["content"] == "Chunk A"


def test_incremental_restore_helpers_plan_and_prune(tmp_path: Path) -> None:
    conn = sqlite3.connect(tmp_path / "rag.db")
    conn.execute(
        "CREATE TABLE chunks (id INTEGER PRIMARY KEY, source TEXT, page INTEGER, chunk_index INTEGER, content_hash TEXT)"
    )
    conn.execute("CREATE TABLE vec_chunks (rowid INTEGER PRIMARY KEY, embedding BLOB)")
    conn.execute("CREATE TABLE fts_chunks (content TEXT, chunk_id INTEGER)")
    conn.executemany(
        "INSERT INTO chunks(id, source, page, chunk_index, content_hash) VALUES (?,?,?,?,?)",
        [
            (1, "/kb/a.txt", 1, 0, "hash-a0"),
            (2, "/kb/a.txt", 1, 1, "hash-a1"),
            (3, "/kb/old.txt", 1, 0, "hash-old"),
        ],
    )
    conn.executemany("INSERT INTO vec_chunks(rowid, embedding) VALUES (?, ?)", [(1, b"a"), (2, b"b"), (3, b"c")])
    conn.executemany(
        "INSERT INTO fts_chunks(content, chunk_id) VALUES (?, ?)",
        [("Chunk A0", 1), ("Chunk A1", 2), ("Chunk old", 3)],
    )
    conn.commit()

    cursor = conn.cursor()
    assert incremental.has_content_hash_column(cursor) is True
    existing = incremental.get_existing_chunks(cursor, "/kb/a.txt")
    assert [(row.id, row.page, row.chunk_index, row.content_hash) for row in existing] == [
        (1, 1, 0, "hash-a0"),
        (2, 1, 1, "hash-a1"),
    ]

    to_add, to_update, to_delete = incremental.plan_diff(
        existing,
        [
            incremental.NewChunk(page=1, chunk_index=0, content="same", content_hash="hash-a0"),
            incremental.NewChunk(page=1, chunk_index=1, content="updated", content_hash="hash-new"),
            incremental.NewChunk(page=2, chunk_index=0, content="new", content_hash="hash-add"),
        ],
    )
    assert [(row.page, row.chunk_index) for row in to_add] == [(2, 0)]
    assert [(row_id, chunk.page, chunk.chunk_index) for row_id, chunk in to_update] == [(2, 1, 1)]
    assert to_delete == []

    deleted = incremental.delete_sources_not_in(cursor, {"/kb/a.txt"}, only_under_prefix="/kb")
    conn.commit()
    assert deleted == 1
    assert cursor.execute("SELECT COUNT(*) FROM chunks WHERE source = '/kb/old.txt'").fetchone()[0] == 0
    assert cursor.execute("SELECT COUNT(*) FROM vec_chunks WHERE rowid = 3").fetchone()[0] == 0
    assert cursor.execute("SELECT COUNT(*) FROM fts_chunks WHERE chunk_id = 3").fetchone()[0] == 0
    conn.close()


def test_searcher_helpers_cover_query_sanitization_and_rrf() -> None:
    assert searcher._sanitize_fts5_query('alpha "OR" beta') == '"alpha ""OR"" beta"'
    fused = searcher._reciprocal_rank_fusion([(1, 0.1), (2, 0.2)], [(2, 0.3), (3, 0.4)], k=10)
    assert [chunk_id for chunk_id, _score in fused] == [2, 1, 3]

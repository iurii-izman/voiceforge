from __future__ import annotations

import sqlite3
import sys
import types
from pathlib import Path
from types import SimpleNamespace

from conftest import raise_when_called

from voiceforge.rag.watcher import KBWatcher, WatchIndexResult, _ensure_indexed_table, _file_sha256


def test_watcher_debounce_and_pending_processing(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 test")
    txt_path = tmp_path / "note.txt"
    txt_path.write_text("hello")

    watcher = KBWatcher(tmp_path, tmp_path / "rag.db", debounce_sec=3.0)
    processed: list[str] = []

    monkeypatch.setattr(
        watcher,
        "_index_if_needed",
        lambda path: processed.append(str(path)) or WatchIndexResult(path=str(path), status="indexed", added=1),
    )

    assert watcher._on_pdf_event(str(txt_path), now=10.0) is False
    assert watcher._on_pdf_event(str(pdf_path), now=10.0) is True
    assert watcher.pending_count() == 1

    assert watcher._process_pending(now=12.0) == []
    assert watcher.pending_count() == 1

    results = watcher._process_pending(now=13.1)
    assert [result.status for result in results] == ["indexed"]
    assert processed == [str(pdf_path.resolve())]
    assert watcher.pending_count() == 0


def test_watcher_index_if_needed_skips_unchanged(tmp_path: Path, monkeypatch) -> None:
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 same")
    db_path = tmp_path / "rag.db"
    watcher = KBWatcher(tmp_path, db_path)

    sha = _file_sha256(pdf_path)
    conn = sqlite3.connect(str(db_path))
    _ensure_indexed_table(conn)
    conn.execute("INSERT INTO indexed_files(path, sha256) VALUES (?, ?)", (str(pdf_path.resolve()), sha))
    conn.commit()
    conn.close()

    init_calls: list[Path] = []

    class FakeKnowledgeIndexer:
        def __init__(self, db_path: Path) -> None:
            init_calls.append(db_path)

    fake_indexer = types.ModuleType("voiceforge.rag.indexer")
    fake_indexer.KnowledgeIndexer = FakeKnowledgeIndexer
    monkeypatch.setitem(sys.modules, "voiceforge.rag.indexer", fake_indexer)

    result = watcher._index_if_needed(pdf_path)

    assert result.status == "skipped"
    assert result.reason == "unchanged"
    assert init_calls == []


def test_watcher_index_if_needed_indexes_and_updates_hash(tmp_path: Path, monkeypatch) -> None:
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 first")
    db_path = tmp_path / "rag.db"
    watcher = KBWatcher(tmp_path, db_path)
    add_calls: list[str] = []
    close_calls: list[str] = []

    class FakeKnowledgeIndexer:
        def __init__(self, db_arg: Path) -> None:
            assert db_arg == db_path

        def add_pdf(self, path: Path) -> int:
            add_calls.append(str(path))
            return 4

        def close(self) -> None:
            close_calls.append("closed")

    fake_indexer = types.ModuleType("voiceforge.rag.indexer")
    fake_indexer.KnowledgeIndexer = FakeKnowledgeIndexer
    monkeypatch.setitem(sys.modules, "voiceforge.rag.indexer", fake_indexer)

    result = watcher._index_if_needed(pdf_path)

    assert result.status == "indexed"
    assert result.added == 4
    assert add_calls == [str(pdf_path.resolve())]
    assert close_calls == ["closed"]

    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT sha256 FROM indexed_files WHERE path = ?", (str(pdf_path.resolve()),)).fetchone()
    conn.close()
    assert row == (_file_sha256(pdf_path),)


def test_watcher_index_if_needed_handles_sha_and_index_errors(tmp_path: Path, monkeypatch) -> None:
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 error")
    db_path = tmp_path / "rag.db"
    watcher = KBWatcher(tmp_path, db_path)

    monkeypatch.setattr("voiceforge.rag.watcher._file_sha256", raise_when_called(OSError("busy")))
    sha_result = watcher._index_if_needed(pdf_path)
    assert sha_result.status == "sha256_failed"
    assert sha_result.reason == "busy"

    monkeypatch.setattr("voiceforge.rag.watcher._file_sha256", lambda path: "sha-1")

    class BrokenKnowledgeIndexer:
        def __init__(self, db_arg: Path) -> None:
            assert db_arg == db_path

        def add_pdf(self, path: Path) -> int:
            raise RuntimeError("index failed")

        def close(self) -> None:
            raise AssertionError("close should not be called after add_pdf failure in current implementation")

    fake_indexer = types.ModuleType("voiceforge.rag.indexer")
    fake_indexer.KnowledgeIndexer = BrokenKnowledgeIndexer
    monkeypatch.setitem(sys.modules, "voiceforge.rag.indexer", fake_indexer)

    error_result = watcher._index_if_needed(pdf_path)
    assert error_result.status == "error"
    assert error_result.reason == "index failed"


def test_watcher_run_registers_handler_and_stops_cleanly(monkeypatch, tmp_path: Path) -> None:
    watch_dir = tmp_path / "kb"
    watch_dir.mkdir()
    pdf_path = watch_dir / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 watcher")
    db_path = tmp_path / "rag" / "rag.db"
    watcher = KBWatcher(watch_dir, db_path, poll_interval=0.01)
    watcher.stop()
    observed: dict[str, object] = {}

    class FakeObserver:
        def schedule(self, handler, path: str, recursive: bool = False) -> None:
            observed["handler"] = handler
            observed["path"] = path
            observed["recursive"] = recursive

        def start(self) -> None:
            observed["started"] = True

        def stop(self) -> None:
            observed["stopped"] = True

        def join(self, timeout: float | None = None) -> None:
            observed["join_timeout"] = timeout

    fake_events = types.ModuleType("watchdog.events")
    fake_events.FileSystemEventHandler = object
    fake_observers = types.ModuleType("watchdog.observers")
    fake_observers.Observer = FakeObserver
    monkeypatch.setitem(sys.modules, "watchdog.events", fake_events)
    monkeypatch.setitem(sys.modules, "watchdog.observers", fake_observers)

    watcher.run()

    assert observed["path"] == str(watch_dir.resolve())
    assert observed["recursive"] is True
    assert observed["started"] is True
    assert observed["stopped"] is True
    assert observed["join_timeout"] == 2
    assert db_path.exists()

    handler = observed["handler"]
    handler.on_created(SimpleNamespace(is_directory=False, src_path=str(pdf_path)))
    assert watcher.pending_count() == 1
    handler.on_modified(SimpleNamespace(is_directory=True, src_path=str(pdf_path)))
    assert watcher.pending_count() == 1


def test_watcher_run_missing_directory_raises(monkeypatch, tmp_path: Path) -> None:
    watcher = KBWatcher(tmp_path / "missing", tmp_path / "rag.db")

    fake_events = types.ModuleType("watchdog.events")
    fake_events.FileSystemEventHandler = object
    fake_observers = types.ModuleType("watchdog.observers")
    fake_observers.Observer = object
    monkeypatch.setitem(sys.modules, "watchdog.events", fake_events)
    monkeypatch.setitem(sys.modules, "watchdog.observers", fake_observers)

    try:
        watcher.run()
    except FileNotFoundError as exc:
        assert "Watch dir not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError")

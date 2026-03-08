"""KB watcher: auto-index PDFs on create/modify. Debounce 3 sec, SHA-256 dedup."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import structlog

log = structlog.get_logger()

DEBOUNCE_SEC = 3.0
INDEXED_FILES_TABLE = "indexed_files"


@dataclass(frozen=True)
class WatchIndexResult:
    """Outcome of one watcher indexing attempt."""

    path: str
    status: str
    sha256: str | None = None
    added: int | None = None
    reason: str | None = None


def _ensure_indexed_table(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS indexed_files(path TEXT PRIMARY KEY, sha256 TEXT)")
    conn.commit()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class KBWatcher:
    """Watch a directory for PDF changes; auto-index with debounce and SHA-256 dedup."""

    def __init__(
        self,
        watch_dir: Path,
        db_path: Path,
        poll_interval: float = 5.0,
        debounce_sec: float = DEBOUNCE_SEC,
    ) -> None:
        self.watch_dir = Path(watch_dir).resolve()
        self.db_path = Path(db_path)
        self.poll_interval = poll_interval
        self.debounce_sec = debounce_sec
        self._pending: dict[str, float] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()

    @staticmethod
    def _normalize_pdf_path(path: str | Path) -> Path | None:
        p = Path(path)
        if p.suffix.lower() != ".pdf" or not p.is_file():
            return None
        return p.resolve()

    def _on_pdf_event(self, path: str, *, now: float | None = None) -> bool:
        resolved = self._normalize_pdf_path(path)
        if resolved is None:
            return False
        with self._lock:
            self._pending[str(resolved)] = time.monotonic() if now is None else now
        return True

    def pending_count(self) -> int:
        with self._lock:
            return len(self._pending)

    def _process_pending(self, *, now: float | None = None) -> list[WatchIndexResult]:
        current_time = time.monotonic() if now is None else now
        to_process: list[str] = []
        with self._lock:
            for path, ts in tuple(self._pending.items()):
                if current_time - ts >= self.debounce_sec:
                    to_process.append(path)
                    del self._pending[path]

        results: list[WatchIndexResult] = []
        for path_str in to_process:
            results.append(self._index_if_needed(Path(path_str)))
        return results

    def _index_if_needed(self, path: Path) -> WatchIndexResult:
        resolved = self._normalize_pdf_path(path)
        path_str = str(Path(path).resolve())
        if resolved is None:
            return WatchIndexResult(path=path_str, status="ignored", reason="not_a_pdf")
        try:
            sha = _file_sha256(resolved)
        except OSError as e:
            log.error("watcher.sha256_failed", path=path_str, error=str(e))
            return WatchIndexResult(path=path_str, status="sha256_failed", reason=str(e))

        conn = sqlite3.connect(str(self.db_path))
        _ensure_indexed_table(conn)
        row = conn.execute("SELECT sha256 FROM indexed_files WHERE path = ?", (path_str,)).fetchone()
        if row and row[0] == sha:
            log.info("watcher.skipped", path=path_str, reason="unchanged")
            conn.close()
            return WatchIndexResult(path=path_str, status="skipped", sha256=sha, reason="unchanged")

        try:
            from voiceforge.rag.indexer import KnowledgeIndexer

            indexer = KnowledgeIndexer(self.db_path)
            added = indexer.add_pdf(resolved)
            indexer.close()
            conn.execute(
                "INSERT OR REPLACE INTO indexed_files(path, sha256) VALUES (?,?)",
                (path_str, sha),
            )
            conn.commit()
            log.info("watcher.indexed", path=path_str, added=added)
            return WatchIndexResult(path=path_str, status="indexed", sha256=sha, added=added)
        except Exception as e:
            log.error("watcher.error", path=path_str, error=str(e))
            return WatchIndexResult(path=path_str, status="error", sha256=sha, reason=str(e))
        finally:
            conn.close()

    def _worker_loop(self) -> None:
        while not self._stop.wait(1.0):
            self._process_pending()

    def run(self) -> None:
        """Start watching; blocks until stop."""
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            raise ImportError("Install [rag]: uv sync --extra rag (watchdog)") from None

        if not self.watch_dir.is_dir():
            raise FileNotFoundError(f"Watch dir not found: {self.watch_dir}")

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        _ensure_indexed_table(conn)
        conn.close()

        class Handler(FileSystemEventHandler):
            @staticmethod
            def _handle_event(event) -> None:
                if event.is_directory:
                    return
                self._on_pdf_event(event.src_path)

            def on_created(inner_self, event):
                inner_self._handle_event(event)

            def on_modified(inner_self, event):
                inner_self._handle_event(event)

        observer = Observer()
        observer.schedule(Handler(), str(self.watch_dir), recursive=True)
        observer.start()
        worker = threading.Thread(target=self._worker_loop, daemon=True)
        worker.start()

        log.info(
            "watcher.start",
            watch_dir=str(self.watch_dir),
            db_path=str(self.db_path),
            debounce_sec=self.debounce_sec,
        )
        try:
            while not self._stop.wait(self.poll_interval):
                pending_count = self.pending_count()
                if pending_count:
                    log.debug("watcher.pending", pending=pending_count)
        except KeyboardInterrupt:
            pass
        finally:
            self._stop.set()
            observer.stop()
            observer.join(timeout=2)

    def stop(self) -> None:
        """Signal the watcher to stop."""
        self._stop.set()

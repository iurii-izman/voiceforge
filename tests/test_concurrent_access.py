"""E12 #135: Concurrent access — daemon/CLI/web hitting same SQLite; no 'database is locked' (WAL)."""

from __future__ import annotations

import threading
from pathlib import Path

from voiceforge.core.transcript_log import TranscriptLog


def _reader(db_path: Path, results: list, index: int) -> None:
    log = TranscriptLog(db_path=db_path)
    try:
        sessions = log.get_sessions()
        results.append((index, "ok", len(sessions)))
    except Exception as e:
        results.append((index, str(e), None))
    finally:
        log.close()


def _writer(db_path: Path, results: list, index: int) -> None:
    log = TranscriptLog(db_path=db_path)
    try:
        log.log_session([{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": f"w{index}"}])
        results.append((index, "ok", None))
    except Exception as e:
        results.append((index, str(e), None))
    finally:
        log.close()


def test_concurrent_transcript_log_readers_and_writers(tmp_path: Path) -> None:
    """Multiple threads read/write same TranscriptLog DB (WAL); no database is locked errors."""
    db_path = tmp_path / "transcripts.db"
    # Bootstrap one session
    log0 = TranscriptLog(db_path=db_path)
    log0.log_session([{"start_sec": 0, "end_sec": 1, "speaker": "B", "text": "init"}])
    log0.close()

    results: list = []
    threads = []
    for i in range(3):
        t = threading.Thread(target=_reader, args=(db_path, results, i))
        threads.append(t)
    for i in range(3, 5):
        t = threading.Thread(target=_writer, args=(db_path, results, i))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for _idx, status, _extra in results:
        assert "locked" not in status.lower(), f"Unexpected locked error: {status}"
        assert status == "ok", status

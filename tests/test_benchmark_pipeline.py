"""Block 88: Benchmark for pipeline-related operations (TranscriptLog get_sessions).

Full end-to-end pipeline benchmark (audio -> analyze) requires real models and is run manually.
This test provides a reproducible benchmark for the DB layer used by the pipeline.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from voiceforge.core.transcript_log import TranscriptLog


@pytest.mark.benchmark
def test_benchmark_get_sessions(benchmark: object, tmp_path: Path) -> None:
    """Benchmark get_sessions(last_n=100) with 100 sessions in DB (block 88)."""
    db = tmp_path / "bench.db"
    log = TranscriptLog(db_path=db)
    base = datetime.now(UTC)
    for i in range(100):
        started = base - timedelta(days=i)
        ended = started + timedelta(seconds=60)
        log.log_session(
            [{"start_sec": 0, "end_sec": 60, "speaker": "S", "text": f"session {i} text"}],
            started_at=started,
            ended_at=ended,
            duration_sec=60.0,
            model="test",
        )
    log.close()

    log2 = TranscriptLog(db_path=db)
    try:
        result = benchmark(log2.get_sessions, 100)  # NOSONAR S5864: pytest-benchmark fixture is callable
        assert len(result) == 100
    finally:
        log2.close()

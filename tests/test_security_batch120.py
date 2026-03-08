from __future__ import annotations

import stat
from pathlib import Path

from pydantic import BaseModel


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_security_batch120_private_permissions_for_local_datastores(monkeypatch, tmp_path: Path) -> None:
    from voiceforge.core.metrics import log_llm_call
    from voiceforge.core.transcript_log import TranscriptLog
    from voiceforge.llm import cache as llm_cache

    class _CachedPayload(BaseModel):
        answer: str

    data_home = tmp_path / "data-home"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))

    transcript_log = TranscriptLog()
    transcript_log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "private transcript"}],
        model="test-model",
    )
    transcript_log.close()

    log_llm_call("anthropic/test", 10, 20, 0.01)
    llm_cache.set(
        "abc123",
        "anthropic/test",
        "CachedPayload",
        _CachedPayload(answer="ok"),
        0.01,
        ttl_seconds=3600,
    )

    app_dir = data_home / "voiceforge"
    assert _mode(app_dir) == 0o700
    assert _mode(app_dir / "transcripts.db") == 0o600
    assert _mode(app_dir / "metrics.db") == 0o600
    assert _mode(app_dir / "llm_response_cache.db") == 0o600


def test_security_batch120_backup_and_status_files_stay_private(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    data_home = tmp_path / "data-home"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    data_dir = data_home / "voiceforge"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "transcripts.db").write_text("t", encoding="utf-8")
    (data_dir / "metrics.db").write_text("m", encoding="utf-8")
    rag_db = tmp_path / "rag.db"
    rag_db.write_text("r", encoding="utf-8")

    status_path = data_dir / "action_item_status.json"
    monkeypatch.setattr(main, "_action_item_status_path", lambda: status_path)
    main._save_action_item_status({"1:0": "done"})
    assert status_path.exists()
    assert _mode(data_dir) == 0o700
    assert _mode(status_path) == 0o600

    backups_root = tmp_path / "backups"
    monkeypatch.setattr(main, "_get_config", lambda: type("Cfg", (), {"get_rag_db_path": lambda self: str(rag_db)})())
    monkeypatch.setattr(main.time, "strftime", lambda fmt: "20260308-130000")

    main.backup_cmd(output_dir=backups_root, keep=0)

    backup_sub = backups_root / "voiceforge-backup-20260308-130000"
    assert _mode(backups_root) == 0o700
    assert _mode(backup_sub) == 0o700
    assert _mode(backup_sub / "transcripts.db") == 0o600
    assert _mode(backup_sub / "metrics.db") == 0o600
    assert _mode(backup_sub / "rag.db") == 0o600

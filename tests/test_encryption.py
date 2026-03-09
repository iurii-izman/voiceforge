"""E17 #140: Optional SQLite encryption — TranscriptLog with encrypt_db True/False, SQLCipher optional."""

from __future__ import annotations

from pathlib import Path

import pytest

from voiceforge.core.transcript_log import TranscriptLog, _connect_transcript_db


def test_transcript_log_plain_when_encrypt_db_false(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With encrypt_db False (default), TranscriptLog uses standard sqlite3 and works."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    (tmp_path / "config" / "voiceforge").mkdir(parents=True, exist_ok=True)
    db = tmp_path / "t.db"
    log = TranscriptLog(db_path=db)
    sid = log.log_session(
        [{"start_sec": 0, "end_sec": 1, "speaker": "A", "text": "plain"}],
        model="m",
    )
    assert sid == 1
    log.close()
    assert db.exists()


def test_transcript_log_encryption_skipped_when_no_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With encrypt_db True but no db_encryption_key in keyring, use plain sqlite and log warning."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    (tmp_path / "config" / "voiceforge").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "voiceforge" / "voiceforge.yaml").write_text("encrypt_db: true\n")
    monkeypatch.setattr(
        "voiceforge.core.secrets.get_api_key",
        lambda name: None,
    )
    db = tmp_path / "enc.db"
    conn = _connect_transcript_db(db)
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    conn.commit()
    conn.close()
    assert db.exists()


def test_transcript_log_encryption_skipped_when_sqlcipher_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With encrypt_db True and key present but sqlcipher3 not installed, use plain sqlite and log warning."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    (tmp_path / "config" / "voiceforge").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "voiceforge" / "voiceforge.yaml").write_text("encrypt_db: true\n")
    monkeypatch.setattr(
        "voiceforge.core.secrets.get_api_key",
        lambda name: "secret-key" if name == "db_encryption_key" else None,
    )
    # Force _sqlcipher to None so we test fallback
    import voiceforge.core.transcript_log as mod

    monkeypatch.setattr(mod, "_sqlcipher", None)
    db = tmp_path / "enc2.db"
    conn = _connect_transcript_db(db)
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)")
    conn.commit()
    conn.close()
    assert db.exists()

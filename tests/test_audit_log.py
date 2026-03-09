"""E17 #140: API key access audit log — get_api_key writes to structlog and metrics.db api_key_access."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import voiceforge.core.metrics as metrics
from voiceforge.core.secrets import get_api_key


def test_get_api_key_logs_to_api_key_access_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """get_api_key causes one row in metrics.db api_key_access (timestamp, key_name, operation)."""
    import keyring

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    metrics._init_done_paths.clear()
    monkeypatch.setattr(
        keyring,
        "get_password",
        lambda service, name: "fake-secret" if name == "test_audit_key" else None,
    )
    result = get_api_key("test_audit_key")
    assert result == "fake-secret"
    db_path = metrics._metrics_db_path()
    assert db_path.exists()
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT timestamp, key_name, operation FROM api_key_access WHERE key_name = ?",
            ("test_audit_key",),
        ).fetchall()
        assert len(rows) >= 1
        assert rows[0][1] == "test_audit_key"
        assert rows[0][2] == "read"
    finally:
        conn.close()


def test_get_api_key_audit_survives_metrics_db_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """When log_api_key_access fails (e.g. DB read-only), get_api_key still returns key."""
    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda service, name: "key")

    def fail_insert(*args: object, **kwargs: object) -> None:
        raise OSError("db read-only")

    monkeypatch.setattr("voiceforge.core.metrics.log_api_key_access", fail_insert)
    # Should not raise; audit is best-effort
    assert get_api_key("x") == "key"

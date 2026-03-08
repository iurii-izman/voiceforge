"""Tests for pre-flight checks: PipeWire, disk, network (E3 #126)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from voiceforge.core.preflight import (
    NetworkUnavailableError,
    check_disk_space,
    check_network_for_llm,
    check_pipewire,
)


def test_check_pipewire_found(monkeypatch) -> None:
    """When pw-record is in PATH, check_pipewire returns None."""
    monkeypatch.setattr("shutil.which", lambda cmd: "/usr/bin/pw-record" if cmd == "pw-record" else None)
    assert check_pipewire() is None


def test_check_pipewire_not_found(monkeypatch) -> None:
    """When pw-record is missing, check_pipewire returns i18n key."""
    monkeypatch.setattr("shutil.which", lambda cmd: None)
    assert check_pipewire() == "error.pipewire_not_found"


def test_check_disk_space_ok(monkeypatch, tmp_path) -> None:
    """When free space > 1GB, no error or warning."""
    monkeypatch.setattr(
        "shutil.disk_usage",
        lambda p: SimpleNamespace(free=2 * 1024**3, total=10 * 1024**3, used=8 * 1024**3),
    )
    err, warn = check_disk_space(str(tmp_path))
    assert err is None
    assert warn is None


def test_check_disk_space_warning(monkeypatch, tmp_path) -> None:
    """When free space < 1GB but >= 200MB, warning only."""
    monkeypatch.setattr(
        "shutil.disk_usage",
        lambda p: SimpleNamespace(free=500 * 1024**2, total=10 * 1024**3, used=9 * 1024**3),
    )
    err, warn = check_disk_space(str(tmp_path))
    assert err is None
    assert warn == "warning.low_disk_space"


def test_check_disk_space_error(monkeypatch, tmp_path) -> None:
    """When free space < 200MB, error."""
    monkeypatch.setattr(
        "shutil.disk_usage",
        lambda p: SimpleNamespace(free=100 * 1024**2, total=10 * 1024**3, used=10 * 1024**3),
    )
    err, warn = check_disk_space(str(tmp_path))
    assert err == "error.no_disk_space"
    assert warn is None


def test_check_network_for_llm_reachable(monkeypatch) -> None:
    """When socket connects, returns None."""
    with patch("socket.create_connection") as mock_conn:
        mock_conn.return_value = SimpleNamespace(close=lambda: None)
        assert check_network_for_llm("anthropic/claude-haiku") is None
        mock_conn.assert_called_once()


def test_check_network_for_llm_unreachable(monkeypatch) -> None:
    """When socket fails, returns i18n key."""
    with patch("socket.create_connection") as mock_conn:
        mock_conn.side_effect = OSError("Connection refused")
        assert check_network_for_llm("anthropic/claude-haiku") == "error.no_network"


def test_check_network_for_llm_unknown_model_skips_check() -> None:
    """Unknown model prefix returns None (no check)."""
    assert check_network_for_llm("custom/foo") is None


def test_network_unavailable_error_has_i18n_key() -> None:
    """NetworkUnavailableError carries i18n key."""
    e = NetworkUnavailableError("error.no_network")
    assert e.i18n_key == "error.no_network"

from __future__ import annotations

import json
import sys
import types
from types import SimpleNamespace

import pytest

from voiceforge.cli import history_helpers as hh
from voiceforge.cli import status_helpers as sh
from voiceforge.cli import watch_helpers as wh
from voiceforge.core import contracts


def test_history_helpers_payloads_and_lines() -> None:
    segment = SimpleNamespace(start_sec=0.0, end_sec=1.2, speaker="S1", text="hello")
    analysis = SimpleNamespace(model="m1", questions=["q1"], answers=["a1"])
    session = SimpleNamespace(id=7, started_at="2026-02-21T12:00:00+00:00", duration_sec=12.5, segments_count=3)

    assert hh.session_not_found_message(9) == "Сессия 9 не найдена."
    assert hh.session_not_found_error(9) == ("SESSION_NOT_FOUND", "Сессия 9 не найдена.", False)

    detail_payload = hh.build_session_detail_payload(7, [segment], analysis)
    assert detail_payload["session_id"] == 7
    assert detail_payload["segments"][0]["speaker"] == "S1"
    assert detail_payload["analysis"]["model"] == "m1"

    detail_lines = hh.render_session_detail_lines(7, [segment], analysis)
    assert detail_lines[0] == "--- Сессия 7 ---"
    assert any("[S1] hello" in line for line in detail_lines)
    assert any(line == "--- Анализ ---" for line in detail_lines)

    assert hh.build_sessions_payload([session]) == {"sessions": [vars(session)]}
    assert hh.empty_sessions_payload() == {"sessions": []}
    assert hh.sessions_list_payload([]) == {"sessions": []}
    assert hh.sessions_list_payload([session])["sessions"][0]["id"] == 7
    assert hh.sessions_list_lines([]) == ["Нет сохранённых сессий. Запустите voiceforge analyze."]
    assert any("id" in line for line in hh.render_sessions_table_lines([session]))

    md = hh.build_session_markdown(7, [segment], analysis, started_at="2026-02-21T12:00:00+00:00")
    assert "# Сессия 7" in md
    assert "## Транскрипт" in md
    assert "## Анализ" in md
    assert "Шаблон" not in md
    analysis_with_tpl = SimpleNamespace(
        model="m1", template="standup", questions=[], answers=[], recommendations=[], action_items=[], cost_usd=None
    )
    md_tpl = hh.build_session_markdown(8, [segment], analysis_with_tpl)
    assert "Шаблон" in md_tpl


def test_status_helpers_text_and_data(monkeypatch) -> None:
    fake_psutil = types.ModuleType("psutil")
    fake_psutil.virtual_memory = lambda: SimpleNamespace(used=8 * 1024**3, total=16 * 1024**3, percent=50.0)
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)

    fake_metrics = types.ModuleType("voiceforge.core.metrics")
    fake_metrics.get_cost_today = lambda: 1.23456789
    monkeypatch.setitem(sys.modules, "voiceforge.core.metrics", fake_metrics)

    fake_i18n = types.ModuleType("voiceforge.i18n")
    fake_i18n.t = lambda key, **kwargs: f"{key}:{kwargs}"
    monkeypatch.setitem(sys.modules, "voiceforge.i18n", fake_i18n)

    fake_local_llm = types.ModuleType("voiceforge.llm.local_llm")
    fake_local_llm.is_available = lambda: True
    monkeypatch.setitem(sys.modules, "voiceforge.llm.local_llm", fake_local_llm)

    text = sh.get_status_text()
    assert "status.ram" in text
    assert "status.cost_today" in text
    assert "status.pii_mode" in text
    assert "status.ollama_available" in text

    data = sh.get_status_data()
    assert data["ram"] == {"used_gb": 8.0, "total_gb": 16.0, "percent": 50.0}
    assert data["cost_today_usd"] == pytest.approx(1.234568)
    assert data["pii_mode"] in ("OFF", "ON", "EMAIL_ONLY")
    assert data["ollama_available"] is True


def test_status_helpers_format_stats_and_detailed(monkeypatch) -> None:
    """_format_stats_block and get_status_detailed_* with mocked get_stats."""
    fake_psutil = types.ModuleType("psutil")
    fake_psutil.virtual_memory = lambda: SimpleNamespace(used=4 * 1024**3, total=8 * 1024**3, percent=50.0)
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    fake_metrics = types.ModuleType("voiceforge.core.metrics")
    fake_metrics.get_cost_today = lambda: 0.5
    fake_metrics.get_stats = lambda days=30: {
        "by_model": [{"model": "m1", "cost_usd": 0.3, "calls": 2}],
        "by_day": [{"date": "2026-03-01", "cost_usd": 0.1, "calls": 1}],
        "total_cost_usd": 0.3,
        "total_calls": 2,
        "response_cache_hit_rate": 0.25,
    }
    monkeypatch.setitem(sys.modules, "voiceforge.core.metrics", fake_metrics)
    fake_i18n = types.ModuleType("voiceforge.i18n")
    fake_i18n.t = lambda key, **kwargs: f"{key}:{kwargs}"
    monkeypatch.setitem(sys.modules, "voiceforge.i18n", fake_i18n)
    fake_local_llm = types.ModuleType("voiceforge.llm.local_llm")
    fake_local_llm.is_available = lambda: False
    monkeypatch.setitem(sys.modules, "voiceforge.llm.local_llm", fake_local_llm)
    fake_config = types.ModuleType("voiceforge.core.config")
    fake_config.Settings = lambda: SimpleNamespace(
        pii_mode="ON",
        get_effective_llm=lambda: ("anthropic/claude-haiku-4-5", False),
    )
    monkeypatch.setitem(sys.modules, "voiceforge.core.config", fake_config)

    detailed_text = sh.get_status_detailed_text(budget_limit_usd=10.0)
    assert "7" in detailed_text
    assert "30" in detailed_text
    detailed_data = sh.get_status_detailed_data(budget_limit_usd=10.0)
    assert detailed_data["budget_limit_usd"] == pytest.approx(10.0)
    assert "stats_7d" in detailed_data
    assert "stats_30d" in detailed_data


def test_contract_payload_builders_and_extractors() -> None:
    err_payload = contracts.build_cli_error_payload(
        code="E1",
        message="boom",
        retryable=True,
        category="network",
        details={"x": 1},
    )
    assert err_payload["schema_version"] == contracts.CLI_SCHEMA_VERSION
    assert err_payload["ok"] is False
    assert err_payload["error"]["details"] == {"x": 1}

    ok_payload = contracts.build_cli_success_payload({"a": 1})
    assert ok_payload == {"schema_version": "1.0", "ok": True, "data": {"a": 1}}

    ipc_ok = contracts.build_ipc_success_json({"a": 2})
    assert json.loads(ipc_ok)["data"] == {"a": 2}

    wrapped = contracts.wrap_ipc_json_payload("result", '{"k": "v"}')
    assert json.loads(wrapped)["data"] == {"result": {"k": "v"}}

    wrapped_raw = contracts.wrap_ipc_json_payload("result", "plain-text")
    assert json.loads(wrapped_raw)["data"] == {"result": "plain-text"}

    structured_error = contracts.build_ipc_error_json("E2", "bad request")
    assert contracts.extract_error_message(structured_error) == "bad request"
    assert contracts.extract_error_message("Ошибка: legacy fail") == "Ошибка: legacy fail"
    assert contracts.extract_error_message("not-an-error") is None
    assert contracts.extract_error_message("[1,2]") is None
    assert contracts.extract_error_message('{"error": "string"}') is None


def test_doctor_text_and_data(monkeypatch) -> None:
    """get_doctor_text and get_doctor_data run _doctor_checks; cover doctor helpers (#56)."""
    from voiceforge.cli import status_helpers as sh

    monkeypatch.setattr("voiceforge.cli.status_helpers._doctor_check_pipewire_audio", lambda t: (True, "pipewire ok", "pw"))
    monkeypatch.setattr("voiceforge.cli.status_helpers._doctor_check_keyring", lambda t: (True, "keyring ok", "k"))
    monkeypatch.setattr(
        "voiceforge.cli.status_helpers._doctor_check_rag_ring",
        lambda cfg, t: [(True, "rag ok", "r"), (True, "ring ok", "ring")],
    )
    monkeypatch.setattr("voiceforge.cli.status_helpers._doctor_check_ollama", lambda t: (True, "ollama ok", "o"))
    monkeypatch.setattr("voiceforge.cli.status_helpers._doctor_check_ram", lambda t: (True, "ram ok", "ram"))
    monkeypatch.setattr(
        "voiceforge.cli.status_helpers._doctor_check_models",
        lambda cfg, t: [
            (True, "models disk 0 MB", "disk"),
            (True, "whisper cached", "whisper"),
            (True, "onnx missing", "onnx"),
            (True, "pyannote ok", "py"),
            (True, "RAM 8 GB", "ram_rec"),
        ],
    )
    monkeypatch.setattr("voiceforge.cli.status_helpers._doctor_check_module", lambda mod, t: (True, f"{mod} ok", mod))
    monkeypatch.setattr(
        "voiceforge.core.config.Settings",
        lambda: SimpleNamespace(get_rag_db_path=lambda: "/x/rag.db", get_ring_file_path=lambda: "/x/ring.raw"),
    )

    text = sh.get_doctor_text()
    assert "✓" in text or "✗" in text
    data = sh.get_doctor_data()
    assert "checks" in data
    assert "errors" in data
    assert isinstance(data["checks"], list)
    # config + keyring + rag_ring + ollama + ram + models (5) + litellm + faster_whisper
    assert len(data["checks"]) >= 8


def test_doctor_check_keyring_fail(monkeypatch) -> None:
    """_doctor_check_keyring returns (False, ...) when no keys found."""
    import keyring

    monkeypatch.setattr(keyring, "get_password", lambda service, name: None)
    from voiceforge.cli.status_helpers import _doctor_check_keyring

    def fake_t(key: str, **kwargs: object) -> str:
        return key

    ok, _, key = _doctor_check_keyring(fake_t)
    assert ok is False
    assert "keyring" in key or "doctor" in key.lower()


def test_doctor_check_rag_ring_optional(monkeypatch) -> None:
    """_doctor_check_rag_ring reports rag_optional when db missing, ring_absent when ring missing."""
    from voiceforge.cli.status_helpers import _doctor_check_rag_ring

    def fake_t(key: str, **kwargs: object) -> str:
        return key

    class FakeCfg:
        def get_rag_db_path(self) -> str:
            return "/tmp/rag.db"

        def get_ring_file_path(self) -> str:
            return "/tmp/ring.raw"

    class FakePath:
        def __init__(self, p: str) -> None:
            self._p = p

        def exists(self) -> bool:
            return "rag" in self._p  # rag.db exists, ring.raw "exists" is False for ring path

    monkeypatch.setattr("voiceforge.cli.status_helpers.Path", FakePath)
    results = _doctor_check_rag_ring(FakeCfg(), fake_t)
    assert len(results) == 2
    keys = [r[2] for r in results]
    assert "doctor.ring_ok" in keys or "doctor.ring_absent" in keys


def test_doctor_check_pipewire_audio_fail(monkeypatch) -> None:
    """_doctor_check_pipewire_audio returns a failed check when PipeWire has no real devices."""
    from voiceforge.cli.status_helpers import _doctor_check_pipewire_audio

    monkeypatch.setattr("voiceforge.core.preflight.check_pipewire", lambda: "error.pipewire_no_audio_devices")

    def fake_t(key: str, **kwargs: object) -> str:
        return key

    ok, msg, key = _doctor_check_pipewire_audio(fake_t)
    assert ok is False
    assert msg == "error.pipewire_no_audio_devices"
    assert key == "doctor.pipewire_fail"


def test_watch_helpers_banner_and_stop_handlers() -> None:
    signal_calls: list[tuple[int, object]] = []
    stop_calls: list[str] = []

    class FakeSignalModule:
        SIGINT = 2
        SIGTERM = 15

        @staticmethod
        def signal(sig: int, handler: object) -> None:
            signal_calls.append((sig, handler))

    banner = wh.get_watch_banner("/kb", "/db/rag.db", lambda key, **kwargs: f"{key}:{kwargs}")
    assert banner == "watch.banner:{'path': '/kb', 'db_path': '/db/rag.db'}"

    wh.install_watch_stop_signal_handlers(FakeSignalModule, lambda: stop_calls.append("stop"))

    assert [sig for sig, _handler in signal_calls] == [FakeSignalModule.SIGINT, FakeSignalModule.SIGTERM]
    for _sig, handler in signal_calls:
        handler()
    assert stop_calls == ["stop", "stop"]

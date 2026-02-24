from __future__ import annotations

import json
import sys
import types
from types import SimpleNamespace

import pytest

from voiceforge.cli import history_helpers as hh
from voiceforge.cli import status_helpers as sh
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

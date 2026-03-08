"""Targeted coverage batch for issue #99.

Cheap helper-level tests for web, daemon, router, and main hotspots.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from voiceforge.core.daemon import _env_flag
from voiceforge.llm import router
from voiceforge.web import server_async


@dataclass
class _FakeSegment:
    text: str


@dataclass
class _FakeAnalysis:
    action_items: list[dict[str, str]] | None = None


class _FakeLogDb:
    def __init__(self, detail_from, detail_next) -> None:
        self._detail_from = detail_from
        self._detail_next = detail_next

    def get_session_detail(self, session_id: int):
        if session_id == 1:
            return self._detail_from
        if session_id == 2:
            return self._detail_next
        return None


def test_server_telegram_webhook_reply_known_commands(monkeypatch) -> None:
    from voiceforge.web.server import _CMD_HELP, _telegram_webhook_reply

    monkeypatch.setattr("voiceforge.web.server._reply_status", lambda: "status ok")
    monkeypatch.setattr("voiceforge.web.server._reply_sessions", lambda: "sessions ok")
    monkeypatch.setattr("voiceforge.web.server._reply_cost", lambda text: f"cost for {text}")
    monkeypatch.setattr("voiceforge.web.server._reply_latest", lambda: "latest ok")

    assert _telegram_webhook_reply("/help") == _CMD_HELP
    assert _telegram_webhook_reply("/status") == "status ok"
    assert _telegram_webhook_reply("/sessions") == "sessions ok"
    assert _telegram_webhook_reply("/cost 30") == "cost for /cost 30"
    assert _telegram_webhook_reply("/latest") == "latest ok"
    assert _telegram_webhook_reply("/unknown") == _CMD_HELP


def test_server_reply_cost_clamps_days(monkeypatch) -> None:
    from voiceforge.web.server import _reply_cost

    observed: dict[str, int] = {}

    def fake_get_stats(*, days: int):
        observed["days"] = days
        return {"total_cost_usd": 1.25, "total_calls": 7}

    monkeypatch.setattr("voiceforge.core.metrics.get_stats", fake_get_stats)

    result = _reply_cost("/cost 999")

    assert observed["days"] == 365
    assert result == "Cost last 365 days: $1.2500 (7 calls)"


def test_server_async_sync_cost_supports_range(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_get_stats_range(start, end):
        observed["start"] = start.isoformat()
        observed["end"] = end.isoformat()
        return {"total_cost_usd": 2.5, "total_calls": 3, "by_day": [{"day": "2026-03-01"}]}

    monkeypatch.setattr("voiceforge.core.metrics.get_stats_range", fake_get_stats_range)

    status, content_type, body = server_async._sync_cost("30", "2026-03-01", "2026-03-02")
    payload = json.loads(body.decode("utf-8"))

    assert status == 200
    assert content_type == server_async._CONTENT_TYPE_JSON
    assert observed == {"start": "2026-03-01", "end": "2026-03-02"}
    assert payload["total_cost_usd"] == 2.5
    assert payload["total_calls"] == 3


def test_server_async_sync_cost_rejects_reversed_range() -> None:
    status, content_type, body = server_async._sync_cost("30", "2026-03-02", "2026-03-01")
    payload = json.loads(body.decode("utf-8"))

    assert status == 400
    assert content_type == server_async._CONTENT_TYPE_JSON
    assert payload == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "from must be <= to",
        }
    }


def test_server_async_sync_telegram_webhook_subscribe(monkeypatch) -> None:
    sent: list[tuple[str, int, str]] = []
    subscribed: list[int] = []

    monkeypatch.setattr("voiceforge.core.secrets.get_api_key", lambda name: "token-123")
    monkeypatch.setattr(
        "voiceforge.web.server._telegram_send_message",
        lambda token, chat_id, text: sent.append((token, chat_id, text)),
    )
    monkeypatch.setattr(
        "voiceforge.core.telegram_notify.set_telegram_chat_id",
        lambda chat_id: subscribed.append(chat_id),
    )

    status, content_type, body = server_async._sync_telegram_webhook(
        json.dumps({"message": {"chat": {"id": 77}, "text": "/subscribe"}}).encode("utf-8")
    )

    assert status == 200
    assert content_type == server_async._CONTENT_TYPE_JSON
    assert body == b'{"ok":true}'
    assert subscribed == [77]
    assert sent == [("token-123", 77, "Push notifications enabled. You'll get a message when analyze completes.")]


def test_server_async_sync_telegram_webhook_rejects_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.core.secrets.get_api_key", lambda name: "token-123")

    status, content_type, body = server_async._sync_telegram_webhook(b"{bad json")
    payload = json.loads(body.decode("utf-8"))

    assert status == 400
    assert content_type == server_async._CONTENT_TYPE_JSON
    assert payload == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "invalid JSON",
        }
    }


def test_router_analysis_prompt_uses_pre_redacted_text_for_claude(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.llm.router.redact", lambda text, mode: "should-not-be-used")
    monkeypatch.setattr("voiceforge.llm.router._system_prompt", lambda: "system prompt")

    prompt = router._analysis_prompt(
        "raw transcript",
        "rag ctx",
        model_id=router.MODEL_CLAUDE_HAIKU,
        transcript_pre_redacted="safe transcript",
    )

    assert prompt[0]["role"] == "system"
    assert prompt[0]["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert prompt[1] == {
        "role": "user",
        "content": "Context (RAG):\nrag ctx\n\nTranscript:\nsafe transcript",
    }


def test_router_stream_part_content_handles_dict_object_and_empty() -> None:
    dict_part = SimpleNamespace(choices=[SimpleNamespace(delta={"content": "abc"})])
    obj_part = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="xyz"))])
    empty_part = SimpleNamespace(choices=[])

    assert router._stream_part_content(dict_part) == "abc"
    assert router._stream_part_content(obj_part) == "xyz"
    assert router._stream_part_content(empty_part) == ""
    assert router._stream_part_content(None) == ""


def test_router_update_action_item_statuses_short_circuits_empty_items() -> None:
    from voiceforge.llm.schemas import StatusUpdateResponse

    response, cost = router.update_action_item_statuses([], "follow-up transcript")

    assert isinstance(response, StatusUpdateResponse)
    assert response.updates == []
    assert cost == 0.0


def test_daemon_env_flag_parses_expected_values(monkeypatch) -> None:
    monkeypatch.delenv("VOICEFORGE_FEATURE_FLAG", raising=False)
    assert _env_flag("VOICEFORGE_FEATURE_FLAG", default=True) is True
    assert _env_flag("VOICEFORGE_FEATURE_FLAG", default=False) is False

    monkeypatch.setenv("VOICEFORGE_FEATURE_FLAG", "YES")
    assert _env_flag("VOICEFORGE_FEATURE_FLAG") is True

    monkeypatch.setenv("VOICEFORGE_FEATURE_FLAG", "off")
    assert _env_flag("VOICEFORGE_FEATURE_FLAG", default=True) is False


def test_main_action_item_status_helpers_and_validate(monkeypatch, tmp_path) -> None:
    from voiceforge import main

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr("pathlib.Path.home", lambda: home)
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/outside-home")

    expected_path = home / ".local" / "share" / "voiceforge" / "action_item_status.json"
    assert main._action_item_status_path() == expected_path
    assert main._load_action_item_status() == {}

    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_text("{bad json")
    assert main._load_action_item_status() == {}

    main._save_action_item_status({"1:0": "done"})
    assert json.loads(expected_path.read_text()) == {"1:0": "done"}

    log_db = _FakeLogDb(
        ([_FakeSegment("segment 1")], _FakeAnalysis(action_items=[{"description": "Ship"}])),
        ([_FakeSegment("done"), _FakeSegment("verified")], None),
    )
    detail_from, detail_next, action_items, transcript_next = main._action_items_update_validate(log_db, 1, 2)
    assert detail_from[1].action_items == [{"description": "Ship"}]
    assert detail_next[0][0].text == "done"
    assert action_items == [{"description": "Ship"}]
    assert transcript_next == "done\nverified"


def test_main_action_items_update_validate_rejects_missing_transcript(monkeypatch) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    log_db = _FakeLogDb(
        ([_FakeSegment("segment 1")], _FakeAnalysis(action_items=[{"description": "Ship"}])),
        ([_FakeSegment("   ")], None),
    )

    with pytest.raises(SystemExit) as exc:
        main._action_items_update_validate(log_db, 1, 2)

    assert exc.value.code == 1
    assert echoed
    assert echoed[-1][1] is True


def test_daemon_get_version_fallback(monkeypatch) -> None:
    from voiceforge.core.daemon import VoiceForgeDaemon

    monkeypatch.setattr("voiceforge.core.daemon.Settings", lambda: MagicMock())
    monkeypatch.setattr("voiceforge.core.daemon.ModelManager", lambda cfg: MagicMock())

    daemon = VoiceForgeDaemon(iface=None)

    import importlib.metadata

    monkeypatch.setattr(importlib.metadata, "version", lambda name: (_ for _ in ()).throw(RuntimeError("no pkg")))
    assert daemon.get_version() == "0.2.0-alpha.1"

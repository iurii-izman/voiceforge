"""Targeted coverage batch for issue #99.

Cheap helper-level tests for web, daemon, router, and main hotspots.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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


def test_server_async_sync_health_returns_200() -> None:
    status, _, body = server_async._sync_health()
    assert status == 200
    assert json.loads(body.decode("utf-8")) == {"status": "ok"}


def test_server_async_sync_ready_200_when_db_ok(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    status, content_type, body = server_async._sync_ready()
    assert status == 200
    assert content_type == server_async._CONTENT_TYPE_JSON
    assert json.loads(body.decode("utf-8"))["ready"] is True


def test_server_async_sync_ready_503_when_db_raises(monkeypatch) -> None:
    class FakeLog:
        def get_sessions(self, last_n: int = 1):
            raise RuntimeError("db unavailable")

        def close(self) -> None:
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", lambda: FakeLog())
    status, _content_type, body = server_async._sync_ready()
    assert status == 503
    assert json.loads(body.decode("utf-8"))["ready"] is False


def test_server_async_sync_export_400_id_required() -> None:
    status, _, body = server_async._sync_export("", "md")
    assert status == 400
    payload = json.loads(body.decode("utf-8"))
    assert "id" in payload["error"]["message"].lower()


def test_server_async_sync_export_400_format_invalid() -> None:
    status, _, body = server_async._sync_export("1", "docx")
    assert status == 400
    payload = json.loads(body.decode("utf-8"))
    assert "format" in payload["error"]["message"].lower()


def test_server_async_sync_export_404_session_not_found(monkeypatch) -> None:
    class FakeLog:
        def get_session_detail(self, session_id: int):
            return None

        def close(self) -> None:
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", lambda: FakeLog())
    status, _, body = server_async._sync_export("999", "md")
    assert status == 404
    payload = json.loads(body.decode("utf-8"))
    assert "999" in payload["error"]["message"] or "not found" in payload["error"]["message"].lower()


def test_server_async_sync_status_200(monkeypatch) -> None:
    monkeypatch.setattr(
        "voiceforge.cli.status_helpers.get_status_data",
        lambda: {"ok": True, "ram_mb": 100},
    )
    status, _, body = server_async._sync_status()
    assert status == 200
    assert json.loads(body.decode("utf-8"))["ok"] is True


def test_server_async_sync_status_500_on_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        "voiceforge.cli.status_helpers.get_status_data",
        lambda: (_ for _ in ()).throw(RuntimeError("status failed")),
    )
    status, _, body = server_async._sync_status()
    assert status == 500
    assert "status failed" in json.loads(body.decode("utf-8"))["error"]["message"]


def test_server_async_sync_session_by_id_400_invalid_id() -> None:
    status, _, body = server_async._sync_session_by_id("x")
    assert status == 400
    assert "invalid" in json.loads(body.decode("utf-8"))["error"]["message"].lower()


def test_server_async_sync_session_by_id_404_not_found(monkeypatch) -> None:
    class FakeLog:
        def get_session_detail(self, session_id: int):
            return None

        def close(self) -> None:
            pass

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", lambda: FakeLog())
    status, _, _body = server_async._sync_session_by_id("999")
    assert status == 404


def test_server_async_sync_action_items_update_400_missing_params() -> None:
    status, _, body = server_async._sync_action_items_update({})
    assert status == 400
    payload = json.loads(body.decode("utf-8"))
    assert "required" in payload["error"]["message"].lower()


def test_server_async_sync_action_items_update_400_not_integers() -> None:
    status, _, body = server_async._sync_action_items_update({"from_session": "x", "next_session": 2})
    assert status == 400
    payload = json.loads(body.decode("utf-8"))
    assert "integer" in payload["error"]["message"].lower()


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


def test_router_is_claude_model() -> None:
    assert router._is_claude_model(router.MODEL_CLAUDE_HAIKU) is True
    assert router._is_claude_model("anthropic/claude-sonnet-4") is True
    assert router._is_claude_model(router.MODEL_GPT4O_MINI) is False
    assert router._is_claude_model("anthropic/other") is False


def test_router_template_schema_known_and_unknown(monkeypatch) -> None:
    monkeypatch.setattr(
        "voiceforge.llm.router._template_prompts",
        lambda: {
            "standup": "prompt standup",
            "sprint_review": "prompt sr",
            "one_on_one": "1:1",
            "brainstorm": "bs",
            "interview": "iv",
        },
    )
    schema, prompt = router._template_schema("standup")
    assert schema is not None
    assert prompt == "prompt standup"
    unknown_schema, unknown_prompt = router._template_schema("unknown_template")
    assert unknown_schema is None
    assert unknown_prompt is None


def test_router_content_from_llm_response() -> None:
    raw = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="hello"))])
    content, raw_content = router._content_from_llm_response(raw, "test/model")
    assert content == "hello"
    assert raw_content == "hello"

    raw_empty = SimpleNamespace(choices=[])
    with pytest.raises(RuntimeError, match="empty choices"):
        router._content_from_llm_response(raw_empty, "test/model")


def test_router_usage_and_cost_from_response(monkeypatch) -> None:
    raw = SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            prompt_tokens_details=SimpleNamespace(cached_tokens=2),
            cache_creation_input_tokens=1,
        ),
        _hidden_params={"response_cost": 0.01},
    )
    try:
        import litellm

        monkeypatch.setattr(litellm, "completion_cost", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mock")))
    except ImportError:
        pass
    inp, out, cache_read, cache_creation, cost = router._usage_and_cost_from_response(raw, "test/model")
    assert inp == 10
    assert out == 5
    assert cache_read == 2
    assert cache_creation == 1
    assert cost == 0.01


def test_router_system_prompt_fallback(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.llm.router.load_prompt", lambda _: None)
    out = router._system_prompt()
    assert "meeting analyst" in out
    assert out == router._SYSTEM_PROMPT_FALLBACK


def test_router_template_prompts_fallback(monkeypatch) -> None:
    monkeypatch.setattr("voiceforge.llm.router.load_template_prompts", lambda: None)
    out = router._template_prompts()
    assert "standup" in out
    assert out == router._TEMPLATE_PROMPTS_FALLBACK


def test_router_live_summary_system_fallback(monkeypatch) -> None:
    """_live_summary_system returns fallback when load_prompt is None (#107)."""
    monkeypatch.setattr("voiceforge.llm.router.load_prompt", lambda _: None)
    out = router._live_summary_system()
    assert "meeting analyst" in out.lower() or "key_points" in out
    assert "action_items" in out


def test_router_status_update_system_fallback(monkeypatch) -> None:
    """_status_update_system returns fallback when load_prompt is None (#107)."""
    monkeypatch.setattr("voiceforge.llm.router.load_prompt", lambda _: None)
    out = router._status_update_system()
    assert "action item" in out.lower() or "updates" in out
    assert "follow-up" in out.lower() or "status" in out.lower()


def test_router_try_ollama_faq_returns_none_when_unavailable(monkeypatch) -> None:
    """_try_ollama_faq returns None when local_llm is_available False (#107)."""
    from voiceforge.llm.schemas import MeetingAnalysis

    fake_llm = MagicMock()
    fake_llm.is_available = lambda: False
    with patch.dict("sys.modules", {"voiceforge.llm.local_llm": fake_llm}):
        result = router._try_ollama_faq("t", "c", "model", MeetingAnalysis)
    assert result is None


def test_router_complete_structured_check_budget_raises(monkeypatch) -> None:
    """_complete_structured_check_budget raises BudgetExceeded when over limit (#107)."""
    from voiceforge.core.contracts import BudgetExceeded

    monkeypatch.setattr("voiceforge.core.metrics.get_cost_today", lambda: 15.0)
    cfg = SimpleNamespace(daily_budget_limit_usd=10.0)
    with pytest.raises(BudgetExceeded, match="exceeded"):
        router._complete_structured_check_budget(cfg)


def test_router_complete_structured_check_budget_no_raise_when_under(monkeypatch) -> None:
    """_complete_structured_check_budget does not raise when under limit (#107)."""
    monkeypatch.setattr("voiceforge.core.metrics.get_cost_today", lambda: 5.0)
    cfg = SimpleNamespace(daily_budget_limit_usd=10.0)
    router._complete_structured_check_budget(cfg)


def test_router_complete_structured_cached_miss_returns_none(monkeypatch) -> None:
    """_complete_structured_cached returns None on cache miss (#107)."""
    monkeypatch.setattr("voiceforge.llm.cache.get", lambda *a, **k: None)
    from voiceforge.llm.schemas import MeetingAnalysis

    result = router._complete_structured_cached("key", MeetingAnalysis, 60)
    assert result is None


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

"""E6 (#129): Ollama zero-config fallback — effective_llm, status, and no-backend error."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from voiceforge.core.config import Settings


def test_config_get_effective_llm_returns_default_llm_when_api_key_present(monkeypatch) -> None:
    """When any API key exists, effective_llm is default_llm (no Ollama fallback)."""
    monkeypatch.setattr(
        "voiceforge.core.secrets.get_api_key",
        lambda name: "fake-key" if name == "anthropic" else None,
    )
    cfg = Settings()
    model, is_fallback = cfg.get_effective_llm()
    assert model == cfg.default_llm
    assert is_fallback is False


def test_config_get_effective_llm_returns_ollama_when_no_keys_and_ollama_available(monkeypatch) -> None:
    """When no API keys and Ollama is running, effective_llm is ollama/<ollama_model>."""
    monkeypatch.setattr("voiceforge.core.secrets.get_api_key", lambda name: None)
    monkeypatch.setattr("voiceforge.llm.local_llm.is_available", lambda timeout=2.0: True)
    cfg = Settings()
    model, is_fallback = cfg.get_effective_llm()
    assert model is not None
    assert model.startswith("ollama/")
    assert is_fallback is True
    assert model == f"ollama/{(cfg.ollama_model or 'phi3:mini').strip() or 'phi3:mini'}"


def test_config_get_effective_llm_returns_none_when_no_keys_and_ollama_unavailable(monkeypatch) -> None:
    """When no API keys and Ollama not running, effective_llm is None."""
    monkeypatch.setattr("voiceforge.core.secrets.get_api_key", lambda name: None)
    monkeypatch.setattr("voiceforge.llm.local_llm.is_available", lambda timeout=2.0: False)
    cfg = Settings()
    model, is_fallback = cfg.get_effective_llm()
    assert model is None
    assert is_fallback is False


def test_status_data_includes_llm_backend_and_ollama_fallback_flag(monkeypatch) -> None:
    """get_status_data() includes llm_backend and llm_ollama_fallback."""
    from voiceforge.cli.status_helpers import get_status_data

    with patch("voiceforge.core.config.Settings.get_effective_llm") as m:
        m.return_value = ("ollama/phi3:mini", True)
        data = get_status_data()
    assert "llm_backend" in data
    assert data["llm_backend"] == "ollama/phi3:mini"
    assert data["llm_ollama_fallback"] is True


def test_status_text_shows_llm_line(monkeypatch) -> None:
    """get_status_text() includes LLM backend line (API or Ollama fallback)."""
    from voiceforge.cli.status_helpers import get_status_text

    with patch("voiceforge.core.config.Settings.get_effective_llm") as m:
        m.return_value = ("anthropic/claude-haiku-4-5", False)
        text = get_status_text()
    assert "LLM:" in text
    assert "anthropic" in text or "claude" in text

    with patch("voiceforge.core.config.Settings.get_effective_llm") as m:
        m.return_value = ("ollama/phi3:mini", True)
        text = get_status_text()
    assert "LLM:" in text
    assert "Ollama" in text or "fallback" in text


def test_run_analyze_pipeline_returns_no_llm_backend_error_when_effective_llm_none(monkeypatch) -> None:
    """When get_effective_llm returns (None, False), run_analyze_pipeline returns error message."""
    from voiceforge.main import run_analyze_pipeline

    class FakeResult:
        def __init__(self):
            self.segments = [SimpleNamespace(start=0.0, end=1.0, text="x")]
            self.transcript = "x"
            self.diar_segments = []
            self.context = ""
            self.transcript_redacted = "x"

    class FakePipeline:
        def __init__(self, cfg=None):
            # Empty: test fake (S1186).
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def run(self, _sec):
            return (FakeResult(), None)

    monkeypatch.setattr("voiceforge.main._get_config", lambda: Settings())
    monkeypatch.setattr("voiceforge.main.Settings.get_effective_llm", lambda self: (None, False))
    with patch("voiceforge.core.pipeline.AnalysisPipeline", FakePipeline):
        text, segments, analysis = run_analyze_pipeline(60)
    assert "No LLM backend" in text or "no_llm_backend" in text or "keyring" in text.lower()
    assert segments == []
    assert analysis == {}


def test_run_analyze_pipeline_skips_llm_on_silence(monkeypatch) -> None:
    """Silence should return a no-speech message and avoid LLM invocation/cost."""
    from voiceforge.main import run_analyze_pipeline

    class FakeResult:
        def __init__(self):
            self.segments = []
            self.transcript = "(тишина)"
            self.diar_segments = []
            self.context = ""
            self.transcript_redacted = "(тишина)"
            self.warnings = []

    class FakePipeline:
        def __init__(self, cfg=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def run(self, _sec):
            return (FakeResult(), None)

    monkeypatch.setattr("voiceforge.main._get_config", lambda: Settings())
    with patch("voiceforge.core.pipeline.AnalysisPipeline", FakePipeline):
        text, segments, analysis = run_analyze_pipeline(60)

    assert "тишина" in text.lower()
    assert "llm" in text.lower() or "анализ пропущен" in text.lower()
    assert segments == []
    assert analysis["cost_usd"] == 0.0

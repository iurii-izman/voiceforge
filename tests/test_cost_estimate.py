"""Tests for analyze --estimate and cost estimate (E9 #132)."""

from __future__ import annotations

from unittest.mock import patch

from typer.testing import CliRunner

import voiceforge.main as main_mod
from voiceforge.llm.router import estimate_analyze_cost

runner = CliRunner()


def test_estimate_analyze_cost_empty_returns_zero() -> None:
    """estimate_analyze_cost with empty transcript returns 0."""
    assert estimate_analyze_cost("", "anthropic/claude-3-5-haiku-20241022") == 0.0
    assert estimate_analyze_cost("   ", "openai/gpt-4o-mini") == 0.0


def test_estimate_analyze_cost_returns_float() -> None:
    """estimate_analyze_cost returns a non-negative float (mock litellm)."""

    def fake_cost_per_token(*, model: str, prompt_tokens: int, completion_tokens: int) -> tuple[float, float]:
        return (0.001, 0.002)

    with patch("litellm.token_counter", return_value=100), patch("litellm.cost_per_token", side_effect=fake_cost_per_token):
        cost = estimate_analyze_cost(
            "Hello world, this is a short transcript.",
            "anthropic/claude-3-5-haiku-20241022",
        )
    assert isinstance(cost, float)
    assert cost >= 0.0
    assert cost == 0.003


def test_analyze_help_shows_estimate() -> None:
    """analyze --help shows --estimate option."""
    result = runner.invoke(main_mod.app, ["analyze", "--help"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "--estimate" in result.stdout or "estimate" in result.stdout


def test_analyze_estimate_exits_zero_and_shows_cost(monkeypatch, tmp_path) -> None:
    """analyze --estimate runs dry pipeline and prints estimated cost then exits 0."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime" / "voiceforge").mkdir(parents=True, exist_ok=True)
    (tmp_path / "runtime" / "voiceforge" / "ring.raw").write_bytes(b"\x00" * 16000)

    def fake_pipeline(seconds: int, template: str | None = None, dry_run: bool = False) -> tuple[str, list, dict]:
        return (
            "Dry-run ok",
            [],
            {"transcript": "Sample meeting transcript for token count."},
        )

    class FakeCfg:
        def get_data_dir(self) -> str:
            return str(tmp_path / "data" / "voiceforge")

        def get_effective_llm(self) -> tuple[str, bool]:
            return ("anthropic/claude-3-5-haiku", False)

        ring_seconds = 30

    monkeypatch.setattr(main_mod, "run_analyze_pipeline", fake_pipeline)
    monkeypatch.setattr(main_mod, "_get_config", lambda: FakeCfg())

    with patch("voiceforge.llm.router.estimate_analyze_cost", return_value=0.0123) as mock_est:
        result = runner.invoke(main_mod.app, ["analyze", "--estimate"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "0.0123" in result.stdout or "$" in result.stdout
    mock_est.assert_called_once()

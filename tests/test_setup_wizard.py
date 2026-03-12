"""E7 (#130): Setup wizard — voiceforge setup & config init (mocked prompts)."""

from __future__ import annotations

import io
from unittest.mock import patch

from voiceforge.cli.setup import (
    _confirm_resilient,
    _ensure_config_dir,
    _prompt_resilient,
    _write_config_yaml,
    run_config_init,
    run_setup_wizard,
)
from voiceforge.core.config import default_config_yaml_content, get_default_config_yaml_path


def test_default_config_yaml_content_contains_model_size_and_language() -> None:
    """default_config_yaml_content() returns YAML with model_size, language, default_llm."""
    content = default_config_yaml_content()
    assert "model_size:" in content
    assert "language:" in content
    assert "default_llm:" in content
    assert "voiceforge" in content.lower() or "config" in content.lower()


def test_get_default_config_yaml_path_under_xdg(monkeypatch) -> None:
    """get_default_config_yaml_path() returns path under XDG_CONFIG_HOME/voiceforge."""
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/cfg")
    path = get_default_config_yaml_path()
    assert "voiceforge" in str(path)
    assert path.name == "voiceforge.yaml"
    assert "/tmp/cfg" in str(path)


def test_ensure_config_dir_creates_dir_and_returns_path(tmp_path, monkeypatch) -> None:
    """_ensure_config_dir() creates XDG_CONFIG_HOME/voiceforge and returns voiceforge.yaml path."""
    cfg = tmp_path / "config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(cfg))
    path = _ensure_config_dir()
    assert path.parent.exists()
    assert path.name == "voiceforge.yaml"
    assert path.parent.name == "voiceforge"


def test_write_config_yaml_writes_model_size_and_language(tmp_path, monkeypatch) -> None:
    """_write_config_yaml() writes YAML with given model_size and language."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    path = _ensure_config_dir()
    _write_config_yaml(path, "tiny", "ru")
    text = path.read_text()
    assert "model_size: tiny" in text
    assert "language: ru" in text


def test_run_config_init_writes_yaml(tmp_path, monkeypatch) -> None:
    """run_config_init(overwrite=True) writes voiceforge.yaml without prompting."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    out: list[str] = []

    run_config_init(overwrite=True, echo_fn=out.append)
    assert any("Config written" in line for line in out)
    path = get_default_config_yaml_path()
    assert path.is_file()
    assert "model_size:" in path.read_text()


def test_run_config_init_skips_if_exists_and_no_overwrite(tmp_path, monkeypatch) -> None:
    """run_config_init(overwrite=False) with confirm=False skips overwrite."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    path = _ensure_config_dir()
    path.write_text("original")
    out: list[str] = []

    run_config_init(
        overwrite=False,
        confirm_fn=lambda msg, **kw: False,
        echo_fn=out.append,
    )
    assert any("Skipped" in line for line in out)
    assert path.read_text() == "original"


def test_run_setup_wizard_mocked_no_download(tmp_path, monkeypatch) -> None:
    """run_setup_wizard with mocked prompts completes without downloading Whisper."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    prompts: list[str] = []
    confirms: list[tuple[str, bool]] = []

    prompt_answers = {
        "language": "auto",
        "whisper": "tiny",
        "anthropic": "",
        "huggingface": "",
    }

    def fake_prompt(msg: str, default: str = "", **kwargs: object) -> str:
        prompts.append(msg)
        lowered = msg.lower()
        if "language" in lowered:
            return prompt_answers["language"]
        if "whisper" in lowered or "model" in lowered:
            return prompt_answers["whisper"]
        if "anthropic" in lowered or "api key" in lowered:
            return prompt_answers["anthropic"]
        if "huggingface" in lowered:
            return prompt_answers["huggingface"]
        return default

    def fake_confirm(msg: str, default: bool = True) -> bool:
        confirms.append((msg, default))
        if "Continue anyway" in msg:
            return True
        if "Pre-download" in msg or "download" in msg.lower():
            return False
        if "Run 'voiceforge meeting'" in msg or "quick test" in msg.lower():
            return False
        return default

    out: list[str] = []

    with patch("voiceforge.cli.setup.check_pipewire", return_value=None):
        run_setup_wizard(
            prompt_fn=fake_prompt,
            confirm_fn=fake_confirm,
            echo_fn=out.append,
        )

    assert any("Setup complete" in line for line in out)
    assert any("Config written" in line or "voiceforge.yaml" in " ".join(out) for line in out)
    path = get_default_config_yaml_path()
    assert path.is_file()
    assert "model_size:" in path.read_text()


def test_run_setup_wizard_hides_secret_prompts(tmp_path, monkeypatch) -> None:
    """Secret prompts should request hidden input so setup does not echo keys in terminal."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    prompt_calls: list[tuple[str, dict[str, object]]] = []

    def fake_prompt(msg: str, default: str = "", **kwargs: object) -> str:
        prompt_calls.append((msg, kwargs))
        if "Language" in msg or "language" in msg.lower():
            return "auto"
        if "Whisper" in msg or "model" in msg.lower():
            return "tiny"
        return ""

    def fake_confirm(msg: str, default: bool = True) -> bool:
        return "Continue anyway" in msg

    with patch("voiceforge.cli.setup.check_pipewire", return_value=None):
        run_setup_wizard(prompt_fn=fake_prompt, confirm_fn=fake_confirm, echo_fn=lambda _msg: None)

    secret_calls = [kwargs for msg, kwargs in prompt_calls if "API key" in msg or "HuggingFace" in msg]
    assert secret_calls
    assert all(call.get("hide_input") is True for call in secret_calls)


def test_prompt_resilient_falls_back_to_raw_stdin(monkeypatch) -> None:
    """Fallback prompt path should decode raw stdin when Typer prompt crashes."""

    class FakeStdin:
        def __init__(self, raw: bytes) -> None:
            self.buffer = io.BytesIO(raw)
            self.encoding = "utf-8"

    monkeypatch.setattr("voiceforge.cli.setup.sys.stdin", FakeStdin(b"auto\n"))

    def boom(*_args: object, **_kwargs: object) -> str:
        raise UnicodeDecodeError("utf-8", b"\xd0", 0, 1, "bad input")

    monkeypatch.setattr("voiceforge.cli.setup.typer.prompt", boom)
    assert _prompt_resilient("Language for STT/UI (ru / en / auto):", default="auto") == "auto"


def test_confirm_resilient_falls_back_to_raw_stdin(monkeypatch) -> None:
    """Fallback confirm path should parse yes/no answers when Typer confirm crashes."""

    class FakeStdin:
        def __init__(self, raw: bytes) -> None:
            self.buffer = io.BytesIO(raw)
            self.encoding = "utf-8"

    monkeypatch.setattr("voiceforge.cli.setup.sys.stdin", FakeStdin(b"\xd0\xb4\xd0\xb0\n"))

    def boom(*_args: object, **_kwargs: object) -> bool:
        raise UnicodeDecodeError("utf-8", b"\xd0", 0, 1, "bad input")

    monkeypatch.setattr("voiceforge.cli.setup.typer.confirm", boom)
    assert _confirm_resilient("Continue anyway?", default=False) is True


def test_prompt_resilient_skips_hidden_tty_prompt_on_non_tty(monkeypatch) -> None:
    """Hidden-input prompts should bypass Typer/getpass when stdin/stderr are not TTYs."""

    class FakeStdin:
        def __init__(self, raw: bytes) -> None:
            self.buffer = io.BytesIO(raw)
            self.encoding = "utf-8"

        def isatty(self) -> bool:
            return False

    class FakeStderr:
        def isatty(self) -> bool:
            return False

    monkeypatch.setattr("voiceforge.cli.setup.sys.stdin", FakeStdin(b"secret\n"))
    monkeypatch.setattr("voiceforge.cli.setup.sys.stderr", FakeStderr())

    def unexpected_getpass(_prompt: str) -> str:
        raise AssertionError("getpass should not be called for non-tty fallback")

    def unexpected_prompt(*_args: object, **_kwargs: object) -> str:
        raise AssertionError("typer.prompt should not be called for non-tty hidden input")

    monkeypatch.setattr("voiceforge.cli.setup.typer.prompt", unexpected_prompt)
    monkeypatch.setattr("voiceforge.cli.setup.getpass.getpass", unexpected_getpass)
    assert _prompt_resilient("Anthropic API key (or Enter to skip):", hide_input=True) == "secret"


def test_setup_cli_help_exposes_setup_and_config_init() -> None:
    """CLI exposes 'setup' and 'config init' commands."""
    from typer.testing import CliRunner

    import voiceforge.main as main_mod

    runner = CliRunner()
    r = runner.invoke(main_mod.app, ["setup", "--help"])
    assert r.exit_code == 0
    assert "setup" in r.stdout.lower() or "wizard" in r.stdout.lower()

    r2 = runner.invoke(main_mod.app, ["config", "init", "--help"])
    assert r2.exit_code == 0
    assert "init" in r2.stdout or "voiceforge.yaml" in r2.stdout


def test_config_init_cli_overwrite(tmp_path, monkeypatch) -> None:
    """voiceforge config init --overwrite writes config without confirm."""
    from typer.testing import CliRunner

    import voiceforge.main as main_mod

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    path = get_default_config_yaml_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("old")
    runner = CliRunner()
    r = runner.invoke(main_mod.app, ["config", "init", "--overwrite"])
    assert r.exit_code == 0
    assert "Config written" in r.output or str(path) in r.output
    assert "model_size:" in path.read_text()


def test_first_run_welcome_message(monkeypatch, tmp_path) -> None:
    """When no DB and no config, main help shows first-run welcome (stderr)."""
    from typer.testing import CliRunner

    import voiceforge.main as main_mod

    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    (tmp_path / "data" / "voiceforge").mkdir(parents=True, exist_ok=True)
    # No transcripts.db, no voiceforge.yaml
    runner = CliRunner()
    r = runner.invoke(main_mod.app, [])
    assert r.exit_code == 0
    # Welcome may be in stdout or stderr depending on typer
    full = r.stdout + r.stderr
    assert "setup" in full.lower() or "VoiceForge" in full

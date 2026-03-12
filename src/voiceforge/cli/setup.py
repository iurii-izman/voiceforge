"""E7 (#130): Setup wizard — voiceforge setup & first-run guidance."""

from __future__ import annotations

import getpass
import locale
import sys
from pathlib import Path
from typing import Any

import typer

from voiceforge.core.config import (
    Settings,
    default_config_yaml_content,
    get_default_config_yaml_path,
)
from voiceforge.core.preflight import check_pipewire, get_pipewire_fix_key
from voiceforge.i18n import t

# Whisper model size -> approximate RAM (MB) for wizard description
_WHISPER_RAM_MB: dict[str, int] = {
    "tiny": 75,
    "base": 142,
    "small": 466,
    "medium": 1500,
    "large": 3000,
    "large-v2": 3000,
    "large-v3": 3000,
}


def _decode_prompt_bytes(raw: bytes) -> str:
    """Decode raw stdin bytes without crashing on locale/PTY mismatches."""
    candidates = [
        "utf-8",
        getattr(sys.stdin, "encoding", None),
        locale.getpreferredencoding(False),
        sys.getfilesystemencoding(),
    ]
    for encoding in candidates:
        if not encoding:
            continue
        try:
            return raw.decode(encoding).strip()
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", errors="ignore").strip()


def _supports_hidden_input() -> bool:
    """Return True when the current terminal can safely handle hidden prompts."""
    stdin_is_tty = bool(getattr(sys.stdin, "isatty", lambda: False)())
    stderr_is_tty = bool(getattr(sys.stderr, "isatty", lambda: False)())
    return stdin_is_tty and stderr_is_tty


def _fallback_prompt(message: str, default: str = "", show_default: bool = True, hide_input: bool = False) -> str:
    """Fallback prompt path when Click/Typer input decoding crashes in toolbox/PTY."""
    label = message.strip()
    if show_default and default not in ("", None):
        label = f"{label} [{default}]"
    label = f"{label}: "
    if hide_input and _supports_hidden_input():
        try:
            value = getpass.getpass(label)
            return (value or default or "").strip()
        except UnicodeDecodeError:
            pass
    sys.stdout.write(label)
    sys.stdout.flush()
    raw = getattr(sys.stdin, "buffer", sys.stdin).readline()
    if isinstance(raw, str):
        value = raw.strip()
    else:
        value = _decode_prompt_bytes(raw)
    return (value or default or "").strip()


def _prompt_resilient(message: str, **kwargs: Any) -> str:
    """Use Typer prompt first; fall back to raw stdin if terminal decoding breaks."""
    if kwargs.get("hide_input") and not _supports_hidden_input():
        return _fallback_prompt(
            message,
            default=str(kwargs.get("default", "") or ""),
            show_default=bool(kwargs.get("show_default", True)),
            hide_input=False,
        )
    try:
        return typer.prompt(message, **kwargs)
    except UnicodeDecodeError:
        return _fallback_prompt(
            message,
            default=str(kwargs.get("default", "") or ""),
            show_default=bool(kwargs.get("show_default", True)),
            hide_input=bool(kwargs.get("hide_input", False)),
        )


def _confirm_resilient(message: str, **kwargs: Any) -> bool:
    """Use Typer confirm first; fall back to raw stdin if terminal decoding breaks."""
    try:
        return typer.confirm(message, **kwargs)
    except UnicodeDecodeError:
        default = bool(kwargs.get("default", False))
        answer = _fallback_prompt(message, default="y" if default else "n", show_default=True, hide_input=False).lower()
        if answer in ("y", "yes", "true", "1", "д", "да"):
            return True
        if answer in ("n", "no", "false", "0", "н", "нет"):
            return False
        return default


def _ensure_config_dir() -> Path:
    """Ensure XDG_CONFIG_HOME/voiceforge exists; return path to voiceforge.yaml."""
    path = get_default_config_yaml_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_config_yaml(path: Path, model_size: str, language: str) -> None:
    """Write voiceforge.yaml with chosen model_size and language."""
    content = default_config_yaml_content()
    # Secrets from the wizard go to keyring only; the config file stores non-secret defaults.
    # Override key fields from wizard choices
    lines = content.split("\n")
    out: list[str] = []
    for line in lines:
        if line.strip().startswith("model_size:"):
            out.append(f"model_size: {model_size}")
        elif line.strip().startswith("language:"):
            out.append(f"language: {language}")
        else:
            out.append(line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _set_keyring_password(service: str, key_name: str, value: str) -> None:
    """Store value in keyring (service, key_name)."""
    try:
        import keyring

        keyring.set_password(service, key_name, value)
    except Exception as e:
        typer.echo(t("setup.keyring_fail", key_name=key_name, error=str(e)), err=True)


def run_setup_wizard(
    prompt_fn: Any = None,
    confirm_fn: Any = None,
    echo_fn: Any = None,
) -> None:
    """Run interactive setup wizard. Uses typer.prompt/confirm/echo by default.

    prompt_fn(msg, default=...), confirm_fn(msg, default=...), echo_fn(msg) can be
    overridden for tests (mocked prompts).
    """
    prompt = prompt_fn or _prompt_resilient
    confirm = confirm_fn or _confirm_resilient
    echo = echo_fn or typer.echo

    echo("=== VoiceForge Setup ===\n")

    # 1. PipeWire
    pw_err = check_pipewire()
    if pw_err:
        echo(t(pw_err), err=True)
        echo(t(get_pipewire_fix_key(pw_err)), err=True)
        if not confirm("Continue anyway?", default=False):
            raise SystemExit(1)
    else:
        echo("1. PipeWire: OK (pw-record found)")

    # 2. Python/uv — informational
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    echo(f"2. Python: {py_ver}")

    # 3. Language
    lang_choice = (
        prompt(
            "Language for STT/UI (ru / en / auto):",
            default="auto",
        )
        .strip()
        .lower()
        or "auto"
    )
    if lang_choice not in ("ru", "en", "auto"):
        lang_choice = "auto"
    echo(f"   Using: {lang_choice}")

    # 4. Whisper model
    echo("\nWhisper model sizes: tiny (~75MB), small (~466MB), medium (~1.5GB RAM)")
    model_choice = (
        prompt(
            "Whisper model (tiny / small / medium):",
            default="small",
        )
        .strip()
        .lower()
        or "small"
    )
    if model_choice not in _WHISPER_RAM_MB:
        model_choice = "small"
    ram_mb = _WHISPER_RAM_MB.get(model_choice, 500)
    echo(f"   Using: {model_choice} (~{ram_mb} MB)")

    # 5. Anthropic API key
    echo("\n5. API keys (optional; press Enter to skip)")
    anthropic_key = prompt(
        "Anthropic API key (or Enter to skip):",
        default="",
        show_default=False,
        hide_input=True,
    )
    if anthropic_key and anthropic_key.strip():
        _set_keyring_password("voiceforge", "anthropic", anthropic_key.strip())
        echo("   Saved to keyring (voiceforge/anthropic)")
    else:
        echo("   Skipped (you can use Ollama or set later: keyring set voiceforge anthropic)")

    # 6. HuggingFace token (diarization)
    hf_token = prompt(
        "HuggingFace token for diarization (or Enter to skip):",
        default="",
        show_default=False,
        hide_input=True,
    )
    if hf_token and hf_token.strip():
        _set_keyring_password("voiceforge", "huggingface", hf_token.strip())
        echo("   Saved to keyring (voiceforge/huggingface)")
    else:
        echo("   Skipped (diarization will be disabled; set later: keyring set voiceforge huggingface)")

    # 7. Pre-download Whisper model (optional)
    if confirm("Pre-download Whisper model now? (recommended)", default=True):
        echo("   Downloading...")
        try:
            from voiceforge.stt.transcriber import Transcriber

            Transcriber(model_size=model_choice, device="cpu", compute_type="int8")
            echo("   Model ready.")
        except Exception as e:
            echo(f"   Download failed: {e}. You can retry later when running listen.", err=True)
    else:
        echo("   Skipped (model will download on first listen)")

    # 8. Generate voiceforge.yaml
    config_path = _ensure_config_dir()
    _write_config_yaml(config_path, model_choice, lang_choice)
    echo(f"\n8. Config written: {config_path}")

    # 9. Run status --doctor
    echo("\n9. Running diagnostics (voiceforge status --doctor)...")
    try:
        cfg = Settings()
        from voiceforge.cli.status_helpers import get_doctor_text

        doctor_text = get_doctor_text()
        echo(doctor_text)
    except Exception as e:
        echo(f"   Diagnostics error: {e}", err=True)

    # 10. Suggest first test
    echo("\n10. Next step: run a test meeting")
    if confirm("Run 'voiceforge meeting' now for a quick test?", default=False):
        from voiceforge.cli.meeting import run_meeting

        cfg = Settings()
        run_meeting(cfg)
    else:
        echo("   Run when ready: voiceforge meeting")
    echo("\nSetup complete.")


def run_config_init(
    overwrite: bool = False,
    confirm_fn: Any = None,
    echo_fn: Any = None,
) -> None:
    """Generate voiceforge.yaml with current defaults and comments (quick alternative to full setup)."""
    echo = echo_fn or typer.echo
    path = _ensure_config_dir()
    if path.is_file() and not overwrite:
        confirm = confirm_fn or (lambda msg, **kw: typer.confirm(msg, **kw))
        if not confirm(f"Overwrite {path}?"):
            echo("Skipped.")
            return
    content = default_config_yaml_content()
    path.write_text(content, encoding="utf-8")
    echo(f"Config written: {path}")

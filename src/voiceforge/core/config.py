"""Pydantic Settings: env → voiceforge.yaml → defaults."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import structlog
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

log = structlog.get_logger()


def _config_base_dir() -> str:
    return os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")


def _config_yaml_paths(base: str) -> list[Path]:
    return [
        Path(base) / "voiceforge" / "voiceforge.yaml",
        Path.cwd() / "voiceforge.yaml",
    ]


def _load_yaml_config(path: Path) -> dict[str, Any] | None:
    try:
        import yaml

        with path.open() as f:
            parsed = yaml.safe_load(f) or {}
    except Exception as e:
        log.warning("config.yaml_parse_failed", path=str(path), error=str(e))
        return None

    if not isinstance(parsed, dict):
        log.warning("config.yaml_invalid_type", path=str(path), got_type=type(parsed).__name__)
        return None
    if not parsed:
        # Empty file should not shadow next source (e.g. cwd/voiceforge.yaml in tests/dev).
        log.info("config.yaml_empty_skip", path=str(path))
        return None
    return parsed


def _yaml_source(_settings_cls: type[BaseSettings]) -> dict[str, Any]:
    """Load from voiceforge.yaml if present (XDG_CONFIG_HOME or cwd)."""
    base = _config_base_dir()
    data: dict[str, Any] = {}
    for path in _config_yaml_paths(base):
        if not path.is_file():
            continue
        parsed = _load_yaml_config(path)
        if parsed is None:
            continue
        data = parsed
        break
    return data


class Settings(BaseSettings):
    """VoiceForge config: model_size, sample_rate, default_llm, budget_limit."""

    model_config = SettingsConfigDict(
        env_prefix="VOICEFORGE_",
        env_file=None,
        extra="ignore",
    )

    model_size: str = Field(default="small", description="faster-whisper model size")
    sample_rate: int = Field(default=16000, description="Audio sample rate Hz")
    default_llm: str = Field(
        default="anthropic/claude-haiku-4-5",
        description="Default LLM model id for analyze (Haiku 4.5)",
    )
    budget_limit_usd: float = Field(default=75.0, description="Monthly API budget USD")
    ring_seconds: float = Field(default=300.0, description="Ring buffer length seconds")
    ring_file_path: str | None = Field(
        default=None,
        description="Ring file path; default XDG_RUNTIME_DIR/voiceforge/ring.raw",
    )
    rag_db_path: str | None = Field(default=None, description="RAG SQLite path")
    smart_trigger: bool = Field(
        default=False,
        description="Block 4.4: auto-analyze on semantic pause (silence > 3s after >= 30s speech)",
    )
    monitor_source: str | None = Field(
        default=None,
        description="Block 6.3: PipeWire source name for app capture (e.g. VoiceForge_Monitor.monitor).",
    )
    aggressive_memory: bool = Field(
        default=False,
        description="Block 7.1: if True, unload models after each analyze (del + gc + torch.cuda.empty_cache).",
    )
    pyannote_restart_hours: int = Field(
        default=2,
        description="Block 7.1: restart pyannote Pipeline every N hours to mitigate memory leak.",
    )
    pipeline_step2_timeout_sec: float = Field(
        default=25.0,
        description="Timeout for parallel step2 (diarization/rag/pii). On timeout pipeline degrades gracefully.",
    )
    streaming_stt: bool = Field(
        default=False,
        description="Block 10.1: during listen, show partial/final transcript in real time (chunk-based STT).",
    )
    language: str = Field(
        default="auto",
        description="Block 11.4: CLI/UI locale: auto (from LANG/LC_ALL) | ru | en.",
    )
    ollama_model: str = Field(
        default="phi3:mini",
        description="Block 4: Ollama model for local classify/simple_answer (e.g. phi3:mini, llama3.2).",
    )
    pii_mode: Literal["OFF", "ON", "EMAIL_ONLY"] = Field(
        default="ON",
        description="PII redaction before LLM: OFF=no redaction, ON=full (regex+GLiNER), EMAIL_ONLY=email regex only.",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        # Env vars have higher priority than YAML (12-factor app convention)
        return (
            init_settings,
            env_settings,
            lambda: _yaml_source(settings_cls),
            file_secret_settings,
        )

    def get_data_dir(self) -> str:
        """XDG_DATA_HOME/voiceforge — base for cost log, RAG db, etc."""
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        return os.path.join(base, "voiceforge")

    def get_ring_file_path(self) -> str:
        """Resolved path to ring PCM file."""
        if self.ring_file_path:
            return self.ring_file_path
        base = os.environ.get("XDG_RUNTIME_DIR") or os.path.expanduser("~/.cache")
        return os.path.join(base, "voiceforge", "ring.raw")

    def get_rag_db_path(self) -> str:
        """Resolved path to RAG SQLite database."""
        if self.rag_db_path:
            return self.rag_db_path
        return os.path.join(self.get_data_dir(), "rag.db")

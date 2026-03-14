"""Pydantic Settings: env → voiceforge.yaml → defaults."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal, Self

import structlog
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from voiceforge.core.fs import voiceforge_data_dir

log = structlog.get_logger()

_CONFIG_DIR_NAME = "voiceforge"
_CONFIG_FILENAME = "voiceforge.yaml"
_RING_FILENAME = "ring.raw"
_DEFAULT_OLLAMA_MODEL = "phi3:mini"


def _config_base_dir() -> str:
    return os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")


def get_default_config_yaml_path() -> Path:
    """Path to voiceforge.yaml in XDG_CONFIG_HOME/voiceforge (E7 setup wizard)."""
    base = _config_base_dir()
    return Path(base) / "voiceforge" / "voiceforge.yaml"


def _config_yaml_paths(base: str) -> list[Path]:
    return [
        Path(base) / _CONFIG_DIR_NAME / _CONFIG_FILENAME,
        Path.cwd() / _CONFIG_FILENAME,
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
    stt_backend: Literal["local", "openai"] = Field(
        default="local",
        description="STT backend: local (faster-whisper) | openai (Whisper API). Key 'openai' in keyring for API (#93).",
    )
    sample_rate: int = Field(default=16000, description="Audio sample rate Hz")
    default_llm: str = Field(
        default="anthropic/claude-haiku-4-5",
        description="Default LLM model id for analyze (Haiku 4.5)",
    )
    budget_limit_usd: float = Field(default=75.0, description="Monthly API budget USD")
    daily_budget_limit_usd: float | None = Field(
        default=None,
        description="Daily LLM budget USD; default budget_limit_usd/30 (#38).",
    )
    cost_anomaly_multiplier: float = Field(
        default=2.0,
        description="E15 #138: cost anomaly threshold; 1 if today > multiplier × 7-day avg.",
    )
    ring_seconds: float = Field(default=300.0, description="Ring buffer length seconds")
    ring_persist_interval_sec: float = Field(
        default=10.0,
        description="Interval (seconds) between full ring file writes in listen loop; reduces I/O (#100).",
    )
    copilot_pre_roll_seconds: float = Field(
        default=1.0,
        ge=0.0,
        le=5.0,
        description="KC3: seconds of audio before capture start marker to include in segment (pre-roll).",
    )
    copilot_max_capture_seconds: float = Field(
        default=30.0,
        ge=5.0,
        le=120.0,
        description="KC3: max capture segment length; auto-release and warning at 25s.",
    )
    copilot_stt_model_size: str = Field(
        default="tiny",
        description="KC4: STT model size for copilot path (short captures, low latency). Use 'tiny' for latency budget.",
    )
    copilot_mode: Literal["cloud", "hybrid", "offline"] = Field(
        default="hybrid",
        description="KC8/KC10: Copilot mode: cloud (API only) | hybrid (API + Ollama fallback) | offline (Ollama only).",
    )
    copilot_max_visible_cards: int = Field(
        default=3,
        ge=1,
        le=7,
        description="KC8: Max cards shown in overlay at once (architecture: 3).",
    )
    copilot_stt_idle_unload_seconds: float = Field(
        default=300.0,
        ge=0,
        description="KC14: Seconds of copilot idle after which STT model is unloaded to save RAM/CPU (0=disabled).",
    )
    ring_file_path: str | None = Field(
        default=None,
        description="Ring file path; default XDG_RUNTIME_DIR/voiceforge/ring.raw",
    )
    rag_db_path: str | None = Field(default=None, description="RAG SQLite path")
    rag_auto_index_path: str | None = Field(
        default=None,
        description="E13 #136: path to auto-index on first analyze (e.g. ~/Documents). Default null = disabled.",
    )
    rag_exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Block 74: glob patterns to exclude paths from RAG indexing (e.g. *.tmp, */.git/*).",
    )
    smart_trigger: bool = Field(
        default=True,
        description="Block 4.4: auto-analyze on semantic pause (silence > 3s after >= 30s speech)",
    )
    smart_trigger_template: str | None = Field(
        default=None,
        description="Optional template for smart-trigger analyze (e.g. standup, one_on_one). None = free-form.",
    )
    monitor_source: str | None = Field(
        default=None,
        description="Block 6.3 / KC11: PipeWire source for system audio. Used only when system_audio_consent_given=True.",
    )
    system_audio_consent_given: bool = Field(
        default=False,
        description="KC11: User has confirmed system audio disclaimer. Required for monitor capture (legal-consent-kv1).",
    )
    copilot_scenario_preset: Literal["default", "demo", "negotiation", "support"] = Field(
        default="default",
        description="KC11: Scenario preset for copilot cards: default | demo | negotiation | support.",
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
    analyze_timeout_sec: float = Field(
        default=120.0,
        description="Max seconds for a single analyze() call (D-Bus/CLI). On timeout returns ANALYZE_TIMEOUT error (#39).",
    )
    streaming_stt: bool = Field(
        default=False,
        description="Block 10.1: during listen, show partial/final transcript in real time (chunk-based STT).",
    )
    live_summary_interval_sec: int = Field(
        default=90,
        description="Block 10: interval (and window) in seconds for listen --live-summary (e.g. every 90s for last 90s).",
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
    retention_days: int = Field(
        default=90,
        description="Data retention: sessions with started_at before (today - retention_days) are purged at daemon start. 0 = disable auto-cleanup (#43).",
    )
    response_cache_ttl_seconds: int = Field(
        default=86400,
        description="LLM response cache TTL in seconds (content-hash key). 0 = disable (#44).",
    )
    calendar_context_enabled: bool = Field(
        default=False,
        description="D3 (#48): inject next CalDAV event into analyze context (keyring: caldav_*).",
    )
    calendar_autostart_enabled: bool = Field(
        default=False,
        description="Block 78: auto-start listen N minutes before next calendar event (requires calendar_autostart_minutes).",
    )
    calendar_autostart_minutes: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Block 78: start listen this many minutes before event start when calendar_autostart_enabled.",
    )
    calendar_auto_listen: bool = Field(
        default=False,
        description="E11 #134: poll CalDAV every 5 min; auto-start listen when meeting in ≤2 min; auto-analyze when meeting ended ≥1 min ago.",
    )
    encrypt_db: bool = Field(
        default=False,
        description="E17 #140: Use SQLCipher for transcripts.db at rest; key from keyring 'db_encryption_key'. Requires optional dependency sqlcipher3.",
    )

    @field_validator("model_size")
    @classmethod
    def _model_size_allowed(cls, v: str) -> str:
        allowed = ("tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo", "large", "auto")
        if v.lower() not in allowed:
            raise ValueError(f"model_size must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("copilot_stt_model_size")
    @classmethod
    def _copilot_stt_model_size_allowed(cls, v: str) -> str:
        allowed = ("tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo", "large", "auto")
        if v.lower() not in allowed:
            raise ValueError(f"copilot_stt_model_size must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator("default_llm")
    @classmethod
    def _default_llm_nonempty(cls, v: str) -> str:
        if not (v and v.strip()):
            raise ValueError("default_llm must be non-empty")
        return v.strip()

    @field_validator("budget_limit_usd")
    @classmethod
    def _budget_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("budget_limit_usd must be >= 0")
        return v

    @field_validator("daily_budget_limit_usd")
    @classmethod
    def _daily_budget_non_negative(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("daily_budget_limit_usd must be >= 0")
        return v

    @field_validator("cost_anomaly_multiplier")
    @classmethod
    def _cost_anomaly_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("cost_anomaly_multiplier must be > 0")
        return v

    @model_validator(mode="after")
    def _set_daily_budget_default(self) -> Self:
        if self.daily_budget_limit_usd is None:
            object.__setattr__(self, "daily_budget_limit_usd", self.budget_limit_usd / 30.0)
        return self

    @field_validator("pipeline_step2_timeout_sec")
    @classmethod
    def _timeout_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("pipeline_step2_timeout_sec must be positive")
        return v

    @field_validator("analyze_timeout_sec")
    @classmethod
    def _analyze_timeout_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("analyze_timeout_sec must be positive")
        return v

    @field_validator("sample_rate")
    @classmethod
    def _sample_rate_positive(cls, v: int) -> int:
        if v <= 0 or v > 192000:
            raise ValueError("sample_rate must be in 1..192000")
        return v

    @field_validator("ollama_model")
    @classmethod
    def _ollama_model_nonempty(cls, v: str) -> str:
        if not (v and v.strip()):
            raise ValueError("ollama_model must be non-empty")
        return v.strip()

    @field_validator("ring_seconds")
    @classmethod
    def _ring_seconds_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("ring_seconds must be positive")
        return v

    @field_validator("ring_persist_interval_sec")
    @classmethod
    def _ring_persist_interval_positive(cls, v: float) -> float:
        if v < 1.0:
            raise ValueError("ring_persist_interval_sec must be >= 1")
        return v

    @field_validator("pyannote_restart_hours")
    @classmethod
    def _pyannote_restart_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("pyannote_restart_hours must be >= 1")
        return v

    @field_validator("live_summary_interval_sec")
    @classmethod
    def _live_summary_interval_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("live_summary_interval_sec must be >= 1")
        return v

    @field_validator("retention_days")
    @classmethod
    def _retention_days_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("retention_days must be >= 0")
        return v

    @field_validator("response_cache_ttl_seconds")
    @classmethod
    def _response_cache_ttl_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("response_cache_ttl_seconds must be >= 0")
        return v

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
        """XDG_DATA_HOME/voiceforge — base for cost log, RAG db, etc. Uses fs.voiceforge_data_dir (QA3)."""
        return str(voiceforge_data_dir())

    def get_ring_file_path(self) -> str:
        """Resolved path to ring PCM file."""
        if self.ring_file_path:
            return self.ring_file_path
        base = os.environ.get("XDG_RUNTIME_DIR") or os.path.expanduser("~/.cache")
        return os.path.join(base, _CONFIG_DIR_NAME, _RING_FILENAME)

    def get_rag_db_path(self) -> str:
        """Resolved path to RAG SQLite database."""
        if self.rag_db_path:
            return self.rag_db_path
        return os.path.join(self.get_data_dir(), "rag.db")

    def get_effective_llm(self) -> tuple[str | None, bool]:
        """E6 (#129), KC10: Effective LLM model and whether using Ollama fallback.

        Respects copilot_mode: offline → Ollama only; cloud → API only; hybrid → API with Ollama fallback.
        Returns (model_id, is_ollama_fallback). model_id is for LiteLLM (anthropic/... or ollama/...).
        """
        from voiceforge.core.secrets import get_api_key

        mode = getattr(self, "copilot_mode", "hybrid") or "hybrid"
        has_api_key = any(get_api_key(name) for name in ("anthropic", "openai", "google"))

        if mode == "offline":
            try:
                from voiceforge.llm.local_llm import is_available
            except ImportError:
                return (None, False)
            if not is_available():
                return (None, False)
            model = (self.ollama_model or _DEFAULT_OLLAMA_MODEL).strip() or _DEFAULT_OLLAMA_MODEL
            return (f"ollama/{model}", True)

        if mode == "cloud":
            if has_api_key:
                return (self.default_llm, False)
            return (None, False)

        # hybrid: API primary, Ollama fallback when no keys
        if has_api_key:
            return (self.default_llm, False)
        try:
            from voiceforge.llm.local_llm import is_available
        except ImportError:
            return (None, False)
        if not is_available():
            return (None, False)
        model = (self.ollama_model or _DEFAULT_OLLAMA_MODEL).strip() or _DEFAULT_OLLAMA_MODEL
        return (f"ollama/{model}", True)


def get_effective_config_and_overrides() -> tuple[dict[str, Any], set[str]]:
    """E14 (#137): Effective config dict and set of keys overridden from defaults (yaml/env).
    Returns (config_dict, overridden_keys). config_dict is flat key -> value for display."""
    effective = Settings()
    # Build default instance (no env/yaml) via model_construct + post-init for derived fields
    default_instance = Settings.model_construct()
    if default_instance.daily_budget_limit_usd is None and default_instance.budget_limit_usd:
        object.__setattr__(default_instance, "daily_budget_limit_usd", default_instance.budget_limit_usd / 30.0)
    raw = effective.model_dump()
    overridden: set[str] = set()
    for key in raw:
        eff_val = raw.get(key)
        def_val = getattr(default_instance, key, None)
        if eff_val != def_val:
            overridden.add(key)
    return raw, overridden


def default_config_yaml_content() -> str:
    """E7 (#130): Default voiceforge.yaml content with comments for config init / setup wizard."""
    return """# VoiceForge config (voiceforge.yaml)
# See docs/runbooks/config-env-contract.md for full options.

# STT: faster-whisper (tiny, base, small, medium, large-v2, large-v3, large-v3-turbo, large; auto=by RAM)
model_size: small
# Language for STT: auto | ru | en
language: auto
# Default LLM for analyze (anthropic/..., openai/..., ollama/phi3:mini)
default_llm: anthropic/claude-haiku-4-5
# Monthly API budget USD
budget_limit_usd: 75.0
# Sample rate Hz
sample_rate: 16000
"""

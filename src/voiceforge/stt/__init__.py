"""VoiceForge stt module."""

from typing import Any


def get_transcriber_for_config(cfg: Any, model_size_override: str | None = None) -> Any:
    """Return Transcriber or OpenAIWhisperTranscriber by cfg.stt_backend (#93).
    KC4: model_size_override forces STT size (e.g. 'tiny' for copilot path)."""
    if getattr(cfg, "stt_backend", "local") == "openai":
        from voiceforge.stt.openai_whisper import OpenAIWhisperTranscriber

        return OpenAIWhisperTranscriber()
    from voiceforge.stt.transcriber import Transcriber

    size = model_size_override if model_size_override is not None else getattr(cfg, "model_size", "small")
    return Transcriber(model_size=size)

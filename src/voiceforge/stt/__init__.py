"""VoiceForge stt module."""

from typing import Any


def get_transcriber_for_config(cfg: Any) -> Any:
    """Return Transcriber or OpenAIWhisperTranscriber by cfg.stt_backend (#93)."""
    if getattr(cfg, "stt_backend", "local") == "openai":
        from voiceforge.stt.openai_whisper import OpenAIWhisperTranscriber

        return OpenAIWhisperTranscriber()
    from voiceforge.stt.transcriber import Transcriber

    return Transcriber(model_size=getattr(cfg, "model_size", "small"))

"""STT via OpenAI Whisper API (optional backend). Key 'openai' in keyring (#93)."""

from __future__ import annotations

import io
import uuid
import wave
from typing import Any

import numpy as np
import structlog

from voiceforge.stt.transcriber import Segment

log = structlog.get_logger()

OPENAI_TRANSCRIPTIONS_URL = "https://api.openai.com/v1/audio/transcriptions"
WHISPER_MODEL = "whisper-1"


def _audio_to_wav_bytes(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
    """Convert float32 or int16 mono audio to WAV bytes."""
    if audio.dtype == np.float32:
        audio_int16 = (audio * 32767).astype(np.int16)
    else:
        audio_int16 = audio.astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio_int16.tobytes())
    return buf.getvalue()


def _parse_verbose_json(data: dict[str, Any], language_hint: str | None) -> list[Segment]:
    """Map OpenAI verbose_json response to list of Segment."""
    segments_raw = data.get("segments") or []
    lang = data.get("language") or language_hint
    out: list[Segment] = []
    for s in segments_raw:
        start = float(s.get("start", 0))
        end = float(s.get("end", start))
        text = (s.get("text") or "").strip()
        out.append(
            Segment(
                start=start,
                end=end,
                text=text,
                language=lang,
                confidence=1.0,
            )
        )
    return out


class OpenAIWhisperTranscriber:
    """Facade: transcribe audio via OpenAI Whisper API. Same interface as Transcriber for pipeline."""

    def __init__(self) -> None:
        self._model_size = "openai"  # for compatibility with getattr(..., "_model_size")

    def transcribe(
        self,
        audio: np.ndarray,
        language: str | None = None,
        sample_rate: int = 16000,
        *,
        beam_size: int = 1,
        vad_filter: bool = True,
        vad_parameters: dict | None = None,
    ) -> list[Segment]:
        """Send audio to OpenAI Whisper API; return list of Segment. Ignores beam_size/vad_*."""
        from voiceforge.core.secrets import get_api_key

        api_key = get_api_key("openai")
        if not (api_key and api_key.strip()):
            raise ValueError("OpenAI API key not found in keyring (service=voiceforge, key=openai)")

        wav_bytes = _audio_to_wav_bytes(audio, sample_rate)
        boundary = uuid.uuid4().hex
        body_start = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
            "Content-Type: audio/wav\r\n\r\n"
        ).encode()
        body_end = (
            f"\r\n--{boundary}\r\n"
            'Content-Disposition: form-data; name="model"\r\n\r\n'
            f"{WHISPER_MODEL}\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="response_format"\r\n\r\n'
            "verbose_json\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        body = body_start + wav_bytes + body_end

        import urllib.request

        req = urllib.request.Request(
            OPENAI_TRANSCRIPTIONS_URL,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key.strip()}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                import json

                data = json.loads(resp.read().decode())
        except Exception as e:
            log.warning("openai_whisper.transcribe_failed", error=str(e))
            raise

        if "segments" not in data and "text" in data:
            # plain format fallback: one segment
            return [
                Segment(
                    start=0.0,
                    end=0.0,
                    text=(data["text"] or "").strip(),
                    language=language or data.get("language"),
                    confidence=1.0,
                )
            ]
        return _parse_verbose_json(data, language)

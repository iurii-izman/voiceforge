"""VoiceForge — мультимодельный AI-помощник для аудиопереговоров."""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("voiceforge")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0+dev"

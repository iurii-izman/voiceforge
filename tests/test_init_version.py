"""Test package __init__ version fallback when metadata is unavailable. #56"""

from __future__ import annotations

import importlib

import pytest


def test_version_fallback_when_package_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """When importlib.metadata.version raises PackageNotFoundError, __version__ is 0.0.0+dev."""
    import voiceforge

    def raise_not_found(name: str) -> None:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", raise_not_found)
    importlib.reload(voiceforge)
    try:
        assert voiceforge.__version__ == "0.0.0+dev"
    finally:
        importlib.reload(voiceforge)

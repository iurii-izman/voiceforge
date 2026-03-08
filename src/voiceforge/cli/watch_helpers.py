"""Helpers for the `voiceforge watch` CLI command."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def get_watch_banner(path: str, db_path: str, translate: Callable[..., str]) -> str:
    """Build localized banner for the watch command."""
    return translate("watch.banner", path=path, db_path=db_path)


def install_watch_stop_signal_handlers(signal_module: Any, stop_callback: Callable[[], None]) -> None:
    """Install SIGINT/SIGTERM handlers that stop the active watcher."""

    def _handle_signal(*_args: object) -> None:
        stop_callback()

    signal_module.signal(signal_module.SIGINT, _handle_signal)
    signal_module.signal(signal_module.SIGTERM, _handle_signal)

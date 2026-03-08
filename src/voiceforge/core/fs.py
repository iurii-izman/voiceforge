"""Filesystem helpers for local private data paths."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import structlog

log = structlog.get_logger()

PRIVATE_DIR_MODE = 0o700
PRIVATE_FILE_MODE = 0o600


def _set_mode_best_effort(path: Path, mode: int) -> None:
    """Best-effort chmod for private local data paths on POSIX filesystems."""
    try:
        if not path.exists() or path.is_symlink():
            return
        current = stat.S_IMODE(path.stat().st_mode)
        if current != mode:
            os.chmod(path, mode)
    except OSError as exc:
        log.warning("fs.private_mode_failed", path=str(path), mode=oct(mode), error=str(exc))


def ensure_private_dir(path: Path) -> Path:
    """Ensure directory exists and is user-private (0700)."""
    path.mkdir(parents=True, exist_ok=True)
    _set_mode_best_effort(path, PRIVATE_DIR_MODE)
    return path


def ensure_private_file(path: Path) -> Path:
    """Ensure parent exists and file, when present, is user-private (0600)."""
    ensure_private_dir(path.parent)
    if path.exists():
        _set_mode_best_effort(path, PRIVATE_FILE_MODE)
    return path

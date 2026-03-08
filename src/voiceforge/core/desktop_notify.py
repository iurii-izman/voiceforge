"""Desktop notification via notify-send (E1: analysis complete)."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404 -- notify-send from PATH, message from our pipeline


def notify_analyze_done(summary: str) -> None:
    """Show 'Analysis complete' via notify-send. No-op if notify-send not found."""
    if not summary:
        return
    if not shutil.which("notify-send"):
        return
    msg = (summary[:80] + "…") if len(summary) > 80 else summary
    subprocess.run(  # nosec B603 B607 -- notify-send from PATH, args from our text
        ["notify-send", "VoiceForge", f"Analysis complete: {msg}"],
        check=False,
        timeout=5,
    )

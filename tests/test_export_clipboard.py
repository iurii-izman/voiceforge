"""E10 (#133): Export --clipboard (wl-copy / xclip)."""

from __future__ import annotations

from unittest.mock import patch

from voiceforge.main import _copy_to_clipboard


def test_copy_to_clipboard_no_tool_returns_false() -> None:
    """When neither wl-copy nor xclip is available, _copy_to_clipboard returns False."""
    with patch("voiceforge.main.subprocess.run") as m:
        m.side_effect = FileNotFoundError()
        assert _copy_to_clipboard("test") is False


def test_copy_to_clipboard_wayland_success() -> None:
    """With WAYLAND_DISPLAY set, wl-copy is used and True returned on success."""
    with (
        patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-1"}, clear=False),
        patch("voiceforge.main.subprocess.run") as m,
    ):
        m.return_value = type("R", (), {"returncode": 0})()
        assert _copy_to_clipboard("hello") is True
        m.assert_called_once()
        assert m.call_args[0][0] == ["wl-copy"]


def test_copy_to_clipboard_x11_success() -> None:
    """Without Wayland, xclip is used and True returned on success."""
    with patch.dict("os.environ", {}, clear=True), patch("voiceforge.main.subprocess.run") as m:
        m.return_value = type("R", (), {"returncode": 0})()
        assert _copy_to_clipboard("hello") is True
        m.assert_called_once()
        assert m.call_args[0][0][0] == "xclip"

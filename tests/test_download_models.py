"""E8 (#131): Tests for voiceforge download-models (mocked download)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from voiceforge.cli.download_models import (
    WHISPER_SIZE_MB,
    _download_whisper_with_retry,
    _ensure_onnx_embedder,
    run_download_models,
)


def test_whisper_size_mb_has_common_models() -> None:
    """WHISPER_SIZE_MB contains tiny, small, medium."""
    assert WHISPER_SIZE_MB["tiny"] == 75
    assert WHISPER_SIZE_MB["small"] == 466
    assert WHISPER_SIZE_MB["medium"] == 1500


def test_download_whisper_with_retry_mocked() -> None:
    """_download_whisper_with_retry loads model (mocked); no real download."""
    with (
        patch("voiceforge.cli.download_models._is_whisper_model_cached", return_value=False),
        patch("voiceforge.cli.download_models.WhisperModel") as mock_wm,
    ):
        mock_instance = MagicMock()
        mock_wm.return_value = mock_instance
        downloaded = _download_whisper_with_retry("tiny", device="cpu", compute_type="int8")
        mock_wm.assert_called_once_with("tiny", device="cpu", compute_type="int8")
        assert downloaded is True


def test_download_whisper_retries_on_failure() -> None:
    """_download_whisper_with_retry retries up to MAX_DOWNLOAD_ATTEMPTS then raises."""
    with (
        patch("voiceforge.cli.download_models._is_whisper_model_cached", return_value=False),
        patch("voiceforge.cli.download_models.WhisperModel") as mock_wm,
    ):
        mock_wm.side_effect = RuntimeError("network error")
        with patch("voiceforge.cli.download_models.time.sleep"), pytest.raises(RuntimeError, match="network error"):
            _download_whisper_with_retry("tiny")
        assert mock_wm.call_count == 3


def test_download_whisper_returns_false_when_cached() -> None:
    """Cached model should be warmed locally without remote-download semantics."""
    with (
        patch("voiceforge.cli.download_models._is_whisper_model_cached", return_value=True),
        patch("voiceforge.cli.download_models.WhisperModel") as mock_wm,
    ):
        mock_wm.return_value = MagicMock()
        downloaded = _download_whisper_with_retry("tiny", device="cpu", compute_type="int8")

    mock_wm.assert_called_once_with("tiny", device="cpu", compute_type="int8", local_files_only=True)
    assert downloaded is False


def test_ensure_onnx_embedder_returns_false_when_no_files(tmp_path) -> None:
    """_ensure_onnx_embedder returns False when model dir has no model.onnx."""
    with patch("voiceforge.rag.embedder.get_default_model_dir", return_value=str(tmp_path)):
        # _ensure_onnx_embedder uses get_default_model_dir from embedder when building Path
        result = _ensure_onnx_embedder()
    assert result is False


def test_run_download_models_mocked_whisper(monkeypatch) -> None:
    """run_download_models calls Whisper download (mocked) and uses config model_size."""
    with (
        patch("voiceforge.cli.download_models._download_whisper_with_retry") as mock_dl,
        patch("voiceforge.cli.download_models._ensure_onnx_embedder", return_value=False),
        patch("voiceforge.core.config.Settings") as mock_settings,
    ):
        mock_dl.return_value = True
        mock_cfg = MagicMock()
        mock_cfg.model_size = "tiny"
        mock_settings.return_value = mock_cfg
        downloaded = run_download_models(model_size=None, skip_onnx=True, use_rich_progress=False)
        mock_dl.assert_called_once_with("tiny")
        assert downloaded is True


def test_run_download_models_respects_model_size_arg(monkeypatch) -> None:
    """run_download_models uses --model-size when provided."""
    with (
        patch("voiceforge.cli.download_models._download_whisper_with_retry") as mock_dl,
        patch("voiceforge.cli.download_models._ensure_onnx_embedder", return_value=False),
        patch("voiceforge.core.config.Settings") as mock_settings,
    ):
        mock_dl.return_value = True
        mock_cfg = MagicMock()
        mock_cfg.model_size = "small"
        mock_settings.return_value = mock_cfg
        downloaded = run_download_models(model_size="base", skip_onnx=True, use_rich_progress=False)
        mock_dl.assert_called_once_with("base")
        assert downloaded is True


def test_run_download_models_calls_onnx_when_not_skipped(monkeypatch) -> None:
    """run_download_models calls _ensure_onnx_embedder when skip_onnx=False."""
    with (
        patch("voiceforge.cli.download_models._download_whisper_with_retry"),
        patch("voiceforge.cli.download_models._ensure_onnx_embedder") as mock_onnx,
        patch("voiceforge.core.config.Settings") as mock_settings,
    ):
        mock_onnx.return_value = False
        mock_cfg = MagicMock()
        mock_cfg.model_size = "tiny"
        mock_settings.return_value = mock_cfg
        run_download_models(skip_onnx=False, use_rich_progress=False)
        mock_onnx.assert_called_once()

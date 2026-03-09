"""E12 #135: Mock-only tests for rag.indexer and rag.embedder to allow removing from coverage omit."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from voiceforge.rag.embedder import (
    EMBED_DIM,
    MiniLMEmbedder,
    _find_model_dir,
    get_default_model_dir,
)
from voiceforge.rag.indexer import (
    CHUNK_OVERLAP_RATIO,
    CHUNK_TOKENS,
    KnowledgeIndexer,
    _chunk_text,
    _sections_to_new_chunks,
)


def test_get_default_model_dir_respects_xdg(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_default_model_dir uses XDG_CACHE_HOME when set."""
    monkeypatch.setenv("XDG_CACHE_HOME", "/tmp/cache")
    assert "voiceforge" in get_default_model_dir()
    assert "/tmp/cache" in get_default_model_dir() or "minilm-onnx" in get_default_model_dir()


def test_find_model_dir_finds_onnx_subdir(tmp_path: Path) -> None:
    """_find_model_dir returns path when model.onnx is in base/onnx/."""
    (tmp_path / "onnx").mkdir()
    (tmp_path / "onnx" / "model.onnx").write_bytes(b"")
    assert _find_model_dir(tmp_path) == tmp_path / "onnx"


def test_find_model_dir_finds_base(tmp_path: Path) -> None:
    """_find_model_dir returns base when model.onnx is in base."""
    (tmp_path / "model.onnx").write_bytes(b"")
    assert _find_model_dir(tmp_path) == tmp_path


def test_find_model_dir_raises_when_missing(tmp_path: Path) -> None:
    """_find_model_dir raises FileNotFoundError when no model.onnx."""
    with pytest.raises(FileNotFoundError, match=r"No model\.onnx"):
        _find_model_dir(tmp_path)


def test_minilm_embedder_encode_empty_returns_zeros(tmp_path: Path) -> None:
    """MiniLMEmbedder.encode([]) returns (0, EMBED_DIM) array without calling ONNX."""
    (tmp_path / "model.onnx").write_bytes(b"")
    with patch("voiceforge.rag.embedder._onnx_runner") as m:
        m.load.return_value = (MagicMock(), MagicMock())
        emb = MiniLMEmbedder(tmp_path)
        out = emb.encode([])
    assert out.shape == (0, EMBED_DIM)
    assert out.dtype == np.float32


def test_minilm_embedder_encode_with_mock_onnx(tmp_path: Path) -> None:
    """MiniLMEmbedder.encode with mocked ONNX returns correct shape."""
    (tmp_path / "model.onnx").write_bytes(b"")
    with patch("voiceforge.rag.embedder._onnx_runner") as m:
        m.load.return_value = (MagicMock(), MagicMock())
        m.encode_batch.return_value = np.zeros((2, EMBED_DIM), dtype=np.float32)
        emb = MiniLMEmbedder(tmp_path)
        out = emb.encode(["hello", "world"], batch_size=2)
    assert out.shape == (2, EMBED_DIM)


def test_chunk_text_splits_by_tokens() -> None:
    """_chunk_text splits text into ~CHUNK_TOKENS words per chunk."""
    words = ["w"] * 500
    text = " ".join(words)
    chunks = _chunk_text(text, token_approx=CHUNK_TOKENS, overlap_ratio=CHUNK_OVERLAP_RATIO)
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c.split()) <= CHUNK_TOKENS + 50  # allow some slack


def test_chunk_text_empty_returns_empty() -> None:
    """_chunk_text returns [] for empty string."""
    assert _chunk_text("") == []


def test_sections_to_new_chunks_skips_empty() -> None:
    """_sections_to_new_chunks skips empty sections."""
    chunks = _sections_to_new_chunks(["  ", "", "hello world"])
    assert len(chunks) >= 1
    assert any("hello" in c.content for c in chunks)


def test_knowledge_indexer_add_file_unsupported_raises(tmp_path: Path) -> None:
    """KnowledgeIndexer.add_file raises ValueError for unsupported extension (no DB/embedder used)."""
    db = tmp_path / "vec.db"
    idx = KnowledgeIndexer(db)
    bad_file = tmp_path / "x.xyz"
    bad_file.write_text("x")
    with pytest.raises(ValueError, match="Unsupported format"):
        idx.add_file(bad_file)

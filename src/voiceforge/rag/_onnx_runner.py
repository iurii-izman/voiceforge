"""Load ONNX session and tokenizer, run embedding (internal)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

# Optional: only used when [rag] installed
try:
    import onnxruntime as ort
except ImportError:
    ort = None  # type: ignore[assignment]
try:
    from tokenizers import Tokenizer
except ImportError:
    Tokenizer = None  # type: ignore[misc, assignment]


def load(model_dir: Path) -> tuple[Any, Any]:
    if ort is None or Tokenizer is None:
        raise ImportError("Install [rag]: uv sync --extra rag (onnxruntime, tokenizers)")
    onnx_path = model_dir / "model.onnx"
    if not onnx_path.is_file():
        raise FileNotFoundError(str(onnx_path))
    session = ort.InferenceSession(
        str(onnx_path),
        providers=["CPUExecutionProvider"],
        sess_options=ort.SessionOptions(),
    )
    tokenizer_path = model_dir.parent / "tokenizer.json"
    if not tokenizer_path.is_file():
        tokenizer_path = model_dir / "tokenizer.json"
    if not tokenizer_path.is_file():
        raise FileNotFoundError("tokenizer.json not in model dir or parent")
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    return session, tokenizer


def encode_batch(
    session: Any,
    tokenizer: Any,
    texts: list[str],
    max_length: int,
) -> np.ndarray:
    enc = tokenizer.encode_batch(texts, add_special_tokens=True)
    pad_len = max_length
    ids_list: list[list[int]] = []
    mask_list: list[list[int]] = []
    for e in enc:
        ids = e.ids[:pad_len]
        mask = [1] * len(ids)
        if len(ids) < pad_len:
            ids = ids + [0] * (pad_len - len(ids))
            mask = mask + [0] * (pad_len - len(mask))
        ids_list.append(ids)
        mask_list.append(mask)
    input_ids = np.array(ids_list, dtype=np.int64)
    attention_mask = np.array(mask_list, dtype=np.int64)
    token_type_ids = np.zeros_like(input_ids, dtype=np.int64)
    feed: dict[str, np.ndarray] = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
    }
    input_names = {inp.name for inp in session.get_inputs()}
    if "token_type_ids" in input_names:
        feed["token_type_ids"] = token_type_ids
    outputs = session.run(None, feed)
    # Prefer sentence_embedding (batch, 384); else mean-pool token_embeddings (batch, seq, 384)
    for o in outputs:
        if o.ndim == 2 and o.shape[1] == 384:
            return o.astype(np.float32)
    out = outputs[0]
    if out.ndim == 3:
        # (batch, seq, 384) -> mean over seq (with attention_mask if needed)
        out = out.mean(axis=1)
    return out.astype(np.float32)

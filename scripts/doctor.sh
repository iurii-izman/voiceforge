#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "[FAIL] uv not found"
  exit 1
fi

echo "[OK] uv: $(uv --version)"

uv run python - <<'PY'
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

from voiceforge.core.config import Settings

cfg = Settings()
errors = 0
warnings = 0

def ok(msg: str) -> None:
    print(f"[OK] {msg}")

def warn(msg: str) -> None:
    global warnings
    warnings += 1
    print(f"[WARN] {msg}")

def fail(msg: str) -> None:
    global errors
    errors += 1
    print(f"[FAIL] {msg}")

ok(f"python: {sys.version.split()[0]}")
ok(f"config default_llm={cfg.default_llm}")
ok(f"ring_file={cfg.get_ring_file_path()}")
ok(f"rag_db={cfg.get_rag_db_path()}")

for optional_path in (
    Path(cfg.get_ring_file_path()),
    Path(cfg.get_rag_db_path()),
):
    if optional_path.exists():
        ok(f"path exists: {optional_path}")
    else:
        warn(f"path missing (optional): {optional_path}")

try:
    import keyring
except Exception as exc:
    warn(f"keyring unavailable: {exc}")
else:
    found = []
    for name in ("anthropic", "openai", "huggingface"):
        try:
            value = keyring.get_password("voiceforge", name)
        except Exception as exc:
            warn(f"keyring read failed for {name}: {exc}")
            continue
        if value:
            found.append(name)
    if found:
        ok(f"keyring entries present: {', '.join(found)}")
    else:
        warn("no keyring entries found for voiceforge/{anthropic,openai,huggingface}")

for module_name, hard in (
    ("faster_whisper", False),
    ("litellm", False),
    ("sqlite_vec", False),
):
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        if hard:
            fail(f"import failed: {module_name} ({exc})")
        else:
            warn(f"import optional: {module_name} unavailable ({exc})")
    else:
        ok(f"import: {module_name}")

status = subprocess.run(
    ["uv", "run", "voiceforge", "status", "--output", "json"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if status.returncode != 0:
    fail("voiceforge status --output json failed")
else:
    parsed = None
    for line in reversed([ln.strip() for ln in status.stdout.splitlines() if ln.strip()]):
        if line.startswith("{") and line.endswith("}"):
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            break
    if parsed is None:
        fail("status output does not contain JSON payload")
    else:
        for key in ("schema_version", "ok", "data"):
            if key not in parsed:
                fail(f"status payload missing key: {key}")
        if parsed.get("ok") is True:
            ok("status contract ok")
        else:
            fail("status payload reports ok=false")

print(f"doctor-summary: errors={errors} warnings={warnings}")
if errors:
    raise SystemExit(1)
PY

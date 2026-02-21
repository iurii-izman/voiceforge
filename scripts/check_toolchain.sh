#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required" >&2
  exit 1
fi

uv_version="$(uv --version | awk '{print $2}')"
if [[ -z "${uv_version}" ]]; then
  echo "Unable to resolve uv version" >&2
  exit 1
fi

python_minor="$(
  uv run python - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"

python_major="${python_minor%%.*}"
python_min="${python_minor##*.}"
if [[ "${python_major}" != "3" || "${python_min}" -lt 12 ]]; then
  echo "Unsupported Python runtime: ${python_minor} (expected >=3.12)" >&2
  exit 1
fi

uv run python - <<'PY'
from pathlib import Path
import tomllib

cfg = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
requires_python = cfg["project"]["requires-python"]
if requires_python != ">=3.12":
    raise SystemExit(f"Unexpected requires-python: {requires_python}")
print(f"toolchain-ok: requires-python={requires_python}")
PY

echo "toolchain-ok: python=${python_minor} uv=${uv_version}"
echo "toolchain-targets: ci-matrix=3.12,3.13"

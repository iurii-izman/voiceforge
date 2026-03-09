#!/usr/bin/env bash
set -euo pipefail

allow_dirty=0
with_tests=0
skip_governance=0

usage() {
  cat <<'EOF'
Usage: ./scripts/preflight_repo.sh [--allow-dirty] [--with-tests] [--skip-governance]

Checks:
  - git workspace cleanliness (unless --allow-dirty)
  - toolchain contract
  - release/install metadata consistency
  - documentation consistency and required stubs
  - repository governance/security baseline (unless --skip-governance)
  - lightweight smoke checks (only with --with-tests)
EOF
  return 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-dirty)
      allow_dirty=1
      ;;
    --with-tests)
      with_tests=1
      ;;
    --skip-governance)
      skip_governance=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

echo "[preflight] repo=$(basename "$PWD")"

if [[ $allow_dirty -ne 1 ]]; then
  if [[ -n "$(git status --short)" ]]; then
    echo "[FAIL] git workspace is dirty; commit/stash or rerun with --allow-dirty" >&2
    exit 1
  fi
  echo "[OK] git workspace is clean"
else
  echo "[SKIP] git cleanliness check disabled (--allow-dirty)"
fi

echo "[preflight] toolchain"
./scripts/check_toolchain.sh

echo "[preflight] release metadata"
uv run python scripts/check_release_metadata.py

echo "[preflight] docs consistency"
uv run python scripts/check_docs_consistency.py

if [[ $skip_governance -ne 1 ]]; then
  echo "[preflight] repo governance"
  ./scripts/check_repo_governance.sh
else
  echo "[SKIP] repo governance check disabled (--skip-governance)"
fi

if [[ $with_tests -eq 1 ]]; then
  echo "[preflight] lightweight smoke"
  ./scripts/check_cli_contract.sh
  uv run pytest tests/test_release_proof.py -q --tb=line
else
  echo "[SKIP] lightweight smoke disabled (use --with-tests)"
fi

echo "preflight_repo.sh: READY"
exit 0

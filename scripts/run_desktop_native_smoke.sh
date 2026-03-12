#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/run_desktop_native_smoke.sh [--headless]

Canonical advisory native smoke runner for VoiceForge desktop.

Options:
  --headless   Run under xvfb-run for toolbox/CI-like Linux environments.
  --help       Show this help.
EOF
  return 0
}

HEADLESS=0
for arg in "$@"; do
  case "$arg" in
    --headless)
      HEADLESS=1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
DESKTOP_DIR="$REPO_ROOT/desktop"
ARTIFACT_ROOT="$DESKTOP_DIR/e2e-native/artifacts"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
if [[ "$HEADLESS" -eq 1 ]]; then
  MODE_NAME="headless"
else
  MODE_NAME="headed"
fi
ARTIFACT_DIR=${VOICEFORGE_NATIVE_SMOKE_ARTIFACT_DIR:-"$ARTIFACT_ROOT/${TIMESTAMP}-${MODE_NAME}"}
SUMMARY_FILE="$ARTIFACT_DIR/summary.txt"
RUN_LOG="$ARTIFACT_DIR/native-smoke.log"
LATEST_LINK="$ARTIFACT_ROOT/latest"
TIMEOUT_SEC=${VOICEFORGE_NATIVE_SMOKE_TIMEOUT_SEC:-120}

mkdir -p "$ARTIFACT_DIR"
rm -f "$LATEST_LINK"
ln -s "$(basename "$ARTIFACT_DIR")" "$LATEST_LINK" 2>/dev/null || true

log() {
  printf '%s\n' "$*" | tee -a "$SUMMARY_FILE"
  return 0
}

fail() {
  log "[FAIL] $*"
  log "[INFO] artifacts: $ARTIFACT_DIR"
  exit 1
}

command -v npm >/dev/null 2>&1 || fail "npm is required"
command -v cargo >/dev/null 2>&1 || fail "cargo is required"

if ! command -v tauri-driver >/dev/null 2>&1 && [[ ! -x "${TAURI_DRIVER_PATH:-$HOME/.cargo/bin/tauri-driver}" ]]; then
  fail "tauri-driver not found. Install with: cargo install tauri-driver --locked"
fi

if [[ "$HEADLESS" -eq 1 ]] && ! command -v xvfb-run >/dev/null 2>&1; then
  fail "xvfb-run not found. Install xvfb in toolbox/system."
fi

TOOLBOX_HINT="host"
if [[ -f /run/.containerenv ]]; then
  TOOLBOX_HINT="toolbox"
fi

{
  echo "mode=$MODE_NAME"
  echo "artifact_dir=$ARTIFACT_DIR"
  echo "repo_root=$REPO_ROOT"
  echo "desktop_dir=$DESKTOP_DIR"
  echo "timeout_sec=$TIMEOUT_SEC"
  echo "environment=$TOOLBOX_HINT"
  echo "npm=$(command -v npm)"
  echo "cargo=$(command -v cargo)"
  echo "tauri_driver=${TAURI_DRIVER_PATH:-$(command -v tauri-driver || true)}"
  echo "webkit_driver=${TAURI_NATIVE_DRIVER:-${WEBKIT_WEBDRIVER:-auto-resolve-in-wdio}}"
} >"$ARTIFACT_DIR/preflight.txt"

log "[INFO] VoiceForge desktop native smoke ($MODE_NAME)"
log "[INFO] environment: $TOOLBOX_HINT"
log "[INFO] artifacts: $ARTIFACT_DIR"
if [[ "$TOOLBOX_HINT" != "toolbox" ]]; then
  log "[WARN] native smoke is most reproducible inside toolbox"
fi

export VOICEFORGE_NATIVE_SMOKE_ARTIFACT_DIR="$ARTIFACT_DIR"
export WDIO_LOG_LEVEL="${WDIO_LOG_LEVEL:-warn}"

log "[INFO] installing native e2e dependencies"
npm --prefix "$DESKTOP_DIR/e2e-native" ci >>"$SUMMARY_FILE" 2>&1

RUN_CMD=(npm --prefix "$DESKTOP_DIR/e2e-native" run test)
if [[ "$HEADLESS" -eq 1 ]]; then
  RUN_CMD=(npm --prefix "$DESKTOP_DIR/e2e-native" run test:headless)
fi

log "[INFO] running: ${RUN_CMD[*]}"
set +e
timeout "${TIMEOUT_SEC}s" "${RUN_CMD[@]}" 2>&1 | tee "$RUN_LOG"
RC=${PIPESTATUS[0]}
set -e

if [[ "$RC" -eq 0 ]]; then
  log "[PASS] native smoke completed"
  log "[INFO] artifacts: $ARTIFACT_DIR"
  exit 0
fi

if [[ "$RC" -eq 124 ]]; then
  fail "native smoke timed out after ${TIMEOUT_SEC}s"
fi

fail "native smoke failed with exit code $RC"

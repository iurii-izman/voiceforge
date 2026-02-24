#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./scripts/check_sonar_status.sh [options]

Options:
  --ref <git-ref>       Git ref to inspect (default: origin/main, fallback: HEAD)
  --repo <owner/name>   GitHub repo (default: current gh repo)
  --timeout <seconds>   Poll timeout (default: 180)
  --interval <seconds>  Poll interval (default: 6)
  --required            Exit non-zero if Sonar check is missing after timeout
  -h, --help            Show this help
EOF
  return 0
}

ref=""
repo=""
timeout_s=180
interval_s=6
required=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ref)
      ref="${2:-}"
      shift 2
      ;;
    --repo)
      repo="${2:-}"
      shift 2
      ;;
    --timeout)
      timeout_s="${2:-}"
      shift 2
      ;;
    --interval)
      interval_s="${2:-}"
      shift 2
      ;;
    --required)
      required=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub auth required. Run: gh auth login" >&2
  exit 1
fi

if [[ -z "${repo}" ]]; then
  repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
fi

if [[ -z "${ref}" ]]; then
  if git rev-parse --verify --quiet origin/main >/dev/null; then
    ref="origin/main"
  else
    ref="HEAD"
  fi
fi

sha="$(git rev-parse "${ref}")"
echo "Checking SonarCloud check-run for ${repo} @ ${ref} (${sha})"

start="$(date +%s)"
while :; do
  line="$(
    gh api "repos/${repo}/commits/${sha}/check-runs" \
      --jq '.check_runs[]? | select(.name=="SonarCloud Code Analysis") | "\(.status)|\(.conclusion // "null")|\(.details_url // "")"' \
      | head -n1 || true
  )"

  if [[ -n "${line}" ]]; then
    status="${line%%|*}"
    rest="${line#*|}"
    conclusion="${rest%%|*}"
    details_url="${rest#*|}"
    case "${status}" in
      completed)
        if [[ "${conclusion}" == "success" ]]; then
          echo "sonar-status: OK (${details_url})"
          exit 0
        fi
        echo "sonar-status: FAIL (conclusion=${conclusion}, url=${details_url})" >&2
        exit 1
        ;;
      queued|in_progress)
        echo "sonar-status: waiting (status=${status})"
        ;;
      *)
        echo "sonar-status: unexpected check status=${status}" >&2
        exit 1
        ;;
    esac
  else
    echo "sonar-status: SonarCloud check-run not found yet for ${sha}"
  fi

  now="$(date +%s)"
  elapsed="$((now - start))"
  if (( elapsed >= timeout_s )); then
    if (( required == 1 )); then
      echo "sonar-status: timeout (${timeout_s}s), check-run missing or not completed" >&2
      exit 1
    fi
    echo "sonar-status: timeout (${timeout_s}s), skipping in non-required mode"
    exit 0
  fi
  sleep "${interval_s}"
done

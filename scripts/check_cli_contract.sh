#!/usr/bin/env bash
set -euo pipefail

uv run pytest tests/test_cli_surface.py -q

help_output="$(uv run voiceforge --help)"
required=(
  "listen"
  "analyze"
  "status"
  "history"
  "index"
  "watch"
  "daemon"
  "install-service"
  "uninstall-service"
)
for cmd in "${required[@]}"; do
  if ! grep -q "${cmd}" <<<"${help_output}"; then
    echo "Missing CLI command in help output: ${cmd}" >&2
    exit 1
  fi
done

if uv run voiceforge tasks >/dev/null 2>&1; then
  echo "Unexpected legacy command 'tasks' still available" >&2
  exit 1
fi

echo "check_cli_contract.sh: OK"

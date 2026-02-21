#!/usr/bin/env bash
set -euo pipefail

if [[ "${VOICEFORGE_ALLOW_MAIN_PUSH:-0}" == "1" ]]; then
  exit 0
fi

while read -r local_ref local_sha remote_ref remote_sha; do
  if [[ "${remote_ref}" == "refs/heads/main" ]]; then
    echo "Direct pushes to main are blocked. Create a PR branch instead." >&2
    echo "Override for emergency only: VOICEFORGE_ALLOW_MAIN_PUSH=1 git push ..." >&2
    exit 1
  fi
done

exit 0

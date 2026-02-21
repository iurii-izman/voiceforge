#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub auth required. Run: gh auth login" >&2
  exit 1
fi

repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
payload_file=".github/rulesets/main-protection.json"
if [[ ! -f "$payload_file" ]]; then
  echo "Missing ruleset file: $payload_file" >&2
  exit 1
fi

set +e
rulesets_response="$(gh api "repos/${repo}/rulesets" 2>&1)"
rulesets_status=$?
set -e
if [[ $rulesets_status -ne 0 ]]; then
  if grep -qi "Upgrade to GitHub Pro" <<<"$rulesets_response"; then
    echo "Rulesets API unavailable for this private repository plan." >&2
    echo "Use repository settings manually after upgrading plan/public visibility." >&2
    exit 2
  fi
  echo "$rulesets_response" >&2
  exit $rulesets_status
fi

existing_id="$(gh api "repos/${repo}/rulesets" --jq '.[] | select(.name=="main-hardening-alpha0.1") | .id' | head -n1 || true)"

if [[ -n "${existing_id}" ]]; then
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${repo}/rulesets/${existing_id}" \
    --input "$payload_file" >/dev/null
  echo "Updated ruleset id=${existing_id} for ${repo}"
else
  gh api \
    --method POST \
    -H "Accept: application/vnd.github+json" \
    "repos/${repo}/rulesets" \
    --input "$payload_file" >/dev/null
  echo "Created ruleset for ${repo}"
fi

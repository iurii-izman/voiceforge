#!/usr/bin/env bash
# Temporarily allow or restore main branch protection (pull_request rule).
# Usage: ./scripts/ruleset_enforcement.sh [allow-direct-push|require-pr]
#   allow-direct-push — remove pull_request rule from ruleset (direct push to main allowed)
#   require-pr       — restore full ruleset from .github/rulesets/main-protection.json (PR required)
# Note: enforcement=evaluate is GitHub Enterprise only; on Free/Team we remove the rule instead.
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub auth required. Run: gh auth login" >&2
  exit 1
fi

mode="${1:-}"
if [[ "$mode" != "allow-direct-push" && "$mode" != "require-pr" ]]; then
  echo "Usage: $0 allow-direct-push | require-pr" >&2
  echo "  allow-direct-push — remove pull_request rule (direct push to main allowed)" >&2
  echo "  require-pr       — restore full ruleset from main-protection.json (PR required)" >&2
  exit 1
fi

repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
payload_file=".github/rulesets/main-protection.json"
ruleset_name="main-hardening-alpha0.1"

ruleset_id="$(gh api "repos/${repo}/rulesets" --jq ".[] | select(.name==\"${ruleset_name}\") | .id" | head -n1 || true)"
if [[ -z "${ruleset_id}" ]]; then
  echo "Ruleset ${ruleset_name} not found." >&2
  exit 1
fi

if [[ "$mode" == "allow-direct-push" ]]; then
  echo "Removing pull_request rule from ruleset (direct push to main allowed)."
  payload="$(gh api "repos/${repo}/rulesets/${ruleset_id}" | jq '
    del(._links, .created_at, .updated_at, .node_id, .source, .source_type, .current_user_can_bypass) |
    .rules |= map(select(.type != "pull_request"))
  ')"
  echo "$payload" | gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${repo}/rulesets/${ruleset_id}" \
    --input - >/dev/null
  echo "Done. pull_request rule removed."
else
  if [[ ! -f "$payload_file" ]]; then
    echo "Missing ruleset file: $payload_file" >&2
    exit 1
  fi
  echo "Restoring full ruleset from ${payload_file} (PR required for main)."
  gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/${repo}/rulesets/${ruleset_id}" \
    --input "$payload_file" >/dev/null
  echo "Done. pull_request rule restored."
fi

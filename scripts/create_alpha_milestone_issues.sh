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
issues_enabled="$(gh repo view "${repo}" --json hasIssuesEnabled --jq .hasIssuesEnabled)"
if [[ "${issues_enabled}" != "true" ]]; then
  echo "Issues are disabled for ${repo}. Enable issues first." >&2
  exit 2
fi

milestone="alpha0.1-hardening"
description="Sprint hardening scope for alpha0.1 baseline"

milestone_id="$(
  gh api "repos/${repo}/milestones?state=all" --jq ".[] | select(.title==\"${milestone}\") | .number" | head -n1 || true
)"
if [[ -z "${milestone_id}" ]]; then
  milestone_id="$(
    gh api \
      --method POST \
      -H "Accept: application/vnd.github+json" \
      "repos/${repo}/milestones" \
      -f title="${milestone}" \
      -f description="${description}" \
      --jq .number
  )"
  echo "Created milestone ${milestone} (#${milestone_id})"
else
  echo "Milestone already exists: ${milestone} (#${milestone_id})"
fi

if ! gh label list --repo "${repo}" --limit 200 --json name --jq '.[] | .name' | grep -qx "chore"; then
  gh label create "chore" --repo "${repo}" --color C2E0C6 --description "chore" >/dev/null
fi

issues=(
  "Protect main with ruleset and required checks"
  "CI matrix on Python 3.12 and 3.13"
  "Dedicated CLI contract CI check"
  "DB migrations test suite (clean + existing DB)"
  "Add end-to-end CLI smoke (listen/analyze/history)"
  "Weekly scheduled security/dependency scan"
  "Draft release notes automation"
  "Generate SBOM on release"
  "Document config/env contract"
  "Add doctor environment diagnostics command/script"
  "Bootstrap installs pre-commit hooks"
  "Rollback runbook for failed alpha release"
)

for title in "${issues[@]}"; do
  exists="$(
    gh issue list --repo "${repo}" --state all --search "in:title ${title}" --json title --jq ".[0].title" || true
  )"
  if [[ "${exists}" == "${title}" ]]; then
    echo "Issue exists: ${title}"
    continue
  fi
  gh issue create \
    --repo "${repo}" \
    --title "${title}" \
    --body "Tracking item for ${milestone}." \
    --milestone "${milestone}" \
    --label "chore" >/dev/null
  echo "Created issue: ${title}"
done

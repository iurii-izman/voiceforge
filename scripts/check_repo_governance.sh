#!/usr/bin/env bash
set -euo pipefail

repo="${1:-}"
ruleset_name="main-hardening-alpha0.1"
expected_checks=("quality (3.12)" "quality (3.13)" "cli-contract" "db-migrations" "e2e-smoke")

if ! command -v gh >/dev/null 2>&1; then
  echo "[FAIL] gh CLI is required"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "[FAIL] GitHub auth required. Run: gh auth login"
  exit 1
fi

if [[ -z "${repo}" ]]; then
  repo="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
fi

errors=0

ok() {
  echo "[OK] $*"
}

fail() {
  echo "[FAIL] $*"
  errors=$((errors + 1))
}

contains_line() {
  local needle="$1"
  shift
  local value
  for value in "$@"; do
    if [[ "${value}" == "${needle}" ]]; then
      return 0
    fi
  done
  return 1
}

echo "governance-check: repo=${repo}"

visibility="$(gh api "repos/${repo}" --jq '.visibility')"
if [[ "${visibility}" == "public" ]]; then
  ok "repo visibility is public"
else
  fail "repo visibility expected public, got ${visibility}"
fi

ruleset_id="$(gh api "repos/${repo}/rulesets" --jq ".[] | select(.name==\"${ruleset_name}\") | .id" | head -n1 || true)"
if [[ -z "${ruleset_id}" ]]; then
  fail "ruleset ${ruleset_name} not found"
else
  ok "ruleset ${ruleset_name} found (id=${ruleset_id})"
  enforcement="$(gh api "repos/${repo}/rulesets/${ruleset_id}" --jq '.enforcement')"
  if [[ "${enforcement}" == "active" ]]; then
    ok "ruleset enforcement is active"
  else
    fail "ruleset enforcement expected active, got ${enforcement}"
  fi

  pr_required="$(gh api "repos/${repo}/rulesets/${ruleset_id}" --jq '.rules[] | select(.type=="pull_request") | .parameters.required_approving_review_count')"
  if [[ "${pr_required}" == "0" ]]; then
    ok "solo PR mode enabled (required approvals=0)"
  else
    fail "required approvals expected 0, got ${pr_required}"
  fi

  mapfile -t checks < <(gh api "repos/${repo}/rulesets/${ruleset_id}" --jq '.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context')
  for expected in "${expected_checks[@]}"; do
    if contains_line "${expected}" "${checks[@]}"; then
      ok "required check present: ${expected}"
    else
      fail "required check missing: ${expected}"
    fi
  done
fi

dependabot_updates="$(gh api "repos/${repo}" --jq '.security_and_analysis.dependabot_security_updates.status')"
if [[ "${dependabot_updates}" == "enabled" ]]; then
  ok "dependabot security updates enabled"
else
  fail "dependabot security updates are ${dependabot_updates}"
fi

secret_scanning="$(gh api "repos/${repo}" --jq '.security_and_analysis.secret_scanning.status')"
if [[ "${secret_scanning}" == "enabled" ]]; then
  ok "secret scanning enabled"
else
  fail "secret scanning is ${secret_scanning}"
fi

push_protection="$(gh api "repos/${repo}" --jq '.security_and_analysis.secret_scanning_push_protection.status')"
if [[ "${push_protection}" == "enabled" ]]; then
  ok "secret scanning push protection enabled"
else
  fail "secret scanning push protection is ${push_protection}"
fi

set +e
gh api "repos/${repo}/vulnerability-alerts" -H "Accept: application/vnd.github+json" >/dev/null 2>&1
vuln_status=$?
set -e
if [[ ${vuln_status} -eq 0 ]]; then
  ok "vulnerability alerts endpoint enabled"
else
  fail "vulnerability alerts endpoint not enabled"
fi

set +e
open_dependabot="$(gh api "repos/${repo}/dependabot/alerts?state=open" --jq 'length' 2>/dev/null)"
dep_status=$?
set -e
if [[ ${dep_status} -eq 0 ]]; then
  ok "dependabot alerts endpoint available (open=${open_dependabot})"
else
  fail "dependabot alerts endpoint unavailable"
fi

echo "governance-check-summary: errors=${errors}"
if [[ ${errors} -ne 0 ]]; then
  exit 1
fi

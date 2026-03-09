#!/usr/bin/env bash
# Create or sync quality remediation issues and add them to GitHub Project.
set -euo pipefail

REPO="iurii-izman/voiceforge"
PROJECT_ID="PVT_kwHODvfgWM4BQC-Z"
STATUS_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-R4aU"
PHASE_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeSw"
PRIORITY_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUM"
EFFORT_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUQ"
AREA_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUU"

TODO="f75ad846"
PHASE_OPERATIONAL="c2ee0707"
P0="1016b51c"
P1="b12f98f6"
P2="595114bb"
S="89ac7c75"
M="10a9e752"
L="4f65026a"
BACKEND="3b82b44a"
DEVOPS="cd368946"
FRONTEND="6bb5ba28"
TESTING="cb342949"
SECURITY="6a0f371d"

ensure_label() {
  local name="$1"
  local color="$2"
  local desc="$3"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force >/dev/null
  return 0
}

find_issue_number() {
  local title="$1"
  gh issue list --repo "$REPO" --state all --limit 200 --json number,title --jq ".[] | select(.title == \"${title}\") | .number" | head -n1
}

find_item_id() {
  local number="$1"
  gh project item-list 1 --owner iurii-izman --limit 200 --format json --jq ".items[] | select(.content.number==${number}) | .id" | head -n1
}

ensure_issue() {
  local title="$1"
  local body="$2"
  local labels="$3"
  local priority="$4"
  local effort="$5"
  local area="$6"

  local number
  number="$(find_issue_number "$title")"
  if [[ -z "$number" ]]; then
    local url
    url="$(gh issue create -R "$REPO" --title "$title" --body "$body" --label "$labels")"
    number="${url##*/}"
  else
    gh issue edit "$number" --repo "$REPO" --title "$title" --body "$body" >/dev/null
    IFS=',' read -r -a label_array <<<"$labels"
    for label in "${label_array[@]}"; do
      gh issue edit "$number" --repo "$REPO" --add-label "$label" >/dev/null
    done
  fi

  local item_id
  item_id="$(find_item_id "$number")"
  if [[ -z "$item_id" ]]; then
    item_id="$(gh project item-add 1 --owner iurii-izman --url "https://github.com/${REPO}/issues/${number}" --format json --jq .id)"
  fi

  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$STATUS_FIELD" --single-select-option-id "$TODO" >/dev/null
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$PHASE_FIELD" --single-select-option-id "$PHASE_OPERATIONAL" >/dev/null
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$PRIORITY_FIELD" --single-select-option-id "$priority" >/dev/null
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$EFFORT_FIELD" --single-select-option-id "$effort" >/dev/null
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$AREA_FIELD" --single-select-option-id "$area" >/dev/null

  printf '%s\t%s\n' "$number" "$title"
}

ensure_label "quality-remediation" "0052CC" "Static analysis, quality gate and security debt remediation track"

echo "=== Creating quality remediation issues ==="

ensure_issue \
"QA1 · Security & Supply Chain Remediation (CodeQL + Dependabot)" \
"$(cat <<'BODY'
## Context

Visible GitHub security debt is now concentrated in:

- CodeQL alert `py/clear-text-logging-sensitive-data` in `scripts/git_credential_keyring_pat.py`
- Dependabot alert `#4` (`serialize-javascript`, npm, `desktop/e2e-native/package-lock.json`)
- Dependabot alert `#3` (`time`, rust, `desktop/src-tauri/Cargo.lock`)
- Dependabot alert `#2` (`glib`, rust, `desktop/src-tauri/Cargo.lock`)
- existing external wait-state: `#65` / `CVE-2025-69872`

## Scope

- Fix the CodeQL alert or prove it is a false positive and document the reason
- Triage and remediate GitHub Dependabot alerts where safe
- Keep `#65` as a tracked upstream wait-state unless an upstream fix actually exists
- Sync `docs/runbooks/security-decision-log.md` with the resulting state

## Acceptance Criteria

- [ ] CodeQL security alert is closed or explicitly dismissed with justified rationale
- [ ] Dependabot alerts are either fixed or documented with explicit revisit triggers
- [ ] `security-decision-log.md` reflects the new reality
- [ ] No secrets or PAT flows are logged in clear text
- [ ] Targeted checks pass

## Notes

Source commands: `gh api repos/.../dependabot/alerts`, `gh api repos/.../code-scanning/alerts`, `uv run python scripts/sonar_fetch_issues.py`.
BODY
)" \
"quality-remediation,autopilot,operational,p0,area:security" "$P0" "$M" "$SECURITY"

ensure_issue \
"QA2 · Local Gate Recovery (mypy + verify_pr parity)" \
"$(cat <<'BODY'
## Context

`ruff`, `bandit`, `pip-audit` and `preflight` are green, but `mypy` currently fails.

Current observed failures:

- `src/voiceforge/stt/transcriber.py:101`
- `src/voiceforge/core/transcript_log.py:24`

## Scope

- Fix current `mypy` failures in tracked source files
- Ensure local type gate matches documented `verify_pr.sh` expectations
- Update docs only if the gate contract changes

## Acceptance Criteria

- [ ] `uv run mypy src/voiceforge/core src/voiceforge/llm src/voiceforge/rag src/voiceforge/stt --ignore-missing-imports` passes
- [ ] `verify_pr.sh` / preflight expectations stay aligned
- [ ] No unrelated feature changes

## Notes

This block exists to restore gate honesty before broader Sonar cleanup.
BODY
)" \
"quality-remediation,autopilot,operational,p0,area:backend" "$P0" "$S" "$BACKEND"

ensure_issue \
"QA3 · Python Core/CLI Sonar Hotspots" \
"$(cat <<'BODY'
## Context

The remaining non-test Sonar backlog is concentrated in Python core/CLI hotspots:

- `src/voiceforge/main.py`
- `src/voiceforge/core/daemon.py`
- `src/voiceforge/cli/status_helpers.py`
- `src/voiceforge/cli/setup.py`
- `src/voiceforge/cli/meeting.py`
- `src/voiceforge/cli/digest.py`
- `src/voiceforge/core/pipeline.py`
- `src/voiceforge/core/config.py`
- `src/voiceforge/llm/router.py`
- `src/voiceforge/calendar/caldav_poll.py`

## Scope

- Reduce cognitive complexity hotspots
- Extract duplicated literals/constants where useful
- Keep behaviour stable via targeted regression tests

## Acceptance Criteria

- [ ] Critical/high-value Python source hotspots are materially reduced in Sonar
- [ ] Main behavioural flows stay covered by targeted tests
- [ ] No drift in CLI/API contracts

## Notes

Focus on real maintainability wins, not mechanical “fix all warnings” churn.
BODY
)" \
"quality-remediation,autopilot,operational,p1,area:backend" "$P1" "$L" "$BACKEND"

ensure_issue \
"QA4 · Test Suite Sonar Cleanup" \
"$(cat <<'BODY'
## Context

Sonar backlog is dominated by test-only findings:

- empty stub methods without comment
- float equality checks
- constant boolean assertions
- async functions with no async behaviour
- a few type-mismatch smells in test helpers

Representative files:

- `tests/test_daemon_batch116.py`
- `tests/test_llm_router_batch115.py`
- `tests/test_coverage_hotspots_batch99.py`
- `tests/test_meeting_mode.py`
- `tests/test_post_listen.py`
- `tests/test_cli_snapshots.py`
- `tests/test_web_status_export_action_items.py`

## Scope

- Clean up test-only Sonar issues while preserving readability and intent
- Prefer small helper comments, approx checks and simpler assertions over noisy rewrites

## Acceptance Criteria

- [ ] Test-only Sonar backlog is materially reduced
- [ ] Coverage and test behaviour remain intact
- [ ] No production-code behaviour changes are hidden inside test cleanup
BODY
)" \
"quality-remediation,autopilot,operational,p1,area:testing" "$P1" "$L" "$TESTING"

ensure_issue \
"QA5 · DevOps & Utility Script Sonar Cleanup" \
"$(cat <<'BODY'
## Context

Script-level Sonar debt is concentrated in:

- `scripts/bootstrap.sh`
- `scripts/create_productization_issues.sh`
- `scripts/check_docs_consistency.py`
- `scripts/preflight_repo.sh`
- `scripts/dependabot_dismiss_moderate.py`

## Scope

- Clean up shell-style issues (`[[`, merged conditionals, explicit returns where sensible)
- Reduce duplicated literals / complexity in repo utility scripts
- Keep scripts executable and idempotent

## Acceptance Criteria

- [ ] DevOps/script Sonar backlog is materially reduced
- [ ] Scripts still work on the current repo/toolbox setup
- [ ] Docs and script contracts remain aligned
BODY
)" \
"quality-remediation,autopilot,operational,p1,area:devops" "$P1" "$M" "$DEVOPS"

ensure_issue \
"QA6 · Desktop Sonar Cleanup" \
"$(cat <<'BODY'
## Context

Remaining desktop/frontend Sonar issues are concentrated in:

- `desktop/src/main.js`
- `desktop/src/platform.js`
- `desktop/e2e/helpers/desktopHarness.js`
- `desktop/e2e-native/specs/native-smoke.e2e.js`

## Scope

- Reduce real frontend/e2e maintainability debt
- Avoid cosmetic churn that would destabilize the desktop track

## Acceptance Criteria

- [ ] Desktop Sonar backlog is materially reduced
- [ ] Desktop build and relevant e2e/smoke paths still pass
- [ ] No product-scope expansion beyond cleanup
BODY
)" \
"quality-remediation,autopilot,operational,p2,area:frontend" "$P2" "$M" "$FRONTEND"

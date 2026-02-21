# Repo Governance (alpha0.1)

## Main Branch Ruleset

Target: `main`

Required policies:
1. No direct pushes.
2. Require pull request before merge.
3. Require up-to-date branch before merge.
4. Require status checks:
   - `quality (3.12)`
   - `quality (3.13)`
   - `cli-contract`
   - `db-migrations`
   - `e2e-smoke`
5. Require linear history.
6. Restrict force pushes and deletions.

`scripts/apply_main_ruleset.sh` can apply these settings via GitHub API (requires authenticated `gh`).

## Alpha0.1 Milestone Planning

Milestone: `alpha0.1-hardening`

Automation helper:
- `scripts/create_alpha_milestone_issues.sh` (requires authenticated `gh`)

Priority issue set (10-15):
1. Protect `main` with ruleset and required checks
2. CI matrix on Python 3.12 and 3.13
3. Dedicated CLI contract CI check
4. DB migration tests (clean + existing DB)
5. End-to-end smoke in CI (listen/analyze/history)
6. Weekly security/dependency scheduled workflow
7. Draft release notes automation
8. SBOM artifact on release
9. Config/env contract documentation
10. Doctor command/script for environment diagnostics
11. Bootstrap installs pre-commit hooks
12. Rollback runbook for failed alpha release

## SonarCloud (non-blocking bootstrap)

1. Add `sonar-project.properties` to repo root.
2. Add workflow `.github/workflows/sonar.yml`.
3. Configure repository secret `SONAR_TOKEN`.
4. Run SonarCloud as non-blocking initially.
5. Move to required check only after stable baseline.

Manual gate visibility:
- `./scripts/check_sonar_status.sh` polls GitHub check-runs for `SonarCloud Code Analysis`.
- Use `./scripts/check_sonar_status.sh --required` before release tagging on `main`.

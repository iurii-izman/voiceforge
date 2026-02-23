# Repo Governance (alpha0.1)

## Main Branch Ruleset

Target: `main`

Required policies:
1. No direct pushes.
2. Require pull request before merge.
3. Solo mode: pull request approval count is `0` (status checks remain mandatory).
4. Require up-to-date branch before merge.
5. Require status checks:
   - `quality (3.12)`
   - `quality (3.13)`
   - `cli-contract`
   - `db-migrations`
   - `e2e-smoke`
6. Require linear history.
7. Restrict force pushes and deletions.

`scripts/apply_main_ruleset.sh` can apply these settings via GitHub API (requires authenticated `gh`).
`scripts/check_repo_governance.sh` validates active ruleset and required checks.

## Порядок на GitHub (ветки и PR)

- После мержа PR: удалить ветку в GitHub (кнопка "Delete branch" на странице PR или `gh pr merge 23 --delete-branch`).
- Локально: `git fetch --prune` и удалить локальные ветки слитых фич (`git branch -d feat/...`).
- Активная разработка — в feature-ветках; мерж в `main` только через PR при зелёных required checks (Sonar не блокирует, см. раздел SonarCloud).

## Security Settings Baseline

Repository-level security baseline:
1. Dependabot alerts endpoint enabled.
2. Dependabot security updates enabled.
3. Secret scanning enabled.
4. Secret scanning push protection enabled.

Verification command:
- `./scripts/check_repo_governance.sh`

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

## SonarCloud (только справочно)

Текущий план SonarCloud не позволяет назначить проекту Quality Gate иной, чем **Sonar way (Default)** — менять gate нельзя.

- Скан в CI включён (workflow `sonar.yml`, `sonar-project.properties`), отчёт доступен в [SonarCloud](https://sonarcloud.io) для просмотра.
- **Используем Sonar только как справочную информацию**: не блокируем merge по чеку, не требуем зелёный gate перед релизом. На поздних этапах при необходимости можно снова ввести проверку (`check_sonar_status.sh --required` в release runbook).
- Список ключей keyring (в т.ч. `sonar_token`): `docs/runbooks/keyring-keys-reference.md`.

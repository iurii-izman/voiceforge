# Repo Governance (alpha0.1)

## Main Branch Ruleset — минимальный набор

Target: `main`. Для простоты включены только необходимые правила:

1. **deletion** — запрет удаления ветки `main`
2. **non_fast_forward** — запрет force-push (только fast-forward)
3. **required_linear_history** — линейная история

Прямой пуш в `main` разрешён. Никаких обязательных PR и status checks.

### Полный набор (опционально, на более поздних этапах)

Когда понадобится обязательный PR и зелёные CI-чеки перед мержем:

- **Включить:** `./scripts/ruleset_enforcement.sh require-pr` — применяется `.github/rulesets/main-protection.json` (добавляются `pull_request` и `required_status_checks`).
- **Вернуть минимальный:** `./scripts/ruleset_enforcement.sh allow-direct-push` — снова только три правила выше.

`scripts/apply_main_ruleset.sh` — применить/обновить полный ruleset из JSON.
`scripts/check_repo_governance.sh` — проверка полного набора (при require-pr); при минимальном наборе часть проверок не выполняется.

## Порядок на GitHub

- На remote — по возможности только `main`; после мержа PR удалять ветку (`gh pr merge N --delete-branch`).
- Локально: `git fetch --prune`, при необходимости `git branch -d <ветка>`.

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
- **Список issues локально:** `uv run python scripts/sonar_fetch_issues.py` (токен из keyring `voiceforge/sonar_token`). Вывод: файл:строка [severity] правило | сообщение; опция `--json` — полный JSON.
- **Используем Sonar только как справочную информацию**: не блокируем merge по чеку, не требуем зелёный gate перед релизом. На поздних этапах при необходимости можно снова ввести проверку (`check_sonar_status.sh --required` в release runbook).
- Список ключей keyring (в т.ч. `sonar_token`): `docs/runbooks/keyring-keys-reference.md`.

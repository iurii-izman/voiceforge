# Репозиторий и Git (объединённый runbook)

Единый документ: правила main, security baseline, SonarCloud; коммиты, ветки, теги, issues, GitHub Project. Объединяет бывшие repo-governance.md и git-github-practices.md. Агент (Cursor) следует этим правилам.

---

## 1. Main branch и правила репозитория

**Минимальный ruleset (target: main):**
1. **deletion** — запрет удаления ветки main
2. **non_fast_forward** — запрет force-push (только fast-forward)
3. **required_linear_history** — линейная история

Прямой пуш в main разрешён. Обязательные PR и status checks не включены.

**Расширенный ruleset (опционально):** `./scripts/ruleset_enforcement.sh require-pr` (добавляются pull_request и required_status_checks). Вернуть минимальный: `./scripts/ruleset_enforcement.sh allow-direct-push`. Скрипты: `apply_main_ruleset.sh`, `check_repo_governance.sh`.

**Порядок на GitHub:** на remote по возможности только main; после мержа PR удалять ветку (`gh pr merge N --delete-branch`). Локально: `git fetch --prune`.

**Security baseline:** Dependabot alerts и security updates включены; secret scanning и push protection включены. Проверка: `./scripts/check_repo_governance.sh`.

**Alpha0.1 milestone:** см. [release-and-quality.md](release-and-quality.md) (раздел 4). Helper: `scripts/create_alpha_milestone_issues.sh` (нужен gh auth).

**SonarCloud:** Quality Gate — только Sonar way (Default). Скан в CI (sonar.yml); отчёт в SonarCloud. Локально: `uv run python scripts/sonar_fetch_issues.py` (токен keyring `voiceforge/sonar_token`). Используем как справочную информацию: не блокируем merge. Порядок при множестве анализов: [sonar-pr-cleanup.md](sonar-pr-cleanup.md).

---

## 2. Коммиты (Conventional Commits)

- **Формат:** `type(scope): краткое описание` (строчными, без точки в конце). Опционально тело и `Closes #N`.
- **Типы:** feat, fix, docs, chore, refactor, test, ci.
- **Примеры:** `feat(caldav): add calendar poll`, `fix(web): Content-Type constant`, `docs(runbooks): add X`.
- **Связь с issue:** в теле или в строке: `Closes #26` или `Refs #27`.

---

## 3. Ветки и PR

Работа по умолчанию в main. Ветки для фич: `feat/short-name`, `fix/short-name`. После мержа: `gh pr merge N --delete-branch`; локально `git fetch --prune`. Правила main — раздел 1 выше.

---

## 4. Теги

- **Формат:** `v<major>.<minor>.<patch>-<prerelease>` (напр. `v0.2.0-alpha.2`). SemVer; альфа — суффикс `-alpha.N`.
- Только аннотированные: `git tag -a v0.2.0-alpha.2 -m "VoiceForge alpha2: ..."`. Пуш: `git push origin v0.2.0-alpha.2`.
- Когда ставить: по [release-and-quality.md](release-and-quality.md) после чеклиста и CHANGELOG/версии.

---

## 5. GitHub Issues и Project

- Одна задача — один issue. В описании: ссылки на runbook/ADR, критерии готовности.
- **Labels:** roadmap, docs, feat, fix, chore, p0/p1/p2. При создании проставлять.
- Закрытие: коммит с `Closes #N` на default branch закрывает issue.
- **Доска:** [VoiceForge Board](https://github.com/users/iurii-izman/projects/1). Status: Todo → In Progress → Done. По завершении (`Closes #N`): перенести в Done через `gh project item-edit`. При старте задачи — в In Progress.

---

## Ссылки

- Релизы и качество: [release-and-quality.md](release-and-quality.md)
- Планирование и канбан: [planning.md](planning.md)
- Ключи keyring: [keyring-keys-reference.md](keyring-keys-reference.md)

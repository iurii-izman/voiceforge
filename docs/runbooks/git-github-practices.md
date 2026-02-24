# Git и GitHub: практики VoiceForge

Единый runbook по современному ведению репозитория: коммиты, теги, issues, Projects, labels. Агент (Cursor) следует этим правилам. Копия правила для Cursor: можно создать `.cursor/rules/git-github-practices.mdc` с тем же содержанием (в репо `.cursor/` в gitignore).

---

## Коммиты (Conventional Commits)

- **Формат:** `type(scope): краткое описание` (строчными, без точки в конце). Опционально тело и `Closes #N`.
- **Типы:** `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`.
- **Примеры:**
  - `feat(caldav): add calendar poll from keyring caldav_*`
  - `fix(web): constant for Content-Type to fix S1192`
  - `docs(runbooks): add git-github-practices.md`
  - `chore(deps): bump ruff in pre-commit`
- **Связь с issue:** в теле или в одной строке: `Closes #26` или `Refs #27`. Полное выполнение — `Closes #N`.

---

## Ветки и PR

- По умолчанию работа в `main`. Ветки для фич: `feat/short-name`, `fix/short-name`.
- После мержа PR: `gh pr merge N --delete-branch`; локально `git fetch --prune`. Правила ветки main: `docs/runbooks/repo-governance.md`.

---

## Теги

- **Формат:** `v<major>.<minor>.<patch>-<prerelease>` (например `v0.2.0-alpha.1`). SemVer; альфа — суффикс `-alpha.N`.
- Только аннотированные: `git tag -a v0.2.0-alpha.1 -m "VoiceForge alpha2: ..."`. Пуш: `git push origin v0.2.0-alpha.1`.
- Когда ставить: по [release.md](release.md) после чеклиста и обновления CHANGELOG/версии.

---

## GitHub Issues

- Одна задача — один issue. В описании: ссылки на runbook/ADR, критерии готовности.
- **Labels:** `roadmap`, `docs`, `feat`, `fix`, `chore`, `p0`/`p1`/`p2`. При создании issue проставлять подходящие.
- Закрытие: коммит с `Closes #N` на default branch закрывает issue.

---

## GitHub Project (канбан)

- Доска: [VoiceForge Board](https://github.com/users/iurii-izman/projects/1). Status: Todo → In Progress → Done.
- По завершении задачи (`Closes #N`): перенести карточку в **Done** через `gh project item-edit` (field Status, option Done).
- При старте задачи по issue: перевести в **In Progress**.

---

## Ссылки

- [release.md](release.md) — релизы и теги
- [repo-governance.md](repo-governance.md) — правила main, security
- [planning-and-tools.md](planning-and-tools.md), [backlog.md](backlog.md) — план и Project

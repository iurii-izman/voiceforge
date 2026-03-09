# AI Tooling Setup and Source of Truth

**Обновлено:** 2026-03-09.

Этот runbook фиксирует, где находится источник истины для `Cursor`, `Codex`, `Claude`, `GitHub CLI` и `Sonar`, а что остаётся локальной машинной настройкой. Цель: не держать расходящиеся инструкции в нескольких местах.

---

## 1. Источник истины в репозитории

Обновлять в первую очередь эти файлы:

1. [../../AGENTS.md](../../AGENTS.md) — короткий контракт для Codex/Cursor/Claude.
2. [agent-context.md](agent-context.md) — полный рабочий контекст агента и конец сессии.
3. [next-iteration-focus.md](next-iteration-focus.md) — следующий шаг и handoff.
4. [phase-e-decision-log.md](phase-e-decision-log.md) — scope guard и решения E19-E21.
5. [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) — execution order и wave-логика.
6. [planning.md](planning.md) — GitHub Project, labels, board workflow.
7. [cursor.md](cursor.md) — режим Cursor, batching, prompts.
8. [repo-and-git-governance.md](repo-and-git-governance.md) — Git/GitHub/Sonar/governance.
9. [../DOCS-INDEX.md](../DOCS-INDEX.md) — индекс актуальных документов.

Если локальные настройки агента спорят с этим списком, править нужно сначала документы выше, а не локальные prompt-файлы.

---

## 2. Что хранится в git

Tracked и обязательные артефакты:

- [../../AGENTS.md](../../AGENTS.md)
- [../../.cursorignore](../../.cursorignore)
- [agent-session-handoff-rule.md](agent-session-handoff-rule.md)
- [git-github-practices-rule.md](git-github-practices-rule.md)

Репозиторий **не требует** tracked `.codex/` или `.claude/` конфигов. Для Codex и Claude источником истины остаются `AGENTS.md` и runbooks.

---

## 3. Что остаётся локальной настройкой машины

Локально и вне git:

- `keyring` сервиса `voiceforge` для всех секретов
- локальный `.cursor/` с prompt/rules, если он используется IDE
- `gh auth` и scope `project`
- Sonar token в keyring (`voiceforge/sonar_token`)
- при наличии: `.claude/`, `.codex/`, IDE-local preferences

Рабочий минимум:

```bash
uv sync --extra all
./scripts/bootstrap.sh
./scripts/preflight_repo.sh --with-tests
gh auth refresh -s project
```

Если локальный агент запускается в среде без keyring, секреты копируются не в репозиторий, а в provider-specific secret storage (`Cursor My Secrets`, local env store и т.п.).

---

## 4. Выравнивание Cursor / Codex / Claude

### Cursor

- использует tracked `.cursor/` правила и [cursor.md](cursor.md);
- для нового чата получает контекст через [agent-context.md](agent-context.md) и [next-iteration-focus.md](next-iteration-focus.md);
- не должен иметь отдельный “тайный” prompt, который переопределяет `phase-e-decision-log.md`.

### Codex

- читает [../../AGENTS.md](../../AGENTS.md);
- продолжает работу по тем же runbook’ам;
- repo-local `.codex/` сейчас **не нужен**.

### Claude

- должен следовать тем же правилам из [../../AGENTS.md](../../AGENTS.md) и [agent-context.md](agent-context.md);
- legacy alignment notes вынесены в архив: [../archive/plans/claude-proposal-alignment.md](../archive/plans/claude-proposal-alignment.md).

### Sonar / GitHub

- SonarCloud остаётся внешним quality signal, а не отдельным планом развития;
- GitHub Project и labels должны совпадать с [planning.md](planning.md) и [phase-e-decision-log.md](phase-e-decision-log.md).

---

## 5. Операционная дисциплина

Перед крупной итерацией или cleanup-сессией:

```bash
./scripts/preflight_repo.sh --with-tests
```

Что должно быть согласовано:

- репозиторий чистый;
- docs links и source-of-truth ссылки не дрейфуют;
- release metadata согласованы;
- GitHub governance baseline проходит;
- `next-iteration-focus.md` указывает на реальный следующий блок.

---

## 6. Статус на 2026-03-09

Текущее состояние считается корректным:

- primary source of truth выровнен на `AGENTS.md` + runbooks;
- tracked Cursor rules синхронизированы с Git/GitHub практиками и session handoff;
- отдельный repo-local `.codex/` не нужен;
- отдельный repo-local `.claude/` не требуется;
- board policy зафиксирован в [phase-e-decision-log.md](phase-e-decision-log.md) и [planning.md](planning.md).

Если позже появится новый assistant-specific config в репозитории, его нужно добавить в этот документ и в [../DOCS-INDEX.md](../DOCS-INDEX.md).

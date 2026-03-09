# Планирование и инструменты (VoiceForge)

Раньше: **backlog.md** и **planning-and-tools.md** объединены в этот файл.

---

## Единый источник текущих задач

- **Канбан и приоритеты:** [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1), рабочее представление для итераций: [View 1](https://github.com/users/iurii-izman/projects/1/views/1).
- **Единый бэклог (ваши решения и ручные шаги):** [backlog-and-actions.md](../plans/backlog-and-actions.md) — блоки A–E; issues #82–86 на доске.
- **Задачи Phase A–D (issues #55–73):** [audit/audit.md](../audit/audit.md) — статус W1–W20, маппинг на issues.
- **Следующий шаг и фокус итерации:** [next-iteration-focus.md](next-iteration-focus.md) — обновляет агент в конце сессии.
- **Границы scope для Phase E:** [phase-e-decision-log.md](phase-e-decision-log.md) — зафиксированные решения по E19-E21.
- **История (что сделано):** [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).
- **Приоритет фич (roadmap 1–19):** [plans.md](../plans.md) — порядок внедрения, что сделано; детали по задачам — [audit/audit.md](../audit/audit.md).

При выполнении задачи: коммит с `Closes #N`; на доске перевести карточку в Done. См. [repo-and-git-governance.md](repo-and-git-governance.md).

---

## Режим Cursor: max throughput без потери качества

- **Источник очереди работ:** сначала `next-iteration-focus.md`, затем [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1), затем `plans.md` / `audit.md`.
- **Правило batching:** брать **1 главный issue/block** и максимум **2 tightly-coupled подзадачи** только если они лежат в том же subsystem, тех же файлах или закрываются тем же набором тестов.
- **Хорошие batches:** bugfix + regression tests + contract docs; hotspot refactor + coverage; version sync + packaging docs + release smoke.
- **Плохие batches:** desktop packaging + RAG parser + calendar; security-only + unrelated UI polish; большие cross-cutting переделки без общей verification loop.
- **После старта по issue:** перевести карточку в `In Progress`. После `Closes #N` и зелёных проверок — в `Done`.
- **Подробный режим Cursor и готовые prompts:** [cursor.md](cursor.md), [next-iteration-focus.md](next-iteration-focus.md), [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md), [phase-e-decision-log.md](phase-e-decision-log.md).

---

## Вариант 1: Markdown в репо (backlog / план)

Один файл в репо (например `docs/runbooks/backlog.md` или `docs/PLAN.md`) — список задач с чекбоксами. Агент читает и правит по просьбе; история в git.

**Плюсы:** агент в контексте, версионирование. **Минусы:** нет drag-and-drop, смена порядка — правка текста или команда агенту.

Пример структуры: разделы «В работе», «Далее (приоритет по порядку)», «Сделано (история в docs/history/)». В чате: «добавь в backlog задачу X», «отметь CalDAV сделанным» — агент правит файл и при необходимости next-iteration-focus.

---

## Вариант 2: GitHub Projects (канбан по issues)

Доска с колонками Todo / In progress / Done; карточки — issues. Агент может управлять канбаном через GitHub CLI при scope `project`.

**Включить управление Projects агентом (один раз):**
```bash
gh auth refresh -s project
```

После этого агент может: создавать issue, добавлять в проект (`gh project item-add`), переводить карточку в другую колонку (`gh project item-edit` с полем Status). Примеры: «создай issue на CalDAV и добавь в проект», «перенеси #17 в Done».

**Текущий проект:** [GitHub Project #1](https://github.com/users/iurii-izman/projects/1) — колонки Status: Todo, In Progress, Done. Рабочий вид: [View 1](https://github.com/users/iurii-izman/projects/1/views/1). На доске остаётся история (`#55-#73`, `#82-#86`, `#96-#123`), но практический execution order для новых сессий задают `next-iteration-focus.md`, `PROJECT-STATUS-SUMMARY.md` и `phase-e-decision-log.md`. Поля: Phase, Priority, Effort, Area — для визуализации и фильтрации.

**Обновление доски (обязательно для агента):**
- При старте работы по issue — перевести карточку в **In Progress**.
- При коммите с `Closes #N` — перевести карточку в **Done**.
- Команда (нужен `gh auth refresh -s project`): получить item ID через `gh project item-list 1 --owner iurii-izman --limit 100 --format json`, затем:
  - В In Progress: `gh project item-edit --project-id PVT_kwHODvfgWM4BQC-Z --id <ITEM_ID> --field-id PVTSSF_lAHODvfgWM4BQC-Zzg-R4aU --single-select-option-id 47fc9ee4`
  - В Done: то же, но `--single-select-option-id 98236657`

---

## Связь с документами

- **Фокус и «следующий шаг»:** [next-iteration-focus.md](next-iteration-focus.md).
- **Бэклог (ваши решения, ручные шаги):** [backlog-and-actions.md](../plans/backlog-and-actions.md) — блоки A–E, рекомендации по работе с доской.
- **Всё сделанное:** [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).
- **Приоритет фич:** [plans.md](../plans.md).

Индекс документации: [DOCS-INDEX.md](../DOCS-INDEX.md).

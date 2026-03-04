# Планирование и инструменты (VoiceForge)

Раньше: **backlog.md** и **planning-and-tools.md** объединены в этот файл.

---

## Единый источник текущих задач

- **Канбан и приоритеты:** [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).
- **Задачи Phase A–D (issues #55–73):** [audit/audit.md](../audit/audit.md) — статус W1–W20, маппинг на issues.
- **Следующий шаг и фокус итерации:** [next-iteration-focus.md](next-iteration-focus.md) — обновляет агент в конце сессии.
- **История (что сделано):** [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).
- **Приоритет фич (roadmap 1–20):** [plans.md](../plans.md) — порядок внедрения, что сделано; детали по задачам — [audit/audit.md](../audit/audit.md).

При выполнении задачи: коммит с `Closes #N`; на доске перевести карточку в Done. См. [git-github-practices.md](git-github-practices.md).

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

**Текущий проект:** [GitHub Project #1](https://github.com/users/iurii-izman/projects/1) — колонки Status: Todo, In Progress, Done. Открытые задачи — issues #26–30 и далее (#55–73 по audit map).

---

## Связь с документами

- **Фокус и «следующий шаг»:** [next-iteration-focus.md](next-iteration-focus.md).
- **Всё сделанное:** [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).
- **Приоритет фич:** [plans.md](../plans.md).

Индекс документации: [DOCS-INDEX.md](../DOCS-INDEX.md).

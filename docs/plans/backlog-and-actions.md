# Единый бэклог и действия (требуют вашего участия или решения)

Один список всего отложенного и ручного: подтверждения, решения по приоритетам, ручные шаги, GitHub. Используется для трекинга в [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

**Источники:** [next-iteration-focus.md](../runbooks/next-iteration-focus.md), [roadmap-100-blocks.md](roadmap-100-blocks.md), [MANUAL-AND-CANNOT-DO.md](MANUAL-AND-CANNOT-DO.md), [pre-beta-sonar-github.md](../runbooks/pre-beta-sonar-github.md).

---

## Блок A. Подтверждения и разовые действия

| Тема | Что нужно от вас | Статус |
|------|-------------------|--------|
| **#65 CVE** | Пока ничего. Когда в upstream (diskcache/instructor) будет фикс — обновить зависимости, убрать `--ignore-vuln` по [security-and-dependencies.md](../runbooks/security-and-dependencies.md) разд. 4. Dependabot-алерт отклонить: «No fix version yet. See docs/runbooks/security-and-dependencies.md. Revisit when upstream fixes.» или скрипт `uv run python scripts/dependabot_dismiss_moderate.py`. | Ждём upstream |
| **Keyring (HuggingFace)** | Один раз сохранить токен, если ещё не сохранён. Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. Сохранение: `secret-tool store --label='voiceforge huggingface' service voiceforge key huggingface`. | По доке проверено |
| **OTel/Jaeger** | Запуск контейнера (podman/docker), открытие http://localhost:16686, при необходимости выставить переменные в сессии. Агент только подсказывает команды. | По желанию |
| **#66 Async** | Ничего подтверждать не нужно. | — |

*Блок A подтверждён 2026-03-07 (#82).*

---

## Блок B. Решения по приоритетам (roadmap — отложенные блоки)

Из [roadmap-100-blocks.md](roadmap-100-blocks.md), раздел «Не реализовано». Нужен **ваш выбор**: делать ли, в каком объёме и в каком порядке.

| # | Блок | Зачем ваше решение |
|---|------|---------------------|
| 35 | Тёмная тема трея | Нужны ассеты и правки в Rust; решить, делать ли в ближайшем релизе. |
| 44 | История буфера обмена | Локальная история копирований в UI; объём и UX — за вами. |
| 46 | Слайд-панель настроек | Опция «настройки в выдвижной панели» — дизайн и приоритет. |
| 49 | Виджет «Последний анализ» | Карточка с summary на главной; нужен контракт API/данных — ваше решение по формату. |
| 66 | Prompt caching | Зависит от API Claude/провайдеров и бэкенда; решить, подключать ли и когда. |
| 68 | Streaming LLM в UI | Пошаговый вывод; бэкенд + фронт; приоритет и объём — за вами. |
| 71 | Whisper API (OpenAI) | Опция STT через OpenAI; решить, нужна ли и в каком виде. |
| 75 | Поиск по RAG из UI | Поле поиска по документам; API + UI; приоритет и scope. |
| 79 | Создание события из сессии | «Добавить в календарь» после анализа; CalDAV POST; нужен ли сценарий и в каком виде. |

После выбора приоритета блоки можно оформить в issues и добавить на доску; агент может реализовывать по вашей расстановке.

---

## Блок C. Ручные шаги (без вас агент не сделает)

По [MANUAL-AND-CANNOT-DO.md](MANUAL-AND-CANNOT-DO.md).

| Действие | Кто |
|----------|-----|
| **Сборка/запуск десктопа** | `cd desktop && npm run tauri build`, `npm run tauri dev` — у вас на машине; проверка в окне. |
| **Ключи и секреты** | Keyring (в т.ч. CalDAV для виджета «Ближайшие встречи»); агент не видит секреты. |
| **Updater** | Сгенерировать ключи подписи (`npm run tauri signer generate -w ~/.tauri/voiceforge.key`), настроить сервер обновлений, при необходимости CI и `TAURI_SIGNING_PRIVATE_KEY`. См. [desktop-updater.md](../runbooks/desktop-updater.md). |
| **Релизы и распространение** | Создание GitHub Release, загрузка артефактов; при желании — Flatpak/Flathub. |
| **Тестирование с человеком** | E2E в среде с GUI, a11y с реальными пользователями/скринридерами, ручные сценарии (second instance, deep link, автозапуск). |

---

## Блок D. GitHub: ваши решения

| Что | Действие |
|-----|----------|
| **PR #81, #79** | Изменения уже в main. Можно закрыть PR с комментарием «Applied in main». |
| **Issue #65** | Оставить открытым до фикса upstream; при желании отклонить Dependabot с комментарием из runbook. |
| **Issue #50** (macOS/WSL2) | В backlog (p2). Решить: оставить в бэклоге или снять/переформулировать. |
| **verify_pr и bandit** | Сейчас падает на bandit (Low/Medium). Решить: добиваться полного зелёного verify_pr или оставить как есть. |

---

## Блок E. Опционально: что поручить агенту

- Привести в порядок **bandit** (если решите, что verify_pr должен быть полностью зелёным).
- Доработать **оставшиеся замечания Sonar** по приоритету, который вы зададите.
- Реализовать любой из **отложенных блоков** B (35, 44, 46, 49, 66, 68, 71, 75, 79) после того как вы определите приоритет и scope.

---

## Работа с GitHub Project (доска)

**Проект:** [VoiceForge Board](https://github.com/users/iurii-izman/projects/1). Поля: **Status** (Todo → In Progress → Done), **Phase**, **Priority**, **Effort**, **Area**.

**Рекомендации для плотного трекинга:**

1. **Один issue — одна задача.** Крупные блоки (например «Решения по приоритетам») можно вести одним issue со ссылкой на этот документ; отдельные фичи (блок 35, 44, …) — отдельными issues с метками и привязкой к проекту.
2. **При старте работы по issue** — перевести карточку в **In Progress** (через веб или `gh project item-edit`).
3. **При коммите с `Closes #N`** — перенести карточку в **Done**.
4. **Агент:** при работе по issue переводит в In Progress; при закрытии — в Done. Нужен scope `project`: `gh auth refresh -s project`. Команды и ID полей — в [planning.md](../runbooks/planning.md).
5. **Раз в итерацию** просматривать доску: что в Todo, что застряло в In Progress, что можно закрыть или переприоритизировать.

Связь с репо: [repo-and-git-governance.md](../runbooks/repo-and-git-governance.md), [planning.md](../runbooks/planning.md).

---

## Промпт для нового чата (решить все задачи бэклога)

Скопируй в начало нового чата:

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, keyring, коммит/пуш в конце сессии). Единый бэклог: @docs/plans/backlog-and-actions.md.

Цель: пройти все блоки A–E и закрыть по максимуму. Доска: [GitHub Project #1](https://github.com/users/iurii-izman/projects/1), issues #82–86.

- Блок A: подтвердить статус CVE #65, keyring, OTel; при необходимости обновить доки или отклонить Dependabot с комментарием из runbook. Закрыть #82 когда всё зафиксировано.
- Блок B: со мной определить приоритет и scope отложенных блоков (35, 44, 46, 49, 66, 68, 71, 75, 79); оформить выбранные в issues и добавить на доску; реализовать по очереди. Закрыть #83 после решений и при необходимости создания под-issues.
- Блок C: напомнить чеклист ручных шагов (сборка, ключи, updater, релиз, тестирование); обновить MANUAL-AND-CANNOT-DO или runbooks по результатам. Закрыть #84 когда ручные пункты выполнены или зафиксированы.
- Блок D: закрыть PR #81 и #79 с комментарием «Applied in main»; зафиксировать решения по #65, #50, verify_pr/bandit в доке или в issue. Закрыть #85.
- Блок E: по моему решению — поручить тебе bandit, Sonar или отложенные блоки; выполнить и закрыть #86.

В конце сессии: тесты, коммит, пуш, обновить next-iteration-focus, перевести закрытые карточки в Done на доске. Начинай с блока A, затем по моим ответам — B, C, D, E.
```

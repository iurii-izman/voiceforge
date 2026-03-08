# Индекс документации (единый знаменатель)

**Назначение:** один источник правды по тому, какой документ за что отвечает и актуален ли он. При изменении кода/фич обновлять соответствующий док и при необходимости этот индекс.

**Обновлено:** 2026-03-08 (deep audit delta, max-autopilot batching, new next-step prompt)

---

## Источники истины (минимум для работы)


| Тема                                                                        | Документ                                                                                                                                     |
| --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Контекст агента, правила, конец сессии                                      | [runbooks/agent-context.md](runbooks/agent-context.md)                                                                                       |
| Следующий шаг / фокус итерации                                              | [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md)                                                                         |
| Текущие задачи и аудит (Phase A–D, W1–W20)                                  | [audit/audit.md](audit/audit.md)                                                                                                             |
| Планы и приоритеты (roadmap 1–19, Phase A–D Steps 1–19, оставшееся до 100%) | [plans.md](plans.md)                                                                                                                         |
| Аудит: статус, оставшееся до 100%, архив                                    | [audit/audit.md](audit/audit.md); снимки — [archive/audit/](archive/audit/)                                                                  |
| Конфиг, env, keyring                                                        | [runbooks/config-env-contract.md](runbooks/config-env-contract.md), [runbooks/keyring-keys-reference.md](runbooks/keyring-keys-reference.md) |
| Установка, сборка десктопа                                                  | [runbooks/installation-guide.md](runbooks/installation-guide.md), [runbooks/desktop-build-deps.md](runbooks/desktop-build-deps.md)           |
| Управление документацией                                                    | [runbooks/doc-governance.md](runbooks/doc-governance.md)                                                                                     |
| Инструкции Cursor Agent (автозагрузка)                                      | [AGENTS.md](../AGENTS.md) (корень репо)                                                                                                      |
| Тюнинг Cursor (промпты, правила, OOM, max-autopilot batching)               | [runbooks/cursor.md](runbooks/cursor.md)                                                                                                     |


---

## По сценариям (блок 94)


| Сценарий                            | Документы                                                                                                                                                                                                                                                                                                                                                    |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Начало работы**                   | [first-meeting-5min.md](first-meeting-5min.md), [runbooks/quickstart.md](runbooks/quickstart.md), [runbooks/installation-guide.md](runbooks/installation-guide.md)                                                                                                                                                                                           |
| **Сборка и установка**              | [runbooks/desktop-build-deps.md](runbooks/desktop-build-deps.md), [runbooks/offline-package.md](runbooks/offline-package.md), [runbooks/desktop-updater.md](runbooks/desktop-updater.md), [runbooks/desktop-gui-testing.md](runbooks/desktop-gui-testing.md) (тесты GUI), [runbooks/desktop-release-gate-matrix.md](runbooks/desktop-release-gate-matrix.md) |
| **Конфигурация и ключи**            | [runbooks/config-env-contract.md](runbooks/config-env-contract.md), [runbooks/keyring-keys-reference.md](runbooks/keyring-keys-reference.md)                                                                                                                                                                                                                 |
| **Разработка и агент**              | [AGENTS.md](../AGENTS.md), [runbooks/agent-context.md](runbooks/agent-context.md), [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md), [runbooks/cursor.md](runbooks/cursor.md), [runbooks/PROJECT-STATUS-SUMMARY.md](runbooks/PROJECT-STATUS-SUMMARY.md), [architecture/README.md](architecture/README.md)                                |
| **Релиз и качество**                | [runbooks/release-and-quality.md](runbooks/release-and-quality.md), [runbooks/pre-beta-sonar-github.md](runbooks/pre-beta-sonar-github.md), [runbooks/repo-and-git-governance.md](runbooks/repo-and-git-governance.md), [audit/audit.md](audit/audit.md)                                                                                                     |
| **Безопасность и зависимости**      | [runbooks/security-and-dependencies.md](runbooks/security-and-dependencies.md)                                                                                                                                                                                                                                                                               |
| **Фичи (календарь, RAG, Telegram)** | [runbooks/calendar-integration.md](runbooks/calendar-integration.md), [runbooks/rag-formats.md](runbooks/rag-formats.md), [runbooks/telegram-bot-setup.md](runbooks/telegram-bot-setup.md)                                                                                                                                                                   |


---

## Вся документация по каталогам

### Корень репо


| Файл      | Роль                                                       | Статус   |
| --------- | ---------------------------------------------------------- | -------- |
| AGENTS.md | Инструкции для Cursor Agent (подхватываются автоматически) | Актуален |


### docs/ (корень)


| Файл                                 | Роль                                                                                                          | Статус                           |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| README.md                            | Вход в документацию                                                                                           | Актуален                         |
| DOCS-INDEX.md                        | Этот индекс                                                                                                   | Актуален                         |
| first-meeting-5min.md                | Первая встреча за 5 минут                                                                                     | Актуален                         |
| plans.md                             | Единый план: roadmap 1–19, Phase A–D (Steps 1–19), оставшееся до 100%                                         | Актуален                         |
| roadmap-priority.md                  | Заглушка → [plans.md](plans.md)                                                                               | Объединён в plans.md             |
| PROJECT_AUDIT_AND_ROADMAP.md         | Заглушка → [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md) | Архив                            |
| grafana-voiceforge-dashboard.json    | Дашборд Grafana                                                                                               | Актуален                         |
| development-plan-post-audit-2026.md  | Заглушка → архив                                                                                              | [archive/plans/](archive/plans/) |
| desktop-tauri-implementation-plan.md | Заглушка → архив                                                                                              | [archive/plans/](archive/plans/) |


### docs/archive/


| Файл/каталог                          | Роль                                                                                                                    |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| [README.md](archive/README.md)        | Когда и что архивировать; правило для агента                                                                            |
| archive/plans/                        | Выполненные/устаревшие планы (development-plan, desktop-tauri, claude-proposal-alignment)                               |
| archive/adr/                          | Superseded ADR (0002-archive-first-cleanup)                                                                             |
| archive/runbooks/                     | Устаревшие/объёмные runbook’и (voiceforge-cursor-tz-2026)                                                               |
| archive/audit/                        | Снимки аудита (PROJECT_AUDIT_AND_ROADMAP_2026, REMAINING_AND_PLAN, FULL_AUDIT, audit-to-github-map, audit-2026-03-full) |
| archive/docs-consolidation-2026-03.md | Отчёт о консолидации доков (объединение runbooks и аудита 2026-03)                                                      |


### docs/audit/


| Файл                         | Роль                                                       | Статус   |
| ---------------------------- | ---------------------------------------------------------- | -------- |
| [audit.md](audit/audit.md)   | Единый аудит: статус W1–W20, Phase A–D, оставшееся до 100% | Актуален |
| [README.md](audit/README.md) | Вход в аудит, ссылки на архив                              | Актуален |


### docs/history/


| Файл                        | Роль                            | Статус    |
| --------------------------- | ------------------------------- | --------- |
| closed-plans-and-roadmap.md | Что сделано по roadmap и планам | Справочно |


### docs/runbooks/


| Файл                                                          | Роль                                                                                    | Статус                           |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------- |
| agent-context.md                                              | Контекст агента, чеклист конца сессии, max-autopilot mode                               | Актуален                         |
| next-iteration-focus.md                                       | Следующий шаг; обновляет агент; готовые prompts                                         | Актуален                         |
| doc-governance.md                                             | Порядок в доках: архив, источники правды, после итерации                                | Актуален                         |
| config-env-contract.md, keyring-keys-reference.md             | Конфиг и ключи                                                                          | Актуален                         |
| installation-guide.md, desktop-build-deps.md, bootstrap.md    | Установка и сборка                                                                      | Актуален                         |
| desktop-gui-testing.md                                        | Тестирование GUI десктопа: mocked autopilot, native smoke, a11y, visual regression      | Актуален                         |
| desktop-release-gate-matrix.md                                | Release gate matrix для desktop: automated vs native vs manual proof                    | Актуален                         |
| quickstart.md                                                 | Краткий сценарий; полная версия — first-meeting-5min                                    | Актуален                         |
| cli-commands-and-run.md                                       | Все CLI-команды, когда пересобирать, как запускать демон и полный стек (toolbox)        | Актуален                         |
| planning.md                                                   | Канбан, audit map, next-iteration-focus; GitHub Project, gh и batching policy           | Актуален                         |
| security-and-dependencies.md                                  | Безопасность, зависимости, Dependabot (объединённый runbook)                            | Актуален                         |
| telegram-bot-setup.md, pyannote-version.md                    | Фичи                                                                                    | Актуален                         |
| repo-and-git-governance.md                                    | Репо, main, Git, PR, теги, issues, Sonar                                                | Актуален                         |
| release-and-quality.md                                        | Релиз, откат, чеклисты альфа, DoD                                                       | Актуален                         |
| lifecycle-smoke.md                                            | Smoke-шаги для audio/STT и RAG lifecycle (#105, #106)                                  | Актуален                         |
| pre-beta-sonar-github.md                                      | Чеклист Sonar и GitHub перед бета-релизом (PR, issues, порядок)                         | Актуален                         |
| PROJECT-STATUS-SUMMARY.md                                     | Итог по проекту (12 разделов): планы↔код, audit delta, critical path, риски, приоритеты | Актуален                         |
| web-api.md, observability-alerts.md                           | API, мониторинг, трассировка Jaeger (#71)                                               | Актуален                         |
| test-operations.md, sonar-pr-cleanup.md                       | Тесты и CI                                                                              | Актуален                         |
| prompt-management.md, calendar-integration.md, rag-formats.md | Фичи и форматы                                                                          | Актуален                         |
| cursor.md, voiceforge-cursor-tz.md                            | Cursor: настройка, тюнинг, prompts, coherent batching; расширенное ТЗ (архив)           | Актуален / заглушка              |
| claude-proposal-alignment.md                                  | Заглушка → архив                                                                        | [archive/plans/](archive/plans/) |
| git-github-practices-rule.md, agent-session-handoff-rule.md   | Копии для .cursor/rules/                                                                | Актуален                         |
| offline-package.md                                            | Flatpak/AppImage (GA #73): сборка, установка, GA checklist                              | Актуален                         |
| desktop-updater.md                                            | Обновления десктопа (Tauri updater): ключи, endpoints, подпись, CI (блок 92)            | Актуален                         |


### docs/plans/


| Файл                                                                     | Роль                                                                                                                                                                | Статус        |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| [desktop-gui-phase2-10-blocks.md](plans/desktop-gui-phase2-10-blocks.md) | Следующие 10 блоков UI (11–20): горячие клавиши, темы, графики, поиск сессий, закрытие в трей, экспорт, онбординг, клавиатура, компактный режим, виджеты            | Актуален      |
| [roadmap-100-blocks.md](plans/roadmap-100-blocks.md)                     | 100 блоков улучшений по всем направлениям (Desktop 31–50, CLI 51–60, D-Bus 61–65, пайплайн, RAG, календарь, экспорт, тесты, CI, доки, безопасность, i18n, упаковка) | Актуален      |
| [MANUAL-AND-CANNOT-DO.md](plans/MANUAL-AND-CANNOT-DO.md)                 | Что сделать вручную после автопилота и что агент не может сделать сам                                                                                               | Актуален      |
| [backlog-and-actions.md](plans/backlog-and-actions.md)                   | Единый бэклог: подтверждения, решения по приоритетам, ручные шаги, GitHub; блоки A–E; issues #82–86 на доске                                                        | Актуален      |
| [video-meetings-integration.md](plans/video-meetings-integration.md)     | Заглушка: интеграция с видеовстречами (Jitsi/Meet) — roadmap блок 80                                                                                                | Запланировано |


### docs/adr/


| Файл                          | Роль                                      | Статус   |
| ----------------------------- | ----------------------------------------- | -------- |
| README.md                     | Список ADR 0001–0006                      | Актуален |
| 0001–0006                     | Активные решения                          | Актуален |
| 0002-archive-first-cleanup.md | Superseded → [archive/adr/](archive/adr/) | Архив    |


### docs/architecture/


| Файл                   | Роль                                                         | Статус   |
| ---------------------- | ------------------------------------------------------------ | -------- |
| README.md, overview.md | Пайплайн, модули; ключевые решения и ссылки на ADR (блок 93) | Актуален |


### monitoring/ (корень репо)


| Файл                                           | Роль                                                                                                         |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| README.md                                      | Prometheus + Grafana, алерты; см. также [runbooks/observability-alerts.md](runbooks/observability-alerts.md) |
| prometheus.yml, alerts.yml, docker-compose.yml | Конфиги стека                                                                                                |


### docs/en/


| Файл                             | Роль                                                                                                                |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| README.md, first-meeting-5min.md | EN-документация                                                                                                     |
| runbooks/                        | Runbooks (EN): installation-guide, quickstart, bootstrap, desktop-build-deps, dependabot-review, telegram-bot-setup |


---

## Правила модерации

1. **Добавление документа:** внести в индекс с ролью и статусом.
2. **Устаревание:** сменить статус на «Справочно» или перенести в [archive/](archive/) (заглушка в старом месте с ссылкой на архив).
3. **После большой итерации:** обновить актуальные доки (next-iteration-focus, runbooks при изменении поведения); завершённые планы перенести в docs/archive/; обновить этот индекс (см. [runbooks/doc-governance.md](runbooks/doc-governance.md)).

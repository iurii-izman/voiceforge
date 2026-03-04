# Индекс документации (единый знаменатель)

**Назначение:** один источник правды по тому, какой документ за что отвечает и актуален ли он. При изменении кода/фич обновлять соответствующий док и при необходимости этот индекс.

**Обновлено:** 2026-03-04 (архив планов и аудита, cursor.md + planning.md, doc governance)

---

## Источники истины (минимум для работы)

| Тема | Документ |
|------|----------|
| Контекст агента, правила, конец сессии | [runbooks/agent-context.md](runbooks/agent-context.md) |
| Следующий шаг / фокус итерации | [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md) |
| Текущие задачи (Phase A–D, #55–73) | [audit/audit-to-github-map.md](audit/audit-to-github-map.md) |
| Приоритет фич (roadmap 1–20) | [roadmap-priority.md](roadmap-priority.md) |
| Аудит: задачи и 10 блоков усиления | [audit/audit-to-github-map.md](audit/audit-to-github-map.md), [audit/FULL_AUDIT_2026.md](audit/FULL_AUDIT_2026.md); снимок 2026-02-26 — [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md) |
| Конфиг, env, keyring | [runbooks/config-env-contract.md](runbooks/config-env-contract.md), [runbooks/keyring-keys-reference.md](runbooks/keyring-keys-reference.md) |
| Установка, сборка десктопа | [runbooks/installation-guide.md](runbooks/installation-guide.md), [runbooks/desktop-build-deps.md](runbooks/desktop-build-deps.md) |
| Управление документацией | [runbooks/doc-governance.md](runbooks/doc-governance.md) |
| Инструкции Cursor Agent (автозагрузка) | [AGENTS.md](../AGENTS.md) (корень репо) |
| Тюнинг Cursor (промпты, правила, OOM) | [runbooks/cursor.md](runbooks/cursor.md) |

---

## Вся документация по каталогам

### Корень репо

| Файл | Роль | Статус |
|------|------|--------|
| AGENTS.md | Инструкции для Cursor Agent (подхватываются автоматически) | Актуален |

### docs/ (корень)

| Файл | Роль | Статус |
|------|------|--------|
| README.md | Вход в документацию | Актуален |
| DOCS-INDEX.md | Этот индекс | Актуален |
| first-meeting-5min.md | Первая встреча за 5 минут | Актуален |
| roadmap-priority.md | Приоритет фич 1–20 | Актуален |
| PROJECT_AUDIT_AND_ROADMAP.md | Заглушка → [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md) | Архив |
| grafana-voiceforge-dashboard.json | Дашборд Grafana | Актуален |
| development-plan-post-audit-2026.md | Заглушка → архив | [archive/plans/](archive/plans/) |
| desktop-tauri-implementation-plan.md | Заглушка → архив | [archive/plans/](archive/plans/) |

### docs/archive/

| Файл/каталог | Роль |
|--------------|------|
| [README.md](archive/README.md) | Когда и что архивировать; правило для агента |
| archive/plans/ | Выполненные/устаревшие планы (development-plan, desktop-tauri, claude-proposal-alignment) |
| archive/adr/ | Superseded ADR (0002-archive-first-cleanup) |
| archive/runbooks/ | Устаревшие/объёмные runbook’и (voiceforge-cursor-tz-2026) |
| archive/audit/ | Снимки аудита (PROJECT_AUDIT_AND_ROADMAP_2026) |

### docs/audit/

| Файл | Роль | Статус |
|------|------|--------|
| audit-to-github-map.md | Weaknesses → issues #55–73; статус по коду | Актуален |
| FULL_AUDIT_2026.md | Степень реализации по фронтам, 10 блоков усиления | Актуален |

### docs/history/

| Файл | Роль | Статус |
|------|------|--------|
| closed-plans-and-roadmap.md | Что сделано по roadmap и планам | Справочно |

### docs/runbooks/

| Файл | Роль | Статус |
|------|------|--------|
| agent-context.md | Контекст агента, чеклист конца сессии | Актуален |
| next-iteration-focus.md | Следующий шаг; обновляет агент | Актуален |
| doc-governance.md | Порядок в доках: архив, источники правды, после итерации | Актуален |
| config-env-contract.md, keyring-keys-reference.md | Конфиг и ключи | Актуален |
| installation-guide.md, desktop-build-deps.md, bootstrap.md | Установка и сборка | Актуален |
| quickstart.md | Краткий сценарий; полная версия — first-meeting-5min | Актуален |
| planning.md | Канбан, audit map, next-iteration-focus; GitHub Project и gh | Актуален |
| dependencies.md, security.md, dependabot-review.md | Зависимости и безопасность | Актуален |
| telegram-bot-setup.md, pyannote-version.md | Фичи | Актуален |
| repo-governance.md, git-github-practices.md | Git, PR, Sonar | Актуален |
| release.md, rollback-alpha-release.md, alpha2-checklist.md, alpha0.1-dod.md | Релизы | Актуален |
| web-api.md, observability-alerts.md | API и мониторинг | Актуален |
| test-operations.md, sonar-pr-cleanup.md | Тесты и CI | Актуален |
| prompt-management.md, calendar-integration.md, rag-formats.md | Фичи и форматы | Актуален |
| cursor.md, voiceforge-cursor-tz.md | Cursor: настройка, тюнинг; расширенное ТЗ (архив) | Актуален / заглушка |
| claude-proposal-alignment.md | Заглушка → архив | [archive/plans/](archive/plans/) |
| git-github-practices-rule.md, agent-session-handoff-rule.md | Копии для .cursor/rules/ | Актуален |
| offline-package.md | Flatpak/AppImage | Черновик |

### docs/adr/

| Файл | Роль | Статус |
|------|------|--------|
| README.md | Список ADR 0001–0006 | Актуален |
| 0001–0006 | Активные решения | Актуален |
| 0002-archive-first-cleanup.md | Superseded → [archive/adr/](archive/adr/) | Архив |

### docs/architecture/

| Файл | Роль | Статус |
|------|------|--------|
| README.md, overview.md | Пайплайн, модули | Актуален |

### monitoring/ (корень репо)

| Файл | Роль |
|------|------|
| README.md | Prometheus + Grafana, алерты; см. также [runbooks/observability-alerts.md](runbooks/observability-alerts.md) |
| prometheus.yml, alerts.yml, docker-compose.yml | Конфиги стека |

### docs/en/

| Файл | Роль |
|------|------|
| README.md, first-meeting-5min.md | EN-документация |
| runbooks/ | Runbooks (EN): installation-guide, quickstart, bootstrap, desktop-build-deps, dependabot-review, telegram-bot-setup |

---

## Правила модерации

1. **Добавление документа:** внести в индекс с ролью и статусом.
2. **Устаревание:** сменить статус на «Справочно» или перенести в [archive/](archive/) (заглушка в старом месте с ссылкой на архив).
3. **После большой итерации:** обновить актуальные доки (next-iteration-focus, runbooks при изменении поведения); завершённые планы перенести в docs/archive/; обновить этот индекс (см. [runbooks/doc-governance.md](runbooks/doc-governance.md)).

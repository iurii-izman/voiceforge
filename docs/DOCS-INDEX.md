# Индекс документации (единый знаменатель)

**Назначение:** один источник правды по тому, какой документ за что отвечает и актуален ли он. При изменении кода/фич обновлять соответствующий док и при необходимости этот индекс.

**Обновлено:** 2026-02-24 (аудит планов: history/closed-plans-and-roadmap.md, next-iteration-focus только открытые задачи, planning-and-tools.md)

---

## Источники истины (что где искать)

| Тема | Документ | Статус |
|------|----------|--------|
| Контекст агента, правила, конец сессии | [runbooks/agent-context.md](runbooks/agent-context.md) | Актуален |
| Следующий шаг / фокус итерации | [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md) | Обновляет агент; только открытые задачи и план |
| История: что сделано (аудит по коду) | [history/closed-plans-and-roadmap.md](history/closed-plans-and-roadmap.md) | Справочно |
| Правило автопилота (копия для .cursor/rules/) | [runbooks/agent-session-handoff-rule.md](runbooks/agent-session-handoff-rule.md) | Актуален |
| Приоритет фич (roadmap 1–20) | [roadmap-priority.md](roadmap-priority.md) | Актуален |
| Конфиг, env, keyring-имена | [runbooks/config-env-contract.md](runbooks/config-env-contract.md), [runbooks/keyring-keys-reference.md](runbooks/keyring-keys-reference.md) | Актуален |
| Установка и запуск (хост/toolbox, демон) | [runbooks/installation-guide.md](runbooks/installation-guide.md) | Актуален |
| Первая встреча за 5 минут | [first-meeting-5min.md](first-meeting-5min.md) | Актуален |
| Сборка десктопа (Tauri) | [runbooks/desktop-build-deps.md](runbooks/desktop-build-deps.md) | Актуален |
| Архитектурные решения | [adr/README.md](adr/README.md) + файлы 0001–0006 | Актуален (0005 Telegram, 0006 календарь) |
| Зависимости, uv, CVE-исключения | [runbooks/dependencies.md](runbooks/dependencies.md), [runbooks/security.md](runbooks/security.md) | Актуален |
| Dependabot (как закрывать алерты) | [runbooks/dependabot-review.md](runbooks/dependabot-review.md) | Актуален |
| Telegram-бот | [runbooks/telegram-bot-setup.md](runbooks/telegram-bot-setup.md), [adr/0005-telegram-bot.md](adr/0005-telegram-bot.md) | Актуален |

---

## Полный список по каталогам

### docs/history/

| Файл | Роль | Статус |
|------|------|--------|
| closed-plans-and-roadmap.md | Что сделано по roadmap и планам (аудит по коду) | Справочно |

### docs/ (корень)

| Файл | Роль | Статус |
|------|------|--------|
| README.md | Вход в документацию, ссылки по смыслу | Актуален |
| DOCS-INDEX.md | Этот индекс; модерация актуальности | Актуален |
| first-meeting-5min.md | Сценарий первой встречи за 5 минут | Актуален |
| first-meeting-5min-en.md | First meeting in 5 minutes (EN) | Актуален |
| roadmap-priority.md | Приоритет внедрения фич 1–20 | Актуален |
| development-plan-post-audit-2026.md | План развития по аудиту; сверка — claude-proposal-alignment | Справочно (многое закрыто) |
| desktop-tauri-implementation-plan.md | План реализации десктопа | Справочно (реализовано) |

### docs/runbooks/

| Файл | Роль | Статус |
|------|------|--------|
| agent-context.md | Контекст для агента, правила, чеклист конца сессии | Актуален |
| next-iteration-focus.md | Фокус следующей итерации; обновляет агент | Актуален |
| config-env-contract.md | VOICEFORGE_*, Settings, D-Bus, keyring | Актуален |
| keyring-keys-reference.md | Список имён ключей в keyring | Актуален |
| installation-guide.md | Гайд установки и запуска (toolbox, демон, ребилд) | Актуален |
| installation-guide-en.md | Installation and run guide (EN) | Актуален |
| desktop-build-deps.md | Зависимости сборки Tauri, pyannote при OOM | Актуален |
| desktop-build-deps-en.md | Desktop build dependencies (EN) | Актуален |
| first-meeting-5min — в docs/ | — | См. docs/first-meeting-5min.md |
| quickstart.md | Краткий сценарий; полная версия — first-meeting-5min | Актуален |
| quickstart-en.md | Quick start (EN) | Актуален |
| bootstrap.md | bootstrap.sh, uv sync, doctor | Актуален |
| bootstrap-en.md | Bootstrap runbook (EN) | Актуален |
| dependencies.md | Политика зависимостей, uv.lock, CVE-исключения | Актуален |
| security.md | Секреты, pip-audit, CVE-2025-69872 | Актуален |
| dependabot-review.md | Как закрывать Dependabot алерты | Актуален |
| telegram-bot-setup.md | Включение Telegram-бота (keyring, webhook, туннель) | Актуален |
| pyannote-version.md | Версия pyannote, откат при OOM | Актуален |
| cursor-agent-setup.md | Настройка Cursor (My Secrets / keyring) | Актуален |
| voiceforge-cursor-tz.md | Расширенное ТЗ для Cursor, чеклисты | Актуален |
| claude-proposal-alignment.md | Сверка предложений с кодом (что реализовано) | Справочно |
| repo-governance.md | main, PR, SonarCloud, security baseline | Актуален |
| git-github-practices.md | Conventional Commits, теги, issues, labels, GitHub Project | Актуален |
| release.md, rollback-alpha-release.md | Релизы и откат | Актуален |
| alpha2-checklist.md, alpha0.1-dod.md | Чеклисты релизов / DoD | Справочно |
| web-api.md | Web UI API | Актуален |
| test-operations.md | Flaky, CI, карантин | Актуален |
| sonar-pr-cleanup.md | Очистка PR/Sonar | Актуален |
| offline-package.md | Flatpak/AppImage, чеклист next steps | Черновик |
| planning-and-tools.md | Планирование: Markdown-backlog vs GitHub Projects в связке с агентом | Актуален |
| backlog.md | Зеркало GitHub Project (текущий фокус + Todo) | Актуален |
| calendar-integration.md | Интеграция с календарём (roadmap 17), исследование | Актуален |
| rag-formats.md | RAG: форматы индексатора, план ODT/RTF (roadmap 18) | Актуален |

### docs/adr/

| Файл | Роль | Статус |
|------|------|--------|
| README.md | Список ADR 0001–0006 | Актуален |
| 0001-core-scope-0.1.md | Заморозка 9 CLI-команд; новые — через ADR | Актуален |
| 0002-action-items-table.md | Таблица action_items, history --action-items | Актуален |
| 0003-version-reset-0.1-alpha1.md | Сброс версии | Актуален |
| 0004-desktop-tauri-dbus.md | Десктоп: Tauri, D-Bus, демон | Актуален |
| 0005-telegram-bot.md | Telegram-бот через voiceforge web, key webhook_telegram | Актуален |
| 0006-calendar-integration.md | Календарь (roadmap 17): CalDAV, keyring | Актуален |
| 0002-archive-first-cleanup.md | Superseded (исторический) | Архив |

### docs/architecture/

| Файл | Роль | Статус |
|------|------|--------|
| README.md | Что где лежит | Актуален |
| overview.md | Пайплайн, модули (mermaid) | Актуален |

---

## Правила модерации

1. **При добавлении документа:** внести в этот индекс с ролью и статусом «Актуален».
2. **При устаревании:** сменить статус на «Справочно» или «Архив» и при необходимости указать замену.
3. **После большой итерации:** проверить, не устарели ли runbooks (installation-guide, first-meeting-5min, config-env-contract) и при необходимости обновить их и индекс.

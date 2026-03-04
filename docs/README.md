# Документация VoiceForge (alpha)

Единая точка входа. Структура по смыслу, без дублирования. **Индекс и актуальность:** [DOCS-INDEX.md](DOCS-INDEX.md).

**English:** [en/README.md](en/README.md) — first meeting, installation, quickstart, runbooks (EN).

---

## Старт

| Кому | Документ |
|------|----------|
| **Пользователь: первая встреча** | [first-meeting-5min.md](first-meeting-5min.md) — полный сценарий за 5 минут |
| **Краткий сценарий** | [runbooks/quickstart.md](runbooks/quickstart.md) — линейные шаги + ссылка на полную версию |
| **Агент (Cursor)** | [runbooks/agent-context.md](runbooks/agent-context.md) — контекст, правила, keyring, чеклист конца сессии (тесты, коммит, пуш); [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md) — следующий шаг. Правило автопилота: `.cursor/rules/agent-session-handoff.mdc` |

---

## Архитектура

- [architecture/overview.md](architecture/overview.md) — пайплайн, модули, runtime flow (mermaid)
- [architecture/voiceforge-arch.jsx](architecture/voiceforge-arch.jsx) — интерактивный визуал (нужен React)
- [architecture/README.md](architecture/README.md) — что где лежит

---

## План и приоритеты

- [plans.md](plans.md) — планы, приоритет фич (roadmap 1–20), что сделано, текущие задачи
- [audit/audit.md](audit/audit.md) — аудит: статус W1–W20, Phase A–D (#55–73), оставшееся до 100%
- [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md) — фокус следующей итерации (обновляет агент)
- Выполненные планы и архив: [archive/README.md](archive/README.md), [DOCS-INDEX.md](DOCS-INDEX.md)

---

## Runbooks

Операционные инструкции и справочники — [runbooks/README.md](runbooks/README.md). Полный список и статусы — [DOCS-INDEX.md](DOCS-INDEX.md). Кратко:

- **Контекст и агент:** agent-context, next-iteration-focus, cursor, voiceforge-cursor-tz (заглушка)
- **Конфиг и среда:** config-env-contract, keyring-keys-reference, bootstrap, installation-guide, desktop-build-deps
- **Безопасность и зависимости:** security, dependencies, dependabot-review
- **Фичи:** telegram-bot-setup (ADR-0005), pyannote-version
- **Релизы:** alpha2-checklist, release, rollback-alpha-release
- **Остальное:** quickstart, repo-governance, test-operations, web-api

---

## Десктоп (Tauri)

- Сборка в toolbox: [runbooks/desktop-build-deps.md](runbooks/desktop-build-deps.md); скрипт `./scripts/setup-desktop-toolbox.sh`, затем `cd desktop && npm run tauri build`
- Перед запуском десктопа обязательно: **voiceforge daemon**
- Полный гайд установки и запуска (хост/toolbox, ребилд, демон, обновление): [runbooks/installation-guide.md](runbooks/installation-guide.md)
- План реализации десктопа выполнен; история — [archive/plans/desktop-tauri-implementation-plan.md](archive/plans/desktop-tauri-implementation-plan.md)

---

## ADR

Решения по архитектуре и процессу — [adr/README.md](adr/README.md). Активные: 0001 (core scope), 0002 (action items), 0003 (version reset), 0004 (desktop Tauri D-Bus), 0005 (Telegram-бот через voiceforge web).

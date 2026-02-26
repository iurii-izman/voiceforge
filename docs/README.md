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

- [roadmap-priority.md](roadmap-priority.md) — приоритет внедрения фич (1–20)
- [development-plan-post-audit-2026.md](development-plan-post-audit-2026.md) — план развития по аудиту; сверка с кодом — в [runbooks/claude-proposal-alignment.md](runbooks/claude-proposal-alignment.md)
- [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md) — фокус следующей итерации (обновляет агент)

---

## Runbooks

Операционные инструкции и справочники — [runbooks/README.md](runbooks/README.md). Полный список и статусы — [DOCS-INDEX.md](DOCS-INDEX.md). Кратко:

- **Контекст и агент:** agent-context, next-iteration-focus, cursor-agent-setup, voiceforge-cursor-tz
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
- План реализации: [desktop-tauri-implementation-plan.md](desktop-tauri-implementation-plan.md)

---

## ADR

Решения по архитектуре и процессу — [adr/README.md](adr/README.md). Активные: 0001 (core scope), 0002 (action items), 0003 (version reset), 0004 (desktop Tauri D-Bus), 0005 (Telegram-бот через voiceforge web).

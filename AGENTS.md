# VoiceForge — инструкции для AI-агента

Краткий контекст (полный — в `docs/runbooks/agent-context.md`). Этот файл подхватывается Cursor/Codex автоматически и задаёт те же правила для Claude при работе в репозитории.

## Проект

**VoiceForge** — локальный ассистент для аудио-встреч на Linux: PipeWire → STT → diarization → RAG → LLM. Alpha 0.2, CLI: cost, export, action-items, web, doctor и др.

## Обязательно

- **Ключи и доступы — только keyring.** Сервис `voiceforge`. Имена: `anthropic`, `openai`, `huggingface` и др. Список: `docs/runbooks/keyring-keys-reference.md`. Не хардкодить, не коммитить.
- **Среда:** Fedora Atomic Cosmic, toolbox/uv. Команды: `uv sync --extra all`, `./scripts/bootstrap.sh`, `./scripts/doctor.sh`.
- **Главный active track:** Knowledge Copilot program. Источники правды: `docs/voiceforge-copilot-architecture.md`, `docs/runbooks/copilot-program-map.md`, `docs/runbooks/next-iteration-focus.md`, `docs/runbooks/PROJECT-STATUS-SUMMARY.md`.
- **Старый roadmap / Phase E:** `docs/plans.md` и `docs/runbooks/phase-e-decision-log.md` остаются историческим контекстом и scope guard для legacy surfaces. Не возвращаться к maintenance backlog как к главному execution order, пока copilot track не блокирован.

## Контекст и продолжение

- **Полный контекст и чеклист конца сессии:** `docs/runbooks/agent-context.md` — приложить в новый чат (`@docs/runbooks/agent-context.md`).
- **Следующий шаг и промпт для нового чата:** `docs/runbooks/next-iteration-focus.md` — при продолжении работы (`@docs/runbooks/next-iteration-focus.md`).
- **Program map для автопилота:** `docs/runbooks/copilot-program-map.md`.
- **Product/architecture source of truth для Copilot:** `docs/voiceforge-copilot-architecture.md`.
- **Scope guard для автопилота:** `docs/runbooks/phase-e-decision-log.md`.
- **AI tooling / Cursor / Codex / Claude / Sonar:** `docs/runbooks/ai-tooling-setup.md`.
- **Индекс документации:** `docs/DOCS-INDEX.md`.

## Конец сессии

По возможности в конце каждой сессии: (1) тесты: `uv run pytest tests/ -q --tb=line`; при OOM — подмножество из next-iteration-focus; (2) коммит и пуш из **корня репо** (Conventional Commits, Closes #N); (3) обновить блок «Следующий шаг» в `docs/runbooks/next-iteration-focus.md`; (4) выдать промпт для следующего чата. Для repo/governance preflight перед крупной итерацией: `./scripts/preflight_repo.sh --with-tests`. Подробно: `docs/runbooks/agent-context.md` и правило agent-session-handoff.

## Эффективность

- Точечный поиск (grep/codebase_search по символам), без лишних шагов. План развития — сверять с кодом перед реализацией (`docs/voiceforge-copilot-architecture.md`, `docs/runbooks/copilot-program-map.md`, `docs/runbooks/PROJECT-STATUS-SUMMARY.md`, правило plan-verify-before-implement).
- Одна задача в сообщении — быстрее и предсказуемее результат.

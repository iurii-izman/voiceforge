# VoiceForge — инструкции для AI-агента

Краткий контекст (полный — в `docs/runbooks/agent-context.md`). Этот файл подхватывается Cursor/Codex автоматически и задаёт те же правила для Claude при работе в репозитории.

## Проект

**VoiceForge** — локальный ассистент для аудио-встреч на Linux: PipeWire → STT → diarization → RAG → LLM. Alpha 0.2, CLI: cost, export, action-items, web, doctor и др.

## Обязательно

- **Ключи и доступы — только keyring.** Сервис `voiceforge`. Имена: `anthropic`, `openai`, `huggingface` и др. Список: `docs/runbooks/keyring-keys-reference.md`. Не хардкодить, не коммитить.
- **Среда:** Fedora Atomic Cosmic, toolbox/uv. Команды: `uv sync --extra all`, `./scripts/bootstrap.sh`, `./scripts/doctor.sh`.
- **Приоритет фич:** по порядку 1→20 из `docs/plans.md`. Для Phase E дополнительно соблюдать `docs/runbooks/phase-e-decision-log.md`. Не предлагать фичи вне этого порядка без запроса.

## Контекст и продолжение

- **Полный контекст и чеклист конца сессии:** `docs/runbooks/agent-context.md` — приложить в новый чат (`@docs/runbooks/agent-context.md`).
- **Следующий шаг и промпт для нового чата:** `docs/runbooks/next-iteration-focus.md` — при продолжении работы (`@docs/runbooks/next-iteration-focus.md`).
- **Scope guard для автопилота:** `docs/runbooks/phase-e-decision-log.md`.
- **Индекс документации:** `docs/DOCS-INDEX.md`.

## Конец сессии

По возможности в конце каждой сессии: (1) тесты: `uv run pytest tests/ -q --tb=line`; при OOM — подмножество из next-iteration-focus; (2) коммит и пуш из **корня репо** (Conventional Commits, Closes #N); (3) обновить блок «Следующий шаг» в `docs/runbooks/next-iteration-focus.md`; (4) выдать промпт для следующего чата. Подробно: `docs/runbooks/agent-context.md` и правило agent-session-handoff.

## Эффективность

- Точечный поиск (grep/codebase_search по символам), без лишних шагов. План развития — сверять с кодом перед реализацией (`docs/plans.md`, `docs/runbooks/PROJECT-STATUS-SUMMARY.md`, правило plan-verify-before-implement).
- Одна задача в сообщении — быстрее и предсказуемее результат.

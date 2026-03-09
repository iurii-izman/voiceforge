# Cursor: настройка и тюнинг (VoiceForge)

Раньше: **cursor-agent-setup**, **cursor-speedup**, **cursor-tuning** объединены в этот файл. Расширенное ТЗ и старые промпты — в [archive/runbooks/voiceforge-cursor-tz-2026.md](../archive/runbooks/voiceforge-cursor-tz-2026.md).

---

## 1. Setup (Cloud Agents и локальная разработка)

**Ключи VoiceForge** — только в keyring; в Cursor My Secrets только если агент запускается без keyring (например Cloud Agent в контейнере).

- **Cloud Agents:** Create PRs — только при необходимости; Slack Notifications — по желанию. My Secrets: имена переменных (без значений в репо) — `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, Huggingface token при использовании pyannote. См. [security-and-dependencies.md](security-and-dependencies.md).
- **Локально (Fedora Atomic Cosmic):** ключи в keyring (хост или toolbox): `keyring set voiceforge anthropic`, `openai`, `huggingface`. Bootstrap: `./scripts/bootstrap.sh`, `uv sync --extra all`; проверка: `uv run voiceforge status`, `./scripts/doctor.sh`. Полный список ключей и конфига: [config-env-contract.md](config-env-contract.md), [keyring-keys-reference.md](keyring-keys-reference.md).

---

## 2. Индексация и поиск (.cursorignore)

В корне репо — **`.cursorignore`** (как .gitignore). Исключены: `.venv/`, `node_modules/`, `target/`, `dist/`, `build/`, кэши (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.uv-cache/`), `*.db`, `*.onnx`, `htmlcov/`. Индексация и codebase search быстрее, меньше шума.

---

## 3. Правила (.cursor/rules)

Правила с `alwaysApply: true` съедают токены на каждый запрос. Рекомендация: минимум таких правил; только критичные (session handoff, cost). Остальные — по файлам или вручную через @.

**Копии для .cursor/rules/:** в docs/runbooks лежат [agent-session-handoff-rule.md](agent-session-handoff-rule.md) → `.cursor/rules/agent-session-handoff.mdc`, [git-github-practices-rule.md](git-github-practices-rule.md) → `git-github-practices.mdc`. cost-and-environment, plan-verify-before-implement — по agent-context.

---

## 4. Что прикреплять в чат (кейсы)

| Цель | Что приложить (@) | Зачем |
|------|-------------------|------|
| **Новый чат, общий контекст** | `@docs/runbooks/agent-context.md` | Правила, keyring, чеклист конца сессии, roadmap. |
| **Продолжить с последней задачи** | `@docs/runbooks/next-iteration-focus.md` | Следующий шаг и готовый промпт для копирования. |
| **Максимум контекста (автопилот)** | Оба выше + `@docs/runbooks/PROJECT-STATUS-SUMMARY.md` + при необходимости `@docs/runbooks/planning.md`, `@docs/audit/audit.md`, `@docs/plans.md` | Аудит, board, batching strategy и планы. |
| **Работа по задачам Phase A–D** | `@docs/audit/audit.md` | Статус W1–W20, issues #55–73. |

Не прикреплять всё подряд: каждый большой файл увеличивает токены. AGENTS.md + один-два тематических документа обычно достаточно.

---

## 5. Промпты для нового чата

Актуальный блок — в [next-iteration-focus.md](next-iteration-focus.md) (секция «Промпт для следующего чата»). Минимальный вариант:

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md.
Ключи в keyring (keyring-keys-reference.md). Fedora Atomic/toolbox/uv; uv sync --extra all.
В конце сессии: тесты, коммит, пуш из корня репо, обновить next-iteration-focus, выдать промпт для следующего чата.

[Твоя задача или: продолжить с next-iteration-focus]
```

---

## 6. Max autopilot и coherent batching

Чтобы Cursor делал **максимум работы за сессию**, но не деградировал по качеству:

- **Стартовый порядок:** `agent-context` → `next-iteration-focus` → `PROJECT-STATUS-SUMMARY` → `planning` → `plans` / `audit`.
- **Один основной блок за итерацию:** брать 1 P0/P1 задачу и максимум 2 соседних подблока только если это тот же subsystem, те же файлы или та же verification loop.
- **Полный цикл в одной итерации:** код → targeted tests → docs/контракты → GitHub Project status → commit/push → новый `next-iteration-focus`.
- **Не спрашивать пользователя**, если ответ можно получить из кода, runbook’ов, board или keyring.
- **Останавливаться на смене поверхности:** если задача внезапно уходит в другой subsystem или требует другого стека/инструментов, закрыть текущий batch и сформировать следующий.

**Рекомендуемые batch-паттерны:**

- `bugfix + regression test + doc/contract update`
- `coverage hotspot + refactor + targeted tests`
- `version sync + release docs + install smoke`
- `web/api drift + async parity + envelope snapshots`

**Нежелательные batch-паттерны:**

- `desktop packaging + RAG + calendar`
- `LLM router + Tauri updater + CI refactor`
- `большой cross-cutting rewrite` без локально воспроизводимой проверки

**Готовый prompt для max autopilot:**

```text
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Scope guard: @docs/runbooks/phase-e-decision-log.md. Режим Cursor и batching: @docs/runbooks/cursor.md. При работе по issues и GitHub Project: @docs/runbooks/planning.md. Сводный статус и приоритеты: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Рабочая доска: https://github.com/users/iurii-izman/projects/1/views/1

Режим: максимальный автопилот и максимум согласованных блоков за итерацию. Выбирай 1 главный P0/P1 блок и до 2 соседних подблоков только если это тот же subsystem, те же файлы или те же проверки. Не смешивай unrelated surfaces. Делай полный цикл: код, targeted tests, docs/контракты, GitHub Project status, commit/push, обновление next-iteration-focus.

Источники правды по порядку: agent-context, next-iteration-focus, phase-e-decision-log, PROJECT-STATUS-SUMMARY, planning, plans, audit. При старте сверяйся с board view и бери верхний coherent `Todo` batch, который совпадает с блоком «Следующий шаг» в `next-iteration-focus.md`. Сейчас practical queue идёт по текущему Wave из `next-iteration-focus.md` и `PROJECT-STATUS-SUMMARY.md`; после E15 desktop-track идёт через E19. При начале работы переводи карточку в In Progress, при `Closes #N` — в Done. Не спрашивай пользователя, если ответ можно получить из кода/доков/board/keyring.

Среда: Fedora Atomic/toolbox/uv. Базово `uv sync --extra all`; при необходимости подключай профильные extras. Полный `pytest tests/` не запускать по умолчанию из-за OOM-risk; использовать safe subsets из next-iteration-focus и запускать ровно те проверки, которые подтверждают текущий batch.

Старт: возьми следующий приоритет из next-iteration-focus. Если он закрыт, возьми верхний согласованный P0/P1 batch из PROJECT-STATUS-SUMMARY и planning. В конце сессии: tests, commit/push из корня репо, обновление next-iteration-focus, готовый prompt для следующего чата.
```

---

## 7. OOM и тяжёлые тесты

Если полный `pytest tests/` вылетает по памяти (pyannote/torch): запускать подмножество
`uv run pytest tests/test_pipeline_integration.py tests/test_caldav_poll.py tests/test_calendar.py tests/test_transcript_log.py -q`
Подробности — в [next-iteration-focus.md](next-iteration-focus.md) (блок «Актуальные напоминания»).

---

## 8. Справка (кратко)

**Keyring (сервис voiceforge):**
`keyring set voiceforge anthropic`, `openai`, `huggingface`, `google` (опц.), `sonar_token`, `github_token`.

**RAM (пиковый, sequential):** ОС + COSMIC + PipeWire ~2–2.5 ГБ; faster-whisper small INT8 ~0.8–1 ГБ; pyannote ~1–1.4 ГБ; all-MiniLM ONNX ~0.1–0.2 ГБ; Python runtime ~0.2–0.3 ГБ. Итого пиковый ~4.2–5.5 ГБ. Swap — safety net.

**Чеклист перед PR:** ruff check/format, pytest -q, bandit, gitleaks; нет print() (только structlog), нет ключей в коде, type hints, ADR-0001 не нарушен; CHANGELOG и config-env-contract при изменении контракта.

---

## Ссылки

- [agent-context.md](agent-context.md) — контекст и конец сессии
- [next-iteration-focus.md](next-iteration-focus.md) — следующий шаг и промпт
- [DOCS-INDEX.md](../DOCS-INDEX.md) — индекс документации

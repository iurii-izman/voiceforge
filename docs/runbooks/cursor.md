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
| **Максимум контекста (автопилот)** | Оба выше + при необходимости `@docs/audit/audit.md`, `@docs/plans.md` | Аудит и планы. |
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

## 6. OOM и тяжёлые тесты

Если полный `pytest tests/` вылетает по памяти (pyannote/torch): запускать подмножество
`uv run pytest tests/test_pipeline_integration.py tests/test_caldav_poll.py tests/test_calendar.py tests/test_transcript_log.py -q`
Подробности — в [next-iteration-focus.md](next-iteration-focus.md) (блок «Актуальные напоминания»).

---

## 7. Справка (кратко)

**Keyring (сервис voiceforge):**
`keyring set voiceforge anthropic`, `openai`, `huggingface`, `google` (опц.), `sonar_token`, `github_token`.

**RAM (пиковый, sequential):** ОС + COSMIC + PipeWire ~2–2.5 ГБ; faster-whisper small INT8 ~0.8–1 ГБ; pyannote ~1–1.4 ГБ; all-MiniLM ONNX ~0.1–0.2 ГБ; Python runtime ~0.2–0.3 ГБ. Итого пиковый ~4.2–5.5 ГБ. Swap — safety net.

**Чеклист перед PR:** ruff check/format, pytest -q, bandit, gitleaks; нет print() (только structlog), нет ключей в коде, type hints, ADR-0001 не нарушен; CHANGELOG и config-env-contract при изменении контракта.

---

## Ссылки

- [agent-context.md](agent-context.md) — контекст и конец сессии
- [next-iteration-focus.md](next-iteration-focus.md) — следующий шаг и промпт
- [DOCS-INDEX.md](../DOCS-INDEX.md) — индекс документации

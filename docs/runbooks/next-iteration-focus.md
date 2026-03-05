# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-05 (#56: audio/capture из omit, fail_under 72, тесты telegram/prompt_loader)

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии (автопилот):** выведен **audio/capture** из omit — добавлен `tests/test_audio_capture.py` (моки subprocess/keyring, без реального pw-record). Добавлены `tests/test_telegram_notify.py` и тест `get_prompt_hashes` в test_prompt_loader. fail_under поднят до **72** (покрытие ~72.4%); цель 75 — следующий шаг. Python 3.12 есть в **toolbox 43** — pre-commit можно запускать там.

**Следующий шаг:** #56 — поднять fail_under до 75 (добавить тесты) или вывести из omit ещё модуль; либо задача из Phase D (#70–#73, #50).

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Промпт для следующего чата (максимальная производительность, автопилот)

**Скопируй блок ниже в начало нового чата.** Агент будет работать максимальными объёмами на автопилоте; запрашивает пользователя только когда без него нельзя (выбор стратегии, секреты не в keyring, и т.п.).

Ключи: все в keyring (сервис `voiceforge`). Список: `docs/runbooks/keyring-keys-reference.md`. Для LLM/STT: `anthropic`, `openai`, `huggingface`; для CI: `sonar_token`, `github_token`. Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print([n for n in ('anthropic','openai','huggingface') if get_api_key(n)])"`.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Фокус: @docs/runbooks/next-iteration-focus.md. Аудит и задачи: @docs/audit/audit.md. Планы и приоритеты: docs/plans.md.

Режим: максимальные объёмы, автопилот. Делай всё сам, без лишних вопросов. Запрашивай пользователя только если нужен явный выбор, подтверждение или данные вне keyring. Ключи в keyring (keyring-keys-reference.md). Fedora Atomic/toolbox/uv; uv sync --extra all. В конце сессии: тесты (uv run pytest tests/ -q --tb=line), коммит и пуш из корня репо (Conventional Commits, Closes #N где уместно), обновить next-iteration-focus (следующий шаг + дата), выдать промпт для следующего чата.

Задача: [из блока «Следующий шаг» выше] — pre-commit/Dependabot или продолжение по аудиту (coverage, pipeline test, async web).
```

---

## Промпт для нового чата: аудит системы и развитие

**Скопируй блок ниже в начало нового чата**, когда будешь готов проводить новый аудит по системе в целом и решать, куда развивать проект дальше.

```
Проект VoiceForge (local-first AI для аудиовстреч на Linux). Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md.

Нужен новый аудит по системе в целом и по основным блокам, и решение — куда расти и развивать проект далее.

Приложи и учти:
- @docs/audit/audit.md — текущий статус W1–W20, Phase A–D, оставшееся до 100%
- @docs/plans.md — планы, roadmap 1–20, что сделано, текущие задачи
- @docs/architecture/overview.md — архитектура и пайплайн
- @docs/plans.md — приоритет фич, что сделано, текущие задачи

Задача:
1. Провести аудит системы в целом (код, тесты, доки, CI/CD, безопасность, observability) и по основным блокам (audio, STT, RAG, LLM, core, web, calendar, desktop).
2. Выявить сильные стороны, узкие места и возможности роста.
3. Предложить приоритеты развития на следующую фазу (стратегия, 3–5 ключевых направлений, порядок).
4. Оформить итог: краткий отчёт + обновлённый фокус или план в docs (audit/ или plans/).

Ключи в keyring (keyring-keys-reference.md). Fedora Atomic, Python 3.12 в toolbox 43; uv sync --extra all. В конце сессии: тесты, коммит и пуш из корня репо, обновить next-iteration-focus, выдать промпт для следующего чата.
```

---

## Текущий план: Phase A–D (20 задач)

Полная доска: **[GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1)**

Аудит и маппинг: [docs/audit/audit.md](../audit/audit.md)

| Phase | Issues | Описание |
|-------|--------|----------|
| **A · Stabilize** | #55–59 | Eval CI, coverage, Sonar/CodeQL blocking, version, .editorconfig |
| **B · Hardening** | #60–64 | /ready, trace IDs, circuit breaker, purge/backup, monitoring |
| **C · Scale** | #65–69 | CVE, async web, prompt hash, benchmarks, error format |
| **D · Productize** | #50, #70–73 | A/B testing, OTel, plugins, macOS/WSL2, packaging GA |

---

## Что сделано (история)

Всё закрытое: [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Вкратце: Roadmap 1–18 реализован. Старые issues #32–49, #51–53 закрыты. Sonar ~25 замечаний закрыто. Аудит 2026-02-26 (архив: docs/archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md) выявил 20 Weaknesses — все 20 оформлены как issues #55–73.

---

## Актуальные напоминания

- **OOM / зависание Cursor при тестах:** запускать тесты **меньшими блоками**, напр. один файл: `uv run pytest tests/test_dbus_service.py -q` или лёгкие: `uv run pytest tests/test_core_metrics.py tests/test_dbus_service.py tests/test_dbus_contract_snapshot.py -q`. Полный `pytest tests/` при нехватке памяти — подмножество без тяжёлых: `uv run pytest tests/ --ignore=tests/test_pipeline_integration.py -q`.
- **OOM при тестах (pyannote/torch):** если полный `pytest tests/` вылетает по памяти, запускать подмножество: `uv run pytest tests/test_pipeline_integration.py tests/test_caldav_poll.py tests/test_calendar.py tests/test_transcript_log.py -q`. В test_pipeline_integration тест с полным run мокает _gather_step2, чтобы не загружать diarizer/RAG.
- **Pre-commit (Fedora Atomic):** Python 3.12 есть в **toolbox 43**. Выполнять `./scripts/ensure_precommit_env.sh` или `./scripts/bootstrap.sh` **внутри toolbox 43** — тогда хуки используют python3.12. При ошибке кэша (3.14.2 vs 3.14.3): `uv run pre-commit clean`. Вне toolbox (на хосте без 3.12) — временно `git commit --no-verify`, `git push --no-verify`.
- **Sonar:** `uv run python scripts/sonar_fetch_issues.py` — проверить остаток после последнего скана.
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — toolbox ([desktop-build-deps.md](desktop-build-deps.md)). Новые CLI-команды — через ADR (ADR-0001).
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).

# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-04 (полировка проекта, промпт для нового аудита)

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** Полный аудит GitHub (concurrency, permissions, Dependabot groups+npm, issue/PR templates, SECURITY.md, ruleset main). Полировка: README (0.2, ссылки на plans.md и audit.md), AGENTS.md и CONTRIBUTING (plans.md, ADR), заголовки runbooks и docs (alpha0.1 → alpha/текущее), release.md (пример тега v0.2.0-alpha.1). Ниже — **промпт для чата «Новый аудит и рост»**.

Следующий шаг: **провести новый аудит по системе в целом и основным блокам; определить направления роста и развития проекта** (использовать промпт из секции ниже).

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Промпт для нового аудита (система + рост)

**Скопируй в начало нового чата**, когда будешь готов к полному аудиту и обсуждению развития.

```
Проект VoiceForge — локальный AI-ассистент для аудиовстреч (Linux, PipeWire → STT → diarization → RAG → LLM). Контекст: @docs/runbooks/agent-context.md. Текущее состояние: @docs/audit/audit.md (статус W1–W20, Phase A–D), @docs/plans.md (roadmap 1–20, что сделано). Ключи в keyring (keyring-keys-reference.md). Fedora Atomic / toolbox 43 / uv.

Задача: провести новый аудит по системе в целом и по основным блокам (код, тесты, документация, CI/GitHub, безопасность, наблюдаемость, продукт). Оценить текущее состояние без шума и устаревших пунктов. Предложить приоритеты: что довести до идеала в первую очередь, куда расти и развивать проект дальше (фичи, платформы, качество, сообщество). Выдать структурированный отчёт и рекомендации; при необходимости — обновить docs/audit/audit.md и docs/plans.md под новый срез.

В конце сессии: тесты, коммит и пуш из корня репо; обновить next-iteration-focus; выдать промпт для следующего чата.
```

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

- **OOM при тестах:** если полный `pytest tests/` вылетает по памяти (pyannote/torch), запускать подмножество: `uv run pytest tests/test_pipeline_integration.py tests/test_caldav_poll.py tests/test_calendar.py tests/test_transcript_log.py -q`. В test_pipeline_integration тест с полным run мокает _gather_step2, чтобы не загружать diarizer/RAG.
- **Pre-commit (Fedora Atomic):** Python 3.12 есть в **toolbox 43** (и в других Fedora-образах). Выполнять `./scripts/ensure_precommit_env.sh` или `./scripts/bootstrap.sh` **внутри toolbox** — тогда хуки используют python3.12. При ошибке кэша (3.14.2 vs 3.14.3): `uv run pre-commit clean`. Вне toolbox (на хосте без 3.12) — временно `git commit --no-verify`, `git push --no-verify`.
- **Sonar:** `uv run python scripts/sonar_fetch_issues.py` — проверить остаток после последнего скана.
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — toolbox ([desktop-build-deps.md](desktop-build-deps.md)). Новые CLI-команды — через ADR (ADR-0001).
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).

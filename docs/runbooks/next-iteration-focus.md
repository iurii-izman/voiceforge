# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-06 (Phase B–C #64,#67,#68,#69 закрыты; доска обновлена)

---

## Что требуется от вас (подтверждения и действия)

- **#65 CVE:** Фикса в upstream (diskcache/instructor) **пока нет — делать ничего не нужно**. Когда появится версия с фиксом: обновить зависимости и убрать `--ignore-vuln` по чеклисту в [security-and-dependencies.md](security-and-dependencies.md) разд. 4. Dependabot-алерт можно отклонить с комментарием «No fix yet; см. runbook».
- **Keyring (HuggingFace токен):** Одна команда — при запросе «Secret:» вставьте только токен (Ctrl+Shift+V). Команда:
  ```bash
  secret-tool store --label='voiceforge huggingface' service voiceforge key huggingface
  ```
  Когда появится запрос **Secret:** — вставьте ваш токен с https://huggingface.co/settings/tokens (hf_...) и Enter.
- **OTel/Jaeger — что это и зачем:** OpenTelemetry (OTel) — это трассировка: каждый шаг пайплайна (подготовка аудио, STT, diarization, RAG, LLM) отправляется в Jaeger как «span» с длительностью. В Jaeger UI (http://localhost:16686) видна временная шкала: где сколько времени ушло, узкие места. Нужно для отладки и оптимизации. Если трейсы не нужны — снимите переменные (`unset VOICEFORGE_OTEL_ENABLED OTEL_EXPORTER_OTLP_ENDPOINT`). Если Jaeger крутится на хосте, а команды в toolbox — из контейнера хост доступен по адресу `10.0.2.2`, поэтому задают `OTEL_EXPORTER_OTLP_ENDPOINT=http://10.0.2.2:4318`.
- **#66 Async:** Реализован опциональный async-сервер (Starlette + uvicorn); см. ниже. Ничего подтверждать не нужно.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** Закрыты #64, #67, #68, #69 (monitoring, prompt hash, benchmark, error format) — реализация была готова по аудиту; добавлена запись в history/closed-plans-and-roadmap.md; карточки 64, 67, 68, 69 на доске переведены в Done. В next-iteration-focus добавлен блок «Что требуется от вас».

**Следующий шаг:** #65 (снять ignore CVE после фикса upstream) или развитие по roadmap (roadmap 19, e2e, качество). Единый план: [plans.md](../plans.md).

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

## Промпт: максимальный автопилот + максимальный объём

**Скопируй блок ниже в начало нового чата.** Агент делает максимум задач за сессию, без остановок и лишних вопросов. Обращаться к пользователю только при явном выборе стратегии, отсутствии данных в keyring или критичном решении.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Аудит: @docs/audit/audit.md. Планы: @docs/plans.md.

Режим: максимальный автопилот, максимально большой объём работы за одну сессию. Бери несколько блоков подряд из «Следующий шаг» и plans.md (coverage #56, #66, W17, Phase D доработки). Делай всё сам: код, доки, доска (In Progress при старте по issue, Done при Closes #N — см. planning.md). Не спрашивай пользователя — действуй. Спрашивай только при явном выборе стратегии или данных вне keyring.

Среда: Fedora Atomic, toolbox, uv. Ключи только в keyring (voiceforge). Команды: uv sync --extra all. Тесты — только лёгкие (см. next-iteration-focus «Актуальные напоминания»), не полный pytest (риск OOM). Pre-commit в toolbox; на хосте без 3.12 — git commit/push с --no-verify.

В конце сессии обязательно: (1) лёгкие тесты, (2) коммит и пуш из корня репо (Conventional Commits, Closes #N где закрыл issue), (3) обновить next-iteration-focus (блок «Сделано в сессии», «Следующий шаг», дата), (4) выдать готовый промпт для следующего чата (этот же формат).

Задача: выполнить следующий шаг из next-iteration-focus и по возможности следующие по порядку из plans.md/audit (coverage в toolbox и fail_under=75 #56; #66/W17; доработки Phase D #70–73). Работать максимальным объёмом без остановок.
```

---

## Промпт для нового чата: аудит системы и развитие

**Скопируй блок ниже в начало нового чата**, когда будешь готов проводить новый аудит по системе в целом и решать, куда развивать проект дальше.

```
Проект VoiceForge (local-first AI для аудиовстреч на Linux). Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md.

Нужен новый аудит по системе в целом и по основным блокам, и решение — куда расти и развивать проект далее.

Приложи и учти:
- @docs/audit/audit.md — текущий статус W1–W20, Phase A–D, оставшееся до 100%
- @docs/plans.md — планы, roadmap 1–19, что сделано, текущие задачи
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

## Текущий план: Phase A–D (19 задач)

**Единый источник:** [docs/plans.md](../plans.md) (Steps 1–19, оставшееся до 100%, критерии Phase D). Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1). Статус W1–W20: [audit/audit.md](../audit/audit.md).

| Phase | Issues | Описание |
|-------|--------|----------|
| **A · Stabilize** | #55–59 | Eval CI, coverage, Sonar/CodeQL blocking, version, .editorconfig |
| **B · Hardening** | #60–64 | /ready, trace IDs, circuit breaker, purge/backup, monitoring |
| **C · Scale** | #65–69 | CVE, async web, prompt hash, benchmarks, error format |
| **D · Productize** | #70–73 | A/B testing, OTel (#71 в работе), plugins, packaging GA |

---

## Что сделано (история)

Всё закрытое: [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Вкратце: Roadmap 1–18 реализован. Старые issues #32–49, #51–53 закрыты. Sonar ~25 замечаний закрыто. Аудит 2026-02-26 (архив: docs/archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md) выявил 20 Weaknesses — все 20 оформлены как issues #55–73.

---

## Актуальные напоминания

- **OOM / зависание Cursor при тестах:** запускать **только лёгкие** тесты, напр. `uv run pytest tests/test_prompt_loader.py tests/test_core_metrics.py tests/test_llm_circuit_breaker.py tests/test_tracing.py tests/test_audio_buffer.py tests/test_telegram_notify.py tests/test_llm_retry.py -q --tb=line` и/или `uv run pytest tests/eval/ -k "not judge" -q`. Не запускать полный `pytest tests/` в Cursor (pyannote/torch/pipeline) — риск OOM.
- **OOM при тестах (pyannote/torch):** если полный `pytest tests/` вылетает по памяти, запускать подмножество: `uv run pytest tests/test_pipeline_integration.py tests/test_caldav_poll.py tests/test_calendar.py tests/test_transcript_log.py -q`. В test_pipeline_integration тест с полным run мокает _gather_step2, чтобы не загружать diarizer/RAG.
- **Pre-commit (Fedora Atomic):** Python 3.12 в контейнере **fedora-toolbox-43** (`toolbox run -c fedora-toolbox-43 bash -c 'cd /var/home/user/Projects/voiceforge && uv run pre-commit run --all-files'`). Выполнять `./scripts/ensure_precommit_env.sh` внутри этого контейнера. Вне toolbox (на хосте без 3.12) — временно `git commit --no-verify`, `git push --no-verify`.
- **Sonar:** `uv run python scripts/sonar_fetch_issues.py` — проверить остаток после последнего скана.
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — toolbox ([desktop-build-deps.md](desktop-build-deps.md)). Новые CLI-команды — через ADR (ADR-0001).
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).
- **Доска (Project):** при работе по issue — перевести карточку в In Progress; при коммите с `Closes #N` — в Done. Команды и ID полей: [planning.md](planning.md) раздел «Обновление доски».

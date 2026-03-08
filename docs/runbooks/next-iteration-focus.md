# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-08 (#97 web action-items batch closed)

---

## Что требуется от вас (подтверждения и действия)

- **#65 CVE:** Фикса в upstream (diskcache/instructor) **пока нет — делать ничего не нужно**. Когда появится версия с фиксом: обновить зависимости и убрать `--ignore-vuln` по чеклисту в [security-and-dependencies.md](security-and-dependencies.md) разд. 4. Dependabot-алерт можно отклонить с комментарием «No fix yet; см. runbook».
- **Keyring (HuggingFace):** Проверка, что ключ сохранён: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. Сохранение (один раз): `secret-tool store --label='voiceforge huggingface' service voiceforge key huggingface` → при запросе **Secret:** вставить токен (hf_...) с https://huggingface.co/settings/tokens. **Проверено:** ключ huggingface в keyring присутствует (present).
- **OTel/Jaeger — кто управляет:** Агент не может сам запускать Jaeger, открывать браузер или смотреть трейсы. Запуск контейнера (podman/docker), открытие http://localhost:16686, установка/снятие переменных в сессии — делаете вы. Агент может только обновить доки и подсказать команды. ОTel — трассировка шагов пайплайна (длительности) в Jaeger для отладки. Если не нужны трейсы: `unset VOICEFORGE_OTEL_ENABLED OTEL_EXPORTER_OTLP_ENDPOINT`. Jaeger на хосте, команды в toolbox: `OTEL_EXPORTER_OTLP_ENDPOINT=http://10.0.2.2:4318`.
- **#66 Async:** Реализован опциональный async-сервер (Starlette + uvicorn); см. ниже. Ничего подтверждать не нужно.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** Закрыт coherent P0 web batch по issue [#97](https://github.com/iurii-izman/voiceforge/issues/97): исправлен tuple-unpack bug в `POST /api/action-items/update` для sync/async web (`server.py`, `server_async.py`), добавлены web regression tests на happy path и nested error envelope (`tests/test_web_action_items_update.py`), обновлён `web-api.md` под фактический error envelope и async-only `/api/analyze/stream`.

**Следующий шаг:** Взять **coherent P1 release/install batch** по issue [#98](https://github.com/iurii-izman/voiceforge/issues/98) из [GitHub Project VoiceForge view](https://github.com/users/iurii-izman/projects/1/views/1): (1) решить contract для `uv sync --extra all` vs `web-async` extra, (2) синхронизировать version metadata между Python/Desktop/Tauri/Flatpak файлами, (3) обновить release/install docs под фактический setup path, (4) добавить лёгкую consistency-проверку или script на release metadata. После #98 идти строго по board order: [#99](https://github.com/iurii-izman/voiceforge/issues/99) → [#100](https://github.com/iurii-izman/voiceforge/issues/100) → [#101](https://github.com/iurii-izman/voiceforge/issues/101). Для verify использовать targeted subset по изменённой поверхности; при отсутствии hypothesis — `pytest tests/ --ignore=tests/test_rag_parsers_hypothesis.py`. Pre-commit в toolbox 43: `cd /var/home/user/Projects/voiceforge && uv run pre-commit run --all-files`.

---

## GitHub: подготовка к бете (PR и issues)

**Полный чеклист:** [pre-beta-sonar-github.md](pre-beta-sonar-github.md).

- **PR #81, #79:** закрыты с комментарием «Applied in main» (2026-03-07).
- **Открытые issues:** #65 (CVE — ждём upstream). #50 (macOS/WSL2) закрыт 2026-03-07 — снят с скоупа.

**Sonar:** S7721, S2737, S3776, S7735 закрыты в 9b92a46. Проверить остаток: `uv run python scripts/sonar_fetch_issues.py` в toolbox 43. **Mypy:** в scope verify_pr — 0 ошибок. **verify_pr:** Ruff + Mypy OK; bandit — зелёный (nosec B310/B608). **Gitleaks:** allowlist .hypothesis/ + .gitignore; шаг [8/8] в CI проходит (workflow Gitleaks зелёный после 270b7e2/42f904c).

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

## Промпт: максимальный автопилот + максимум согласованных блоков

**Скопируй блок ниже в начало нового чата.** Агент делает максимум работы за сессию, но берёт только согласованные блоки в одном subsystem и доводит их до конца без лишних вопросов.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Режим Cursor и batching: @docs/runbooks/cursor.md. При работе по issues и GitHub Project: @docs/runbooks/planning.md. Сводный статус и приоритеты: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. При необходимости деталей: @docs/audit/audit.md и @docs/plans.md. Рабочая доска: https://github.com/users/iurii-izman/projects/1/views/1

Режим: максимальный автопилот и максимум согласованных блоков за итерацию. Выбирай 1 главный P0/P1 блок и до 2 соседних подблоков только если это тот же subsystem, те же файлы или те же проверки. Не смешивай unrelated surfaces. Делай полный цикл: код, targeted tests, docs/контракты, GitHub Project status, commit/push, обновление next-iteration-focus. Не спрашивай пользователя, если ответ можно получить из кода, docs, board или keyring.

Источники правды по порядку: agent-context, next-iteration-focus, PROJECT-STATUS-SUMMARY, planning, plans, audit. При старте всегда сверяйся с GitHub Project view и бери верхнюю `Todo` карточку из audit-batches: #97, затем #98, #99, #100, #101. При начале работы переводи карточку в In Progress, при `Closes #N` — в Done.

Среда: Fedora Atomic, toolbox, uv. Ключи только в keyring (voiceforge). Базово `uv sync --extra all`; при необходимости подключай профильные extras. Полный `pytest tests/` не запускать по умолчанию из-за OOM-risk; использовать safe subsets из next-iteration-focus и запускать ровно те проверки, которые подтверждают текущий batch. Pre-commit в toolbox; на хосте без 3.12 — git commit/push с --no-verify.

В конце сессии обязательно: (1) targeted tests по изменённой поверхности, (2) commit/push из корня репо (Conventional Commits, `Closes #N` где уместно), (3) обновить next-iteration-focus (блоки «Сделано в сессии», «Следующий шаг», дата), (4) выдать готовый prompt для следующего чата.

Задача: выполнить следующий coherent batch из блока «Следующий шаг», начиная с issue #97. Если он закрыт, взять верхний P0/P1 batch из PROJECT-STATUS-SUMMARY и GitHub Project: #98, затем #99, #100, #101.
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
- **Pre-commit (Fedora Atomic):** Python **3.12 и 3.14** установлены в контейнере **fedora-toolbox-43** (toolbox-43). Pre-commit и uv: `toolbox run -c fedora-toolbox-43 bash -c 'cd /var/home/user/Projects/voiceforge && uv run pre-commit run --all-files'`. Выполнять `./scripts/ensure_precommit_env.sh` внутри этого контейнера. Вне toolbox (на хосте без 3.12) — временно `git commit --no-verify`, `git push --no-verify`.
- **Sonar:** `uv run python scripts/sonar_fetch_issues.py` — проверить остаток после последнего скана.
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — toolbox ([desktop-build-deps.md](desktop-build-deps.md)). Новые CLI-команды — через ADR (ADR-0001).
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).
- **Доска (Project):** при работе по issue — перевести карточку в In Progress; при коммите с `Closes #N` — в Done. Команды и ID полей: [planning.md](planning.md) раздел «Обновление доски».

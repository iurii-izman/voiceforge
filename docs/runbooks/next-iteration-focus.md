# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-08 (closed #117; следующий batch = #118 `stt/*`)

---

## Что требуется от вас (подтверждения и действия)

- **#65 CVE:** Фикса в upstream (diskcache/instructor) **пока нет — делать ничего не нужно**. Когда появится версия с фиксом: обновить зависимости и убрать `--ignore-vuln` по чеклисту в [security-and-dependencies.md](security-and-dependencies.md) разд. 4. Dependabot-алерт можно отклонить с комментарием «No fix yet; см. runbook».
- **Новая стратегическая очередь #114-#123:** ручных действий для её сопровождения не требуется; после закрытия `#114`, `#115`, `#116` и `#117` текущий practical execution order на ближайшие сессии: **#118 -> #119 -> #120**.
- **Keyring (HuggingFace):** Проверка, что ключ сохранён: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. Сохранение (один раз): `secret-tool store --label='voiceforge huggingface' service voiceforge key huggingface` → при запросе **Secret:** вставить токен (hf_...) с https://huggingface.co/settings/tokens. **Проверено:** ключ huggingface в keyring присутствует (present).
- **OTel/Jaeger — кто управляет:** Агент не может сам запускать Jaeger, открывать браузер или смотреть трейсы. Запуск контейнера (podman/docker), открытие http://localhost:16686, установка/снятие переменных в сессии — делаете вы. Агент может только обновить доки и подсказать команды. ОTel — трассировка шагов пайплайна (длительности) в Jaeger для отладки. Если не нужны трейсы: `unset VOICEFORGE_OTEL_ENABLED OTEL_EXPORTER_OTLP_ENDPOINT`. Jaeger на хосте, команды в toolbox: `OTEL_EXPORTER_OTLP_ENDPOINT=http://10.0.2.2:4318`.
- **#66 Async:** Реализован опциональный async-сервер (Starlette + uvicorn); см. ниже. Ничего подтверждать не нужно.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** закрыт **#117**. Добавлен focused suite [tests/test_rag_batch117.py](../../tests/test_rag_batch117.py), который даёт reproducible confidence для heavy RAG lifecycle без захода в ONNX-heavy internals: покрыты `_index_directory`, CLI `index` с prune semantics, CLI `rag-export`, restore helpers из [incremental.py](../../src/voiceforge/rag/incremental.py) и lightweight search helpers из [searcher.py](../../src/voiceforge/rag/searcher.py). Поверх нового suite перепроверен существующий RAG subset (`test_cli_e2e_smoke`, `test_rag_query_keywords`, `test_rag_parsers`, `test_pipeline_integration`); граница batch явно зафиксирована: embedder/ONNX-heavy search internals остаются manual/heavy. Обновлён [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md): `#117` отмечен как закрытый, practical queue сдвинут на `#118 -> #119 -> #120`.

**Следующий шаг:** брать **#118** как отдельный coherent batch только по audio/STT lifecycle/perf proof в `src/voiceforge/stt/*` и смежных lifecycle helpers. Цель: cheap benchmark/smoke path, подтверждение repeat analyze/listen lifecycle и хотя бы один measurable perf/lifecycle improvement либо честное ограничение. Не смешивать этот batch с RAG, web, security или release/docs.

---

## GitHub: подготовка к бете (PR и issues)

**Полный чеклист:** [pre-beta-sonar-github.md](pre-beta-sonar-github.md).

- **PR #81, #79:** закрыты с комментарием «Applied in main» (2026-03-07).
- **Открытые issues:** #65 (CVE — ждём upstream) и стратегическая очередь **#118-#123**. `#114`, `#115`, `#116` и `#117` уже закрыты; следующий code-heavy кандидат — `#118`, затем `#119`, затем `#120`. #50 (macOS/WSL2) закрыт 2026-03-07 — снят с активного скоупа.

**Sonar:** S7721, S2737, S3776, S7735 закрыты в 9b92a46. Проверить остаток: `uv run python scripts/sonar_fetch_issues.py` в toolbox 43. **Mypy:** в scope verify_pr — 0 ошибок. **verify_pr:** Ruff + Mypy OK; bandit — зелёный (nosec B310/B608). **Gitleaks:** allowlist .hypothesis/ + .gitignore; шаг [8/8] в CI проходит (workflow Gitleaks зелёный после 270b7e2/42f904c).

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Промпт для следующего чата (максимальная производительность, автопилот)

**Скопируй блок ниже в начало нового чата.** Агент будет работать максимальными объёмами на автопилоте; запрашивает пользователя только когда без него нельзя (выбор стратегии, секреты не в keyring, и т.п.).

Ключи: все в keyring (сервис `voiceforge`). Список: `docs/runbooks/keyring-keys-reference.md`. Для LLM/STT: `anthropic`, `openai`, `huggingface`; для CI: `sonar_token`, `github_token`. Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print([n for n in ('anthropic','openai','huggingface') if get_api_key(n)])"`.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Фокус: @docs/runbooks/next-iteration-focus.md. Сводный статус и очередь: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Аудит и задачи: @docs/audit/audit.md. Планы и приоритеты: docs/plans.md.

Режим: максимальные объёмы, автопилот. Делай всё сам, без лишних вопросов. Запрашивай пользователя только если нужен явный выбор, подтверждение или данные вне keyring. Ключи в keyring (keyring-keys-reference.md). Fedora Atomic/toolbox/uv; uv sync --extra all. В конце сессии: тесты (uv run pytest tests/ -q --tb=line), коммит и пуш из корня репо (Conventional Commits, Closes #N где уместно), обновить next-iteration-focus (следующий шаг + дата), выдать промпт для следующего чата.

Задача: взять верхний coherent batch из блока «Следующий шаг» и GitHub Project. На сейчас это **#118**: audio/STT lifecycle/perf proof в `src/voiceforge/stt/*` и смежных lifecycle helpers. Сделай cheap benchmark/smoke path для repeat analyze/listen lifecycle и отдельно зафиксируй, что остаётся дорогим/manual.
```

---

## Промпт: максимальный автопилот + максимум согласованных блоков

**Скопируй блок ниже в начало нового чата.** Агент делает максимум работы за сессию, но берёт только согласованные блоки в одном subsystem и доводит их до конца без лишних вопросов.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Режим Cursor и batching: @docs/runbooks/cursor.md. При работе по issues и GitHub Project: @docs/runbooks/planning.md. Сводный статус и приоритеты: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. При необходимости деталей: @docs/audit/audit.md и @docs/plans.md. Рабочая доска: https://github.com/users/iurii-izman/projects/1/views/1

Режим: максимальный автопилот и максимум согласованных блоков за итерацию. Выбирай 1 главный P0/P1 блок и до 2 соседних подблоков только если это тот же subsystem, те же файлы или те же проверки. Не смешивай unrelated surfaces. Делай полный цикл: код, targeted tests, docs/контракты, GitHub Project status, commit/push, обновление next-iteration-focus. Не спрашивай пользователя, если ответ можно получить из кода, docs, board или keyring.

Источники правды по порядку: agent-context, next-iteration-focus, PROJECT-STATUS-SUMMARY, planning, plans, audit. При старте всегда сверяйся с GitHub Project view и бери верхнюю `Todo` карточку, которая совпадает с блоком «Следующий шаг». При начале работы переводи карточку в In Progress, при `Closes #N` — в Done.

Среда: Fedora Atomic, toolbox, uv. Ключи только в keyring (voiceforge). Базово `uv sync --extra all`; при необходимости подключай профильные extras. Полный `pytest tests/` не запускать по умолчанию из-за OOM-risk; использовать safe subsets из next-iteration-focus и запускать ровно те проверки, которые подтверждают текущий batch. Pre-commit в toolbox; на хосте без 3.12 — git commit/push с --no-verify.

В конце сессии обязательно: (1) targeted tests по изменённой поверхности, (2) commit/push из корня репо (Conventional Commits, `Closes #N` где уместно), (3) обновить next-iteration-focus (блоки «Сделано в сессии», «Следующий шаг», дата), (4) выдать готовый prompt для следующего чата.

Задача: выполнить следующий coherent batch из блока «Следующий шаг» и GitHub Project, сохраняя batching discipline: один subsystem, один verification loop, один честный handoff. На сейчас это **#118** по audio/STT lifecycle/perf proof; `#119` и `#120` трогать только в следующих сессиях.
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

## Текущая стратегическая очередь: score `76.5 -> 100`

**Единый источник:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) разд. 10-12 + [planning.md](planning.md). Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1). Исторический план Phase A-D закрыт; активный queue теперь ведётся отдельными стратегическими issues.

| Priority | Issues | Описание |
|----------|--------|----------|
| **P0** | - | Текущий P0 structural queue закрыт batches `#114-#116` |
| **P1 code-heavy** | #118, #119, #120 | Audio/STT lifecycle/perf proof, contract drift prevention, security hardening |
| **P1 evidence/manual** | #121, #122, #123 | Jaeger/runtime evidence, release proof, docs/governance sweep |

---

## Что сделано (история)

Всё закрытое: [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Вкратце: Roadmap 1–18 реализован. Старые issues #32–49, #51–53 закрыты. Sonar ~25 замечаний закрыто. Аудит 2026-02-26 (архив: docs/archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md) выявил 20 Weaknesses — они прошли через issues #55–73 и последующие follow-up batches #97–#113; текущий score-to-100 queue продолжен стратегическими блоками #114–#123, из которых `#114`, `#115`, `#116` и `#117` уже закрыты.

---

## Актуальные напоминания

- **OOM / зависание Cursor при тестах:** запускать **только лёгкие** тесты, напр. `uv run pytest tests/test_prompt_loader.py tests/test_core_metrics.py tests/test_llm_circuit_breaker.py tests/test_tracing.py tests/test_audio_buffer.py tests/test_telegram_notify.py tests/test_llm_retry.py -q --tb=line` и/или `uv run pytest tests/eval/ -k "not judge" -q`. Не запускать полный `pytest tests/` в Cursor (pyannote/torch/pipeline) — риск OOM.
- **OOM при тестах (pyannote/torch):** если полный `pytest tests/` вылетает по памяти, запускать подмножество: `uv run pytest tests/test_pipeline_integration.py tests/test_caldav_poll.py tests/test_calendar.py tests/test_transcript_log.py -q`. В test_pipeline_integration тест с полным run мокает _gather_step2, чтобы не загружать diarizer/RAG.
- **Pre-commit (Fedora Atomic):** Python **3.12 и 3.14** установлены в контейнере **fedora-toolbox-43** (toolbox-43). Pre-commit и uv: `toolbox run -c fedora-toolbox-43 bash -c 'cd /var/home/user/Projects/voiceforge && uv run pre-commit run --all-files'`. Выполнять `./scripts/ensure_precommit_env.sh` внутри этого контейнера. Вне toolbox (на хосте без 3.12) — временно `git commit --no-verify`, `git push --no-verify`.
- **Sonar:** `uv run python scripts/sonar_fetch_issues.py` — проверить остаток после последнего скана.
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — toolbox ([desktop-build-deps.md](desktop-build-deps.md)). Новые CLI-команды — через ADR (ADR-0001).
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).
- **Доска (Project):** при работе по issue — перевести карточку в In Progress; при коммите с `Closes #N` — в Done. Команды и ID полей: [planning.md](planning.md) раздел «Обновление доски».

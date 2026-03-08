# Итог по проекту VoiceForge (12 разделов)

Единый свод: планы vs код, что сделано, что осталось вам, Sonar/GitHub, приоритеты. Обновлено: 2026-03-08.

---

## 1. Что сделано агентом в этой сессии

- **Сверка планов с кодом:** подтверждено, что блоки 44 (история буфера), 46 (слайд-панель настроек), 49 (виджет «Последний анализ»), 68 (streaming LLM), 71 (Whisper API), 75 (поиск RAG), 79 (создание события из сессии) уже реализованы в коде.
- **Обновлены документы:** в [backlog-and-actions.md](../plans/backlog-and-actions.md) отмечены как реализованные блоки 44, 46, 49 (плюс ранее 35, 68, 71, 75, 79). В [roadmap-100-blocks.md](../plans/roadmap-100-blocks.md) секция «Не реализовано» приведена в соответствие (66 — только prompt caching; 68, 71, 79 — зачёркнуты).
- **Правки по Sonar:** optional chain в `desktop/src/main.js` (S6582); dict comprehension в `scripts/git_credential_keyring_pat.py` (S7494); NOSONAR для неиспользуемых параметров интерфейса в `stt/openai_whisper.py` (S1172) и для вызова fixture в `tests/test_benchmark_pipeline.py` (S5864).

---

## 2. Соответствие планов и кода (что реализовано)

| Источник | Реализовано в коде |
|----------|---------------------|
| **backlog-and-actions блок B** | 35, 44, 46, 49, 66 (cache_control есть), 68, 71, 75, 79 |
| **roadmap 1–19 (plans.md)** | 1–18 реализованы; 19 (prompt caching для не-Claude) — research |
| **Phase A–D (Steps 1–19)** | Большинство закрыто; #65 (CVE) ждёт upstream; Phase D #70–#73 реализованы |
| **roadmap-100-blocks «Не реализовано»** | Остаётся только 66 (prompt caching — доработка по API) |

Файлы-подтверждения: `desktop/src/main.js` (clipboard_history, last-analysis, settings_as_panel, streaming-analysis-chunk, add-to-calendar), `stt/openai_whisper.py`, `llm/router.py` (stream_completion, analyze_meeting_stream), `core/pipeline.py` (_step1_stt stt_backend), демон/D-Bus (CreateEventFromSession, StreamingAnalysisChunk, SearchRag).

---

## 3. Что осталось реализовать (кодом)

- **По приоритету (на усмотрение):**
  - Блок 66: prompt caching для Claude реализован (cache_control в router); для не-Claude документировано в prompt-management.md, доработка по API провайдеров.
  - ~~Блок 69~~: реализовано — retry с backoff в circuit_breaker. ~~Блок 72~~: уже было — подсказка «Analyzing… (≈ N–M s)» в CLI.
  - Phase D: ~~#70~~ (A/B), ~~#71~~ (OTel: core/otel.py + observability-alerts.md), ~~#72~~ (custom templates), ~~#73~~ (packaging: offline-package.md, make flatpak-build) — реализованы.
- **Из roadmap-100 списка:** часть пунктов (45, 50, 51–54, 57–65, 67, 70, 73–78, 80–100) уже есть в коде или в доке; остальное — по приоритету из планов и backlog.

---

## 4. Что осталось сделать вам (ручные шаги и решения)

- **Блок A (подтверждения):** #65 CVE — пока ничего; при появлении фикса upstream обновить зависимости и убрать `--ignore-vuln` по [security-and-dependencies.md](security-and-dependencies.md). Keyring (HuggingFace) — по доке проверено. OTel/Jaeger — запуск контейнера и просмотр трейсов у вас.
- **Блок C (ручные шаги):** сборка/запуск десктопа (`cd desktop && npm run tauri build/dev`); ключи в keyring; при необходимости — updater (ключи подписи, сервер обновлений); релизы и распространение; ручное тестирование с человеком. Чеклист: [MANUAL-AND-CANNOT-DO.md](../plans/MANUAL-AND-CANNOT-DO.md).
- **Блок D (GitHub):** #65 оставить открытым; #50 в бэклоге (p2). По verify_pr/bandit — решить, добиваться ли полного зелёного (см. блок E).
- **Блок E (опционально):** поручить агенту доработку bandit и оставшихся замечаний Sonar по приоритету.

---

## 5. Sonar: замечания и что исправлено

**Получить актуальный список:** `uv run python scripts/sonar_fetch_issues.py` (нужен `sonar_token` в keyring).

**На 2026-03-07 (выборка):**
- **Исправлено в сессии:** S6582 (optional chain в main.js), S7494 (dict comprehension в git_credential_keyring_pat.py), S1172 (NOSONAR в openai_whisper.py), S5864 (NOSONAR в test_benchmark_pipeline.py).
- **Остаются (требуют рефакторинга или принятия):**
  - **S3776 (Cognitive Complexity):** daemon.py:418, main.py:1680, main.py:1143, daemon.py:520, router.py:210, router.py:560, server_async.py:343, desktop main.js:2184 — рефакторинг функций для снижения сложности.
  - **Прочие:** S3358 (test_caldav_poll.py), S7735/S4624/S6582 (desktop main.js) — по желанию; принять или править по приоритету.

Чеклист перед бета: [pre-beta-sonar-github.md](pre-beta-sonar-github.md).

---

## 6. GitHub: PR, issues, доска

- **PR:** #81, #79 закрыты с комментарием «Applied in main» (2026-03-07).
- **Issues:** #65 (CVE — ждём upstream), #50 (macOS/WSL2 — p2/backlog). Остальные по планам и доске.
- **Доска:** [VoiceForge Board](https://github.com/users/iurii-izman/projects/1). При работе по issue — In Progress; при Closes #N — Done. Команды и ID полей: [planning.md](planning.md).
- **Dependabot:** при CVE #65 — отклонить с комментарием из security-and-dependencies.md или скрипт `uv run python scripts/dependabot_dismiss_moderate.py`.

---

## 7. Рекомендации по приоритетам

1. **Стабилизация:** довести Sonar (S3776 и остальное) по решению команды; при появлении фикса CVE #65 — обновить зависимости.
2. **Phase D:** #70–#73 закрыты (eval-ab, OTel, custom templates, packaging runbook).
3. **Блоки 69/72:** retry LLM, оценка длительности analyze — быстрые улучшения UX.
4. **Ручные шаги:** сборка десктопа, ключи, релиз, тестирование — по чеклисту MANUAL-AND-CANNOT-DO.

---

## 8. Критичные/важные проблемы на следующую итерацию

- **#65 CVE:** следить за upstream (diskcache/instructor); при фиксе — обновить и убрать ignore.
- **Sonar S3776:** 8 мест с высокой когнитивной сложностью — рефакторинг по одному или принять по решению.
- **verify_pr/bandit:** при желании полного зелёного — доработать оставшиеся предупреждения bandit.
- **Pre-commit на хосте:** без Python 3.12 использовать `git commit/push --no-verify`; полный pre-commit в toolbox 43.

---

## 9. Промпт для следующего чата

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Фокус: @docs/runbooks/next-iteration-focus.md. Итог по проекту: @docs/runbooks/PROJECT-STATUS-SUMMARY.md.

Режим: автопилот. Ключи только в keyring (сервис voiceforge). Fedora Atomic, toolbox 43; uv sync --extra all. В конце сессии: тесты (uv run pytest … -q --tb=line или лёгкое подмножество при OOM), коммит и пуш из корня репо (Conventional Commits, Closes #N где уместно), обновить next-iteration-focus, выдать промпт для следующего чата.

Задача: По PROJECT-STATUS-SUMMARY разд. 3–4 и 7–8 — следующий приоритет: рефакторинг Sonar S3776, блоки 69/72, Phase D (#70–73) или ручные шаги из MANUAL-AND-CANNOT-DO.
```

---

## 10. Deep audit delta (2026-03-08)

Новый независимый аудит показал: **интегральная оценка проекта ~71.3/100**, реалистичный эталон для этой системы — **~86.5/100**. Сильные стороны: security baseline, observability, docs coverage по breadth, breadth of product surface. Главные просадки: transport parity, effective coverage, release/packaging contract и docs drift.

| Направление | Текущее | Эталон | Gap | Ключевой вывод |
|-------------|---------|--------|-----|----------------|
| Core architecture & module boundaries | 61 | 84 | 23 | Слишком много логики в `main.py`, `daemon.py`, `server.py`, `router.py`, `desktop/src/main.js` |
| Audio / STT / diarization | 74 | 86 | 12 | Работает, но есть lifecycle/perf debt |
| RAG / data / storage | 76 | 88 | 12 | Блок функционально сильный, lifecycle и restore confidence слабее |
| LLM / prompts / PII | 73 | 87 | 14 | Good guardrails, но coverage router и policy centralization ограничены |
| Interfaces & integrations | 64 | 85 | 21 | Найден реальный web bug + docs/API drift |
| Testing & QA | 71 | 86 | 15 | Реальное coverage ~63.95%, а не то, что ощущается по docs |
| Security & dependency hygiene | 78 | 89 | 11 | Сильный baseline; open risk — CVE #65 и local unencrypted DBs |
| Observability & runtime ops | 77 | 88 | 11 | Хорошо для alpha, но часть paths не верифицирована end-to-end |
| CI/CD & release / packaging | 74 | 87 | 13 | CI зрелый, packaging/updater contract пока inconsistent |
| Documentation & governance | 68 | 86 | 18 | Доков много, но есть stale/broken refs и version drift |

**Подтверждённые hotspots:** [src/voiceforge/main.py](/home/user/Projects/voiceforge/src/voiceforge/main.py), [src/voiceforge/core/daemon.py](/home/user/Projects/voiceforge/src/voiceforge/core/daemon.py), [src/voiceforge/web/server.py](/home/user/Projects/voiceforge/src/voiceforge/web/server.py), [src/voiceforge/web/server_async.py](/home/user/Projects/voiceforge/src/voiceforge/web/server_async.py), [src/voiceforge/llm/router.py](/home/user/Projects/voiceforge/src/voiceforge/llm/router.py), [desktop/src/main.js](/home/user/Projects/voiceforge/desktop/src/main.js).

**Текущие evidence gaps:** локально не гонялся `cargo-audit`, не запускался полный `pytest tests/` из-за OOM-risk, не проверялись live Jaeger traces и updater signing flow. Desktop packaging/updater изменения в worktree считать `worktree-in-progress`, а не завершённым состоянием.

---

## 11. Critical Path, Quick Wins, top risks

**Critical Path (в порядке):**

1. Исправить bug в `POST /api/action-items/update` для sync/async web и добавить regression tests.
2. Закрыть install/release contract: `web-async` profile, version sync, release/docs drift.
3. Сократить coverage blind spots в `server.py`, `server_async.py`, `daemon.py`, `router.py`, `main.py`.
4. Убрать performance debt: new-per-analyze `Diarizer`/`HybridSearcher`, full ring rewrite каждые 2 сек.
5. Довести packaging/updater до честного состояния: blocking checks, repeatable build, signed/update-ready или explicit disable.

**Quick Wins (1-2 часа):**

1. Починить tuple unpack bug в sync/async web.
2. Добавить web regression tests на `action-items/update`.
3. Обновить `web-api.md` под nested error envelope и async `/api/analyze/stream`.
4. Синхронизировать desktop version metadata (`package.json`, `tauri.conf.json`, `Cargo.toml`, Flatpak manifest).
5. Сделать `uv sync --extra all` действительно full-stack или переименовать/уточнить профиль в docs.

**Top risks:**

- Silent regressions в untested web/async endpoints.
- Ложное ощущение готовности из-за optimistic docs/plans.
- Memory/perf cliffs на Linux-хостах около 8 GB RAM.
- Packaging/updater ambiguity перед релизом.
- Затянувшийся accepted risk по `CVE-2025-69872` (#65).

---

## 12. Как давать Cursor максимум эффективности без потери качества

- **Не просить “сделай всё подряд”.** Лучший throughput даёт `coherent batch`: 1 главный issue/block + до 2 тесно связанных подблока в том же subsystem.
- **Лучший формат batches:** `bugfix + regression tests + docs`, `coverage hotspot + refactor + targeted tests`, `version sync + release docs + install smoke`.
- **Худший формат batches:** desktop packaging + RAG + calendar; security + UI polish + infra refactor в одной сессии.
- **Источник очереди работ:** сначала [next-iteration-focus.md](next-iteration-focus.md), затем [planning.md](planning.md) / [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1), затем `plans.md` / `audit.md`.
- **Готовый prompt и batching strategy:** [cursor.md](cursor.md), [next-iteration-focus.md](next-iteration-focus.md), [agent-context.md](agent-context.md).

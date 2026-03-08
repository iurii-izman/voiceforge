# Итог по проекту VoiceForge (12 разделов)

Единый свод: планы vs код, что сделано, что осталось вам, Sonar/GitHub, приоритеты. Обновлено: 2026-03-08 (сверено по текущему репо).

---

## 1. Что подтверждено по репо

- **Сверка планов с кодом:** подтверждено, что блоки 44 (история буфера), 46 (слайд-панель настроек), 49 (виджет «Последний анализ»), 68 (streaming LLM), 71 (Whisper API), 75 (поиск RAG), 79 (создание события из сессии) уже реализованы в коде.
- **Обновлены документы:** в [backlog-and-actions.md](../plans/backlog-and-actions.md) отмечены как реализованные блоки 44, 46, 49 (плюс ранее 35, 68, 71, 75, 79). В [roadmap-100-blocks.md](../plans/roadmap-100-blocks.md) секция «Не реализовано» приведена в соответствие (66 — только prompt caching; 68, 71, 79 — зачёркнуты).
- **Правки по Sonar:** optional chain в `desktop/src/main.js` (S6582); dict comprehension в `scripts/git_credential_keyring_pat.py` (S7494); NOSONAR для неиспользуемых параметров интерфейса в `stt/openai_whisper.py` (S1172) и для вызова fixture в `tests/test_benchmark_pipeline.py` (S5864).
- **После audit-driven batches дополнительно подтверждено:** `#97` закрыт кодом и regression tests для `/api/action-items/update`; `#98` закрыт через `web-async` в full-stack extras и `scripts/check_release_metadata.py`; `#99` продвинут дальше и из `omit` теперь выведены `server.py` и `rag/watcher.py`; `#100` подтверждён process-scoped cache для `Diarizer`/`HybridSearcher` и редкой ring persistence; `#101` подтверждён desktop release gate (`desktop-release-gate-matrix.md`, `npm run e2e:native`, updater contract check).

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
- **Coverage blind spots:** после `server.py` и `rag/watcher.py` в `omit` всё ещё остаются `main.py`, `core/daemon.py`, `llm/router.py`, `stt/diarizer.py`, тяжёлые `rag/*`, `llm/local_llm.py`.
- **verify_pr/bandit:** при желании полного зелёного — доработать оставшиеся предупреждения bandit.
- **Pre-commit на хосте:** без Python 3.12 использовать `git commit/push --no-verify`; полный pre-commit в toolbox 43.

---

## 9. Промпт для следующего чата

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Фокус: @docs/runbooks/next-iteration-focus.md. Итог по проекту: @docs/runbooks/PROJECT-STATUS-SUMMARY.md.

Режим: автопилот. Ключи только в keyring (сервис voiceforge). Fedora Atomic, toolbox 43; uv sync --extra all. В конце сессии: тесты (uv run pytest … -q --tb=line или лёгкое подмножество при OOM), коммит и пуш из корня репо (Conventional Commits, Closes #N где уместно), обновить next-iteration-focus, выдать промпт для следующего чата.

Задача: По PROJECT-STATUS-SUMMARY разд. 3–4 и 7–8 — следующий приоритет: coverage blind spots (`core/daemon.py` или `llm/router.py`) отдельным coherent batch, либо Sonar S3776, либо ручные release/desktop шаги из MANUAL-AND-CANNOT-DO.
```

---

## 10. Deep audit delta (2026-03-08)

Базовый clean-room audit давал **~71.3/100**. После уже подтверждённых закрытых batches `#97–#101`, вывода `rag/watcher.py` из `omit` и актуализации release/docs текущая evidence-based оценка по репо — **~75.0/100**. Реалистичный эталон для этой системы остаётся **~86.5/100**. Сильные стороны: security baseline, observability, breadth of product surface. Главные просадки теперь сместились в structural hotspots, honest coverage, manual release evidence и docs drift.

| Направление | Текущее | Эталон | Gap | Ключевой вывод |
|-------------|---------|--------|-----|----------------|
| Core architecture & module boundaries | 63 | 84 | 21 | Главный structural gap всё ещё в крупных hotspot-модулях: `main.py`, `daemon.py`, `server.py`, `router.py`, `desktop/src/main.js` |
| Audio / STT / diarization | 76 | 86 | 10 | Path стал стабильнее, но lifecycle/perf доказан не полностью и diarization остаётся дорогим |
| RAG / data / storage | 78 | 88 | 10 | RAG функционально силён; watcher покрыт честнее, но restore/search lifecycle ещё не fully proved |
| LLM / prompts / PII | 75 | 87 | 12 | Guardrails хорошие; router coverage, policy centralization и non-Claude prompt caching всё ещё ограничивают зрелость |
| Interfaces & integrations | 73 | 85 | 12 | Web bug и docs/API drift по `action-items/update` закрыты, но contract parity между sync/async/desktop надо удерживать тестами |
| Testing & QA | 76 | 86 | 10 | Coverage policy стала честнее, но confidence всё ещё строится на targeted subsets и blind spots в hotspot-модулях |
| Security & dependency hygiene | 79 | 89 | 10 | Baseline сильный; открытые риски не изменились: `#65` и local data-at-rest posture |
| Observability & runtime ops | 78 | 88 | 10 | Инструментация хорошая для alpha, но live Jaeger/runtime evidence ещё не собран end-to-end |
| CI/CD & release / packaging | 80 | 87 | 7 | Metadata/updater contract и desktop release gate оформлены лучше, но signed/manual release proof всё ещё вне CI |
| Documentation & governance | 72 | 86 | 14 | Summary/runbooks стали ближе к коду, но stale refs, version drift и active-vs-archive hygiene ещё требуют sweep |

**Новые рабочие блоки на GitHub Project:** [#104](https://github.com/iurii-izman/voiceforge/issues/104) core architecture, [#105](https://github.com/iurii-izman/voiceforge/issues/105) audio/STT, [#106](https://github.com/iurii-izman/voiceforge/issues/106) RAG lifecycle, [#107](https://github.com/iurii-izman/voiceforge/issues/107) LLM/prompts/PII, [#108](https://github.com/iurii-izman/voiceforge/issues/108) interface parity, [#109](https://github.com/iurii-izman/voiceforge/issues/109) testing/QA, [#110](https://github.com/iurii-izman/voiceforge/issues/110) security hygiene, [#111](https://github.com/iurii-izman/voiceforge/issues/111) observability evidence, [#112](https://github.com/iurii-izman/voiceforge/issues/112) release/packaging proof, [#113](https://github.com/iurii-izman/voiceforge/issues/113) docs/governance sweep.

**Подтверждённые hotspots:** [src/voiceforge/main.py](/home/user/Projects/voiceforge/src/voiceforge/main.py), [src/voiceforge/core/daemon.py](/home/user/Projects/voiceforge/src/voiceforge/core/daemon.py), [src/voiceforge/web/server.py](/home/user/Projects/voiceforge/src/voiceforge/web/server.py), [src/voiceforge/web/server_async.py](/home/user/Projects/voiceforge/src/voiceforge/web/server_async.py), [src/voiceforge/llm/router.py](/home/user/Projects/voiceforge/src/voiceforge/llm/router.py), [desktop/src/main.js](/home/user/Projects/voiceforge/desktop/src/main.js).

**Текущие evidence gaps:** локально не гонялся `cargo-audit`, не запускался полный `pytest tests/` из-за OOM-risk, не проверялись live Jaeger traces и updater signing flow. Packaging/updater contract уже подтверждён runbook-ами и `check_release_metadata.py`, но финальный signed-release flow остаётся manual evidence gap.

---

## 11. Critical Path, Quick Wins, top risks

**Critical Path (в порядке, актуализировано):**

1. Coverage blind spots после уже закрытого `#99`: `core/daemon.py`, `llm/router.py`, затем `main.py` отдельными cheap helper/smoke batches.
2. `#65` CVE: дождаться фикса upstream и снять `--ignore-vuln` без регресса CI.
3. Sonar S3776: постепенно выносить сложные ветки из `daemon.py`, `main.py`, `router.py`, `server_async.py`, `desktop/src/main.js`.
4. Manual release evidence: `cargo-audit`, live Jaeger traces, signed updater path, desktop native release gate на реальном окружении.
5. Prompt caching для non-Claude (roadmap 19 / block 66 continuation): пока research/documented, но не productized.

**Quick Wins (1-2 часа):**

1. Взять `core/daemon.py` как следующий ROI-candidate из `omit` и добавить узкий helper/smoke batch.
2. Либо взять `llm/router.py` тем же форматом: helper-level tests без тяжёлого LLM loop.
3. При желании полного quality signal добрать оставшиеся bandit/Sonar quick-fixes без cross-cutting rewrite.
4. Для release confidence отдельно прогнать `python scripts/check_release_metadata.py`.
5. Для desktop confidence отдельно прогнать `cd desktop && npm run e2e:native` в toolbox/local release path.

**Top risks:**

- Silent regressions в untested web/async endpoints.
- Ложное ощущение готовности из-за optimistic docs/plans.
- Memory/perf cliffs на Linux-хостах около 8 GB RAM.
- Packaging/updater manual proof всё ещё дороже и частично вне CI.
- Затянувшийся accepted risk по `CVE-2025-69872` (#65).

---

## 12. Как давать Cursor максимум эффективности без потери качества

- **Не просить “сделай всё подряд”.** Лучший throughput даёт `coherent batch`: 1 главный issue/block + до 2 тесно связанных подблока в том же subsystem.
- **Лучший формат batches:** `bugfix + regression tests + docs`, `coverage hotspot + refactor + targeted tests`, `version sync + release docs + install smoke`.
- **Худший формат batches:** desktop packaging + RAG + calendar; security + UI polish + infra refactor в одной сессии.
- **Источник очереди работ:** сначала [next-iteration-focus.md](next-iteration-focus.md), затем [planning.md](planning.md) / [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1), затем `plans.md` / `audit.md`.
- **Актуальные audit-driven items на board:** [#96](https://github.com/iurii-izman/voiceforge/issues/96), [#97](https://github.com/iurii-izman/voiceforge/issues/97), [#98](https://github.com/iurii-izman/voiceforge/issues/98), [#99](https://github.com/iurii-izman/voiceforge/issues/99), [#100](https://github.com/iurii-izman/voiceforge/issues/100), [#101](https://github.com/iurii-izman/voiceforge/issues/101) уже закрыты; следующий practical queue теперь идёт не от этих карточек, а от оставшихся blind spots, Sonar debt и manual release evidence gaps.
- **Готовый prompt и batching strategy:** [cursor.md](cursor.md), [next-iteration-focus.md](next-iteration-focus.md), [agent-context.md](agent-context.md).

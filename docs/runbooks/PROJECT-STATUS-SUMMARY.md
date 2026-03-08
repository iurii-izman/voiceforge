# Итог по проекту VoiceForge (12 разделов)

Единый свод: планы vs код, что сделано, что осталось вам, Sonar/GitHub, приоритеты. Обновлено: 2026-03-08 (сверено по текущему репо).

---

## 1. Что подтверждено по репо

- **Сверка планов с кодом:** подтверждено, что блоки 44 (история буфера), 46 (слайд-панель настроек), 49 (виджет «Последний анализ»), 68 (streaming LLM), 71 (Whisper API), 75 (поиск RAG), 79 (создание события из сессии) уже реализованы в коде.
- **Обновлены документы:** в [backlog-and-actions.md](../plans/backlog-and-actions.md) отмечены как реализованные блоки 44, 46, 49 (плюс ранее 35, 68, 71, 75, 79). В [roadmap-100-blocks.md](../plans/roadmap-100-blocks.md) секция «Не реализовано» приведена в соответствие (66 — только prompt caching; 68, 71, 79 — зачёркнуты).
- **Правки по Sonar:** optional chain в `desktop/src/main.js` (S6582); dict comprehension в `scripts/git_credential_keyring_pat.py` (S7494); NOSONAR для неиспользуемых параметров интерфейса в `stt/openai_whisper.py` (S1172) и для вызова fixture в `tests/test_benchmark_pipeline.py` (S5864).
- **После audit-driven batches дополнительно подтверждено:** `#97` закрыт кодом и regression tests для `/api/action-items/update`; `#98` закрыт через `web-async` в full-stack extras и `scripts/check_release_metadata.py`; `#99` продвинут дальше и из `omit` теперь выведены `server.py` и `rag/watcher.py`; `#100` подтверждён process-scoped cache для `Diarizer`/`HybridSearcher` и редкой ring persistence; `#101` подтверждён desktop release gate (`desktop-release-gate-matrix.md`, `npm run e2e:native`, updater contract check).
- **Follow-up blocks по deep audit тоже подтверждены:** `#104` закрыт extraction в `core/daemon.py` (`_event_description_from_detail` + tests), `#105` и `#106` закрыты runbook [lifecycle-smoke.md](lifecycle-smoke.md), `#107` подтверждён helper-level router tests, `#108` — parity suite `tests/test_web_contract_parity.py`, `#109` — `tests/test_daemon_helpers.py`, `#110` — раздел data-at-rest/dependency hygiene в `security-and-dependencies.md`, `#111` — trace evidence checklist в `observability-alerts.md`, `#112` — release proof section в `release-and-quality.md`, `#113` — docs/status sync sweep в runbooks.

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
- **Блок D (GitHub):** #65 оставить открытым до фикса upstream; стратегическую очередь вести через `#114-#123` на Project `#1`. `#50` уже закрыт и в активный queue не возвращать. По verify_pr/bandit — решить, добиваться ли полного зелёного (см. блок E).
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
- **Issues:** открытый внешний риск по-прежнему **#65** (CVE — ждём upstream). Новый стратегический queue для движения `76.5 -> 100` оформлен как **#114-#123**: hotspot decomposition, honest coverage, RAG/audio confidence, contract drift, security/ops/release/docs evidence. **#50** (macOS/WSL2) закрыт и снят с активного скоупа.
- **Доска:** [VoiceForge Board](https://github.com/users/iurii-izman/projects/1). При работе по issue — In Progress; при Closes #N — Done. Команды и ID полей: [planning.md](planning.md).
- **Dependabot:** при CVE #65 — отклонить с комментарием из security-and-dependencies.md или скрипт `uv run python scripts/dependabot_dismiss_moderate.py`.

---

## 7. Рекомендации по приоритетам

1. **Первый ROI-приоритет:** взять **#115** и честно вытащить `llm/router.py` из blind spot через helper/smoke/regression batch и локальную coverage-проверку.
2. **Следом:** взять **#116** (`core/daemon.py` behavioral coverage), затем **#114** (`main.py` / `server_async.py` hotspot decomposition) без смешивания surfaces.
3. **Параллельный внешний риск:** при появлении фикса CVE **#65** обновить зависимости и убрать `--ignore-vuln`.
4. **После code-heavy P0:** двигать manual/evidence blocks **#121** и **#122** и только затем более широкие P1 (`#117-#120`, `#123`) по capacity.

---

## 8. Критичные/важные проблемы на следующую итерацию

- **#65 CVE:** следить за upstream (diskcache/instructor); при фиксе — обновить и убрать ignore.
- **Новый practical queue:** сначала **#115** (`llm/router.py` out of blind spot), затем **#116** (`core/daemon.py` behavioral coverage), затем **#114** (`main.py` / `server_async.py` hotspot decomposition) как три верхних ROI-блока.
- **Sonar S3776:** 8 мест с высокой когнитивной сложностью — рефакторинг по одному или принять по решению. После уже закрытого `#104` следующий structural hotspot batch теперь зафиксирован отдельным issue **#114**.
- **Coverage blind spots:** после `server.py` и `rag/watcher.py` в `omit` всё ещё остаются `main.py`, `core/daemon.py`, `llm/router.py`, `stt/diarizer.py`, тяжёлые `rag/*`, `llm/local_llm.py`. Первые два coverage-driven блока в новой очереди: **#115** и **#116**.
- **verify_pr/bandit:** при желании полного зелёного — доработать оставшиеся предупреждения bandit.
- **Pre-commit на хосте:** без Python 3.12 использовать `git commit/push --no-verify`; полный pre-commit в toolbox 43.

---

## 9. Промпт для следующего чата

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Фокус: @docs/runbooks/next-iteration-focus.md. Итог по проекту: @docs/runbooks/PROJECT-STATUS-SUMMARY.md.

Режим: автопилот. Ключи только в keyring (сервис voiceforge). Fedora Atomic, toolbox 43; uv sync --extra all. В конце сессии: тесты (uv run pytest … -q --tb=line или лёгкое подмножество при OOM), коммит и пуш из корня репо (Conventional Commits, Closes #N где уместно), обновить next-iteration-focus, выдать промпт для следующего чата.

Задача: взять верхний coherent batch из новой стратегической очереди `#114-#123`. Первый приоритет: **#115** — `src/voiceforge/llm/router.py` out of blind spot. Сделать узкий helper/smoke/regression batch вокруг router policy/fallback/provider-selection paths, локально проверить coverage с временно снятым `omit` именно для `llm/router.py` и менять `pyproject.toml` только при честном проценте.
```

---

## 10. Deep audit delta (2026-03-08)

Базовый clean-room audit давал **~71.3/100**. После повторной сверки по текущему репо, уже закрытых batches `#97–#113`, вывода `rag/watcher.py` из `omit`, daemon helper coverage, parity/runbook cleanup и release/docs updates текущая evidence-based оценка по репо — **~76.5/100**. Реалистичный эталон для этой системы остаётся **~86.5/100**. Сильные стороны: security baseline, observability, breadth of product surface. Главные просадки теперь сместились в structural hotspots, honest coverage, manual release evidence и остаточный docs drift.

| Направление | Текущее | Эталон | Gap | Ключевой вывод |
|-------------|---------|--------|-----|----------------|
| Core architecture & module boundaries | 64 | 84 | 20 | После `#104` есть один cheap extraction в `daemon.py`, но главные structural hotspots всё ещё в `main.py`, `daemon.py`, `server.py`, `router.py`, `desktop/src/main.js` |
| Audio / STT / diarization | 77 | 86 | 9 | Lifecycle smoke уже задокументирован (`#105`), но perf/diarization path всё ещё дорогой и частично manual-only |
| RAG / data / storage | 79 | 88 | 9 | `rag/watcher.py` покрыт честнее, lifecycle/restore smoke добавлен (`#106`), но search/indexer-heavy paths всё ещё не fully proved |
| LLM / prompts / PII | 76 | 87 | 11 | Router helper coverage и policy fallback checks улучшены (`#107`), но `router.py` всё ещё вне report и non-Claude caching остаётся research |
| Interfaces & integrations | 75 | 85 | 10 | После `#108` есть parity suite для sync/async contracts; основной риск теперь не bug, а drift при следующих изменениях |
| Testing & QA | 78 | 86 | 8 | `server.py` и `rag/watcher.py` уже выведены из omit, `daemon.py` получил helper suite (`#109`), но общий confidence всё ещё subset-driven |
| Security & dependency hygiene | 80 | 89 | 9 | `#110` добавил честкий dependency/data-at-rest checklist, но `#65` и отсутствие at-rest encryption по-прежнему открыты |
| Observability & runtime ops | 79 | 88 | 9 | `#111` оформил trace evidence path, но live Jaeger/runtime proof всё ещё выполняется вручную и не собран в этом чате |
| CI/CD & release / packaging | 81 | 87 | 6 | `#112` усилил release proof beyond metadata contract, но signed updater/native release evidence всё ещё не автоматизированы |
| Documentation & governance | 75 | 86 | 11 | После `#113` summary/runbooks стали ближе к коду, но drift ещё не нулевой и DOCS hygiene требует регулярной поддержки |

**Deep-audit follow-up blocks:** [#104](https://github.com/iurii-izman/voiceforge/issues/104), [#105](https://github.com/iurii-izman/voiceforge/issues/105), [#106](https://github.com/iurii-izman/voiceforge/issues/106), [#107](https://github.com/iurii-izman/voiceforge/issues/107), [#108](https://github.com/iurii-izman/voiceforge/issues/108), [#109](https://github.com/iurii-izman/voiceforge/issues/109), [#110](https://github.com/iurii-izman/voiceforge/issues/110), [#111](https://github.com/iurii-izman/voiceforge/issues/111), [#112](https://github.com/iurii-izman/voiceforge/issues/112), [#113](https://github.com/iurii-izman/voiceforge/issues/113) уже закрыты и остаются историей предыдущего цикла. Текущий score-to-100 queue теперь формализован отдельными стратегическими блоками [#114](https://github.com/iurii-izman/voiceforge/issues/114), [#115](https://github.com/iurii-izman/voiceforge/issues/115), [#116](https://github.com/iurii-izman/voiceforge/issues/116), [#117](https://github.com/iurii-izman/voiceforge/issues/117), [#118](https://github.com/iurii-izman/voiceforge/issues/118), [#119](https://github.com/iurii-izman/voiceforge/issues/119), [#120](https://github.com/iurii-izman/voiceforge/issues/120), [#121](https://github.com/iurii-izman/voiceforge/issues/121), [#122](https://github.com/iurii-izman/voiceforge/issues/122), [#123](https://github.com/iurii-izman/voiceforge/issues/123); первый practical execution order: **#115 -> #116 -> #114**.

**Подтверждённые hotspots:** [src/voiceforge/main.py](/home/user/Projects/voiceforge/src/voiceforge/main.py), [src/voiceforge/core/daemon.py](/home/user/Projects/voiceforge/src/voiceforge/core/daemon.py), [src/voiceforge/web/server.py](/home/user/Projects/voiceforge/src/voiceforge/web/server.py), [src/voiceforge/web/server_async.py](/home/user/Projects/voiceforge/src/voiceforge/web/server_async.py), [src/voiceforge/llm/router.py](/home/user/Projects/voiceforge/src/voiceforge/llm/router.py), [desktop/src/main.js](/home/user/Projects/voiceforge/desktop/src/main.js).

**Текущие evidence gaps:** локально не гонялся `cargo-audit`, не запускался полный `pytest tests/` из-за OOM-risk, не проверялись live Jaeger traces и updater signing flow. Packaging/updater contract уже подтверждён runbook-ами и `check_release_metadata.py`, но финальный signed-release flow остаётся manual evidence gap.

---

## 11. Critical Path, Quick Wins, top risks

**Critical Path (в порядке, актуализировано):**

1. **#115**: вытащить `llm/router.py` из blind spot честным helper/smoke/regression batch и локальной coverage-проверкой с временно снятым `omit`.
2. **#116**: поднять `core/daemon.py` от helper-only coverage к behavioral coverage вокруг `listen/analyze/status/settings` или retention/backup-adjacent paths.
3. **#114**: продолжить structural cleanup через extraction batches в `main.py` и `server_async.py`, чтобы снижать architecture/S3776 debt без cross-cutting rewrite.
4. `#65` CVE: дождаться фикса upstream и снять `--ignore-vuln` без регресса CI.
5. Manual evidence blocks **#121** и **#122**: `cargo-audit`, live Jaeger traces, signed updater path, desktop native release gate на реальном окружении.
6. Prompt caching для non-Claude (roadmap 19 / block 66 continuation): пока research/documented, но не productized.

**Quick Wins (1-2 часа):**

1. Взять **#115** и покрыть `llm/router.py` cheap helper/smoke tests без тяжёлого LLM loop.
2. Следом взять **#116** и расширить `core/daemon.py` до behavioral coverage batch.
3. Для release confidence отдельно прогнать **#122** lightweight proof steps: `python scripts/check_release_metadata.py` и manual/native gate checklist.
4. Для observability confidence отдельно оформить **#121** через Jaeger/runtime evidence checklist.
5. При желании полного quality signal добрать оставшиеся bandit/Sonar quick-fixes без cross-cutting rewrite.

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
- **Актуальные strategic items на board:** [#114](https://github.com/iurii-izman/voiceforge/issues/114), [#115](https://github.com/iurii-izman/voiceforge/issues/115), [#116](https://github.com/iurii-izman/voiceforge/issues/116), [#117](https://github.com/iurii-izman/voiceforge/issues/117), [#118](https://github.com/iurii-izman/voiceforge/issues/118), [#119](https://github.com/iurii-izman/voiceforge/issues/119), [#120](https://github.com/iurii-izman/voiceforge/issues/120), [#121](https://github.com/iurii-izman/voiceforge/issues/121), [#122](https://github.com/iurii-izman/voiceforge/issues/122), [#123](https://github.com/iurii-izman/voiceforge/issues/123) плюс внешний риск [#65](https://github.com/iurii-izman/voiceforge/issues/65). Practical queue начинается с **#115 -> #116 -> #114**.
- **Готовый prompt и batching strategy:** [cursor.md](cursor.md), [next-iteration-focus.md](next-iteration-focus.md), [agent-context.md](agent-context.md).

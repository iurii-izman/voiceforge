# Итог по проекту VoiceForge (9 разделов)

Единый свод: планы vs код, что сделано, что осталось вам, Sonar/GitHub, приоритеты. Обновлено: 2026-03-07.

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
  - Блок 66: доработка prompt caching для не-Claude (LiteLLM/провайдеры) — по документации API.
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

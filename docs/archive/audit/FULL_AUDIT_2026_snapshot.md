# Полный аудит VoiceForge: реализация, документация, код (2026)

Дата: 2026-03-04. Дополняет снимок аудита [PROJECT_AUDIT_AND_ROADMAP_2026.md](PROJECT_AUDIT_AND_ROADMAP_2026.md) и [audit-to-github-map_2026_snapshot.md](audit-to-github-map_2026_snapshot.md). Цель: оценка степени реализации по всем «фронтам» и 10 блоков по усилению до 100%.

---

## 1. Оценка степени реализации

### 1.1 Функциональные модули (код)

| Подсистема | Модули | Реализация | Слабости | Оценка |
|------------|--------|------------|----------|--------|
| **audio/** | capture, buffer, smart_trigger | Захват PipeWire, кольцевой буфер, VAD работают. | capture/buffer в omit coverage; зависимость от pw-record. | 85% |
| **stt/** | transcriber, diarizer, streaming | faster-whisper, pyannote, streaming STT реализованы. | diarizer в omit; OOM-риск; нет бенчмарков. | 80% |
| **rag/** | embedder, indexer, searcher, parsers, watcher, query_keywords | ONNX, FTS5+vector, парсеры (PDF, DOCX, MD, ODT, RTF), watcher. | Почти все rag-модули в omit; нет semantic chunking. | 75% |
| **llm/** | router, schemas, pii_filter, prompt_loader, cache, local_llm | LiteLLM, Instructor, 5 шаблонов, PII, кеш, Ollama. | Нет circuit breaker; нет hash-валидации промптов; local_llm в omit. | 78% |
| **core/** | config, pipeline, daemon, metrics, transcript_log, observability, secrets, contracts, tracing | Конфиг, пайплайн, D-Bus, метрики, БД, observability, tracing. | pipeline, daemon, dbus_service, transcript_log в omit; нет периодического purge; нет CLI backup. | 82% |
| **web/** | server.py | HTTP API, Telegram webhook, /metrics, /health, /ready, X-Trace-Id. | stdlib HTTPServer (однопоточный); server в omit; ошибки не в едином формате. | 72% |
| **calendar/** | caldav_poll.py | CalDAV polling, keyring. | caldav_poll в omit. | 80% |
| **cli/** | status_helpers, history_helpers | status, doctor, history, сессии, экспорт. | Часть логики в main.py; helpers покрыты частично. | 85% |
| **i18n/** | __init__, ru.json, en.json | RU/EN, typer help. | — | 95% |

**Итог по коду:** ~80%. Критичные пробелы: покрытие тестами (много omit), circuit breaker, периодический purge, CLI backup, async web, единый формат ошибок API.

---

### 1.2 Документация

| Область | Файлы | Реализация | Слабости | Оценка |
|---------|-------|------------|----------|--------|
| **Runbooks** | agent-context, next-iteration-focus, config-env, keyring, installation, bootstrap, security, release, telegram, calendar, web-api, observability-alerts, prompt-management, dependencies, git-github-practices, planning, cursor | 20+ runbooks, RU+EN. | Часть runbooks может отставать от кода (tracing, /ready). | 92% |
| **ADR** | 0001–0006 (scope, action_items, version, desktop, telegram, calendar) | Все ключевые решения зафиксированы. | — | 95% |
| **Architecture** | overview, README | C4-подобные диаграммы, пайплайн. | Можно добавить диаграмму данных (БД, миграции). | 88% |
| **Аудит и roadmap** | archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026, audit-to-github-map, roadmap-priority, development-plan | Полный аудит (архив), маппинг на issues, приоритеты 1–19. | Аудит от 2026-02-26; после #61 (tracing) нужна точечная синхронизация. | 90% |
| **Индекс** | DOCS-INDEX.md | Единый индекс, модерация актуальности. | — | 95% |
| **First meeting / quickstart** | first-meeting-5min (RU/EN), quickstart | Сценарий за 5 минут. | — | 90% |

**Итог по документации:** ~92%. Документация — сильная сторона; поддерживать актуальность после каждого крупного изменения (tracing, circuit breaker, backup).

---

### 1.3 Тесты и качество

| Область | Реализация | Слабости | Оценка |
|---------|------------|----------|--------|
| **Unit/интеграция** | 150 тестов, 19 файлов; eval (ROUGE-L), db-migrations, cli-contract, pipeline memory guard, STT integration, web smoke, tracing. | Много модулей в omit (main, pipeline, web/server, daemon, dbus, diarizer, rag/*, transcript_log, caldav_poll, local_llm); fail_under=63. | 65% |
| **Coverage** | branch=true, exclude_lines. | Цель 80% недостигнута; 20+ модулей в omit. | 55% |
| **Eval** | tests/eval/, golden samples, ROUGE-L, LLM-judge. | Eval job в CI есть; LLM-judge не в CI (нужен ключ). | 75% |
| **CI** | quality (ruff, mypy, pytest), cli-contract, eval, db-migrations; Sonar, CodeQL (по аудиту — blocking). | check_new_code_coverage с низким порогом (20%); без optional deps часть тестов падает. | 78% |

**Итог по тестам/качеству:** ~68%. Главный разрыв — реальное покрытие критичного runtime (pipeline, daemon, web, RAG, STT) и подъём fail_under до 80%.

---

### 1.4 Observability и надёжность

| Область | Реализация | Слабости | Оценка |
|---------|------------|----------|--------|
| **Логи** | structlog везде; trace_id в context (CLI, web, run_analyze_pipeline); TimeStamper. | — | 90% |
| **Метрики** | 6 Prometheus метрик, /metrics. | Нет развёрнутого стека (Prometheus + Grafana); нет alerts. | 70% |
| **Трассировка** | trace_id, X-Trace-Id в ответах web. | Нет OpenTelemetry/span'ов. | 75% |
| **Надёжность** | Timeouts, fallbacks, budget, retry. | Нет circuit breaker. | 70% |
| **Health** | /health, /ready (проверка БД). | — | 95% |

**Итог по observability/надёжности:** ~80%. Не хватает: circuit breaker, monitoring stack (Grafana + alerts), при желании — OTel.

---

### 1.5 Безопасность и данные

| Область | Реализация | Слабости | Оценка |
|---------|------------|----------|--------|
| **Секреты** | keyring (voiceforge), список в keyring-keys-reference. | — | 95% |
| **Сканирование** | gitleaks, bandit, pip-audit, semgrep, CodeQL. | CVE-2025-69872 в ignore. | 85% |
| **PII** | Режимы OFF/EMAIL_ONLY/ON, GLiNER. | — | 90% |
| **Retention/backup** | purge_before при старте демона и в history --purge-before; backup только при миграции. | Нет периодического purge (timer); нет CLI backup. | 60% |

**Итог по безопасности/данным:** ~82%. Критично: периодический purge, команда backup, снятие CVE-ignore по возможности.

---

### 1.6 Сводная оценка по «фронтам»

| Фронт | Оценка | Цель 100% |
|-------|--------|-----------|
| Функциональные модули (код) | 80% | Убрать omit по мере покрытия; circuit breaker; backup; единый формат ошибок; при желании async web. |
| Документация | 92% | Держать индекс и runbooks в актуальности после фич. |
| Тесты и coverage | 68% | Поднять покрытие включённых модулей; вывести модули из omit + тесты; fail_under 80%. |
| Observability и надёжность | 80% | Circuit breaker; monitoring stack; при желании OTel. |
| Безопасность и данные | 82% | Периодический purge; CLI backup; решить CVE. |

**Общая степень реализации (взвешенно):** ~80%. Самые слабые точки: **тесты/coverage**, **retention/backup**, **circuit breaker**, **monitoring stack**, **формат ошибок API**.

---

## 2. Десять блоков по усилению (до 100%)

Акцент на самых слабых точках; блоки можно выполнять параллельно по подзадачам, где это возможно.

---

### Блок 1: Покрытие тестами и вывод из omit (цель: 80%+ реальный coverage)

**Проблема:** Много критичного кода в omit; fail_under=63; реальное покрытие runtime неизвестно.

**Входы:** pyproject.toml (omit, fail_under), тесты для daemon, pipeline, web, RAG, STT, cli helpers, core/metrics, core/daemon.

**Шаги:**
1. Добавить тесты для модулей с наименьшим риском: core/metrics, cli/history_helpers, cli/status_helpers, rag/parsers (уже частично есть).
2. Поочерёдно выводить из omit по одному модулю (или группе), добавляя unit/mock-тесты: model_manager, smart_trigger (уже есть test_daemon_streaming_smart_trigger_model_manager), затем pipeline (mock-integration), daemon (mock D-Bus), web (уже есть smoke — расширить), transcript_log (миграции уже тестируются), caldav_poll, local_llm.
3. Поднимать fail_under с 63 до 70, затем до 80.
4. Оставить в omit только то, что обоснованно (например, __main__.py, тяжёлые интеграции с железом).

**Критерий 100%:** Все ключевые модули в отчёте coverage; fail_under=80; нет «мёртвых» omit для продакшен-путей.

**Связь с issues:** #56.

---

### Блок 2: Circuit breaker и устойчивость LLM (цель: быстрый отказ при сбоях провайдера)

**Проблема:** При стабильных отказах LLM — лишние retry и расход; нет состояний open/half-open/closed.

**Входы:** llm/router.py, llm/local_llm.py.

**Шаги:**
1. Ввести llm/circuit_breaker.py: состояния closed/open/half-open; порог consecutive failures (например 3); cooldown (например 5 мин); привязка к провайдеру/модели.
2. Обернуть вызовы к внешним LLM и Ollama в circuit breaker.
3. Логировать и при желании экспортировать в метрики (gauge: state per provider).
4. Тесты: смена состояний, поведение при open (skip вызова), half-open (один пробный вызов).

**Критерий 100%:** При 3 подряд сбоях провайдер пропускается на cooldown; метрика/лог состояния; тесты.

**Связь с issues:** #62.

---

### Блок 3: Retention и backup (цель: предсказуемая очистка и сохранность данных)

**Проблема:** Purge только при старте демона и по ручной команде; нет периодического backup.

**Входы:** core/daemon.py, core/transcript_log.py, main.py.

**Шаги:**
1. Периодический purge: в демоне — threading.Timer (раз в 24 ч) или вызов purge_before по расписанию; альтернатива — systemd timer + `voiceforge purge --before YYYY-MM-DD`.
2. CLI `voiceforge backup`: копия transcripts.db, metrics.db, rag.db в каталог с timestamp; опция rotation (хранить последние N).
3. Документировать в runbook: где лежат бэкапы, как восстановить.

**Критерий 100%:** Purge выполняется не реже раз в сутки; команда backup есть и задокументирована; rotation опционально.

**Связь с issues:** #63.

---

### Блок 4: Мониторинг и алертинг (цель: дашборды и алерты по метрикам)

**Проблема:** Метрики есть, дашборд в JSON — не развёрнут; нет alert rules.

**Входы:** docs/grafana-voiceforge-dashboard.json, core/observability.py, web/server.py (/metrics).

**Шаги:**
1. Директория monitoring/: prometheus.yml (scrape /metrics), alerts.yml (например: pipeline_errors_total > 5 за 5m; дневные затраты > 80% бюджета).
2. docker-compose (или инструкция): Prometheus + Grafana; импорт grafana-voiceforge-dashboard.json.
3. Runbook: как поднять стек, куда смотреть при срабатывании алертов.

**Критерий 100%:** Запуск стека по инструкции; дашборд показывает метрики; хотя бы 2 алерта настроены и проверены.

**Связь с issues:** #64.

---

### Блок 5: Единый формат ошибок API (цель: все 4xx/5xx — JSON с code и message)

**Проблема:** В web разные форматы ошибок; analyze иногда возвращает ошибку в 200.

**Входы:** web/server.py.

**Шаги:**
1. Ввести единый формат: `{"error": {"code": "CODE", "message": "..."}}` для всех 4xx/5xx.
2. Ошибки analyze возвращать с подходящим HTTP-кодом (например 422/503), не 200 с error внутри.
3. Обновить web-api runbook и при необходимости клиентов (desktop).

**Критерий 100%:** Любой ответ с ошибкой — JSON с code и message; статус-коды соответствуют семантике.

**Связь с issues:** #69.

---

### Блок 6: Валидация промптов и целостность (цель: детектирование drift, предсказуемый fallback)

**Проблема:** Нет hash-валидации файлов промптов; fallback на hardcoded может быть незаметен.

**Входы:** llm/prompt_loader.py, llm/prompts/, router.py.

**Шаги:**
1. Хранить или генерировать hash (например SHA256) для каждого файла в prompts/; при загрузке проверять (или проверять в CI).
2. При использовании fallback — warning в structlog.
3. CI-check: наличие файлов и при необходимости совпадение hash.

**Критерий 100%:** Drift детектируется; fallback логируется; CI проверяет целостность.

**Связь с issues:** #67.

---

### Блок 7: CVE и зависимости (цель: pip-audit без исключений)

**Проблема:** CVE-2025-69872 в --ignore-vuln.

**Входы:** pyproject.toml, .github/workflows/test.yml, зависимости (diskcache — прямой или транзитивный).

**Шаги:**
1. Выяснить источник diskcache; проверить наличие фикса/альтернативы.
2. Обновить зависимость или заменить; убрать --ignore-vuln.
3. Документировать в dependencies.md/security runbook.

**Критерий 100%:** pip-audit проходит без --ignore-vuln.

**Связь с issues:** #65.

---

### Блок 8: Web-сервер: конкурентность и структура (цель: не блокировать другие запросы; при желании — async)

**Проблема:** stdlib HTTPServer обрабатывает запросы последовательно; длинный /api/analyze блокирует остальное.

**Входы:** web/server.py.

**Шаги (минимальный путь):**
1. ThreadingMixIn + HTTPServer: один запрос — один поток, чтобы /api/status не ждал /api/analyze.
2. Сохранить текущее API и поведение (/health, /ready, X-Trace-Id).

**Шаги (полный путь):**
1. Миграция на async (Starlette/Litestar + uvicorn); перенос маршрутов и middleware (trace_id, ошибки).
2. Тесты и runbook обновить.

**Критерий 100% (минимальный):** Параллельная обработка запросов. Критерий 100% (полный): Async stack, единый формат ошибок, сохранение контракта API.

**Связь с issues:** #66.

---

### Блок 9: Бенчмарки и регрессии производительности (цель: базовые замеры и порог в CI)

**Проблема:** Нет зафиксированных замеров latency/throughput; регрессии не детектируются.

**Входы:** tests/, pytest-benchmark (или аналог).

**Шаги:**
1. Бенчмарки: STT на fixture WAV; RAG search (несколько запросов); при желании — полный pipeline с mock LLM.
2. Сохранить baseline (файл или артефакт CI).
3. В CI (опционально): сравнение с baseline; предупреждение при деградации > N%.

**Критерий 100%:** Есть хотя бы STT и один другой бенчмарк; baseline зафиксирован; при желании — проверка в CI.

**Связь с issues:** #68.

---

### Блок 10: Документация и актуализация (цель: индекс и runbooks соответствуют коду)

**Проблема:** После добавления tracing, /ready, изменений в API часть документов может отставать.

**Входы:** DOCS-INDEX.md, runbooks (config-env, web-api, observability-alerts, installation, keyring), audit-to-github-map, archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.

**Шаги:**
1. Пройти по списку изменений за последние месяцы (tracing, /ready, X-Trace-Id, systemd, версия) и обновить соответствующие runbooks и архитектуру.
2. В audit-to-github-map отметить #61 (trace IDs) как сделанное; при закрытии других issues — обновлять таблицу.
3. В audit-to-github-map и FULL_AUDIT при крупных релизах — обновить дату и ключевые цифры (строки кода, количество тестов, omit); полный снимок в archive/audit при смене фазы.
4. Правило: при добавлении фичи — обновить индекс и затронутый runbook в том же PR.

**Критерий 100%:** Индекс актуален; runbooks отражают текущее поведение (config, API, observability, установка); аудит-таблицы синхронизированы с GitHub issues.

---

## 3. Приоритизация и путь к 100%

Рекомендуемый порядок с учётом зависимостей и «слабых точек»:

1. **Блок 1 (Coverage)** — база для уверенности в изменениях; можно делать параллельно с блоками 2–3.
2. **Блок 2 (Circuit breaker)** — напрямую усиливает надёжность LLM.
3. **Блок 3 (Retention/backup)** — данные и соответствие политике хранения.
4. **Блок 5 (Формат ошибок)** — быстрый выигрыш для API и клиентов.
5. **Блок 6 (Промпты)** — целостность и предсказуемость LLM.
6. **Блок 4 (Мониторинг)** — опирается на уже имеющиеся метрики и trace_id.
7. **Блок 7 (CVE)** — по возможности раньше, зависит от апстрима.
8. **Блок 8 (Web)** — сначала ThreadingMixIn, при необходимости потом async.
9. **Блок 9 (Бенчмарки)** — после стабилизации coverage и основных фич.
10. **Блок 10 (Документация)** — непрерывно; после каждого блока обновлять затронутые разделы.

После закрытия этих блоков оценка по всем фронтам может уверенно приближаться к 95–100% при сохранении текущего объёма функциональности и без учёта опциональных больших шагов (полный async web, OTel, плагины).

---

## 4. Сводная таблица блоков

| # | Блок | Слабые точки | Цель 100% | Issues |
|---|------|--------------|-----------|--------|
| 1 | Покрытие тестами, вывод из omit | Тесты, coverage | fail_under=80, ключевые модули без omit | #56 |
| 2 | Circuit breaker LLM | Надёжность | Состояния, cooldown, метрика/тесты | #62 |
| 3 | Retention + backup | Данные | Периодический purge, CLI backup | #63 |
| 4 | Мониторинг и алерты | Observability | Prometheus+Grafana+alerts, runbook | #64 |
| 5 | Единый формат ошибок API | Web API | Все ошибки JSON {code, message} | #69 |
| 6 | Валидация промптов | LLM, качество | Hash/CI, warning при fallback | #67 |
| 7 | CVE и зависимости | Безопасность | Без --ignore-vuln | #65 |
| 8 | Web: конкурентность / async | Web | Threading или async, без блокировки | #66 |
| 9 | Бенчмарки | Производительность | Baseline, опционально CI | #68 |
| 10 | Документация и актуализация | Документы | Индекс и runbooks в актуальном состоянии | — |

---

*Документ подготовлен по состоянию репозитория на 2026-03-04. Trace IDs (#61) учтены как реализованные.*

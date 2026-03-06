# Аудит VoiceForge (март 2026) — полный текст

**Дата:** 2026-03-05. Актуальный краткий статус и ссылка на этот снимок: [audit/audit.md](../../audit/audit.md). Контекст: [plans.md](../../plans.md), [architecture/overview.md](../../architecture/overview.md).

---

## 1. Executive summary

1. **VoiceForge** — local-first AI-ассистент для аудиовстреч на Linux: PipeWire → STT (faster-whisper) → диаризация (pyannote) → RAG → LLM → SQLite. Alpha 0.2, CLI, daemon (D-Bus), Web UI, Telegram-бот, десктоп (Tauri 2).
2. **Текущее состояние:** большинство W1–W20 в статусе «СДЕЛАНО». Остаётся: #56 (coverage 69→70→80%, omit по модулям), #65 (CVE-2025-69872 до фикса upstream), #66 (полный async web опционально), W17 (когнитивная сложность do_GET/do_POST), Phase D в бэклоге.
3. **Сильные стороны:** документация и runbooks (5/5), CI (eval в CI, Sonar/CodeQL blocking, матрица 3.12/3.13), безопасность (keyring, pip-audit, bandit, gitleaks), observability (trace IDs, /ready, /metrics, monitoring stack, circuit breaker), качество кода (ruff, mypy, graceful degradation по пайплайну).
4. **Главные риски:** реальное покрытие занижено из‑за omit (main, audio/buffer, capture, dbus_service, server, diarizer, rag/*, local_llm); CVE в цепочке instructor→diskcache до фикса; полный pytest может OOM на слабых машинах (pyannote/torch).
5. **Возможности роста:** доведение качества до 100% (coverage, CVE); observability и продуктизация (OTel #71, алерты); расширяемость (plugins #72); упаковка (#73); качество AI (A/B #70, prompt caching #19).
6. **Приоритеты следующей фазы (3–5 направлений):** (1) Качество и надёжность до 100% — #56, #65, при необходимости W17/#66. (2) Observability и продуктизация — OTel #71, алерты/дашборды. (3) Расширяемость — plugins #72. (4) Упаковка и распространение — #73, Flatpak/AppImage. (5) Качество AI и эксперименты — A/B #70, #19.

---

## 2. Системный аудит (шесть областей)

| Область | Оценка | Комментарий |
|--------|:------:|-------------|
| **Код** | 4/5 | Ruff (E,W,F,I,UP,B,SIM,RUF), mypy по core/llm/rag/stt; структура пакетов ясная. Узкое место: do_GET/do_POST в server.py (S3776), часть закрыта. |
| **Тесты** | 3/5 | Eval в CI (tests/eval/), pipeline integration с моками, e2e-smoke, db-migrations, stt-integration. fail_under=69; в omit — main, audio/buffer, capture, dbus_service, server, diarizer, rag/*, local_llm. Полный pytest может OOM. |
| **Доки** | 5/5 | DOCS-INDEX, runbooks, agent-context, next-iteration-focus, audit/plans как источники правды; doc-governance, архив. |
| **CI/CD** | 4/5 | quality (ruff, mypy, pytest, cov), cli-contract, eval, db-migrations, e2e-smoke, stt-integration, security (pip-audit с ignore CVE, bandit). Sonar и CodeQL без continue-on-error. |
| **Безопасность** | 4/5 | Keyring для секретов; pip-audit (CVE-2025-69872 временно ignore до upstream); bandit, gitleaks (weekly), semgrep, CodeQL. Параметризованные запросы к БД. |
| **Observability** | 4/5 | core/tracing.py (trace_id), X-Trace-Id в web; /ready, /metrics; observability.py (Prometheus); monitoring/ (prometheus.yml, alerts.yml, docker-compose); circuit breaker state в метриках. Нет OTel (#71 в бэклоге). |

---

## 3. Блочный аудит

| Блок | Сильные стороны | Узкие места |
|------|-----------------|-------------|
| **audio** | PipeWire capture, ring buffer, smart_trigger с VAD; тесты в test_daemon_streaming_smart_trigger и test_pipeline_integration (_prepare_audio). | buffer.py и capture.py в omit coverage; зависимость от pw-record. |
| **STT** | faster-whisper, streaming STT, diarizer с memory guard; test_stt_integration, test_pipeline_integration (run с моками), test_pipeline_memory_guard. | diarizer в omit; OOM риск при полном прогоне (pyannote/torch). |
| **RAG** | ONNX embedder, FTS5 + vector search, парсеры (MD, HTML, PDF, DOCX, ODT, RTF); test_rag_parsers, test_rag_query_keywords, rag_merge в pipeline test. | Весь rag/* в omit (embedder, indexer, searcher, watcher, dedup, incremental, _onnx_runner). |
| **LLM** | Router (LiteLLM + Instructor), circuit breaker, prompt_loader с hash validation, cache, PII filter; тесты router/circuit_breaker/retry/prompt_loader, eval ROUGE-L. | local_llm в omit. |
| **core** | Pipeline, config, daemon (D-Bus), metrics, transcript_log, observability, tracing, secrets; тесты pipeline_integration, core_metrics, transcript_log, tracing, db_migrations. | dbus_service в omit. |
| **web** | ThreadingMixIn, /ready, /metrics, единый error format, X-Trace-Id; test_web_smoke. | server.py в omit; do_GET/do_POST — высокая когнитивная сложность (W17); полный async (#66) опционально. |
| **calendar** | caldav_poll выведен из omit; test_caldav_poll, test_calendar. | Зависимость от keyring (caldav_*). |
| **desktop** | Tauri 2 + Vite, D-Bus контракт (ADR-0004), Flatpak manifest; README и desktop-build-deps. | Отдельный стек; e2e десктопа опциональны в альфа2. |

---

## 4. Приоритеты следующей фазы

1. **Качество и надёжность до 100%** — поднять fail_under до 70, затем 80; сокращать omit по одному модулю с тестами (#56); убрать ignore CVE после фикса upstream (#65); при необходимости снизить сложность server (W17) или отложить до #66.
2. **Observability и продуктизация** — внедрить OTel (#71) для трассировки; усилить алерты и дашборды (уже есть monitoring/, grafana-voiceforge-dashboard.json).
3. **Расширяемость** — плагины (#72).
4. **Упаковка и распространение** — довести packaging до GA (#73), Flatpak/AppImage (roadmap #14).
5. **Качество AI и эксперименты** — A/B тестирование промптов/моделей (#70); исследование prompt caching для не-Claude (#19).

---

## 5. Рекомендуемые следующие шаги

1. **#56:** Поднять fail_under с 69 до 70 в pyproject.toml после проверки текущего coverage; запланировать вывод из omit по одному модулю (начиная с наименее рискованных).
2. **#65:** Следить за фиксом CVE-2025-69872 в upstream (diskcache/instructor); после фикса убрать `--ignore-vuln CVE-2025-69872` в test.yml и security-weekly.yml.
3. **Phase D:** Вынести в отдельные итерации #70, #71, #72, #73; обновить next-iteration-focus и при необходимости plans.md по приоритету.
4. **Документация:** Следующий шаг в next-iteration-focus — первый пункт из приоритетов (например реализация шага по #56 или выбор issue Phase D).
5. **Тесты:** При OOM запускать подмножество тестов (см. next-iteration-focus); сохранять стабильность pipeline integration с моками.

---

## Ссылки

- Единый статус W1–W20 и Phase A–D: [audit/audit.md](../../audit/audit.md)
- План «оставшееся до 100%»: [REMAINING_AND_PLAN_TO_100_2026.md](REMAINING_AND_PLAN_TO_100_2026.md)
- Полный снимок 2026-02-26: [PROJECT_AUDIT_AND_ROADMAP_2026.md](PROJECT_AUDIT_AND_ROADMAP_2026.md)
- Планы и roadmap: [plans.md](../../plans.md)
- Архитектура: [architecture/overview.md](../../architecture/overview.md)

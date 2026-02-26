# Audit → GitHub: маппинг задач

Источник: `docs/PROJECT_AUDIT_AND_ROADMAP.md` (2026-02-26, commit 6a49402).
Сверка с кодом: 2026-02-26 (агент).

---

## Статус реализации (сверка с кодом)

| # | Weakness / Step | Статус | Доказательство |
|---|----------------|--------|----------------|
| W1 / Step 1 | Eval harness **в CI** | **НЕ СДЕЛАНО** | Нет eval job в test.yml; нет eval-*.yml workflow |
| W2 / Step 2 | Coverage omit убран | **НЕ СДЕЛАНО** | pyproject.toml L111-118: 5 модулей в omit, fail_under=80 |
| W3 / Step 3 | Sonar blocking | **НЕ СДЕЛАНО** | sonar.yml L14,32: `continue-on-error: true` |
| W4 / Step 5 | CodeQL blocking | **НЕ СДЕЛАНО** | codeql.yml L13,26: `continue-on-error: true` |
| W5 | Pipeline integration test | **НЕ СДЕЛАНО** | Нет test_pipeline_integration.py |
| W6 / Step 6 | systemd MemoryMax | **НЕ СДЕЛАНО** | voiceforge.service: нет MemoryMax/MemoryHigh/OOMScoreAdjust |
| W7 / Step 12 | Async web server | **НЕ СДЕЛАНО** | server.py L10: `from http.server import ...` |
| W8 / Step 8 | Circuit breaker | **НЕ СДЕЛАНО** | Нет circuit_breaker.py; нет tracking в router.py |
| W9 / Step 7 | Trace IDs | **НЕ СДЕЛАНО** | Нет trace_id нигде в src/ |
| W10 / Step 13 | Prompt hash validation | **НЕ СДЕЛАНО** | prompt_loader.py: нет hash/SHA256 |
| W11 / Step 9 | Periodic retention purge | **НЕ СДЕЛАНО** | daemon.py: purge_before() только в init, нет Timer |
| W12 / Step 9 | DB backup CLI | **НЕ СДЕЛАНО** | main.py: нет backup команды |
| W13 / Step 11 | CVE-2025-69872 | **НЕ СДЕЛАНО** | test.yml L117: `--ignore-vuln CVE-2025-69872` |
| W14 / Step 6 | /ready endpoint | **НЕ СДЕЛАНО** | server.py: нет /ready |
| W15 / Step 4 | Version inconsistency | **НЕ СДЕЛАНО** | __init__.py: `"0.1.0a1"` vs pyproject.toml `"0.2.0a1"` |
| W16 / Step 5 | .editorconfig | **НЕ СДЕЛАНО** | Файл не существует |
| W17 | Cognitive complexity S3776 | **ЧАСТИЧНО** | do_GET/do_POST ещё if-chains; часть S3776 закрыта |
| W18 / Step 15 | Error responses | **НЕ СДЕЛАНО** | `{"error": msg}` — нет `{"error": {"code":...,"message":...}}` |
| W19 / Step 10 | Alerting / monitoring stack | **НЕ СДЕЛАНО** | Нет monitoring/ директории; нет alerts.yml |
| W20 / Step 14 | Benchmark suite | **НЕ СДЕЛАНО** | Нет benchmark файлов в tests/ |

---

## Roadmap Steps → GitHub Issues

| Phase | Step | Описание | Milestone | Issue |
|-------|------|----------|-----------|-------|
| **A** | 1 | Eval job в CI (ROUGE-L offline) | Phase A | [#55](https://github.com/iurii-izman/voiceforge/issues/55) |
| **A** | 2 | Coverage: убрать omit, тесты, fail_under 70→80 | Phase A | [#56](https://github.com/iurii-izman/voiceforge/issues/56) |
| **A** | 3 | Sonar quality gate blocking | Phase A | [#57](https://github.com/iurii-izman/voiceforge/issues/57) |
| **A** | 4 | Version: importlib.metadata | Phase A | [#58](https://github.com/iurii-izman/voiceforge/issues/58) |
| **A** | 5 | .editorconfig + CodeQL blocking | Phase A | [#59](https://github.com/iurii-izman/voiceforge/issues/59) |
| **B** | 6 | /ready endpoint + systemd MemoryMax | Phase B | [#60](https://github.com/iurii-izman/voiceforge/issues/60) |
| **B** | 7 | Request tracing (trace IDs + structlog) | Phase B | [#61](https://github.com/iurii-izman/voiceforge/issues/61) |
| **B** | 8 | Circuit breaker для LLM провайдеров | Phase B | [#62](https://github.com/iurii-izman/voiceforge/issues/62) |
| **B** | 9 | Periodic purge + DB backup CLI | Phase B | [#63](https://github.com/iurii-izman/voiceforge/issues/63) |
| **B** | 10 | Monitoring stack deploy (Grafana + alerts) | Phase B | [#64](https://github.com/iurii-izman/voiceforge/issues/64) |
| **C** | 11 | Resolve CVE-2025-69872 | Phase C | [#65](https://github.com/iurii-izman/voiceforge/issues/65) |
| **C** | 12 | Async web server (Starlette/Litestar) | Phase C | [#66](https://github.com/iurii-izman/voiceforge/issues/66) |
| **C** | 13 | Prompt versioning + hash validation | Phase C | [#67](https://github.com/iurii-izman/voiceforge/issues/67) |
| **C** | 14 | Benchmark suite (pytest-benchmark) | Phase C | [#68](https://github.com/iurii-izman/voiceforge/issues/68) |
| **C** | 15 | Standardize error responses | Phase C | [#69](https://github.com/iurii-izman/voiceforge/issues/69) |
| **D** | 16 | Model A/B testing framework | Phase D | [#70](https://github.com/iurii-izman/voiceforge/issues/70) |
| **D** | 17 | OpenTelemetry integration | Phase D | [#71](https://github.com/iurii-izman/voiceforge/issues/71) |
| **D** | 18 | Plugin system (custom templates) | Phase D | [#72](https://github.com/iurii-izman/voiceforge/issues/72) |
| **D** | 19 | macOS / WSL2 support | Phase D | [#50](https://github.com/iurii-izman/voiceforge/issues/50) |
| **D** | 20 | Offline packaging GA (AppImage+Flatpak) | Phase D | [#73](https://github.com/iurii-izman/voiceforge/issues/73) |

---

## Закрытые issues (старый план → новый аудит)

Старые issues #32–49, #51–53 закрыты по предыдущему плану развития (development-plan-post-audit-2026.md). Новый аудит (PROJECT_AUDIT_AND_ROADMAP.md) выявил следующий уровень задач — см. таблицу выше.

| Старый issue | Тема | Связь с новым аудитом |
|---|---|---|
| #32 A1 Eval harness | Создание harness + golden samples | Готово; **Step 1** = интеграция в CI |
| #33 A2 Instructor retry | max_retries=3 | Готово; не требует продолжения |
| #34 A3 Unit tests | Тесты daemon/streaming/smart_trigger | Готово; **Step 2** = убрать из omit |
| #35 A4 WAV integration | Тесты с WAV | Готово |
| #36 B1 Observability | Prometheus metrics, /metrics | Готово; **Step 10** = Grafana + alerts deploy |
| #37 B2 pyannote guard | 2GB RAM guard | Готово; **Step 6** = systemd MemoryMax |
| #38 B3 Budget | Pre-call check | Готово |
| #39 B4 IPC envelope | Default envelope | Готово |
| #40 B5 CI cache | uv cache | Готово |
| #41 C1 Prompt mgmt | Файлы промптов | Готово; **Step 13** = hash validation |
| #42 C2 RAG query | Keyword extraction | Готово |
| #43 C3 Data retention | retention_days + purge | Готово; **Step 9** = periodic purge |
| #44 C4 Response caching | SQLite cache | Готово |
| #45 C5 Healthcheck | /health endpoint | Готово; **Step 6** = /ready |
| #46 D1 Desktop signals | D-Bus reactive | Готово |
| #47 D2 Telegram bot | Webhook + push | Готово |
| #48 D3 Calendar | CalDAV auto-context | Готово |
| #49 D4 Flatpak | Manifest + build | Готово; **Step 20** = GA release |
| #50 D5 macOS/WSL2 | Исследование | **Открыт** = Step 19 |
| #51 QW1 scipy | Base deps fix | Готово |
| #52 QW2 i18n | Hardcoded strings | Готово |
| #53 QW3 ThreadPool | Single executor | Готово |

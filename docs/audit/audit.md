# Аудит VoiceForge: статус и задачи (единый документ)

**Обновлено:** 2026-03-06. **Единый план (Phase A–D, Steps 1–19, оставшееся до 100%):** [plans.md](../plans.md). **Полный аудит 2026-03:** [archive/audit/audit-2026-03-full.md](../archive/audit/audit-2026-03-full.md); краткое содержание — раздел 5 ниже. Исторический снимок 2026-02-26: [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](../archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md).

---

## 1. Статус реализации (W1–W20)

| # | Weakness / Step | Статус | Доказательство |
|---|-----------------|--------|----------------|
| W1 / Step 1 | Eval harness в CI | **СДЕЛАНО** | test.yml: job `eval` — pytest tests/eval/ (ROUGE-L) |
| W2 / Step 2 | Coverage omit, fail_under | **СДЕЛАНО** | fail_under=60 (#99). `server.py` и `rag/watcher.py` выведены из omit; suite: `test_web_*.py`, `test_coverage_hotspots_batch99.py`, `test_rag_watcher.py`, `test_cli_e2e_smoke.py`, `test_cli_helpers_contracts.py`. В omit остаются `main.py`, `stt/diarizer.py`, тяжёлые `rag/*` (indexer/embedder/searcher/_onnx_runner/dedup/incremental), `llm/local_llm.py`. |
| W3 / Step 3 | Sonar blocking | **СДЕЛАНО** | sonar.yml: убран continue-on-error |
| W4 / Step 5 | CodeQL blocking | **СДЕЛАНО** | codeql.yml: убран continue-on-error |
| W5 | Pipeline integration test | **СДЕЛАНО** | test_pipeline_integration.py: _prepare_audio, run with mocked STT/_gather_step2 |
| W6 / Step 6 | systemd MemoryMax, /ready | **СДЕЛАНО** | voiceforge.service: MemoryMax=4G, MemoryHigh=3G, OOMScoreAdjust=500; GET /ready (DB check) |
| W7 / Step 12 | Async web | **СДЕЛАНО** | ThreadingMixIn + опциональный Starlette+uvicorn (#66): `voiceforge web --async` или VOICEFORGE_WEB_ASYNC=1, uv sync --extra web-async |
| W8 / Step 8 | Circuit breaker | **СДЕЛАНО** | llm/circuit_breaker.py, router, метрика state (#62) |
| W9 / Step 7 | Trace IDs | **СДЕЛАНО** | core/tracing.py, main, web (X-Trace-Id), test_tracing.py (#61) |
| W10 / Step 13 | Prompt hash validation | **СДЕЛАНО** | prompt_loader.get_prompt_hashes(), warning при fallback, test_prompt_content_snapshot (#67) |
| W11 / Step 9 | Periodic retention purge | **СДЕЛАНО** | daemon: Timer 24h purge (#63) |
| W12 / Step 9 | DB backup CLI | **СДЕЛАНО** | voiceforge backup (--keep N) (#63) |
| W13 / Step 11 | CVE-2025-69872 | **СДЕЛАНО** | Historical wait-state снят: `pip-audit` снова чист без ignore, issue [#65](https://github.com/iurii-izman/voiceforge/issues/65) закрыта; audit trail — [security-and-dependencies.md](../runbooks/security-and-dependencies.md) разд. 4. |
| W14 / Step 6 | /ready endpoint | **СДЕЛАНО** | web/server.py: GET /ready, 200/503; test_web_smoke |
| W15 / Step 4 | Version inconsistency | **СДЕЛАНО** | __init__.py: importlib.metadata.version("voiceforge") |
| W16 / Step 5 | .editorconfig | **СДЕЛАНО** | .editorconfig в корне |
| W17 | Cognitive complexity S3776 | **СДЕЛАНО** | do_GET/do_POST переведены на dispatch table (_GET_ROUTES, _POST_ROUTES) |
| W18 / Step 15 | Error responses | **СДЕЛАНО** | Единый формат `{"error": {"code", "message"}}` (#69) |
| W19 / Step 10 | Monitoring stack | **СДЕЛАНО** | monitoring/: prometheus.yml, alerts.yml, docker-compose, README (#64) |
| W20 / Step 14 | Benchmark suite | **СДЕЛАНО** | tests/benchmark_stt.py, benchmark_rag.py, baseline_benchmark.json (#68) |

---

## 2. Phase A–D → GitHub Issues

| Phase | Step | Описание | Issue |
|-------|------|----------|-------|
| **A** | 1–5 | Eval CI, coverage, Sonar, version, .editorconfig+CodeQL | [#55](https://github.com/iurii-izman/voiceforge/issues/55)–[#59](https://github.com/iurii-izman/voiceforge/issues/59) |
| **B** | 6–10 | /ready+MemoryMax, trace IDs, circuit breaker, purge+backup, monitoring | [#60](https://github.com/iurii-izman/voiceforge/issues/60)–[#64](https://github.com/iurii-izman/voiceforge/issues/64) |
| **C** | 11–15 | CVE, async web, prompt hash, benchmarks, error format | [#65](https://github.com/iurii-izman/voiceforge/issues/65)–[#69](https://github.com/iurii-izman/voiceforge/issues/69) |
| **D** | 16–19 | A/B testing, OTel, plugins, packaging GA | [#70](https://github.com/iurii-izman/voiceforge/issues/70)–[#73](https://github.com/iurii-izman/voiceforge/issues/73) |

Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

---

## 3. Оставшееся до 100% (кратко)

- **#56 Coverage:** закрыто — fail_under=75, тесты стабилизированы (eval/llm_retry skip при отсутствии instructor), добавлены тесты config/otel; `uv sync --extra all` включает [otel] для покрытия OTel-путей.
- **#65 CVE:** закрыто; ignore убран из активных CI/scripts.
- **#66 Async web (полный):** миграция на Starlette/Litestar — опционально; минимальный путь (ThreadingMixIn) выполнен.
- **W17:** закрыто — do_GET/do_POST через dispatch table (S3776).
- **Phase D (#70–#73):** закрыт — #70 eval-ab, #71 OTel (core/otel.py + observability-alerts), #72 custom templates, #73 packaging (offline-package.md, make flatpak-build). См. [plans.md](../plans.md) разд. 3.2.

---

## 4. Закрытые issues (старый план)

#32–49, #51–53 закрыты (development-plan, Alpha2 A–D). Детали: [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

---

## 5. Подробный снимок 2026-03 (executive summary)

**Дата:** 2026-03-05. Полный текст отчёта: [archive/audit/audit-2026-03-full.md](../archive/audit/audit-2026-03-full.md).

**Резюме:** VoiceForge — local-first AI для аудиовстреч на Linux (PipeWire → STT → diarization → RAG → LLM → SQLite). Alpha 0.2, CLI, daemon, Web UI, Telegram, десктоп (Tauri 2). W1–W20 по сути закрыты, historical CVE wait-state тоже снят, а repo перешёл в maintenance mode. Сильные стороны: доки, CI, безопасность (keyring, pip-audit, bandit, gitleaks), observability.

**Системный аудит (оценки):** Код 4/5, Тесты 3/5, Доки 5/5, CI/CD 4/5, Безопасность 4/5, Observability 4/5. Блочный аудит и рекомендуемые шаги — в полном отчёте по ссылке выше.

# Аудит VoiceForge: статус и задачи (единый документ)

**Обновлено:** 2026-03-05. **Единый план (Phase A–D, Steps 1–19, оставшееся до 100%):** [plans.md](../plans.md). **Полный аудит 2026-03:** [archive/audit/audit-2026-03-full.md](../archive/audit/audit-2026-03-full.md); краткое содержание — раздел 5 ниже. Исторический снимок 2026-02-26: [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](../archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md).

---

## 1. Статус реализации (W1–W20)

| # | Weakness / Step | Статус | Доказательство |
|---|-----------------|--------|----------------|
| W1 / Step 1 | Eval harness в CI | **СДЕЛАНО** | test.yml: job `eval` — pytest tests/eval/ (ROUGE-L) |
| W2 / Step 2 | Coverage omit, fail_under | **ЧАСТИЧНО** | pipeline, transcript_log, caldav_poll, dbus_service, audio/buffer, **audio/capture** выведены из omit; fail_under=72 (цель 75→80); в omit остаются main, server, diarizer, rag/*, local_llm (#56). Добавлены test_audio_capture, test_telegram_notify, get_prompt_hashes тест. |
| W3 / Step 3 | Sonar blocking | **СДЕЛАНО** | sonar.yml: убран continue-on-error |
| W4 / Step 5 | CodeQL blocking | **СДЕЛАНО** | codeql.yml: убран continue-on-error |
| W5 | Pipeline integration test | **СДЕЛАНО** | test_pipeline_integration.py: _prepare_audio, run with mocked STT/_gather_step2 |
| W6 / Step 6 | systemd MemoryMax, /ready | **СДЕЛАНО** | voiceforge.service: MemoryMax=4G, MemoryHigh=3G, OOMScoreAdjust=500; GET /ready (DB check) |
| W7 / Step 12 | Async web | **ЧАСТИЧНО** | ThreadingMixIn (#66); полный Starlette/Litestar — опционально |
| W8 / Step 8 | Circuit breaker | **СДЕЛАНО** | llm/circuit_breaker.py, router, метрика state (#62) |
| W9 / Step 7 | Trace IDs | **СДЕЛАНО** | core/tracing.py, main, web (X-Trace-Id), test_tracing.py (#61) |
| W10 / Step 13 | Prompt hash validation | **СДЕЛАНО** | prompt_loader.get_prompt_hashes(), warning при fallback, test_prompt_content_snapshot (#67) |
| W11 / Step 9 | Periodic retention purge | **СДЕЛАНО** | daemon: Timer 24h purge (#63) |
| W12 / Step 9 | DB backup CLI | **СДЕЛАНО** | voiceforge backup (--keep N) (#63) |
| W13 / Step 11 | CVE-2025-69872 | **ЧАСТИЧНО** | Источник (instructor) задокументирован; pip-audit с ignore в CI до фикса upstream (#65); чеклист снятия — [security-and-dependencies.md](../runbooks/security-and-dependencies.md) разд. 4. |
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

- **#56 Coverage:** fail_under=72; в toolbox make coverage даёт 71.74%. Для fail_under=75 нужны дополнительные тесты или вывод модулей из omit (server, main и др.).
- **#65 CVE:** убрать `--ignore-vuln` после фикса upstream (diskcache/instructor).
- **#66 Async web (полный):** миграция на Starlette/Litestar — опционально; минимальный путь (ThreadingMixIn) выполнен.
- **W17:** закрыто — do_GET/do_POST через dispatch table (S3776).
- **Phase D (#70–#73):** см. [plans.md](../plans.md) (раздел 3.2); #71 OTel — в работе.

---

## 4. Закрытые issues (старый план)

#32–49, #51–53 закрыты (development-plan, Alpha2 A–D). Детали: [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

---

## 5. Подробный снимок 2026-03 (executive summary)

**Дата:** 2026-03-05. Полный текст отчёта: [archive/audit/audit-2026-03-full.md](../archive/audit/audit-2026-03-full.md).

**Резюме:** VoiceForge — local-first AI для аудиовстреч на Linux (PipeWire → STT → diarization → RAG → LLM → SQLite). Alpha 0.2, CLI, daemon, Web UI, Telegram, десктоп (Tauri 2). Большинство W1–W20 в статусе «СДЕЛАНО». Остаётся: #56 (coverage), #65 (CVE), #66 (async опционально), W17, Phase D в бэклоге. Сильные стороны: доки, CI, безопасность (keyring, pip-audit, bandit, gitleaks), observability. Приоритеты: качество до 100%, OTel #71, plugins #72, packaging #73, A/B #70.

**Системный аудит (оценки):** Код 4/5, Тесты 3/5, Доки 5/5, CI/CD 4/5, Безопасность 4/5, Observability 4/5. Блочный аудит и рекомендуемые шаги — в полном отчёте по ссылке выше.

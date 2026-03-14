# Аудит vs реальность кода (сводка 2026-03)

Сравнение запланированного (аудит, roadmap, Copilot program) с тем, что реально сделано в коде, в процентах и по категориям.

**Дата:** 2026-03-14. **Версия:** 1.0.0-beta.1.

---

## 1. Knowledge Copilot Program (KD/KC/KV)

| Блок | Issue | Запланировано | В коде | % | Примечание |
|------|-------|----------------|--------|---|------------|
| KD1–KD3 | #170–#172 | Product/UX/Architecture contracts | Done, decision-locked | 100 | Документально зафиксировано |
| KC1 | #173 | Bootstrap, traceability | Done | 100 | Program map, docs |
| KC2–KC6 | #174–#178 | Overlay, capture, STT, RAG, fast cards | Реализовано | 100 | daemon, overlay, router, D-Bus |
| KC7–KC8 | #179–#180 | Deep track, main-window integration | Реализовано | 100 | deep cards, GetSettings, overlay |
| KC9 | #181 | Knowledge UI, context packs | Реализовано | 100 | desktop knowledge tab |
| KC10 | #182 | Mode system (cloud/hybrid/offline) | Реализовано | 100 | config, get_effective_llm, UI badge |
| KC11 | #183 | System audio, scenario presets | **Не начато** | 0 | Блокируется KV1 |
| KC12 | #184 | Pro cards, answer refinement | Реализовано | 100 | objections, follow_up, refine_copilot_answer |
| KC13 | #185 | Adaptive intelligence, extensibility | **Не начато** | 0 | Блокируется KV5 |
| KC14 | #186 | QA, release gate, perf, idle-unload | Реализовано | 100 | runbook, config, daemon unload |
| KV1–KV5 | #187–#191 | User/external gates | Не реализуются кодом | — | Требуют решений пользователя |

**Итого по программе:** реализовано 12 из 14 KC-блоков (86%); 2 блока (KC11, KC13) ждут снятия gate (KV1, KV5).

---

## 2. Phase A–D и W1–W20 (аудит)

По [audit.md](audit.md) и [plans.md](../plans.md): W1–W20 и Phase A–D Steps 1–19 закрыты.

| Категория | Запланировано | В коде | % | Не сделано / граница |
|-----------|----------------|--------|---|----------------------|
| Eval, coverage, Sonar, CodeQL | W1–W4, Steps 1–5 | CI, omit, fail_under, sonar.yml | 100 | — |
| /ready, MemoryMax, trace IDs, circuit breaker | W6, W9, W8 | server, service, tracing, circuit_breaker | 100 | — |
| Async web, purge, backup, CVE | W7, W11–W13 | ThreadingMixIn, daemon purge, backup CLI | 100 | — |
| Prompt hash, benchmarks, error format | W10, W20, W18 | prompt_loader, benchmark_*, JSON error | 100 | — |
| Monitoring, OTel, packaging | W19, #71, #73 | monitoring/, otel, flatpak | 100 | OTel — ручная проверка в Jaeger |

**Итого Phase A–D:** 100% по чек-листу аудита; остаточные пункты — Sonar residual (#165), glib (#164), не блокируют.

---

## 3. Engineering Score (по коду)

Оценки из [PROJECT-STATUS-SUMMARY.md](runbooks/PROJECT-STATUS-SUMMARY.md): Engineering ~80/100, Daily Driver ~35/100.

| Направление | Оценка | Что сделано | Что не доделано |
|-------------|--------|-------------|------------------|
| Core / main.py, daemon | 67 | Pipeline, daemon, D-Bus, copilot path | Высокая cognitive complexity (Sonar S3776), частичный omit в coverage |
| Audio / STT / diarization | 80 | faster-whisper, streaming, pyannote, ring buffer | diarizer heavy; ONNX — manual |
| RAG / storage | 81 | FTS, chunks, index/search, groundedness | ONNX embedder, incremental — omit |
| LLM / prompts | 78 | Router, Instructor, fallback, PII | Non-Claude caching — research |
| Testing & QA | 82 | E2E, release gate, copilot tests | Coverage 75%; часть модулей в omit |
| Security | 84 | keyring, pip-audit, bandit, gitleaks | Dependabot alerts 3 (1 high, 2 mod) — advisory |
| Observability | 79 | Prometheus, OTel spans, /ready, /metrics | Live Jaeger — manual |
| Documentation | 75 | 15+ runbooks, ADR, DOCS-INDEX | Residual drift, индексация |

**Итого:** ~80% от эталона 86.5; главные дыры — сложность в main/daemon/preflight, omit-модули, Sonar residual.

---

## 4. Что не сделано вообще (0% или вне scope)

| Область | Что не сделано | Почему |
|---------|----------------|--------|
| KC11 | System audio capture, scenario presets | KV1 не разрешён (legal/consent) |
| KC13 | Adaptive intelligence, plugins, extensibility | KV5 не разрешён (platform gate) |
| KV2–KV4 | Overlay sign-off, pilot validation, business/packaging | Ручные решения |
| Updater | Signed updates, update server | Явно отключён; нужны ключи и инфра |
| Windows/macOS | Порт десктопа | Решение по KV5 |
| Sonar | Все CRITICAL/MAJOR (S3776, S7924, S6819, S1244 и др.) | Часть в #165; рефакторинг без изменения поведения |
| Coverage | main.py, daemon.py, router.py до 75%+ без omit | Постепенный вывод из omit по batch |

---

## 5. Процент «сделано по коду» (сводка)

| Срез | Сделано | Всего / эталон | % |
|------|---------|-----------------|---|
| Copilot KC (без KV) | 12 KC | 14 KC | **86%** |
| Phase A–D / W1–W20 | 20/20 | 20 | **100%** |
| Engineering (оценка) | 80 | 86.5 | **92%** |
| Daily Driver (оценка) | 35 | 85 | **41%** |
| Релиз (версия, тег, артефакты) | 1.0.0-beta.1 | beta.1 | **100%** для беты |

**Итог:** По «железу» (код, CI, контракты) проект близок к эталону; по продукту (Daily Driver) — чуть меньше половины пути до целевого 85%. Два KC-блока и все KV лежат вне автопилота до решений пользователя.

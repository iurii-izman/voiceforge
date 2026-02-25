# PROJECT_AUDIT_AND_ROADMAP — VoiceForge

Дата: 2026-02-24 | Branch: `main` | Commit: `15d1321`

---

## 0) Executive summary

1. **VoiceForge** — local-first AI-ассистент для аудиовстреч на Linux: запись (PipeWire) → транскрипция (faster-whisper) → диаризация (pyannote) → анализ (LLM) → структурированный вывод.
2. **Текущая версия:** 0.2.0-alpha.1. Десктоп (Tauri 2 + D-Bus), CLI (9 замороженных команд по ADR-0001), Web UI (FastAPI), RAG (sqlite-vec + FTS5).
3. **Зрелость:** ранняя альфа. Ядро работает, документация отличная, CI/CD зрелый, но нет eval harness, observability и полного покрытия критичных модулей.
4. **Главные риски:** pyannote OOM на ≤8 ГБ RAM; LLM-вызовы без retry/circuit breaker; нет eval-метрик для качества анализа; daemon/streaming без unit-тестов.
5. **Безопасность:** keyring для секретов, gitleaks + bandit + pip-audit + semgrep + CodeQL в CI. CVE-2025-69872 отслеживается.
6. **Документация — главная сила проекта:** 40+ документов, ADR, runbooks, билингвальность (RU/EN), agent-aware handoff.
7. **Стек:** Python 3.12+ / uv, Rust (Tauri 2), TypeScript (Vite), SQLite, D-Bus, PipeWire. Без Docker/k8s — нативная Linux-установка.
8. **Главные возможности роста:** eval harness → измерение качества; Instructor retry → надёжность LLM; observability → production readiness.
9. **Ближайший фокус (backlog):** AppImage сборка (#27), RAG ODT/RTF тесты (#29), Dependabot alert (#30).
10. **Результат аудита:** проект на уверенном альфа-уровне с сильной документацией и CI, но нуждается в hardening по reliability, observability и AI quality.

---

## 1) Assumptions & Unknowns

### Допущения
- Проект используется одним разработчиком / маленькой командой (solo-dev pattern видно по коммитам и CODEOWNERS).
- Целевая платформа: Fedora Atomic / toolbox, другие Linux-дистрибутивы — secondary.
- Нет внешних пользователей (alpha), поэтому SLO/SLA не определены.
- Бюджет LLM: $75/мес (захардкожено в комментарии `router.py`, но настраиваемо через `budget_limit_usd`).
- GPU не обязателен (CPU-only path через faster-whisper + ONNX).

### Что не удалось подтвердить
- Реальное покрытие тестами: CI показывает `--cov-fail-under=0` (порог отключён в CI, реальный check через `check_new_code_coverage.sh --fail-under 20`).
- Состояние SonarCloud quality gate (скрипт `sonar_fetch_issues.py` не запускался).
- Работоспособность AppImage / Flatpak сборки (issue #27 в процессе).
- Реальное потребление RAM pyannote 4.0.4 на целевом железе.
- Наличие и полнота `voiceforge.yaml` конфига у пользователей.

---

## 2) Current state ("Where we are now")

### 2.1 Product snapshot

**Пользователи:** разработчик(и), которые проводят аудиовстречи на Linux и хотят автоматического анализа.

**Use-cases:**
- Запись встречи через PipeWire → транскрипция → анализ (вопросы, ответы, рекомендации, action items)
- 5 шаблонов: standup, sprint_review, one_on_one, brainstorm, interview
- Поиск по истории встреч (FTS5)
- RAG: подгрузка контекста из документов (PDF, DOCX, MD, HTML, ODT, RTF)
- PII-фильтрация (GLiNER + regex)
- Live summary во время записи
- Отслеживание action items между сессиями
- Контроль затрат на LLM (по моделям/дням)
- CalDAV интеграция (poll)

**Non-goals (явно):** macOS/Windows поддержка (пока), cloud deployment, multi-tenant.

### 2.2 Architecture map (C4)

#### Context
```
┌─────────────┐     PipeWire      ┌──────────────────┐
│  Микрофон /  │ ───────────────→ │   VoiceForge     │
│  Системный   │                  │   (CLI/Daemon)    │
│  аудио       │                  └────────┬─────────┘
└─────────────┘                            │
                                   D-Bus IPC│
                              ┌────────────┴────────────┐
                              │                         │
                    ┌─────────▼──────┐       ┌──────────▼─────┐
                    │  Desktop UI    │       │   Web UI       │
                    │  (Tauri 2)     │       │   (FastAPI)    │
                    └────────────────┘       └────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Anthropic│   │ OpenAI   │   │ Ollama   │
        │ (Claude) │   │ (GPT-4o) │   │ (local)  │
        └──────────┘   └──────────┘   └──────────┘
```

#### Container
| Контейнер | Технология | Назначение |
|-----------|-----------|-----------|
| CLI | Python 3.12+ / typer | 9 команд: listen, analyze, history, cost, status, export, daemon, action-items, calendar |
| Daemon | Python / D-Bus (dbus-fast) | Фоновый сервис: запись, streaming STT, smart trigger, D-Bus API |
| Desktop UI | Tauri 2 / Rust + JS | Нативное GUI-приложение, D-Bus клиент |
| Web UI | FastAPI | Локальный веб-интерфейс |
| STT | faster-whisper | Транскрипция аудио |
| Diarizer | pyannote.audio 4.0.4 | Определение спикеров |
| LLM Router | LiteLLM | Маршрутизация к Claude/GPT/Gemini/Ollama |
| RAG | ONNX + sqlite-vec + FTS5 | Поиск контекста из документов |
| PII Filter | GLiNER + regex | Фильтрация персональных данных |
| DB: transcripts | SQLite | Сессии, сегменты, анализ, action items |
| DB: metrics | SQLite | Стоимость по моделям/дням |
| DB: RAG | SQLite + sqlite-vec | Чанки, эмбеддинги, FTS5 |

#### Component (ключевые модули)
```
src/voiceforge/
├── main.py              # CLI entrypoint (1088 строк)
├── core/
│   ├── config.py        # Pydantic Settings, 14 валидаторов
│   ├── pipeline.py      # STT → Diarization+RAG+PII (параллельно) → LLM
│   ├── daemon.py         # D-Bus daemon, threading
│   ├── dbus_service.py  # D-Bus интерфейсы
│   ├── secrets.py       # Keyring интеграция
│   ├── metrics.py       # Учёт стоимости
│   ├── transcript_log.py # Лог сессий
│   ├── model_manager.py # Lifecycle ML-моделей
│   └── migrations/      # 5 SQL-миграций
├── llm/
│   ├── router.py        # Multi-model routing + prompt caching
│   ├── schemas.py       # Pydantic-схемы (5 шаблонов + base)
│   ├── pii_filter.py    # PII redaction
│   └── local_llm.py     # Ollama $0-path
├── rag/
│   ├── indexer.py       # Multi-format, incremental
│   ├── searcher.py      # Hybrid: vector + FTS5
│   ├── embedder.py      # ONNX MiniLM
│   └── parsers.py       # PDF, DOCX, ODT, RTF, MD, HTML, TXT
├── stt/
│   ├── transcriber.py   # faster-whisper
│   ├── diarizer.py      # pyannote
│   └── streaming.py     # Streaming STT
├── audio/
│   ├── capture.py       # PipeWire capture
│   ├── buffer.py        # Ring buffer
│   └── smart_trigger.py # Auto-trigger на паузе
├── calendar/caldav_poll.py
├── web/server.py        # FastAPI
├── cli/                 # history_helpers, status_helpers
└── i18n/                # RU/EN
```

### 2.3 Repo map

| Директория | Содержание |
|-----------|-----------|
| `src/voiceforge/` | Python-ядро (~6500 строк) |
| `desktop/` | Tauri 2: `src-tauri/` (Rust), `src/` (JS/CSS) |
| `tests/` | 10 тест-файлов (pytest) |
| `docs/` | 40+ документов: architecture/, runbooks/, adr/, history/ |
| `scripts/` | 15+ shell/python скриптов для CI/dev |
| `.github/` | 8 workflows, dependabot, issue templates, rulesets, CODEOWNERS |

**Entrypoints:**
- CLI: `src/voiceforge/main.py` → `voiceforge` console script
- Daemon: `src/voiceforge/core/daemon.py` → `run_daemon()`
- Desktop: `desktop/src-tauri/src/main.rs`
- Web: `src/voiceforge/web/server.py`
- Systemd: `scripts/voiceforge.service`

### 2.4 AI subsystem

**Тип:** LLM app + RAG + STT/diarization pipeline (не fine-tuning).

**Данные:**
- Источник: PipeWire аудио (int16, 16kHz после ресэмплинга)
- Хранение: SQLite (transcripts.db, rag.db), ring buffer (raw PCM)
- Пайплайн: Audio → STT → parallel(Diarization, RAG search, PII) → LLM analysis

**Модель/провайдер:**
- STT: faster-whisper (small/medium/large, CPU/GPU)
- Diarization: pyannote.audio 4.0.4 (HuggingFace token через keyring)
- LLM: LiteLLM routing — Claude Haiku 4.5 (default) → GPT-4o-mini → Gemini Flash → Claude Sonnet (fallback chain)
- Embeddings: ONNX MiniLM (sqlite-vec)
- NER/PII: GLiNER ≥ 0.2.20
- Local: Ollama (FAQ-classify → simple_answer, $0 path)

**Промпты:**
- Встроены в `llm/router.py`: SYSTEM_PROMPT (general), 5 × TEMPLATE_PROMPTS, LIVE_SUMMARY_SYSTEM, STATUS_UPDATE_SYSTEM
- Prompt caching для Claude (ephemeral cache_control)
- Не вынесены в отдельные файлы; нет версионирования промптов

**Eval/метрики/guardrails:**
- **Eval harness: отсутствует.** Нет автоматизированной проверки качества LLM-ответов.
- Guardrails: PII-фильтр (regex + GLiNER), бюджетный лимит (`budget_limit_usd`).
- Метрики: cost tracking (by model, by day), cache hit rate. Нет метрик качества (accuracy, hallucination rate).

### 2.5 Engineering maturity snapshot

| Категория | Оценка | Комментарий | Доказательства |
|-----------|--------|------------|---------------|
| **Code** | 4/5 | Чёткая модульная структура, structlog, Pydantic. Неполный mypy (только core/llm/rag/stt). | `pyproject.toml` [tool.mypy], `src/voiceforge/` |
| **Tests** | 3/5 | 10 файлов, 80% gate (но `--cov-fail-under=0` в CI). Критичные модули excluded: daemon, streaming, smart_trigger. | `.github/workflows/test.yml:32`, `pyproject.toml` [tool.pytest] |
| **CI/CD** | 4/5 | 8 workflows, SBOM, quality gates, multi-Python matrix. Нет caching ML-зависимостей. | `.github/workflows/` |
| **Security** | 4/5 | Keyring, gitleaks, bandit, pip-audit, semgrep, CodeQL, pre-commit. CVE tracking. | `.pre-commit-config.yaml`, `.bandit.yaml`, `.gitleaks.toml` |
| **Observability** | 2/5 | structlog для логов. Нет metrics, tracing, alerting, dashboards, SLO. | `src/voiceforge/core/metrics.py` — только cost, не Prometheus/OTLP |
| **Reliability** | 2/5 | Один retry в `complete_structured()` на parse error. Нет circuit breaker, rate limit, idempotency. pyannote OOM риск. | `src/voiceforge/llm/router.py:356-368`, `src/voiceforge/core/daemon.py` |
| **Performance/Cost** | 3/5 | Budget tracking, prompt caching (Claude), Ollama $0-path. Нет response caching, batching. | `src/voiceforge/llm/router.py:17-25`, `src/voiceforge/core/metrics.py` |
| **Docs/Onboarding** | 5/5 | 40+ документов, quickstart, ADR, runbooks, agent-aware handoff, DOCS-INDEX. Билингвально. | `docs/DOCS-INDEX.md`, `docs/runbooks/` |
| **AI Quality** | 2/5 | Нет eval harness, regression suite, drift detection. PII-фильтр есть, но без аудита. | Нет файлов eval/benchmark |
| **Data Governance** | 2/5 | PII-фильтр, .gitignore для аудио. Нет retention policy, audit trail, data lineage. | `src/voiceforge/llm/pii_filter.py`, `.gitignore` |

---

## 3) Gap analysis

| # | Разрыв | Причина | Эффект | Приоритет | Как закрыть |
|---|--------|---------|--------|-----------|------------|
| G1 | Нет eval harness для LLM | Alpha-фокус на функционале | Невозможно измерить/регрессировать качество анализа | **Высокий** | DeepEval + золотой датасет 20-50 стенограмм |
| G2 | LLM без retry/circuit breaker | Только один retry на parse error | Сбой API → потеря анализа, нет graceful degradation | **Высокий** | Instructor max_retries + LiteLLM cooldowns |
| G3 | Критичные модули без тестов | Исключены из coverage (daemon, streaming, smart_trigger, model_manager) | Регрессии в фоновых процессах не ловятся | **Высокий** | Unit-тесты с моками для ключевых сценариев |
| G4 | Нет observability | Только structlog, нет metrics/tracing | Невозможно отследить деградацию в production | **Средний** | Structured metrics → Prometheus/OTLP export |
| G5 | pyannote OOM | 4.0.4 требует 6x больше VRAM vs 3.3.x | Crash на ≤8ГБ системах | **Высокий** | Memory guard + fallback to no-diarization |
| G6 | Промпты не версионированы | Встроены в router.py | Нет regression suite при изменении промптов | **Средний** | Вынести в YAML/файлы, версионировать |
| G7 | Нет integration тестов с аудио | Тесты мокируют AudioCapture | Реальный pipeline не проверяется end-to-end | **Средний** | Тестовые WAV-файлы + smoke test с реальным pipeline |
| G8 | Нет data retention policy | Транскрипты хранятся бессрочно | Риск накопления PII, нарушение GDPR-подобных норм | **Средний** | Configurable retention + auto-cleanup job |
| G9 | Desktop не упакован | AppImage/Flatpak в процессе (#27) | Нет простого способа дистрибуции | **Средний** | Завершить сборку в toolbox |
| G10 | Single-threaded event loop в daemon | `asyncio.new_event_loop()` + threading | Потенциальный bottleneck при concurrent D-Bus requests | **Низкий** | Profile under load; consider asyncio-native design |

---

## 4) Top-20 weakest points + усиление

### Weakness #1: Нет eval harness для LLM-выводов
- **Impact:** High — невозможно измерить качество анализа встреч, нет regression detection
- **Evidence:** Отсутствуют файлы `eval/`, `benchmark/`, `tests/test_llm_quality*`. В `router.py` нет метрик accuracy.
- **Root cause:** Alpha-фокус на функционале; eval не приоритизирован
- **Quick win (1-3 дня):** Создать 10 golden transcripts с reference outputs; pytest-параметризованный тест с ROUGE + LLM-as-judge
- **Proper fix (1-4 недели):** DeepEval integration, SummarizationMetric, 50+ golden samples по шаблонам
- **Long-term (1-3 мес):** Online eval (sample 5% production), drift dashboard, A/B на промптах
- **Acceptance criteria:** CI-job `eval` зелёный; ROUGE-L ≥ 0.4, LLM-judge score ≥ 3.5/5 на golden set

### Weakness #2: LLM-вызовы без Instructor retry и circuit breaker
- **Impact:** High — сбой API или невалидный JSON → потеря анализа; только 1 retry в `complete_structured()`
- **Evidence:** `src/voiceforge/llm/router.py:355-368` — ручной retry без exponential backoff, без Instructor. W5 в `development-plan-post-audit-2026.md`.
- **Root cause:** Instructor подключён через `response_format`, но не используется для retry/validation
- **Quick win:** `instructor.from_litellm(completion, max_retries=3)` в `complete_structured()`
- **Proper fix:** LiteLLM `cooldowns` config, budget alerts, fallback timeout tuning
- **Long-term:** Circuit breaker pattern (tenacity + custom state), dead letter queue для failed analyses
- **Acceptance criteria:** 95% success rate при provider outage до 30с; нет unhandled JSON parse errors в логах

### Weakness #3: Критичные модули без unit-тестов
- **Impact:** High — daemon, streaming, smart_trigger, model_manager — backbone приложения, не покрыты тестами
- **Evidence:** `pyproject.toml` `[tool.coverage.report]` exclude: `daemon.py`, `smart_trigger.py`, `model_manager.py`, `streaming.py`
- **Root cause:** Сложность мокирования D-Bus, PipeWire, ML-моделей
- **Quick win:** 5-10 unit-тестов на `VoiceForgeDaemon.analyze()`, `listen_start/stop`, `SmartTrigger.check()` с моками
- **Proper fix:** Test doubles для D-Bus (fake bus), AudioCapture mock, model_manager с fixture
- **Long-term:** Integration test environment (CI с PipeWire virtual source)
- **Acceptance criteria:** daemon, smart_trigger, model_manager ≥ 60% coverage; streaming ≥ 40%

### Weakness #4: Нет observability stack
- **Impact:** Medium — нельзя отследить latency, error rates, model drift в production
- **Evidence:** `src/voiceforge/core/metrics.py` — только cost tracking в SQLite. Нет Prometheus/OTLP/Grafana.
- **Root cause:** Для alpha достаточно structlog; production observability не приоритизировалась
- **Quick win:** structlog JSON → файл; скрипт для grep-аналитики
- **Proper fix:** prometheus_client counters: `stt_duration_seconds`, `llm_cost_usd`, `pipeline_errors_total`; Grafana dashboard
- **Long-term:** OpenTelemetry SDK, distributed tracing (daemon ↔ CLI ↔ LLM), alerting (cost spike, error rate)
- **Acceptance criteria:** 5 ключевых метрик в Prometheus; Grafana dashboard с 3+ панелями; alert на budget > 80%

### Weakness #5: pyannote.audio OOM на ≤8 ГБ RAM
- **Impact:** High — crash daemon при дiarization длинного аудио на типовом ноутбуке
- **Evidence:** `docs/runbooks/pyannote-version.md`, pyannote/pyannote-audio#1963 (4.0.3 → 6x VRAM). Код pin: `pyannote.audio==4.0.4`.
- **Root cause:** pyannote 4.x `exclusive_speaker_diarization` потребляет 9.5 ГБ VRAM на 72-мин аудио
- **Quick win:** `resource.setrlimit(RLIMIT_AS)` guard + try/except MemoryError → skip diarization
- **Proper fix:** Проверить `speaker-diarization-community-1` model; chunk длинные записи; fallback на 3.3.x
- **Long-term:** Adaptive model selection по доступной RAM; lazy unload после diarization
- **Acceptance criteria:** Daemon не падает на 8 ГБ системе с 30-мин аудио; если OOM → graceful degradation (анализ без диаризации)

### Weakness #6: Промпты встроены в код, не версионированы
- **Impact:** Medium — изменение промпта может сломать качество без обнаружения
- **Evidence:** `src/voiceforge/llm/router.py:28-75` — SYSTEM_PROMPT + 5 TEMPLATE_PROMPTS + LIVE_SUMMARY_SYSTEM как строковые константы
- **Root cause:** Простота реализации в alpha
- **Quick win:** Вынести промпты в `src/voiceforge/llm/prompts/` (YAML/txt), загружать при старте
- **Proper fix:** Версионирование промптов (hash/semver), snapshot-тесты на промпты
- **Long-term:** Prompt management tool (promptfoo, Langfuse), A/B testing промптов
- **Acceptance criteria:** Промпты в файлах; тест на неизменность промпта (snapshot); CI ловит drift

### Weakness #7: Нет integration тестов с реальным аудио pipeline
- **Impact:** Medium — реальный path (PipeWire → STT → analysis) не тестируется автоматически
- **Evidence:** `tests/test_cli_e2e_smoke.py` — моки AudioCapture, fake pipeline
- **Root cause:** PipeWire недоступен в GitHub Actions
- **Quick win:** 3 тестовых WAV-файла (5с, 30с, silence); тест STT → verify transcript содержит ожидаемые слова
- **Proper fix:** CI с PipeWire virtual source (Ubuntu + pipewire); integration test suite
- **Long-term:** Nightly regression на real-world recordings (anonymized)
- **Acceptance criteria:** 3+ WAV-based тестов в CI; STT accuracy ≥ 80% WER на clean audio

### Weakness #8: Нет rate limiting и budget enforcement в реальном времени
- **Impact:** Medium — runaway LLM costs при smart_trigger loops или ошибках
- **Evidence:** `src/voiceforge/llm/router.py:2` — комментарий "Budget $75/mo", но `complete_structured()` не проверяет текущий spend перед вызовом
- **Root cause:** Budget check в `metrics.py` — постфактум (at log time), не pre-call
- **Quick win:** Pre-call check: `if get_daily_cost() > daily_limit: raise BudgetExceeded`
- **Proper fix:** LiteLLM budget manager, per-model caps, alert на 80% budget
- **Long-term:** Rate limiter (token bucket), cost dashboard, auto-downgrade model при приближении к лимиту
- **Acceptance criteria:** LLM-вызов отклоняется при превышении дневного/месячного бюджета; alert в логах

### Weakness #9: RAG query truncation и ограниченный контекст
- **Impact:** Medium — `transcript[:1000]` для RAG query может пропустить ключевые темы в конце стенограммы
- **Evidence:** `src/voiceforge/core/pipeline.py:17` — `RAG_QUERY_MAX_CHARS = 1000`, `pipeline.py:107` — `transcript[:RAG_QUERY_MAX_CHARS]`
- **Root cause:** W3 fix увеличил с 200 до 1000, но подход наивный (prefix truncation)
- **Quick win:** Keyword extraction (TF-IDF top-10 terms) вместо prefix
- **Proper fix:** Summarize transcript → use summary as query; multi-query RAG
- **Long-term:** Semantic chunking + reranking (cross-encoder)
- **Acceptance criteria:** RAG recall ≥ 70% на golden set из 20 query-document пар

### Weakness #10: `complete_structured()` — response_format вместо Instructor
- **Impact:** Medium — LiteLLM `response_format=response_model` менее надёжен чем Instructor validation loop
- **Evidence:** `src/voiceforge/llm/router.py:347-353` — `response_format=response_model` передаётся в `completion()`, parse вручную
- **Root cause:** Instructor был заявлен в зависимостях, но не интегрирован
- **Quick win:** `client = instructor.from_litellm(completion); client.chat.completions.create(response_model=...)` с `max_retries=3`
- **Proper fix:** Кастомные validators в Pydantic-схемах + Instructor retry с контекстом ошибки
- **Long-term:** Мониторинг validation failure rate → alert → auto-switch model
- **Acceptance criteria:** 0 unhandled JSON parse errors за 100 вызовов; Instructor retry покрывает все LLM endpoints

### Weakness #11: IPC envelope по умолчанию отключён
- **Impact:** Low-Medium — без envelope D-Bus-клиенты не различают success/error
- **Evidence:** `src/voiceforge/core/daemon.py:314` — `"envelope_v1": _env_flag("VOICEFORGE_IPC_ENVELOPE", default=False)`
- **Root cause:** W7 — обратная совместимость с первой версией
- **Quick win:** Поменять default на True
- **Proper fix:** API version negotiation: клиент запрашивает capabilities, daemon отвечает с envelope
- **Long-term:** Protobuf/MessagePack для D-Bus payload
- **Acceptance criteria:** Envelope по умолчанию True; desktop и CLI работают с envelope; test snapshot обновлён

### Weakness #12: Нет data retention и auto-cleanup
- **Impact:** Medium — transcripts.db растёт бессрочно, содержит потенциально PII
- **Evidence:** Нет конфигурации retention в `config.py`; нет cleanup job; `transcripts.db` без TTL
- **Root cause:** Alpha — нет пользователей, данные не накапливаются
- **Quick win:** `voiceforge history --purge-before DATE` команда
- **Proper fix:** `retention_days` в Settings; автоматический cleanup при старте daemon
- **Long-term:** Audit trail (кто/когда удалил), compliance report
- **Acceptance criteria:** Retention policy настраиваема; auto-cleanup в daemon; PII purge по запросу

### Weakness #13: Нет graceful degradation при отсутствии scipy
- **Impact:** Low-Medium — если scipy не установлен, аудио не ресэмплируется, качество STT деградирует тихо
- **Evidence:** `src/voiceforge/core/pipeline.py:24-28` — ImportError → warning → return audio as-is
- **Root cause:** scipy — опциональная зависимость (не в base)
- **Quick win:** Добавить scipy в base dependencies
- **Proper fix:** Numpy-based ресэмплинг (без scipy); или signal rate validation при capture
- **Long-term:** Capture всегда в 16kHz (PipeWire format negotiation)
- **Acceptance criteria:** `uv sync` без extras → ресэмплинг работает; или capture гарантирует 16kHz

### Weakness #14: Hardcoded error messages на русском
- **Impact:** Low — `pipeline.py:150`, `pipeline.py:157` содержат русские строки вне i18n
- **Evidence:** `"Ошибка: сначала запустите voiceforge listen."`, `"Ошибка: недостаточно аудио в буфере."`
- **Root cause:** W6 — i18n не полностью интегрирован
- **Quick win:** Заменить на `t("pipeline.error.no_ring")`, `t("pipeline.error.insufficient_audio")`
- **Proper fix:** Аудит всех string literals в src/ → замена на t() где user-facing
- **Long-term:** CI lint rule: запрет кириллицы в .py файлах вне i18n/
- **Acceptance criteria:** 0 hardcoded user-facing строк на русском в src/ (кроме i18n/)

### Weakness #15: ThreadPoolExecutor создаётся на каждый вызов pipeline
- **Impact:** Low — overhead создания executor на каждый `AnalysisPipeline.run()`
- **Evidence:** `src/voiceforge/core/pipeline.py:187` — `executor = ThreadPoolExecutor(max_workers=3)` внутри `run()`
- **Root cause:** Stateless design pipeline
- **Quick win:** Executor как атрибут класса с `__enter__/__exit__`
- **Proper fix:** Shared executor через ModelManager или daemon scope
- **Long-term:** asyncio-based pipeline (без threads)
- **Acceptance criteria:** Один executor на daemon lifecycle; benchmark: no regression

### Weakness #16: Нет health check endpoint
- **Impact:** Low-Medium — systemd service без health check; нет способа мониторить daemon health
- **Evidence:** `scripts/voiceforge.service` — no WatchdogSec; D-Bus `Ping()` → "pong" есть, но не используется для monitoring
- **Root cause:** Alpha — простой systemd unit
- **Quick win:** `WatchdogSec=30` + `sd_notify(WATCHDOG=1)` в daemon loop
- **Proper fix:** `/health` endpoint в Web UI; D-Bus health signal; readiness probe
- **Long-term:** Structured health: model loaded, DB accessible, keyring available, PipeWire connected
- **Acceptance criteria:** systemd watchdog restart при зависании; health status доступен через CLI/D-Bus

### Weakness #17: Desktop D-Bus signals — нет подписки на изменения
- **Impact:** Low — desktop UI использует polling вместо push notifications
- **Evidence:** `desktop/src-tauri/src/dbus_signals.rs` (modified) — подписка в процессе разработки
- **Root cause:** Часть III, п.5 в development plan — ещё не реализовано
- **Quick win:** Подписка на `ListenStateChanged`, `AnalysisDone` сигналы
- **Proper fix:** Полный set signal handlers в Tauri → UI reactive update
- **Long-term:** Event sourcing: все изменения через D-Bus signals
- **Acceptance criteria:** Desktop обновляется в реальном времени при analyze/listen без polling

### Weakness #18: Нет SBOM для desktop (Rust/JS)
- **Impact:** Low — SBOM генерируется только для Python (cyclonedx)
- **Evidence:** `.github/workflows/release.yml` — `cyclonedx-py` только для Python wheel
- **Root cause:** Desktop — отдельный артефакт, сборка в toolbox
- **Quick win:** `cargo sbom` или `cargo cyclonedx` в release pipeline
- **Proper fix:** Unified SBOM: Python + Rust + JS
- **Long-term:** SBOM validation в CI; dependency graph visualization
- **Acceptance criteria:** SBOM для desktop в release артефактах

### Weakness #19: Нет timeout для D-Bus методов
- **Impact:** Low-Medium — `analyze()` через D-Bus может блокироваться бесконечно (LLM timeout)
- **Evidence:** `src/voiceforge/core/daemon.py:98-104` — `analyze()` вызывает `run_analyze_pipeline()` без timeout
- **Root cause:** D-Bus интерфейс не имеет timeout-wrapper
- **Quick win:** `analyze_timeout_v1` в capabilities → timeout в Tauri клиенте
- **Proper fix:** asyncio.wait_for с configurable timeout в daemon
- **Long-term:** Cancellation support: D-Bus CancelAnalysis method
- **Acceptance criteria:** analyze timeout настраиваем (default 120s); при timeout → error response, не зависание

### Weakness #20: CI не кеширует ML-зависимости
- **Impact:** Low — CI медленнее, чем мог бы быть
- **Evidence:** `.github/workflows/test.yml` — `uv sync --extra all` без cache для onnxruntime, pyannote, etc.
- **Root cause:** ML-зависимости тяжёлые, но скачиваются каждый раз
- **Quick win:** `actions/cache@v4` для `~/.cache/uv`
- **Proper fix:** Docker image с pre-installed ML deps для CI
- **Long-term:** Self-hosted runner с кешем
- **Acceptance criteria:** CI time ≤ 3 мин (сейчас ~5-7 мин предположительно)

---

## 5) Roadmap: 20 шагов развития

### Phase A: Stabilize (качество, тесты, воспроизводимость)

#### Step 1: Eval harness для LLM-выводов
- **Цель:** Измеримое качество анализа встреч
- **Scope:** Создать `tests/eval/`, 20+ golden transcripts, DeepEval integration, ROUGE + LLM-as-judge
- **Dependencies:** Нет
- **Effort:** M | Риск: Low
- **Owner:** ML/Backend
- **Deliverables:** `tests/eval/`, `eval/golden_samples/`, CI job `eval`
- **Acceptance:** ROUGE-L ≥ 0.4; LLM-judge ≥ 3.5/5; CI green
- **KPI:** Accuracy score на golden set

#### Step 2: Instructor retry + LLM resilience
- **Цель:** 95%+ success rate LLM-вызовов
- **Scope:** `llm/router.py` — instructor.from_litellm, max_retries=3, cooldowns config
- **Dependencies:** Нет
- **Effort:** S | Риск: Low
- **Owner:** Backend
- **Deliverables:** Обновлённый `router.py`, тесты на retry
- **Acceptance:** 0 unhandled parse errors за 100 calls; retry logs в structlog
- **KPI:** LLM call success rate, retry count

#### Step 3: Unit-тесты для daemon, smart_trigger, model_manager, streaming
- **Цель:** ≥ 60% coverage критичных модулей
- **Scope:** `tests/test_daemon_*`, моки для D-Bus, AudioCapture, ML models
- **Dependencies:** Нет
- **Effort:** M | Риск: Low
- **Owner:** Backend
- **Deliverables:** 15-20 новых тестов, обновлённый coverage exclude
- **Acceptance:** daemon ≥ 60%, smart_trigger ≥ 60%, streaming ≥ 40%
- **KPI:** Coverage % по модулям

#### Step 4: Integration тесты с WAV-файлами
- **Цель:** Проверка реального STT pipeline в CI
- **Scope:** 3 тестовых WAV (5s/30s/silence), pytest с faster-whisper CPU
- **Dependencies:** Step 3
- **Effort:** S | Риск: Medium (CI time)
- **Owner:** Backend/ML
- **Deliverables:** `tests/fixtures/*.wav`, `tests/test_stt_integration.py`
- **Acceptance:** STT WER ≤ 20% на clean audio; CI green
- **KPI:** WER, test duration

#### Step 5: AppImage сборка (#27)
- **Цель:** Распространяемый десктоп-пакет
- **Scope:** `scripts/setup-desktop-toolbox.sh` → `cargo tauri build` → AppImage artifact
- **Dependencies:** Нет
- **Effort:** S | Риск: Medium (toolbox env)
- **Owner:** DevOps
- **Deliverables:** AppImage в GitHub Release, runbook обновлён
- **Acceptance:** AppImage запускается на чистой Fedora 43; D-Bus IPC работает
- **KPI:** Artifact size, startup time

### Phase B: Hardening (security, CI/CD, observability, reliability)

#### Step 6: Observability — structured metrics
- **Цель:** Измеримые метрики для production readiness
- **Scope:** prometheus_client: `stt_duration`, `llm_cost`, `pipeline_errors`, `diarization_duration`, `rag_query_time`
- **Dependencies:** Нет
- **Effort:** M | Риск: Low
- **Owner:** Backend/DevOps
- **Deliverables:** `core/observability.py`, Prometheus endpoint, Grafana dashboard template
- **Acceptance:** 5+ метрик в Prometheus; dashboard с 3+ панелями
- **KPI:** Метрики доступны через `/metrics`

#### Step 7: pyannote memory guard + graceful degradation
- **Цель:** Daemon не падает на ≤8 ГБ RAM
- **Scope:** `pipeline.py` — memory check перед diarization; fallback to no-diarization; warning в UI
- **Dependencies:** Нет
- **Effort:** S | Риск: Low
- **Owner:** Backend/ML
- **Deliverables:** Memory guard в pipeline, тест на fallback
- **Acceptance:** 30-мин аудио на 8 ГБ системе → анализ без crash; log warning
- **KPI:** OOM-free rate

#### Step 8: Budget enforcement — pre-call check
- **Цель:** Предотвращение runaway LLM costs
- **Scope:** `router.py` — pre-call budget check; `config.py` — `daily_budget_limit_usd`; alert log
- **Dependencies:** Нет
- **Effort:** S | Риск: Low
- **Owner:** Backend
- **Deliverables:** Pre-call check, daily limit config, budget alert
- **Acceptance:** LLM-вызов отклоняется при > daily limit; log alert
- **KPI:** Daily spend vs limit

#### Step 9: IPC envelope по умолчанию + timeout
- **Цель:** Надёжный D-Bus контракт
- **Scope:** `daemon.py` — envelope default=True; analyze timeout 120s; desktop compatibility
- **Dependencies:** Step 5 (AppImage)
- **Effort:** S | Риск: Medium (breaking change)
- **Owner:** Backend
- **Deliverables:** Updated daemon, desktop client, D-Bus snapshot test
- **Acceptance:** Envelope active; analyze с timeout; desktop тест green
- **KPI:** D-Bus error rate

#### Step 10: CI optimization — cache ML deps + SBOM desktop
- **Цель:** Быстрый CI, полный SBOM
- **Scope:** `actions/cache@v4` для uv cache; `cargo sbom` в release; unified SBOM
- **Dependencies:** Нет
- **Effort:** S | Риск: Low
- **Owner:** DevOps
- **Deliverables:** Обновлённые workflows, SBOM desktop
- **Acceptance:** CI time ≤ 3 мин; SBOM для Python + Rust в release
- **KPI:** CI duration, SBOM completeness

### Phase C: Scale (perf/cost, data/model scale, throughput)

#### Step 11: Prompt management — вынести промпты из кода
- **Цель:** Версионирование и тестирование промптов
- **Scope:** `llm/prompts/` — YAML файлы; загрузка при старте; snapshot-тесты
- **Dependencies:** Step 1 (eval)
- **Effort:** S | Риск: Low
- **Owner:** ML/Backend
- **Deliverables:** `llm/prompts/*.yaml`, loader, snapshot tests
- **Acceptance:** Промпты в файлах; snapshot test ловит изменения; eval score не деградировал
- **KPI:** Prompt version count, eval score delta

#### Step 12: RAG query improvement — keyword extraction
- **Цель:** Лучший recall RAG при длинных стенограммах
- **Scope:** TF-IDF keyword extraction → multi-query; reranking top-k results
- **Dependencies:** Step 1 (eval), golden RAG dataset
- **Effort:** M | Риск: Medium
- **Owner:** ML
- **Deliverables:** Обновлённый `pipeline.py`, `rag/searcher.py`; eval на RAG recall
- **Acceptance:** RAG recall ≥ 70% на golden set (20 пар query-document)
- **KPI:** RAG recall, query latency

#### Step 13: Data retention policy + auto-cleanup
- **Цель:** Контролируемое хранение PII
- **Scope:** `config.py` — `retention_days`; daemon auto-cleanup; CLI `history --purge-before`
- **Dependencies:** Нет
- **Effort:** S | Риск: Low
- **Owner:** Backend
- **Deliverables:** Retention config, cleanup job, CLI command
- **Acceptance:** Auto-cleanup работает; тест на purge; PII удаляется по расписанию
- **KPI:** DB size trend, PII entries age

#### Step 14: Response caching для повторяющихся анализов
- **Цель:** Снижение LLM costs при повторных запросах
- **Scope:** Content-hash based cache (SQLite); TTL; cache hit rate metric
- **Dependencies:** Step 6 (metrics)
- **Effort:** S | Риск: Low
- **Owner:** Backend
- **Deliverables:** `llm/cache.py`, integration в router
- **Acceptance:** Cache hit rate > 0% при повторных анализах; cost снижение ≥ 10%
- **KPI:** Cache hit rate, cost savings

#### Step 15: Healthcheck + systemd watchdog
- **Цель:** Production-grade daemon monitoring
- **Scope:** `sd_notify(WATCHDOG=1)` в daemon loop; health endpoint в Web UI; structured health check
- **Dependencies:** Step 6 (observability)
- **Effort:** S | Риск: Low
- **Owner:** DevOps/Backend
- **Deliverables:** Watchdog в service unit, health endpoint, health CLI
- **Acceptance:** Daemon restarts при зависании; health доступен через D-Bus/HTTP
- **KPI:** Uptime, restart count

### Phase D: Productization (DX, docs, UX, integrations, governance)

#### Step 16: Desktop UI — reactive D-Bus signals
- **Цель:** Real-time обновления в desktop без polling
- **Scope:** `desktop/src-tauri/src/dbus_signals.rs` — subscribe to ListenStateChanged, AnalysisDone, TranscriptChunk
- **Dependencies:** Step 5 (AppImage), Step 9 (envelope)
- **Effort:** M | Риск: Medium
- **Owner:** Frontend/Backend
- **Deliverables:** Signal handlers в Tauri, reactive UI updates
- **Acceptance:** Desktop обновляется < 1с после события; no polling
- **KPI:** UI latency, event delivery rate

#### Step 17: Telegram bot integration
- **Цель:** Push-уведомления и отчёты в Telegram
- **Scope:** По ADR-0005: webhook, /start, /status, /latest; keyring `webhook_telegram`
- **Dependencies:** Step 8 (budget), Step 9 (envelope)
- **Effort:** M | Риск: Medium
- **Owner:** Backend
- **Deliverables:** `integrations/telegram.py`, webhook handler, runbook
- **Acceptance:** /latest возвращает последний анализ; /status — текущее состояние
- **KPI:** Message delivery rate, user engagement

#### Step 18: Calendar integration — auto-context
- **Цель:** Автоматический RAG-контекст из календаря
- **Scope:** По ADR-0006: CalDAV poll → next meeting → inject context in analysis prompt
- **Dependencies:** Step 12 (RAG improvement)
- **Effort:** M | Риск: Medium
- **Owner:** Backend
- **Deliverables:** `calendar/caldav_poll.py` improvement, auto-context injection
- **Acceptance:** Анализ получает контекст из следующего события календаря
- **KPI:** Context injection rate, analysis quality delta

#### Step 19: Flatpak packaging
- **Цель:** Дистрибуция через Flathub
- **Scope:** `desktop/flatpak/` — манифест, sandbox permissions, D-Bus, PipeWire
- **Dependencies:** Step 5 (AppImage), Step 16 (signals)
- **Effort:** L | Риск: High (sandbox ↔ D-Bus ↔ PipeWire)
- **Owner:** DevOps
- **Deliverables:** Flatpak manifest, CI build, Flathub submission
- **Acceptance:** Flatpak installs and runs; PipeWire + D-Bus + keyring work in sandbox
- **KPI:** Install count, bug reports

#### Step 20: macOS / WSL2 support exploration
- **Цель:** Расширение платформ
- **Scope:** Исследование: CoreAudio (macOS) / PulseAudio (WSL2) вместо PipeWire; D-Bus alternatives
- **Dependencies:** Phase A-C полностью
- **Effort:** L | Риск: High
- **Owner:** Backend/DevOps
- **Deliverables:** ADR для multi-platform; prototype audio capture на macOS
- **Acceptance:** STT pipeline работает на macOS с тестовым WAV
- **KPI:** Platform test matrix pass rate

---

## 6) План усиления сетапа

### Dev environment
- **Текущее:** `make bootstrap` → `uv sync --extra all` → pre-commit install. Работает.
- **Улучшить:** Добавить `make dev` (one-command: bootstrap + pre-commit + generate IDE config). Dockerfile для dev (optional, не обязательно — проект Linux-native).
- **Pre-commit:** Уже настроен (trailing-whitespace, yaml, ruff). Добавить: `ruff format --check` hook, sync versions with uv.lock.
- **Линтеры/форматирование:** Ruff (check + format), MyPy (core/llm/rag/stt). Расширить mypy на `web/`, `calendar/`, `cli/`.

### Secrets
- **Текущее:** gnome-keyring через `keyring` library. Ключи: anthropic, openai, huggingface, google, sonar_token, github_token, и др.
- **Улучшить:** Документировать ротацию ключей (runbook). CI: GitHub Secrets, не keyring. Валидация ключей при `status --doctor`.
- **Политика:** Никогда в `.env`/конфиге; только keyring. CI masking через GitHub Secrets.

### CI
- **Текущее:** 8 workflows. Quality gates: ruff, mypy, pytest, pip-audit, bandit, gitleaks, semgrep, CodeQL, SonarCloud.
- **Улучшить:** Cache ML deps (`actions/cache@v4` для `~/.cache/uv`). SBOM для desktop. Eval job для LLM качества. Coverage upload в Codecov (config есть, использование неясно).
- **Security scans:** Еженедельный `security-weekly.yml` ✓. Добавить: `cargo audit` для Rust deps.

### Release
- **Текущее:** Tag → release-draft → wheel + SBOM. Conventional Commits. CHANGELOG.md.
- **Улучшить:** Автоматический CHANGELOG генерация (release-drafter уже есть). Desktop artifacts в release. Rollback runbook актуален.
- **Версионирование:** semver pre-release (0.2.0a1). Миграции с version target.

### Observability
- **Текущее:** structlog (JSON). Cost tracking в SQLite.
- **Улучшить:** prometheus_client → `/metrics`. Grafana dashboard. Alert на budget > 80%, error rate > 5%.
- **Трассировка:** OpenTelemetry SDK для daemon ↔ LLM ↔ RAG spans.
- **Dashboards:** STT latency, LLM cost/day, pipeline errors, diarization success rate, RAG hit rate.

### Security
- **Текущее:** Keyring, CI scans, SECURITY.md, gitleaks pre-commit, CODEOWNERS, branch protection.
- **Threat model:** Не формализован. Основные поверхности: D-Bus IPC (local), LLM API keys (keyring), PII в transcripts (PII filter), RAG documents (local FS).
- **Supply chain:** pip-audit ✓, dependabot ✓, CodeQL ✓. Добавить: `cargo audit`, npm audit для desktop.
- **Least privilege:** D-Bus capabilities в `desktop/src-tauri/capabilities/default.json`. Systemd unit без root.

### Reliability
- **Текущее:** Pipeline timeout (25s step2), signal handlers (SIGTERM/SIGINT), PID file.
- **Улучшить:** LLM retry (Instructor), circuit breaker, memory guard (pyannote), idempotent analyze.
- **DR/backup:** SQLite WAL mode (проверить). Backup: `cp *.db`. Rollback: `rollback-alpha-release.md` ✓.

---

## 7) AI Quality & Safety plan

### Eval harness
- **Offline eval:** DeepEval + SummarizationMetric; 50 golden transcripts (10 per template); ROUGE-L + LLM-as-judge
- **Online eval:** Sample 5% production analyses; LLM-as-judge score; drift detection (sliding window)
- **CI integration:** `make eval` → pytest `tests/eval/`; threshold: ROUGE-L ≥ 0.4, judge ≥ 3.5/5

### Regression suite для промптов/моделей
- **Prompt snapshots:** Hash промптов в `llm/prompts/`; snapshot test ловит изменения
- **Model regression:** При смене default model → прогон golden set → сравнение scores
- **Baseline:** Зафиксировать scores для Claude Haiku 4.5 / GPT-4o-mini / Gemini Flash

### Monitoring качества
- **Drift:** Скользящее среднее LLM-judge score за 7 дней; alert при drop > 10%
- **Hallucination signals:** Пустые `action_items` при наличии в transcript; `questions` без контекста
- **Latency/cost:** prometheus: `llm_latency_seconds`, `llm_cost_usd`; alert на anomalies

### Guardrails
- **PII:** GLiNER + regex (ON/EMAIL_ONLY/OFF). Расширить: phone, address, credit card patterns.
- **Jailbreak resistance:** System prompt injection guard (не актуально — user = owner, но защита от prompt leak через RAG documents)
- **Output validation:** Pydantic schemas ✓. Добавить: field-level constraints (max length, allowed values)
- **Content safety:** Не требуется (private meetings, не public content)

### Data governance
- **PII:** Фильтр есть. Нет audit trail (кто/когда запрашивал данные).
- **Лицензии:** RAG documents — ответственность пользователя. Модели: faster-whisper (MIT), pyannote (MIT), MiniLM (Apache-2.0).
- **Retention:** Нет policy. Рекомендация: configurable `retention_days`, auto-cleanup.

### Cost controls
- **Budget:** `budget_limit_usd` в config. Pre-call check (planned).
- **Caching:** Claude prompt caching (ephemeral) ✓. Response caching (planned).
- **Batching:** Не применимо (single request per analysis).
- **Model routing:** Ollama $0-path для FAQ ✓. Auto-downgrade при приближении к бюджету (planned).

---

## 8) Research & experiments backlog

| # | Идея | Зачем | Как проверить | Критерий успеха | Риски | Источники |
|---|------|-------|---------------|----------------|-------|-----------|
| R1 | VAD (Voice Activity Detection) перед STT | Уменьшить тишину/шум → лучше accuracy | faster-whisper VAD filter; сравнить WER | WER drop ≥ 5% | False positive (cut speech) | [faster-whisper docs](https://github.com/SYSTRAN/faster-whisper), 2025 |
| R2 | `large-v3-turbo` + int8 quantization | 4x speedup vs large-v3 | Benchmark: latency, WER, RAM | Latency ≤ 50% of large-v3; WER delta ≤ 2% | Accuracy loss on noisy audio | [Modal Whisper variants](https://modal.com/blog/choosing-whisper-variants), 2024 |
| R3 | DeepEval SummarizationMetric | Автоматическая оценка анализа | Golden set + DeepEval pytest | LLM-judge ≥ 3.5/5 | Non-deterministic scores | [DeepEval docs](https://deepeval.com/docs/metrics-summarization), 2025 |
| R4 | Instructor from_litellm | Retry с контекстом ошибки | 100 calls; measure retry rate | retry rate ≤ 5%; success ≥ 99% | Breaking change в API | [Instructor docs](https://python.useinstructor.com/integrations/litellm/), 2025 |
| R5 | pyannote community model | Меньше RAM vs 4.0.4 | Memory profiling; DER comparison | RAM ≤ 4 ГБ; DER delta ≤ 5% | Model quality | [pyannote-audio#1963](https://github.com/pyannote/pyannote-audio/issues/1963), 2025 |
| R6 | sqlite-vec binary quantization | 2x capacity при тех же latency | Benchmark: recall@10, latency | Recall delta ≤ 5%; latency stable | Recall degradation | [sqlite-vec docs](https://github.com/asg017/sqlite-vec), 2025 |
| R7 | OpenTelemetry Python SDK | Distributed tracing daemon→LLM | Instrument pipeline; visualize in Jaeger | Traces видны для full pipeline | Overhead ≤ 5% latency | [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/), 2025 |
| R8 | Whisper streaming (real-time) | Мгновенный транскрипт | Measure latency end-to-end | Partial results ≤ 2s latency | CPU load, accuracy | [faster-whisper streaming](https://github.com/SYSTRAN/faster-whisper), 2025 |
| R9 | Cross-encoder reranking для RAG | Лучший recall/precision | A/B: top-3 results quality | Precision@3 ≥ 80% | Latency +200ms | [sentence-transformers](https://www.sbert.net/docs/cross_encoder/pretrained_models.html), 2025 |
| R10 | Langfuse для prompt analytics | Версионирование промптов, A/B | Integration, 100 calls tracked | Dashboards доступны; cost tracked | Self-hosted complexity | [Langfuse docs](https://langfuse.com/docs), 2025 |
| R11 | Keyword extraction (TF-IDF) для RAG query | Лучше контекст чем prefix truncation | Compare RAG recall: prefix vs keywords | Recall ≥ 70% (vs current ~50%) | Extra processing time | Standard NLP, scikit-learn |
| R12 | Auto-model selection по RAM | Адаптация под железо | Profile RAM; select model_size | No OOM на 4/8/16 ГБ | Complexity | Empirical |
| R13 | Whisper word-level timestamps | Точная синхронизация с diarization | Compare speaker alignment | Alignment error ≤ 0.5s | API complexity | [faster-whisper docs](https://github.com/SYSTRAN/faster-whisper), 2025 |
| R14 | Flatpak portal для PipeWire | Sandbox-safe audio capture | Test in Flatpak sandbox | Audio capture works in sandbox | Portal API complexity | [Flatpak docs](https://docs.flatpak.org/), 2025 |
| R15 | LLM cost prediction | Estimate cost before call | Token count × price; confirm vs actual | Prediction error ≤ 10% | Model-specific pricing | [LiteLLM pricing](https://docs.litellm.ai/docs/completion/token_usage), 2025 |

---

## 9) Risk register

| Risk | Likelihood | Impact | Mitigation | Owner | Status |
|------|-----------|--------|-----------|-------|--------|
| pyannote OOM → daemon crash | High | High | Memory guard, fallback, community model eval | ML/Backend | Open |
| LLM API outage → no analysis | Medium | High | Instructor retry, LiteLLM fallback chain, Ollama local | Backend | Partial (fallback exists, retry weak) |
| Runaway LLM costs | Medium | Medium | Pre-call budget check, daily limit, alerts | Backend | Open |
| PII leak in transcripts | Low | High | PII filter (GLiNER + regex), retention policy | Backend/Security | Partial (filter exists, no retention) |
| CVE in dependencies | Medium | Medium | pip-audit weekly, dependabot, semgrep | DevOps | Active (CVE-2025-69872 tracked) |
| Keyring unavailable (headless/SSH) | Medium | Medium | Env var fallback in secrets.py, documentation | Backend | Mitigated |
| D-Bus IPC breaking change | Low | Medium | Envelope versioning, API version negotiation, snapshot tests | Backend | Partial |
| faster-whisper model download failure | Low | Medium | Model manager cache, offline package | ML/DevOps | Partial |
| Desktop build failure in toolbox | Medium | Low | CI desktop build, check-desktop-deps.sh | DevOps | Open (#27) |
| pyannote license change | Low | Medium | Pin version, evaluate alternatives (NeMo, speechbrain) | ML | Monitoring |
| SonarCloud quality gate drift | Low | Low | Weekly sonar_fetch_issues.py, relaxed gate for alpha | DevOps | Active |
| Single developer bus factor | High | High | Documentation (excellent), agent-aware handoff, runbooks | Product | Mitigated (docs strong) |

---

## 10) "Next actions"

### Следующие 72 часа (5-10 задач)
1. **Закрыть #27:** Завершить AppImage сборку в toolbox (`./scripts/setup-desktop-toolbox.sh` → `cargo tauri build`)
2. **Instructor retry:** `instructor.from_litellm(completion, max_retries=3)` в `complete_structured()` (~30 строк)
3. **Pre-call budget check:** Добавить `get_daily_cost() > limit` проверку перед LLM вызовом в `router.py` (~20 строк)
4. **IPC envelope default=True:** Изменить `default=False` → `default=True` в `daemon.py:314`; обновить snapshot тест
5. **Закрыть #30:** Dismiss dependabot moderate alert вручную
6. **CI cache:** Добавить `actions/cache@v4` для `~/.cache/uv` в `test.yml`

### Следующие 2 недели (5-10 задач)
1. **Eval harness:** Создать `tests/eval/`, 10 golden transcripts, DeepEval integration
2. **Unit-тесты daemon:** 10+ тестов на `VoiceForgeDaemon` с моками (analyze, listen_start/stop, smart_trigger)
3. **pyannote memory guard:** `psutil.virtual_memory()` check → skip diarization если < 2 ГБ free
4. **Промпты в файлы:** Вынести SYSTEM_PROMPT + TEMPLATE_PROMPTS в `llm/prompts/*.yaml`
5. **RAG тесты (#29):** Тесты для ODT/RTF парсеров
6. **scipy в base deps:** Или numpy-based ресэмплинг для гарантии 16kHz
7. **i18n audit:** Заменить оставшиеся русские строки в pipeline.py на t()
8. **Desktop D-Bus signals:** Завершить подписку на ListenStateChanged, AnalysisDone в `dbus_signals.rs`

### Следующие 2 месяца (5-10 задач)
1. **Observability stack:** prometheus_client metrics, Grafana dashboard, structlog JSON → file
2. **Integration тесты:** 3+ WAV-based тестов в CI
3. **Prompt regression suite:** Snapshot тесты, baseline scores per model
4. **Data retention:** `retention_days` config, auto-cleanup в daemon
5. **Response caching:** Content-hash SQLite cache для LLM responses
6. **Healthcheck:** systemd watchdog, structured health endpoint
7. **Flatpak manifest:** Начать с desktop/flatpak/, тест sandbox + D-Bus + PipeWire
8. **Telegram bot:** По ADR-0005, webhook, /start /status /latest
9. **Calendar auto-context:** CalDAV → next meeting → inject context
10. **SBOM desktop:** `cargo sbom` в release pipeline

---

*Документ подготовлен на основе полного аудита кодовой базы (commit 15d1321, branch main, 2026-02-24). Все пути к файлам верифицированы. Секреты не раскрыты.*

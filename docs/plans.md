# Планы и приоритеты (единый документ)

Единый источник правды по планам VoiceForge: roadmap 1–19, Phase A–D (Steps 1–19), оставшееся до 100%. Работа только на текущей системе (Linux); macOS/WSL2 вне скоупа. Детальная история закрытых планов: [history/closed-plans-and-roadmap.md](history/closed-plans-and-roadmap.md). Архив планов: [archive/plans/](archive/plans/). Полный текст аудита 2026-02-26: [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md).

---

## 1. Приоритет внедрения (roadmap 1–19)

| # | Направление | Рейтинг | Статус |
|---|-------------|--------|--------|
| 1 | Шаблоны встреч в `analyze` | 93 | Реализовано |
| 2 | Action items по следующей встрече | 90 | Реализовано |
| 3 | Экспорт сессии (Markdown/PDF) | 82 | Реализовано |
| 4 | Выбор модели Ollama в конфиге | 70 | Реализовано |
| 5 | Документация «Первая встреча за 5 минут» | 73 | Реализовано |
| 6 | Отчёты по затратам | 77 | Реализовано |
| 7 | Явный язык для STT | 81 | Реализовано |
| 8 | Расширенные e2e-тесты | 76 | Реализовано |
| 9 | Стриминговый STT в CLI (listen) | 84 | Реализовано |
| 10 | Live summary во время listen | 88 | Реализовано |
| 11 | Управление PII | 68 | Реализовано |
| 12 | Простой локальный Web UI | 74 | Реализовано |
| 13 | Десктопный UI (Tauri) | 95 | Реализовано |
| 14 | Офлайн-пакет (Flatpak/AppImage) | 85 | Черновик/скрипты |
| 15 | Smart trigger по умолчанию | 55 | Реализовано (default false) |
| 16 | Бот (Telegram) | 72 | Реализовано |
| 17 | Интеграция с календарём (CalDAV) | 78 | Реализовано |
| 18 | RAG: ODT, RTF | 62 | Реализовано |
| 19 | Prompt caching для не-Claude | 58 | Не реализовано (research) |

---

## 2. Phase A–D → Steps 1–19 и GitHub Issues

Единая нумерация: **Phase** (A=Stabilize, B=Hardening, C=Scale, D=Productize), **Step** 1–19, **Issue**. Статус по W1–W20: [audit/audit.md](audit/audit.md).

| Phase | Step | Описание | Issue |
|-------|------|----------|-------|
| **A · Stabilize** | 1 | Eval harness в CI (ROUGE-L) | [#55](https://github.com/iurii-izman/voiceforge/issues/55) |
| A | 2 | Coverage: omit → тесты, fail_under 70→80 | [#56](https://github.com/iurii-izman/voiceforge/issues/56) |
| A | 3 | Sonar quality gate blocking | [#57](https://github.com/iurii-izman/voiceforge/issues/57) |
| A | 4 | Version: importlib.metadata | [#58](https://github.com/iurii-izman/voiceforge/issues/58) |
| A | 5 | .editorconfig + CodeQL blocking | [#59](https://github.com/iurii-izman/voiceforge/issues/59) |
| **B · Hardening** | 6 | /ready + systemd MemoryMax | [#60](https://github.com/iurii-izman/voiceforge/issues/60) |
| B | 7 | Trace IDs (structlog) | [#61](https://github.com/iurii-izman/voiceforge/issues/61) |
| B | 8 | Circuit breaker для LLM | [#62](https://github.com/iurii-izman/voiceforge/issues/62) |
| B | 9 | Periodic purge + backup CLI | [#63](https://github.com/iurii-izman/voiceforge/issues/63) |
| B | 10 | Monitoring stack (Grafana + alerts) | [#64](https://github.com/iurii-izman/voiceforge/issues/64) |
| **C · Scale** | 11 | CVE-2025-69872 (upstream fix) | [#65](https://github.com/iurii-izman/voiceforge/issues/65) |
| C | 12 | Async web (Starlette/Litestar опционально) | [#66](https://github.com/iurii-izman/voiceforge/issues/66) |
| C | 13 | Prompt hash validation | [#67](https://github.com/iurii-izman/voiceforge/issues/67) |
| C | 14 | Benchmark suite | [#68](https://github.com/iurii-izman/voiceforge/issues/68) |
| C | 15 | Единый error format API | [#69](https://github.com/iurii-izman/voiceforge/issues/69) |
| **D · Productize** | 16 | Model A/B testing framework | [#70](https://github.com/iurii-izman/voiceforge/issues/70) |
| D | 17 | OpenTelemetry integration | [#71](https://github.com/iurii-izman/voiceforge/issues/71) |
| D | 18 | Plugin system (custom templates) | [#72](https://github.com/iurii-izman/voiceforge/issues/72) |
| D | 19 | Offline packaging GA (AppImage+Flatpak) | [#73](https://github.com/iurii-izman/voiceforge/issues/73) |

Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

---

## 3. Оставшееся до 100% (полный список)

### 3.1 Текущие (не Phase D)

- **#56 (Step 2):** fail_under=72; цель 75→80%; вывести из omit по одному модулю (server, main, diarizer, rag/*, local_llm) с тестами.
- **#65 (Step 11):** убрать `--ignore-vuln CVE-2025-69872` после фикса upstream (diskcache/instructor).
- **#66 (Step 12):** полная миграция на Starlette/Litestar — опционально; минимальный путь (ThreadingMixIn) выполнен.
- **W17:** снизить когнитивную сложность do_GET/do_POST или отложить до #66.

### 3.2 Phase D (Steps 16–19)

| Step | Issue | Цель | Критерий приёмки |
|------|-------|------|------------------|
| 16 | #70 | A/B testing моделей/промптов | `make eval-ab MODEL_A=haiku MODEL_B=sonnet` → сравнение |
| 17 | #71 | OpenTelemetry (tracing) | Trace в Jaeger: все шаги pipeline с durations |
| 18 | #72 | Plugin system (custom templates) | Custom template из `~/.config/voiceforge/templates/`; eval на custom |
| 19 | #73 | Packaging GA | AppImage: download → chmod +x → run; Flatpak: install → run |

Подробные формулировки (Scope, Effort, KPI): [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md) — раздел «Phase D: Productization».

---

## 4. Что сделано (кратко)

- **Roadmap 1–18:** в коде; см. [history/closed-plans-and-roadmap.md](history/closed-plans-and-roadmap.md).
- **План развития (development-plan) Часть I:** все 10 пунктов реализованы (--template, streaming listen, export, status --detailed, history --search, action items DB, history --date/--from/--to, quickstart, GetAnalytics, status --doctor).
- **Issues #32–49, #51–53:** закрыты. Текущий фокус — только Linux (macOS/WSL2 вне скоупа).
- **Phase A–C (Steps 1–15):** большинство в статусе «СДЕЛАНО»; частично #56, #65, #66, W17. См. [audit/audit.md](audit/audit.md).
- **Phase D (Steps 16–19):** в работе/бэклог; #71 (OTel) — базовая интеграция в работе.

---

## 5. Текущие задачи и фокус

- **В работе / частично:** #56 (coverage 75→80), #65 (CVE), #66 (async web опционально), W17 (S3776), #71 (OTel).
- **Phase D бэклог:** #70 (A/B), #72 (plugins), #73 (packaging GA).

Фокус итерации: [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md). Статус W1–W20: [audit/audit.md](audit/audit.md).

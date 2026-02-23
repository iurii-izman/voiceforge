# VoiceForge — План развития (по аудиту, февраль 2026)

Документ составлен по результатам полного аудита кодовой базы. Каждый пункт проверен против реального состояния кода. **Перед реализацией сверяй с текущим кодом** — часть пунктов могла быть уже закрыта (например export, --template, Ollama config).

---

## Контекст и ограничения

- **ADR-0001:** CLI поверхность заморожена на 9 командах. Новая команда — только через новый ADR. **Флаг к существующей команде не нарушает ADR.**
- Стек: Python 3.12 + uv, faster-whisper, pyannote, LiteLLM + Instructor, SQLite, PipeWire, D-Bus, GLiNER. Ollama — опционально ($0-путь).
- Coverage gate: 80% (85% для нового кода, Python 3.12).

---

## Часть I — 10 приоритетных задач развития

### 1. Флаг `--template` в команде `analyze`

- **Статус в коде (на момент аудита):** ~90% готово. `llm/schemas.py` — 5 схем (StandupOutput, SprintReviewOutput, OneOnOneOutput, BrainstormOutput, InterviewOutput). В `router.py` параметр `template` мог быть заглушен.
- **Что нужно:** `--template` в `analyze` (standup | sprint_review | one_on_one | brainstorm | interview), передача нужной схемы в `complete_structured(response_model=...)`, убрать заглушки.
- **Объём:** ~60–80 строк. Без новой миграции БД.
- **Ценность:** структурированный вывод под тип встречи.

### 2. Streaming-транскрипт в терминале при `listen`

- **Статус в коде:** `stt/streaming.py` (StreamingTranscriber) реализован. Демон транслирует TranscriptChunk через D-Bus. CLI `listen` может не выводить поток в реальном времени.
- **Что нужно:** при `cfg.streaming_stt = True` (или флаг `--stream`) запускать StreamingTranscriber в фоне; в колбэках `on_partial` / `on_final` выводить текст (например через `typer.echo` или stdout).
- **Объём:** ~40–50 строк.
- **Ценность:** живой транскрипт — сильное UX-улучшение.

### 3. `history --format md` — экспорт сессии в Markdown

- **Статус в коде:** `history --id N --output json` возвращает полные данные. Отдельная команда `export` может нарушать ADR-0001 (если в репо уже есть `export` — использовать её).
- **Что нужно:** либо `--format text|json|md` у `history`, либо использование существующей команды `export`. При md: заголовок с датой, таблица сегментов, секции Вопросы/Ответы/Рекомендации/Action items.
- **Объём:** ~60–80 строк в `cli/history_helpers.py`.
- **Ценность:** shareable отчёт без сторонних инструментов.

### 4. `status --detailed` — разбивка затрат по моделям и дням

- **Статус в коде:** `metrics.py` — `get_stats(days=30)` с `by_model`, `by_day`, `total_cost_usd`, `cache_hit_rate`. В `status` показывается лишь часть.
- **Что нужно:** флаг `--detailed`: daily cost за 7/30 дней, by_model, cache hit rate, % от бюджета.
- **Объём:** ~30–40 строк.
- **Ценность:** контроль расходов без прямого SQL.

### 5. Поиск по транскриптам: `history --search "запрос"`

- **Статус в коде:** `TranscriptLog.search_transcripts(query, limit)` реализован (FTS5, snippet). Из CLI не вызывается.
- **Что нужно:** опция `--search TEXT` в `history`, вызов `log_db.search_transcripts(query)`, вывод session_id | start_sec | snippet.
- **Объём:** ~25–30 строк.
- **Ценность:** «найди встречу, где обсуждали X».

### 6. Action items: DB-таблица + cross-session трекинг (миграция 004)

- **Статус в коде:** Action items в JSON в `analyses.action_items`. В `schemas.py` есть ActionItemStatusUpdate, StatusUpdateResponse; может быть уже использованы в `action-items update`.
- **Что нужно:** при необходимости — миграция `004_action_items_table.sql`, обновление SCHEMA_VERSION_TARGET, запись action items в отдельную таблицу, обновление статусов по следующей встрече, `history --action-items`.
- **Объём:** ~200–250 строк при полной реализации с нуля.
- **Ценность:** цикл «встреча → задачи → следующая встреча → статусы».

### 7. `history --date YYYY-MM-DD` и `history --from ... --to ...`

- **Статус в коде:** `TranscriptLog` может иметь `get_sessions_for_date()`, `get_sessions_in_range()` и др. — проверить и подключить к CLI.
- **Что нужно:** опции `--date DATE` и `--from DATE --to DATE` в `history`.
- **Объём:** ~50–70 строк.
- **Ценность:** «что обсуждали за период» одной командой.

### 8. Quick start / «Первая встреча за 5 минут»

- **Статус в коде:** `docs/runbooks/bootstrap.md` — установка; сценария первой встречи может не быть.
- **Что нужно:** `docs/runbooks/quickstart.md` (или аналог) — линейный сценарий: зависимости → ключ → listen → analyze → history → следующие шаги.
- **Объём:** ~80–100 строк Markdown.
- **Ценность:** снижение порога входа для alpha-тестеров.

### 9. GetAnalytics в D-Bus — реальные данные или честное отключение

- **Статус в коде:** `get_analytics()` может возвращать `"{}"` при декларации `"analytics": True` в capabilities.
- **Что нужно:** наполнить `get_analytics(last)` данными из `metrics.get_stats_range()` или убрать `"analytics": True` из capabilities.
- **Объём:** ~40–60 строк или 1 строка (убрать флаг).
- **Ценность:** консистентный контракт D-Bus.

### 10. `voiceforge doctor` как `status --doctor`

- **Статус в коде:** в i18n есть строки `doctor.*`, отдельной команды `doctor` может не быть (ADR не разрешает новую команду без ADR).
- **Что нужно:** реализовать как `status --doctor`: проверки конфига, keyring, RAG db, ring file, Ollama, RAM, импорты; вывод ✓/✗ и fix-suggestions. Использовать существующие i18n-ключи.
- **Объём:** ~50–70 строк.
- **Ценность:** диагностика окружения одной командой.

---

## Часть II — 10 слабых мест (баги и риски)

| # | Проблема | Серьёзность | Что делать | Усилие |
|---|----------|-------------|------------|--------|
| W1 | Бюджет guard: в `metrics.py` захардкожено 75.0 вместо `Settings().budget_limit_usd` | Высокая | Убрать константу, читать из Settings | XS |
| W2 | Транскрибер тихо деградирует при неверном sample_rate (нет ресэмплинга 44.1→16 kHz) | Высокая | Ресэмплинг или явная проверка + warning | S |
| W3 | RAG: в запрос уходит только `transcript[:200]` — мало контекста | Средняя | Увеличить до 1000 или keyword extraction | XS |
| W4 | `privacy_mode` в GetSettings D-Bus, но поля нет в Settings | Низкая | Убрать из get_settings() или добавить в Settings | XS |
| W5 | Instructor не используется — нет retry при невалидном JSON от LLM | Средняя | instructor.from_litellm или try/except + retry | S |
| W6 | main.py не использует i18n (t(key)) — вывод только на русском | Низкая | Заменить строки на t("key"), приоритет ошибки/заголовки | M |
| W7 | D-Bus envelope только при VOICEFORGE_IPC_ENVELOPE=1 | Средняя | Envelope по умолчанию или версия 2.0 с envelope | S |
| W8 | Нет валидации полей Settings (model_size, default_llm и др.) | Средняя | @field_validator для model_size, default_llm, budget_limit_usd, timeout | S |
| W9 | cost_usd в двух БД (transcripts.db и metrics.db) — риск рассинхрона | Низкая | Документировать source of truth или миграция 005 | M |
| W10 | Рискованные модули (daemon, smart_trigger, model_manager, streaming) вне coverage | Средняя | Unit-тесты с моками для ключевых сценариев | M |

Усилия: XS &lt; 20 строк, S &lt; 80 строк, M &lt; 250 строк.

---

## Сводная таблица (Часть I)

| # | Задача | Усилие | Ценность |
|---|--------|--------|----------|
| 1 | --template в analyze | S | ★★★★★ |
| 2 | Streaming в CLI listen | S | ★★★★☆ |
| 3 | history --format md / export | S | ★★★★☆ |
| 4 | status --detailed | XS | ★★★☆☆ |
| 5 | history --search TEXT | S | ★★★★☆ |
| 6 | Action items DB (миграция 004) | M | ★★★★☆ |
| 7 | history --date / --from --to | S | ★★★☆☆ |
| 8 | Quickstart runbook | S | ★★★★☆ |
| 9 | GetAnalytics D-Bus | S | ★★☆☆☆ |
| 10 | doctor как status --doctor | S | ★★★☆☆ |

---

## Порядок реализации (рекомендуемый)

1. Сначала сверять пункты с текущим кодом (часть уже сделана в main).
2. Часть I: по приоритету 1 → 10, учитывая зависимости (например 2 перед live summary).
3. Часть II: W1, W2, W3, W8 — в первую очередь; остальные по возможности.
4. После каждой фичи: тесты, обновление контрактов (config-env-contract.md, CLI surface test), CHANGELOG при user-facing изменениях.
5. **После каждой большой итерации** — по правилам из `docs/runbooks/agent-context.md` (раздел «После каждой большой итерации»): тесты, коммит+пуш, лог изменений, рекомендательные приоритетные задачи, промпт для нового чата, до 5 важных/критических проблем на следующую итерацию, 1 общий совет.

---

## Промпт для реализации в новом чате

Скопируй в начало нового чата (полный промпт также в `docs/runbooks/prompt-implement-development-plan.md`):

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Работай по нему без поиска по проекту. Приоритет фич — docs/roadmap-priority.md. Эффективно и дёшево; ключи в keyring; Fedora Atomic/toolbox/uv.

Реализовать план развития по аудиту февраля 2026: @docs/development-plan-post-audit-2026.md

Порядок:
1. Сверь пункты Части I и II с текущим кодом — что уже сделано (export, --template, Ollama, action-items update), не дублируй.
2. Часть I — задачи 1→10 по одной, начиная с первых нереализованных.
3. Часть II — W1 (бюджет из Settings), W2 (sample_rate), W3 (RAG), W8 (валидация Settings); затем остальные по возможности.
4. После каждой фичи: тесты при необходимости, config-env-contract.md при изменении контракта, CHANGELOG для user-facing. Не нарушать ADR-0001 (флаги к командам — можно, новые команды — только через ADR).
```

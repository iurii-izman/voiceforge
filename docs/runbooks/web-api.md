# Web UI API Contract (alpha0.1)

Source of truth: `src/voiceforge/web/server.py`. Локальный HTTP-сервер без внешних зависимостей (stdlib only).

Запуск: `uv run voiceforge web --port 8765 --host 127.0.0.1`.

## Endpoints

### GET /api/status

Возвращает снимок состояния: RAM, затраты за сегодня, доступность Ollama.

**Ответ (200):** JSON, например:

- `ram.used_gb`, `ram.total_gb`
- `cost_today_usd`
- `ollama_available` (bool)

### GET /api/sessions

Список последних сессий (до 50).

**Ответ (200):** `{ "sessions": [ { "id", "started_at", "ended_at", "duration_sec", "segments_count" }, ... ] }`

### GET /api/sessions/<id>

Детали одной сессии: сегменты транскрипта и анализ (включая `template`, если задан).

**Параметры:** `id` — числовой ID сессии в path.

**Ответ (200):** `{ "session_id", "segments": [ { "start_sec", "end_sec", "speaker", "text" } ], "analysis": { "model", "questions", "answers", "recommendations", "action_items", "cost_usd", "template" } }`

**Ошибки:** 400 (invalid id), 404 (session not found), 500.

### POST /api/analyze

Запуск анализа последних N секунд из кольцевого буфера (опционально с шаблоном встречи).

**Тело (JSON):**

- `seconds` (int, обязательный) — 1..600, по умолчанию 30.
- `template` (str, опционально) — один из: `standup`, `sprint_review`, `one_on_one`, `brainstorm`, `interview`.

**Ответ (200):** `{ "session_id", "display_text", "analysis" }` или при ошибке pipeline: `{ "error", "display_text" }`.

**Ошибки:** 400 (invalid JSON, seconds вне диапазона, неверный template), 500.

### GET /api/export

Скачать сессию в формате Markdown или PDF.

**Параметры (query):**

- `id` (обязательный) — ID сессии.
- `format` — `md` или `pdf`, по умолчанию `md`.

**Ответ (200):**

- Для `format=md`: `Content-Type: text/markdown; charset=utf-8`, тело — Markdown.
- Для `format=pdf`: `Content-Type: application/pdf`, тело — бинарный PDF (требуется pandoc + pdflatex на сервере).

**Ошибки:** 400 (id отсутствует или не числовой, format не md/pdf), 404 (сессия не найдена), 501 (pandoc не установлен для PDF), 500.

### GET /api/cost

Отчёт по затратам LLM за период.

**Параметры (query):**

- `days` (int) — за последние N дней (по умолчанию 30), 1..365. Используется, если не заданы `from` и `to`.
- `from` — начало периода (YYYY-MM-DD).
- `to` — конец периода (YYYY-MM-DD). Если заданы оба `from` и `to`, используется диапазон дат вместо `days`.

**Ответ (200):** `{ "total_cost_usd", "total_calls", "by_day": [ { "date", "cost_usd", "calls" }, ... ] }`

**Ошибки:** 400 (invalid date, from > to), 500.

### POST /api/action-items/update

Обновить статусы action items из одной сессии по транскрипту другой (встреча).

**Тело (JSON):**

- `from_session` (int) — ID сессии, из которой взяты action items.
- `next_session` (int) — ID сессии (встреча), по транскрипту которой обновляются статусы.

**Ответ (200):** `{ "from_session", "next_session", "updates": [ { "id", "status" } ], "cost_usd" }`

**Ошибки:** 400 (отсутствуют параметры или не целые числа), 404 (сессия не найдена), 500.

## Формат ошибок

При 4xx/5xx для JSON-ответов тело имеет вид: `{ "error": "сообщение" }`.

## Связь с CLI

- `voiceforge status` → данные, аналогичные `/api/status` (частично).
- `voiceforge history --last N` / `voiceforge history --id N` → `/api/sessions`, `/api/sessions/<id>`.
- `voiceforge analyze --seconds N [--template T]` → POST `/api/analyze`.
- `voiceforge export --id N --format md|pdf` → GET `/api/export`.
- `voiceforge cost --days N` / `--from` `--to` → GET `/api/cost`.
- `voiceforge action-items update --from-session A --next-session B` → POST `/api/action-items/update`.

# D-Bus контракт для десктопа (com.voiceforge.App)

Источник истины: демон `voiceforge daemon`, интерфейс `com.voiceforge.App`, путь `/com/voiceforge/App`.

При `VOICEFORGE_IPC_ENVELOPE=1` (по умолчанию) методы, возвращающие JSON, оборачиваются в **envelope**:

- Успех: `{ "schema_version": "1.0", "ok": true, "data": { "<key>": <payload> } }`
- Ошибка: `{ "schema_version": "1.0", "ok": false, "error": { "code", "message", "retryable" } }`

## Методы

| Метод | Аргументы | Возврат / ключ в data |
|-------|-----------|-------------------------|
| Ping | — | строка `"pong"` (без envelope) |
| GetSettings | — | envelope `data.settings` (объект) |
| GetSessions | last_n: u32 | envelope `data.sessions` (массив) |
| GetSessionDetail | session_id: u32 | envelope `data.session_detail` (объект) |
| GetAnalytics | last: str (например "7d", "30d") | envelope `data.analytics` (объект) |
| IsListening | — | bool (не envelope) |
| ListenStart | — | void |
| ListenStop | — | void |
| Analyze | seconds: u32, template: str | envelope `data.text` при успехе или `error` |
| GetStreamingTranscript | — | envelope `data.streaming_transcript` (partial, finals) |

## Сигналы

- **ListenStateChanged**(is_listening: bool) — после Start/Stop записи.
- **TranscriptUpdated**(session_id: u32) — обновление транскрипта/сессий (session_id может быть 0).
- **AnalysisDone**(status: str) — завершение анализа, status = "ok" | "error".
- **TranscriptChunk**(text, speaker, timestamp_ms, is_final) — стриминг STT (опционально).

Десктоп подписывается на сигналы **ListenStateChanged**, **AnalysisDone**, **TranscriptChunk** и **TranscriptUpdated** (модуль `dbus_signals`) и обновляет UI по событиям (реактивно); опрос IsListening/GetStreamingTranscript по таймеру используется при инициализации и как fallback.

## Экспорт

Экспорт сессии (Markdown/PDF) в альфа2 выполняется через вызов CLI: `voiceforge export --id <id> --format md|pdf` из Tauri-команды `export_session`.

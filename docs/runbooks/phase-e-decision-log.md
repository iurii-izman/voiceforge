# Phase E Decision Log (E19-E21)

**Обновлено:** 2026-03-09.

Этот документ фиксирует решения по блокам **E19-E21** и убирает двусмысленность для автопилота. Если код, issue или prompt конфликтуют с этим документом, источником истины считаются:

1. Этот decision log
2. [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md)
3. [next-iteration-focus.md](next-iteration-focus.md)

---

## 1. Зафиксированная форма продукта

- **Primary surfaces:** CLI, daemon, Tauri desktop
- **Maintenance-only surfaces:** Web UI, Telegram bot, RAG watcher
- **Narrow investment surface:** Calendar automation на текущем CalDAV stack
- **Future accepted expansion:** managed packaging после Linux beta / стабильного release proof

Коротко: VoiceForge остаётся **Linux-first, local-first, desktop-assisted** продуктом. В Phase E не делаем browser-first pivot, SaaS pivot и multi-user pivot.

---

## 2. Решения по E19-E21

| Block | Issue | Решение | Политика |
|---|---|---|---|
| E19 | [#142](https://github.com/iurii-izman/voiceforge/issues/142) | **Invest in Tauri** | Tauri становится основным GUI surface. После Wave 3 backend/quality брать desktop-first track: E2E meeting flow, tray, hotkeys, packaging verification. |
| E20 | [#143](https://github.com/iurii-izman/voiceforge/issues/143) | **Web UI = Freeze** | Только maintenance: bugfix, contract parity, health/debug/admin. Не превращать в второй основной продуктовый UI, не добавлять SPA и feature parity с desktop без нового решения. |
| E20 | [#143](https://github.com/iurii-izman/voiceforge/issues/143) | **Telegram = Freeze** | Только reliability/notification path: webhook, delivery, summary push. Не развивать rich bot UX, inline flows и bot-first сценарии без нового решения. |
| E20 | [#143](https://github.com/iurii-izman/voiceforge/issues/143) | **Calendar = Invest narrow** | Разрешён только узкий scope: auto-listen / auto-analyze / notify для существующего CalDAV пути. Не добавлять новых провайдеров и не строить calendar platform. |
| E20 | [#143](https://github.com/iurii-izman/voiceforge/issues/143) | **RAG watcher = Freeze** | Только stability/bugfix/coverage. Не добавлять management UI, auto-discovery и крупный UX слой без нового решения. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Managed packaging = Accept later** | Отдельный будущий трек после Linux beta и стабилизации desktop release path. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **macOS / Windows = Defer** | Вернуться только после Linux beta и стабилизации audio/IPC abstractions. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Browser extension = Defer** | Вернуться только если PipeWire останется главным onboarding blocker после setup/package improvements. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **GPU acceleration = Defer** | Вернуться только если CPU latency станет системным bottleneck на реальных сессиях. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Whisper.cpp / MLX = Defer** | Вернуться только если Python/faster-whisper path перестанет укладываться в latency/RAM targets. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Cloud/SaaS = Reject for current phase** | Не выходим за local-first boundary в Phase E. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Web-only main UI = Reject for current phase** | Не делаем architectural pivot away from Tauri. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Real-time collaborative notes = Reject for current phase** | Не делаем server/auth/team-product pivot. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **PostgreSQL + pgvector = Reject for current phase** | SQLite остаётся правильным default для zero-config local-first продукта. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **LLM fine-tuning = Reject for current phase** | Слишком высокий cost/privacy/ops burden для текущего этапа. |

---

## 3. Что разрешено автопилоту

### 3.1 Desktop / Tauri

Разрешено:

- доводить Tauri до desktop-first daily flow
- усиливать tray, hotkeys, onboarding inside desktop, release proof
- добавлять desktop E2E и native smoke coverage

Не делать без нового решения:

- замену Tauri на SPA/Electron как основной UI
- параллельную гонку feature parity между Tauri и Web UI

### 3.2 Web UI

Разрешено:

- bugfix
- contract parity с CLI / daemon / async web
- health, admin, export, debug usability

Не делать без нового решения:

- SPA rewrite
- desktop-level UX polish
- реальный второй основной frontend roadmap

### 3.3 Telegram

Разрешено:

- webhook reliability
- subscribe / delivery fixes
- notifications и summary push

Не делать без нового решения:

- rich bot product
- inline keyboards как отдельный UX track
- bot-first meeting workflow

### 3.4 Calendar

Разрешено:

- CalDAV auto-listen / auto-analyze / notify
- narrow UX improvements around scheduled meetings

Не делать без нового решения:

- Google Calendar / Outlook / Exchange provider expansion
- большой интеграционный слой вне CalDAV

### 3.5 RAG watcher

Разрешено:

- bugfix
- debounce / dedup / reliability / tests

Не делать без нового решения:

- management UI
- auto-discovery
- полноценный knowledge ingestion product surface

---

## 4. Когда пересматривать deferred items

| Item | Триггер пересмотра |
|---|---|
| Managed packaging | Linux beta readiness, стабильный desktop release proof, понятный install/update path |
| macOS / Windows | Linux beta достигнута, audio capture и IPC abstraction выделены явно |
| Browser extension | PipeWire по-прежнему главный blocker после setup/package work |
| GPU acceleration | Реальные пользователи регулярно упираются в latency > target на CPU |
| Whisper.cpp / MLX | faster-whisper/Python path не даёт нужный perf/RAM profile |

Если триггер не выполнен, статус остаётся **defer**.

---

## 5. Практическое правило для новых задач

Перед созданием нового issue или расширением scope задавать вопрос:

> Это усиливает primary path (CLI/daemon/Tauri/calendar narrow), или создаёт новый surface tax?

Если это новый surface tax, задача не должна попадать в автопилот без явного нового решения пользователя.

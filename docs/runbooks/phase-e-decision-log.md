# Phase E Decision Log (E19-E21)

**Обновлено:** 2026-03-14.

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
| KV1 | [#187](https://github.com/iurii-izman/voiceforge/issues/187) | **Legal/consent wording approved** | Формулировки system audio, retention и юрисдикций утверждены. KC11 в scope (opt-in system audio, consent UX, scenario presets). См. [legal-consent-kv1.md](legal-consent-kv1.md). |
| KV5 | [#191](https://github.com/iurii-izman/voiceforge/issues/191) | **Linux-only** | Явный no-go на расширение на Windows/macOS; остаёмся Linux-only. KC13 разблокирован (adaptive/extensibility в рамках Linux). См. [platform-gate-kv5.md](platform-gate-kv5.md). |

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

### 3.6 Project markers

Чтобы board и policy не расходились:

- [#142](https://github.com/iurii-izman/voiceforge/issues/142) должен оставаться `decision-locked` + `primary-track`
- [#143](https://github.com/iurii-izman/voiceforge/issues/143) должен оставаться `decision-locked` + `freeze` + `maintenance-only`
- [#144](https://github.com/iurii-izman/voiceforge/issues/144) должен оставаться `decision-locked`; future items под ним маркируются `defer` или `accept-later`
- будущие placeholders на board: [#148](https://github.com/iurii-izman/voiceforge/issues/148) = managed packaging, [#149](https://github.com/iurii-izman/voiceforge/issues/149) = macOS/Windows, [#150](https://github.com/iurii-izman/voiceforge/issues/150) = browser extension, [#151](https://github.com/iurii-izman/voiceforge/issues/151) = GPU / Whisper.cpp / MLX

---

## 4. Entry gate для E19 (desktop-first track)

Автопилот переходит в активный desktop-first режим только если выполнены все условия:

- E13, E14 и E15 завершены или явно переупорядочены новым решением пользователя
- [next-iteration-focus.md](next-iteration-focus.md) и [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) указывают на [#142](https://github.com/iurii-izman/voiceforge/issues/142) как на следующий track
- Web UI, Telegram и RAG watcher по-прежнему остаются maintenance-only
- Calendar по-прежнему остаётся в narrow CalDAV scope
- desktop work остаётся Linux-first / Tauri-first и не превращается в web-only pivot

Если хотя бы одно условие не выполнено, автопилот не должен открывать новый frontend scope и должен вернуться к текущему wave order.

---

## 5. Когда пересматривать deferred items

| Item | Триггер пересмотра |
|---|---|
| Managed packaging | Linux beta readiness, стабильный desktop release proof, понятный install/update path |
| macOS / Windows | Linux beta достигнута, audio capture и IPC abstraction выделены явно |
| Browser extension | PipeWire по-прежнему главный blocker после setup/package work |
| GPU acceleration | Реальные пользователи регулярно упираются в latency > target на CPU |
| Whisper.cpp / MLX | faster-whisper/Python path не даёт нужный perf/RAM profile |

Если триггер не выполнен, статус остаётся **defer**.

---

## 6. Практическое правило для новых задач

Перед созданием нового issue или расширением scope задавать вопрос:

> Это усиливает primary path (CLI/daemon/Tauri/calendar narrow), или создаёт новый surface tax?

Если это новый surface tax, задача не должна попадать в автопилот без явного нового решения пользователя.

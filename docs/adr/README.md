# ADR (Architecture Decision Records)

Решения по архитектуре и процессу. Нумерация последовательная.

| Номер | Файл | Суть |
|-------|------|------|
| 0001 | [0001-core-scope-0.1.md](0001-core-scope-0.1.md) | Core scope alpha 0.1; заморозка 9 CLI-команд; новые команды — только через ADR. |
| 0002 | [0002-action-items-table.md](0002-action-items-table.md) | Таблица action_items, миграция 005, history --action-items. |
| — | [0002-archive-first-cleanup.md](0002-archive-first-cleanup.md) | **Superseded (исторический):** политика архивации до zero-reset. |
| 0003 | [0003-version-reset-0.1-alpha1.md](0003-version-reset-0.1-alpha1.md) | Сброс версии на 0.1.0-alpha.1. |
| 0004 | [0004-desktop-tauri-dbus.md](0004-desktop-tauri-dbus.md) | Десктоп: Tauri 2, единственный бэкенд — D-Bus (демон). |
| 0005 | [0005-telegram-bot.md](0005-telegram-bot.md) | Telegram-бот: webhook через `voiceforge web` (/api/telegram/webhook), ключ keyring `webhook_telegram`. |

При добавлении нового ADR: следующий номер (0005, 0006, …), имя файла `NNNN-краткое-название.md`.

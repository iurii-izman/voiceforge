# ADR-0005: Telegram bot (optional); webhook via existing Web UI

Status: Accepted

## Context

- Roadmap 16: бот (Telegram/Slack) — нишевый сценарий после стабилизации продукта.
- Токен бота хранится в keyring: сервис `voiceforge`, ключ `webhook_telegram` (см. keyring-keys-reference.md).
- Нужна точка входа для Telegram без добавления новой CLI-команды (ADR-0001: заморозка 9 команд).

## Decision

- **Telegram bot** — опциональный компонент. Не обязателен для работы CLI/daemon/desktop.
- **Точка входа:** webhook обрабатывается в существующем HTTP-сервере `voiceforge web`: путь `POST /api/telegram/webhook` (и при необходимости `GET` для проверки/установки webhook). Новой CLI-команды не вводим.
- **Ключ:** `get_api_key("webhook_telegram")` — токен бота. Если ключа нет, обработчик Telegram не регистрируется или возвращает 503.
- **Команды бота (первый минимум):** `/start` — приветствие; `/status` — краткий статус (RAM, cost today, Ollama), данные через те же хелперы, что и Web UI (`get_status_data()`).
- **Архитектура:** один HTTP-сервер (web) обслуживает и Web UI, и Telegram webhook. Демон не обязан быть запущен для ответов бота: бот вызывает те же слои (config, status_helpers, metrics), что и `voiceforge status` / Web UI. Для сценариев «запустить анализ из бота» позже можно вызывать CLI или D-Bus (отдельное решение).
- **Безопасность:** webhook URL должен быть HTTPS в продакшене (ngrok/прокси). Локально — только для разработки/тестов.

## Consequences

- Пользователь с ключом `webhook_telegram` может включить бота, запустив `voiceforge web` и настроив Telegram на этот URL (с HTTPS при необходимости).
- Добавление команд (например `/sessions`, `/analyze`) — последующие итерации; контракт команд и формат ответов можно расширять без нового ADR.
- Slack или иные боты — отдельные ADR при появлении спроса.

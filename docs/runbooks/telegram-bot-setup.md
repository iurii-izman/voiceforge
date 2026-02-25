# Telegram bot (ADR-0005): включение и настройка

Бот опционален. Webhook обрабатывается в `voiceforge web` по пути `POST /api/telegram/webhook`. Ключ в keyring: сервис `voiceforge`, имя **`webhook_telegram`** (токен бота от @BotFather).

## 1. Ключ в keyring

```bash
keyring set voiceforge webhook_telegram
# ввести токен бота (например 123456:ABC-DEF...)
```

Проверка (без вывода значения):

```bash
uv run python -c "from voiceforge.core.secrets import get_api_key; print('ok' if get_api_key('webhook_telegram') else 'absent')"
```

## 2. Запуск Web UI (с ботом)

```bash
uv run voiceforge web --port 8765
```

Если ключ есть, Telegram может слать обновления на этот сервер. Локально нужен **доступный из интернета URL** (ngrok, туннель или публичный хост).

## 3. Установка webhook в Telegram

После того как сервер доступен по HTTPS (обязательно для продакшена):

```bash
# Подставить YOUR_TOKEN и YOUR_HTTPS_URL (например https://your-domain.com/api/telegram/webhook)
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=YOUR_HTTPS_URL/api/telegram/webhook"
```

Локально для теста — туннель с HTTPS (обязателен для Telegram webhook):

**ngrok:**
```bash
ngrok http 8765
# взять https://....ngrok.io и: curl "https://api.telegram.org/botTOKEN/setWebhook?url=https://....ngrok.io/api/telegram/webhook"
```

**cloudflared (альтернатива):**
```bash
cloudflared tunnel --url http://127.0.0.1:8765
# в выводе будет https://....trycloudflare.com — подставить в setWebhook как выше
```

## 4. Команды бота

- `/start` — приветствие и список команд.
- `/help` — список команд (как /start).
- `/status` — краткий статус: RAM, затраты за сегодня, Ollama.
- `/sessions` — последние 10 сессий (id, дата, длительность).
- `/latest` — последний анализ (сессия + первый ответ или «нет анализов»).
- `/cost [дней]` — затраты за период (по умолчанию 7 дней; до 365).
- `/subscribe` — включить push-уведомления: после этой команды бот сохранит ваш chat_id в keyring (`telegram_chat_id`), и при каждом завершении анализа (CLI, Web UI или демон) вам придёт короткое сообщение в Telegram.

Дальше: `/analyze` и др. — по необходимости.

## 5. Push-уведомления по завершении analyze

После команды `/subscribe` в боте при успешном завершении анализа (команда `voiceforge analyze`, кнопка «Анализ» в Web UI или срабатывание smart trigger в демоне) в Telegram отправляется сообщение с номером сессии и началом результата. Ключи: `webhook_telegram` (токен бота) и `telegram_chat_id` (записывается автоматически при `/subscribe`). Если `telegram_chat_id` не задан, уведомления не отправляются.

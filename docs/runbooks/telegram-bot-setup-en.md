# Telegram bot (ADR-0005): enabling and configuration

The bot is optional. The webhook is handled by `voiceforge web` at `POST /api/telegram/webhook`. Key in keyring: service `voiceforge`, name **`webhook_telegram`** (bot token from @BotFather).

## 1. Key in keyring

```bash
keyring set voiceforge webhook_telegram
# enter the bot token (e.g. 123456:ABC-DEF...)
```

Check (without printing the value):

```bash
uv run python -c "from voiceforge.core.secrets import get_api_key; print('ok' if get_api_key('webhook_telegram') else 'absent')"
```

## 2. Running the Web UI (with the bot)

```bash
uv run voiceforge web --port 8765
```

If the key is set, Telegram can send updates to this server. Locally you need a **publicly reachable URL** (ngrok, tunnel, or public host).

## 3. Setting the webhook in Telegram

Once the server is reachable over HTTPS (required for production):

```bash
# Replace YOUR_TOKEN and YOUR_HTTPS_URL (e.g. https://your-domain.com/api/telegram/webhook)
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=YOUR_HTTPS_URL/api/telegram/webhook"
```

For local testing — use a tunnel with HTTPS (required for Telegram webhook):

**ngrok:**
```bash
ngrok http 8765
# take https://....ngrok.io and: curl "https://api.telegram.org/botTOKEN/setWebhook?url=https://....ngrok.io/api/telegram/webhook"
```

**cloudflared (alternative):**
```bash
cloudflared tunnel --url http://127.0.0.1:8765
# output will show https://....trycloudflare.com — use that in setWebhook as above
```

## 4. Bot commands

- `/start` — greeting and list of commands.
- `/help` — list of commands (same as /start).
- `/status` — short status: RAM, cost today, Ollama.
- `/sessions` — last 10 sessions (id, date, duration).
- `/latest` — latest analysis (session + first answer or "no analyses yet").
- `/cost [days]` — cost for the period (default 7 days; up to 365).
- `/subscribe` — enable push notifications: the bot stores your chat_id in keyring (`telegram_chat_id`), and when an analysis completes (CLI, Web UI, or daemon) you get a short message in Telegram.

Further: `/analyze` etc. — as needed.

## 5. Push notifications when analyze completes

After sending `/subscribe` in the bot, whenever an analysis finishes successfully (`voiceforge analyze`, Web UI "Analyze" button, or daemon smart trigger), a Telegram message is sent with the session id and the start of the result. Keys: `webhook_telegram` (bot token) and `telegram_chat_id` (set automatically by `/subscribe`). If `telegram_chat_id` is not set, no notifications are sent.

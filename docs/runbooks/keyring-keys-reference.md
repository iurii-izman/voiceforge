# Keyring keys reference (voiceforge service)

Список имён ключей в keyring (service=`voiceforge`) для справки агента и автоматизации. Значения хранятся только в keyring, не в репо.

| Key name | Назначение |
|----------|------------|
| `anthropic` | Anthropic API (Claude) |
| `openai` | OpenAI API |
| `huggingface` | Hugging Face (pyannote, STT) |
| `google` | Google / Gemini API |
| `sonar_token` | SonarCloud (CI, quality gate, API) |
| `github_token` | GitHub (API, push) |
| `github_token_pat` | GitHub Personal Access Token |
| `codecov_token` | Codecov |
| `codecov_token_codecov.yml` | Codecov (workflow) |
| `webhook_telegram` | Telegram webhook (bot token) |
| `telegram_chat_id` | Telegram chat for push notifications (set by bot `/subscribe`) |
| `b24webhook` | Bitrix24 webhook |
| `MCPcode` | Прочие сервисы |
| `caldav_url` | CalDAV calendar URL (e.g. https://nextcloud.example.com/remote.php/dav) |
| `caldav_username` | CalDAV login |
| `caldav_password` | CalDAV password or token |

Проверка доступа (без вывода значений):
```bash
uv run python -c "
from voiceforge.core.secrets import get_api_key
for name in ('anthropic','openai','huggingface','sonar_token','github_token'):
    print(name, ':', 'present' if get_api_key(name) else 'absent')
"
```

Использование в скриптах: брать токен через `get_api_key('sonar_token')` и т.д.; не логировать и не коммитить значения.

# Первая встреча за 5 минут (alpha0.1)

Краткий сценарий: записать аудио → разобрать встречу → посмотреть историю и экспорт.

## 1. Установка и проверка

```bash
./scripts/bootstrap.sh
uv run voiceforge status
```

Ключи API хранятся в **keyring** (сервис `voiceforge`):

```bash
keyring set voiceforge anthropic
keyring set voiceforge openai
keyring set voiceforge huggingface   # если нужен pyannote
```

## 2. Запись в кольцевой буфер

В отдельном терминале или в фоне:

```bash
uv run voiceforge listen
```

Идёт запись с микрофона в кольцевой буфер (по умолчанию последние 5 минут). Остановка: Ctrl+C.

## 3. Анализ фрагмента

После встречи или во время паузы:

```bash
uv run voiceforge analyze --seconds 60
```

Разбор последних 60 секунд: транскрипция → диарзация → RAG → LLM. Результат выводится в консоль и пишется в лог сессий.

Шаблоны встреч (приоритет 1):

```bash
uv run voiceforge analyze --template standup
uv run voiceforge analyze --template one_on_one
# standup | sprint_review | one_on_one | brainstorm | interview
```

## 4. История и экспорт

Список сессий:

```bash
uv run voiceforge history --last 10
```

Детали сессии и экспорт в файл:

```bash
uv run voiceforge history --id 1
uv run voiceforge export --id 1 --format md -o meeting.md
uv run voiceforge export --id 1 --format pdf   # опционально: нужны pandoc и pdflatex (dnf install pandoc texlive-scheme-basic)
```

## 5. Отчёт по затратам

Затраты LLM за период (из БД метрик):

```bash
uv run voiceforge cost --days 30
uv run voiceforge cost --from 2025-01-01 --to 2025-01-31   # за период
uv run voiceforge cost --days 7 --output json
```

## 6. Действия по следующей встрече (приоритет 2)

Обновить статусы action items из сессии 1 по транскрипту сессии 2:

```bash
uv run voiceforge action-items update --from-session 1 --next-session 2
```

Статусы сохраняются в `~/.local/share/voiceforge/action_item_status.json` (или `XDG_DATA_HOME/voiceforge/`).

## 7. Настройки

Конфиг: `~/.config/voiceforge/voiceforge.yaml` или `voiceforge.yaml` в текущей папке. Переменные окружения `VOICEFORGE_*` имеют приоритет.

Основные опции:

- **ollama_model** — модель Ollama для локальных ответов (по умолчанию `phi3:mini`).
- **language** — язык для STT: `auto` (из LANG), `ru`, `en`.
- **pii_mode** — маскирование PII перед LLM: `OFF`, `ON`, `EMAIL_ONLY`.
- **streaming_stt** — показывать partial/final транскрипт во время `listen` (true/false).
- При запуске `listen` можно указать `--live-summary` для периодического краткого саммари по последним 90 с.

Подробнее: `docs/runbooks/config-env-contract.md`, приоритеты фич: `docs/roadmap-priority.md`.

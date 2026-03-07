# CLI: все команды, сборка и запуск

Справочник всех команд VoiceForge, когда пересобирать, как запускать демон и полный стек. Рекомендуемая среда: **toolbox** (Fedora 43: `fedora-toolbox-43`).

---

## 1. Список команд (voiceforge)

Источник правды: `voiceforge --help` и `voiceforge <команда> --help`. Если запустить `voiceforge` без команды — выведется справка (то же, что `voiceforge --help`). ADR-0001 расширен; ниже — полный перечень.

| Команда | Назначение |
|---------|------------|
| **listen** | Запись с микрофона/монитора в кольцевой буфер (последние N мин). Опции: `--stream` (стриминг транскрипта), `--live-summary` (периодический саммари). Остановка: Ctrl+C. |
| **analyze** | Запуск пайплайна (STT → diarization → RAG → LLM) по последним N секундам из буфера. Обязательно: `--seconds N` (1–600). Опционально: `--template standup \| sprint_review \| one_on_one \| brainstorm \| interview`. Перед первым analyze нужен listen (или демон с записью). |
| **status** | Снимок состояния: RAM, затраты за сегодня, Ollama. Опции: `--detailed` (разбивка по моделям/дням), `--doctor` (диагностика окружения), `--output json`. |
| **history** | Список сессий или детали одной. Опции: `--last N`, `--id N`, `--search "текст"`, `--date YYYY-MM-DD`, `--from`/`--to`, `--action-items`, `--output text \| json \| md`. |
| **cost** | Отчёт по затратам на LLM. Опции: `--days N`, `--from`/`--to`, `--output text \| json`. |
| **export** | Экспорт сессии в файл. Обязательно: `--id N`, `--format md \| pdf`. Опционально: `-o file.md`. Для PDF нужны pandoc и pdflatex. |
| **action-items update** | Обновление статусов action items по тексту следующей встречи. Опции: `--from-session N`, `--next-session M`. |
| **index** | Индексация каталога в RAG (добавление документов в базу). Опции: путь к папке, форматы по [rag-formats.md](rag-formats.md). |
| **watch** | Слежение за каталогом и автоиндексация при изменениях. |
| **daemon** | Запуск демона: D-Bus-сервис, запись в буфер, smart trigger (опционально). Один процесс на сессию. Для десктопа и Web UI демон должен быть запущен. |
| **install-service** | Установка пользовательского systemd-юнита для демона. |
| **uninstall-service** | Удаление пользовательского юнита. |
| **web** | Локальный HTTP-сервер (Web UI): статус, сессии, анализ, затраты, action-items. Опции: `--port`, `--host`. С опцией `--async` (или `VOICEFORGE_WEB_ASYNC=1`) — Starlette+uvicorn (нужен `uv sync --extra web-async`). |
| **backup** | Копирование БД (transcripts, metrics, RAG) в timestamped-каталог. Опция `--keep N` — оставить только последние N бэкапов. |
| **calendar poll** | Опрос CalDAV (keyring: caldav_url, caldav_username, caldav_password). Опции: `--minutes`, `--output`. |

**Единый формат --output (block 53):** команды `status`, `cost`, `history`, `calendar *`, `analyze` и др. поддерживают `--output text` (по умолчанию) и `--output json`. При `--output json` ответ всегда в виде envelope: успех — `{ "ok": true, "data": ... }`, ошибка — `{ "ok": false, "error": { "code": "...", "message": "..." } }`. Предсказуемый парсинг для скриптов и CI.

Проверка ключей в keyring (без вывода значений):

```bash
uv run python -c "
from voiceforge.core.secrets import get_api_key
for name in ('anthropic','openai','huggingface'):
    print(name, ':', 'present' if get_api_key(name) else 'absent')
"
```

---

## 2. Сборка и когда пересобирать

| Что меняли | Действие |
|------------|----------|
| Только Python (backend, CLI) | Перезапуск демона и/или `uv run voiceforge ...`; **ребилд десктопа не нужен**. |
| Зависимости Python (pyproject.toml) | `uv sync --extra all` (или нужный extra). |
| Frontend (Vite/TS в `desktop/`) или Tauri (Rust в `desktop/src-tauri/`) | Ребилд десктопа: `cd desktop && npm run build && cargo tauri build`. Для разработки: `cd desktop && npm run tauri dev` (hot reload при изменении фронта). |
| Конфиг Tauri / npm / Cargo | `cd desktop && npm install` при смене npm-зависимостей; при необходимости обновить Cargo, затем полный билд. |

Итого: после правок только в Python пересобирать десктоп не требуется. После правок в `desktop/` — либо `npm run tauri dev`, либо полный `npm run tauri build`.

---

## 3. Как запускать полный стек (рекомендуется toolbox)

- **Вход в toolbox:** на хосте `toolbox enter` (или `toolbox enter fedora-toolbox-43`). Все команды ниже — внутри toolbox, из каталога репо: `cd /var/home/user/Projects/voiceforge`.

- **Один раз подготовка:**
  ```bash
  ./scripts/bootstrap.sh
  uv sync --extra all
  uv run voiceforge status --doctor
  ```

- **Демон (обязателен для десктопа и для «фона»):** в одном терминале:
  ```bash
  uv run voiceforge daemon
  ```

- **Второй терминал (toolbox enter снова):** CLI или десктоп:
  - Запись и анализ: `uv run voiceforge listen` → в другом окне `uv run voiceforge analyze --seconds 30`
  - Web UI: `uv run voiceforge web` (или `uv run voiceforge web --async` при установленном `web-async`)
  - Десктоп: `cd desktop && npm run tauri dev` (или запуск собранного бинарника)

- **Почему toolbox:** на Fedora Atomic нет части пакетов на хосте; в toolbox есть Python 3.12+, Node, Rust, WebKit/GTK. Репозиторий на хосте доступен в контейнере по тому же пути. Подробнее: [installation-guide.md](installation-guide.md) (раздел 0).

---

## 4. Ссылки

- Установка и окружение: [installation-guide.md](installation-guide.md)
- Первая встреча за 5 минут: [quickstart.md](quickstart.md), [../first-meeting-5min.md](../first-meeting-5min.md)
- Конфиг и ключи: [config-env-contract.md](config-env-contract.md), [keyring-keys-reference.md](keyring-keys-reference.md)
- Web API: [web-api.md](web-api.md)
- Сборка десктопа: [desktop-build-deps.md](desktop-build-deps.md)

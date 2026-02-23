# Quick start — первая встреча за 5 минут

Линейный сценарий для alpha-тестеров. Полная версия: [../first-meeting-5min.md](../first-meeting-5min.md).

## Порядок действий

1. **Зависимости и ключи**
   - `./scripts/bootstrap.sh` → `uv sync --extra all`
   - Проверка: `uv run voiceforge status` или `uv run voiceforge status --doctor`
   - Ключи в keyring: `keyring set voiceforge anthropic`, `openai`, `huggingface` (см. [config-env-contract.md](config-env-contract.md))

2. **Запись**
   - `uv run voiceforge listen` — запись в кольцевой буфер (последние 5 мин). Остановка: Ctrl+C.

3. **Анализ**
   - `uv run voiceforge analyze --seconds 60` — разбор последних 60 с (STT → diarization → RAG → LLM)
   - Шаблоны: `--template standup | one_on_one | sprint_review | brainstorm | interview`

4. **История и экспорт**
   - `uv run voiceforge history --last 10` — список сессий
   - `uv run voiceforge history --id N` — детали сессии; `--output md` — вывод в Markdown в stdout
   - `uv run voiceforge history --search "текст"` — поиск по транскриптам
   - `uv run voiceforge history --date 2026-02-23` или `--from YYYY-MM-DD --to YYYY-MM-DD`
   - `uv run voiceforge export --id N --format md` — экспорт в Markdown (всегда доступен)
   - `uv run voiceforge export --id N --format pdf` — экспорт в PDF **опционален**: нужны `pandoc` и `pdflatex` (например `dnf install pandoc texlive-scheme-basic`). Без них выводится подсказка, Markdown сохраняется во временный файл.

5. **Затраты и диагностика**
   - `uv run voiceforge cost --days 30` — отчёт по затратам
   - `uv run voiceforge status --detailed` — разбивка по моделям/дням и % от бюджета
   - `uv run voiceforge status --doctor` — проверка окружения

6. **Десктоп (Tauri)**
   - Сборка: см. [desktop-build-deps.md](desktop-build-deps.md); из корня `./scripts/check-desktop-deps.sh`, затем `cd desktop && npm install && npm run tauri dev`.
   - Перед запуском десктопа обязательно запустите демон: `voiceforge daemon` (в отдельном терминале или как сервис).

7. **Следующие шаги**
   - Action items: `uv run voiceforge action-items update --from-session 1 --next-session 2`
   - Конфиг и переменные: [config-env-contract.md](config-env-contract.md)
   - Приоритет фич: [../roadmap-priority.md](../roadmap-priority.md)

# Prompt management (C1, #41)

Промпты LLM вынесены из кода в файлы. Версионирование и загрузка — через `voiceforge.llm.prompt_loader`.

## Расположение

- **Каталог:** `src/voiceforge/llm/prompts/`
- **Файлы:**
  - `analysis.txt` — системный промпт для общего анализа встречи
  - `live_summary.txt` — live summary во время listen
  - `status_update.txt` — статус-апдейт
  - `template_standup.txt`, `template_sprint_review.txt`, `template_one_on_one.txt`, `template_brainstorm.txt`, `template_interview.txt` — промпты по шаблонам встреч
  - `version` — опциональная метка версии набора промптов (показывается в `status --detailed`)

## Загрузка

- `load_prompt(name)` — загружает `prompts/<name>.txt`, возвращает `None` если файла нет
- `load_template_prompts()` — загружает все `template_*.txt`, возвращает `None` если хотя бы один отсутствует
- `get_prompt_version()` — читает `prompts/version`, возвращает `None` если файла нет или он пустой

В `router.py` при отсутствии файлов используются fallback-промпты из кода.

## Изменение промптов

1. Редактировать нужный `.txt` в `src/voiceforge/llm/prompts/`.
2. При необходимости обновить `version`.
3. Запустить тесты: `uv run pytest tests/test_prompt_loader.py -v`. Snapshot-тест `test_prompt_content_snapshot` упадёт при изменении содержимого — обновить ожидаемые хэши в тесте (константа `expected` в `test_prompt_content_snapshot`).

## Тесты

- `tests/test_prompt_loader.py` — загрузка, наличие контента, snapshot по хэшам содержимого (регрессия при случайном изменении).

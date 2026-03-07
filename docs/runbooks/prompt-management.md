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

В `router.py` при отсутствии файлов используются fallback-промпты из кода. **Block 6 (#67):** при использовании fallback пишется предупреждение в лог (`prompt_loader_fallback`, prompt=…, reason="file missing").

## Изменение промптов

1. Редактировать нужный `.txt` в `src/voiceforge/llm/prompts/`.
2. При необходимости обновить `version`.
3. Запустить тесты: `uv run pytest tests/test_prompt_loader.py -v`. Snapshot-тест `test_prompt_content_snapshot` упадёт при изменении содержимого — обновить ожидаемые хэши в тесте (константа `expected` в `test_prompt_content_snapshot`).

## Целостность (hash / CI). Block 6 (#67)

- **Хэши:** `get_prompt_hashes()` в `prompt_loader` возвращает SHA256 по каждому промпту (для скриптов/CI).
- **CI:** тест `test_prompt_content_snapshot` в `tests/test_prompt_loader.py` проверяет совпадение хэшей с эталоном; при изменении промптов нужно обновить словарь `expected` в этом тесте.

## Prompt caching (block 66, #90)

**Текущее состояние:** для моделей Claude в `router.py` при формировании сообщений используется `cache_control: {"type": "ephemeral"}` (system-контент) в `_build_analysis_messages`, `analyze_live_summary` и `update_action_item_statuses`. Это снижает стоимость и задержки при повторных вызовах с тем же системным промптом.

**Не-Claude (Ollama, OpenAI и др.):** параметры кэширования зависят от провайдера и LiteLLM. Для расширения на другие модели нужно смотреть документацию LiteLLM и конкретного провайдера (например [Anthropic prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching), аналоги для других API) и при необходимости добавлять соответствующие поля в сообщения или опции вызова в `router.py`.

## Custom templates (Phase D #72)

Шаблоны встреч можно переопределить пользовательскими: положите `template_<name>.txt` в `~/.config/voiceforge/templates/` (или в `$XDG_CONFIG_HOME/voiceforge/templates/`). При вызове `analyze`, `eval` и `make eval-ab` загрузка идёт через `load_prompt()` — сначала проверяется пользовательский каталог, затем встроенные файлы в `prompts/`. Таким образом, **eval и eval-ab используют custom-шаблоны**, когда они присутствуют.

Пример: скопируйте `src/voiceforge/llm/prompts/template_standup.txt` в `~/.config/voiceforge/templates/template_standup.txt`, отредактируйте — при следующем запуске `analyze` или `make eval-ab` будет использоваться ваша версия.

## Тесты

- `tests/test_prompt_loader.py` — загрузка, наличие контента, snapshot по хэшам содержимого (регрессия при случайном изменении), загрузка custom-шаблона из пользовательского каталога (#72).

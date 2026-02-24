# RAG: поддерживаемые форматы и план расширения (roadmap 18)

Текущее состояние индексатора знаний и план добавления форматов ODT/RTF.

## Текущее состояние

- **Модуль:** `src/voiceforge/rag/indexer.py` — класс `KnowledgeIndexer`; парсеры в `voiceforge.rag.parsers`.
- **Расширения и парсеры:** в `indexer.py` заданы `_SUPPORTED_EXTENSIONS` и `_PARSERS`; в `main.py` для команды `index` используется тот же набор расширений `_INDEX_EXTENSIONS`.

Поддерживаемые форматы:

| Расширение | Парсер | Примечание |
|------------|--------|------------|
| `.pdf` | `parse_pdf` | PDF → текст по страницам |
| `.md`, `.markdown` | `parse_markdown` | Markdown |
| `.html`, `.htm` | `parse_html` | HTML |
| `.docx` | `parse_docx` | Word (Office Open XML) |
| `.txt` | `parse_txt` | Plain text |

Файлы с другими расширениями при `voiceforge index <path>` пропускаются (сообщение «unsupported format» или «skip»).

## План: ODT и RTF

- **ODT (OpenDocument Text):** формат LibreOffice/OpenOffice. Вариант реализации — библиотека `odfpy` (чтение ODT, извлечение текста). Добавить в `voiceforge.rag.parsers` функцию `parse_odt`, зарегистрировать в `indexer.py` расширение `.odt` и парсер; при добавлении — тест на примере ODT-файла и обновление этого runbook.
- **RTF (Rich Text Format):** распространённый обменный формат. Вариант реализации — библиотека `striprtf` (или аналог) для извлечения текста. Добавить `parse_rtf` в parsers, расширение `.rtf` в indexer; при добавлении — тесты и обновление runbook.

Порядок внедрения — по желанию (ODT часто нужнее для офисных сценариев). Реализацию выполнять отдельной итерацией: зависимости в `pyproject.toml`, парсеры, регистрация в indexer, тесты, обновление данного документа.

## Правила при добавлении форматов

1. Парсер: функция с сигнатурой, совместимой с остальными (например путь к файлу → список строк по «страницам»/секциям).
2. Зарегистрировать расширение в `_SUPPORTED_EXTENSIONS` и `_PARSERS` в `indexer.py`; при наличии дублирования в `main.py` (`_INDEX_EXTENSIONS`) — синхронизировать.
3. Добавить тесты (unit для парсера и/или интеграционный тест `voiceforge index` на файле нового типа).
4. Обновить этот runbook (таблица форматов, при необходимости — зависимости в `dependencies.md`).

## См. также

- [dependencies.md](dependencies.md) — политика зависимостей и добавление новых пакетов.
- [architecture/overview.md](../architecture/overview.md) — место RAG в пайплайне.

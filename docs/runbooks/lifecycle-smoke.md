# Lifecycle smoke: audio/STT и RAG (#105, #106)

Краткие воспроизводимые шаги для проверки жизненного цикла без полного CI. Выполняются вручную в toolbox или на хосте.

---

## Audio / STT lifecycle (#105)

**Цель:** убедиться, что путь listen → capture → stop и analyze → STT не падает и возвращает ожидаемую форму.

1. **Listen (короткий цикл):** в toolbox с настроенным keyring и PipeWire:
   ```bash
   uv run voiceforge listen
   ```
   Подождать 5–10 с, Ctrl+C. Ожидание: выход без traceback; при наличии ring-файла — он обновляется (опционально проверить `ls -la` в XDG_RUNTIME_DIR или пути ring из конфига).

2. **Analyze (короткий отрезок):** если есть записанный ring или тестовый wav:
   ```bash
   uv run voiceforge analyze 5
   ```
   Ожидание: вывод текста или сообщение об ошибке по таймауту/источнику; без падения процесса.

3. **Targeted tests (автоматически):** `uv run pytest tests/test_audio_buffer.py tests/test_audio_capture.py -q --tb=line` — проверка буфера и захвата без полного пайплайна.

---

## RAG lifecycle / restore confidence (#106)

**Цель:** убедиться, что индекс создаётся, поиск по нему работает, путь «нет БД → индекс → поиск» воспроизводим.

1. **Путь к БД:** по умолчанию `$XDG_DATA_HOME/voiceforge/rag.db` (см. [config-env-contract.md](config-env-contract.md)); при необходимости использовать отдельный каталог через настройки проекта.

2. **Индекс одного PDF:** в toolbox с установленным `[rag]` (`uv sync --extra rag`):
   ```bash
   uv run voiceforge index /path/to/one.pdf
   ```
   Ожидание: завершение без ошибки; появление/обновление `rag.db` в каталоге данных.

3. **Поиск:** через демон (D-Bus) или API: вызов SearchRag / `GET /api/...` с запросом по тексту из проиндексированного PDF. Ожидание: ответ с непустым списком попаданий или пустой список без падения.

4. **Restore:** при отсутствии БД первый `index` создаёт её; при повреждении — пересоздать каталог и заново выполнить `index`. Миграции схемы — см. `tests/test_db_migrations.py`.

5. **Targeted tests:** `uv run pytest tests/test_rag_watcher.py tests/test_transcript_log.py -q --tb=line` (без тяжёлого ONNX при необходимости исключить test_rag_* с полным индексером).

---

## Ссылки

- Установка и окружение: [installation-guide.md](installation-guide.md)
- Конфиг и пути: [config-env-contract.md](config-env-contract.md)
- Релиз и чеклисты: [release-and-quality.md](release-and-quality.md)

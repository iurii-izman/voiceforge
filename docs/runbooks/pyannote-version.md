# Версия pyannote.audio

Источник истины для версии: `pyproject.toml` (зависимость `pyannote.audio`).

## FFmpeg (torchcodec)

pyannote.audio тянет torchcodec для декодирования аудио; torchcodec при импорте подгружает shared-библиотеки FFmpeg (libavutil, libavdevice и т.д.). Если в окружении их нет (например, минимальный toolbox), в логах и при `pytest` появляется предупреждение: «torchcodec is not installed correctly… libavutil.so.X: cannot open shared object file».

**Что сделать:** установить FFmpeg в том окружении, где запускаются тесты или демон с диаризацией:

- **Fedora / toolbox:** `sudo dnf install ffmpeg`
- После установки предупреждение при импорте pyannote исчезает (если версия libavutil совпадает с той, под которую собран torchcodec).

## Текущая версия

- **4.0.4** — зафиксирована в `pyproject.toml` (alpha2).

## Memory guard (#37)

На системах с ≤8 ГБ RAM диаризация может приводить к OOM. В пайплайне включён **memory guard**:

- **Проверка до запуска:** если `psutil.virtual_memory().available < 2 ГБ`, диаризация **пропускается** с предупреждением в structlog (`pipeline.diarization.skipped_low_memory`). Анализ продолжается без спикеров (diar_segments = []).
- **При OOM во время диаризации:** перехват `MemoryError` и CUDA `RuntimeError` с текстом "out of memory" → логирование `pipeline.diarization.oom` и возврат пустого списка (graceful degradation).

Константа порога: `voiceforge.core.pipeline.MIN_AVAILABLE_FOR_DIARIZATION_BYTES` (2 ГБ). Тесты: `tests/test_pipeline_memory_guard.py`.

## При OOM на машинах с 8 ГБ RAM (откат версии)

На части машин с 8 ГБ оперативной памяти pyannote 4.x может приводить к Out of Memory при загрузке модели или диаризации. Сначала срабатывает memory guard (см. выше); при необходимости допустим **откат на 3.3.2**.

**Шаги отката:**

1. В `pyproject.toml` заменить зависимость на `pyannote.audio==3.3.2`.
2. Выполнить `uv sync` (или `pip install -e .`) в окружении проекта.
3. Проверить совместимость API: в коде демона/пайплайна используются вызовы pyannote (загрузка модели, диаризация); при переходе 4.x → 3.x возможны изменения сигнатур — пройти тесты и при необходимости адаптировать вызовы.
4. Зафиксировать в этом runbook фактическую версию после отката (например: «3.3.2 (откат из-за OOM на 8 ГБ)»).

После стабилизации памяти или обновления pyannote можно вернуться на 4.x и снова зафиксировать версию здесь.

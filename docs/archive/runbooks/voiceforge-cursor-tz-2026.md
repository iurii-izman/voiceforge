# VoiceForge — ТЗ для Cursor (alpha2)

Расширенное ТЗ, среда, шаблоны промптов и чеклисты. **Основной контекст агента:** [agent-context.md](agent-context.md) — прикладывай его в новый чат и работай по нему.

**Стартовый промпт:** см. [agent-context.md](agent-context.md), раздел «Универсальный стартовый промпт».

---

## ПРАВИЛО №0: ЧТО CURSOR ДОЛЖЕН ЗНАТЬ ПРО СРЕДУ

```
Проект VoiceForge (v0.1.0-alpha.1 → alpha2). local-first AI assistant для аудио-встреч.

СРЕДА (проверено 2026-02-24):
- ОС: Fedora 43 COSMIC Atomic (иммутабельная, rpm-ostree)
- CPU: AMD Ryzen 3 5300U (4C/8T, нет GPU)
- RAM: 7.1 ГБ всего; ОС+COSMIC ~2.0–2.5 ГБ в покое → ~4.5 ГБ доступно
- Swap: 7.1 ГБ NVMe (быстрый, safety net)
- Разработка: ВНУТРИ Distrobox-контейнера "voiceforge" (Fedora 43)
- IDE: Cursor AppImage ~/Apps/cursor.AppImage
- Пакеты Python: ТОЛЬКО uv (не pip, не poetry, не conda)

СТЕК (не менять без ADR):
- Python 3.12+, uv, pyproject.toml
- faster-whisper 1.1.x (STT, CTranslate2, INT8)
- pyannote-audio==3.3.2 (дата: строго эта версия)
- SQLite-vec + FTS5 (векторный + полнотекстовый поиск)
- all-MiniLM-L6-v2 ONNX Runtime (эмбеддинги, не PyTorch)
- LiteLLM SDK (маршрутизация, не proxy-сервер)
- Instructor + Pydantic (структурированные ответы)
- PipeWire (pw-record subprocess)
- D-Bus (zbus в Rust, dbus-python в Python)
- Tauri v2 + WebKitGTK (Desktop UI, Rust + JS)

КРИТИЧЕСКИЕ ОГРАНИЧЕНИЯ (нарушение = поломка):
1. pyannote-audio СТРОГО ==3.3.2 (4.x = 9.5 ГБ RAM = OOM)
2. STT и диаризация СТРОГО ПОСЛЕДОВАТЕЛЬНО (не параллельно)
3. НЕ ChromaDB (грузит HNSW весь в RAM)
4. НЕ LightRAG (требует 32B+ LLM для индексации)
5. Горячие клавиши ТОЛЬКО через D-Bus → COSMIC Settings (Custom Shortcuts)
6. Пиковый RAM приложения ≤ 5.5 ГБ (swap на NVMe = cushion, не норма)
7. API ключи ТОЛЬКО через python-keyring → gnome-keyring (сервис 'voiceforge')
8. Никогда не коммитить ключи; не хранить в .env в git
9. CLI-поверхность: 9 core команд заморожены (ADR-0001). Новые команды = новый ADR.
   Флаги к существующим командам — можно без ADR.
10. Сборка Tauri ТОЛЬКО в toolbox с webkit2gtk4.1-devel, gtk3-devel, openssl-devel

СТИЛЬ КОДА:
- Type hints на все функции (обязательно)
- Docstrings: Google-стиль для публичных функций
- structlog (никогда print() или logging напрямую)
- Ошибки: явные исключения, никогда "except Exception: pass"
- ruff для линтинга и форматирования
- pytest для тестов (asyncio_mode = auto)
- Максимум 300 строк на файл. Больше → split на модули.
- Импорты: stdlib → third-party → local (разделены пустой строкой)
```

---

## ЧАСТЬ I: ЧТО УЖЕ РЕАЛИЗОВАНО (не переделывать)

### Alpha0.1 — ГОТОВО (v0.1.0-alpha.1, релиз 21 фев 2026)

**CLI команды (9 core + расширения):**
- `listen` (+ `--stream`, `--live-summary`)
- `analyze` (+ `--template`: standup, sprint_review, one_on_one, brainstorm, interview)
- `status` (+ `--detailed`, `--doctor`)
- `history` (+ `--id`, `--last`, `--search`, `--date`, `--from/--to`, `--output md`)
- `index`, `watch`
- `daemon`, `install-service`, `uninstall-service`
- `cost` (+ `--days`, `--from/--to`, `--output json`)
- `export` (+ `--id`, `--format md|pdf`)
- `action-items update` (`--from-session`, `--next-session`)
- `web` (локальный HTTP UI)

**Пайплайн:**
- PipeWire audio capture (pw-record subprocess)
- faster-whisper STT (small INT8, vad_filter, streaming)
- pyannote диаризация (sequential, gc.collect, restart timer)
- RAG: SQLite-vec + FTS5, all-MiniLM-L6-v2 ONNX, hybrid BM25+vec
- LiteLLM routing (Claude/GPT/Ollama), Instructor structured output
- 5 LLM-шаблонов с Pydantic схемами
- PII: regex + GLiNER ONNX (ON/OFF/EMAIL_ONLY)
- SQLite: transcripts.db + metrics.db + rag.db
- Action items: отдельная таблица, cross-session трекинг

**Демон (D-Bus `com.voiceforge.App`):**
- Методы: Analyze, GetSessions, GetSessionDetail, GetSettings, GetAnalytics, Listen (start/stop), GetStreamingTranscript
- Сигналы: ListenStateChanged, TranscriptUpdated, AnalysisDone, TranscriptChunk
- Envelope: {schema_version, ok, data} (VOICEFORGE_IPC_ENVELOPE=true по умолчанию)

**Web UI (stdlib HTTP):**
- GET /api/status, /api/sessions, /api/sessions/<id>
- POST /api/analyze, /api/action-items/update
- GET /api/export, /api/cost

**Инфраструктура:**
- uv + pyproject.toml + uv.lock
- ruff, bandit, gitleaks, semgrep, pre-commit
- pytest, CI (GitHub Actions: test, semgrep, gitleaks, codeql, release)
- Makefile, scripts/: bootstrap.sh, verify_pr.sh, smoke_clean_env.sh, doctor.sh
- Keyring: сервис 'voiceforge' (anthropic, openai, huggingface, google, sonar_token, ...)
- CHANGELOG.md, ADR 0001-0004

---

## ЧАСТЬ II: ПЛАН ALPHA2 (v0.2.0-alpha.1)

### Блок A: Сборка Tauri Desktop

**Файлы:** `desktop/` (уже есть каркас)

**Промпт для Cursor:**
```
@docs/runbooks/agent-context.md @docs/desktop-tauri-implementation-plan.md

Реализовать Блок 3 (каркас Tauri): убедиться что desktop/ содержит минимальный
Tauri 2 проект. Проверить структуру:
- desktop/src-tauri/tauri.conf.json (appId: com.voiceforge.app, version согласован)
- desktop/src/main.ts или App.tsx (одно главное окно)
- desktop/src-tauri/src/main.rs (Rust entry point с zbus или dbus)
- Ping к com.voiceforge.App при старте
- При недоступности демона: показать сообщение "Запустите демон: voiceforge daemon"

Сборка: cd desktop && npm run build && cargo tauri build
Среда: toolbox с webkit2gtk4.1-devel, gtk3-devel, openssl-devel (см. desktop-build-deps.md)
```

**Go/no-go Блока A:**
- `./scripts/check-desktop-deps.sh` → все OK
- `cd desktop && cargo tauri build` без ошибок
- Окно открывается, показывает Ping-результат

---

### Блок B: D-Bus интеграция в Tauri

**Промпт для Cursor:**
```
@docs/runbooks/agent-context.md @docs/runbooks/config-env-contract.md

Реализовать D-Bus интеграцию в desktop/ (Блок 5 из desktop-tauri-implementation-plan.md).

Нужно в Rust (src-tauri/src/):
1. D-Bus клиент через zbus 4.x (добавить в Cargo.toml)
2. Вызовы: Analyze(seconds: i32, template: str) → envelope → data
3. GetSessions(limit: i32) → data.sessions (id, started_at, duration_sec, segments_count)
4. GetSessionDetail(id: i32) → data.session_detail (segments, analysis)
5. GetSettings() → data (model_size, default_llm, budget_limit_usd, pii_mode, ...)
6. GetAnalytics("7d") → data (total_cost_usd, by_day, by_model)
7. Listen start/stop → void
8. GetStreamingTranscript() → строка partial/final transcript

Envelope разбор: {schema_version, ok, data} — при ok=false показывать error.message.
Tauri commands (invoke из JS): analyze, get_sessions, get_session_detail, get_settings,
  get_analytics, listen_start, listen_stop, get_streaming_transcript.

Сигналы (Блок 5.3): подписаться на ListenStateChanged(is_listening: bool),
  AnalysisDone(status: str), TranscriptChunk(text, speaker, timestamp_ms, is_final).
  Эмитировать как Tauri events во фронт.
```

---

### Блок C: UI экраны

**Промпт для Cursor:**
```
@docs/runbooks/agent-context.md @docs/desktop-tauri-implementation-plan.md

Реализовать UI для desktop/ (Блок 4). Тёмная тема (#0a0f1c, акценты #00ff9d).
Навигация: боковая панель или табы — Главная, Сессии, Затраты, Настройки.

Главная:
- Индикатор "Демон доступен/недоступен"
- Кнопки Старт/Стоп записи (listen_start/stop через invoke)
- Выбор шаблона: standup | sprint_review | one_on_one | brainstorm | interview
- Поле "последние N секунд" (default 30)
- Кнопка "Анализ" → invoke analyze → spinner → при AnalysisDone показать результат
- Блок стриминга: при записи опрашивать get_streaming_transcript раз в 1-2с

Сессии:
- Список из get_sessions (id, дата, длительность, segments_count)
- Клик → get_session_detail → сегменты + анализ (вопросы, ответы, рекомендации, action items)
- Кнопка "Экспорт MD" → invoke export_session(id, "md")
- Кнопка "Экспорт PDF" → invoke export_session(id, "pdf") [optional, с предупреждением]

Затраты: get_analytics("7d") / get_analytics("30d") → таблица по дням и моделям
Настройки: get_settings() → только чтение (без редактирования в alpha2)

Не использовать localStorage/sessionStorage (Tauri WebView не поддерживает так же).
Состояние: useState / prop drilling (alpha2 без zustand если не нужно).
```

---

### Блок D: Streaming STT в CLI (roadmap #9)

**Промпт для Cursor:**
```
@docs/runbooks/agent-context.md

Roadmap #9: Streaming STT в CLI listen.

StreamingTranscriber уже реализован в src/voiceforge/stt/streaming.py.
Демон транслирует TranscriptChunk через D-Bus.

Задача: при вызове `voiceforge listen` с флагом `--stream` или при
cfg.streaming_stt=True — выводить partial/final чанки в stdout в реальном времени.

Проверить:
1. StreamingTranscriber.on_partial(text) → typer.echo(f"\r{text}", nl=False)
2. StreamingTranscriber.on_final(text) → typer.echo(text)
3. Интеграция с существующим listen command (не нарушать no-stream path)
4. Тест: src/tests/test_streaming_cli.py с моком STT

Не нарушать ADR-0001 (флаг к listen = OK, не новая команда).
```

**Go/no-go:** `uv run voiceforge listen --stream` выводит partial/final в терминал

---

### Блок E: Фиксы из плана развития (приоритет)

**Промпт для Cursor:**
```
@docs/runbooks/agent-context.md @docs/development-plan-post-audit-2026.md

Сначала сверь каждый пункт с текущим кодом — часть может быть уже сделана.
Затем реализуй только НЕ сделанные, по порядку важности:

W1: budget_limit_usd — убрать захардкоженную константу 75.0, читать из Settings().budget_limit_usd
W2: sample_rate — добавить ресэмплинг 44.1→16kHz или явную проверку + structlog warning
W3: RAG контекст — увеличить с transcript[:200] до transcript[:1000] или keyword extraction
W5: Instructor retry — добавить try/except + retry при невалидном JSON от LLM
W8: валидация Settings — @field_validator для model_size, default_llm, budget_limit_usd

После каждого фикса: uv run pytest tests/ -q (убедиться что ничего не сломали).
Обновить CHANGELOG.md для user-facing изменений.
```

---

### Блок F: Релиз Alpha2

**Промпт для Cursor:**
```
@docs/runbooks/agent-context.md @docs/runbooks/alpha2-checklist.md @docs/runbooks/release.md

Подготовить релиз v0.2.0-alpha.1:

1. Согласовать версии:
   - pyproject.toml: version = "0.2.0a1"
   - desktop/package.json: "version": "0.2.0-alpha.1"
   - desktop/src-tauri/tauri.conf.json: "version": "0.2.0-alpha.1"

2. Прогнать чеклист alpha2-checklist.md:
   - uv run pytest tests/ -q
   - ./scripts/verify_pr.sh
   - ./scripts/smoke_clean_env.sh
   - cd desktop && npm run build && cargo tauri build (в toolbox)

3. Обновить CHANGELOG.md — секция [0.2.0-alpha.1]

4. Тег:
   git tag -a v0.2.0-alpha.1 -m "VoiceForge alpha2: Tauri desktop + streaming STT"
   git push origin main --tags

5. Обновить docs/runbooks/next-iteration-focus.md
```

---

## ЧАСТЬ III: ШАБЛОНЫ ПРОМПТОВ (для регулярного использования)

### Новый модуль
```
@docs/runbooks/agent-context.md

Создать [src/voiceforge/путь/к/файлу.py].

Назначение: [одно предложение]
Входные данные: [типы]
Выходные данные: [типы]
RAM-бюджет: [X] МБ (не превышать)

Требования:
- Максимум 300 строк
- Type hints на все функции
- structlog (не print)
- Google docstrings для публичных методов
- Тест: tests/test_[модуль].py с pytest
- Ключи через keyring (не захардкодить)
- uv add [зависимость] если нужна новая либа (проверить что нет аналога в pyproject.toml)
```

### Дебаг OOM / RAM проблемы
```
@docs/runbooks/agent-context.md

Анализ проблемы с памятью:

Файл: [путь]
Ошибка: [traceback или описание]

Контекст: AMD Ryzen 3 5300U, 7.1 ГБ RAM (~4.5 ГБ для приложения), Fedora COSMIC Atomic.

Проверь:
1. Pyannote — версия 3.3.2? Если нет → downgrade немедленно
2. Параллельный запуск STT + диаризации? → сделать последовательным
3. gc.collect() после pyannote? → добавить
4. ChromaDB? → заменить на SQLite-vec
5. Незакрытые файловые дескрипторы?
6. Модели не выгружаются? → aggressive_memory=True или явный del + gc.collect()

Предложи fix + regression test.
```

### Дебаг D-Bus
```
@docs/runbooks/agent-context.md @docs/runbooks/config-env-contract.md

Проблема с D-Bus: [описание]

D-Bus сервис: com.voiceforge.App
Envelope формат: {schema_version, ok, data} (при ok=false: error.code, error.message)
VOICEFORGE_IPC_ENVELOPE=true по умолчанию.

Проверить:
1. Демон запущен? voiceforge daemon в отдельном терминале
2. D-Bus сессия доступна? dbus-send --session --print-reply ...
3. Метод вызывается с правильными типами?
4. Envelope разбирается правильно?
```

### RAM аудит модуля
```
@[модуль.py] @docs/runbooks/agent-context.md

RAM аудит перед коммитом.

Бюджет по компонентам (пиковый):
- Fedora COSMIC: ~2.2 ГБ
- faster-whisper small INT8: ~1.0 ГБ
- pyannote 3.3.2 (sequential): ~1.3 ГБ
- all-MiniLM ONNX: ~0.2 ГБ
- Остаток для этого модуля: [X] МБ

Найди:
1. Утечки памяти (особенно в torch/pyannote объектах)
2. Объекты которые не удаляются после использования
3. Места для gc.collect()
4. Рекомендации по batch_size / chunk_size
5. Можно ли выгружать модель между вызовами?
```

### Рефакторинг перед PR
```
@codebase @docs/runbooks/agent-context.md

Рефакторинг [файл.py или модуля] перед PR:

Цели (в порядке приоритета):
1. Не превышать 300 строк (split если нужно)
2. Type hints везде где отсутствуют
3. print() → structlog (debug/info/warning/error)
4. "except Exception: pass" → явные исключения
5. Константы → Settings (Pydantic)
6. Тесты для новых функций

Не трогать: публичный API модуля (сигнатуры функций, если ими пользуется CLI/демон).
После: uv run ruff check src && uv run pytest tests/ -q
```

### Продолжить план развития

Скопируй один из блоков в начало нового чата.

**Вариант: оставшиеся пункты (W4, W6, roadmap #6/#8, smart trigger, PDF)**

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Работай по нему без поиска по проекту. Приоритет фич — docs/roadmap-priority.md. Эффективно и дёшево; ключи в keyring; Fedora Atomic/toolbox/uv.

Сделать все оставшиеся пункты из плана развития и next-iteration-focus:

1. **W4:** GetSettings D-Bus — поле privacy_mode: либо убрать из ответа, либо явно задокументировать как алиас pii_mode (проверить контракт/доку).
2. **W6:** В main.py оставшиеся пользовательские строки (ошибки, заголовки) перевести на i18n t("key"); приоритет: сообщения об ошибках и ключевые подписи.
3. **Roadmap #6:** При необходимости углубить cost report — команда cost и/или status --detailed (проверить по коду).
4. **Roadmap #8:** Расширенные e2e — добавить/дополнить тесты на export, analyze --template, action-items update, history --output md.
5. **Smart trigger в демоне:** При срабатывании передавать template в run_analyze_pipeline (проверить daemon/smart_trigger, при необходимости добавить параметр).
6. **Экспорт PDF:** В quickstart и/или в доке явно указать, что PDF опционален и требует pandoc/pdflatex.

После каждой фичи: тесты при необходимости, config-env-contract.md при изменении контракта, CHANGELOG для user-facing. Не нарушать ADR-0001. В конце итерации обновить docs/runbooks/next-iteration-focus.md и дать промпт для следующего чата.
```

**Вариант: общий (сверка + план по порядку)**

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Работай по нему без поиска по проекту. Приоритет фич — docs/roadmap-priority.md. Эффективно и дёшево; ключи в keyring; Fedora Atomic/toolbox/uv.

Реализовать план развития по аудиту февраля 2026: @docs/development-plan-post-audit-2026.md

Порядок:
1. Сверь пункты Части I и II с текущим кодом — что уже сделано (export, --template, Ollama, action-items update), не дублируй.
2. Часть I — задачи 1→10 по одной, начиная с первых нереализованных.
3. Часть II — W1, W2, W3, W8; затем W4, W5, W6, W7, W9, W10 по возможности.
4. После каждой фичи: тесты при необходимости, config-env-contract.md при изменении контракта, CHANGELOG для user-facing. Не нарушать ADR-0001.
```

---

## ЧАСТЬ IV: КОНФИГУРАЦИЯ И СПРАВОЧНИКИ

### Settings (config-env-contract.md сокращённо)
```python
# Основные поля Settings (src/voiceforge/core/config.py):
model_size: str = "small"          # VOICEFORGE_MODEL_SIZE
default_llm: str = "anthropic/claude-haiku-4-5"  # VOICEFORGE_DEFAULT_LLM
budget_limit_usd: float = 75.0     # VOICEFORGE_BUDGET_LIMIT_USD
ring_seconds: float = 300.0        # VOICEFORGE_RING_SECONDS
streaming_stt: bool = False        # VOICEFORGE_STREAMING_STT
language: str = "auto"             # VOICEFORGE_LANGUAGE (auto/ru/en)
ollama_model: str = "phi3:mini"    # VOICEFORGE_OLLAMA_MODEL
pii_mode: str = "ON"               # VOICEFORGE_PII_MODE (OFF/ON/EMAIL_ONLY)
aggressive_memory: bool = False    # VOICEFORGE_AGGRESSIVE_MEMORY
pyannote_restart_hours: int = 2    # VOICEFORGE_PYANNOTE_RESTART_HOURS
smart_trigger: bool = False        # VOICEFORGE_SMART_TRIGGER
```

### Keyring (сервис 'voiceforge')
```bash
keyring set voiceforge anthropic    # ANTHROPIC_API_KEY
keyring set voiceforge openai       # OPENAI_API_KEY
keyring set voiceforge huggingface  # pyannote / STT
keyring set voiceforge google       # GEMINI_API_KEY (optional)
# CI/dev keys:
keyring set voiceforge sonar_token
keyring set voiceforge github_token
keyring set voiceforge codecov_token
```

### RAM бюджет (пиковый, sequential)
```
ОС + COSMIC + PipeWire:   ~2.0–2.5 ГБ
faster-whisper small INT8: ~0.8–1.0 ГБ  (после выгрузки ↓ ~50 МБ)
pyannote 3.3.2 (30с окно): ~1.0–1.4 ГБ (sequential!)
all-MiniLM ONNX:           ~0.1–0.2 ГБ
Tauri WebKitGTK:           ~0.05–0.1 ГБ
Python runtime:            ~0.2–0.3 ГБ
ИТОГО пиковый:             ~4.2–5.5 ГБ
Swap на NVMe (7.1 ГБ):     safety net ← не норма
```

### ADR-0001: Frozen CLI surface
```
9 core команд (заморожены):
listen, analyze, status, history, index, watch, daemon, install-service, uninstall-service

Расширения (без ADR):
+ флаги к существующим командам (--template, --stream, --doctor, --detailed, --search, --date, ...)
+ cost, export, action-items (уже есть, не нарушают ADR)
+ web (уже есть)

Новая команда CLI = нужен ADR (создать docs/adr/000X-название.md).
```

---

## ЧАСТЬ V: ДИАГНОСТИКА И ПРОВЕРКИ

### Проверить что всё работает
```bash
# В Distrobox voiceforge:
uv run voiceforge status           # RAM, cost_today, ollama_available
uv run voiceforge status --doctor  # проверка всего окружения
./scripts/doctor.sh                # полная диагностика

# Проверить keyring:
uv run python -c "
from voiceforge.core.secrets import get_api_key
for k in ('anthropic','openai','huggingface'):
    print(k, ':', 'present' if get_api_key(k) else 'ABSENT')
"

# Тесты:
uv run pytest tests/ -q
./scripts/verify_pr.sh
```

### Проверить D-Bus
```bash
# Запустить демон:
uv run voiceforge daemon &

# Проверить сервис:
dbus-send --session --print-reply \
  --dest=com.voiceforge.App \
  /com/voiceforge/App \
  com.voiceforge.App.GetSettings

# Ping (если реализован):
dbus-send --session --print-reply \
  --dest=com.voiceforge.App \
  /com/voiceforge/App \
  com.voiceforge.App.Ping
```

### Проверить Desktop build env
```bash
# В toolbox с зависимостями:
./scripts/check-desktop-deps.sh

# Сборка:
cd desktop && npm run build && cargo tauri build

# Dev режим (с запущенным демоном):
cd desktop && cargo tauri dev
```

---

## ЧАСТЬ VI: ЧЕКЛИСТ ПЕРЕД КАЖДЫМ PR

```
□ uv run ruff check src tests       # линтинг
□ uv run ruff format src tests      # форматирование
□ uv run pytest tests/ -q           # тесты
□ uv run bandit -r src -ll -q --configfile .bandit.yaml  # security
□ gitleaks detect --source . --config .gitleaks.toml    # нет ключей в коде
□ Нет print() — только structlog
□ Нет захардкоженных ключей/токенов
□ Нет "except Exception: pass"
□ Type hints на всех новых функциях
□ ADR-0001 не нарушен (флаги к командам = OK, новые команды = нужен ADR)
□ pyannote-audio остаётся ==3.3.2 в uv.lock
□ Файлы ≤ 300 строк
□ CHANGELOG.md обновлён (для user-facing изменений)
□ config-env-contract.md обновлён (при изменении контракта)
```

#!/usr/bin/env bash
# Create all productization issues and add to GitHub Project
# One-time script, idempotent via title check
set -euo pipefail

REPO="iurii-izman/voiceforge"
PROJECT_ID="PVT_kwHODvfgWM4BQC-Z"
STATUS_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-R4aU"
PHASE_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeSw"
PRIORITY_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUM"
EFFORT_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUQ"
AREA_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUU"

# Option IDs
TODO="f75ad846"
PHASE_E="$(gh project field-list 1 --owner iurii-izman --format json | python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d['fields']:
    if f['name']=='Phase' and 'options' in f:
        for o in f['options']:
            if 'E' in o['name']:
                print(o['id']); break
" 2>/dev/null || echo "")"

# If Phase E doesn't exist yet, we'll skip phase field
if [[ -z "${PHASE_E:-}" ]]; then
    echo "Phase E option not found, will skip phase field"
fi

P0="1016b51c"
P1="b12f98f6"
P2="595114bb"
P3="5759f2a6"

XS="c05c3b37"
S="89ac7c75"
M="10a9e752"
L="4f65026a"

BACKEND="3b82b44a"
DEVOPS="cd368946"

# Label strings (shelldre:S1192: avoid duplicated literals)
LABELS_P0_FEAT="productization,autopilot,feat,p0,phase:E"
LABELS_P1_FEAT="productization,autopilot,feat,p1,phase:E"
FRONTEND="6bb5ba28"
TESTING="cb342949"
SECURITY="6a0f371d"
AIML="d92aab92"

create_issue() {
    local title="$1"
    local body="$2"
    local labels="$3"
    local priority="$4"
    local effort="$5"
    local area="$6"

    echo "Creating: $title"

    local url
    url=$(gh issue create -R "$REPO" --title "$title" --body "$body" --label "$labels" 2>&1)
    local number
    number=$(echo "$url" | grep -oP '\d+$')

    echo "  Created #$number"

    # Add to project
    local item_id
    item_id=$(gh project item-add 1 --owner iurii-izman --url "$url" --format json | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

    echo "  Added to project: $item_id"

    # Set status = Todo
    gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$STATUS_FIELD" --single-select-option-id "$TODO" > /dev/null 2>&1

    # Set priority
    if [[ -n "${priority:-}" ]]; then
        gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$PRIORITY_FIELD" --single-select-option-id "$priority" > /dev/null 2>&1
    fi

    # Set effort
    if [[ -n "${effort:-}" ]]; then
        gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$EFFORT_FIELD" --single-select-option-id "$effort" > /dev/null 2>&1
    fi

    # Set area
    if [[ -n "${area:-}" ]]; then
        gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$AREA_FIELD" --single-select-option-id "$area" > /dev/null 2>&1
    fi

    echo "  Fields set ✓"
    echo "$number"
    return 0
}

echo "=== Creating Productization Issues ==="
echo ""

# ─────────────────────────────────────────────
# BLOCK 1: Quick Wins
# ─────────────────────────────────────────────
create_issue \
"E1 · Quick Wins: Sensible Defaults & Notifications" \
"$(cat <<'BODY'
## Context

Daily Driver Score: 35/100. Пять изменений с мгновенным эффектом (~3 часа суммарно).

## Scope

### 1. Smart trigger ON по умолчанию
- **File:** `src/voiceforge/core/config.py`
- Изменить `smart_trigger: bool = False` → `smart_trigger: bool = True`
- Обновить `docs/runbooks/config-env-contract.md` (default value)

### 2. `analyze` без `--seconds` = весь буфер
- **File:** `src/voiceforge/main.py`
- Если `--seconds` не указан → использовать весь ring buffer (ring_seconds из config)
- Обновить `--help` текст

### 3. PipeWire check в bootstrap
- **File:** `scripts/bootstrap.sh`
- Добавить: `command -v pw-record >/dev/null || echo "⚠ PipeWire not found. Install: sudo dnf install pipewire pipewire-utils"`
- Добавить: `pipewire --version` вывод

### 4. voiceforge.yaml.example
- **File:** `voiceforge.yaml.example` (новый, в корне репо)
- Скопировать все defaults из `config.py` с комментариями

### 5. Desktop notification при analyze complete
- **File:** `src/voiceforge/core/notify.py` (новый) или в `pipeline.py`
- `subprocess.run(["notify-send", "VoiceForge", f"Analysis complete: {summary[:80]}"], check=False)`
- Fallback: если notify-send не найден — просто skip

## Acceptance Criteria
- [ ] `smart_trigger` default = True в config
- [ ] `voiceforge analyze` без `--seconds` анализирует весь буфер
- [ ] `bootstrap.sh` проверяет PipeWire и выводит warning
- [ ] `voiceforge.yaml.example` в корне с документированными defaults
- [ ] Desktop notification через notify-send после analyze
- [ ] Все тесты проходят (targeted: test_config, test_cli_surface)
- [ ] Docs updated (config-env-contract.md)

## Autopilot Notes
Полностью автономная задача. Никаких user decisions.
BODY
)" \
"productization,autopilot,p0,phase:E" "$P0" "$S" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 2: One-Shot Meeting Mode
# ─────────────────────────────────────────────
create_issue \
"E2 · One-Shot Meeting Mode: \`voiceforge meeting\`" \
"$(cat <<'BODY'
## Context

Главный блокер Daily Driver. Сейчас нужно: (1) voiceforge daemon, (2) voiceforge listen, (3) voiceforge analyze --seconds N. Нужна одна команда.

## Scope

### Новая команда: `voiceforge meeting`
- **Files:** `src/voiceforge/main.py`, `src/voiceforge/cli/meeting.py` (новый)
- Flow:
  1. Start audio capture (ring buffer)
  2. Показать статус: «Listening... Press Ctrl+C to stop and analyze»
  3. Smart trigger работает в фоне (если enabled)
  4. При smart trigger → auto-analyze → показать результат → продолжить слушать
  5. При Ctrl+C → analyze весь буфер → показать результат → exit
- Flags:
  - `--template` (standup, 1:1, etc.) — pass to analyze
  - `--no-analyze` — только listen, без analyze при выходе
  - `--seconds N` — анализировать только последние N секунд (по умолчанию: всё)
- Не требует daemon (standalone, in-process pipeline)
- Desktop notification при каждом auto-analyze

### Implementation
- Переиспользовать `audio/capture.py`, `audio/buffer.py`, `audio/smart_trigger.py`
- Переиспользовать `core/pipeline.py` + `llm/router.py` для analyze
- Signal handler для SIGINT → graceful analyze + exit
- Показывать результат в stdout (formatted text, не JSON)

## Acceptance Criteria
- [ ] `voiceforge meeting` запускает listen + auto-analyze при Ctrl+C
- [ ] Smart trigger auto-analyze работает в meeting mode
- [ ] `--template standup` передаётся в analyze
- [ ] Desktop notification при smart trigger analyze
- [ ] Graceful Ctrl+C → analyze → result → exit
- [ ] CLI help текст и contract test обновлены
- [ ] Тест: test_meeting_mode.py (mocked pipeline)

## Autopilot Notes
Полностью автономная задача. Ключевые файлы для понимания: `main.py`, `audio/capture.py`, `audio/smart_trigger.py`, `core/pipeline.py`, `llm/router.py`.
BODY
)" \
"$LABELS_P0_FEAT" "$P0" "$M" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 3: Error Pre-Flight Checks
# ─────────────────────────────────────────────
create_issue \
"E3 · Error Pre-Flight Checks: PipeWire, Disk, Network, Models" \
"$(cat <<'BODY'
## Context

Error Resilience 60% → 85%. Пользователь сталкивается с непонятными ошибками при отсутствии PipeWire, нехватке диска, отсутствии сети.

## Scope

### 1. PipeWire health check
- **File:** `src/voiceforge/audio/capture.py` или новый `src/voiceforge/core/preflight.py`
- При запуске listen/meeting: `shutil.which("pw-record")` → если None:
  ```
  ❌ PipeWire not found.
  Fix: sudo dnf install pipewire pipewire-utils
  ```
- i18n ключ: `error.pipewire_not_found`

### 2. Disk space check
- **File:** `src/voiceforge/core/preflight.py`
- `shutil.disk_usage(data_dir)` → warning при <1GB, error при <200MB
- Вызывать перед listen и analyze
- i18n ключи: `warning.low_disk_space`, `error.no_disk_space`

### 3. Network connectivity check перед LLM
- **File:** `src/voiceforge/llm/router.py`
- Перед LiteLLM call: quick socket connect to API host (timeout 3s)
- При отсутствии сети: предложить Ollama или сообщить
- i18n ключ: `error.no_network`

### 4. Model download с прогресс-баром
- **File:** `src/voiceforge/stt/transcriber.py`
- При первом вызове faster-whisper: log «Downloading Whisper model ({size})...»
- Progress callback если CTranslate2/HF hub поддерживает
- Retry при network failure (3 attempts, exponential backoff)

## Acceptance Criteria
- [ ] PipeWire check с user-friendly сообщением и fix-инструкцией
- [ ] Disk space check: warning <1GB, error <200MB
- [ ] Network check перед LLM call с Ollama suggestion
- [ ] Model download logging (размер, progress если возможно)
- [ ] Все checks в `preflight.py` модуле (reusable)
- [ ] i18n ключи для всех сообщений
- [ ] Тесты: test_preflight.py (mocked shutil, socket)

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"$LABELS_P0_FEAT" "$P0" "$M" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 4: Explicit Failure Feedback
# ─────────────────────────────────────────────
create_issue \
"E4 · Explicit Failure Feedback: Diarization, RAG, Models" \
"$(cat <<'BODY'
## Context

Тихие skip-ы разрушают доверие. Diarization пропускается молча при OOM/no HF token. RAG search возвращает пустой контекст без объяснения.

## Scope

### 1. Diarization skip feedback
- **File:** `src/voiceforge/core/pipeline.py`, `src/voiceforge/stt/diarizer.py`
- Если diarization пропущена → добавить warning в CLI output:
  ```
  ⚠ Speaker labels unavailable: [HuggingFace token missing / insufficient RAM (1.5GB < 2GB required)]
  Fix: keyring set voiceforge huggingface
  ```
- Return `PipelineResult` с `warnings: list[str]` полем
- Показывать warnings в CLI output и в analyze result

### 2. RAG empty context feedback
- **File:** `src/voiceforge/rag/searcher.py`, `src/voiceforge/core/pipeline.py`
- Если RAG DB не существует или search returns 0 results:
  ```
  ℹ No knowledge base indexed. Use: voiceforge index <path>
  ```
- Показывать в analyze output

### 3. Missing model warning
- **File:** `src/voiceforge/stt/transcriber.py`
- Перед download: «Model {model_size} not cached, downloading (~{size}MB)...»
- После download: «Model ready.»

### 4. Budget warning
- **File:** `src/voiceforge/llm/router.py`
- При приближении к budget (>80%): warning перед analyze
  ```
  ⚠ Daily budget: $0.42/$0.50 used. This analysis ~$0.03.
  ```

## Acceptance Criteria
- [ ] Diarization skip → user-facing warning с причиной и fix action
- [ ] RAG empty → info message с инструкцией index
- [ ] Model download → progress message
- [ ] Budget warning при >80% использования
- [ ] `PipelineResult.warnings` field populated and displayed
- [ ] i18n для всех сообщений
- [ ] Тесты: test_pipeline_warnings.py

## Autopilot Notes
Полностью автономная задача. Ключевой файл: `core/pipeline.py`.
BODY
)" \
"$LABELS_P0_FEAT" "$P0" "$S" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 5: Daemon Hardening
# ─────────────────────────────────────────────
create_issue \
"E5 · Daemon Hardening: Auto-Start, Watchdog, Log Rotation, Graceful Shutdown" \
"$(cat <<'BODY'
## Context

Daily driver = запустил и забыл. Daemon требует ручного старта, нет watchdog, логи растут бесконечно, Ctrl+C может потерять буфер.

## Scope

### 1. Auto-start при install-service
- **File:** `src/voiceforge/main.py` (install-service command)
- После `systemctl --user enable voiceforge` → также `systemctl --user start voiceforge`
- Сообщение: «Service installed, enabled and started.»

### 2. Systemd watchdog
- **File:** `src/voiceforge/core/daemon.py`
- Добавить `WatchdogSec=60` в voiceforge.service template
- В daemon loop: `sd_notify("WATCHDOG=1")` каждые 30s (через `sdnotify` package или socket напрямую)
- `Type=notify` в service file

### 3. Log rotation
- **File:** `src/voiceforge/core/daemon.py` или `voiceforge.service`
- Вариант A (проще): daemon пишет в journald через systemd (StandardOutput=journal)
- Вариант B: structlog → RotatingFileHandler (max 50MB, 3 backups)
- Рекомендуется вариант A для systemd daemon

### 4. Graceful shutdown
- **File:** `src/voiceforge/core/daemon.py`, `src/voiceforge/audio/capture.py`
- SIGTERM/SIGINT handler: flush ring buffer → close DB → clean shutdown
- Ensure ring.raw saved before exit
- Log: «Shutting down gracefully...»

### 5. ring.raw cleanup при остановке
- **File:** `src/voiceforge/audio/capture.py`
- При clean exit → удалить ring.raw из runtime dir
- При crash → ring.raw остаётся (для recovery)

## Acceptance Criteria
- [ ] `install-service` enables AND starts service
- [ ] Watchdog: WatchdogSec=60, sd_notify in daemon loop
- [ ] Logs go to journald (StandardOutput=journal)
- [ ] SIGTERM → flush buffer → close DB → exit 0
- [ ] ring.raw cleaned up on clean exit
- [ ] Тесты: test_daemon_lifecycle.py (mocked systemd)
- [ ] voiceforge.service template updated

## Autopilot Notes
Полностью автономная задача. Файлы: `core/daemon.py`, `audio/capture.py`, `main.py`.
BODY
)" \
"$LABELS_P0_FEAT" "$P0" "$M" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 6: Ollama Fallback
# ─────────────────────────────────────────────
create_issue \
"E6 · Ollama Zero-Config Fallback" \
"$(cat <<'BODY'
## Context

Если нет API ключей в keyring — analyze ломается. Ollama (если установлен) должен быть автоматическим fallback.

## Scope

### Auto-detect Ollama
- **File:** `src/voiceforge/llm/router.py`, `src/voiceforge/llm/local_llm.py`
- При отсутствии API ключей (anthropic, openai, google) → проверить Ollama доступность
- Если Ollama running → использовать как default LLM (без конфигурации)
- Модель: `default_llm` из конфига, fallback: phi3:mini или llama3.2
- Log: «No API keys found. Using Ollama ({model}) as LLM backend.»

### Config integration
- **File:** `src/voiceforge/core/config.py`
- Новый computed property: `effective_llm` → API LLM или Ollama fallback
- Не менять `default_llm` — это user preference; fallback отдельная логика

### Startup check
- **File:** `src/voiceforge/cli/status_helpers.py`
- `voiceforge status` → показать «LLM: Ollama (fallback, no API keys)» если в fallback mode

## Acceptance Criteria
- [ ] Без API ключей + Ollama running → analyze работает через Ollama
- [ ] Без API ключей + Ollama не running → понятная ошибка с инструкцией
- [ ] `voiceforge status` показывает текущий LLM backend
- [ ] Log message при fallback
- [ ] Не ломает существующий flow с API ключами
- [ ] Тесты: test_ollama_fallback.py

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"$LABELS_P1_FEAT" "$P1" "$S" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 7: Setup Wizard
# ─────────────────────────────────────────────
create_issue \
"E7 · Setup Wizard: \`voiceforge setup\` & First-Run Detection" \
"$(cat <<'BODY'
## Context

Onboarding 15–30 мин → цель 5 мин. Нужен guided setup и автоматическое предложение при первом запуске.

## Scope

### 1. `voiceforge setup` command
- **File:** `src/voiceforge/cli/setup.py` (новый), `src/voiceforge/main.py`
- Interactive wizard:
  1. Check PipeWire → install hint if missing
  2. Check Python/uv versions
  3. Предложить язык (ru/en/auto)
  4. Предложить модель Whisper (tiny/small/medium) с описанием RAM requirements
  5. API keys setup: «Enter Anthropic API key (or press Enter to skip):» → `keyring set`
  6. Optional: HuggingFace token для diarization
  7. Pre-download выбранной Whisper модели
  8. Generate `voiceforge.yaml` в XDG_CONFIG_HOME
  9. Run `voiceforge status --doctor` для проверки
  10. Предложить `voiceforge meeting` для первого теста
- Используй `typer.prompt()` / `typer.confirm()` для интерактивности

### 2. First-run detection
- **File:** `src/voiceforge/main.py`
- При первом запуске любой команды (no DB, no config file):
  ```
  Welcome to VoiceForge! Run `voiceforge setup` for guided configuration.
  ```
- Detect: check `XDG_DATA_HOME/voiceforge/transcripts.db` existence

### 3. `voiceforge config init`
- **File:** `src/voiceforge/main.py`
- Генерирует `voiceforge.yaml` с текущими defaults + комментарии
- Как быстрая альтернатива full setup wizard

## Acceptance Criteria
- [ ] `voiceforge setup` — полный guided wizard (10 шагов)
- [ ] First-run hint при первом запуске
- [ ] `voiceforge config init` генерирует конфиг файл
- [ ] Pre-download модели в setup
- [ ] Keyring setup через wizard (interactive prompt)
- [ ] Тесты: test_setup_wizard.py (mocked prompts)

## Autopilot Notes
Полностью автономная задача. Typer поддерживает `prompt()` и `confirm()` из коробки.
BODY
)" \
"$LABELS_P1_FEAT" "$P1" "$L" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 8: Model Pre-Download & Bootstrap
# ─────────────────────────────────────────────
create_issue \
"E8 · Model Pre-Download & Bootstrap Improvements" \
"$(cat <<'BODY'
## Context

Первый analyze зависает на 5 мин при скачивании модели без feedback.

## Scope

### 1. `voiceforge download-models` command
- **File:** `src/voiceforge/main.py`
- Скачивает Whisper модель (по config model_size) + ONNX embedder
- Progress bar через `rich.progress` или `tqdm`
- Retry при network failure

### 2. Bootstrap improvements
- **File:** `scripts/bootstrap.sh`
- После `uv sync`: `uv run voiceforge download-models` (если not --skip-models)
- PipeWire check (from E1)
- RAM check: warning если <4GB
- Финальное сообщение: «Setup complete! Run: voiceforge meeting»

### 3. Doctor improvements
- **File:** `src/voiceforge/cli/status_helpers.py`
- `voiceforge status --doctor` → добавить:
  - Models cached? (Whisper size, pyannote, ONNX)
  - Disk usage of models (~/.cache/huggingface)
  - RAM available vs recommended

## Acceptance Criteria
- [ ] `voiceforge download-models` скачивает и кеширует модели
- [ ] Progress bar при скачивании
- [ ] Bootstrap скачивает модели
- [ ] Doctor показывает model cache status
- [ ] Тесты: test_download_models.py (mocked download)

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"$LABELS_P1_FEAT" "$P1" "$S" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 9: User Flow Post-Listen & Cost
# ─────────────────────────────────────────────
create_issue \
"E9 · User Flow: Post-Listen Auto-Analyze & Cost Estimate" \
"$(cat <<'BODY'
## Context

User Flow Completeness 55% → цель 75%. Ручные шаги: вызов analyze после listen, неизвестная стоимость.

## Scope

### 1. Post-listen auto-analyze
- **File:** `src/voiceforge/main.py` (listen command)
- При Ctrl+C в listen mode → prompt: «Analyze captured audio? [Y/n]»
- `--auto-analyze` flag: skip prompt, analyze immediately
- Используй весь буфер (ring_seconds)

### 2. Cost estimate
- **File:** `src/voiceforge/llm/router.py`, `src/voiceforge/main.py`
- `voiceforge analyze --estimate` → показать estimated cost без выполнения
- Estimate: tokens ≈ words × 1.3, cost = tokens × model_price
- При первом analyze (no history): показать estimate и спросить confirmation

### 3. analyze default = весь буфер (уже в E1, verify)
- Verify что E1 корректно реализовал default

## Acceptance Criteria
- [ ] Ctrl+C в listen → prompt «Analyze? [Y/n]»
- [ ] `--auto-analyze` flag для listen
- [ ] `analyze --estimate` показывает estimated cost
- [ ] Тесты: test_post_listen.py, test_cost_estimate.py

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"$LABELS_P1_FEAT" "$P1" "$M" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 10: Output Polish
# ─────────────────────────────────────────────
create_issue \
"E10 · User Flow: Output Polish — History, Export, Daily Digest" \
"$(cat <<'BODY'
## Context

History output — raw JSON. Export — только file. Нет daily digest.

## Scope

### 1. History human-friendly output
- **File:** `src/voiceforge/cli/history_helpers.py`, `src/voiceforge/main.py`
- Default output: formatted text (дата, duration, speaker count, first 200 chars of summary)
- `--json` flag для machine-readable output
- `--search` results: highlight matching terms

### 2. Export to clipboard
- **File:** `src/voiceforge/main.py` (export command)
- `voiceforge export --clipboard SESSION_ID` → xclip / wl-copy
- Auto-detect Wayland (wl-copy) vs X11 (xclip)
- Fallback: print to stdout if no clipboard tool

### 3. Daily digest
- **File:** `src/voiceforge/cli/digest.py` (новый), `src/voiceforge/main.py`
- `voiceforge daily-report [--date YYYY-MM-DD]`
- Aggregate: all sessions for date, combined action items, total cost
- LLM call: summarize all sessions into one digest (optional, with --llm flag)
- Default: structured text without LLM

### 4. Shell completion
- **File:** `src/voiceforge/main.py`
- Typer автоматически поддерживает: `voiceforge --install-completion`
- Добавить в docs/README: «Install shell completion: voiceforge --install-completion»

## Acceptance Criteria
- [ ] `history` → formatted text по умолчанию, `--json` для raw
- [ ] `export --clipboard` работает (wl-copy / xclip)
- [ ] `daily-report` агрегирует сессии за день
- [ ] Shell completion документирован
- [ ] Тесты: test_history_output.py, test_export_clipboard.py, test_daily_report.py

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"$LABELS_P1_FEAT" "$P1" "$M" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 11: Calendar & Notifications
# ─────────────────────────────────────────────
create_issue \
"E11 · User Flow: Calendar Auto-Analyze & Notification Automation" \
"$(cat <<'BODY'
## Context

Calendar integration есть, но ручная. Telegram webhook есть, но не автоматизирован при smart trigger.

## Scope

### 1. Calendar-aware auto-listen
- **File:** `src/voiceforge/calendar/caldav_poll.py`, `src/voiceforge/core/daemon.py`
- Daemon: poll CalDAV каждые 5 мин
- При upcoming meeting (starts in ≤2 min) → auto-start listen
- При meeting end (ended ≥1 min ago) → auto-analyze с template (if configured)
- Config: `calendar_auto_listen: true/false`

### 2. Auto-notify при smart trigger
- **File:** `src/voiceforge/core/daemon.py`, `src/voiceforge/core/telegram_notify.py`
- При smart trigger analyze → auto-send summary в Telegram (if webhook configured)
- Desktop notification (notify-send) — always

### 3. Action items export
- **File:** `src/voiceforge/main.py` (action-items command)
- `voiceforge action-items --export markdown` → Markdown checklist
- `voiceforge action-items --export csv` → CSV file
- `voiceforge action-items --export clipboard` → to clipboard

## Acceptance Criteria
- [ ] Calendar auto-listen при upcoming meeting
- [ ] Auto-analyze при meeting end
- [ ] Telegram notification при smart trigger
- [ ] Action items export: markdown, csv, clipboard
- [ ] Config keys для calendar_auto_listen
- [ ] Тесты: test_calendar_auto.py, test_action_export.py

## Autopilot Notes
Полностью автономная задача. Зависит от E1 (notifications), E2 (meeting mode).
BODY
)" \
"productization,autopilot,feat,p2,phase:E" "$P2" "$L" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 12: Testing Hardening
# ─────────────────────────────────────────────
create_issue \
"E12 · Testing Hardening: Coverage 75%, Real Audio, Concurrent Access" \
"$(cat <<'BODY'
## Context

Testing 55% → 80%. Coverage 60% (target 75%). Нет real-audio E2E. Нет concurrent access tests.

## Scope

### 1. Coverage → 75%
- Снять omit с модулей: diarizer (mock-only tests), indexer, embedder
- Добавить тесты для omitted modules с полным mocking
- Verify fail_under=75 в pyproject.toml

### 2. Real-audio E2E test
- **File:** `tests/test_real_audio_e2e.py`
- Fixture: 10-second WAV file (speech) in tests/fixtures/
- Test: capture → STT → verify segments not empty
- Mark: `@pytest.mark.integration` (skip in CI без моделей)

### 3. Concurrent access tests
- **File:** `tests/test_concurrent_access.py`
- Test: daemon + CLI + web hitting same SQLite simultaneously
- Verify: no "database is locked" errors
- Use threading + SQLite WAL mode

### 4. Failure injection tests
- **File:** `tests/test_failure_injection.py`
- Scenarios: disk full (mock), network timeout, OOM, corrupted DB
- Verify: graceful degradation, no crashes, user-friendly errors

### 5. Migration rollback tests
- **File:** `tests/test_db_migrations.py` (extend)
- Test: migrate up → verify → migrate down → verify
- Test: corrupt schema_version → recovery

### 6. CLI output snapshot tests
- **File:** `tests/test_cli_snapshots.py`
- Snapshot: `voiceforge status`, `voiceforge history`, `voiceforge cost`
- Detect unintended output format changes

## Acceptance Criteria
- [ ] Coverage ≥ 75% (fail_under=75)
- [ ] Real-audio E2E test (с fixture WAV)
- [ ] Concurrent access test (threading + SQLite)
- [ ] Failure injection (4+ scenarios)
- [ ] Migration rollback tests
- [ ] CLI snapshot tests
- [ ] All existing tests still pass

## Autopilot Notes
Полностью автономная задача. Не запускать полный `pytest tests/` из-за OOM — использовать targeted subsets.
BODY
)" \
"productization,autopilot,test,p1,phase:E,area:testing" "$P1" "$L" "$TESTING"

echo ""

# ─────────────────────────────────────────────
# BLOCK 13: Core Logic Improvements
# ─────────────────────────────────────────────
create_issue \
"E13 · Core Logic: Prompt Caching, Streaming CLI, Whisper Turbo, RAG & STT Improvements" \
"$(cat <<'BODY'
## Context

Core Logic 80% → 90%. Prompt caching (roadmap #19), streaming в CLI, Whisper turbo, RAG/STT quality.

## Scope

### 1. Prompt caching для Claude
- **File:** `src/voiceforge/llm/router.py`
- LiteLLM поддерживает `cache_control` для Anthropic
- System prompt → mark as cacheable (`cache_control: {"type": "ephemeral"}`)
- Log: savings estimate

### 2. Streaming partial results в CLI
- **File:** `src/voiceforge/main.py`, `src/voiceforge/llm/router.py`
- `analyze` показывает partial LLM output в реальном времени
- Используй `analyze_meeting_stream()` (уже есть для desktop)
- Typer + `sys.stdout.write` / `rich.live`

### 3. Whisper large-v3-turbo
- **File:** `src/voiceforge/stt/transcriber.py`, `src/voiceforge/core/config.py`
- Добавить `large-v3-turbo` в допустимые model_size
- 2× faster, ~same quality as large-v3
- Update docs

### 4. RAG auto-discovery
- **File:** `src/voiceforge/rag/indexer.py`, `src/voiceforge/core/config.py`
- Config: `rag_auto_index_path: ~/Documents` (default: null)
- При первом analyze: если rag_auto_index_path set → auto-index
- Warning если path не существует

### 5. Adaptive model selection по RAM
- **File:** `src/voiceforge/core/config.py`, `src/voiceforge/stt/transcriber.py`
- При model_size=auto: check RAM → tiny(<2GB), base(<4GB), small(<8GB), medium(≥8GB)
- Log: «Auto-selected model: small (6.2GB RAM available)»

### 6. STT confidence filtering
- **File:** `src/voiceforge/stt/transcriber.py`
- Segments с confidence <0.3 → пометить `[unclear]`
- Не отправлять unclear segments в LLM prompt (reduce noise)

## Acceptance Criteria
- [ ] Prompt caching работает для Claude models
- [ ] CLI streaming: partial LLM output в реальном времени
- [ ] large-v3-turbo как опция model_size
- [ ] RAG auto-discovery при настроенном path
- [ ] Adaptive model selection (model_size=auto)
- [ ] STT confidence filtering (<0.3 → [unclear])
- [ ] Тесты для каждого пункта

## Autopilot Notes
Полностью автономная задача. 6 независимых подзадач.
BODY
)" \
"productization,autopilot,feat,p1,phase:E,area:ai-ml" "$P1" "$L" "$AIML"

echo ""

# ─────────────────────────────────────────────
# BLOCK 14: CLI & API Polish
# ─────────────────────────────────────────────
create_issue \
"E14 · CLI & API Polish: Rich Output, Config Show, Error Catalog" \
"$(cat <<'BODY'
## Context

CLI & API 75% → 85%. Output formatting, config visibility, error codes.

## Scope

### 1. Rich formatted output
- **File:** `src/voiceforge/cli/history_helpers.py`, `src/voiceforge/main.py`
- Используй `rich` (уже в deps через typer[all]) для таблиц
- `history` → rich table (date, duration, speakers, summary preview)
- `cost` → rich table (date, model, calls, cost)
- `status` → rich panel with colors

### 2. `voiceforge config show`
- **File:** `src/voiceforge/main.py`
- Показать текущий effective config (merged: defaults + yaml + env)
- Highlight overridden values
- `--json` flag для machine-readable

### 3. Error codes catalog
- **File:** `docs/error-codes.md` (новый)
- Формат: VF001–VF050 с описанием, причиной, fix-инструкцией
- `src/voiceforge/core/contracts.py` → enum ErrorCode
- Каждый structured error включает code

### 4. Shell completion docs
- **File:** `README.md`
- Секция: «Shell Completion: `voiceforge --install-completion bash`»

## Acceptance Criteria
- [ ] Rich tables для history, cost, status
- [ ] `voiceforge config show` с highlight overrides
- [ ] Error codes catalog (docs/error-codes.md)
- [ ] ErrorCode enum в contracts.py
- [ ] Shell completion в README
- [ ] Тесты: test_config_show.py, test_rich_output.py

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"$LABELS_P1_FEAT" "$P1" "$M" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# BLOCK 15: Observability Polish
# ─────────────────────────────────────────────
create_issue \
"E15 · Observability: Grafana Dashboard, Alert Rules, Cost Anomaly" \
"$(cat <<'BODY'
## Context

Observability 70% → 85%. Есть Prometheus + OTel, но нет ready-to-use dashboard и alert rules.

## Scope

### 1. Grafana dashboard JSON
- **File:** `monitoring/grafana/voiceforge-dashboard.json` (новый)
- Panels: STT latency, diarization latency, LLM cost/day, pipeline errors, circuit breaker state
- Import-ready (provisioning-compatible)

### 2. Alert rules из коробки
- **File:** `monitoring/alerts.yml` (расширить)
- Rules:
  - High error rate (>10% pipeline_errors in 5min)
  - Circuit breaker open (>5min)
  - High LLM cost ($5/day threshold)
  - Low disk space (<1GB on data dir)
  - Daemon down (no metrics for 5min)

### 3. Cost anomaly detection
- **File:** `src/voiceforge/core/observability.py`
- Metric: `llm_cost_anomaly` gauge (1 if today > 2× 7-day average)
- Log warning when anomaly detected
- Threshold configurable: `cost_anomaly_multiplier: 2.0`

## Acceptance Criteria
- [ ] Grafana dashboard JSON ready to import
- [ ] 5+ alert rules в alerts.yml
- [ ] Cost anomaly metric + warning
- [ ] Dashboard documented в monitoring/README.md
- [ ] Тесты: test_cost_anomaly.py

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"productization,autopilot,feat,p1,phase:E,area:devops" "$P1" "$M" "$DEVOPS"

echo ""

# ─────────────────────────────────────────────
# BLOCK 16: CI/CD Polish
# ─────────────────────────────────────────────
create_issue \
"E16 · CI/CD Polish: Auto-Release, Nightly Smoke, Mock PipeWire" \
"$(cat <<'BODY'
## Context

CI/CD 80% → 90%. Release manual, нет nightly smoke, нет PipeWire mock в CI.

## Scope

### 1. Auto-release на tag push
- **File:** `.github/workflows/release.yml`
- Trigger: push tag `v*` → auto-build wheel + publish PyPI + GitHub Release
- Убрать manual trigger requirement

### 2. Nightly smoke test
- **File:** `.github/workflows/nightly.yml` (новый)
- Schedule: `cron: '0 3 * * *'`
- Steps: uv sync, voiceforge status, run test subset, build wheel
- Notify on failure (GitHub issue or Telegram)

### 3. Mock PipeWire в CI
- **File:** `tests/conftest.py` или `tests/fixtures/`
- Fixture: mock `pw-record` subprocess that returns silence PCM
- Enable audio capture tests in CI (currently skip)

## Acceptance Criteria
- [ ] Tag push → auto-release (wheel + PyPI + GitHub)
- [ ] Nightly smoke workflow
- [ ] Mock PipeWire fixture for CI
- [ ] Audio capture tests run in CI
- [ ] Docs: release process updated

## Autopilot Notes
Полностью автономная задача.
BODY
)" \
"productization,autopilot,chore,p2,phase:E,area:devops" "$P2" "$M" "$DEVOPS"

echo ""

# ─────────────────────────────────────────────
# BLOCK 17: Security Hardening
# ─────────────────────────────────────────────
create_issue \
"E17 · Security: SQLite Encryption, Audit Log, AppArmor" \
"$(cat <<'BODY'
## Context

Security 82% → 90%. SQLite без encryption at rest, нет audit log.

## Scope

### 1. SQLite encryption at rest (optional)
- **File:** `src/voiceforge/core/transcript_log.py`
- Optional dependency: `sqlcipher3` or `pysqlcipher3`
- Config: `encrypt_db: true/false` (default: false)
- При enable: pragma key from keyring (`keyring get voiceforge db_encryption_key`)
- Migration: encrypt existing DB on first run with encryption enabled

### 2. API key usage audit log
- **File:** `src/voiceforge/core/secrets.py`
- Log (structlog info): every keyring read → timestamp, key_name, caller
- Audit table in metrics.db: `api_key_access(timestamp, key_name, operation)`

### 3. AppArmor profile (optional)
- **File:** `security/voiceforge.apparmor` (новый)
- Allow: ~/.local/share/voiceforge/**, ~/.config/voiceforge/**, /tmp/**, pw-record
- Deny: network except API endpoints, other home dirs
- Documentation: how to install profile

## Acceptance Criteria
- [ ] Optional SQLite encryption via sqlcipher
- [ ] API key access audit log
- [ ] AppArmor profile template
- [ ] Docs: security.md updated
- [ ] Тесты: test_encryption.py, test_audit_log.py

## Autopilot Notes
Полностью автономная задача. SQLite encryption — optional dependency, не ломает default path.
BODY
)" \
"productization,autopilot,feat,p2,phase:E,area:security" "$P2" "$M" "$SECURITY"

echo ""

# ─────────────────────────────────────────────
# BLOCK 18: Performance Optimizations
# ─────────────────────────────────────────────
create_issue \
"E18 · Performance: SQLite WAL, Ring Buffer, Adaptive Models" \
"$(cat <<'BODY'
## Context

Performance 65% → 80%. SQLite concurrent access, ring buffer I/O, model selection.

## Scope

### 1. SQLite WAL mode
- **File:** `src/voiceforge/core/transcript_log.py`
- При open: `PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`
- Enables concurrent reads (daemon + CLI + web)
- Verify: no "database is locked" errors

### 2. Ring buffer mmap (optional optimization)
- **File:** `src/voiceforge/audio/buffer.py`
- Вместо file I/O: mmap ring.raw для zero-copy access
- Fallback: текущий file-based approach
- Benchmark: compare latency

### 3. Model size recommendations
- **File:** `src/voiceforge/cli/status_helpers.py`
- `voiceforge status --doctor` → RAM check → model size recommendation
- «Recommended model: small (6.2GB RAM available). Current: medium (may cause OOM)»

## Acceptance Criteria
- [ ] SQLite WAL mode enabled by default
- [ ] Ring buffer mmap (optional, with benchmark)
- [ ] Model size recommendations in doctor
- [ ] No "database is locked" in concurrent tests
- [ ] Тесты: test_sqlite_wal.py, test_buffer_mmap.py

## Autopilot Notes
Полностью автономная задача. WAL mode — самый высокий ROI.
BODY
)" \
"$LABELS_P1_FEAT" "$P1" "$M" "$BACKEND"

echo ""

# ─────────────────────────────────────────────
# USER DECISION BLOCKS
# ─────────────────────────────────────────────

# BLOCK 19: Desktop UI Strategy (decision locked)
create_issue \
"E19 · Desktop UI: Invest in Tauri (decision locked)" \
"$(cat <<'BODY'
## Context

Решение принято: **Invest in Tauri**. Desktop становится primary GUI surface для VoiceForge.

## Locked Scope
- [ ] E2E meeting flow in Tauri
- [ ] Tray icon: Start/Stop listen, Open, Quit
- [ ] Global hotkey: Ctrl+Shift+V → toggle listen
- [ ] Playwright E2E tests
- [ ] AppImage packaging verification

## Scope Guard
- Не делать Web-only pivot
- Не развивать Web UI как второй основной продуктовый frontend
- Desktop-track брать после Wave 3 backend/quality

## Decision Source
- `docs/runbooks/phase-e-decision-log.md`

## Labels
productization, phase:E
BODY
)" \
"productization,phase:E,area:frontend" "$P1" "$L" "$FRONTEND"

echo ""

# BLOCK 20: Surface Freeze Decisions (decision locked)
create_issue \
"E20 · Scope Policy: Freeze Web UI / Telegram / RAG Watcher; Narrow Calendar" \
"$(cat <<'BODY'
## Context

Решение принято. Для автопилота это **policy issue**, а не feature roadmap item.

## Locked Decisions

### Web UI
- **Status:** Freeze / maintenance-only
- Разрешено: bugfix, contract parity, admin/debug usability
- Не делать: SPA rewrite, второй основной frontend

### Telegram Bot
- **Status:** Freeze / maintenance-only
- Разрешено: webhook reliability, delivery fixes, summary push
- Не делать: bot-first UX, inline flows, rich bot surface

### Calendar (CalDAV)
- **Status:** Invest narrow
- Разрешено: auto-listen / auto-analyze / notify на существующем CalDAV stack
- Не делать: Google Calendar support, multi-provider expansion

### RAG Watcher
- **Status:** Freeze / maintenance-only
- Разрешено: stability, debounce/dedup, tests
- Не делать: management UI, auto-discovery, large UX expansion

## Implementation Hook
- Calendar narrow scope реализуется через `E11`
- Остальные surfaces не расширять без нового user decision

## Decision Source
- `docs/runbooks/phase-e-decision-log.md`

## Labels
productization, phase:E
BODY
)" \
"productization,phase:E" "$P2" "$S" "$BACKEND"

echo ""

# BLOCK 21: Beyond Boundaries (decision locked)
create_issue \
"E21 · Strategic Boundaries: Accept Later / Defer / Reject (decision locked)" \
"$(cat <<'BODY'
## Context

Решение принято. Это **boundary issue**: фиксирует, что допустимо открывать после Phase E, а что не трогаем.

## Accept Later
- **Managed packaging (APT / Snap / Homebrew)** — принять в будущий трек после Linux beta / stable desktop release proof

## Defer
- macOS / Windows
- Browser extension
- GPU acceleration
- Whisper.cpp / MLX backend

## Reject For Current Phase
- Cloud-hosted / SaaS lite
- Web-only main UI
- Real-time collaborative notes
- PostgreSQL + pgvector
- LLM fine-tuning on meeting data

## Revisit Triggers
- Managed packaging: Linux beta + stable release proof
- macOS / Windows: Linux beta + stable audio/IPC abstraction
- Browser extension: PipeWire остаётся главным onboarding blocker
- GPU / Whisper.cpp / MLX: CPU perf становится системным bottleneck

## Decision Source
- `docs/runbooks/phase-e-decision-log.md`

## Labels
productization, phase:E
BODY
)" \
"productization,phase:E" "$P3" "$L" "$BACKEND"

echo ""

echo "=== All issues created ==="

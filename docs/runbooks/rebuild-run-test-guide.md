# Пошаговый гайд: пересборка, запуск и тесты (в toolbox)

Линейная последовательность для **Fedora Atomic Cosmic**: всё выполняется **внутри toolbox**. Путь к репо в контейнере: **`/var/home/user/Projects/voiceforge`** (домашний каталог хоста проброшен в toolbox).

**Среда:** Fedora Atomic; разработка и сборка — только в toolbox. Демон и десктоп запускаются в том же toolbox (одна D-Bus-сессия).

---

## Шаг 0. Вход в toolbox и переход в репо

**На хосте** (один раз на сессию):

```bash
toolbox enter
```

При необходимости указать контейнер: `toolbox enter fedora-toolbox-43` (имя смотрите в `toolbox list`).

**В toolbox** (все дальнейшие команды — из этого каталога):

```bash
cd /var/home/user/Projects/voiceforge
```

Все шаги ниже выполняются **внутри toolbox**, из корня репо `/var/home/user/Projects/voiceforge`, если не указано иное.

---

## Шаг 1. Окружение и зависимости Python (в toolbox)

**1.1. uv** (если ещё нет в toolbox):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

**1.2. Синхронизировать зависимости (и при необходимости модели):**

```bash
./scripts/bootstrap.sh
```

Без предзагрузки моделей: `./scripts/bootstrap.sh --skip-models`.

**1.3. Проверить окружение:**

```bash
uv run voiceforge status --doctor
```

Ожидаются зелёные проверки (конфиг, keyring при нужде API, RAG, PipeWire). Ошибки — [config-env-contract.md](config-env-contract.md), [keyring-keys-reference.md](keyring-keys-reference.md).

---

## Шаг 2. Пересборка десктопа (Tauri) в toolbox

**2.1. Системные зависимости для сборки (в toolbox):**

```bash
./scripts/check-desktop-deps.sh
```

При `[FAIL]` установить пакеты **внутри toolbox**:

```bash
sudo dnf install -y gcc nodejs npm pipewire-utils pulseaudio-utils pkg-config \
  webkit2gtk4.1-devel gtk3-devel openssl-devel librsvg2-devel ffmpeg
```

Rust (если нет): `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`, затем `source "$HOME/.cargo/env"`.
Одной командой: [desktop-build-deps.md](desktop-build-deps.md), скрипт `./scripts/setup-desktop-toolbox.sh`.

**2.2. Сборка фронта и Tauri:**

```bash
cd /var/home/user/Projects/voiceforge/desktop && npm install && npm run build && npm run tauri build
```

При ошибке из‑за `--ci`: `CI=false npm run tauri build`.

Артефакты:

- Бинарник: `/var/home/user/Projects/voiceforge/desktop/src-tauri/target/release/voiceforge-desktop`
- Пакеты: `/var/home/user/Projects/voiceforge/desktop/src-tauri/target/release/bundle/` (.deb, rpm, appimage)

**2.3. Вернуться в корень репо:**

```bash
cd /var/home/user/Projects/voiceforge
```

---

## Шаг 3. Запуск демона (в toolbox)

Во **втором терминале** на хосте снова войти в тот же toolbox, затем:

```bash
cd /var/home/user/Projects/voiceforge
uv run voiceforge daemon
```

Оставить работающим. Демон поднимает D-Bus `com.voiceforge.App`; без него десктоп не делает запись и анализ.

Проверка (в третьем терминале или после остановки демона): из корня репо в toolbox `uv run voiceforge status` — без ошибки.

---

## Шаг 4. Запуск десктопа (в toolbox)

**Вариант A — режим разработки (hot reload):**

В другом терминале: `toolbox enter`, затем:

```bash
cd /var/home/user/Projects/voiceforge/desktop && npm run tauri dev
```

**Вариант B — запуск собранного бинарника (для KV2 sign-off и т.п.):**

Демон уже запущен (шаг 3). В другом терминале в toolbox:

```bash
/var/home/user/Projects/voiceforge/desktop/src-tauri/target/release/voiceforge-desktop
```

Либо после установки .deb из `bundle/deb/` — команда `voiceforge-desktop` из PATH.

(имя файла — по версии в сборке). Убедиться, что в интерфейсе статус «демон доступен», доступны запись и copilot.

---

## Шаг 5. Тестирование (в toolbox)

Все команды — из корня репо в toolbox: `cd /var/home/user/Projects/voiceforge`.

| Уровень | Что проверяет | Команда |
|--------|----------------|--------|
| **Python** | Юнит и интеграционные тесты | `uv run pytest tests/ -q --tb=line` |
| **Desktop UI (Playwright)** | Навигация, моки, a11y, визуальные снимки | `cd desktop && npm run e2e:release-gate` |
| **Native (WebdriverIO)** | Реальное окно Tauri (advisory) | `cd desktop && npm run e2e:native:headless` |

**Подмножество тестов (быстрее):**

```bash
uv run pytest tests/test_daemon_helpers.py tests/test_config_settings.py tests/test_release_metadata.py -q --tb=line
```

**E2E десктопа:**

```bash
cd /var/home/user/Projects/voiceforge/desktop && npm run e2e:release-gate
```

**Визуальный прогон Playwright (с UI):**

```bash
cd desktop && npm run e2e:ui
```

**Preflight репо (опционально):**

```bash
./scripts/preflight_repo.sh --with-tests
```

**Где лежат отчёты (в репо в toolbox):**

| Отчёт | Путь в toolbox |
|-------|-----------------|
| Playwright HTML | `desktop/playwright-report/`; открыть: `cd desktop && npm run e2e:report` |
| Playwright trace/screenshot | `desktop/test-results/` (при падении) |
| Native smoke | `desktop/e2e-native/artifacts/latest/` |
| Python coverage | корень репо: `coverage.xml`, `coverage.json` (при запуске с `--cov`) |

---

## Шпаргалка (копировать по шагам, всё в toolbox)

```bash
# В терминале 1 — вход и окружение
toolbox enter
cd /var/home/user/Projects/voiceforge
./scripts/bootstrap.sh
uv run voiceforge status --doctor

# Сборка десктопа
./scripts/check-desktop-deps.sh
cd /var/home/user/Projects/voiceforge/desktop && npm install && npm run build && npm run tauri build
cd /var/home/user/Projects/voiceforge

# В терминале 2 — демон
toolbox enter
cd /var/home/user/Projects/voiceforge
uv run voiceforge daemon

# В терминале 3 — десктоп (dev или бинарник)
toolbox enter
cd /var/home/user/Projects/voiceforge/desktop && npm run tauri dev
# или бинарник:
# /var/home/user/Projects/voiceforge/desktop/src-tauri/target/release/voiceforge-desktop

# Тесты (из корня репо в toolbox)
cd /var/home/user/Projects/voiceforge
uv run pytest tests/ -q --tb=line
cd desktop && npm run e2e:release-gate
```

---

## Частые проблемы (toolbox)

| Проблема | Решение (в toolbox) |
|----------|----------------------|
| `pw-record` not found | `sudo dnf install pipewire pipewire-utils` |
| `webkit2gtk-4.1` / `gtk+-3.0` not found | `sudo dnf install webkit2gtk4.1-devel gtk3-devel` |
| `invalid value '1' for '--ci'` при tauri build | `CI=false npm run tauri build` |
| Десктоп не видит демон | Демон и десктоп должны быть в **одном и том же** toolbox (одна D-Bus-сессия). Запускать оба после `toolbox enter`. |
| OOM при тестах/анализе | Закрыть лишние приложения; для diarization см. [pyannote-version.md](pyannote-version.md) |
| Много skipped в pytest | `uv sync --extra all --group dev` или заново `./scripts/bootstrap.sh` |
| torchcodec/pyannote «libavutil.so not found» | `sudo dnf install ffmpeg` **в toolbox**; см. [pyannote-version.md](pyannote-version.md) |

Дополнительно: [installation-guide.md](installation-guide.md) (раздел 0 — только toolbox), [desktop-build-deps.md](desktop-build-deps.md), [cli-commands-and-run.md](cli-commands-and-run.md).

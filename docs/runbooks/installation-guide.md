# Гайд установки и запуска VoiceForge

Краткий полный гайд: где запускать, когда ребилдить, как поднять демон и как обновляться.

---

## 1. Где и как запускать

### CLI (команды voiceforge)

- **Окружение:** Fedora Atomic / обычный Fedora; удобно разрабатывать в **toolbox** (или distrobox).
- **Из репо (без установки в систему):**
  ```bash
  cd /path/to/voiceforge
  ./scripts/bootstrap.sh   # один раз
  uv sync --extra all      # при изменении зависимостей
  uv run voiceforge <команда>
  ```
- **Запуск на хосте:** те же команды можно выполнять на хосте, если в этой среде установлены `uv`, Python и ключи в keyring (сервис `voiceforge`, имена `anthropic`, `openai`, `huggingface`). Либо установить пакет: `uv pip install -e .` и тогда `voiceforge` доступен в PATH.

### Десктоп (Tauri)

- **Сборка** делается в среде, где есть gcc, Node, Rust, WebKit/GTK (на Atomic — в **toolbox**):
  ```bash
  cd /path/to/voiceforge
  ./scripts/setup-desktop-toolbox.sh   # один раз
  ./scripts/check-desktop-deps.sh     # проверка
  cd desktop && npm run tauri build
  ```
  Эквивалент: `cd desktop && npm run build && cargo tauri build`.
- **Где запускать приложение:** собранный бинарник лежит в `desktop/src-tauri/target/release/bundle/` (поддиректория зависит от формата: deb, appimage и т.д.). Запускать можно **на хосте** или в том же toolbox — нужна одна и та же D-Bus сессия, что и у демона (см. ниже).
- **Удобный запуск:** добавить в PATH путь к бинарнику или создать ярлык на исполняемый файл из `bundle/`.

---

## 2. Нужно ли ребилдить после правок

| Что меняли | Действие |
|------------|----------|
| Только Python (backend, CLI) | Перезапуск демона и/или `uv run voiceforge ...`; ребилд десктопа не нужен. |
| Frontend (Vite/TS/UI в `desktop/`) или Tauri (Rust в `desktop/src-tauri/`) | Ребилд десктопа: `cd desktop && npm run build && cargo tauri build`. Для итераций удобнее **режим разработки**: `cd desktop && npm run tauri dev` (перезапуск при изменении фронта). |
| Конфиг Tauri / зависимости npm или Cargo | После смены зависимостей: `npm install` в `desktop/`, при необходимости `cargo build` в `desktop/src-tauri/`, затем полный билд. |

Итого: после правок только в Python — ребилд десктопа не требуется. После правок в `desktop/` — либо `npm run tauri dev`, либо полный `npm run tauri build`.

---

## 3. Как запустить «все демоны»

У VoiceForge **один демон** — процесс `voiceforge daemon`. Он обслуживает и CLI, и десктоп (через D-Bus).

- **Вручную (отдельный терминал):**
  ```bash
  cd /path/to/voiceforge
  uv run voiceforge daemon
  ```
  Или, если voiceforge установлен в окружение: `voiceforge daemon`.
- **Как сервис пользователя (systemd):** `voiceforge install-service` и `voiceforge uninstall-service` (см. документацию по сервису в проекте).
- Перед запуском **десктопного приложения** демон должен быть уже запущен, иначе приложение покажет подсказку «Запустите демон: voiceforge daemon».

---

## 4. Быстрое обновление

- **Обновление кода и зависимостей:**
  ```bash
  cd /path/to/voiceforge
  git pull
  uv sync --extra all
  ```
- **Десктоп:** если менялись только Python/бэкенд — перезапуск демона достаточен. Если менялись `desktop/` (фронт или Tauri) — пересобрать:
  ```bash
  cd desktop && npm install && npm run build && cargo tauri build
  ```
- **Быстрая итерация по UI:** не собирать каждый раз релизный билд — использовать `cd desktop && npm run tauri dev` (демон при этом должен быть запущен).

---

## См. также

- [quickstart.md](quickstart.md) — быстрые шаги по первой встрече
- [desktop-build-deps.md](desktop-build-deps.md) — зависимости и проверка окружения для сборки десктопа
- [config-env-contract.md](config-env-contract.md) — переменные и keyring

# Гайд установки и запуска VoiceForge

Краткий полный гайд: где запускать, когда ребилдить, как поднять демон и как обновляться.

---

## 0. Работа только в toolbox (рекомендуется)

Чтобы не ставить окружение и на хост, и в контейнер, делайте **всё внутри одного toolbox**: CLI, демон, сборка и запуск десктопа. Репозиторий на хосте доступен в контейнере по тому же пути (домашний каталог проброшен).

**Куда что вводить:** в командах ниже указано **«Хост»** или **«В toolbox»** — вводите в том терминале, где вы сейчас (на хосте Fedora или уже внутри контейнера).

---

### Шаг 0.1. Узнать, есть ли уже контейнер

**Хост** (терминал на Fedora, не в контейнере):

```bash
toolbox list
```

Если видите контейнер (например `fedora-toolbox-43` или `fedora-toolbox-40`) — можно в него войти. Если список пустой — создать контейнер (шаг 0.2).

---

### Шаг 0.2. Создать контейнер (если ещё нет)

**Хост:**

```bash
toolbox create
```

Имя по умолчанию будет что-то вроде `fedora-toolbox-43` (по версии образа). Запомните его или снова выполните `toolbox list`.

---

### Шаг 0.3. Войти в контейнер

**Хост:**

```bash
toolbox enter
```

Если контейнеров несколько, укажите имя:

```bash
toolbox enter fedora-toolbox-43
```

(подставьте своё имя из `toolbox list`). После входа приглашение может измениться (например, показывается имя контейнера) — дальше все команды вводите **в этом же терминале (в toolbox)**.

---

### Шаг 0.4. Установка VoiceForge внутри toolbox

**В toolbox** (тот же терминал, куда вы вошли):

```bash
cd /var/home/user/Projects/voiceforge
./scripts/bootstrap.sh
```

Дождитесь окончания (keyring при необходимости настройте здесь же: `keyring set voiceforge anthropic` и т.д.).

Для записи аудио (`voiceforge listen`) в контейнере нужен `pw-record`:

**В toolbox:**

```bash
sudo dnf install -y pipewire-utils
```

Затем установка зависимостей для десктопа:

**В toolbox:**

```bash
./scripts/setup-desktop-toolbox.sh
```

Проверка окружения:

**В toolbox:**

```bash
./scripts/check-desktop-deps.sh
uv run voiceforge status   # или voiceforge doctor — диагностика конфига, keyring, RAG, Ollama
```

Если все проверки [OK] — можно собирать десктоп и запускать CLI/демон **только из этого контейнера**. На хосте больше ничего для VoiceForge ставить не нужно.

---

### Шаг 0.5. Ежедневный вход: только toolbox

- **Хост:** один раз выполнить `toolbox enter` (при необходимости `toolbox enter ИМЯ_КОНТЕЙНЕРА`).
- **В toolbox:**
  `cd /var/home/user/Projects/voiceforge`
  затем, например:
  `uv run voiceforge daemon` (в одном терминале),
  в другом терминале снова `toolbox enter` → `cd /var/home/user/Projects/voiceforge` → `uv run voiceforge listen` или запуск десктопа (`cd desktop && npm run tauri dev`).

Итого: **на хосте** вы только входите в контейнер (`toolbox enter`). **Всё остальное** — внутри toolbox, по пути `/var/home/user/Projects/voiceforge`.

---

## 1. Где и как запускать

### CLI (команды voiceforge)

- **Окружение:** Fedora Atomic / обычный Fedora; удобно разрабатывать в **toolbox** (или distrobox). Рекомендуется один окружение — см. раздел 0 выше.
- **Из репо (без установки в систему)** — команды выполнять **в toolbox** (или на хосте, если решили ставить и там):
  ```bash
  cd /var/home/user/Projects/voiceforge
  ./scripts/bootstrap.sh   # один раз
  uv sync --extra all      # при изменении зависимостей
  uv run voiceforge <команда>
  ```
- **Запуск на хосте:** те же команды можно выполнять на хосте, если в этой среде установлены `uv`, Python и ключи в keyring (сервис `voiceforge`, имена `anthropic`, `openai`, `huggingface`). Для единого окружения лучше только toolbox — тогда на хосте ничего не ставим.

### Десктоп (Tauri)

- **Сборка** делается в среде, где есть gcc, Node, Rust, WebKit/GTK (на Atomic — в **toolbox**):
  ```bash
  cd /path/to/voiceforge
  ./scripts/setup-desktop-toolbox.sh   # один раз
  ./scripts/check-desktop-deps.sh     # проверка
  cd desktop && npm run tauri build
  ```
  Эквивалент: `cd desktop && npm run build && cargo tauri build`.
- **Где запускать приложение:** собранный бинарник — `desktop/src-tauri/target/release/voiceforge-desktop`; пакеты (.rpm, .deb) — в `desktop/src-tauri/target/release/bundle/rpm/` и `bundle/deb/`. Запускать можно **на хосте** или в том же toolbox — нужна одна и та же D-Bus сессия, что и у демона (см. ниже).
- **Запуск без установки:** `./desktop/src-tauri/target/release/voiceforge-desktop` (из корня репо). Или установить пакет: Fedora — `sudo dnf install desktop/src-tauri/target/release/bundle/rpm/VoiceForge-*.rpm`; Debian/Ubuntu — `sudo dpkg -i desktop/.../bundle/deb/VoiceForge_*.deb`. Подробнее: [desktop-build-deps.md](desktop-build-deps.md) (раздел «Установка и запуск после сборки»).

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
- [pyannote-version.md](pyannote-version.md) — при OOM или падениях диаризации (откат на 3.3.2)

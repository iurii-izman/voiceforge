# Тестирование GUI десктопа (VoiceForge)

Практический runbook для desktop QA без платных сервисов: как автоматизировать проверку кнопок, состояний, вёрстки и доступности, и что оставить отдельным release-gate/manual audit.

**Среда:** Fedora Atomic Cosmic; разработка и тяжёлые тесты — в **toolbox**. См. также [desktop-build-deps.md](desktop-build-deps.md), [test-operations.md](test-operations.md).

---

## 1. Рекомендуемая стратегия: 3 слоя

| Слой | Что проверяем | Инструменты | Статус в проекте |
|------|----------------|-------------|------------------|
| **Layer 1 — Mocked desktop autopilot** | Навигация, кнопки, widgets, mock-Tauri/mock-daemon happy paths | Playwright + `window.__VOICEFORGE_TEST_HOOKS__` | **Уже внедрён** |
| **Layer 2 — Accessibility + visual regression** | Серьёзные WCAG-регрессии и визуальные сдвиги на ключевых экранах | `@axe-core/playwright`, `toHaveScreenshot()` | **Уже внедрён** |
| **Layer 3 — Native shell smoke** | Реальное окно Tauri, shell render, daemon-off path, settings/toggles, базовые native сценарии | `tauri-driver` + WebdriverIO | **Внедрён локальный Linux path** |

Идея простая: большинство регрессий ловить дешёвым deterministic слоем, а дорогие native-specific вещи оставить отдельным узким smoke/release gate.

---

## 2. Layer 1: Playwright desktop autopilot

Текущий стек запускается против **vite preview** (localhost:4173), но уже не ограничивается простым layout smoke. В проекте есть bridge `desktop/src/platform.js`, который переключает frontend между реальными Tauri APIs и test hooks `window.__VOICEFORGE_TEST_HOOKS__`.

### 2.0. Один обязательный запуск

Чтобы не держать в голове несколько разрозненных команд, в `desktop/package.json` закреплены canonical entrypoints:

- `npm run e2e:gate` — **обязательный бесплатный desktop regression gate** для каждой итерации
- `npm run e2e:release-gate` — **канонический blocking desktop UI gate**, сначала пересобирает свежий `dist`, затем гоняет `e2e:gate`
- `npm run e2e:native:headless` — **канонический advisory native smoke** для Linux/toolbox; пишет evidence в `desktop/e2e-native/artifacts/`

Policy:

- CI и обычная разработка опираются на `npm run e2e:gate`
- перед desktop release или заметным desktop-first изменением прогоняется `npm run e2e:release-gate`
- `npm run e2e:native:headless` остаётся advisory Linux-native smoke, а не частью обязательного gate
- `npm run e2e:native` остаётся headed-вариантом для локального ручного smoke

### 2.1. Запуск локально

```bash
cd desktop
npm ci
npm run e2e:gate
npm run e2e:release-gate
npm run e2e:native:headless
npm run e2e:ui
npm run e2e:report
```

Playwright сам поднимет `npm run preview`. HTML report сохраняется в `desktop/playwright-report/`, детальные артефакты падений — в `desktop/test-results/`.

### 2.2. Что уже проверяется

- `desktop/e2e/nav.spec.js`: layout/navigation smoke, роли, вкладки, базовые controls
- `desktop/e2e/autopilot.spec.js`: mocked desktop flows вокруг listen/analyze, sessions/detail, transcript/RAG search, calendar action, settings/autostart/updater; **E19 desktop-first flow** — один сценарий Record → Analyze → View → Export (полный цикл встречи)
- `desktop/e2e/regression.spec.js`: stateful desktop UX regression matrix для daily-driver path: onboarding/state persistence, compact/full recovery, recent-session open/back, settings persistence, daemon-off → retry recovery
- `desktop/e2e/helpers/desktopHarness.js`: детерминированный mock runtime для invoke/listen/store/window/notification/global shortcuts/updater

**Tray и hotkeys (E19 #142):** пункты меню трея (Open, Start/Stop listen, Quit) реализованы в `desktop/src-tauri/src/tray.rs`. Глобальный hotkey для toggle listen настраивается в Settings и регистрируется через `@tauri-apps/plugin-global-shortcut` в `desktop/src/main.js`; проверка — вручную по [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md) § 4.

### 2.3. Ограничения слоя

- этот слой не поднимает реальное окно Tauri
- не доказывает корректность tray icon, native notifications UX, global hotkeys в фоне, updater install flow
- не заменяет Wayland/X11-специфичные проверки

---

## 3. Layer 2: a11y и visual regression

### 3.1. Accessibility smoke

В проекте уже есть `desktop/e2e/a11y.spec.js` на `@axe-core/playwright`.

Покрытие:

- Home
- Sessions
- Settings slide-out panel

Запуск:

```bash
cd desktop
npm ci
npm run build
npx playwright test e2e/a11y.spec.js --project=chromium
```

Policy:

- блокирующими считаются `serious` и `critical` нарушения
- найденные дефекты исправляются в UI, а не маскируются в тестах

### 3.2. Visual regression

В проекте уже есть `desktop/e2e/visual.spec.js` и baseline snapshots:

- `home-dashboard-chromium-linux.png`
- `sessions-list-chromium-linux.png`
- `settings-slide-panel-chromium-linux.png`

Обновление baseline только после осознанного UI-изменения:

```bash
cd desktop
npm ci
npm run build
npm run e2e:update-snapshots
```

---

## 4. Layer 3: Реальное окно Tauri

Здесь тесты запускают **собранный бинарник** и управляют им через WebDriver. Нужны: `tauri-driver`, WebdriverIO, на Linux — **WebKitWebDriver** и при необходимости **xvfb** для headless.

### 4.1. Когда нужен этот слой

- перед release candidate
- для smoke по реальному окну, shell render и native integration
- когда mocked Playwright layer уже зелёный, а нужно подтвердить native shell contract

### 4.2. Текущее решение в репо

В репо теперь есть отдельный каталог:

```text
desktop/e2e-native/
```

Он содержит:

- `package.json`
- `wdio.conf.js`
- `specs/native-smoke.e2e.js`

Запуск из `desktop/`:

```bash
npm run e2e:native
```

Headless/path для GUI-less Linux runner:

```bash
npm run e2e:native:headless
```

Текущее покрытие native smoke:

- launch реального Tauri window
- daemon-off shell / retry path
- main navigation
- settings slide-out panel
- persistence для `close-to-tray` и `updater-check-on-launch`

### 4.3. Зависимости

Нужны:

- `tauri-driver`
- `WebKitWebDriver`
- при headless-запуске: `xvfb-run`

Установка `tauri-driver` без root:

```bash
cargo install tauri-driver --locked
```

Если `WebKitWebDriver` не найден автоматически, используйте:

```bash
export TAURI_NATIVE_DRIVER=/path/to/WebKitWebDriver
npm run e2e:native
```

### 4.4. Фактическая структура каталогов

```text
desktop/
  e2e/                     # mocked Playwright
  e2e-native/              # WebdriverIO + tauri-driver
    package.json
    wdio.conf.js
    specs/native-smoke.e2e.js
```

Корень запуска остаётся `desktop/`, debug binary собирается в `desktop/src-tauri/target/debug/voiceforge-desktop`.

### 4.5. Как работает конфиг

`desktop/e2e-native/wdio.conf.js` сам:

- собирает debug Tauri binary через `npm run tauri build -- --debug --no-bundle`
- находит `tauri-driver`
- ищет `WebKitWebDriver` через env и известные Linux paths
- поднимает `tauri-driver` с явным `--native-driver`

### 4.6. Запуск native smoke

Канонический advisory native smoke для reproducible Linux/toolbox evidence:

```bash
cd desktop
npm run e2e:native:headless
```

Он запускает `../scripts/run_desktop_native_smoke.sh --headless`, пишет preflight/context и собирает артефакты в:

```text
desktop/e2e-native/artifacts/latest/
```

Если smoke падает или уходит в timeout, первым делом смотреть:

```text
desktop/e2e-native/artifacts/latest/summary.txt
desktop/e2e-native/artifacts/latest/wdio.log
desktop/e2e-native/artifacts/latest/tauri-driver.log
desktop/e2e-native/artifacts/latest/tauri-driver.stderr.log
```

Headed-вариант для локального smoke с видимым окном:

```bash
cd desktop
npm run e2e:native
```

Полный локальный blocking desktop UI gate одной командой:

```bash
cd desktop
npm run e2e:release-gate
```

Если нужен smoke с реальным daemon, запускайте `uv run voiceforge daemon` в отдельном терминале до native suite. Базовый smoke path в репо намеренно не зависит от живого backend и проверяет shell в daemon-off режиме.

### 4.7. CI policy

- mocked Playwright suite остаётся основным CI regression signal
- native smoke через `tauri-driver` пока считается **toolbox/local advisory Linux shell smoke**, а не обязательным CI job
- причина: runner должен иметь `tauri-driver`, `WebKitWebDriver`, GUI-capable environment и поддержку Linux desktop stack
- если появится стабильный Linux GUI runner, native smoke можно вынести в отдельный blocking job

---

## 5. Release gate и ручные проверки

Полная матрица desktop release gate вынесена в [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md).

Короткая идея:

- Playwright/autopilot закрывает functional/a11y/visual regressions
- `desktop/e2e/regression.spec.js` теперь является каноническим UX evidence слоем для stateful regressions desktop daily-driver path
- native smoke доказывает, что реальный Tauri shell вообще поднимается и не ломает базовые сценарии
- tray, updater install, global shortcuts, Wayland/X11 quirks и multi-monitor остаются manual/environment-specific proof

Краткая policy:

- **обязательный бесплатный gate:** `cd desktop && npm run e2e:gate`
- **blocking desktop UI gate:** `cd desktop && npm run e2e:release-gate`
- **advisory native smoke:** `cd desktop && npm run e2e:native:headless`
- **если advisory smoke падает:** triage вести по `desktop/e2e-native/artifacts/latest/`

---

## 6. Ссылки

- [Tauri — Tests](https://v2.tauri.app/develop/tests/)
- [Tauri — WebDriver](https://v2.tauri.app/develop/tests/webdriver/)
- [Tauri — WebdriverIO example](https://v2.tauri.app/develop/tests/webdriver/example/webdriverio/)
- [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md)
- [desktop-build-deps.md](desktop-build-deps.md)
- [test-operations.md](test-operations.md)

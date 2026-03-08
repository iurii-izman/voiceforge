# Тестирование GUI десктопа (VoiceForge)

Практический runbook для desktop QA без платных сервисов: как автоматизировать проверку кнопок, состояний, вёрстки и доступности, и что оставить отдельным release-gate/manual audit.

**Среда:** Fedora Atomic Cosmic; разработка и тяжёлые тесты — в **toolbox**. См. также [desktop-build-deps.md](desktop-build-deps.md), [test-operations.md](test-operations.md).

---

## 1. Рекомендуемая стратегия: 3 слоя

| Слой | Что проверяем | Инструменты | Статус в проекте |
|------|----------------|-------------|------------------|
| **Layer 1 — Mocked desktop autopilot** | Навигация, кнопки, widgets, mock-Tauri/mock-daemon happy paths | Playwright + `window.__VOICEFORGE_TEST_HOOKS__` | **Уже внедрён** |
| **Layer 2 — Accessibility + visual regression** | Серьёзные WCAG-регрессии и визуальные сдвиги на ключевых экранах | `@axe-core/playwright`, `toHaveScreenshot()` | **Уже внедрён** |
| **Layer 3 — Native shell smoke** | Реальное окно Tauri, tray/window/plugin/native integration paths | `tauri-driver` + WebdriverIO | **Следующий этап** |

Идея простая: большинство регрессий ловить дешёвым deterministic слоем, а дорогие native-specific вещи оставить отдельным целевым smoke/release gate.

---

## 2. Layer 1: Playwright desktop autopilot (текущий baseline)

Текущий стек запускается против **vite preview** (localhost:4173), но уже не ограничивается простым layout smoke. В проекте есть bridge `desktop/src/platform.js`, который переключает frontend между реальными Tauri APIs и test hooks `window.__VOICEFORGE_TEST_HOOKS__`.

### 2.1. Запуск локально

**В toolbox** (рекомендуется) или на хосте с Node.js:

```bash
cd desktop
npm ci
npm run build
npm run e2e
npm run e2e:ui
npm run e2e:report
```

Playwright сам поднимет `npm run preview`. HTML report сохраняется в `desktop/playwright-report/`, детальные артефакты падений — в `desktop/test-results/`.

### 2.2. Что уже проверяется

- `desktop/e2e/nav.spec.js`: layout/navigation smoke, роли, вкладки, базовые controls
- `desktop/e2e/autopilot.spec.js`: mocked desktop flows вокруг listen/analyze, sessions/detail, transcript/RAG search, calendar action, settings/autostart/updater
- `desktop/e2e/helpers/desktopHarness.js`: детерминированный mock runtime для invoke/listen/store/window/notification/global shortcuts/updater

### 2.3. Почему это лучший open-source baseline

- быстрый и воспроизводимый: не нужен реальный daemon, D-Bus и собранный Tauri binary на каждый PR
- ловит реальные пользовательские сценарии, а не только snapshot DOM
- даёт артефакты для разбора regressions: trace, screenshot, video, HTML report
- не создаёт OOM-risk и не завязывает CI на нестабильные desktop-driver зависимости

### 2.4. Ограничения слоя

- этот слой не поднимает реальное окно Tauri
- не доказывает корректность tray icon, native notifications UX, global hotkeys в фоне, updater install flow
- не заменяет Wayland/X11-специфичные проверки

---

## 3. Layer 2: a11y и visual regression (текущий baseline)

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

## 4. Layer 3: Реальное окно Tauri (следующий слой, не замена текущему)

Здесь тесты запускают **собранный бинарник** и управляют им через WebDriver. Нужны: `tauri-driver`, WebdriverIO, на Linux — **WebKitWebDriver** (webkit2gtk-driver) и при необходимости **xvfb** для headless.

### 4.1. Когда нужен этот слой

- перед release candidate
- для smoke по реальному окну, tray, background behavior и plugin integration
- когда mocked Playwright layer уже зелёный, а нужно подтвердить native shell contract

### 4.2. Зависимости

**В toolbox (Fedora):**

```bash
# Rust и tauri-driver
cargo install tauri-driver --locked

# Драйвер WebKit для WebDriver (Linux)
sudo dnf install -y webkit2gtk4.1-devel   # уже есть для сборки Tauri
# Отдельный пакет драйвера (проверить наличие в репо Fedora):
sudo dnf install -y webkit2gtk-driver || true
# Если пакета нет — возможно, WebKitWebDriver входит в webkit2gtk4; проверка:
which WebKitWebDriver || echo "WebKitWebDriver not in PATH"
```

Если `WebKitWebDriver` не найден: в Fedora пакет может называться иначе или входить в `webkit2gtk4.1`; для CI на Ubuntu в доках Tauri указывают `webkit2gtk-driver`.

**Для headless (например CI):**

```bash
sudo dnf install -y xvfb
# Запуск тестов: xvfb-run npm test (в каталоге e2e-tests)
```

### 4.3. Рекомендуемая структура каталогов

Чтобы не смешивать с текущими Playwright-тестами, выделить отдельную папку под WebDriver E2E:

```
desktop/
  e2e/                    # Playwright (Tier 1) — как сейчас
    nav.spec.js
  e2e-tests/               # WebdriverIO + tauri-driver (Tier 2)
    package.json
    wdio.conf.js
    specs/
      desktop-smoke.e2e.js
```

Корень запуска — `desktop/`, бинарник ожидается в `desktop/src-tauri/target/debug/voiceforge-desktop` (или `release`).

### 4.4. Инициализация WebdriverIO (когда слой реально внедряется)

**Шаг 1.** Создать каталог и package.json:

```bash
cd desktop
mkdir -p e2e-tests/specs
cd e2e-tests
npm init -y
```

В `package.json` добавить (или заменить scripts/dependencies):

```json
{
  "name": "voiceforge-desktop-e2e",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "wdio run wdio.conf.js",
    "test:headless": "xvfb-run wdio run wdio.conf.js"
  },
  "devDependencies": {
    "@wdio/cli": "^9",
    "@wdio/local-runner": "^9",
    "@wdio/mocha-framework": "^9",
    "@wdio/spec-reporter": "^9"
  }
}
```

Выполнить: `npm install`.

**Шаг 2.** Создать `wdio.conf.js` в `e2e-tests/`. Пример (ESM, путь к бинарнику — из `desktop/`):

```javascript
// e2e-tests/wdio.conf.js — запуск из desktop/e2e-tests/
import os from 'os';
import path from 'path';
import { spawn, spawnSync } from 'child_process';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const desktopDir = path.resolve(__dirname, '..');
const binaryPath = path.join(desktopDir, 'src-tauri', 'target', 'debug', 'voiceforge-desktop');

let tauriDriver;
let exit = false;

function closeTauriDriver() {
  exit = true;
  if (tauriDriver) {
    tauriDriver.kill();
    tauriDriver = null;
  }
}

export const config = {
  host: '127.0.0.1',
  port: 4444,
  specs: ['./specs/**/*.js'],
  maxInstances: 1,
  capabilities: [
    {
      maxInstances: 1,
      'tauri:options': {
        application: binaryPath,
      },
    },
  ],
  reporters: ['spec'],
  framework: 'mocha',
  mochaOpts: { ui: 'bdd', timeout: 60000 },

  onPrepare() {
    spawnSync('npm', ['run', 'tauri', 'build', '--', '--debug', '--no-bundle'], {
      cwd: desktopDir,
      stdio: 'inherit',
      shell: true,
    });
  },

  beforeSession() {
    const driverPath = path.join(os.homedir(), '.cargo', 'bin', 'tauri-driver');
    tauriDriver = spawn(driverPath, [], { stdio: ['ignore', process.stdout, process.stderr] });
    tauriDriver.on('error', (err) => {
      console.error('tauri-driver error:', err);
      process.exit(1);
    });
    tauriDriver.on('exit', (code) => {
      if (!exit) {
        console.error('tauri-driver exited with code:', code);
        process.exit(1);
      }
    });
  },

  afterSession() {
    closeTauriDriver();
  },
};

['exit', 'SIGINT', 'SIGTERM', 'SIGHUP'].forEach((ev) => {
  process.on(ev, () => {
    closeTauriDriver();
    process.exit();
  });
});
```

Если бинарник уже собран (release), замените `target/debug` на `target/release` в `binaryPath`.

**Шаг 3.** Создать спек `specs/desktop-smoke.e2e.js` (те же селекторы, что в Playwright):

```javascript
// e2e-tests/specs/desktop-smoke.e2e.js
describe('VoiceForge Desktop (real window)', () => {
  it('shows main layout and sidebar', async () => {
    const sidebar = await $('#main-sidebar');
    await sidebar.waitForDisplayed({ timeout: 15000 });
    const content = await $('#main-content');
    await expect(content).toBeDisplayed();
  });

  it('can switch to Sessions tab', async () => {
    await $('[data-tab="sessions"]').click();
    const tab = await $('#tab-sessions');
    await tab.waitForDisplayed({ timeout: 5000 });
    await expect(tab).toHaveElementClassContaining('active');
  });
});
```

В WebdriverIO v8+ матчеры могут называться иначе (например `toHaveElementClass`); при необходимости сверьтесь с [документацией WebdriverIO](https://webdriver.io/docs/api). Дальше можно добавить проверки баннера демона, кнопки «Повторить», вкладок Costs и Settings по тому же принципу.

### 4.5. Запуск native smoke

**С демоном (рекомендуется для полного сценария):**

В одном терминале (в toolbox):

```bash
cd /path/to/voiceforge
uv run voiceforge daemon
```

В другом:

```bash
cd desktop/e2e-tests
npm test
```

Если дисплея нет (CI):

```bash
xvfb-run npm test
```

**Без демона** можно проверить только «холодный» старт: баннер о недоступности демона, кнопка «Повторить» — без проверки реальных вызовов D-Bus.

### 3.5. CI (опционально)

В GitHub Actions (или аналоге):

- Установить зависимости Tauri (как в [desktop-build-deps.md](desktop-build-deps.md)), плюс `webkit2gtk-driver` (или эквивалент для Ubuntu), `xvfb`.
- Установить Rust, `cargo install tauri-driver --locked`.
- Собрать приложение: `cd desktop && npm run tauri build -- --debug --no-bundle` (или release).
- Установить зависимости e2e-tests: `cd desktop/e2e-tests && npm ci`.
- Запуск: `xvfb-run npm test` в `desktop/e2e-tests`.
- Демон в CI можно не поднимать, если достаточно smoke «окно открылось, UI виден»; для проверки D-Bus нужен запуск `voiceforge daemon` (например в фоне) перед тестами.

---

## 4. Порядок шагов при внедрении (кратко)

1. **Оставить как есть:** Playwright (Tier 1) в `desktop/e2e/`, CI job `desktop-e2e` — без изменений.
2. **Добавить Tier 2:** создать `desktop/e2e-tests/`, настроить WebdriverIO и tauri-driver, один спек desktop-smoke (открытие окна, сайдбар, одна вкладка).
3. **Локально:** в toolbox установить tauri-driver и webkit2gtk-driver (или аналог), прогнать `npm test` в `e2e-tests` с запущенным демоном.
4. **CI:** при необходимости добавить job с xvfb и запуском Tier 2.
5. **Документация:** обновить этот runbook и [desktop-build-deps.md](desktop-build-deps.md) (раздел про тесты), добавить в [DOCS-INDEX.md](../DOCS-INDEX.md) ссылку на этот гайд.

---

## 5. A11y-аудит (репорт без ручного тыкания)

- **Уже в CI:** pa11y по `http://localhost:4173` (preview) — см. workflow.
- **В тестах Playwright:** можно вызывать axe-core (например `@axe-core/playwright`), собирать нарушения и падать при критичных — получится автоматический a11y-репорт на каждый прогон Tier 1.
- **Для реального окна (Tier 2):** после открытия окна через WebdriverIO выполнить скрипт axe в контексте страницы и вернуть результат в тест — тогда репорт будет и по настоящему десктоп-окну.

---

## 6. Ручной чек-лист перед релизом

Имеет смысл завести короткий чек-лист в runbook релиза (например [release-and-quality.md](release-and-quality.md)):

- [ ] Приложение запускается (бинарник из bundle или установленный пакет).
- [ ] При запущенном демоне: главное окно, без баннера «Демон недоступен».
- [ ] Вкладки: Home, Sessions, Costs, Settings — переключаются, контент виден.
- [ ] Home: кнопки «Запись» и «Анализ 60 сек» кликабельны (при наличии демона).
- [ ] Settings: смена языка (ru/en) отражается в интерфейсе.
- [ ] Sessions: список сессий (или пустое состояние), поиск/фильтры без падений.
- [ ] Costs: отображение периода, кнопка экспорта.
- [ ] При выключенном демоне: баннер и кнопка «Повторить» работают.

Часть пунктов со временем можно заменить или дублировать автоматическими тестами Tier 2.

---

## 7. Ссылки

- [Tauri — Tests](https://v2.tauri.app/develop/tests/)
- [Tauri — WebDriver](https://v2.tauri.app/develop/tests/webdriver/)
- [Tauri — WebdriverIO example](https://v2.tauri.app/develop/tests/webdriver/example/webdriverio/)
- [Tauri — WebDriver CI](https://v2.tauri.app/develop/tests/webdriver/ci/)
- [desktop-build-deps.md](desktop-build-deps.md) — сборка и зависимости Tauri
- [test-operations.md](test-operations.md) — pytest, coverage, OOM

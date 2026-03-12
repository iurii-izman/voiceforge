# VoiceForge Desktop (Tauri)

Десктопный UI для VoiceForge: **Tauri 2** + D-Bus-клиент к демону `com.voiceforge.App`.

## Требования

- Демон должен быть запущен: `voiceforge daemon`
- Сборка: Rust, Node.js (npm/pnpm), системные пакеты для Tauri (см. [docs/runbooks/desktop-build-deps.md](../docs/runbooks/desktop-build-deps.md))

Проверка окружения из корня репо:

```bash
./scripts/check-desktop-deps.sh
```

## Сборка и запуск

```bash
cd desktop
npm install
npm run tauri dev    # разработка (запускает Vite + окно)
npm run tauri build  # релизный бинарник в src-tauri/target/release/bundle/
```

При старте приложение проверяет доступность демона (Ping). Если демон не запущен — показывается сообщение и кнопка «Повторить».

## Контракт D-Bus

Интерфейс: `com.voiceforge.App`, путь: `/com/voiceforge/App`.
Методы, используемые в каркасе: `Ping`, `GetSettings`, `GetSessions(limit)`.
Формат ответов при `VOICEFORGE_IPC_ENVELOPE=1`: envelope `{ "schema_version", "ok", "data" }`, данные в `data.settings` / `data.sessions`.

Подробнее: [docs/runbooks/config-env-contract.md](../docs/runbooks/config-env-contract.md), [docs/adr/0004-desktop-tauri-dbus.md](../docs/adr/0004-desktop-tauri-dbus.md).

## Иконка и качество (альфа2)

- Иконка приложения: в альфа2 можно не задавать (bundle.icon пустой); для релиза — добавить в `src-tauri/icons/` и обновить `tauri.conf.json` (или `tauri icon`).
- Для релизного quality signal больше не полагаться только на ручное “потыкать UI”: использовать desktop QA autopilot ниже.

## Desktop QA Autopilot

Стек без платных сервисов:

- `Playwright` для пользовательских сценариев и HTML/trace reports
- `window.__VOICEFORGE_TEST_HOOKS__` bridge для детерминированных mock-Tauri/mock-daemon flows
- `@axe-core/playwright` для a11y smoke на ключевых экранах
- `toHaveScreenshot()` для visual regression на базовых desktop states

Запуск:

```bash
cd desktop
npm ci
npm run e2e:gate
npm run e2e:release-gate
npm run e2e:native:headless
npm run e2e:native
npm run e2e:ui
npm run e2e:update-snapshots
npm run e2e:report
```

Минимальная policy:

- обязательный бесплатный regression gate для каждой итерации: `npm run e2e:gate`
- канонический blocking desktop UI gate: `npm run e2e:release-gate` (пересобирает свежий `dist` перед тестами)
- канонический advisory native smoke: `npm run e2e:native:headless`
- headed native smoke остаётся отдельной локальной проверкой: `npm run e2e:native`

Что покрывается:

- functional/autopilot flows: daemon ok, listen/analyze, sessions/detail, settings/autostart/updater
- stateful regression matrix: onboarding persistence, compact/full recovery, recent-session open/back, settings persistence, daemon retry recovery
- a11y smoke: home, sessions, settings panel
- visual baselines: home dashboard, sessions list, settings slide-out panel

Артефакты:

- `desktop/playwright-report/` — HTML report
- `desktop/test-results/` — JUnit + trace/video/screenshot artifacts on failure

Ограничения:

- этот слой тестирует реальный frontend и mocked Tauri runtime, но не заменяет отдельные native-shell smoke tests для tray, updater install, глобальных hotkeys, notifications UX и Wayland/X11 quirks
- native-shell smoke вынесен отдельно: `npm run e2e:native:headless` (если `WebKitWebDriver` не находится автоматически, задать `TAURI_NATIVE_DRIVER=/path/to/WebKitWebDriver`; артефакты пишутся в `desktop/e2e-native/artifacts/`; см. `docs/runbooks/desktop-gui-testing.md` и `docs/runbooks/desktop-release-gate-matrix.md`)

## После альфа2

- Подписка на D-Bus-сигналы (ListenStateChanged, AnalysisDone, TranscriptUpdated) вместо опроса.
- Перенос экспорта в демон (D-Bus метод ExportSession) при желании убрать вызов CLI из десктопа.
- Системный трей с «Старт/стоп записи»; уведомления при завершении анализа.

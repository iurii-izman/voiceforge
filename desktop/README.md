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
- E2E-тесты десктопа в альфа2 опциональны; достаточно ручной проверки и стабильного контракта D-Bus.

## После альфа2

- Подписка на D-Bus-сигналы (ListenStateChanged, AnalysisDone, TranscriptUpdated) вместо опроса.
- Перенос экспорта в демон (D-Bus метод ExportSession) при желании убрать вызов CLI из десктопа.
- Системный трей с «Старт/стоп записи»; уведомления при завершении анализа.

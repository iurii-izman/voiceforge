# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-24

**Последняя итерация:** десктоп по плану `docs/desktop-tauri-implementation-plan.md`: блоки 1–8. Архитектура (ADR-0004), окружение (desktop-build-deps.md, check-desktop-deps.sh), каркас Tauri в `desktop/`, UI (Главная, Сессии, Затраты, Настройки), D-Bus-методы и envelope, сборка/релиз-доки, альфа2-чеклист, качество и следующие шаги.

---

## Сверка плана развития (development-plan-post-audit-2026.md)

Без изменений: Часть I и II по-прежнему реализованы. Десктоп — отдельный план (desktop-tauri-implementation-plan.md), выполнен в рамках альфа2.

---

## Рекомендательные приоритетные задачи (что делать дальше)

1. **Сборка десктопа в окружении с зависимостями:** в toolbox с установленными webkit2gtk4.1-devel, gtk3-devel выполнить `cd desktop && npm run build && cargo tauri build`; при необходимости добавить иконку в `src-tauri/icons/` (bundle.icon).
2. **Подписка на D-Bus-сигналы** (ListenStateChanged, AnalysisDone) в десктопе — опционально, вместо опроса; документировано в desktop/DBUS.md.
3. **Flatpak для альфа2:** при желании добавить манифест в `desktop/flatpak/` и шаг в release runbook.
4. **Версия 0.2.0a1:** при релизе альфа2 согласовать pyproject.toml с тегом v0.2.0-alpha.1; чеклист в docs/runbooks/alpha2-checklist.md.
5. **Контракт D-Bus:** при изменении методов/сигналов обновлять desktop/DBUS.md и config-env-contract.md.

---

## Важные/критические проблемы на следующую итерацию

1. **Сборка без cc/webkit:** в среде без линкера и GTK/WebKit десктоп не соберётся; сборка только в toolbox/окружении с зависимостями из desktop-build-deps.md.
2. **Экспорт из десктопа:** вызывает CLI `voiceforge export`; для альфа2 достаточно; позже можно перенести в демон (D-Bus ExportSession).
3. **Контракт:** при изменении D-Bus обновлять config-env-contract.md и при необходимости test_dbus_contract_snapshot.
4. **ADR-0001:** новые команды CLI — только через ADR.

---

## Общий совет

Десктоп — единственный UI, работающий через D-Bus; браузерное UI опционально. Все новые фичи для пользователя сначала в Tauri (D-Bus), при необходимости — в web.

# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-24

**Последняя итерация:** приведение в порядок DOCS: единый вход docs/README.md (навигация по разделам), runbooks/README.md и adr/README.md по смыслу; дубли в voiceforge-cursor-tz убраны (стартовый промпт → ссылка на agent-context); промпты «Продолжить план развития» перенесены в voiceforge-cursor-tz, файл prompt-implement-development-plan.md удалён; architecture/README уточнён (runtime flow в overview).

---

## Сверка плана развития (development-plan-post-audit-2026.md)

- **Часть I (все 10 пунктов)** и **блоки Alpha2 A–D** (Tauri, D-Bus, UI, streaming CLI) — реализованы. Детальная сверка: `docs/runbooks/claude-proposal-alignment.md`.
- **Часть II:** W1, W2, W3, W4, W7, W8, W9 закрыты; остаются W5 (retry LLM), W6 (i18n), W10 (coverage).
- **Часть III** в development-plan: приоритеты на ближайшее время (релиз Alpha2, сборка десктопа, pyannote, W5, сигналы, Flatpak, E2E).

---

## Рекомендательные приоритетные задачи (что делать дальше)

1. **Релиз Alpha2 (Блок F):** версия 0.2.0a1 в pyproject.toml, тег v0.2.0-alpha.1, alpha2-checklist.md, CHANGELOG, release runbook.
2. **Сборка десктопа в toolbox:** `./scripts/check-desktop-deps.sh` → `cd desktop && npm run build && cargo tauri build`; иконка при необходимости.
3. **Согласовать версию pyannote:** в коде 4.0.4, в архитектуре — 3.3.2 (риск OOM). Решить: зафиксировать в доке или откатить зависимость.
4. **Подписка на D-Bus-сигналы** в десктопе (ListenStateChanged, AnalysisDone) — опционально; Flatpak и E2E — по желанию после стабильной сборки.
5. **Контракт D-Bus:** при изменении методов/сигналов обновлять desktop/DBUS.md и config-env-contract.md.

---

## Важные/критические проблемы на следующую итерацию

1. **Версия pyannote:** в pyproject.toml и uv.lock — 4.0.4; в архитектуре и ТЗ Claude — строго 3.3.2 (4.x = OOM). Нужно согласовать и либо обновить доки, либо откатить зависимость.
2. **Сборка без cc/webkit:** десктоп собирается только в toolbox/окружении с зависимостями из desktop-build-deps.md.
3. **Экспорт из десктопа:** через CLI `voiceforge export`; для альфа2 достаточно; позже — ExportSession в D-Bus.
4. **ADR-0001:** новые команды CLI — только через ADR.

---

## Общий совет

Предложение Claude совпадает с нашей философией и ограничениями; план скорректирован без изменения архитектуры. Десктоп — основной UI через D-Bus; браузерное UI опционально. Следующий шаг — закрыть релиз Alpha2 и согласовать версию pyannote.

# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-24

**Последняя итерация:** Сверка roadmap 1–8 по коду — все пункты закрыты (без доработки кода). Обновлён фокус: приоритет следующий блок 9–12 (стриминг/live summary уже в коде; PII/Web UI) или стабилизация/доки.

---

## Roadmap 1–8: статус (сверка по коду)

| # | Направление | Статус |
|---|-------------|--------|
| 1 | Шаблоны встреч в `analyze` | ✓ `--template`, D-Bus, daemon, web |
| 2 | Обновление статусов action items по следующей встрече | ✓ `action-items update`, БД, Web API |
| 3 | Экспорт сессии (Markdown/PDF) | ✓ `export --format md/pdf`, e2e в test_cli_e2e_smoke |
| 4 | Выбор модели Ollama в конфиге | ✓ `ollama_model` в config, router, config-env-contract |
| 5 | Документация «Первая встреча за 5 минут» | ✓ `docs/first-meeting-5min.md` |
| 6 | Отчёты по затратам (cost report) | ✓ `cost --days/--from/--to`, GetAnalytics, API |
| 7 | Явный язык для STT | ✓ `language` в config, `language_hint` в Whisper (main, daemon, pipeline) |
| 8 | Расширенные e2e-тесты | ✓ export, analyze --template, action-items update, history --output md в test_cli_e2e_smoke.py |

Дублировать реализацию не нужно.

---

## Сверка плана развития (development-plan-post-audit-2026.md)

- **Часть I (все 10 пунктов)** и **блоки Alpha2 A–D** (Tauri, D-Bus, UI, streaming CLI) — реализованы. Детальная сверка: `docs/runbooks/claude-proposal-alignment.md`.
- **Часть II:** W1–W10 закрыты.
- **Часть III:** релиз Alpha2 выполнен; сборка в toolbox описана в desktop-build-deps.md.

---

## Рекомендательные приоритетные задачи (что делать дальше)

1. **Roadmap 9–10:** стриминг STT и live summary уже в коде (`--stream`/`streaming_stt`, `--live-summary`); при необходимости — доработка UX или тесты.
2. **Roadmap 11–12:** PII (уже есть pii_mode), простой Web UI (уже есть в web/server.py) — приоритет по желанию.
3. **Сборка десктопа в toolbox:** см. `desktop-build-deps.md` (полная последовательность).
4. **Согласовать версию pyannote:** 4.0.4 в коде; при OOM — зафиксировать в доке или откатить на 3.3.2.
5. **Контракт D-Bus:** при изменении методов/сигналов обновлять desktop/DBUS.md и config-env-contract.md.
6. **Flatpak / e2e десктопа:** по желанию после стабильной сборки.

---

## Важные/критические проблемы на следующую итерацию

1. **Версия pyannote:** 4.0.4; при падениях/OOM — пересмотреть (доки или откат до 3.3.2).
2. **Сборка без cc/webkit:** десктоп только в toolbox/окружении из desktop-build-deps.md.
3. **Экспорт из десктопа:** пока через CLI `voiceforge export`; позже — ExportSession в D-Bus при необходимости.
4. **ADR-0001:** новые команды CLI — только через ADR.

---

## Общий совет

Roadmap 1–8 закрыты по коду и тестам. Следующий логичный блок — 9–12 (улучшение стриминг/live summary, PII, Web UI) или фокус на стабилизацию и документацию (installation-guide, first-meeting-5min уже есть). Десктоп — основной UI через D-Bus; один вход для установки: [installation-guide.md](installation-guide.md).

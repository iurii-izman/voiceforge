# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-23

**Последняя итерация:** расширенные e2e (#8), cost report e2e (cost --from/--to), PII UX (#11 — pii_mode в status), локализация e2e (VOICEFORGE_LANGUAGE=ru в тестах с русским выводом), config-env-contract и CHANGELOG.

---

## Сверка плана развития (development-plan-post-audit-2026.md)

**Часть I (1–10):** все пункты реализованы в коде (--template, export, status --detailed, history --search/--date/--from/--to/--action-items/--output md, quickstart, GetAnalytics, status --doctor, action-items update, миграция 005).

**Часть II:** W1–W3, W8 реализованы. **W4** — в config-env-contract задокументировано: GetSettings возвращает `privacy_mode` как алиас `pii_mode`. **W6** — оставшиеся строки в main.py переведены на i18n t(key). W5, W7, W9 закрыты ранее. W10 — по мере доработок дополнять тестами.

---

## Рекомендательные приоритетные задачи (что делать дальше)

1. **Roadmap #10** — Live summary: закрыто. Интервал в конфиге; при включении `listen --live-summary` сообщение показывает настроенный интервал (i18n `{interval}`). Дальше по желанию — вывод саммари в отдельный поток/файл.
2. **Roadmap #9** — Стриминг STT: добавлен unit-тест `test_streaming_transcriber_passes_language_to_transcribe`; при доработках — дополнять тестами.
3. **Roadmap #7** — Явный язык для STT: реализован (language → Whisper hint в CLI и daemon), задокументирован в CHANGELOG и config-env-contract.
4. **Покрытие (W10):** при доработках daemon/smart_trigger/streaming дополнять unit-тестами.
5. **Локализация e2e:** закрыто — в тестах index/watch, export md, history md задаётся `VOICEFORGE_LANGUAGE=ru` для стабильных проверок.

---

## Важные/критические проблемы на следующую итерацию

1. **Покрытие:** daemon/smart_trigger/streaming — при добавлении фич дополнять тестами.
2. **ADR-0001:** новые команды — только через ADR; флаги к существующим — допустимы.
3. **Контракт:** при изменении D-Bus/API обновлять config-env-contract.md и при необходимости test_dbus_contract_snapshot.

---

## Общий совет

Перед реализацией пункта из плана развития сверять его с текущим кодом (grep по ключевым словам): многое уже сделано, чтобы не дублировать и не тратить бюджет на закрытые задачи.

# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-02-24

---

## Следующий шаг (для копирования в новый чат)

Один конкретный шаг для следующего чата (или пользователь подставляет свою задачу).

- **Сейчас:** Реализован CalDAV опрос (issue #26): `voiceforge calendar poll`, keyring `caldav_url` / `caldav_username` / `caldav_password`, опциональная зависимость `calendar`. Следующий шаг: взять задачу с доски — **#27 AppImage** (полная сборка в toolbox) или **#28 EN runbook** (dependabot-review / telegram-bot-setup).

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Последняя итерация (кратко)

Roadmap 17 (CalDAV): подкоманда `voiceforge calendar poll`, модуль `voiceforge.calendar.caldav_poll`, ключи в keyring-keys-reference.md, опция `uv sync --extra calendar`. Тесты 45 passed. Closes #26.

---

## Что сделано (история)

**Всё закрытое вынесено в один документ со сверкой по коду:** [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Там: Roadmap 1–12, план развития Часть I и блоки Alpha2 A–D, W1–W10, Sonar, «Следующие 10 шагов» (п.1–6). В текущем файле ниже — только **не сделанное** и план.

---

## Не сделано / открытые задачи

| Приоритет | Задача | Заметка |
|-----------|--------|--------|
| Roadmap 14 | Офлайн-пакет (Flatpak/AppImage) | Черновик offline-package.md; appimage в bundle.targets; полная сборка в toolbox не проверена. |
| Roadmap 16 | Бот Telegram/Slack | Telegram: ADR-0005, webhook, /start /status — сделано; Slack/расширение — по желанию. |
| Roadmap 17 | Интеграция с календарём | CalDAV: исследование в calendar-integration.md, ADR-0006; кода нет. |
| Roadmap 18 | RAG: ODT/RTF | Парсеры и индекс — по rag-formats.md; при добавлении — тесты. |
| Roadmap 19–20 | Prompt caching, macOS/WSL2 | По необходимости. |
| Операционно | Dependabot 1 moderate | Закрыть вручную в GitHub (dismiss Accept risk) — dependabot-review.md. |
| Операционно | Перевод runbook на EN | Частично (quickstart, bootstrap, installation-guide, first-meeting-5min, desktop-build-deps); остальные по желанию. |

---

## Следующие шаги (план)

1. **Выбрать направление:** CalDAV (roadmap 17), ещё EN-runbook, сборка AppImage в toolbox, или RAG ODT/RTF.
2. **CalDAV:** реализация опроса по calendar-integration.md и ADR-0006 (keyring caldav_*, подкоманда или daemon).
3. **AppImage:** полная сборка в toolbox (`./scripts/setup-desktop-toolbox.sh` → `cargo tauri build`), проверка артефакта в `target/release/bundle/`.
4. **Стабилизация:** при изменении CLI/конфига обновлять installation-guide, first-meeting-5min; обновлять DOCS-INDEX при новых доках.

---

## Актуальные напоминания

- **Sonar:** список открытых issues — `uv run python scripts/sonar_fetch_issues.py`. Закрытые S1192, S3626, S3358, S7785, S3776 — в [history](../history/closed-plans-and-roadmap.md).
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — сборка только в toolbox/окружении из [desktop-build-deps.md](desktop-build-deps.md). Новые CLI-команды — только через ADR (ADR-0001).

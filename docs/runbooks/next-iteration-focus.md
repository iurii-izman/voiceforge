# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-02-24

---

## Следующий шаг (для копирования в новый чат)

Один конкретный шаг для следующего чата (или пользователь подставляет свою задачу).

- **Сейчас:** Добавлен runbook [desktop-build-deps-en.md](desktop-build-deps-en.md), DOCS-INDEX обновлён. Следующий шаг на выбор: **CalDAV** по calendar-integration.md и ADR-0006; **ещё runbook на EN** (например dependabot-review, telegram-bot-setup); **сборка AppImage в toolbox**; или другая задача из roadmap. При новом чате — универсальный промпт из agent-context + задача или «продолжить с @docs/runbooks/next-iteration-focus.md».

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Последняя итерация (кратко)

Перевод runbook на EN: добавлен desktop-build-deps-en.md, DOCS-INDEX обновлён. Тесты 44 passed; коммит и пуш выполнены.

---

## План на следующие 4 блока (недоделанное + критичное)

Составлен по анализу next-iteration-focus, roadmap-priority, development-plan и кода.

| Блок | Название | Содержание | Критичность |
|------|----------|------------|-------------|
| **1** | **Sonar S3776 — добить** | ~~Оставшиеся 4 места~~ — сделано: main (history), web/server (do_GET/do_POST), core/metrics, llm/router. | Закрыто. |
| **2** | **Стабилизация и документация** | installation-guide и first-meeting-5min обновлены (doctor); Dependabot (1 moderate) — проверить вручную в GitHub; при необходимости — перевод ключевых runbook на английский. | Частично: доки обновлены. |
| **3** | **Качество и консистентность** | installation-guide → pyannote-version; desktop-build-deps → pyannote при OOM. При необходимости — дописать e2e/дымовые; D-Bus без доп. работ. | Частично: перекрёстные ссылки добавлены. |
| **4** | **Следующий продуктовый шаг** | Один из пунктов roadmap 16–18 или стабилизация 14: **Бот (Telegram/Slack)** — ADR + черновик архитектуры; **Календарь** — исследование CalDAV/триггер «встреча началась»; **RAG (ODT/RTF)** — поддержка в индексаторе; **Офлайн-пакет** — продвинуть offline-package.md (Flatpak/AppImage). Выбор по приоритету команды. | По желанию: расширение сценариев. |

**Порядок выполнения:** 1 → 2 → 3 → 4 (либо 2 раньше 1, если важнее доки и безопасность).

---

## Следующие 3 блока (план продолжения)

После закрытия блоков 1–3 и частичного блока 4 — логичное продолжение в три итерации.

| Блок | Название | Содержание | Результат |
|------|----------|------------|-----------|
| **A** | **Завершение стабилизации** | Сделано: runbook [dependabot-review.md](dependabot-review.md), дымовой тест GET /api/cost в test_web_smoke. Остаётся: закрыть Dependabot вручную в GitHub; опционально — перевод runbook на EN. | Частично: доки и тесты готовы. |
| **B** | **Выбор и старт продуктового шага** | Сделано: **Telegram (ТГ)** — [ADR-0005](../adr/0005-telegram-bot.md), ключ keyring `webhook_telegram`. | Закрыто для бота. |
| **C** | **Минимум по выбранному направлению** | Сделано: **Бот** — webhook `POST /api/telegram/webhook`, команды `/start`, `/status`; runbook [telegram-bot-setup.md](telegram-bot-setup.md); тест 503 без ключа. | Минимум бота готов. |

**Порядок:** A → B → C. Блок A можно сократить до одного пункта (Dependabot), если остальное отложить. Блок B задаёт направление; блок C — первый инкремент по нему.

---

## Блоки Sonar (актуально)

Список: `uv run python scripts/sonar_fetch_issues.py`.

**Закрыто:** S1192, S3626, S3358, S7785 (NOSONAR), все S3776 (server _telegram_webhook_reply, _read_post_json; main live summary/cost/history; history_helpers _format_analysis_*; core/metrics _unpack_llm_row). После пушa проверить Sonar: `uv run python scripts/sonar_fetch_issues.py`.

---

## Roadmap 1–12: статус (сверка по коду)

| # | Направление | Статус |
|---|-------------|--------|
| 1 | Шаблоны встреч в `analyze` | ✓ `--template`, D-Bus, daemon, web |
| 2 | Обновление статусов action items по следующей встрече | ✓ `action-items update`, БД, Web API |
| 3 | Экспорт сессии (Markdown/PDF) | ✓ `export --format md/pdf`, e2e в test_cli_e2e_smoke |
| 4 | Выбор модели Ollama в конфиге | ✓ `ollama_model` в config, router, config-env-contract |
| 5 | Документация «Первая встреча за 5 минут» | ✓ `docs/first-meeting-5min.md` |
| 6 | Отчёты по затратам (cost report) | ✓ `cost --days/--from/--to`, GetAnalytics, API |
| 7 | Явный язык для STT | ✓ `language` в config, `language_hint` в Whisper |
| 8 | Расширенные e2e-тесты | ✓ export, analyze --template, action-items, history --output md |
| 9 | Стриминговый STT в CLI (listen) | ✓ `--stream`/`streaming_stt`, e2e test_cli_listen_stream_smoke |
| 10 | Live summary во время listen | ✓ `--live-summary`, e2e test_cli_listen_live_summary_smoke |
| 11 | Управление PII (вкл/выкл, только email) | ✓ `pii_mode` OFF/ON/EMAIL_ONLY в config и status |
| 12 | Простой локальный Web UI | ✓ web/server.py: статус, сессии, затраты, action-items, экспорт |

Дублировать реализацию не нужно.

---

## Следующие 10 шагов по реализации проекта

1. ~~**Стабилизация сборки десктопа (roadmap 13)**~~ — сделано: `desktop-build-deps.md` (pkg-config, воспроизводимая последовательность).
2. ~~**Экспорт сессии из десктопа**~~ — реализован: Tauri `export_session` вызывает CLI `voiceforge export`; кнопки в UI есть.
3. ~~**Офлайн-пакет (roadmap 14)**~~ — черновик: `docs/runbooks/offline-package.md` (Flatpak/AppImage, этапы).
4. ~~**Согласовать версию pyannote**~~ — сделано: `docs/runbooks/pyannote-version.md` (4.0.4, откат 3.3.2 при OOM).
5. ~~**Контракт D-Bus**~~ — сделано: в `config-env-contract.md` ссылка на `desktop/DBUS.md`; при изменениях обновлять оба.
6. ~~**Smart trigger по умолчанию (roadmap 15)**~~ — политика зафиксирована: default остаётся `false` до сбора отзывов; при включении по умолчанию — обновить config и `config-env-contract.md` (см. описание `smart_trigger`).
7. **Бот Telegram/Slack (roadmap 16)** — приоритет по желанию: ADR + черновик архитектуры (webhook, команды, интеграция с демоном/CLI).
8. **Интеграция с календарём (roadmap 17)** — исследование: CalDAV/Google Calendar, триггер «встреча началась» для listen/analyze; описать в runbook или ADR.
9. **RAG: новые форматы (roadmap 18)** — постепенно: поддержка ODT/RTF в индексаторе; при добавлении — тесты и обновление доков.
10. **Стабилизация и документация** — обновить `installation-guide.md` и `first-meeting-5min.md` при изменении CLI/конфига; рассмотреть перевод ключевых runbook на английский; при необходимости — prompt caching (roadmap 19), macOS/WSL2 (roadmap 20).

---

## Сверка плана развития (development-plan-post-audit-2026.md)

- **Часть I (все 10 пунктов)** и **блоки Alpha2 A–D** (Tauri, D-Bus, UI, streaming CLI) — реализованы. Детальная сверка: `docs/runbooks/claude-proposal-alignment.md`.
- **Часть II:** W1–W10 закрыты.
- **Часть III:** релиз Alpha2 выполнен; сборка в toolbox описана в desktop-build-deps.md.

---

## Рекомендательные приоритетные задачи (что делать дальше)

- Перевод 1–2 runbook на английский (installation-guide, first-meeting-5min) — по желанию.
- Roadmap 17 (календарь), 18 (RAG ODT/RTF), 14 (офлайн-пакет) — выбор следующего продуктового шага.
- Dependabot: при желании закрыть алерт CVE-2025-69872 вручную (dismiss Accept risk) — см. dependabot-review.md.
- Индекс документации: при добавлении/изменении доков обновлять `docs/DOCS-INDEX.md`.

---

## Важные/критические проблемы на следующую итерацию

1. **Версия pyannote:** 4.0.4; при падениях/OOM — см. `docs/runbooks/pyannote-version.md` (откат до 3.3.2 и шаги).
2. **Сборка без cc/webkit:** десктоп только в toolbox/окружении из desktop-build-deps.md.
3. **Экспорт из десктопа:** пока через CLI `voiceforge export`; позже — ExportSession в D-Bus при необходимости.
4. **ADR-0001:** новые команды CLI — только через ADR.

---

## Общий совет

Roadmap 1–12 закрыты по коду и тестам (e2e для 9–10 добавлены). Дальше — «Следующие 10 шагов» (roadmap 13–20 + стабилизация). Десктоп — основной UI через D-Bus; один вход для установки: [installation-guide.md](installation-guide.md).

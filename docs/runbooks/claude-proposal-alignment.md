# Сверка предложения Claude с проектом VoiceForge

Документ сравнивает материалы от Claude (`docs/architecture/voiceforge-arch.jsx`, `docs/runbooks/voiceforge-cursor-tz.md`) с нашими условиями, ограничениями, философией и текущим состоянием кода. Используется для корректировки плана развития.

**Дата сверки:** 2026-02-24.

---

## 1. Соответствие условиям и ограничениям

| Аспект | Предложение Claude | Наш проект | Совпадение |
|--------|--------------------|------------|------------|
| **Стек** | Python 3.12, uv, faster-whisper, pyannote **3.3.2**, SQLite-vec, LiteLLM, PipeWire, D-Bus, Tauri 2 | То же; в `pyproject.toml` указан **pyannote.audio==4.0.4** | ⚠️ Расхождение по версии pyannote (см. ниже) |
| **Ключи** | keyring, сервис voiceforge, не .env в git | config-env-contract.md, cost-and-environment.mdc | ✓ |
| **Среда** | Fedora Atomic Cosmic, toolbox, 8 GB RAM, swap NVMe | agent-context, desktop-build-deps | ✓ |
| **CLI** | 9 core + флаги, ADR-0001 для новых команд | Зафиксировано в ADR-0001 | ✓ |
| **Демон** | com.voiceforge.App, envelope {schema_version, ok, data} | dbus_service: default True для envelope | ✓ |
| **Десктоп** | Tauri → только D-Bus, без HTTP внутри; web опционален | desktop-tauri-implementation-plan, ADR-0004 | ✓ |
| **Критичные ограничения** | pyannote 3.3.2, STT→diarize последовательно, не ChromaDB, RAM ≤5.5 ГБ, сборка в toolbox | Те же в архитектуре и runbooks | ✓ (при версии pyannote — см. ниже) |
| **Стиль кода** | type hints, structlog, 300 строк/файл, ruff, pytest | development-plan, agent-context | ✓ |

**Вывод:** Философия и архитектура совпадают. Единственное существенное расхождение — версия pyannote (в коде 4.0.4, в описании Claude — строго 3.3.2 из-за RAM). Нужно либо зафиксировать в доке «текущая 4.0.4, при OOM — откат на 3.3.2», либо явно откатить зависимость на 3.3.2.

---

## 2. Что уже реализовано (проверено по коду)

Ниже — сверка пунктов из voiceforge-cursor-tz.md и development-plan-post-audit-2026.md с репозиторием.

### Часть I плана развития (аудит)

| # | Пункт | Статус в коде |
|---|--------|----------------|
| 1 | `analyze --template` | ✓ Реализовано (standup, sprint_review, one_on_one, brainstorm, interview) |
| 2 | Streaming STT в CLI `listen` | ✓ `--stream` / `streaming_stt`, `_streaming_listen_worker` в main.py |
| 3 | export / history --format md | ✓ Команда `export`, форматы md/pdf |
| 4 | `status --detailed` | ✓ get_status_detailed_* в status_helpers, budget из cfg |
| 5 | `history --search` | ✓ Реализовано |
| 6 | Action items DB + cross-session | ✓ Таблица, action-items update, history --action-items |
| 7 | `history --date`, `--from`/`--to` | ✓ Реализовано |
| 8 | Quickstart / первая встреча за 5 мин | ✓ Документация в runbooks |
| 9 | GetAnalytics D-Bus | ✓ get_stats/get_stats_range, данные в демоне |
| 10 | doctor как `status --doctor` | ✓ Реализовано |

### Блоки Alpha2 (voiceforge-cursor-tz.md)

| Блок | Содержание | Статус |
|------|------------|--------|
| A | Каркас Tauri (desktop/, Ping, GetSettings/GetSessions) | ✓ desktop/ есть, версия 0.2.0-alpha.1, сборка deb/rpm |
| B | D-Bus интеграция в Tauri (все методы, envelope) | ✓ DBUS.md, invoke-команды, envelope |
| C | UI: Главная, Сессии, Затраты, Настройки | ✓ По next-iteration-focus и desktop-tauri-implementation-plan |
| D | Streaming STT в CLI | ✓ См. пункт 2 выше |
| E | Фиксы W1–W8 | Частично (см. таблицу W ниже) |
| F | Релиз Alpha2 (версия, чеклист, CHANGELOG) | В работе: pyproject 0.1.0a1 → 0.2.0a1 при релизе |

### Слабые места (Часть II) — актуальный статус

| Код | Проблема | Статус |
|-----|----------|--------|
| W1 | budget_limit_usd не 75.0 хардкод | ✓ Берётся из Settings(), передаётся в status_helpers и cost |
| W2 | sample_rate 44.1→16 kHz ресэмплинг | ✓ В streaming.py и pipeline есть ресэмплинг / проверка |
| W3 | RAG transcript[:200] → 1000 | ✓ RAG_QUERY_MAX_CHARS = 1000 в pipeline.py |
| W4 | privacy_mode в GetSettings | ✓ В контракте: privacy_mode как alias pii_mode |
| W5 | Instructor retry при невалидном JSON | Проверить наличие retry в router |
| W6 | i18n в main.py | Частично (есть t(key) в ряде мест) |
| W7 | Envelope по умолчанию | ✓ _uses_ipc_envelope() default=True в dbus_service |
| W8 | Валидация Settings | ✓ field_validator для budget_limit_usd, sample_rate, и др. в config.py |
| W9 | cost_usd source of truth | ✓ Описано в config-env-contract.md (metrics.db vs transcripts.db) |
| W10 | Coverage рисковых модулей | Остаётся задачей (тесты с моками) |

---

## 3. Расхождение: pyannote.audio 3.3.2 vs 4.0.4

- В **документации** (архитектура, ТЗ Claude): «pyannote-audio **строго 3.3.2**», «4.x = 9.5 ГБ RAM = OOM».
- В **коде**: `pyproject.toml` и `uv.lock` — **pyannote.audio==4.0.4**.

**Рекомендация:** Либо (1) зафиксировать в архитектуре и плане: «сейчас 4.0.4; при OOM на 8 ГБ — откат на 3.3.2», либо (2) явно откатить зависимость на 3.3.2 и обновить код под неё. До решения — в плане развития указывать эту задачу как «согласовать версию pyannote с RAM-ограничением».

---

## 4. Как скорректировать план

- **Оставить как есть:** философия (local-first, D-Bus единственный бэкенд для Tauri), ограничения (RAM, keyring, toolbox), шаблоны промптов из voiceforge-cursor-tz.md.
- **Взять из предложения Claude:** разбивку Alpha2 по блокам A–F, фокус «после Alpha2» (стриминг, Flatpak, E2E, затем live summary, smart trigger, экспорт в демон, трей, уведомления).
- **Убрать/не дублировать:** пункты Части I и блоки A–D, уже реализованные (см. таблицы выше).
- **Добавить в план:** явную задачу по согласованию версии pyannote; оставшиеся пункты из Блока E (W5, W6, W10) и Блок F (релиз 0.2.0a1); приоритеты по roadmap-priority.md и по сложности/эффективности (см. следующий документ — обновлённый development-plan или раздел в нём).

Итоговый порядок работ: сначала релиз Alpha2 (версия, чеклист, сборка), затем по приоритету — оставшиеся W, подписка на D-Bus-сигналы в десктопе, Flatpak, E2E, затем «после Alpha2» из роадмапа.

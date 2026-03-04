# Планы и приоритеты (единый документ)

Объединённый обзор: приоритет фич (roadmap 1–20), что сделано, текущие задачи Phase A–D. Детальная история закрытых планов: [history/closed-plans-and-roadmap.md](history/closed-plans-and-roadmap.md). Архив планов: [archive/plans/](archive/plans/) (development-plan, desktop-tauri, claude-proposal-alignment).

---

## 1. Приоритет внедрения (roadmap 1–20)

| # | Направление | Рейтинг | Статус |
|---|-------------|--------|--------|
| 1 | Шаблоны встреч в `analyze` | 93 | Реализовано |
| 2 | Action items по следующей встрече | 90 | Реализовано |
| 3 | Экспорт сессии (Markdown/PDF) | 82 | Реализовано |
| 4 | Выбор модели Ollama в конфиге | 70 | Реализовано |
| 5 | Документация «Первая встреча за 5 минут» | 73 | Реализовано |
| 6 | Отчёты по затратам | 77 | Реализовано |
| 7 | Явный язык для STT | 81 | Реализовано |
| 8 | Расширенные e2e-тесты | 76 | Реализовано |
| 9 | Стриминговый STT в CLI (listen) | 84 | Реализовано |
| 10 | Live summary во время listen | 88 | Реализовано |
| 11 | Управление PII | 68 | Реализовано |
| 12 | Простой локальный Web UI | 74 | Реализовано |
| 13 | Десктопный UI (Tauri) | 95 | Реализовано |
| 14 | Офлайн-пакет (Flatpak/AppImage) | 85 | Черновик/скрипты |
| 15 | Smart trigger по умолчанию | 55 | Реализовано (default false) |
| 16 | Бот (Telegram) | 72 | Реализовано |
| 17 | Интеграция с календарём (CalDAV) | 78 | Реализовано |
| 18 | RAG: ODT, RTF | 62 | Реализовано |
| 19 | Prompt caching для не-Claude | 58 | Не реализовано (research) |
| 20 | macOS / WSL2 | 65 | Не реализовано (#50) |

---

## 2. Что сделано (кратко)

- **Roadmap 1–18:** в коде (см. [history/closed-plans-and-roadmap.md](history/closed-plans-and-roadmap.md)).
- **План развития (development-plan) Часть I:** все 10 пунктов реализованы (--template, streaming listen, export, status --detailed, history --search, action items DB, history --date/--from/--to, quickstart, GetAnalytics, status --doctor).
- **Issues #32–49, #51–53:** закрыты. **#50** (macOS/WSL2) открыт.
- **Аудит Phase A–D:** большинство W1–W20 в статусе «СДЕЛАНО»; см. [audit/audit.md](audit/audit.md).

---

## 3. Текущие задачи (Phase A–D)

Источник правды: [audit/audit.md](audit/audit.md).

- **В работе / частично:** #56 (coverage, fail_under 70→80), #65 (CVE), #66 (async web — опционально полный путь), W17 (S3776).
- **Phase D (бэклог):** #70 A/B testing, #71 OTel, #72 plugins, #50 macOS/WSL2, #73 packaging GA.

Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1). Фокус итерации: [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md).

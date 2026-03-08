# Agent context (VoiceForge)

Единый контекст для Cursor-агента. Новый чат: приложи этот файл (@docs/runbooks/agent-context.md) — не ищи по проекту, работай по этому документу. Для продолжения — @docs/runbooks/next-iteration-focus.md (обновляет агент в конце сессии).

**Индекс документации (актуальность):** `docs/DOCS-INDEX.md`. **Порядок в доках (архив, источники правды):** [doc-governance.md](doc-governance.md). **Автопилот конца сессии:** `.cursor/rules/agent-session-handoff.mdc` (копия в репо: [agent-session-handoff-rule.md](agent-session-handoff-rule.md)). **Max-autopilot и batching:** [cursor.md](cursor.md), [planning.md](planning.md), [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md).

---

## Проект

**VoiceForge** — локальный ассистент для аудио-встреч на Linux: PipeWire → STT → diarization → RAG → LLM. Alpha 0.2, 19 CLI-команд (`voiceforge --help`: version, listen, analyze, index, watch, rag-export, daemon, install-service, uninstall-service, cost, status, sessions-to-ical, weekly-report, export, backup, history, web, action-items, calendar).

---

## Правила и окружение

- **Правила**: `.cursor/rules/cost-and-environment.mdc` — эффективность, точечный поиск, без лишних шагов.
- **Ключи и доступы — только keyring:** сервис `voiceforge`, имена: `anthropic`, `openai`, `huggingface`, `webhook_telegram`, `sonar_token`, `github_token` и др. Полный список: `docs/runbooks/keyring-keys-reference.md`. Не хардкодить, не коммитить; в облаке без keyring — Cursor My Secrets.
- **Конфиг:** `docs/runbooks/config-env-contract.md` — VOICEFORGE_*, Settings, D-Bus.
- **Среда:** Fedora Atomic Cosmic (toolbox/uv); `./scripts/bootstrap.sh`, `uv sync --extra all`, `./scripts/doctor.sh`. См. `.cursor/rules/agent-session-handoff.mdc` — коммит и пуш агент выполняет сам из корня репо.
- **Режим Cursor:** для максимальной производительности использовать coherent batching, а не хаотичный мультизадачный режим: [cursor.md](cursor.md), [planning.md](planning.md), [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md).

---

## Приоритет фич (roadmap)

Источник: `docs/plans.md` (roadmap 1–19, Phase A–D Steps 1–19, оставшееся до 100%). При предложении фич — по порядку 1→19.

| Приоритет | Направление |
|-----------|-------------|
| 1 | Шаблоны встреч в `analyze` |
| 2 | Обновление статусов action items по следующей встрече |
| 3 | Экспорт сессии (Markdown/PDF) |
| 4 | Выбор модели Ollama в конфиге |
| 5 | Документация «Первая встреча за 5 минут» |
| 6 | Отчёты по затратам (cost report) |
| 7 | Явный язык для STT |
| 8 | Расширенные e2e-тесты |
| 9 | Стриминговый STT в CLI (listen) |
| 10 | Live summary во время listen |
| 11 | Управление PII (вкл/выкл, только email) |
| 12 | Простой локальный Web UI |
| 13 | Десктопный UI (Tauri) |
| 14 | Офлайн-пакет (Flatpak/AppImage) |
| 15–19 | Smart trigger, бот, календарь, RAG-форматы, prompt caching |

Блоки: 1–4 быстрые победы; 5–7 доки/отчёты/STT; 8 e2e; 9–10 стриминг и live summary; 11–12 настройки и Web UI; 13–14 десктоп и упаковка; 15–20 опционально.

---

## Режим max autopilot (Cursor)

- **Порядок источников правды:** `agent-context` → `next-iteration-focus` → `PROJECT-STATUS-SUMMARY` → `planning` → `plans` / `audit`.
- **Брать 1 главный P0/P1 блок** и максимум **2 соседних подблока** только если это тот же subsystem, те же файлы или тот же тестовый набор.
- **Не смешивать unrelated surfaces** в одной итерации: например desktop packaging + RAG parsers + calendar.
- **Цель итерации:** код → targeted tests → docs/контракты → GitHub Project card → commit/push → обновление `next-iteration-focus`.
- **Если есть доступ к GitHub Project**, переводить карточку в `In Progress` при старте и в `Done` при `Closes #N`.
- **Подробная стратегия batching и готовый prompt:** [cursor.md](cursor.md), [planning.md](planning.md).

---

## Чеклист конца сессии (обязательно)

**Подробно:** `.cursor/rules/agent-session-handoff.mdc`. Кратко — в конце **каждой** сессии агент по возможности:

1. **Тесты:** `uv run pytest tests/ -q --tb=line`; при падении — починить или зафиксировать в next-iteration-focus.
2. **Коммит и пуш** — **сам** из **корня репо** (workspace path): `git add`, `git commit` (формат Conventional Commits: `feat:`, `fix:`, `docs:`, при задаче — `Closes #N`), `git push`. Не предлагать «выполните сами» — делать самому. Правила: [repo-and-git-governance.md](repo-and-git-governance.md).
3. **Обновить next-iteration-focus.md:** блок **«Следующий шаг»** (один конкретный шаг для следующего чата), дата, при необходимости криты/совет.
4. **Выдать промпт для следующего чата** — один блок для копирования (см. ниже). В нём уже есть: контекст, keyring, коммит/пуш, конкретная задача.

После **большой** итерации дополнительно: рекомендательные приоритетные задачи (5–7), до 5 критичных проблем, 1 совет — и всё это отразить в next-iteration-focus.

---

## Конец сессии (обязательно)

При завершении чата или по запросу «подвести итог»:

1. **Саммари:** что сделано, что отложено; краткий лог изменений.
2. **Обновить** `next-iteration-focus.md`: блок **«Следующий шаг»** (один шаг для следующего чата), дата.
3. **Выдать промпт для следующего чата** — один блок для копирования (формат ниже). В нём уже вшито: контекст, keyring, коммит/пуш в конце сессии, конкретная задача из следующего шага.

---

## Универсальный стартовый промпт (копируй в новый чат)

В начале **каждого** нового чата вставлять этот блок (и при необходимости дописать задачу). Агент по нему знает: контекст, keyring, что в конце сессии делать коммит/пуш и обновлять next-iteration-focus.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Режим Cursor и batching: @docs/runbooks/cursor.md. При работе по доске и issues: @docs/runbooks/planning.md. Сводный статус и приоритеты: @docs/runbooks/PROJECT-STATUS-SUMMARY.md.

Режим: максимальный автопилот и максимум согласованных блоков за итерацию. Выбирай 1 главный P0/P1 блок и до 2 соседних подблоков только если это тот же subsystem, те же файлы или те же проверки. Не смешивай unrelated surfaces. Делай полный цикл: код, targeted tests, docs/контракты, GitHub Project status, commit/push, обновление next-iteration-focus.

Ключи и доступы только в keyring (voiceforge). Fedora Atomic/toolbox/uv; базово `uv sync --extra all`, при нужде подключай профильные extras. В конце сессии: тесты, коммит, пуш, обновить next-iteration-focus, выдать prompt для следующего чата.

[Задача или: продолжить с @docs/runbooks/next-iteration-focus.md]
```

# Agent context (VoiceForge)

Единый контекст для Cursor-агента. Новый чат: приложи этот файл (@docs/runbooks/agent-context.md) — не ищи по проекту, работай по этому документу. Для продолжения — @docs/runbooks/next-iteration-focus.md (обновляет агент в конце сессии).

**Индекс документации (актуальность):** `docs/DOCS-INDEX.md`. **Порядок в доках (архив, источники правды):** [doc-governance.md](doc-governance.md). **AI tooling и source of truth:** [ai-tooling-setup.md](ai-tooling-setup.md). **Knowledge Copilot source of truth:** [../voiceforge-copilot-architecture.md](../voiceforge-copilot-architecture.md), [copilot-program-map.md](copilot-program-map.md). **Quality remediation snapshot:** [quality-audit-2026-03.md](quality-audit-2026-03.md). **Автопилот конца сессии:** `.cursor/rules/agent-session-handoff.mdc` (копия в репо: [agent-session-handoff-rule.md](agent-session-handoff-rule.md)). **Max-autopilot и batching:** [cursor.md](cursor.md), [planning.md](planning.md), [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md).

---

## Проект

**VoiceForge** — локальный ассистент для аудио-встреч на Linux: PipeWire → STT → diarization → RAG → LLM. Alpha 0.2, 20 CLI-команд (`voiceforge --help`: version, listen, meeting, analyze, index, watch, rag-export, daemon, install-service, uninstall-service, cost, status, sessions-to-ical, weekly-report, export, backup, history, web, action-items, calendar).

---

## Правила и окружение

- **Правила**: `.cursor/rules/cost-and-environment.mdc` — эффективность, точечный поиск, без лишних шагов.
- **Ключи и доступы — только keyring:** сервис `voiceforge`, имена: `anthropic`, `openai`, `huggingface`, `webhook_telegram`, `sonar_token`, `github_token` и др. Полный список: `docs/runbooks/keyring-keys-reference.md`. Не хардкодить, не коммитить; в облаке без keyring — Cursor My Secrets.
- **Конфиг:** `docs/runbooks/config-env-contract.md` — VOICEFORGE_*, Settings, D-Bus.
- **Среда:** Fedora Atomic Cosmic (toolbox/uv); `./scripts/bootstrap.sh`, `uv sync --extra all`, `./scripts/doctor.sh`. См. `.cursor/rules/agent-session-handoff.mdc` — коммит и пуш агент выполняет сам из корня репо.
- **Preflight перед крупной итерацией:** `./scripts/preflight_repo.sh --with-tests`.
- **Режим Cursor:** для максимальной производительности использовать coherent batching, а не хаотичный мультизадачный режим: [cursor.md](cursor.md), [planning.md](planning.md), [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md).

---

## Приоритет программы

Главный active track теперь задают:

1. [../voiceforge-copilot-architecture.md](../voiceforge-copilot-architecture.md)
2. [copilot-program-map.md](copilot-program-map.md)
3. [next-iteration-focus.md](next-iteration-focus.md)
4. [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md)

Старый roadmap в `docs/plans.md` и policy-слой `phase-e-decision-log.md` остаются историческим контекстом и scope guard для legacy surfaces, но не определяют основной execution order, пока Copilot track не заблокирован.

---

## Режим max autopilot (Cursor)

- **Порядок источников правды:** `agent-context` → `next-iteration-focus` → `copilot-program-map` → `voiceforge-copilot-architecture` → `PROJECT-STATUS-SUMMARY` → `planning` → legacy `plans` / `audit`.
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
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Product/architecture source of truth: @docs/voiceforge-copilot-architecture.md. Program map: @docs/runbooks/copilot-program-map.md. Режим Cursor и batching: @docs/runbooks/cursor.md. При работе по доске и issues: @docs/runbooks/planning.md. Сводный статус и приоритеты: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Scope guard для legacy surfaces: @docs/runbooks/phase-e-decision-log.md. AI/tooling source of truth: @docs/runbooks/ai-tooling-setup.md.

Режим: максимальный автопилот и максимум согласованных блоков за итерацию. Выбирай 1 главный P0/P1 блок и до 2 соседних подблоков только если это тот же subsystem, те же файлы или те же проверки. Не смешивай unrelated surfaces. Работай по существующим issue и policy-артефактам проекта; не создавай новые feature issues без отдельной причины. Делай полный цикл: код, targeted tests, docs/контракты, GitHub Project status, commit/push, обновление next-iteration-focus.

Ключи и доступы только в keyring (voiceforge). Fedora Atomic/toolbox/uv; базово `uv sync --extra all`, при нужде подключай профильные extras. Для infra/docs/governance cleanup сначала запускай `./scripts/preflight_repo.sh --with-tests`. В конце сессии: тесты, коммит, пуш, обновить next-iteration-focus, выдать prompt для следующего чата.

[Задача или: продолжить с @docs/runbooks/next-iteration-focus.md]
```

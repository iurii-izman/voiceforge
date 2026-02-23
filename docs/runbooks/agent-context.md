# Agent context (VoiceForge)

Единый контекст для Cursor-агента. Новый чат: приложи этот файл (@docs/runbooks/agent-context.md) — не ищи по проекту, работай по этому документу.

---

## Проект

**VoiceForge** — локальный ассистент для аудио-встреч на Linux: PipeWire → STT → diarization → RAG → LLM. Alpha 0.1, 9 CLI-команд.

---

## Правила и окружение

- **Правила**: `.cursor/rules/cost-and-environment.mdc`
  Эффективность и стоимость: точечный поиск (grep/codebase_search), параллельные чтения, без лишних шагов. Ключи только в keyring; разработка в Fedora Atomic Cosmic (toolbox/uv).
- **Конфиг и ключи**: `docs/runbooks/config-env-contract.md`
  `VOICEFORGE_*`, keyring сервис `voiceforge`, ключи: `anthropic`, `openai`, `huggingface`. Полный список имён ключей (sonar_token, github_token, codecov, …) — `docs/runbooks/keyring-keys-reference.md`. Не коммитить ключи; в облаке/без keyring — Cursor My Secrets.
- **Cursor/агент**: `docs/runbooks/cursor-agent-setup.md`
  My Secrets только если нет keyring; локально — keyring, `./scripts/bootstrap.sh`, `uv sync --extra all`, `./scripts/doctor.sh`.

---

## Приоритет фич (roadmap)

Источник: `docs/roadmap-priority.md`. При предложении фич — по порядку 1→20.

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
| 15–20 | Smart trigger, бот, календарь, RAG-форматы, prompt caching, macOS/WSL2 |

Блоки: 1–4 быстрые победы; 5–7 доки/отчёты/STT; 8 e2e; 9–10 стриминг и live summary; 11–12 настройки и Web UI; 13–14 десктоп и упаковка; 15–20 опционально.

---

## Конец сессии (обязательно)

Когда пользователь завершает чат или просит подвести итог:

1. **Саммари** (кратко): что сделано, что решено, что осталось в работе или отложено.
2. **Промпт для следующего чата** — один блок текста, который можно скопировать и вставить в начало нового чата. В промпте должны быть:
   - упоминание проекта VoiceForge и что агент должен опираться на контекст из `@docs/runbooks/agent-context.md`;
   - приоритет фич из roadmap (или «по docs/roadmap-priority.md»);
   - краткое напоминание: эффективно и дёшево, keyring, Fedora Atomic/toolbox/uv.

Пример финального блока для копирования:

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Работай по нему без поиска по проекту. Приоритет фич — docs/roadmap-priority.md. Эффективно и дёшево; ключи в keyring; Fedora Atomic/toolbox/uv.
[Здесь задача или «продолжить с …».]
```

---

## Универсальный стартовый промпт (копируй в новый чат)

```
VoiceForge. Контекст: @docs/runbooks/agent-context.md. Работай по нему, не ищи по проекту. Приоритеты: docs/roadmap-priority.md. Эффективно и дёшево; keyring; Fedora Atomic/toolbox/uv.

[Твоя задача]
```

# Единый бэклог и действия (требуют вашего участия или решения)

Один список всего отложенного и ручного: подтверждения, решения по приоритетам, ручные шаги, GitHub. Используется для трекинга в [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

**Источники:** [../../runbooks/next-iteration-focus.md](../../runbooks/next-iteration-focus.md), [../../plans/roadmap-100-blocks.md](../../plans/roadmap-100-blocks.md), [../../plans/MANUAL-AND-CANNOT-DO.md](../../plans/MANUAL-AND-CANNOT-DO.md), [../../runbooks/pre-beta-sonar-github.md](../../runbooks/pre-beta-sonar-github.md).

---

## Блок A. Подтверждения и разовые действия

| Тема | Что нужно от вас | Статус |
|------|-------------------|--------|
| **#65 CVE** | Пока ничего. Когда в upstream (diskcache/instructor) будет фикс — обновить зависимости, убрать `--ignore-vuln` по [../../runbooks/security-and-dependencies.md](../../runbooks/security-and-dependencies.md) разд. 4. Dependabot-алерт отклонить: «No fix version yet. See docs/runbooks/security-and-dependencies.md. Revisit when upstream fixes.» или скрипт `uv run python scripts/dependabot_dismiss_moderate.py`. | Ждём upstream |
| **Local data-at-rest posture** | Дополнительного решения сейчас не требуется: filesystem privacy baseline уже усилен (`0700/0600` для local data/cache/backup artifacts), но encryption-at-rest по-прежнему не реализован. При новых требованиях конфиденциальности — отдельный batch/решение про LUKS или SQLCipher, см. [../../runbooks/security-and-dependencies.md](../../runbooks/security-and-dependencies.md) §5, §7. | Accepted risk зафиксирован |
| **Keyring (HuggingFace)** | Один раз сохранить токен, если ещё не сохранён. Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. Сохранение: `secret-tool store --label='voiceforge huggingface' service voiceforge key huggingface`. | По доке проверено |
| **OTel/Jaeger** | Запуск контейнера (podman/docker), открытие http://localhost:16686, при необходимости выставить переменные в сессии. Агент только подсказывает команды. | По желанию |
| **#66 Async** | Ничего подтверждать не нужно. | — |

*Блок A подтверждён 2026-03-07 (#82).*

---

## Блок B. Решения по приоритетам (roadmap — отложенные блоки)

Из [roadmap-100-blocks.md](roadmap-100-blocks.md), раздел «Не реализовано». Нужен **ваш выбор**: делать ли, в каком объёме и в каком порядке.

| # | Блок | Зачем ваше решение |
|---|------|---------------------|
| ~~35~~ | ~~Тёмная тема трея~~ | Реализовано: icon-dark.png + set_tray_theme по теме UI (#87). |
| ~~44~~ | ~~История буфера обмена~~ | Реализовано (#88): voiceforge_clipboard_history, кнопка «История копирований», поповер в деталях сессии. |
| ~~46~~ | ~~Слайд-панель настроек~~ | Реализовано (#89): voiceforge_settings_as_panel, settings-slide-panel, чекбокс в настройках. |
| ~~49~~ | ~~Виджет «Последний анализ»~~ | Реализовано (#92): карточка last-analysis на главной, get_sessions + get_session_detail, кнопка «Открыть». |
| 66 | Prompt caching | В router.py cache_control (ephemeral) для Claude; для не-Claude — по API провайдера. Документация: [../../runbooks/prompt-management.md](../../runbooks/prompt-management.md) § Prompt caching (block 66). |
| ~~68~~ | ~~Streaming LLM в UI~~ | Реализовано (#91): stream_completion, analyze_meeting_stream, D-Bus StreamingAnalysisChunk, UI #analyze-streaming-output. |
| ~~71~~ | ~~Whisper API (OpenAI)~~ | Реализовано (#93): stt_backend local\|openai, OpenAIWhisperTranscriber, pipeline и демон по конфигу. |
| ~~75~~ | ~~Поиск по RAG из UI~~ | Реализовано: search_rag в демоне, D-Bus SearchRag, поле и результаты в UI (#94). |
| 79 | Создание события из сессии | Реализовано (#95): create_event в calendar, CLI calendar create-from-session, демон + D-Bus CreateEventFromSession, Tauri create_event_from_session. |

Под-issues созданы и добавлены на доску: #87 (35), #88 (44), #89 (46), #92 (49), #90 (66), #91 (68), #93 (71), #94 (75), #95 (79). Приоритет и порядок реализации — на усмотрение maintainer; агент может реализовывать по расстановке.

**Заметки по реализации (2026-03-07, обновлено 2026-03-07):**
- **#90 (66 prompt caching):** В `router.py` cache_control для Claude в `analyze_meeting`, `analyze_live_summary`, `_analysis_prompt`, `update_action_item_statuses`. Документация в prompt-management.md § Prompt caching (block 66); для не-Claude — по документации LiteLLM/провайдеров.
- **#91 (68 streaming LLM в UI):** Реализовано. Бэкенд: `stream_completion()` в router, `analyze_meeting_stream(stream_callback)`; демон передаёт delta в D-Bus `StreamingAnalysisChunk`; UI подписан на `streaming-analysis-chunk`, выводит в `#analyze-streaming-output`.
- **#93 (71 Whisper API):** Реализовано. Конфиг `stt_backend: local | openai`, ключ `openai` в keyring; `stt/openai_whisper.py` — `OpenAIWhisperTranscriber`; `get_transcriber_for_config` и `pipeline._step1_stt` выбирают по конфигу.
- **Блок 69 (retry LLM):** Реализовано. В `llm/circuit_breaker.py`: до 3 попыток (1 + _LLM_RETRY_MAX) с экспоненциальной задержкой (1s, 2s); после исчерпания — record_failure и открытие circuit.

---

## Блок C. Ручные шаги (без вас агент не сделает)

По [../../plans/MANUAL-AND-CANNOT-DO.md](../../plans/MANUAL-AND-CANNOT-DO.md).

| Действие | Кто |
|----------|-----|
| **Сборка/запуск десктопа** | `cd desktop && npm run tauri build`, `npm run tauri dev` — у вас на машине; проверка в окне. |
| **Ключи и секреты** | Keyring (в т.ч. CalDAV для виджета «Ближайшие встречи»); агент не видит секреты. |
| **Updater** | Сгенерировать ключи подписи (`npm run tauri signer generate -- -w ~/.tauri/voiceforge.key`), настроить сервер обновлений, при необходимости CI и `TAURI_SIGNING_PRIVATE_KEY`. См. [../../runbooks/desktop-updater.md](../../runbooks/desktop-updater.md). |
| **Релизы и распространение** | Создание GitHub Release, загрузка артефактов; при желании — Flatpak/Flathub. |
| **Тестирование с человеком** | E2E в среде с GUI, a11y с реальными пользователями/скринридерами, ручные сценарии (second instance, deep link, автозапуск). |

Чеклист ручных шагов зафиксирован в [../../plans/MANUAL-AND-CANNOT-DO.md](../../plans/MANUAL-AND-CANNOT-DO.md) (раздел «Чеклист ручных шагов»). (#84)

---

## Блок D. GitHub: ваши решения

| Что | Действие | Статус |
|-----|----------|--------|
| **PR #81, #79** | Изменения уже в main. Закрыть PR с комментарием «Applied in main». | ✓ Закрыты 2026-03-07 |
| **Issue #65** | Оставить открытым до фикса upstream; при желании отклонить Dependabot с комментарием из runbook. | Решение: оставить открытым; см. [../../runbooks/security-and-dependencies.md](../../runbooks/security-and-dependencies.md) §3–4 |
| **Issue #50** (macOS/WSL2) | Снят с текущего скоупа (фокус только Linux). | ✓ Закрыт 2026-03-07 |
| **verify_pr и bandit** | Добиться зелёного verify_pr (mypy, bandit, hypothesis в dev deps). | ✓ Mypy исправлен, hypothesis добавлен в dev; bandit зелёный |

---

## Блок E. Опционально: что поручить агенту

- Привести в порядок **bandit** (если решите, что verify_pr должен быть полностью зелёным).
- Доработать **оставшиеся замечания Sonar** по приоритету, который вы зададите.
- Реализовать любой из **отложенных блоков** B (35, 44, 46, 49, 66, 68, 71, 75, 79) после того как вы определите приоритет и scope.

---

## Работа с GitHub Project (доска)

**Проект:** [VoiceForge Board](https://github.com/users/iurii-izman/projects/1). Поля: **Status** (Todo → In Progress → Done), **Phase**, **Priority**, **Effort**, **Area**.

**Рекомендации для плотного трекинга:**

1. **Один issue — одна задача.** Крупные блоки (например «Решения по приоритетам») можно вести одним issue со ссылкой на этот документ; отдельные фичи (блок 35, 44, …) — отдельными issues с метками и привязкой к проекту.
2. **При старте работы по issue** — перевести карточку в **In Progress** (через веб или `gh project item-edit`).
3. **При коммите с `Closes #N`** — перенести карточку в **Done**.
4. **Агент:** при работе по issue переводит в In Progress; при закрытии — в Done. Нужен scope `project`: `gh auth refresh -s project`. Команды и ID полей — в [../../runbooks/planning.md](../../runbooks/planning.md).
5. **Раз в итерацию** просматривать доску: что в Todo, что застряло в In Progress, что можно закрыть или переприоритизировать.

Связь с репо: [../../runbooks/repo-and-git-governance.md](../../runbooks/repo-and-git-governance.md), [../../runbooks/planning.md](../../runbooks/planning.md).

---

## Промпт для нового чата (решить все задачи бэклога)

Скопируй в начало нового чата:

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, keyring, коммит/пуш в конце сессии). Единый бэклог: @docs/plans/backlog-and-actions.md.

Цель: пройти все блоки A–E и закрыть по максимуму. Доска: [GitHub Project #1](https://github.com/users/iurii-izman/projects/1), issues #82–86.

- Блок A: подтвердить статус CVE #65, keyring, OTel; при необходимости обновить доки или отклонить Dependabot с комментарием из runbook. Закрыть #82 когда всё зафиксировано.
- Блок B: со мной определить приоритет и scope отложенных блоков (35, 44, 46, 49, 66, 68, 71, 75, 79); оформить выбранные в issues и добавить на доску; реализовать по очереди. Закрыть #83 после решений и при необходимости создания под-issues.
- Блок C: напомнить чеклист ручных шагов (сборка, ключи, updater, релиз, тестирование); обновить MANUAL-AND-CANNOT-DO или runbooks по результатам. Закрыть #84 когда ручные пункты выполнены или зафиксированы.
- Блок D: закрыть PR #81 и #79 с комментарием «Applied in main»; зафиксировать решения по #65, #50, verify_pr/bandit в доке или в issue. Закрыть #85.
- Блок E: по моему решению — поручить тебе bandit, Sonar или отложенные блоки; выполнить и закрыть #86.

В конце сессии: тесты, коммит, пуш, обновить next-iteration-focus, перевести закрытые карточки в Done на доске. Начинай с блока A, затем по моим ответам — B, C, D, E.
```

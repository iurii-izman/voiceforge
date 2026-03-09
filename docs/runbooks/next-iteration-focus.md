# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-09 (E11 #134 закрыт; следующий — E16 #139 CI/CD Polish)

---

## Что требуется от вас (подтверждения и решения)

- **#65 CVE:** Фикса в upstream (diskcache/instructor) **пока нет — делать ничего не нужно**. Чеклист снятия: [security-and-dependencies.md](security-and-dependencies.md) разд. 4.
- **E19-E21:** дополнительных решений сейчас **не требуется**. Политика зафиксирована в [phase-e-decision-log.md](phase-e-decision-log.md):
  - `#142`: **Invest in Tauri**
  - `#143`: **Freeze Web UI / Telegram / RAG watcher; Invest narrow in Calendar**
  - `#144`: **Accept later = managed packaging; Defer = macOS/Windows, browser extension, GPU, Whisper.cpp/MLX; Reject current phase = SaaS, Web-only main UI, collaborative notes, PostgreSQL, fine-tuning**
- **Keyring (HuggingFace):** Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. **Проверено:** ключ присутствует.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** E11 (#134) Calendar Auto-Analyze: calendar_auto_listen (poll 5 min, start listen ≤2 min, auto-analyze after meeting end), desktop notify on smart trigger, action-items export (markdown/csv/clipboard), config key calendar_auto_listen, tests test_caldav_poll + test_action_export.

**Следующий шаг:** взять **E16 (#139)** CI/CD Polish (Auto-Release, Nightly Smoke).

---

## Текущий practical queue

**Единый источник:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) разд. 2. Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

| Wave | Issues | Статус | Что делать |
|------|--------|--------|------------|
| **Wave 1 (P0)** | #124✓→#125✓→#126✓→#127✓→#128✓ | **Done** | DDR 35→55 |
| **Wave 2 (P1 core)** | #129✓→#130✓→#131✓→#132✓→#133✓→#141✓ | **Done** | DDR 55→70 |
| **Wave 3 (P1 quality)** | #135✓→#136✓→#137✓→#138✓ | **Done** | — |
| **Wave 3.5 (Frontend)** | #142✓ | Done | Desktop-first Tauri (E19) |
| **Wave 4 (P2 polish)** | #134✓→#139→#140 | In progress | Calendar (narrow CalDAV) ✓; next E16 CI/CD |
| **Decision log** | #143✓, #144✓ | Resolved | Scope guard для автопилота; новых user decisions сейчас не нужно |
| **External wait** | #65 | Waiting upstream | CVE — ждём fix |

---

## Промпт для следующего чата (Phase E autopilot)

**Скопируй блок ниже в начало нового чата.** Агент работает на максимальном автопилоте, берёт E-блоки строго по порядку Wave.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Scope guard: @docs/runbooks/phase-e-decision-log.md. AI/tooling source of truth: @docs/runbooks/ai-tooling-setup.md.

Режим: максимальный автопилот, Phase E productization. Работать по уже существующим E-issues и текущему Wave order из PROJECT-STATUS-SUMMARY: E1→E18, E19 (desktop-first) закрыт; далее Wave 4. Новые E-issues не создавать без отдельной задачи. Брать 1 блок за сессию: код, targeted tests, docs sync, GitHub Project status, commit + push, обновить PROJECT-STATUS-SUMMARY и next-iteration-focus.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring (keyring-keys-reference.md). Тесты: targeted subset, не полный pytest (OOM risk). Для infra/docs сначала прогонять `./scripts/preflight_repo.sh --with-tests`. Pre-commit в toolbox; на хосте git push --no-verify если нет Python 3.12.

Задача: взять верхний незакрытый E-блок из Wave 4. Перевести issue в In Progress. Реализовать по чеклисту. Соблюдать phase-e-decision-log: Tauri = primary GUI, Web UI/Telegram/RAG watcher = maintenance-only, Calendar = narrow CalDAV; placeholders #148–#151 не активировать. Targeted tests. Commit с Closes #N (Conventional Commits). Done на доске. Обновить docs. Выдать промпт для следующего чата.

Текущий блок: Wave 4 — **E16 (#139)** CI/CD Polish (по приоритету на доске).
```

---

## Промпт: максимальный автопилот + максимум блоков за сессию

**Скопируй блок ниже если хочешь агрессивный темп (2-3 блока за сессию).**

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Scope guard: @docs/runbooks/phase-e-decision-log.md.

Режим: AGGRESSIVE автопилот, Phase E. Максимум E-блоков за сессию. Брать блоки строго по Wave order. Если блок завершён раньше ожидания — сразу брать следующий. Не тратить время на вопросы, если ответ есть в коде/docs/keyring.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring. Тесты: targeted, не полный pytest. Не создавать новые E-issues без явной необходимости; работать по существующим #124-#151 и policy placeholders не активировать.

Задача: начать с верхнего незакрытого E-блока, максимум блоков за итерацию. При каждом закрытии: commit + push, update docs, сразу следующий блок. В конце сессии: финальный docs sync + prompt для следующего чата.

Текущий Wave: 3 (E13 #136 → E15 #138), затем Wave 3.5: E19 #142. Цель сессии: закрыть верхний открытый блок текущего Wave и двигаться дальше без нарушения phase-e-decision-log.
```

---

## Актуальные напоминания

- **OOM / зависание при тестах:** запускать **только лёгкие** тесты по изменённому surface. Не запускать полный `pytest tests/` в Cursor (pyannote/torch/pipeline) — риск OOM.
- **Pre-commit (Fedora Atomic):** Python 3.12 в toolbox 43. Pre-commit: `toolbox run -c fedora-toolbox-43 bash -c 'cd /var/home/user/Projects/voiceforge && uv run pre-commit run --all-files'`. Вне toolbox: `git commit --no-verify`.
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).
- **Новые CLI-команды:** через ADR (ADR-0001). `voiceforge meeting` и `voiceforge setup` — новые команды, потребуют ADR update.
- **Scope guard:** UI-расширения делать в Tauri; Web UI, Telegram и RAG watcher не расширять beyond maintenance без нового решения. Calendar — только current CalDAV narrow path.
- **Доска:** при работе по issue In Progress → Done. Команды: [planning.md](planning.md).
- **Repo preflight:** перед cleanup / infra / governance-сессией запускать `./scripts/preflight_repo.sh --with-tests`.

---

## Что сделано (история)

Всё закрытое: [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Вкратце: Roadmap 1-18 реализован. Phase A-D (#55-#73) закрыт. Score-to-100 (#97-#123) закрыт. Engineering Score 80/100. Теперь Phase E: Daily Driver productization (#124-#144).

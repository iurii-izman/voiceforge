# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-09 (QA5 #156 закрыт; следующий — QA4 #155)

---

## Что требуется от вас (подтверждения и решения)

- **#65 CVE:** Фикса в upstream (diskcache/instructor) **пока нет — отдельно делать ничего не нужно**, кроме periodic re-check в рамках QA1. Чеклист снятия: [security-and-dependencies.md](security-and-dependencies.md) разд. 4.
- **E19-E21:** дополнительных решений сейчас **не требуется**. Политика зафиксирована в [phase-e-decision-log.md](phase-e-decision-log.md):
  - `#142`: **Invest in Tauri**
  - `#143`: **Freeze Web UI / Telegram / RAG watcher; Invest narrow in Calendar**
  - `#144`: **Accept later = managed packaging; Defer = macOS/Windows, browser extension, GPU, Whisper.cpp/MLX; Reject current phase = SaaS, Web-only main UI, collaborative notes, PostgreSQL, fine-tuning**
- **Keyring (HuggingFace):** Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. **Проверено:** ключ присутствует.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** QA5 #156 закрыт: DevOps/scripts Sonar — bootstrap.sh, preflight_repo.sh, create_productization_issues.sh (shell `[[`, explicit exit); check_docs_consistency.py (path.exists перед read); dependabot_dismiss_moderate.py (явный sys.exit(0)). Targeted checks + commit+push.

**Следующий шаг:** Взять QA4 #155 (Test suite Sonar: test-only debt, stubs, float equality, type smells). Затем #157 (Desktop/frontend Sonar).

---

## Текущий practical queue

**Единый источник:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) разд. 2. Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

| Wave | Issues | Статус | Что делать |
|------|--------|--------|------------|
| **Phase E** | #124✓→#142✓ | **Done** | Feature-track закрыт |
| **QA-A** | #152✓ → #153✓ | **Done** | Security + mypy закрыты |
| **QA-B** | #154✓ → #156✓ | **Done** | DevOps/scripts Sonar закрыт |
| **QA-C** | #155 → #157 | **Next** | Test suite Sonar (QA4 #155), затем desktop/frontend (#157) |
| **Decision log** | #143✓, #144✓ | Resolved | Scope guard для автопилота; новых user decisions сейчас не нужно |
| **External wait** | #65 | Waiting upstream | CVE остаётся tracked wait state до upstream fix |

---

## Промпт для следующего чата (quality remediation autopilot)

**Скопируй блок ниже в начало нового чата.** Агент работает по доске и next-iteration-focus; при появлении новой issue-задачи переводит её в In Progress и выполняет по чеклисту.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Quality audit: @docs/runbooks/quality-audit-2026-03.md. Scope guard: @docs/runbooks/phase-e-decision-log.md. AI/tooling source of truth: @docs/runbooks/ai-tooling-setup.md.

Режим: максимальный автопилот, post-Phase-E quality remediation wave. Работать по QA-блокам `#152-#157` в порядке `QA-A → QA-B → QA-C`. Новые feature issues не создавать без отдельной задачи пользователя. Брать 1 QA-блок за сессию, доводить до конца: код, targeted tests, docs sync, GitHub Project status, commit + push, обновить PROJECT-STATUS-SUMMARY и next-iteration-focus.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring (keyring-keys-reference.md). Тесты: targeted subset, не полный pytest (OOM risk). Для infra/docs/governance cleanup сначала прогонять `./scripts/preflight_repo.sh --with-tests`. Pre-commit в toolbox; на хосте git push --no-verify если нет Python 3.12.

Задача: взять QA4 #155 (Test suite Sonar: test-only debt). Перевести issue в In Progress, реализовать по чеклисту, targeted checks, commit с `Closes #155`, обновить docs. Затем при возможности #157 (Desktop Sonar). Соблюдать phase-e-decision-log; placeholders #148-#151 не активировать.
```

---

## Промпт: aggressive quality autopilot

**Скопируй блок ниже если хочешь агрессивный темп (2-3 блока за сессию).**

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Quality audit: @docs/runbooks/quality-audit-2026-03.md. Scope guard: @docs/runbooks/phase-e-decision-log.md.

Режим: AGGRESSIVE автопилот, quality remediation wave. Максимум согласованных QA-блоков за сессию. Брать блоки строго по порядку `#152 → #153 → #154 → #156 → #155 → #157`, но объединять только соседние блоки одного subsystem и одного verification loop.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring. Тесты: targeted, не полный pytest. Не создавать новые feature issues без явной необходимости; работать по существующим QA issues и не активировать placeholders #148-#151.

Задача: начать с верхнего открытого QA-блока. Если блок завершён раньше ожидания и следующий лежит в том же subsystem, сразу брать следующий. При каждом закрытии: commit + push, update docs, сразу следующий блок. В конце сессии: финальный docs sync + prompt для следующего чата.
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

Вкратце: Roadmap 1-18 реализован. Phase A-D (#55-#73) закрыт. Score-to-100 (#97-#123) закрыт. Phase E Daily Driver (#124-#144) закрыт. Текущий live queue: quality remediation wave `#152-#157`.

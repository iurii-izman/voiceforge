# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-13 (desktop test policy #160 done)

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

**Сделано в сессии:** закрыт `#160`: введён единый advisory native smoke runner с таймаутом и артефактами (`desktop/e2e-native/artifacts/latest/`), `desktop/package.json` и `check_release_proof.py` теперь закрепляют две канонические команды: `cd desktop && npm run e2e:release-gate` (blocking) и `cd desktop && npm run e2e:native:headless` (advisory). `npm --prefix desktop run e2e:release-gate` зелёный, а native smoke теперь завершается предсказуемо и оставляет evidence вместо немого зависания.

**Следующий шаг:** перейти к `#161` — расширить desktop regression matrix под реальные user-visible state bugs: persistence, navigation recovery, mode transitions и другие UX-regressions, которые теперь должны сразу превращаться в Playwright coverage.

---

## Текущий practical queue

**Единый источник:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) разд. 2. Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

| Wave | Issues | Статус | Что делать |
|------|--------|--------|------------|
| **Phase E** | #124✓→#142✓ | **Done** | Feature-track закрыт |
| **QA-A** | #152✓ → #153✓ | **Done** | Security + mypy закрыты |
| **QA-B** | #154✓ → #156✓ | **Done** | DevOps/scripts Sonar закрыт |
| **QA-C** | #155 ✓ → #157 ✓ | **Done** | Desktop/frontend Sonar закрыт |
| **Desktop Stabilization** | #159✓ → #160✓ → #161 | **In progress** | UX bugs и test policy закрыты, дальше regression matrix |
| **Decision log** | #143✓, #144✓ | Resolved | Scope guard для автопилота; новых user decisions сейчас не нужно |
| **External wait** | #65 | Waiting upstream | CVE остаётся tracked wait state до upstream fix |

---

## Промпт для следующего чата (desktop stabilization autopilot)

**Скопируй блок ниже в начало нового чата.** Агент работает по доске и next-iteration-focus; при появлении новой issue-задачи переводит её в In Progress и выполняет по чеклисту.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Desktop QA policy: @docs/runbooks/desktop-gui-testing.md. Desktop release gate: @docs/runbooks/desktop-release-gate-matrix.md. Scope guard: @docs/runbooks/phase-e-decision-log.md. AI/tooling source of truth: @docs/runbooks/ai-tooling-setup.md.

Режим: максимальный автопилот. Активная очередь после Phase E и QA wave — desktop stabilization wave `#159 → #160 → #161`. Новые feature issues не создавать без отдельной задачи. Полный цикл: код → targeted tests → docs sync → GitHub Project status → commit + push → next-iteration-focus.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring (keyring-keys-reference.md). Тесты: targeted subset, не полный pytest (OOM risk). Для infra/docs/governance cleanup сначала прогонять `./scripts/preflight_repo.sh --with-tests`. Pre-commit в toolbox; на хосте git push --no-verify если нет Python 3.12.

Задача: взять `#161` — расширить desktop regression matrix под реальные UX-regressions: persistence, navigation recovery, mode transitions, onboarding/state recovery. Каждый найденный руками desktop UI баг сразу превращать в regression test. Сохранять policy из `desktop-gui-testing.md`: blocking = `cd desktop && npm run e2e:release-gate`, advisory native evidence = `cd desktop && npm run e2e:native:headless`.
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

Вкратце: Roadmap 1-18 реализован. Phase A-D (#55-#73) закрыт. Score-to-100 (#97-#123) закрыт. Phase E Daily Driver (#124-#144) закрыт. QA wave #152–#157 завершена. Desktop UX stabilization `#159` закрыт. Следующий активный трек: `#160 → #161`.

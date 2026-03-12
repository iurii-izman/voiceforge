# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-13 (desktop GUI audit closed; remaining follow-up is remote Sonar recheck plus GTK/glib alert)

---

## Что требуется от вас (подтверждения и решения)

- **Security/CVE:** дополнительных ручных действий сейчас **не требуется**. `pip-audit` снова чист; источник правды по remaining remote alerts — [security-decision-log.md](security-decision-log.md).
- **E19-E21:** дополнительных решений сейчас **не требуется**. Политика зафиксирована в [phase-e-decision-log.md](phase-e-decision-log.md):
  - `#142`: **Invest in Tauri**
  - `#143`: **Freeze Web UI / Telegram / RAG watcher; Invest narrow in Calendar**
  - `#144`: **Accept later = managed packaging; Defer = macOS/Windows, browser extension, GPU, Whisper.cpp/MLX; Reject current phase = SaaS, Web-only main UI, collaborative notes, PostgreSQL, fine-tuning**
- **Keyring (HuggingFace):** Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. **Проверено:** ключ присутствует.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** закрыт desktop GUI audit `#166`: runtime i18n добит для живых empty/error/notification/update states, home/dashboard refresh унифицирован после daemon recovery и analyze, regression matrix расширена на English runtime и widget recovery consistency. Локальные проверки зелёные: `npm --prefix desktop run e2e:release-gate` (`28 passed`), `check_docs_consistency.py`. Desktop stabilization wave теперь закрыта полностью.

**Следующий шаг:** завершить `#165`: дождаться re-analysis SonarCloud после уже запушенного low-risk cleanup и снять новый issue snapshot. Если low-risk findings реально ушли, закрыть `#165` и только потом возвращаться к `#164` как узкому Linux GTK/Tauri refresh для remaining `glib` alert.

---

## Текущий practical queue

**Единый источник:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) разд. 2. Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

| Wave | Issues | Статус | Что делать |
|------|--------|--------|------------|
| **Phase E** | #124✓→#142✓ | **Done** | Feature-track закрыт |
| **QA-A** | #152✓ → #153✓ | **Done** | Security + mypy закрыты |
| **QA-B** | #154✓ → #156✓ | **Done** | DevOps/scripts Sonar закрыт |
| **QA-C** | #155 ✓ → #157 ✓ | **Done** | Desktop/frontend Sonar закрыт |
| **Desktop Stabilization** | #159✓ → #160✓ → #161✓ | **Done** | UX bugs, test policy и regression matrix закрыты |
| **Decision log** | #143✓, #144✓ | Resolved | Scope guard для автопилота; новых user decisions сейчас не нужно |
| **Maintenance** | #162✓ | Done | Weekly re-check добавлен |
| **Security Hardening** | #163✓ → #164 | Active | npm native-e2e alert закрыт; `time` alert закрыт; remaining coordinated block = `glib` in Linux desktop stack |
| **Sonar Sweep** | #165 | Active | Low-risk local cleanup готов; нужен remote Sonar recheck и residual triage |

---

## Промпт для следующего чата (desktop stabilization autopilot)

**Скопируй блок ниже в начало нового чата.** Агент работает в maintenance mode: если нет новой issue-задачи или нового bug report, ограничивается periodic re-check и не разворачивает новый feature-track.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Desktop QA policy: @docs/runbooks/desktop-gui-testing.md. Desktop release gate: @docs/runbooks/desktop-release-gate-matrix.md. Scope guard: @docs/runbooks/phase-e-decision-log.md. AI/tooling source of truth: @docs/runbooks/ai-tooling-setup.md.

Режим: максимальный автопилот, maintenance/hardening mode. Feature-track закрыт. Работать только по существующим targeted hardening issues или по новым подтверждённым bug reports. Новые feature issues не создавать без отдельной задачи. Если появляется новый bug report, сначала оформить issue на доске, затем работать по полному циклу: код → targeted tests → docs sync → GitHub Project status → commit + push → next-iteration-focus.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring (keyring-keys-reference.md). Тесты: targeted subset, не полный pytest (OOM risk). Для infra/docs/governance cleanup сначала прогонять `./scripts/preflight_repo.sh --with-tests`. Pre-commit в toolbox; на хосте git push --no-verify если нет Python 3.12.

Задача: взять `#165` как следующий targeted hardening block. Сначала выполнить `uv run python scripts/check_maintenance_state.py`, затем запушить текущий low-risk Sonar cleanup, дождаться SonarCloud re-analysis и снять новый snapshot через `uv run python scripts/sonar_fetch_issues.py --json`. Если low-risk findings ушли, закрыть `#165`, обновить docs и только потом возвращаться к `#164` как отдельному Rust/GTK refresh для remaining `glib` alert.
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

Вкратце: Roadmap 1-18 реализован. Phase A-D (#55-#73) закрыт. Score-to-100 (#97-#123) закрыт. Phase E Daily Driver (#124-#144) закрыт. QA wave #152–#157 завершена. Desktop stabilization `#159-#161` завершена. Репо в maintenance mode; активных open blockers сейчас нет.

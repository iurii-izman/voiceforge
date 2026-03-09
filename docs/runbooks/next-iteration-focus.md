# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-09 (E8 #131 закрыт; следующий — E9 #132)

---

## Что требуется от вас (подтверждения и решения)

- **#65 CVE:** Фикса в upstream (diskcache/instructor) **пока нет — делать ничего не нужно**. Чеклист снятия: [security-and-dependencies.md](security-and-dependencies.md) разд. 4.
- **E19 Desktop UI Strategy (#142):** Решите: Invest (E2E + tray) / Freeze / Replace with SPA. Пока решения нет — блок пропускается.
- **E20 Surface Freeze (#143):** Решите по каждому surface: Web UI, Telegram, Calendar, RAG Watcher.
- **E21 Beyond Boundaries (#144):** macOS, SaaS, GPU, browser extension и др. — по каждому Accept/Reject/Defer.
- **Keyring (HuggingFace):** Проверка: `uv run python -c "from voiceforge.core.secrets import get_api_key; print('huggingface:', 'present' if get_api_key('huggingface') else 'absent')"`. **Проверено:** ключ присутствует.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** E8 (#131) Model Pre-Download & Bootstrap: voiceforge download-models (Whisper по config + ONNX check, rich progress, retry); bootstrap.sh — uv run voiceforge download-models (если не --skip-models), RAM warning <4GB, финальное «Setup complete! Run: voiceforge meeting»; status --doctor — models cached (Whisper/ONNX/pyannote), disk usage ~/.cache/huggingface, RAM recommended ≥4 GB; тесты test_download_models.py.

**Следующий шаг:** взять **E9 (#132) Post-Listen Auto-Analyze & Cost Estimate** — следующий блок Wave 2.

---

## Текущий practical queue

**Единый источник:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) разд. 2. Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

| Wave | Issues | Статус | Что делать |
|------|--------|--------|------------|
| **Wave 1 (P0)** | #124✓→#125✓→#126✓→#127✓→#128✓ | **Done** | DDR 35→55 |
| **Wave 2 (P1 core)** | #129✓→#130✓→#131✓→#132→#133→#141 | In progress | E9 следующий. DDR 55→70 |
| **Wave 3 (P1 quality)** | #135→#136→#137→#138 | Todo | Testing + Core + CLI + Obs |
| **Wave 4 (P2 polish)** | #134→#139→#140 | Todo | Calendar + CI/CD + Security |
| **User decisions** | #142, #143, #144 | Awaiting user | Требуют решения пользователя |
| **External wait** | #65 | Waiting upstream | CVE — ждём fix |

---

## Промпт для следующего чата (Phase E autopilot)

**Скопируй блок ниже в начало нового чата.** Агент работает на максимальном автопилоте, берёт E-блоки строго по порядку Wave.

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md.

Режим: максимальный автопилот, Phase E productization. Реализовать блоки E1-E18 по порядку Wave 1→2→3→4. Каждый блок — GitHub issue с label `autopilot` + `phase:E`. Брать 1 блок за сессию, доводить до конца: код, тесты, docs sync, commit + push, обновить PROJECT-STATUS-SUMMARY и next-iteration-focus.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring (keyring-keys-reference.md). Тесты: targeted subset, не полный pytest (OOM risk). Pre-commit в toolbox; на хосте git push --no-verify если нет Python 3.12.

Задача: взять верхний незакрытый E-блок из текущего Wave. Перевести issue в In Progress на доске. Реализовать по чеклисту в issue body. Targeted tests. Commit с `Closes #N` (Conventional Commits). Done на доске. Обновить docs. Выдать prompt для следующего чата.

Текущий блок: E9 (#132) — Post-Listen Auto-Analyze & Cost Estimate.
```

---

## Промпт: максимальный автопилот + максимум блоков за сессию

**Скопируй блок ниже если хочешь агрессивный темп (2-3 блока за сессию).**

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md.

Режим: AGGRESSIVE автопилот, Phase E. Максимум E-блоков за сессию. Брать блоки строго по Wave order. Если блок завершён раньше ожидания — сразу брать следующий. Не тратить время на вопросы, если ответ есть в коде/docs/keyring.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring. Тесты: targeted, не полный pytest.

Задача: начать с верхнего незакрытого E-блока, максимум блоков за итерацию. При каждом закрытии: commit + push, update docs, сразу следующий блок. В конце сессии: финальный docs sync + prompt для следующего чата.

Текущий Wave: 1 (E1 #124 → E5 #128). Цель сессии: закрыть E1 + E2 (или больше).
```

---

## Актуальные напоминания

- **OOM / зависание при тестах:** запускать **только лёгкие** тесты по изменённому surface. Не запускать полный `pytest tests/` в Cursor (pyannote/torch/pipeline) — риск OOM.
- **Pre-commit (Fedora Atomic):** Python 3.12 в toolbox 43. Pre-commit: `toolbox run -c fedora-toolbox-43 bash -c 'cd /var/home/user/Projects/voiceforge && uv run pre-commit run --all-files'`. Вне toolbox: `git commit --no-verify`.
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).
- **Новые CLI-команды:** через ADR (ADR-0001). `voiceforge meeting` и `voiceforge setup` — новые команды, потребуют ADR update.
- **Доска:** при работе по issue In Progress → Done. Команды: [planning.md](planning.md).

---

## Что сделано (история)

Всё закрытое: [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Вкратце: Roadmap 1-18 реализован. Phase A-D (#55-#73) закрыт. Score-to-100 (#97-#123) закрыт. Engineering Score 80/100. Теперь Phase E: Daily Driver productization (#124-#144).

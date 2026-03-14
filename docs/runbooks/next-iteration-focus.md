# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии**. Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-14 (KC14 done: Copilot QA, release, perf & reliability; KC-волна программы закрыта)

---

## Что требуется от вас (подтверждения и решения)

- **KV1 / legal-consent:** пока дополнительных ручных действий не требуется, но до `KC11` нужно будет отдельное подтверждение по system-audio consent и retention wording.
- **KV2 / overlay UX sign-off:** KC2 реализован; до финального sign-off желателен живой просмотр overlay UX (опционально).
- **Security hardening:** `#164/#165` остаются открытыми, но не задают основной execution order, пока не появится blocking regression.
- **Legacy scope guard:** [phase-e-decision-log.md](phase-e-decision-log.md) остаётся ограничителем для старых surfaces (Web UI / Telegram / RAG watcher / calendar narrow path) и не должен silently переопределяться в copilot треке.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** KC14 · Copilot QA, release, performance & reliability (#186): честный copilot release gate в матрице и release-and-quality; runbook [copilot-qa-and-release.md](copilot-qa-and-release.md) (latency budgets, failure UX, idle-unload); config `copilot_stt_idle_unload_seconds` (default 300) и idle-unload в daemon capture_start; get_settings возвращает ключ; тесты и DOCS-INDEX обновлены. Docs: copilot-program-map, next-iteration-focus, config-env-contract, desktop-release-gate-matrix, release-and-quality.

**Следующий шаг:** Разблокированных KC нет. Варианты: (1) разрешить KV1 → KC11 (#183); (2) разрешить KV5 → KC13 (#185); (3) поддержка/другая работа по приоритетам.

---

## Текущий practical queue

**Единый источник:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) разд. 2 и [copilot-program-map.md](copilot-program-map.md). Доска: [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1).

| Track | Issues | Статус | Что делать |
| --- | --- | --- | --- |
| **KD** | #170✓ → #172✓ | Done | Decision-locked product / UX / architecture contracts |
| **KC bootstrap** | #173✓ | Done | Program seeding, traceability, docs handoff |
| **Wave 1 MVP Core** | #174✓ → #175✓ → #176✓ → #177✓ → #178✓ | Done | KC6 done; Wave 1 complete |
| **Wave 2 MVP Complete** | #179✓ → #180✓ | Done | KC8 done |
| **Wave 2 V2 Surface** | #181✓ | Done | KC9 done |
| **Wave 3 V2 Expansion** | #182✓ → #183 (blocked) | Active | KC10 done; KC11 ждёт KV1 |
| **Wave 4 V3 / Frontier** | #184✓ → #185 (blocked) → #186✓ | Done | KC12, KC14 done; KC13 ждёт KV5 |
| **Manual gates** | #187 → #191 | Todo | Legal, UX sign-off, pilot validation, business gate, platform gate |
| **Background hardening** | #165, #164 | Open | Keep below copilot program unless blocking |

---

## Промпт для следующего чата (copilot autopilot)

```text
Проект VoiceForge. Главный source of truth по новому треку: @docs/voiceforge-copilot-architecture.md и @docs/runbooks/copilot-program-map.md. Статус и active queue: @docs/runbooks/PROJECT-STATUS-SUMMARY.md и @docs/runbooks/next-iteration-focus.md. Planning/process: @docs/runbooks/planning.md. Existing desktop QA policy: @docs/runbooks/desktop-qa-plan.md. Legacy scope guard for old surfaces: @docs/runbooks/phase-e-decision-log.md.

Режим: максимальный автопилот, главный active track = Knowledge Copilot program. Работать только по блокам KC/KV/KD из GitHub Project. KD блоки считать decision-locked. KV блоки не реализовывать кодом, если в issue явно указан внешний/manual gate. Брать один верхний открытый KC-блок, переводить в In Progress, доводить до конца: код -> targeted tests -> docs sync -> GitHub Project -> commit + push -> обновить next-iteration-focus.

Не расширять scope блока за пределы его acceptance criteria. Любой найденный UI/UX баг сразу превращать в отдельный issue только если он не помещается в текущий KC-блок и имеет собственный verification loop.

Перед началом крупного блока: `./scripts/preflight_repo.sh --with-tests`. Для desktop/UI изменений: `cd desktop && npm run e2e:release-gate`. Для native/Tauri/system-level изменений дополнительно: `cd desktop && npm run e2e:native:headless`.

KC14 выполнен; KC-волна программы закрыта. Следующих разблокированных KC нет. Варианты: (1) разрешить KV1 → взять KC11; (2) разрешить KV5 → взять KC13; (3) maintenance/ hardening/другая работа по приоритетам.
```

---

## Актуальные напоминания

- **OOM / зависание при тестах:** запускать только targeted tests по изменённому surface. Не гонять полный `pytest tests/`, если нет отдельной причины.
- **Pre-commit / toolbox:** основной рабочий контур — toolbox + `uv sync --extra all`; перед крупной итерацией запускать `./scripts/preflight_repo.sh --with-tests`.
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).
- **Project hygiene:** любой новый copilot bug, не помещающийся в текущий `KC` block, оформлять отдельным issue на доске и закрывать только с regression coverage.
- **Background hardening:** `#164/#165` не закрывать и не удалять; возвращаться к ним только если Copilot track не блокирован.

---

## Что сделано (история)

Всё закрытое: [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Вкратце: Roadmap 1-18 реализован. Phase A-D (#55-#73) закрыт. Score-to-100 (#97-#123) закрыт. Phase E Daily Driver (#124-#144) закрыт. QA wave #152–#157 завершена. Desktop stabilization `#159-#169` завершена. Новый активный трек: Knowledge Copilot program `#170-#191`.

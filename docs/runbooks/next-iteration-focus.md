# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии**. Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-03-14 (Updater включён: pubkey, endpoints, install flow doc)

---

## Что требуется от вас (подтверждения и решения)

- **KV1 / legal-consent:** пока дополнительных ручных действий не требуется, но до `KC11` нужно будет отдельное подтверждение по system-audio consent и retention wording.
- **KV2 / overlay UX sign-off:** KC2 реализован; до финального sign-off желателен живой просмотр overlay UX (опционально).
- **Security hardening:** `#164/#165` остаются открытыми, но не задают основной execution order, пока не появится blocking regression.
- **Legacy scope guard:** [phase-e-decision-log.md](phase-e-decision-log.md) остаётся ограничителем для старых surfaces (Web UI / Telegram / RAG watcher / calendar narrow path) и не должен silently переопределяться в copilot треке.

---

## Следующий шаг (для копирования в новый чат)

**Сделано в сессии:** Updater подготовлен к включению: `createUpdaterArtifacts: true`, скрипт `scripts/enable_updater.py` (генерация ключа и подстановка pubkey/endpoints), манифест `updates/update.json` и скрипт `scripts/write_update_json.py` для релиза; runbook [desktop-updater.md](desktop-updater.md) обновлён (включение, манифест при релизе, проверка install flow). Включение: выполнить `enable_updater.py` и закоммитить изменённый tauri.conf.json. Ранее: Sonar BLOCKER, релиз 1.0.0-beta.1, audit/what-user-must-do/reflective-summary.

**Следующий шаг:** KV5 разрешён (Linux-only, зафиксировано в #191 и [platform-gate-kv5.md](platform-gate-kv5.md)). **KC13 (#185) разблокирован** — можно брать на автопилот. Варианты: (1) взять KC13 · Adaptive intelligence and extensibility; (2) разрешить KV1 → KC11; (3) Sonar/hardening, Dependabot.

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
| **Wave 4 V3 / Frontier** | #184✓ → #185 → #186✓ | Active | KC12, KC14 done; KC13 разблокирован (KV5 resolved) |
| **Manual gates** | #187 → #191✓ | KV5 done | KV1/KV2/KV3/KV4 остаются; KV5 закрыт (Linux-only) |
| **Background hardening** | #165, #164 | Open | Keep below copilot program unless blocking |

---

## Промпт для следующего чата (copilot autopilot)

```text
Проект VoiceForge. Главный source of truth по новому треку: @docs/voiceforge-copilot-architecture.md и @docs/runbooks/copilot-program-map.md. Статус и active queue: @docs/runbooks/PROJECT-STATUS-SUMMARY.md и @docs/runbooks/next-iteration-focus.md. Planning/process: @docs/runbooks/planning.md. Existing desktop QA policy: @docs/runbooks/desktop-qa-plan.md. Legacy scope guard for old surfaces: @docs/runbooks/phase-e-decision-log.md.

Режим: максимальный автопилот, главный active track = Knowledge Copilot program. Работать только по блокам KC/KV/KD из GitHub Project. KD блоки считать decision-locked. KV блоки не реализовывать кодом, если в issue явно указан внешний/manual gate. Брать один верхний открытый KC-блок, переводить в In Progress, доводить до конца: код -> targeted tests -> docs sync -> GitHub Project -> commit + push -> обновить next-iteration-focus.

Не расширять scope блока за пределы его acceptance criteria. Любой найденный UI/UX баг сразу превращать в отдельный issue только если он не помещается в текущий KC-блок и имеет собственный verification loop.

Перед началом крупного блока: `./scripts/preflight_repo.sh --with-tests`. Для desktop/UI изменений: `cd desktop && npm run e2e:release-gate`. Для native/Tauri/system-level изменений дополнительно: `cd desktop && npm run e2e:native:headless`.

KV5 разрешён (Linux-only). KC13 (#185) разблокирован — можно брать KC13 на автопилот. Варианты: (1) брать KC13; (2) KV1 → KC11; (3) Sonar/hardening/Dependabot.
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

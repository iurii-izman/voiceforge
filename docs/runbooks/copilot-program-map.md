# Knowledge Copilot Program Map

**Updated:** 2026-03-14 (KC14 done: Copilot QA, release, performance & reliability; program wave complete)
**Primary source of truth:** [voiceforge-copilot-architecture.md](../voiceforge-copilot-architecture.md)
**Execution queue:** [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md), [next-iteration-focus.md](next-iteration-focus.md)
**Background hardening:** [#164](https://github.com/iurii-izman/voiceforge/issues/164), [#165](https://github.com/iurii-izman/voiceforge/issues/165)

## Purpose

This file is the operational map for the Knowledge Copilot program. Nothing in the architecture document should be left "just in prose": every section must be covered by a decision block (`KD`), an autopilot implementation block (`KC`), or a manual/user gate (`KV`).

## Current State

- `KD1-KD3` are seeded and closed as `decision-locked` policy artefacts.
- `KC1` is complete: the program is bootstrapped, the GitHub Project is seeded, and handoff is switched to the Copilot track.
- **Current next executable block:** KC11 (#183) или KC13 (#185) — KV1 и KV5 разрешены; оба KC доступны для автопилота.
- `#164` and `#165` remain open as background maintenance/security hardening and are not part of the main copilot execution order.

## Block Registry

### KD · Decision-Locked

| Prefix | Issue | Status | Role |
| --- | --- | --- | --- |
| KD1 | [#170](https://github.com/iurii-izman/voiceforge/issues/170) | Done | Product charter: Knowledge Copilot positioning, personas, scenarios, Concept A selection |
| KD2 | [#171](https://github.com/iurii-izman/voiceforge/issues/171) | Done | UX contract: calm technology, push-to-capture, no always-on recording, no TTS/auto-response, max 3 cards |
| KD3 | [#172](https://github.com/iurii-izman/voiceforge/issues/172) | Done | Architecture contract: RAG-first, hybrid default, mic-only MVP, single orchestrator with fast/deep tracks |

### KC · Autopilot Implementation Blocks

| Prefix | Issue | Wave | Status | Notes |
| --- | --- | --- | --- | --- |
| KC1 | [#173](https://github.com/iurii-izman/voiceforge/issues/173) | 0 | Done | Program bootstrap, traceability, project seeding, docs sync |
| KC2 | [#174](https://github.com/iurii-izman/voiceforge/issues/174) | 1 | Done | Overlay shell, second window, hotkey down/up, recording indicator, armed/recording/analyzing/error, no focus steal |
| KC3 | [#175](https://github.com/iurii-izman/voiceforge/issues/175) | 1 | Done | Capture runtime, markers, pre-roll, 30s auto-stop, recording_warning, stt_ambiguous |
| KC4 | [#176](https://github.com/iurii-izman/voiceforge/issues/176) | 1 | Done | Tiny-model streaming STT copilot path |
| KC5 | [#177](https://github.com/iurii-izman/voiceforge/issues/177) | 1 | Done | Evidence-first RAG, groundedness, citations |
| KC6 | [#178](https://github.com/iurii-izman/voiceforge/issues/178) | 1 | Done | Fast-track cards: Answer, Do/Don't, Clarify |
| KC7 | [#179](https://github.com/iurii-izman/voiceforge/issues/179) | 2 | Done | Deep track, session memory, card priority/overflow |
| KC8 | [#180](https://github.com/iurii-izman/voiceforge/issues/180) | 2 | Done | Main-window copilot integration and settings |
| KC9 | [#181](https://github.com/iurii-izman/voiceforge/issues/181) | 2 | Done | Knowledge management UI and context packs |
| KC10 | [#182](https://github.com/iurii-izman/voiceforge/issues/182) | 3 | Done | Explicit mode system, hybrid/offline maturity |
| KC11 | [#183](https://github.com/iurii-izman/voiceforge/issues/183) | 3 | Todo | System audio and scenario presets (KV1 resolved) |
| KC12 | [#184](https://github.com/iurii-izman/voiceforge/issues/184) | 4 | Done | Pro cards and answer refinement |
| KC13 | [#185](https://github.com/iurii-izman/voiceforge/issues/185) | 4 | Todo | Adaptive intelligence and extensibility (KV5 resolved: Linux-only) |
| KC14 | [#186](https://github.com/iurii-izman/voiceforge/issues/186) | 4 | Done | Copilot QA, perf/reliability, release evidence |

### KV · User / External Intervention Blocks

| Prefix | Issue | Timing | Status | Gate |
| --- | --- | --- | --- | --- |
| KV1 | [#187](https://github.com/iurii-izman/voiceforge/issues/187) | Before KC11 | Resolved | Legal/consent wording approved; KC11 in scope. See [legal-consent-kv1.md](legal-consent-kv1.md) |
| KV2 | [#188](https://github.com/iurii-izman/voiceforge/issues/188) | Before KC2 completion | Todo | Overlay UX sign-off |
| KV3 | [#189](https://github.com/iurii-izman/voiceforge/issues/189) | After KC6 | Todo | Pilot validation with primary persona |
| KV4 | [#190](https://github.com/iurii-izman/voiceforge/issues/190) | Before commercial packaging | Todo | Business/packaging decision |
| KV5 | [#191](https://github.com/iurii-izman/voiceforge/issues/191) | Before KC13 platform frontier | Resolved (Linux-only) | Explicit platform expansion gate; no-go, KC13 unblocked |

## Execution Order

1. `KD1 -> KD3` seeded and closed as decision records.
2. `KC1` completed as the bootstrap block.
3. **Wave 1 MVP Core:** `KC2 -> KC3 -> KC4 -> KC5 -> KC6`
4. **Wave 2 MVP Complete:** `KC7 -> KC8`
5. **Wave 3 V2 Expansion:** `KC9 -> KC10 -> KC11`
6. **Wave 4 V3 / Pro / Frontier:** `KC12 -> KC13 -> KC14`
7. `KV` blocks stay in `Todo` until their gate is explicitly resolved.
8. `#164` and `#165` stay open but remain below the Copilot track in handoff.

## Section-To-Block Traceability

| Source sections | Covered by |
| --- | --- |
| `Executive Summary`, `1`, `2`, `3`, `18` | `KD1`, `KD2`, `KD3`, `KC1` |
| `4` | `KC2`, `KC3`, `KC4`, `KC6`, `KC7` |
| `5` | `KD2`, `KC3`, `KC11`, `KV1` |
| `6` | `KD2`, `KC6`, `KC7`, `KC12` |
| `7` | `KD3`, `KC5` |
| `8` | `KD3` |
| `9` | `KD3`, `KC10`, `KV4` |
| `10` | `KC2`, `KC3`, `KC4`, `KC5`, `KC10`, `KC13` |
| `11` | `KC2`, `KC6`, `KC7`, `KC8`, `KV2` |
| `12` | `KC7`, `KC9`, `KC10`, `KC11`, `KC12`, `KC13` |
| `13` | `KC14`, `KV1`, `KV3`, `KV5` |
| `14` | `KC2` through `KC8` |
| `15` | `KC9` through `KC13` |
| `16` | Entire wave order |
| `17` | Priority and scope boundaries in this file and issue bodies |

## Issue Body Contract For KC Blocks

Every `KC` issue body follows the same structure:

- Context
- Scope
- Explicit dependencies
- Acceptance Criteria
- Targeted tests
- Docs to sync
- Autopilot Notes

This is intentional: Cursor/Codex should be able to execute one block end-to-end without additional planning work.

## Cursor Autopilot Prompt

```text
Проект VoiceForge. Главный source of truth по новому треку: @docs/voiceforge-copilot-architecture.md и @docs/runbooks/copilot-program-map.md. Статус и active queue: @docs/runbooks/PROJECT-STATUS-SUMMARY.md и @docs/runbooks/next-iteration-focus.md. Planning/process: @docs/runbooks/planning.md. Existing desktop QA policy: @docs/runbooks/desktop-qa-plan.md.

Режим: максимальный автопилот, главный active track = Knowledge Copilot program. Работать только по блокам KC/KV/KD из GitHub Project. KD блоки считать decision-locked. KV блоки не реализовывать кодом, если в issue явно указан внешний/manual gate. Брать один верхний открытый KC-блок, переводить в In Progress, доводить до конца: код -> targeted tests -> docs sync -> GitHub Project -> commit + push -> обновить next-iteration-focus.

Не расширять scope блока за пределы его acceptance criteria. Любой найденный UI/UX баг сразу превращать в отдельный issue только если он не помещается в текущий KC-блок и имеет собственный verification loop.

Перед началом крупного блока: `./scripts/preflight_repo.sh --with-tests`. Для desktop/UI изменений: `cd desktop && npm run e2e:release-gate`. Для native/Tauri/system-level изменений дополнительно: `cd desktop && npm run e2e:native:headless`.

Текущий блок: KC2 · Overlay Shell & Input Model (#174).
```

## Notes For Future Sessions

- `docs/voiceforge-copilot-architecture.md` is not a brainstorming doc anymore; it is the main spec for this track.
- If the source-of-truth document changes, update this file and the affected issue bodies in the same session.
- The maintenance/security backlog remains active, but it does not outrank the Copilot program unless a blocking regression or production-level security problem appears.

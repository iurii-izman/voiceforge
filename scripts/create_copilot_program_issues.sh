#!/usr/bin/env bash
# Create or sync Knowledge Copilot program issues and add them to GitHub Project.
set -euo pipefail

REPO="iurii-izman/voiceforge"
PROJECT_ID="PVT_kwHODvfgWM4BQC-Z"
STATUS_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-R4aU"
PHASE_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeSw"
PRIORITY_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUM"
EFFORT_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUQ"
AREA_FIELD="PVTSSF_lAHODvfgWM4BQC-Zzg-SeUU"

TODO="f75ad846"
IN_PROGRESS="47fc9ee4"
DONE="98236657"
PHASE_OPERATIONAL="c2ee0707"

P0="1016b51c"
P1="b12f98f6"
P2="595114bb"
P3="5759f2a6"

XS="c05c3b37"
S="89ac7c75"
M="10a9e752"
L="4f65026a"

BACKEND="3b82b44a"
DEVOPS="cd368946"
FRONTEND="6bb5ba28"
TESTING="cb342949"
SECURITY="6a0f371d"
AIML="d92aab92"

ensure_label() {
  local name="$1"
  local color="$2"
  local desc="$3"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" --force >/dev/null
  return 0
}

find_issue_number() {
  local title="$1"
  gh issue list --repo "$REPO" --state all --limit 300 --json number,title --jq ".[] | select(.title == \"${title}\") | .number" | head -n1
  return 0
}

find_issue_state() {
  local number="$1"
  gh issue view "$number" --repo "$REPO" --json state --jq .state
  return 0
}

find_item_id() {
  local number="$1"
  gh project item-list 1 --owner iurii-izman --limit 300 --format json --jq ".items[] | select(.content.number==${number}) | .id" | head -n1
  return 0
}

set_project_status() {
  local item_id="$1"
  local status="$2"
  local option_id

  case "$status" in
    TODO) option_id="$TODO" ;;
    IN_PROGRESS) option_id="$IN_PROGRESS" ;;
    DONE) option_id="$DONE" ;;
    *)
      echo "Unknown status: $status" >&2
      return 1
      ;;
  esac

  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$STATUS_FIELD" --single-select-option-id "$option_id" >/dev/null
  return 0
}

ensure_issue() {
  local title="$1"
  local body="$2"
  local labels="$3"
  local priority="$4"
  local effort="$5"
  local area="$6"
  local desired_status="$7"
  local close_issue="$8"

  local number
  number="$(find_issue_number "$title")"
  if [[ -z "$number" ]]; then
    local url
    url="$(gh issue create -R "$REPO" --title "$title" --body "$body" --label "$labels")"
    number="${url##*/}"
  else
    gh issue edit "$number" --repo "$REPO" --title "$title" --body "$body" >/dev/null
    IFS=',' read -r -a label_array <<<"$labels"
    for label in "${label_array[@]}"; do
      gh issue edit "$number" --repo "$REPO" --add-label "$label" >/dev/null
    done
  fi

  local state
  state="$(find_issue_state "$number")"
  if [[ "$desired_status" != "DONE" && "$state" == "CLOSED" ]]; then
    gh issue reopen "$number" --repo "$REPO" >/dev/null
  fi

  local item_id
  item_id="$(find_item_id "$number")"
  if [[ -z "$item_id" ]]; then
    item_id="$(gh project item-add 1 --owner iurii-izman --url "https://github.com/${REPO}/issues/${number}" --format json --jq .id)"
  fi

  set_project_status "$item_id" "$desired_status"
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$PHASE_FIELD" --single-select-option-id "$PHASE_OPERATIONAL" >/dev/null
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$PRIORITY_FIELD" --single-select-option-id "$priority" >/dev/null
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$EFFORT_FIELD" --single-select-option-id "$effort" >/dev/null
  gh project item-edit --project-id "$PROJECT_ID" --id "$item_id" --field-id "$AREA_FIELD" --single-select-option-id "$area" >/dev/null

  if [[ "$close_issue" == "yes" ]]; then
    gh issue close "$number" --repo "$REPO" --reason completed >/dev/null
  fi

  printf '%s\t%s\t%s\n' "$number" "$desired_status" "$title"
  return 0
}

ensure_label "copilot-program" "5319E7" "Knowledge Copilot program track: decisions, autopilot blocks and external gates"

echo "=== Creating Knowledge Copilot program issues ==="

ensure_issue \
"KD1 · Product Charter · Knowledge Copilot" \
"$(cat <<'BODY'
## Context

Knowledge Copilot is now the canonical product framing for VoiceForge. `docs/voiceforge-copilot-architecture.md` is the source of truth for personas, key scenarios, value proposition and the chosen concept.

## Scope

- Lock the product charter around **Knowledge Copilot**
- Preserve the chosen framing: documents-first, real-time augmentation, not a meeting-intelligence red-ocean pivot
- Keep the primary persona focused on presales / solution-architecture usage, while retaining the documented secondary personas

## Locked Decisions

- Primary concept: **Concept A · Knowledge Copilot**
- Core value: fast answers from the user's own documents during a live conversation
- Product value is not generic meeting recording; it is real-time knowledge recall and live assistance

## Traceability

Source sections: `Executive Summary`, `1`, `2`, `3`, `18`
Mapped implementation blocks: `KC1`
BODY
)" \
"copilot-program,decision-locked,primary-track" "$P0" "$XS" "$AIML" "DONE" "yes"

ensure_issue \
"KD2 · UX Contract · Push-to-Capture Calm Technology" \
"$(cat <<'BODY'
## Context

The copilot UX contract is already decided in the architecture document and should not be renegotiated inside implementation blocks.

## Scope

Lock the following UX rules:

- invisible until needed
- push, not pull
- glanceable, not readable
- documents first, model second
- calm technology
- no always-on recording
- no TTS or auto-response
- max 3 visible cards
- progressive disclosure, not dense dashboards

## Traceability

Source sections: `Executive Summary`, `2`, `5`, `6`, `11`, `14`, `17`, `18`
Mapped implementation blocks: `KC2`, `KC3`, `KC6`, `KC7`, `KC12`, `KV2`
BODY
)" \
"copilot-program,decision-locked,primary-track" "$P0" "$XS" "$FRONTEND" "DONE" "yes"

ensure_issue \
"KD3 · Architecture Contract · RAG-First Hybrid Single-Orchestrator" \
"$(cat <<'BODY'
## Context

The high-level architecture for the copilot program is fixed before implementation starts.

## Scope

Lock the following architecture rules:

- RAG-first over LLM-first
- local audio capture and local STT by default
- hybrid deployment default
- mic-only MVP
- single orchestrator with fast/deep tracks, not multi-agent
- evidence-first rendering and groundedness labels

## Traceability

Source sections: `Executive Summary`, `7`, `8`, `9`, `10`, `18`
Mapped implementation blocks: `KC4`, `KC5`, `KC10`, `KC13`
BODY
)" \
"copilot-program,decision-locked,primary-track" "$P0" "$XS" "$BACKEND" "DONE" "yes"

ensure_issue \
"KC1 · Program Bootstrap & Traceability" \
"$(cat <<'BODY'
## Context

Bootstrap the full Knowledge Copilot program so the next implementation block can run on autopilot without additional planning passes.

## Scope

- Add `docs/runbooks/copilot-program-map.md`
- Add `scripts/create_copilot_program_issues.sh`
- Seed KD/KC/KV issues into GitHub Project #1 with Priority / Effort / Area / Status
- Make `docs/voiceforge-copilot-architecture.md` the explicit source of truth for the new track
- Update handoff docs so the active focus leaves maintenance mode and enters the Copilot Program
- Preserve `#164` and `#165` as background hardening backlog

## Explicit Dependencies

- `docs/voiceforge-copilot-architecture.md`
- existing GitHub Project field schema
- existing planning / handoff docs

## Acceptance Criteria

- [ ] All KD/KC/KV blocks exist in GitHub Project
- [ ] KD issues are closed as decision-locked policy artifacts
- [ ] `copilot-program-map.md` contains a full traceability matrix
- [ ] `PROJECT-STATUS-SUMMARY.md` contains a Copilot Program section
- [ ] `next-iteration-focus.md` points to the first executable copilot block

## Targeted Tests

- `bash -n scripts/create_copilot_program_issues.sh`
- `uv run python scripts/check_docs_consistency.py`

## Docs To Sync

- `docs/runbooks/copilot-program-map.md`
- `docs/runbooks/PROJECT-STATUS-SUMMARY.md`
- `docs/runbooks/next-iteration-focus.md`
- `docs/DOCS-INDEX.md`

## Autopilot Notes

This bootstrap block is allowed to reshape the active queue because it installs a new primary program track.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P0" "$M" "$DEVOPS" "DONE" "yes"

ensure_issue \
"KC2 · Overlay Shell & Input Model" \
"$(cat <<'BODY'
## Context

Wave 1 starts with the visible copilot shell: a second window overlay that reacts to hotkey pressed/released input and stays calm under Linux desktop constraints.

## Scope

- second overlay window contract
- always-on-top / no-focus / skip-taskbar behaviour
- hotkey pressed/released flow
- recording indicator
- armed / recording / analyzing / error states
- latest-capture replacement policy
- no focus stealing

## Explicit Dependencies

- `KD2`
- `KD3`
- `KV2`

## Acceptance Criteria

- [ ] overlay window exists as a dedicated shell
- [ ] hotkey press/release states are visible and reversible
- [ ] recording/analyzing/error states are represented in UI
- [ ] latest capture replaces previous overlay state without trap states
- [ ] desktop QA coverage exists for overlay shell behaviour

## Targeted Tests

- `cd desktop && npm run e2e:release-gate`
- `cd desktop && npm run e2e:native:headless`

## Docs To Sync

- `docs/voiceforge-copilot-architecture.md`
- `docs/runbooks/copilot-program-map.md`
- desktop GUI runbooks / release gate docs as needed

## Autopilot Notes

Do not dilute this block with deep pipeline work; this block owns the visible shell and input-state contract.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P0" "$L" "$FRONTEND" "TODO" "no"

ensure_issue \
"KC3 · Capture Runtime & Ring Buffer UX" \
"$(cat <<'BODY'
## Context

Copilot capture uses push-to-capture rather than continuous recording. The runtime contract must feel immediate and privacy-safe.

## Scope

- ring buffer marker model
- pre-roll handling
- segment extraction on release
- auto-stop at 30 seconds with warning state
- transcript snippet during capture where feasible
- UX path for STT ambiguity / ask-to-confirm

## Explicit Dependencies

- `KD2`
- `KC2`

## Acceptance Criteria

- [ ] capture markers and extraction boundaries are deterministic
- [ ] 30-second auto-stop path is implemented with user-visible warning
- [ ] transcript snippet / capture feedback exists without breaking calm-UI rules
- [ ] ambiguity handling path is explicit and testable

## Targeted Tests

- targeted Python capture / meeting tests
- overlay/desktop regression coverage for capture-state transitions

## Docs To Sync

- `docs/voiceforge-copilot-architecture.md`
- capture / setup / doctor runbooks if user-visible behaviour changes

## Autopilot Notes

Keep system-audio and consent work out of this block; that belongs to `KC11` and `KV1`.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P0" "$L" "$BACKEND" "TODO" "no"

ensure_issue \
"KC4 · Streaming STT Copilot Pipeline" \
"$(cat <<'BODY'
## Context

The copilot path needs a short-fragment, low-latency STT slot with partial transcript support.

## Scope

- dedicated tiny STT slot for copilot
- streaming partial transcript flow
- finalize-on-release path
- transcript snippet rendering hooks
- latency budgeting for short captures

## Explicit Dependencies

- `KD3`
- `KC3`

## Acceptance Criteria

- [ ] copilot STT path uses the tiny-model latency budget
- [ ] partial transcript flow exists for short captures
- [ ] release finalization is deterministic
- [ ] transcript snippet is available to downstream fast track and UI

## Targeted Tests

- targeted STT / pipeline tests
- latency-oriented smoke around short fragments

## Docs To Sync

- `docs/voiceforge-copilot-architecture.md`
- copilot program map and relevant architecture/runbooks

## Autopilot Notes

This block optimizes for short, live fragments; do not conflate it with legacy full-meeting transcription quality work.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P0" "$L" "$AIML" "TODO" "no"

ensure_issue \
"KC5 · Evidence-First RAG & Groundedness" \
"$(cat <<'BODY'
## Context

The first useful copilot output is the Evidence Card. Groundedness and citations are core product trust mechanisms.

## Scope

- keyword extraction tuned for short captures
- `confidence_from_results()` / groundedness normalization
- evidence citations with basename + page
- conflict handling for contradictory sources
- grounded / semi-grounded / ungrounded / no-KB fallbacks

## Explicit Dependencies

- `KD3`
- `KC4`

## Acceptance Criteria

- [ ] short-capture query extraction is implemented
- [ ] groundedness classification is explicit and testable
- [ ] evidence citations show source + page when available
- [ ] conflict cases surface clear user-visible wording
- [ ] no-KB fallback path is explicit

## Targeted Tests

- targeted RAG / searcher tests
- regression coverage for groundedness labels and no-KB fallbacks

## Docs To Sync

- `docs/voiceforge-copilot-architecture.md`
- `docs/runbooks/copilot-program-map.md`

## Autopilot Notes

Prefer evidence-first reliability over clever prompt tricks in this block.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P0" "$M" "$AIML" "TODO" "no"

ensure_issue \
"KC6 · Fast Track Cards" \
"$(cat <<'BODY'
## Context

MVP card delivery is driven by the fast-track call plus evidence-first rendering.

## Scope

- structured fast-track schema and prompts
- Answer + Do/Don't + Clarify cards
- streaming render path
- short-token budget for live conversations
- progressive reveal from Evidence -> Answer -> Do/Don't -> Clarify

## Explicit Dependencies

- `KD2`
- `KD3`
- `KC5`

## Acceptance Criteria

- [ ] fast-track schema is implemented and validated
- [ ] Answer / Do / Don't / Clarify render in the expected order
- [ ] streaming render works without breaking calm-UI rules
- [ ] short token budgets keep the fast-track practical for live use

## Targeted Tests

- targeted prompt/router tests
- desktop/UI regression coverage for card render order and states

## Docs To Sync

- copilot architecture doc
- copilot program map
- desktop QA docs if release gate coverage changes

## Autopilot Notes

This closes the MVP core loop together with `KC2-KC5`.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P0" "$M" "$AIML" "TODO" "no"

ensure_issue \
"KC7 · Deep Track & Session Memory" \
"$(cat <<'BODY'
## Context

After MVP core, the copilot needs deeper cards and continuity across sequential captures inside one live session.

## Scope

- conversation memory within session
- Risk + Strategy + Emotion cards
- follow-up cycle behaviour
- card priority rules
- overflow handling

## Explicit Dependencies

- `KC6`

## Acceptance Criteria

- [ ] session memory accumulates across captures in one live conversation
- [ ] deep-track cards render when available without blocking fast-track utility
- [ ] card priority and overflow rules match the UX contract
- [ ] follow-up captures replace or stack correctly

## Targeted Tests

- targeted pipeline/memory tests
- desktop card-priority and overflow regression coverage

## Docs To Sync

- copilot architecture doc
- copilot program map

## Autopilot Notes

Do not add pro-card scope here; keep this block limited to V2 deep-track essentials.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P1" "$L" "$AIML" "TODO" "no"

ensure_issue \
"KC8 · Main Window Copilot Integration" \
"$(cat <<'BODY'
## Context

The main window remains the management surface for sessions, settings and historical context, but it must become copilot-aware.

## Scope

- refactor main window around copilot workflow
- session/detail/history integration
- copilot settings for mode, card types, overlay position, max cards
- groundedness visibility

## Explicit Dependencies

- `KC2`
- `KC6`
- `KC7`

## Acceptance Criteria

- [ ] main window surfaces copilot-generated artefacts coherently
- [ ] settings expose copilot-specific controls
- [ ] groundedness/evidence state is visible in the main-window workflow
- [ ] history/detail flow stays regression-covered

## Targeted Tests

- `cd desktop && npm run e2e:release-gate`
- targeted desktop regression tests around session/detail/settings flows

## Docs To Sync

- desktop README/runbooks
- copilot program map

## Autopilot Notes

This is the bridge between tray/overlay usage and the historical session-management UI.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P1" "$L" "$FRONTEND" "TODO" "no"

ensure_issue \
"KC9 · Knowledge Management & Context Packs" \
"$(cat <<'BODY'
## Context

V2 requires a first-class knowledge-management surface so the copilot can switch between document contexts intentionally.

## Scope

- Knowledge tab
- document list / progress / metadata
- drag-and-drop ingest
- knowledge packs / project contexts
- pinned pack selection

## Explicit Dependencies

- `KC8`

## Acceptance Criteria

- [ ] main window contains a Knowledge management surface
- [ ] users can inspect ingest metadata and progress
- [ ] project-specific context packs are representable and selectable
- [ ] pinning/switching context packs is supported

## Targeted Tests

- targeted desktop/UI tests for knowledge management flows
- targeted ingest/index tests where backend contracts change

## Docs To Sync

- copilot architecture doc
- desktop docs
- copilot program map

## Autopilot Notes

This block owns GUI-first knowledge management; do not bury it inside generic RAG maintenance.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P1" "$L" "$FRONTEND" "TODO" "no"

ensure_issue \
"KC10 · Mode System & Offline/Hybrid Maturity" \
"$(cat <<'BODY'
## Context

Mode handling must become explicit instead of implicit key detection so users can understand cloud / hybrid / offline behaviour.

## Scope

- explicit `copilot_mode`
- mode indicator in UI / overlay
- Ollama fallback behaviour
- cloud / hybrid / offline semantics
- stealth mode
- card history scrollback

## Explicit Dependencies

- `KD3`
- `KC8`

## Acceptance Criteria

- [ ] mode selection is explicit in config/UI
- [ ] overlay/main window show current mode meaningfully
- [ ] fallback behaviour across cloud/hybrid/offline is testable
- [ ] stealth mode and card-history scope are implemented or explicitly guarded within block acceptance

## Targeted Tests

- targeted config/router tests
- desktop/UI tests for mode indicators and settings

## Docs To Sync

- copilot architecture doc
- config / install / desktop runbooks
- copilot program map

## Autopilot Notes

Mode semantics must stay honest; do not imply offline parity where only degraded behaviour exists.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P1" "$L" "$BACKEND" "TODO" "no"

ensure_issue \
"KC11 · System Audio & Scenario Presets" \
"$(cat <<'BODY'
## Context

This wave expands beyond mic-only MVP and needs explicit consent and scenario-layer UX.

## Scope

- opt-in system audio path
- monitor source selector
- per-session consent UX
- scenario presets for demo / negotiation / support
- question intent classification

## Explicit Dependencies

- `KV1`
- `KC10`

## Acceptance Criteria

- [ ] system-audio path is opt-in and technically selectable
- [ ] consent UX exists before capture expands beyond mic-only
- [ ] presets for documented scenario classes exist
- [ ] intent classification is wired into preset/card behaviour where needed

## Targeted Tests

- targeted audio/config tests
- desktop/UI regression coverage for consent and scenario selection

## Docs To Sync

- copilot architecture doc
- legal/privacy-facing runbooks as applicable
- copilot program map

## Autopilot Notes

Do not start this block until `KV1` is explicitly resolved.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P2" "$L" "$BACKEND" "TODO" "no"

ensure_issue \
"KC12 · Pro Cards & Answer Refinement" \
"$(cat <<'BODY'
## Context

This block extends the card system beyond the MVP/V2 core into optional pro-mode refinement features.

## Scope

- Objection / Opportunity if retained
- Deep Answer on demand
- tone switch
- quick rewrite
- follow-up suggestions
- auto-save snippets

## Explicit Dependencies

- `KC7`
- `KC10`

## Acceptance Criteria

- [ ] optional pro-card/refinement features are implemented without degrading calm-UI defaults
- [ ] expandable/deeper answer paths are on-demand, not forced
- [ ] rewritten/tone-switched answers preserve source grounding semantics

## Targeted Tests

- targeted prompt/router tests
- desktop/UI regression coverage for on-demand deep-answer and rewrite flows

## Docs To Sync

- copilot architecture doc
- copilot program map

## Autopilot Notes

This block is allowed to trim optional scope if the architecture source of truth is updated, but only by explicit docs sync.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P2" "$L" "$AIML" "TODO" "no"

ensure_issue \
"KC13 · Adaptive Intelligence & Extensibility" \
"$(cat <<'BODY'
## Context

V3 frontier work covers adaptive behaviour and extensibility contracts after the core copilot loop is stable.

## Scope

- adaptive model selection
- plugin/API system
- contradiction detection
- speaker profiles
- jargon simplifier
- extensibility contracts

## Explicit Dependencies

- `KV5`
- `KC10`
- `KC12`

## Acceptance Criteria

- [ ] adaptive/extensibility frontier is implemented behind stable contracts
- [ ] any platform-frontier work obeys the explicit gate from `KV5`
- [ ] no MVP/V2 guarantees regress because of frontier experimentation

## Targeted Tests

- targeted backend/router/plugin tests
- platform smoke only where scope explicitly allows it

## Docs To Sync

- copilot architecture doc
- ADR/runbooks as architecture expands
- copilot program map

## Autopilot Notes

This block should not start until the platform-expansion gate is resolved.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P3" "$L" "$AIML" "TODO" "no"

ensure_issue \
"KC14 · Copilot QA, Release, Performance & Reliability" \
"$(cat <<'BODY'
## Context

The final program wave hardens the copilot path as a releasable desktop product.

## Scope

- overlay-specific e2e/native smoke
- latency harness and benchmark thresholds
- battery / CPU controls
- lazy model unload after idle
- failure UX
- observability and release evidence for the copilot path

## Explicit Dependencies

- `KC2` through `KC13` as applicable

## Acceptance Criteria

- [ ] copilot-specific release gate exists and is honest
- [ ] latency/perf budgets are measurable
- [ ] failure UX is explicit under the documented risk model
- [ ] battery/CPU controls and idle-unload policy are implemented

## Targeted Tests

- `./scripts/preflight_repo.sh --with-tests`
- desktop release gate
- targeted latency/perf smoke for the copilot path

## Docs To Sync

- release and quality runbooks
- observability/performance docs
- copilot program map

## Autopilot Notes

This block closes the program only after both user-visible reliability and release evidence are in place.
BODY
)" \
"copilot-program,autopilot,primary-track" "$P1" "$L" "$TESTING" "TODO" "no"

ensure_issue \
"KV1 · Legal & Consent Policy" \
"$(cat <<'BODY'
## Context

System audio, consent wording and retention language carry legal and trust consequences that cannot be auto-finalized by engineering alone.

## Manual Gate

- system-audio disclaimer and consent wording
- jurisdiction-specific recording guidance
- retention wording and privacy text

## Blocked Follow-Up

- `KC11`

## Completion Condition

User/project owner explicitly confirms the legal/privacy wording and acceptable scope for system-audio capture.
BODY
)" \
"copilot-program,user-decision,operational" "$P1" "$M" "$SECURITY" "TODO" "no"

ensure_issue \
"KV2 · Overlay UX Sign-Off" \
"$(cat <<'BODY'
## Context

The overlay is the primary visible surface of Knowledge Copilot. Visual direction and intrusiveness need a human sign-off before the shell is treated as complete.

## Manual Gate

- overlay visual direction
- card density
- motion and animation intensity
- perceived intrusiveness during live work

## Blocked Follow-Up

- `KC2` final acceptance

## Completion Condition

User explicitly approves the overlay UX direction after live review.
BODY
)" \
"copilot-program,user-decision,operational" "$P0" "$S" "$FRONTEND" "TODO" "no"

ensure_issue \
"KV3 · Pilot Validation With Primary Persona" \
"$(cat <<'BODY'
## Context

After MVP core cards exist, the product needs validation with the actual primary persona rather than only internal engineering judgment.

## Manual Gate

- presales / support style pilot sessions
- usefulness of Evidence / Answer / Do-Don't cards
- validation of value proposition under real pressure

## Blocked Follow-Up

- `KC14` confidence for release positioning

## Completion Condition

Real user/pilot feedback is captured and the program backlog is adjusted explicitly if needed.
BODY
)" \
"copilot-program,user-decision,operational" "$P1" "$M" "$TESTING" "TODO" "no"

ensure_issue \
"KV4 · Business & Packaging Gate" \
"$(cat <<'BODY'
## Context

Commercial framing and packaging boundaries affect how the copilot mode system and delivery artefacts should be positioned.

## Manual Gate

- pricing / self-hosted / SaaS framing
- enterprise versus local-product packaging boundaries
- commercial positioning after the new product charter

## Blocked Follow-Up

- commercial packaging beyond local/dev flows
- architecture section on deployment packaging assumptions

## Completion Condition

User/project owner explicitly decides the business/packaging direction for the copilot track.
BODY
)" \
"copilot-program,user-decision,operational" "$P2" "$M" "$DEVOPS" "TODO" "no"

ensure_issue \
"KV5 · Platform Expansion Gate" \
"$(cat <<'BODY'
## Context

Windows/macOS/platform-frontier work has real support consequences. The architecture document requires an explicit go/no-go before expanding platform scope.

## Manual Gate

- go/no-go on Windows/macOS investigation
- support commitments and platform boundaries
- what counts as experimental versus supported

## Blocked Follow-Up

- `KC13`

## Completion Condition

User/project owner explicitly approves or rejects platform expansion work.
BODY
)" \
"copilot-program,user-decision,operational" "$P2" "$M" "$DEVOPS" "TODO" "no"

# KC13: Adaptive Intelligence & Extensibility (Contracts)

**Scope (KC13 #185):** Adaptive model selection, plugin/API system, contradiction detection, speaker profiles, jargon simplifier, extensibility contracts. **KV5 resolved:** Linux-only; no platform expansion.

**Updated:** 2026-03-14.

---

## 1. Stable contracts (no MVP/V2 regression)

- **Adaptive model selection:** Implemented via `get_effective_llm()` (config + `copilot_mode`) and LLM router fallback. Extension point: config fields and keyring; no code change required for new providers beyond router.
- **Plugin/API system:** Contract: future plugins register via a single entry point (e.g. `voiceforge.copilot.plugins` or config-driven hooks). Not implemented as a loadable plugin runtime in KC13; only the contract and doc are in place. No regression: existing pipeline is unchanged.
- **Contradiction detection / speaker profiles / jargon simplifier:** Documented as future extension points; optional pipeline steps that can be wired when implemented. No stub in critical path; add behind feature flags or config when needed.

---

## 2. Linux-only (KV5)

All KC13 work is within the existing Linux desktop/daemon stack. No Windows/macOS or new platforms.

---

## 3. Extension points (reference)

| Area | Current | Extension |
|------|---------|-----------|
| Model selection | `config.get_effective_llm()`, router fallback | Add provider in router; config/keyring for keys |
| Scenario preset | `copilot_scenario_preset` (KC11) | Use in prompts or card logic |
| Plugins | — | Future: register hooks (pre/post analyze, custom cards) via config or entry points |
| Contradiction | — | Future: optional step after RAG/LLM; schema + prompt |
| Speaker profiles | — | Future: optional diarization enrichment |
| Jargon | — | Future: optional post-step or prompt hint |

---

## 4. Targeted tests

- Backend/router tests: existing coverage for `get_effective_llm`, router fallback.
- No new plugin runtime tests until plugins are implemented; contract is doc-only.

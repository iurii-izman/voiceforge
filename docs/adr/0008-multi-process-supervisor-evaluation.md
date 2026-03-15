# ADR-0008: Multi-process supervisor evaluation — no split at current scale

Status: Accepted (defer — 2026-03-15)

Part of Epic: #193. Closes #205.

## Context

VoiceForge runs a single Python daemon (`voiceforge daemon`) under systemd (ADR-0007). This issue evaluates whether and when to split the daemon into multiple processes (e.g. STT worker, RAG indexer, fast-path copilot) and what supervisor layer would be needed.

## Recommendation

**No split at current scale.** Keep the single-process daemon. Re-evaluate only when one or more of the following triggers are met:

| Trigger | Threshold / condition |
|--------|------------------------|
| Memory | Daemon consistently uses > 3GB RAM |
| UI lag | Users report UI lag during STT processing |
| Copilot latency | Copilot latency > 200ms due to daemon load |
| GPU STT | Need to run STT on GPU in a separate process |

Until then, no multi-process architecture or new supervisor layer is justified.

## If split is needed later

1. **Supervisor option:** Prefer **systemd (multiple units)** or **systemd target group** — we already use systemd; adding units (e.g. `voiceforge-stt.service`, `voiceforge-daemon.service`) keeps one stack. Avoid Python supervisors (circus, etc.) and custom process managers.
2. **IPC:** D-Bus for control/status (already in place); consider Unix sockets or shared memory for high-throughput streams only if profiling shows need.
3. **Single entry point for UI:** Tauri app continues to talk to one primary D-Bus service that can proxy or aggregate; no change to UI contract.
4. **Coordinated startup:** systemd `After=` / `Requires=` or a target unit; no in-app orchestration.

## References

- Epic #193 (Runtime Control Panel)
- ADR-0007 (systemctl + D-Bus, no custom supervisor)
- Issue #205 (this evaluation deliverable)

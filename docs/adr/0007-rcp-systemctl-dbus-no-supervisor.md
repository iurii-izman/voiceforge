# ADR-0007: Runtime Control Panel — systemctl + D-Bus, no custom supervisor, no manifest

Status: Accepted (LOCKED — 2026-03-14)

Part of Epic: #193. Refs #194.

## Context

Runtime Control Panel (RCP) must manage daemon lifecycle (start/stop/restart), show status, run health checks (Doctor), and provide diagnostics. Options considered: custom process supervisor inside the app, OS-native only (systemctl), separate launcher binary, manifest-driven orchestration.

## Decision

**Variant A: UI → systemctl + D-Bus** is adopted:

1. **Tauri app** controls daemon lifecycle via `systemctl --user start/stop/restart voiceforge`.
2. **D-Bus IPC** is used for monitoring (Ping, Status, Doctor) — already implemented / to be extended.
3. **systemd** is the process supervisor — already configured (`Restart=on-failure`, `WatchdogSec=60`, `MemoryMax=4G`).
4. **Do not build** a custom process supervisor — systemd does this better.
5. **Do not build** a declarative runtime manifest — one daemon, one config (`voiceforge.yaml` + `voiceforge.service`).
6. **Do not embed** a terminal emulator in the app — use an external terminal for “debug in terminal”.

## Comparison (rationale)

| Criterion        | A: UI→systemctl ✅ | B: Internal supervisor | C: OS-native only | D: Separate launcher | E: Manifest-driven |
|------------------|--------------------|------------------------|-------------------|----------------------|--------------------|
| Simplicity       | ★★★★★              | ★★☆☆☆                  | ★★★★☆             | ★★☆☆☆                | ★☆☆☆☆              |
| Reliability      | ★★★★☆              | ★★★☆☆                  | ★★★★★             | ★★★☆☆                | ★★★☆☆              |
| Debugging        | ★★★★☆              | ★★★☆☆                  | ★★★★☆             | ★★☆☆☆                | ★★☆☆☆              |
| UX               | ★★★★☆              | ★★★★☆                  | ★★★☆☆             | ★★★★★                | ★★★☆☆              |
| Support cost     | ★★★★★              | ★★☆☆☆                  | ★★★★★             | ★★☆☆☆                | ★☆☆☆☆              |
| Dev/debug compat | ★★★★★              | ★★★☆☆                  | ★★★★☆             | ★★★☆☆                | ★★☆☆☆              |

## Rejected alternatives

- **B (Internal supervisor):** Embedding a supervisor in the Tauri app makes the frontend infrastructure. App crash → supervisor crash. Update app → restart all services. Anti-pattern.
- **D (Separate launcher):** A separate launcher binary is for a fleet of services. We have one daemon. YAGNI.
- **E (Manifest-driven):** Declarative manifest (services, commands, startup order, readiness probes) is for multi-service orchestration. `voiceforge.yaml` + `voiceforge.service` already cover our needs.

## Top-10 locked decisions

| # | Decision              | Answer                    | Reason |
|---|------------------------|---------------------------|--------|
| 1 | Custom supervisor?     | **No**                    | Months of work, worse than systemd |
| 2 | Status: polling vs push? | **Polling (ping 5s)**   | Push requires alive daemon; we need to detect death |
| 3 | First-run: auto-install? | **Ask user**            | Transparency, trust |
| 4 | Panel: separate window? | **No, Settings tab**     | Avoid extra window management |
| 5 | Daemon control: D-Bus or systemctl? | **systemctl lifecycle, D-Bus data** | D-Bus stop = no reply; systemctl = external control |
| 6 | Distrobox: hardcode?    | **Parameterize**          | Not all users run in distrobox (#206) |
| 7 | Terminal emulator in app? | **No**                  | xterm.js heavy, VTE = native GTK; cost >> value |
| 8 | Status format?         | **Structured JSON**       | Need failure reasons, not just colours |
| 9 | When updater?          | **When signing keys ready** | Broken updater worse than none (#207) |
| 10 | Doctor checks blocking? | **Advisory**            | Do not block startup on optional deps |

## When to revisit

- If VoiceForge targets macOS → need launchd adapter (see #149).
- If daemon is split into multiple processes → revisit supervisor approach.
- If user count > 50 → revisit auto-update strategy.

## Consequences

- RCP implementation follows this ADR: systemctl for lifecycle, D-Bus for status/Doctor.
- Manual gates: #206 (Distrobox parameterization), #207 (signing keys for updater) remain separate.

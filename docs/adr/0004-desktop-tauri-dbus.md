# ADR-0004: Desktop UI = Tauri + D-Bus; daemon as single backend

Status: Accepted

## Context

- VoiceForge has a Python daemon (`voiceforge daemon`) that exposes D-Bus interface `com.voiceforge.App` (Analyze, GetSessions, GetSettings, Listen start/stop, signals, etc.).
- A separate `voiceforge web` HTTP server runs the pipeline and DB directly, duplicating logic and not using D-Bus.

## Decision

- **Desktop UI** is implemented as a **Tauri 2** application (Rust + system WebView). On Linux: WebKitGTK; no Electron; small binary footprint.
- The **only backend for the desktop GUI is the daemon**. The Tauri app is a **D-Bus client only**: it calls methods and subscribes to signals. No embedded Python, no HTTP server inside the app.
- **Browser UI** (`voiceforge web`) remains **optional**: for “CLI + browser only” or remote access without building Tauri. It is not the focus of the alpha2 release; new features are implemented first in the Tauri (D-Bus) desktop. It may be removed later to reduce maintenance surface.
- Tauri build dependencies: Rust toolchain, `webkit2gtk` (and dev packages). On Fedora Atomic, build inside toolbox with Tauri/GTK dev packages installed.

## Consequences

- Single source of truth: all desktop features go through D-Bus to the daemon.
- No logic duplication between daemon and desktop; contract is documented (envelope, methods, signals).
- Optional web UI keeps a fallback path without requiring a Tauri build.

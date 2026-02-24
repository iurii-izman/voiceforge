# VoiceForge installation and run guide

Short full guide: where to run, when to rebuild, how to start the daemon, and how to update.

---

## 0. Working only inside toolbox (recommended)

To avoid installing the environment on both host and container, do **everything inside a single toolbox**: CLI, daemon, desktop build and run. The repo on the host is available in the container at the same path (home directory is mounted).

**Where to type:** in the commands below, **"Host"** or **"In toolbox"** indicates which terminal to use (on Fedora host or already inside the container).

---

### Step 0.1. Check if a container already exists

**Host** (terminal on Fedora, not in container):

```bash
toolbox list
```

If you see a container (e.g. `fedora-toolbox-43` or `fedora-toolbox-40`) — you can enter it. If the list is empty — create a container (step 0.2).

---

### Step 0.2. Create a container (if none exists)

**Host:**

```bash
toolbox create
```

The default name will be something like `fedora-toolbox-43` (from the image version). Remember it or run `toolbox list` again.

---

### Step 0.3. Enter the container

**Host:**

```bash
toolbox enter
```

If you have multiple containers, specify the name:

```bash
toolbox enter fedora-toolbox-43
```

(substitute your name from `toolbox list`). After entering, the prompt may change (e.g. show the container name) — from then on run all commands **in this same terminal (in toolbox)**.

---

### Step 0.4. Install VoiceForge inside toolbox

**In toolbox** (same terminal you entered):

```bash
cd /var/home/user/Projects/voiceforge
./scripts/bootstrap.sh
```

Wait for it to finish (configure keyring here if needed: `keyring set voiceforge anthropic`, etc.).

For audio recording (`voiceforge listen`) in the container you need `pw-record`:

**In toolbox:**

```bash
sudo dnf install -y pipewire-utils
```

Then install desktop build dependencies:

**In toolbox:**

```bash
./scripts/setup-desktop-toolbox.sh
```

Check the environment:

**In toolbox:**

```bash
./scripts/check-desktop-deps.sh
uv run voiceforge status   # or voiceforge doctor — config, keyring, RAG, Ollama diagnostics
```

If all checks are [OK] — you can build the desktop and run CLI/daemon **only from this container**. You do not need to install anything else for VoiceForge on the host.

---

### Step 0.5. Daily workflow: toolbox only

- **Host:** run `toolbox enter` once (or `toolbox enter CONTAINER_NAME` if needed).
- **In toolbox:**
  `cd /var/home/user/Projects/voiceforge`
  then, for example:
  `uv run voiceforge daemon` (in one terminal),
  in another terminal run `toolbox enter` again → `cd /var/home/user/Projects/voiceforge` → `uv run voiceforge listen` or start the desktop (`cd desktop && npm run tauri dev`).

Summary: **on the host** you only enter the container (`toolbox enter`). **Everything else** runs inside toolbox, under `/var/home/user/Projects/voiceforge`.

---

## 1. Where and how to run

### CLI (voiceforge commands)

- **Environment:** Fedora Atomic or regular Fedora; convenient to develop in **toolbox** (or distrobox). One environment is recommended — see section 0 above.
- **From repo (no system install)** — run commands **in toolbox** (or on host if you chose to install there too):
  ```bash
  cd /var/home/user/Projects/voiceforge
  ./scripts/bootstrap.sh   # once
  uv sync --extra all      # when dependencies change
  uv run voiceforge <command>
  ```
- **Running on host:** the same commands can be run on the host if `uv`, Python, and keyring keys (service `voiceforge`, names `anthropic`, `openai`, `huggingface`) are set up there. For a single environment, toolbox-only is better — then nothing is installed on the host.

### Desktop (Tauri)

- **Build** is done in an environment with gcc, Node, Rust, WebKit/GTK (on Atomic — in **toolbox**):
  ```bash
  cd /path/to/voiceforge
  ./scripts/setup-desktop-toolbox.sh   # once
  ./scripts/check-desktop-deps.sh     # check
  cd desktop && npm run tauri build
  ```
  Equivalent: `cd desktop && npm run build && cargo tauri build`.
- **Where to run the app:** built binary — `desktop/src-tauri/target/release/voiceforge-desktop`; packages (.rpm, .deb) — in `desktop/src-tauri/target/release/bundle/rpm/` and `bundle/deb/`. You can run **on the host** or in the same toolbox — the same D-Bus session as the daemon is required (see below).
- **Run without installing:** `./desktop/src-tauri/target/release/voiceforge-desktop` (from repo root). Or install the package: Fedora — `sudo dnf install desktop/src-tauri/target/release/bundle/rpm/VoiceForge-*.rpm`; Debian/Ubuntu — `sudo dpkg -i desktop/.../bundle/deb/VoiceForge_*.deb`. See [desktop-build-deps.md](desktop-build-deps.md) (section «Installation and run after build») for details.

---

## 2. When to rebuild after changes

| What changed | Action |
|--------------|--------|
| Python only (backend, CLI) | Restart daemon and/or `uv run voiceforge ...`; desktop rebuild not needed. |
| Frontend (Vite/TS/UI in `desktop/`) or Tauri (Rust in `desktop/src-tauri/`) | Rebuild desktop: `cd desktop && npm run build && cargo tauri build`. For iteration, **dev mode** is easier: `cd desktop && npm run tauri dev` (restarts on frontend changes). |
| Tauri config / npm or Cargo dependencies | After changing dependencies: `npm install` in `desktop/`, then `cargo build` in `desktop/src-tauri/` if needed, then full build. |

Summary: after Python-only changes — no desktop rebuild. After changes in `desktop/` — either `npm run tauri dev` or full `npm run tauri build`.

---

## 3. How to run “all daemons”

VoiceForge has **one daemon** — the `voiceforge daemon` process. It serves both CLI and desktop (via D-Bus).

- **Manually (separate terminal):**
  ```bash
  cd /path/to/voiceforge
  uv run voiceforge daemon
  ```
  Or, if voiceforge is installed in the environment: `voiceforge daemon`.
- **As a user systemd service:** `voiceforge install-service` and `voiceforge uninstall-service` (see project docs for the service).
- Before starting the **desktop app**, the daemon must already be running; otherwise the app will show a hint «Start the daemon: voiceforge daemon».

---

## 4. Quick update

- **Update code and dependencies:**
  ```bash
  cd /path/to/voiceforge
  git pull
  uv sync --extra all
  ```
- **Desktop:** if only Python/backend changed — restarting the daemon is enough. If `desktop/` (frontend or Tauri) changed — rebuild:
  ```bash
  cd desktop && npm install && npm run build && cargo tauri build
  ```
- **Quick UI iteration:** do not build a release every time — use `cd desktop && npm run tauri dev` (daemon must be running).

---

## See also

- [quickstart.md](quickstart.md) — quick steps for the first meeting
- [desktop-build-deps.md](desktop-build-deps.md) — dependencies and environment check for desktop build
- [config-env-contract.md](config-env-contract.md) — environment variables and keyring
- [pyannote-version.md](pyannote-version.md) — on OOM or diarization crashes (rollback to 3.3.2)

# VoiceForge documentation

Single entry point for all docs. **Index and freshness:** [DOCS-INDEX.md](DOCS-INDEX.md).

**English:** [en/README.md](en/README.md) — first meeting, installation, quickstart (EN).

---

## Start

| For whom | Document |
| -------- | -------- |
| **First run (5 min)** | [first-meeting-5min.md](first-meeting-5min.md) |
| **Short scenario** | [runbooks/quickstart.md](runbooks/quickstart.md) |
| **Install & toolbox** | [runbooks/installation-guide.md](runbooks/installation-guide.md) |
| **Rebuild & test (toolbox)** | [runbooks/rebuild-run-test-guide.md](runbooks/rebuild-run-test-guide.md) |
| **Agent (Cursor/Claude)** | [runbooks/agent-context.md](runbooks/agent-context.md), [runbooks/next-iteration-focus.md](runbooks/next-iteration-focus.md) |

---

## Product & architecture

- **Knowledge Copilot (product/arch):** [voiceforge-copilot-architecture.md](voiceforge-copilot-architecture.md)
- **Program map (traceability):** [runbooks/copilot-program-map.md](runbooks/copilot-program-map.md)
- **Technical architecture:** [architecture/README.md](architecture/README.md), [architecture/overview.md](architecture/overview.md)

---

## Config & keys

- [runbooks/config-env-contract.md](runbooks/config-env-contract.md) — env, config file, D-Bus
- [runbooks/keyring-keys-reference.md](runbooks/keyring-keys-reference.md) — keyring keys (anthropic, openai, etc.)

---

## Desktop (Tauri)

- **Build (toolbox):** [runbooks/desktop-build-deps.md](runbooks/desktop-build-deps.md), `./scripts/setup-desktop-toolbox.sh`
- **Install & run:** [runbooks/installation-guide.md](runbooks/installation-guide.md)
- **Rebuild & test:** [runbooks/rebuild-run-test-guide.md](runbooks/rebuild-run-test-guide.md)
- Before running desktop: start **voiceforge daemon**

---

## Runbooks (full list)

Operational guides — [runbooks/README.md](runbooks/README.md). Full catalog: [DOCS-INDEX.md](DOCS-INDEX.md).

- **Context & agent:** agent-context, next-iteration-focus, cursor, ai-tooling-setup
- **Config & env:** config-env-contract, keyring-keys-reference, bootstrap, installation-guide, desktop-build-deps
- **Security & deps:** security-and-dependencies, security-decision-log
- **Release & quality:** release-and-quality, repo-and-git-governance
- **Features:** telegram-bot-setup, pyannote-version, calendar-integration, rag-formats

---

## Plans & status

- [plans.md](plans.md) — roadmap, Phase A–D
- [runbooks/PROJECT-STATUS-SUMMARY.md](runbooks/PROJECT-STATUS-SUMMARY.md) — status, Copilot program, hardening
- [audit/audit.md](audit/audit.md) — audit snapshot
- Archive: [archive/README.md](archive/README.md)

---

## ADR

Architecture decisions: [adr/README.md](adr/README.md). Active: 0001 (core scope), 0002 (action items), 0003 (version reset), 0004 (desktop Tauri D-Bus), 0005 (Telegram bot).

# Security Runbook

**Объединён с dependencies и dependabot-review.** Актуальный документ: [security-and-dependencies.md](security-and-dependencies.md).

## E17 #140: Security hardening (optional)

- **SQLite encryption:** Set `encrypt_db: true` in config (or `VOICEFORGE_ENCRYPT_DB=true`). Store key: `keyring set voiceforge db_encryption_key`. Requires optional dependency: `uv sync --extra security` (sqlcipher3). See [security-and-dependencies.md](security-and-dependencies.md) § E17.
- **API key audit log:** Every keyring read is logged to structlog and to `metrics.db` table `api_key_access` (timestamp, key_name, operation). No configuration needed.
- **AppArmor:** Template profile in `security/voiceforge.apparmor`. Install: `sudo cp security/voiceforge.apparmor /etc/apparmor.d/voiceforge` then `sudo apparmor_parser -r /etc/apparmor.d/voiceforge`. Adjust binary path in the profile if running from venv.

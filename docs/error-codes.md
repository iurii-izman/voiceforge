# VoiceForge Error Codes (E14 #137)

Canonical codes for CLI and IPC. Each structured error includes `code`; see `src/voiceforge/core/contracts.py` (`ErrorCode` enum).

| Code | Description | Cause | Fix |
|------|-------------|-------|-----|
| **VF001** | Session not found | Requested session ID does not exist in DB | Check `voiceforge history`; use valid `--id`. |
| **VF002** | Analyze failed | LLM/STT/diarization or pipeline error during analyze | Check keyring (anthropic/openai), logs; retry. |
| **VF003** | Analyze timeout | analyze() exceeded `analyze_timeout_sec` | Increase timeout in config or shorten audio. |
| **VF010** | Budget exceeded | Daily LLM budget limit reached | Wait for next day or raise `daily_budget_limit_usd`. |
| **VF020** | CalDAV upcoming failed | Could not fetch upcoming events | Check keyring: caldav_url, caldav_username, caldav_password. |
| **VF021** | CalDAV list failed | Could not list calendars | Same as VF020; verify CalDAV URL and credentials. |
| **VF022** | CalDAV poll failed | Poll for events in time window failed | Same as VF020; check network and calendar server. |
| **VF023** | CalDAV create event failed | Creating event from session failed | Same as VF020; check write permissions on calendar. |
| **VF030** | Config invalid | Invalid voiceforge.yaml or env value | Fix config; see docs/runbooks/config-env-contract.md. |
| **VF031** | Keyring missing | Required API key not in keyring (voiceforge) | Run `voiceforge setup` or set key in keyring. |
| **VF099** | Generic error | Unclassified runtime error | Check logs; report with code and message. |

Reserved range: VF001–VF050. New codes added in order; document here and in `contracts.ErrorCode`.

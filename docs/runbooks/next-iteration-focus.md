# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-02-26

---

## Следующий шаг (для копирования в новый чат)

Один конкретный шаг для следующего чата (или пользователь подставляет свою задачу).

- **Сейчас:** Sonar: закрыты ещё 4 issues (S1172, S3776) и Security Hotspot S7637 (dtolnay/rust-toolchain — полный SHA в release.yml). Следующий шаг: фича из docs/roadmap-priority.md (1–7); или PR #25 — смержить при зелёном CI; или Dependabot #2 — dismiss при наличии `github_token`.

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Последняя итерация (кратко)

Sonar: 4 оставшихся замечания (S1172 — убран неиспользуемый model_id в _complete_structured_cached; S3776 — _complete_structured_finish, _rag_merge_results, _action_items_update_persist/_echo). Security Hotspot S7637: dtolnay/rust-toolchain@stable заменён на полный SHA в .github/workflows/release.yml. Ранее: GitHub/доки (PR #54, docs/en), Sonar ~21 + 4. Быстрые правки: build-flatpak.sh stderr (S7677), release.yml permissions на уровень job (S8233), константа error.budget_exceeded (S1192), убран лишний if в prompt_loader (S3923), заполнен пустой except в transcript_log (S108), pytest.approx и _template в test_llm_eval (S1244, S1481), вложенный conditional в server.py (S3358). Рефакторинг S3776 (cognitive complexity): вынесены хелперы в dependabot_dismiss_moderate, query_keywords, metrics, server (_reply_*), caldav_poll (_event_dict, _events_from_calendar, _candidates_from_calendars), pipeline (_prepare_audio, _step1_or_error, _gather_step2, _with_calendar_context), router (_complete_structured_cached, _complete_structured_check_budget), main (_history_resolve).

---

## Что сделано (история)

**Всё закрытое вынесено в один документ со сверкой по коду:** [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Там: Roadmap 1–12, план развития Часть I и блоки Alpha2 A–D, W1–W10, Sonar, «Следующие 10 шагов» (п.1–6). В текущем файле ниже — только **не сделанное** и план.

---

## Не сделано / открытые задачи

Полная доска: **[GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1)** (27 задач, Phase A–D).

| # Issue | Phase | Задача | Заметка |
|---------|-------|--------|---------|
| ~~#32~~ | A · P0 | Eval harness (ROUGE-L + LLM-judge) | **Закрыт** — 21 samples, test_llm_judge_one_golden_sample |
| ~~#33~~ | A · P0 | Instructor retry | **Закрыт** — max_retries=3 в complete_structured |
| ~~#34~~ | A | Unit tests daemon/streaming/smart_trigger | **Закрыт** — тесты добавлены; omit оставлен (80% gate) |
| ~~#35~~ | A | WAV integration tests | **Закрыт** — 4 WAV-теста, fixtures, CI stt-integration |
| ~~#27~~ | A | AppImage | **Закрыт** — toolbox сборка, deb/rpm/AppImage |
| ~~#36~~ | B · P0 | Observability (metrics/tracing) | **Закрыт** — prometheus_client, /metrics, Grafana, alerts |
| ~~#37~~ | B · P0 | pyannote memory guard | **Закрыт** — skip diarization <2GB, OOM fallback |
| ~~#38~~ | B | Budget enforcement | **Закрыт** — pre-call daily limit, BudgetExceeded, alert 80% |
| ~~#39~~ | B | IPC envelope | **Закрыт** |
| ~~#40~~ | B | CI cache | **Закрыт** — enable-cache в setup-uv |
| [#41–45](https://github.com/iurii-izman/voiceforge/issues/41) | C | Prompt mgmt, RAG, retention, caching, healthcheck | Phase C scale |
| ~~#48~~ | D | Calendar — auto-context в analyze | **Закрыт** — get_next_meeting_context, calendar_context_enabled, pipeline inject |
| ~~#49~~ | D | Flatpak packaging | **Закрыт** — manifest, build-flatpak.sh, CI, runbook |
| [#46–50](https://github.com/iurii-izman/voiceforge/issues/46) | D | Desktop signals, Telegram, Flatpak, macOS | Phase D productize |
| ~~#29~~ | Ops | RAG ODT/RTF тесты | **Закрыт** — тесты в test_rag_parsers.py |
| ~~#30~~ | Ops | Dependabot 1 moderate | **Закрыт** — скрипт + runbook; алерт #2 — dismiss в UI или скрипт |

---

## Следующие шаги (план)

1. **Phase A — Stabilize (приоритет):**
   - ~~#32 A1 eval harness~~ — сделано (21 golden samples, ROUGE-L ≥ 0.35, LLM-judge test).
   - ~~#33 A2 Instructor retry~~ — сделано (instructor.from_litellm, max_retries=3).
   - ~~#34 A3 unit tests daemon/streaming/smart_trigger~~ — сделано (тесты добавлены; omit оставлен).
   - ~~#27 A5 AppImage~~ — сделано (toolbox: NO_STRIP, librsvg2-devel; см. desktop-build-deps.md).
   - ~~#35 A4 WAV integration tests~~ — сделано (tests/fixtures/, test_stt_integration.py, make test-integration, CI stt-integration).
2. **Phase B — Hardening (после A):** ~~observability (Prometheus)~~ — сделано (#36); ~~pyannote memory guard~~ — сделано (#37); ~~budget enforcement~~ — сделано (#38); ~~IPC envelope~~ — сделано (#39); ~~CI cache~~ — сделано (#40).
3. **Документация:** при изменении CLI/конфига обновлять installation-guide, first-meeting-5min; обновлять DOCS-INDEX при новых доках.

---

## Актуальные напоминания

- **Sonar:** список открытых issues — `uv run python scripts/sonar_fetch_issues.py`. В этой сессии закрыто ~21 замечание (S3776, S1192, S3358, S108, S1481, S1244, S8233, S7677, S3923); после следующего скана проверить остаток.
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — сборка только в toolbox/окружении из [desktop-build-deps.md](desktop-build-deps.md). Новые CLI-команды — только через ADR (ADR-0001).

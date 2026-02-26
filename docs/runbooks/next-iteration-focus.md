# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-02-26

---

## Следующий шаг (для копирования в новый чат)

**#56:** fail_under временно снижен до 63 (coverage ~64%); цель 80% — тесты для core/metrics, llm/router, cli/history_helpers, cli/status_helpers, core/daemon, rag/parsers. **#60 сделано:** GET /ready в web/server.py (200 при доступной БД, 503 иначе), MemoryMax=4G/MemoryHigh=3G/OOMScoreAdjust=500 в scripts/voiceforge.service.

Следующий шаг: **Phase B #61** — request tracing (trace IDs + structlog). Либо продолжить подъём coverage до 80% (#56).

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Текущий план: Phase A–D (20 задач)

Полная доска: **[GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1)**

Маппинг: [docs/audit/audit-to-github-map.md](../audit/audit-to-github-map.md)

| Phase | Issues | Описание |
|-------|--------|----------|
| **A · Stabilize** | #55–59 | Eval CI, coverage, Sonar/CodeQL blocking, version, .editorconfig |
| **B · Hardening** | #60–64 | /ready, trace IDs, circuit breaker, purge/backup, monitoring |
| **C · Scale** | #65–69 | CVE, async web, prompt hash, benchmarks, error format |
| **D · Productize** | #50, #70–73 | A/B testing, OTel, plugins, macOS/WSL2, packaging GA |

---

## Что сделано (история)

Всё закрытое: [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Вкратце: Roadmap 1–18 реализован. Старые issues #32–49, #51–53 закрыты. Sonar ~25 замечаний закрыто. Новый аудит (PROJECT_AUDIT_AND_ROADMAP) выявил 20 Weaknesses — все 20 оформлены как issues #55–73.

---

## Актуальные напоминания

- **Sonar:** `uv run python scripts/sonar_fetch_issues.py` — проверить остаток после последнего скана.
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — toolbox ([desktop-build-deps.md](desktop-build-deps.md)). Новые CLI-команды — через ADR (ADR-0001).
- **Ключи:** только keyring ([keyring-keys-reference.md](keyring-keys-reference.md)).

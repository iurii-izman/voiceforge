# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-02-25

---

## Следующий шаг (для копирования в новый чат)

Один конкретный шаг для следующего чата (или пользователь подставляет свою задачу).

- **Сейчас:** Roadmap 3 (экспорт сессии Markdown/PDF) проверен по коду — реализован полностью: CLI `export --id/--format md|pdf`, `build_session_markdown`, PDF через pandoc (pdflatex), Web `/api/export?id=&format=md|pdf`, e2e test в test_cli_e2e_smoke. Следующий шаг: **roadmap 4** — выбор модели Ollama в конфиге или следующий пункт Phase C по доске (#41–45).

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Последняя итерация (кратко)

Roadmap 3 — экспорт сессии (Markdown/PDF): сверка с кодом показала полную реализацию (main.py export_session, build_session_markdown, pandoc для PDF, web/server _handle_get_export, тест export --format md). Изменений не вносилось; обновлён только next-iteration-focus.

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
| [#46–50](https://github.com/iurii-izman/voiceforge/issues/46) | D | Desktop signals, Telegram, Calendar, Flatpak, macOS | Phase D productize |
| [#29](https://github.com/iurii-izman/voiceforge/issues/29) | Ops | RAG ODT/RTF тесты | При добавлении парсеров |
| [#30](https://github.com/iurii-izman/voiceforge/issues/30) | Ops | Dependabot 1 moderate | dependabot-review.md |

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

- **Sonar:** список открытых issues — `uv run python scripts/sonar_fetch_issues.py`. Закрытые S1192, S3626, S3358, S7785, S3776 — в [history](../history/closed-plans-and-roadmap.md).
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — сборка только в toolbox/окружении из [desktop-build-deps.md](desktop-build-deps.md). Новые CLI-команды — только через ADR (ADR-0001).

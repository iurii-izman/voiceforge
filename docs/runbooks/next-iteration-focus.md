# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-02-25

---

## Следующий шаг (для копирования в новый чат)

Один конкретный шаг для следующего чата (или пользователь подставляет свою задачу).

- **Сейчас:** #32 eval закрыт (21 golden samples, LLM-judge test). Следующий шаг: **#34 A3** unit tests daemon/streaming/smart_trigger (снять исключение из coverage), или **#35** WAV e2e integration tests.

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Последняя итерация (кратко)

#32 Eval закрыт: 21 golden samples (standup 5, sprint_review 4, one_on_one 4, brainstorm 4, interview 4), опциональный test_llm_judge_one_golden_sample (skip без anthropic key).

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
| [#34](https://github.com/iurii-izman/voiceforge/issues/34) | A | Unit tests daemon/streaming/smart_trigger | W3; daemon.py excluded from coverage |
| [#35](https://github.com/iurii-izman/voiceforge/issues/35) | A | WAV integration tests | e2e pipeline test |
| ~~#27~~ | A | AppImage | **Закрыт** — toolbox сборка, deb/rpm/AppImage |
| [#36](https://github.com/iurii-izman/voiceforge/issues/36) | B · P0 | Observability (metrics/tracing) | Prometheus/OpenTelemetry |
| [#37](https://github.com/iurii-izman/voiceforge/issues/37) | B · P0 | pyannote memory guard | OOM risk ≤8GB |
| [#38–40](https://github.com/iurii-izman/voiceforge/issues/38) | B | Budget enforcement, IPC envelope, CI cache | Phase B hardening |
| [#41–45](https://github.com/iurii-izman/voiceforge/issues/41) | C | Prompt mgmt, RAG, retention, caching, healthcheck | Phase C scale |
| [#46–50](https://github.com/iurii-izman/voiceforge/issues/46) | D | Desktop signals, Telegram, Calendar, Flatpak, macOS | Phase D productize |
| [#29](https://github.com/iurii-izman/voiceforge/issues/29) | Ops | RAG ODT/RTF тесты | При добавлении парсеров |
| [#30](https://github.com/iurii-izman/voiceforge/issues/30) | Ops | Dependabot 1 moderate | dependabot-review.md |

---

## Следующие шаги (план)

1. **Phase A — Stabilize (приоритет):**
   - ~~#32 A1 eval harness~~ — сделано (21 golden samples, ROUGE-L ≥ 0.35, LLM-judge test).
   - ~~#33 A2 Instructor retry~~ — сделано (instructor.from_litellm, max_retries=3).
   - #34 A3: unit tests daemon/streaming/smart_trigger — снять исключение из coverage.
   - ~~#27 A5 AppImage~~ — сделано (toolbox: NO_STRIP, librsvg2-devel; см. desktop-build-deps.md).
2. **Phase B — Hardening (после A):** observability (Prometheus), pyannote memory guard, budget enforcement.
3. **Документация:** при изменении CLI/конфига обновлять installation-guide, first-meeting-5min; обновлять DOCS-INDEX при новых доках.

---

## Актуальные напоминания

- **Sonar:** список открытых issues — `uv run python scripts/sonar_fetch_issues.py`. Закрытые S1192, S3626, S3358, S7785, S3776 — в [history](../history/closed-plans-and-roadmap.md).
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — сборка только в toolbox/окружении из [desktop-build-deps.md](desktop-build-deps.md). Новые CLI-команды — только через ADR (ADR-0001).

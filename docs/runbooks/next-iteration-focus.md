# Фокус следующей итерации

Файл обновляется **агентом в конце каждой сессии** (см. `agent-context.md`, `.cursor/rules/agent-session-handoff.mdc`). Новый чат: приложить `@docs/runbooks/next-iteration-focus.md` и начать с блока «Следующий шаг» ниже.

**Обновлено:** 2026-02-24

---

## Следующий шаг (для копирования в новый чат)

Один конкретный шаг для следующего чата (или пользователь подставляет свою задачу).

- **Сейчас:** Проведён полный технический аудит (docs/PROJECT_AUDIT_AND_ROADMAP.md, 767 строк). GitHub Project populated: 27 задач в 4 фазах (A Stabilize / B Hardening / C Scale / D Productize), issues #32–53. Следующий шаг: **#32 A1 eval harness** — добавить DeepEval/ROUGE-L тест-жгут для LLM-выходов (Phase A, P0) или продолжить **#27 AppImage** (In Progress).

*(Агент в конце сессии обновляет этот блок одной задачей для следующего чата.)*

---

## Последняя итерация (кратко)

Технический аудит проекта: создан docs/PROJECT_AUDIT_AND_ROADMAP.md (C4, матрица зрелости 1-5, 20 слабых мест, 20-шаговый roadmap). GitHub Project наполнен: 22 новых issue (#32–53) по фазам A–D, операционные QW1–QW3, 5 существующих (#26–#30) обновлены единым schema меток/milestone/полей. Доска: 2 Done, 1 In Progress (#27 AppImage), 24 Todo.

---

## Что сделано (история)

**Всё закрытое вынесено в один документ со сверкой по коду:** [docs/history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

Там: Roadmap 1–12, план развития Часть I и блоки Alpha2 A–D, W1–W10, Sonar, «Следующие 10 шагов» (п.1–6). В текущем файле ниже — только **не сделанное** и план.

---

## Не сделано / открытые задачи

Полная доска: **[GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1)** (27 задач, Phase A–D).

| # Issue | Phase | Задача | Заметка |
|---------|-------|--------|---------|
| [#32](https://github.com/iurii-izman/voiceforge/issues/32) | A · P0 | Eval harness (DeepEval/ROUGE-L) | Первый приоритет Phase A |
| [#33](https://github.com/iurii-izman/voiceforge/issues/33) | A · P0 | Instructor retry loop | W5; router.py complete_structured |
| [#34](https://github.com/iurii-izman/voiceforge/issues/34) | A | Unit tests daemon/streaming/smart_trigger | W3; daemon.py excluded from coverage |
| [#35](https://github.com/iurii-izman/voiceforge/issues/35) | A | WAV integration tests | e2e pipeline test |
| [#27](https://github.com/iurii-izman/voiceforge/issues/27) | A | AppImage (In Progress) | offline-package.md; toolbox сборка |
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
   - #32 A1: eval harness — `tests/test_llm_eval.py` с DeepEval/ROUGE-L, порог ROUGE-L ≥ 0.35.
   - #33 A2: Instructor retry — рефакторинг `complete_structured()` в `router.py`.
   - #34 A3: unit tests daemon/streaming/smart_trigger — снять исключение из coverage.
   - #27 A5: AppImage — `cargo tauri build` в toolbox, артефакт в `target/release/bundle/`.
2. **Phase B — Hardening (после A):** observability (Prometheus), pyannote memory guard, budget enforcement.
3. **Документация:** при изменении CLI/конфига обновлять installation-guide, first-meeting-5min; обновлять DOCS-INDEX при новых доках.

---

## Актуальные напоминания

- **Sonar:** список открытых issues — `uv run python scripts/sonar_fetch_issues.py`. Закрытые S1192, S3626, S3358, S7785, S3776 — в [history](../history/closed-plans-and-roadmap.md).
- **Критично:** pyannote 4.0.4; при OOM — [pyannote-version.md](pyannote-version.md). Десктоп — сборка только в toolbox/окружении из [desktop-build-deps.md](desktop-build-deps.md). Новые CLI-команды — только через ADR (ADR-0001).

# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-23

---

## Сверка плана развития (development-plan-post-audit-2026.md)

**Часть I (1–10):** все пункты реализованы в коде (--template, export, status --detailed, history --search/--date/--from/--to/--action-items/--output md, quickstart, GetAnalytics, status --doctor, action-items update, миграция 005).

**Часть II:** W1 (бюджет из Settings) — в metrics нет хардкода 75, status использует cfg.budget_limit_usd. W2 (sample_rate) — ресэмплинг в pipeline и streaming. W3 (RAG) — RAG_QUERY_MAX_CHARS=1000. W8 — валидация Settings дополнена: ollama_model, ring_seconds, pyannote_restart_hours.

---

## Рекомендательные приоритетные задачи (что делать дальше)

1. **Roadmap #6** — cost report: углубить `cost` / `status --detailed` при необходимости.
2. **Roadmap #10** — Live summary во время listen (уже есть `--live-summary`).
3. **Расширенные e2e** (roadmap #8): покрыть export, analyze --template, action-items, history --output md.
4. **Часть II остальное:** W4 (privacy_mode в GetSettings), W5 (Instructor retry — уже есть), W7 (envelope по умолчанию — уже true), W9 (документировано в config-env-contract), W10 (покрытие).

---

## Важные/критические проблемы на следующую итерацию

1. **W2 (sample_rate):** закрыто — ресэмплинг в стриминге добавлен (scipy при отсутствии — warning).
2. **W3 (RAG):** закрыто — контекст 1000 символов, константа `RAG_QUERY_MAX_CHARS`.
3. **Smart trigger в демоне:** при срабатывании не передаётся `template` в `run_analyze_pipeline` — при необходимости добавить.
4. **Экспорт PDF:** зависимость от pandoc/pdflatex; в quickstart/доках явно указать опциональность.
5. **Покрытие:** сложные модули (daemon, smart_trigger, streaming) при доработках дополнять тестами.

---

## Общий совет

Перед реализацией пункта из плана развития сверять его с текущим кодом (grep по ключевым словам): многое уже сделано (--template, status --detailed, history --search/--date/--from/--to, GetAnalytics, quickstart), чтобы не дублировать и не тратить бюджет на закрытые задачи.

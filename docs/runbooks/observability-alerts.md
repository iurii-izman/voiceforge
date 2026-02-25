# Observability: alerts (Issue #36)

Рекомендуемые алерты для Prometheus/Alertmanager при использовании метрик VoiceForge.

## Метрики

- **voiceforge_llm_cost_usd_total** — накопленная стоимость по моделям.
- **voiceforge_llm_calls_total** — вызовы по модели и статусу (success/error).
- **voiceforge_pipeline_errors_total** — ошибки пайплайна по шагу (stt, diarization, rag и т.д.).

Бюджет и дневная стоимость берутся из `metrics.db` (Settings.budget_limit_usd); в Prometheus есть только счётчики стоимости.

## Рекомендуемые алерты

### 1. Budget > 80%

Используйте **дневную стоимость из приложения** (например, D-Bus `GetAnalytics` или API `/api/status`), а не только Prometheus. Вариант с Prometheus: если вы скрапите дневной total из своего экспортера (агрегирующего `voiceforge_llm_cost_usd_total` за день), то:

- **Alert:** `voiceforge_daily_cost_usd / budget_limit_usd > 0.8`
- **Annotation:** «Бюджет LLM превысил 80%».

*Примечание:* встроенный endpoint `/metrics` отдаёт только сырые счётчики; дневной бюджет и лимит нужно считать в отдельном экспортере или в приложении.

### 2. Error rate > 5%

- **Expr (PromQL):**
  ```promql
  (
    sum(rate(voiceforge_llm_calls_total{status="error"}[5m]))
    /
    sum(rate(voiceforge_llm_calls_total[5m]))
  ) > 0.05
  ```
- **For:** 5m (чтобы избежать всплесков при перезапуске).
- **Annotation:** «Доля ошибок LLM вызовов > 5%».

### 3. Pipeline errors (опционально)

- **Expr:** `increase(voiceforge_pipeline_errors_total[15m]) > 3`
- **Annotation:** «Рост ошибок пайплайна (STT/diarization/RAG)».

## Grafana

- Импорт дашборда: `docs/grafana-voiceforge-dashboard.json`.
- Datasource: Prometheus, указывающий на скрап `/metrics` (например через Pushgateway или прямой скрап HTTP сервера VoiceForge).

## Ссылки

- Issue [#36](https://github.com/iurii-izman/voiceforge/issues/36) — Observability (metrics/tracing).
- `src/voiceforge/core/observability.py` — определение метрик.

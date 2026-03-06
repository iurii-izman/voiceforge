# Observability: alerts (Issue #36)

Рекомендуемые алерты для Prometheus/Alertmanager при использовании метрик VoiceForge. Трассировка (Phase D #71): [config-env-contract.md](config-env-contract.md) — переменные `VOICEFORGE_OTEL_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`; опция `voiceforge[otel]`; спаны pipeline.run, prepare_audio, step1_stt, step2_parallel; экспорт в Jaeger/OTLP.

## Tracing: Jaeger (Phase D #71)

**Цель:** Trace в Jaeger показывает все шаги pipeline с durations.

1. **Запуск Jaeger (all-in-one):** `docker run -d --name jaeger -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one` (OTLP HTTP на 4318, UI на 16686).
2. **Включение OTel:** `export VOICEFORGE_OTEL_ENABLED=1` и `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`. Или только `OTEL_EXPORTER_OTLP_ENDPOINT` — тогда OTel включается автоматически. Установить опцию: `uv sync --extra otel`.
3. **Запуск пайплайна:** демон или CLI (например `voiceforge daemon` и триггер analyze). Спаны: `pipeline.run`, `pipeline.prepare_audio`, `pipeline.step1_stt`, `pipeline.step2_parallel` — видны в Jaeger UI: http://localhost:16686.
4. **Проверка:** выбрать сервис `voiceforge`, найти trace с операцией `pipeline.run` и дочерними spans с длительностями.

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

## Развёртывание стека (Prometheus + Grafana)

См. **`monitoring/README.md`** в корне репо: конфиги `prometheus.yml`, `alerts.yml`, `docker-compose.yml`, импорт дашборда Grafana из `docs/grafana-voiceforge-dashboard.json`. Issue [#64](https://github.com/iurii-izman/voiceforge/issues/64).

## Ссылки

- Issue [#36](https://github.com/iurii-izman/voiceforge/issues/36) — Observability (metrics/tracing).
- Issue [#64](https://github.com/iurii-izman/voiceforge/issues/64) — Monitoring stack (Grafana + alerts).
- `monitoring/` — конфиги Prometheus и алертов.
- `src/voiceforge/core/observability.py` — определение метрик.

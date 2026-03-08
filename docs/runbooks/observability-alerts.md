# Observability: alerts (Issue #36)

Рекомендуемые алерты для Prometheus/Alertmanager при использовании метрик VoiceForge. Трассировка (Phase D #71): [config-env-contract.md](config-env-contract.md) — переменные `VOICEFORGE_OTEL_ENABLED`, `OTEL_EXPORTER_OTLP_ENDPOINT`; опция `voiceforge[otel]`; спаны pipeline.run, prepare_audio, step1_stt, step2_parallel; экспорт в Jaeger/OTLP.

## Tracing: Jaeger (Phase D #71)

**Цель:** Trace в Jaeger показывает все шаги pipeline с durations.

1. **Запуск Jaeger (all-in-one):** на хосте `podman run -d --name jaeger -p 16686:16686 -p 4318:4318 docker.io/jaegertracing/all-in-one` (или `docker run …`). OTLP HTTP на 4318, UI на 16686.
2. **Включение OTel:** экспорт и запуск демона делаются **в том же окружении, где крутится демон** (см. installation-guide: обычно это **внутри toolbox** — `fedora-toolbox-43`). Если демон в **toolbox**, Jaeger на хосте — endpoint должен указывать на хост. Имя `host.containers.internal` может не резолвиться в Fedora toolbox; тогда используйте IP хоста: `export OTEL_EXPORTER_OTLP_ENDPOINT=http://10.0.2.2:4318` (часто это шлюз контейнера) или с хоста выполните `hostname -I` и подставьте первый IP. Если демон на **хосте** (как и Jaeger): `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`. Чтобы не слать трейсы (и не получать ошибки экспорта), снимите переменные: `unset VOICEFORGE_OTEL_ENABLED OTEL_EXPORTER_OTLP_ENDPOINT`. Установить опцию: `uv sync --extra otel`.
3. **Запуск пайплайна:** демон или CLI (например `voiceforge daemon` и триггер analyze). Спаны: `pipeline.run`, `pipeline.prepare_audio`, `pipeline.step1_stt`, `pipeline.step2_parallel` — видны в Jaeger UI: http://localhost:16686.
4. **Проверка:** выбрать сервис `voiceforge`, найти trace с операцией `pipeline.run` и дочерними spans с длительностями.

## Reproducible Runtime Proof Path (#121)

Этот раздел фиксирует **полный proof path**, который можно воспроизвести без догадок. Агент может подготовить команды и синхронизировать docs; **сам запуск Jaeger, старт runtime и просмотр UI делает пользователь**.

### Что считается доказательством

- `uv run pytest tests/test_otel.py tests/test_observability.py -q --tb=line` проходит локально.
- Jaeger UI показывает сервис `voiceforge`.
- Есть хотя бы один trace с root span `pipeline.run`.
- Внутри trace видны дочерние spans `pipeline.prepare_audio`, `pipeline.step1_stt`, `pipeline.step2_parallel`.
- Trace получен из реального runtime path, а не из synthetic snippet.

### Топология окружения

- Если Jaeger и runtime на **хосте**: `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`.
- Если runtime в **toolbox**, а Jaeger на **хосте**: обычно `OTEL_EXPORTER_OTLP_ENDPOINT=http://10.0.2.2:4318`.
- Если `10.0.2.2` не подходит: на хосте `hostname -I`, затем взять первый доступный IP хоста и подставить его в endpoint.

### Preflight

1. Проверить OTel deps: `uv sync --extra otel`.
2. Проверить cheap local contract:
   ```bash
   uv run pytest tests/test_otel.py tests/test_observability.py -q --tb=line
   ```
3. Поднять Jaeger:
   ```bash
   podman run -d --name jaeger -p 16686:16686 -p 4318:4318 docker.io/jaegertracing/all-in-one
   ```
4. В том же окружении, где будет запущен VoiceForge runtime:
   ```bash
   export VOICEFORGE_OTEL_ENABLED=1
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://10.0.2.2:4318
   ```

### Runtime proof

1. Запустить runtime-path, который реально создаёт пайплайн:
   - `uv run voiceforge daemon` и затем trigger `analyze`, или
   - другой существующий CLI path, который доходит до `AnalysisPipeline.run()`.
2. Открыть Jaeger UI: `http://localhost:16686`.
3. Выбрать сервис `voiceforge`.
4. Найти свежий trace с root span `pipeline.run`.
5. Подтвердить наличие дочерних spans:
   - `pipeline.prepare_audio`
   - `pipeline.step1_stt`
   - `pipeline.step2_parallel`
6. Зафиксировать evidence:
   - screenshot trace tree, или
   - exported trace JSON/ID, если удобнее хранить это вне репо.

### Failure signatures

- Нет сервиса `voiceforge` в Jaeger:
  - OTel env не выставлен в том процессе, где реально крутится runtime.
  - runtime отправляет в неверный OTLP endpoint.
  - Jaeger container не поднят или порт `4318` не проброшен.
- Есть сервис, но нет trace `pipeline.run`:
  - запуск не дошёл до `AnalysisPipeline.run()`.
  - runtime path завершился до analyze step.
- Есть root span, но нет дочерних spans:
  - выполнялся не тот pipeline path.
  - runtime упал до Step 1 / Step 2.

### Stop / cleanup

После ручной проверки снять env, чтобы не слать трейсы в пустоту:

```bash
unset VOICEFORGE_OTEL_ENABLED OTEL_EXPORTER_OTLP_ENDPOINT
```

### Честная manual boundary

- Агент **не** запускает Jaeger, **не** открывает браузер и **не** подтверждает визуально trace tree.
- Агент **может** держать актуальными команды, expected spans, failure signatures и cheap local tests.
- Поэтому `#121` закрывается как **documented reproducible proof path**, а не как автоматизированный GUI/runtime capture inside repo.

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

## Чеклист доказательства трейсов (#111, #121)

**Ручные шаги (evidence):** агент не запускает Jaeger и не открывает браузер. Выполняете вы.

1. Запустить Jaeger: `podman run -d --name jaeger -p 16686:16686 -p 4318:4318 docker.io/jaegertracing/all-in-one`.
2. В окружении демона: `export VOICEFORGE_OTEL_ENABLED=1 OTEL_EXPORTER_OTLP_ENDPOINT=http://<host>:4318` (из toolbox — часто `http://10.0.2.2:4318`).
3. Запустить демон и выполнить analyze (или listen + trigger). Открыть http://localhost:16686, выбрать сервис `voiceforge`, убедиться в наличии trace с `pipeline.run` и дочерними spans.
4. После проверки: `unset VOICEFORGE_OTEL_ENABLED OTEL_EXPORTER_OTLP_ENDPOINT`, чтобы не слать трейсы в пустоту.

См. также разделы «Tracing: Jaeger» и «Reproducible Runtime Proof Path (#121)» выше.

## Ссылки

- Issue [#36](https://github.com/iurii-izman/voiceforge/issues/36) — Observability (metrics/tracing).
- Issue [#64](https://github.com/iurii-izman/voiceforge/issues/64) — Monitoring stack (Grafana + alerts).
- `monitoring/` — конфиги Prometheus и алертов.
- `src/voiceforge/core/observability.py` — определение метрик.

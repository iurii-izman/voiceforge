# Monitoring stack (Prometheus + Grafana). Issue #64

Запуск стека мониторинга для VoiceForge: дашборды и алерты по метрикам.

## Требования

- Docker / Podman (docker-compose или `podman-compose`)
- Запущенный VoiceForge web (по умолчанию порт 8765), отдающий `/metrics`

## Запуск

1. **Настроить scrape target.**
   VoiceForge должен быть доступен с контейнера Prometheus. Варианты:
   - **Linux (Docker):** в `prometheus.yml` заменить `host.docker.internal:8765` на IP хоста или добавить в `docker-compose.yml` для сервиса prometheus: `extra_hosts: ["host.docker.internal:host-gateway"]`.
   - **Локально:** запустить VoiceForge на хосте и в `prometheus.yml` указать `targets: ["127.0.0.1:8765"]` (тогда Prometheus лучше запускать с `network_mode: host` или через host-gateway).

2. **Поднять стек:**
   ```bash
   cd monitoring
   docker compose up -d
   # или: podman-compose up -d
   ```

3. **Grafana:** http://localhost:3000 (логин `admin`, пароль `admin`).
   - Добавить datasource: Configuration → Data sources → Add Prometheus → URL `http://prometheus:9090` → Save.
   - Импорт дашборда: Dashboards → New → Import → Upload JSON → выбрать `monitoring/grafana/voiceforge-dashboard.json` (E15 #138; альтернатива: `docs/grafana-voiceforge-dashboard.json`).

4. **Проверка алертов:** в Prometheus (http://localhost:9090) → Alerts — должны быть видны правила VoiceForge (pipeline errors, LLM error rate, circuit breaker, LLM cost, low disk, daemon down). Для доставки уведомлений настроить Alertmanager (опционально).

## Дашборд (E15 #138)

Файл **`monitoring/grafana/voiceforge-dashboard.json`** — import-ready, provisioning-compatible. Панели:

| Панель | Метрика | Описание |
|--------|---------|----------|
| STT latency (avg) | `voiceforge_stt_duration_seconds` | Средняя длительность STT за 5m |
| Diarization latency (avg) | `voiceforge_diarization_duration_seconds` | Средняя длительность diarization |
| LLM cost/day | `voiceforge_llm_cost_usd_total` | Прирост стоимости за 1d |
| Pipeline errors (1h increase) | `voiceforge_pipeline_errors_total` | Ошибки пайплайна по шагам |
| Circuit breaker state | `voiceforge_llm_circuit_breaker_state` | 0=closed, 1=half_open, 2=open |
| Data dir free space | `voiceforge_data_dir_free_bytes` | Свободное место на ФС данных |
| LLM cost anomaly | `voiceforge_llm_cost_anomaly` | 1 если сегодня > threshold × 7d avg |

Порог аномалии стоимости задаётся в конфиге: `cost_anomaly_multiplier` (по умолчанию 2.0). При аномалии в логах пишется предупреждение `observability.cost_anomaly`.

## Файлы

| Файл | Назначение |
|------|------------|
| `prometheus.yml` | Конфиг Prometheus: scrape /metrics, загрузка правил алертов |
| `alerts.yml` | Правила: pipeline errors, LLM error rate, circuit breaker open, LLM cost > $5/day, low disk < 1GB, daemon down |
| `grafana/voiceforge-dashboard.json` | Дашборд Grafana (E15 #138) |
| `docker-compose.yml` | Prometheus + Grafana |

## Алерты (E15 #138)

| Алерт | Условие | Действие |
|-------|---------|----------|
| VoiceForgePipelineErrorsHigh | > 3 ошибок за 15m | Проверить логи (STT, diarization, RAG) |
| VoiceForgePipelineErrorRateHigh | > 5 ошибок за 5m | То же |
| VoiceForgeLLMErrorRateHigh | > 5% ошибок LLM за 5m | Keyring, circuit breaker, провайдер |
| VoiceForgeCircuitBreakerOpen | circuit_breaker_state == 2 > 5m | Снять нагрузку или проверить API |
| VoiceForgeLLMCostHigh | Дневная стоимость > $5 | Проверить использование, бюджет |
| VoiceForgeDataDirLowDisk | Свободно < 1GB на data dir | Очистить или расширить диск |
| VoiceForgeDaemonDown | Нет метрик 5m (up=0) | Проверить процесс, порт 8765 |

## Куда смотреть при срабатывании

- **VoiceForgePipelineErrorsHigh / PipelineErrorRateHigh:** проверить логи VoiceForge (STT, diarization, RAG); возможны проблемы с моделью, RAG index или сетью.
- **VoiceForgeLLMErrorRateHigh:** проверить доступность провайдера LLM, ключи (keyring), circuit breaker (метрика `voiceforge_llm_circuit_breaker_state`).
- **VoiceForgeCircuitBreakerOpen:** снизить частоту запросов или проверить квоты API.
- **VoiceForgeLLMCostHigh:** оценить объём вызовов и при необходимости поднять лимит или оптимизировать промпты.
- **VoiceForgeDataDirLowDisk:** очистить старые бэкапы/логи или увеличить диск.
- **VoiceForgeDaemonDown:** убедиться, что web/daemon запущен и слушает порт 8765.

Бюджет (дневная стоимость > 80% лимита) и аномалия стоимости (today > 2× 7d avg) экспортируются в метриках `voiceforge_llm_cost_anomaly` и в логах; смотреть также через API `/api/status` или D-Bus GetAnalytics (см. `docs/runbooks/observability-alerts.md`).

## Ссылки

- Runbook алертов: `docs/runbooks/observability-alerts.md`
- Дашборд: `monitoring/grafana/voiceforge-dashboard.json` (основной), `docs/grafana-voiceforge-dashboard.json`
- Метрики в коде: `src/voiceforge/core/observability.py`

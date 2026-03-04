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
   - Импорт дашборда: Dashboards → New → Import → Upload JSON → выбрать `docs/grafana-voiceforge-dashboard.json` из корня репо.

4. **Проверка алертов:** в Prometheus (http://localhost:9090) → Alerts — должны быть видны правила VoiceForgePipelineErrorsHigh и VoiceForgeLLMErrorRateHigh. Для доставки уведомлений настроить Alertmanager (опционально).

## Файлы

| Файл | Назначение |
|------|------------|
| `prometheus.yml` | Конфиг Prometheus: scrape /metrics, загрузка правил алертов |
| `alerts.yml` | Правила: рост ошибок пайплайна, доля ошибок LLM > 5% |
| `docker-compose.yml` | Prometheus + Grafana |

## Куда смотреть при срабатывании

- **VoiceForgePipelineErrorsHigh:** проверить логи VoiceForge (STT, diarization, RAG); возможны проблемы с моделью, RAG index или сетью.
- **VoiceForgeLLMErrorRateHigh:** проверить доступность провайдера LLM, ключи (keyring), circuit breaker (метрика `voiceforge_llm_circuit_breaker_state`).

Бюджет (дневная стоимость > 80% лимита) не экспортируется в Prometheus; смотреть через API `/api/status` или D-Bus GetAnalytics (см. `docs/runbooks/observability-alerts.md`).

## Ссылки

- Runbook алертов: `docs/runbooks/observability-alerts.md`
- Дашборд: `docs/grafana-voiceforge-dashboard.json`
- Метрики в коде: `src/voiceforge/core/observability.py`

# Безопасность и зависимости (объединённый runbook)

Единый документ: политика секретов, проверки, зависимости (pyproject/uv), Dependabot. Объединяет бывшие security.md, dependencies.md, dependabot-review.md. Открытые remote alerts и wait states фиксируются отдельно в [security-decision-log.md](security-decision-log.md).

---

## 1. Секреты и проверки (security)

- **Секреты:** только keyring; никогда не коммитить учётные данные.
- **Локальные проверки:**
  ```bash
  gitleaks detect --source . --config .gitleaks.toml
  uv run bandit -r src -ll -q --configfile .bandit.yaml
  uv run pip-audit --desc
  ```
  Если `gitleaks` не установлен локально, `scripts/verify_pr.sh` запускает скан через Podman/Docker.
- **Исключения gitleaks:** в `.gitleaks.toml` в allowlist добавлены `.venv/`, кэши (`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`) и `.hypothesis/` (кэш Hypothesis — тестовые данные могут давать ложные срабатывания при локальном `verify_pr` с `--no-git`).
- **CVE-2025-69872:** historical wait-state закрыт 2026-03-13 — `pip-audit` снова чист без ignore. Источник правды по текущим remote alerts: [security-decision-log.md](security-decision-log.md).
- **Native e2e npm alert (`serialize-javascript`):** локально закрыт 2026-03-13 через npm override в `desktop/e2e-native`; `npm audit` для workspace снова чист. Источник правды по remaining remote alerts: [security-decision-log.md](security-decision-log.md).
- **Ротация токенов:** минимум раз в 90 дней; least privilege; удалять устаревшие; фиксировать в аудит-логе.

---

## 2. Политика зависимостей (dependencies)

- **Источник истины:** `pyproject.toml` (намерения), `uv.lock` (зафиксированные версии). Runtime и CI: `uv sync --extra all`, если не задано иное.
- **Контракт тулчейна:** Python 3.12, 3.13 в CI; `requires-python >=3.12`; CI на uv 0.8. Проверка: `./scripts/check_toolchain.sh`.
- **Обновления:** только через `./scripts/update_deps.sh`; каждое обновление должно проходить `./scripts/verify_pr.sh` и `./scripts/smoke_clean_env.sh`.
- Изменения security-скриптов и CI должны оставлять `pip-audit --desc` чистым без локальных allowlist, если новый explicit wait-state не зафиксирован отдельно в [security-decision-log.md](security-decision-log.md).
- **uv.lock:** не править вручную; при изменении pyproject.toml перегенерировать lock; коммитить pyproject.toml и uv.lock вместе.

---

## 3. Dependabot

- **Где смотреть:** GitHub → Repository → Security → Dependabot alerts.
- **Действия:** для каждого алерта — принять (мержить PR после проверки тестов) или отложить (Dismiss с комментарием).
- **Source of truth для открытых alerts:** [security-decision-log.md](security-decision-log.md). Любой открытый remote alert должен быть отражён там с revisit trigger.
- **CVE-2025-69872 (diskcache):** historical wait-state закрыт 2026-03-13. `uv run pip-audit --desc` проходит без ignore. Если GitHub Dependabot alert всё ещё открыт на remote, его нужно закрыть как fixed/obsolete и синхронизировать [security-decision-log.md](security-decision-log.md).
- **Desktop native-e2e (`serialize-javascript`):** локально закрыт 2026-03-13; после push remote Dependabot alert должен перейти в fixed. Если не перейдёт, проверить, что GitHub видит обновлённый `desktop/e2e-native/package-lock.json`.

---

## 4. Чеклист закрытия historical CVE wait-state (#65)

Фикс подтверждён локально на 2026-03-13 (`uv run pip-audit --desc` чист). Для полного закрытия historical следа:

1. **Проверить:** `uv run pip-audit --desc` — проходит без ошибок.
2. **Синхронизировать CI/scripts:** не должно остаться `--ignore-vuln CVE-2025-69872` в активных workflow и скриптах.
3. **Закрыть issue:** `#65`.
4. **Dependabot:** при наличии открытого алерта — закрыть как fixed/obsolete.
5. **Обновить docs:** `security-decision-log.md`, `next-iteration-focus.md`, `PROJECT-STATUS-SUMMARY.md`.

---

## 5. Локальные данные на диске: текущий baseline и accepted risk

Локальные SQLite-базы (transcripts.db, metrics.db, RAG) и локальный LLM cache **не шифруются**. Данные хранятся в открытом виде в `XDG_DATA_HOME/voiceforge/` (или заданных путях).

Что уже сделано как security baseline:

- runtime создаёт `XDG_DATA_HOME/voiceforge/` и backup directories с private permissions `0700`;
- создаваемые local DB/cache/status/backup files приводятся к private permissions `0600`;
- regression suite `tests/test_security_batch120.py` фиксирует этот baseline, чтобы проект не выглядел защищённее, чем он есть.

**E17 #140 (реализовано):**

- **SQLite encryption at rest (optional):** В конфиге опция `encrypt_db: true`; ключ в keyring `db_encryption_key`. Требуется опциональная зависимость `sqlcipher3` (`uv sync --extra security`). Без ключа или без sqlcipher3 при включённом encrypt_db используется обычный sqlite3 с предупреждением в лог. Миграция существующей незашифрованной БД: backup → удалить или переименовать transcripts.db → запуск создаст новую зашифрованную БД (данные нужно восстанавливать из backup вручную или отдельным скриптом).
- **API key audit log:** Каждое обращение к keyring (get_api_key) пишется в structlog и в таблицу `api_key_access` в metrics.db (timestamp, key_name, operation). Caller передаётся только в structlog.
- **AppArmor:** Шаблон профиля в `security/voiceforge.apparmor`. Установка: см. [security.md](security.md).

**Возможные направления на будущее:** LUKS/ecryptfs для каталога данных; автоматическая миграция существующей БД в SQLCipher (export/import).

---

## 6. Надёжность вызовов LLM (блок 69)

- **Circuit breaker:** в `voiceforge.llm.circuit_breaker` — при повторных сбоях вызов к модели временно не выполняется (состояние open), затем пробный вызов (half-open). Снижает нагрузку при недоступности API.
- **Retry:** Instructor использует `max_retries=3` при ошибках парсинга; при сетевых сбоях повторные попытки зависят от провайдера (LiteLLM). Явный экспоненциальный backoff для всех провайдеров — возможное расширение.

---

## 7. Риски зависимостей и данные на диске (#110)

**Чеклист (dependency risk):**

- Еженедельно: `uv run pip-audit --desc`.
- При добавлении зависимости: проверить лицензию и известные CVE; обновлять через `./scripts/update_deps.sh`; коммитить pyproject.toml и uv.lock вместе.
- Dependabot: не игнорировать алерты без решения; для новых wait-state сначала оформить запись в [security-decision-log.md](security-decision-log.md).

**Чеклист (data-at-rest):**

- Локальные БД, cache и backup artifacts — в `XDG_DATA_HOME/voiceforge/` (или заданных путях); runtime держит private filesystem permissions `0700/0600`, но это **не** заменяет encryption-at-rest.
- При требовании конфиденциальности — LUKS/каталог в зашифрованном разделе или будущий блок 96 (SQLCipher).
- Секреты — только keyring (сервис `voiceforge`); не хранить в конфиг-файлах и не коммитить.

---

## Ссылки

- Ключи keyring: [keyring-keys-reference.md](keyring-keys-reference.md)
- Конфиг и env: [config-env-contract.md](config-env-contract.md)

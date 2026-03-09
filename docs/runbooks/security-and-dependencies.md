# Безопасность и зависимости (объединённый runbook)

Единый документ: политика секретов, проверки, зависимости (pyproject/uv), Dependabot. Объединяет бывшие security.md, dependencies.md, dependabot-review.md. Открытые remote alerts и wait states фиксируются отдельно в [security-decision-log.md](security-decision-log.md).

---

## 1. Секреты и проверки (security)

- **Секреты:** только keyring; никогда не коммитить учётные данные.
- **Локальные проверки:**
  ```bash
  gitleaks detect --source . --config .gitleaks.toml
  uv run bandit -r src -ll -q --configfile .bandit.yaml
  uv run pip-audit --desc --ignore-vuln CVE-2025-69872
  ```
  Если `gitleaks` не установлен локально, `scripts/verify_pr.sh` запускает скан через Podman/Docker.
- **Исключения gitleaks:** в `.gitleaks.toml` в allowlist добавлены `.venv/`, кэши (`.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`) и `.hypothesis/` (кэш Hypothesis — тестовые данные могут давать ложные срабатывания при локальном `verify_pr` с `--no-git`).
- **Исключение CVE-2025-69872:** дискcache (transitive через instructor); снять ignore после фикса upstream. Weekly workflow запускает pip-audit без ignore (allowed to fail), чтобы обнаружить появление фикса.
- **Ротация токенов:** минимум раз в 90 дней; least privilege; удалять устаревшие; фиксировать в аудит-логе.

---

## 2. Политика зависимостей (dependencies)

- **Источник истины:** `pyproject.toml` (намерения), `uv.lock` (зафиксированные версии). Runtime и CI: `uv sync --extra all`, если не задано иное.
- **Контракт тулчейна:** Python 3.12, 3.13 в CI; `requires-python >=3.12`; CI на uv 0.8. Проверка: `./scripts/check_toolchain.sh`.
- **Обновления:** только через `./scripts/update_deps.sh`; каждое обновление должно проходить `./scripts/verify_pr.sh` и `./scripts/smoke_clean_env.sh`.
- **CVE-2025-69872:** временное исключение (diskcache через instructor). Держать ignore в скриптах/workflow до фикса upstream. См. также раздел 1.
- **uv.lock:** не править вручную; при изменении pyproject.toml перегенерировать lock; коммитить pyproject.toml и uv.lock вместе.

---

## 3. Dependabot

- **Где смотреть:** GitHub → Repository → Security → Dependabot alerts.
- **Действия:** для каждого алерта — принять (мержить PR после проверки тестов) или отложить (Dismiss с комментарием).
- **Source of truth для открытых alerts:** [security-decision-log.md](security-decision-log.md). Любой открытый remote alert должен быть отражён там с revisit trigger.
- **CVE-2025-69872 (diskcache):** фиксирующей версии нет (проверено 2026-03: upstream не выпустил патч). В CI уже `pip-audit --ignore-vuln CVE-2025-69872`. Рекомендуется отложить алерт: Dependabot → Dismiss → «Accept risk», комментарий: «No fix version yet. See docs/runbooks/security-and-dependencies.md. Revisit when upstream fixes.» Либо скрипт (нужен `github_token` в keyring с правом security_events): `uv run python scripts/dependabot_dismiss_moderate.py`. После появления фикса — выполнить чеклист ниже.

---

## 4. Чеклист снятия CVE-2025-69872 (#65)

Когда в upstream (diskcache или instructor) появится версия с фиксом:

1. **Проверить:** [PyPI diskcache](https://pypi.org/project/diskcache/), [instructor](https://pypi.org/project/instructor/) или `uv run pip-audit --desc` (без ignore) — что vuln закрыта.
2. **Обновить зависимости:** `uv lock --upgrade-package diskcache` или `--upgrade-package instructor`; при необходимости поправить pyproject.toml; `uv sync --extra all`; прогнать тесты.
3. **Удалить `--ignore-vuln CVE-2025-69872`** из: `scripts/verify_pr.sh`, `.github/workflows/test.yml`, `.github/workflows/security-weekly.yml`; в этом runbook — убрать ignore из примеров команд и упоминаний.
4. **Проверить:** `uv run pip-audit --desc` без аргументов — проходит без ошибок.
5. **Dependabot:** при наличии открытого алерта — принять PR с обновлением или закрыть с комментарием «Fixed in commit …».

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

- Еженедельно: `uv run pip-audit --desc` (с учётом временного `--ignore-vuln` для #65 до фикса upstream).
- При добавлении зависимости: проверить лицензию и известные CVE; обновлять через `./scripts/update_deps.sh`; коммитить pyproject.toml и uv.lock вместе.
- Dependabot: не игнорировать алерты без решения; для #65 — Dismiss с комментарием по разделу 3.

**Чеклист (data-at-rest):**

- Локальные БД, cache и backup artifacts — в `XDG_DATA_HOME/voiceforge/` (или заданных путях); runtime держит private filesystem permissions `0700/0600`, но это **не** заменяет encryption-at-rest.
- При требовании конфиденциальности — LUKS/каталог в зашифрованном разделе или будущий блок 96 (SQLCipher).
- Секреты — только keyring (сервис `voiceforge`); не хранить в конфиг-файлах и не коммитить.

---

## Ссылки

- Ключи keyring: [keyring-keys-reference.md](keyring-keys-reference.md)
- Конфиг и env: [config-env-contract.md](config-env-contract.md)

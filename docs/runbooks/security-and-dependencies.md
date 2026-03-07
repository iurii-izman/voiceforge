# Безопасность и зависимости (объединённый runbook)

Единый документ: политика секретов, проверки, зависимости (pyproject/uv), Dependabot. Объединяет бывшие security.md, dependencies.md, dependabot-review.md.

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
- **CVE-2025-69872 (diskcache):** фиксирующей версии нет. В CI уже `pip-audit --ignore-vuln CVE-2025-69872`. Рекомендуется отложить алерт: Dependabot → Dismiss → «Accept risk», комментарий: «No fix version yet. See docs/runbooks/security-and-dependencies.md. Revisit when upstream fixes.» Либо скрипт (нужен `github_token` в keyring с правом security_events): `uv run python scripts/dependabot_dismiss_moderate.py`. После появления фикса — выполнить чеклист ниже.

---

## 4. Чеклист снятия CVE-2025-69872 (#65)

Когда в upstream (diskcache или instructor) появится версия с фиксом:

1. **Проверить:** [PyPI diskcache](https://pypi.org/project/diskcache/), [instructor](https://pypi.org/project/instructor/) или `uv run pip-audit --desc` (без ignore) — что vuln закрыта.
2. **Обновить зависимости:** `uv lock --upgrade-package diskcache` или `--upgrade-package instructor`; при необходимости поправить pyproject.toml; `uv sync --extra all`; прогнать тесты.
3. **Удалить `--ignore-vuln CVE-2025-69872`** из: `scripts/verify_pr.sh`, `.github/workflows/test.yml`, `.github/workflows/security-weekly.yml`; в этом runbook — убрать ignore из примеров команд и упоминаний.
4. **Проверить:** `uv run pip-audit --desc` без аргументов — проходит без ошибок.
5. **Dependabot:** при наличии открытого алерта — принять PR с обновлением или закрыть с комментарием «Fixed in commit …».

---

## 5. Шифрование локальных БД (опция, блок 96)

Локальные SQLite-базы (transcripts.db, metrics.db, RAG) **не шифруются**. Данные хранятся в открытом виде в `XDG_DATA_HOME/voiceforge/` (или заданных путях).

**Возможные направления на будущее:** SQLCipher, шифрование на уровне файловой системы (LUKS, ecryptfs), или опция «хранить в зашифрованном каталоге». Реализация не входит в текущий roadmap; при появлении требований — см. [roadmap-100-blocks.md](../plans/roadmap-100-blocks.md) блок 96.

---

## Ссылки

- Ключи keyring: [keyring-keys-reference.md](keyring-keys-reference.md)
- Конфиг и env: [config-env-contract.md](config-env-contract.md)

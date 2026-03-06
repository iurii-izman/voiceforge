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
- **CVE-2025-69872 (diskcache):** фиксирующей версии нет. В CI уже `pip-audit --ignore-vuln CVE-2025-69872`. Рекомендуется отложить алерт: Dependabot → Dismiss → «Accept risk», комментарий: «No fix version yet. See docs/runbooks/security-and-dependencies.md. Revisit when upstream fixes.» Либо скрипт (нужен `github_token` в keyring с правом security_events): `uv run python scripts/dependabot_dismiss_moderate.py`. После появления фикса — снять ignore и обновить зависимость.

---

## Ссылки

- Ключи keyring: [keyring-keys-reference.md](keyring-keys-reference.md)
- Конфиг и env: [config-env-contract.md](config-env-contract.md)

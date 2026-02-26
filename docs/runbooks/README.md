# Runbooks

Операционные инструкции и справочники. Группировка по смыслу. **Индекс всей документации (актуальность, модерация):** [../DOCS-INDEX.md](../DOCS-INDEX.md).

**English:** [en/README.md](en/README.md) — installation-guide, quickstart, bootstrap, desktop-build-deps, dependabot-review, telegram-bot-setup.

---

## Контекст и агент

| Файл | Назначение |
|------|------------|
| [agent-context.md](agent-context.md) | Единый контекст для Cursor: правила, keyring, чеклист конца сессии, универсальный промпт. Прикладывать в новый чат. |
| [next-iteration-focus.md](next-iteration-focus.md) | Следующий шаг (один для следующего чата); обновляет агент в конце сессии. |
| [cursor-agent-setup.md](cursor-agent-setup.md) | Настройка Cursor (My Secrets только без keyring; локально — keyring). |
| [voiceforge-cursor-tz.md](voiceforge-cursor-tz.md) | Расширенное ТЗ для Cursor: среда, стек, ограничения, шаблоны промптов. |
| [claude-proposal-alignment.md](claude-proposal-alignment.md) | Сверка предложений с кодом (что реализовано). Справочно. |

---

## Конфиг и среда

| Файл | Назначение |
|------|------------|
| [config-env-contract.md](config-env-contract.md) | VOICEFORGE_*, Settings, D-Bus GetSettings, keyring. |
| [keyring-keys-reference.md](keyring-keys-reference.md) | Полный список имён ключей в keyring (anthropic, openai, webhook_telegram, sonar_token, …). |
| [bootstrap.md](bootstrap.md) | Установка: bootstrap.sh, uv sync, doctor, опционально сервис. |
| [installation-guide.md](installation-guide.md) | Полный гайд: где запускать (хост/toolbox), когда ребилдить, демон, обновление. |
| [desktop-build-deps.md](desktop-build-deps.md) | Зависимости для сборки Tauri в toolbox; при OOM — pyannote-version.md. |

---

## Релизы и качество

| Файл | Назначение |
|------|------------|
| [alpha2-checklist.md](alpha2-checklist.md) | Чеклист перед тегом v0.2.0-alpha.1. |
| [release.md](release.md) | Release runbook: проверки, команды, артефакты. |
| [rollback-alpha-release.md](rollback-alpha-release.md) | Откат неудачного альфа-релиза. |
| [alpha0.1-dod.md](alpha0.1-dod.md) | Definition of Done для alpha0.1. |

---

## Безопасность и зависимости

| Файл | Назначение |
|------|------------|
| [security.md](security.md) | Секреты, keyring, pip-audit, CVE-исключения (diskcache). |
| [dependencies.md](dependencies.md) | Политика зависимостей: pyproject.toml, uv.lock, обновления. |
| [dependabot-review.md](dependabot-review.md) | Как закрывать Dependabot алерты (в т.ч. CVE-2025-69872). |

## Фичи (runbooks)

| Файл | Назначение |
|------|------------|
| [telegram-bot-setup.md](telegram-bot-setup.md) | Telegram-бот (ADR-0005): keyring webhook_telegram, webhook, туннель. |
| [pyannote-version.md](pyannote-version.md) | Версия pyannote, откат при OOM. |

## Операции и справочники

| Файл | Назначение |
|------|------------|
| [quickstart.md](quickstart.md) | Краткий сценарий первой встречи; полная версия — docs/first-meeting-5min.md. |
| [repo-governance.md](repo-governance.md) | Правила main, PR, security baseline, SonarCloud. |
| [test-operations.md](test-operations.md) | Flaky-тесты, CI, карантин. |
| [web-api.md](web-api.md) | Web UI API (опционально). |

---

План реализации десктопа (Tauri) — в корне docs: [../desktop-tauri-implementation-plan.md](../desktop-tauri-implementation-plan.md).

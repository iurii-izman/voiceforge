# Runbooks

Операционные инструкции и справочники. Группировка по смыслу. **Индекс всей документации (актуальность, модерация):** [../DOCS-INDEX.md](../DOCS-INDEX.md).

**English:** [en/README.md](en/README.md) — installation-guide, quickstart, bootstrap, desktop-build-deps, dependabot-review, telegram-bot-setup.

---

## Контекст и агент

| Файл | Назначение |
|------|------------|
| [agent-context.md](agent-context.md) | Единый контекст для Cursor: правила, keyring, чеклист конца сессии, универсальный промпт. Прикладывать в новый чат. |
| [next-iteration-focus.md](next-iteration-focus.md) | Следующий шаг (один для следующего чата); обновляет агент в конце сессии. |
| [doc-governance.md](doc-governance.md) | Порядок в доках: источники правды, архив, актуализация после итераций. |
| [cursor.md](cursor.md) | Cursor: настройка (Cloud/локально), тюнинг, промпты, OOM, справка. |
| [voiceforge-cursor-tz.md](voiceforge-cursor-tz.md) | Заглушка → [archive/runbooks/voiceforge-cursor-tz-2026.md](../archive/runbooks/voiceforge-cursor-tz-2026.md). |
| [claude-proposal-alignment.md](claude-proposal-alignment.md) | Заглушка → архив (см. [../archive/plans/](../archive/plans/)). |

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
| [release-and-quality.md](release-and-quality.md) | **Единый документ:** релиз (чеклист, команды), откат, чеклист альфа2, Alpha0.1 DoD. Раньше: release.md, rollback-alpha-release.md, alpha2-checklist.md, alpha0.1-dod.md (теперь заглушки со ссылкой). |

---

## Безопасность и зависимости

| Файл | Назначение |
|------|------------|
| [security-and-dependencies.md](security-and-dependencies.md) | **Единый документ:** секреты, keyring, pip-audit, CVE; политика зависимостей (pyproject, uv.lock); Dependabot. Раньше: security.md, dependencies.md, dependabot-review.md (теперь заглушки). |

## Фичи (runbooks)

| Файл | Назначение |
|------|------------|
| [telegram-bot-setup.md](telegram-bot-setup.md) | Telegram-бот (ADR-0005): keyring webhook_telegram, webhook, туннель. |
| [pyannote-version.md](pyannote-version.md) | Версия pyannote, откат при OOM. |

## Планирование и задачи

| Файл | Назначение |
|------|------------|
| [planning.md](planning.md) | Канбан (GitHub Project), audit map, next-iteration-focus; gh и связка с агентом. |

## Операции и справочники

| Файл | Назначение |
|------|------------|
| [quickstart.md](quickstart.md) | Краткий сценарий первой встречи; полная версия — docs/first-meeting-5min.md. |
| [repo-and-git-governance.md](repo-and-git-governance.md) | **Единый документ:** правила main, security baseline, SonarCloud; коммиты, ветки, теги, issues, GitHub Project. Раньше: repo-governance.md, git-github-practices.md (теперь заглушки). |
| [test-operations.md](test-operations.md) | Flaky-тесты, CI, карантин. |
| [web-api.md](web-api.md) | Web UI API (опционально). |

---

Текущие задачи и план: [../audit/audit.md](../audit/audit.md), [../plans.md](../plans.md), [next-iteration-focus.md](next-iteration-focus.md). Архив: [../archive/README.md](../archive/README.md).

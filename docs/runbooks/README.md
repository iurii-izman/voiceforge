# Runbooks

Операционные инструкции и справочники. Группировка по смыслу.

---

## Контекст и агент

| Файл | Назначение |
|------|------------|
| [agent-context.md](agent-context.md) | Единый контекст для Cursor: правила, конфиг, приоритеты, конец сессии. Прикладывать в новый чат. |
| [next-iteration-focus.md](next-iteration-focus.md) | Фокус следующей итерации; обновляет агент после большой итерации. |
| [cursor-agent-setup.md](cursor-agent-setup.md) | Настройка Cursor (My Secrets только без keyring; локально — keyring). |
| [voiceforge-cursor-tz.md](voiceforge-cursor-tz.md) | Расширенное ТЗ для Cursor: среда, стек, ограничения, блоки Alpha2, шаблоны промптов, чеклисты. |
| [claude-proposal-alignment.md](claude-proposal-alignment.md) | Сверка предложения Claude с проектом; что реализовано, расхождения (pyannote). |

---

## Конфиг и среда

| Файл | Назначение |
|------|------------|
| [config-env-contract.md](config-env-contract.md) | VOICEFORGE_*, Settings, D-Bus GetSettings, keyring. |
| [keyring-keys-reference.md](keyring-keys-reference.md) | Полный список имён ключей в keyring (anthropic, openai, sonar_token, …). |
| [bootstrap.md](bootstrap.md) | Установка: bootstrap.sh, uv sync, doctor, опционально сервис. |
| [installation-guide.md](installation-guide.md) | Полный гайд: где запускать (хост/toolbox), когда ребилдить, демон, обновление. |
| [desktop-build-deps.md](desktop-build-deps.md) | Зависимости для сборки Tauri в toolbox (Fedora). |

---

## Релизы и качество

| Файл | Назначение |
|------|------------|
| [alpha2-checklist.md](alpha2-checklist.md) | Чеклист перед тегом v0.2.0-alpha.1. |
| [release.md](release.md) | Release runbook: проверки, команды, артефакты. |
| [rollback-alpha-release.md](rollback-alpha-release.md) | Откат неудачного альфа-релиза. |
| [alpha0.1-dod.md](alpha0.1-dod.md) | Definition of Done для alpha0.1. |

---

## Операции и справочники

| Файл | Назначение |
|------|------------|
| [quickstart.md](quickstart.md) | Краткий сценарий первой встречи; полная версия — docs/first-meeting-5min.md. |
| [dependencies.md](dependencies.md) | Политика зависимостей: pyproject.toml, uv.lock, обновления. |
| [repo-governance.md](repo-governance.md) | Правила main, PR, security baseline, SonarCloud. |
| [security.md](security.md) | Секреты, ключи, не коммитить. |
| [test-operations.md](test-operations.md) | Flaky-тесты, CI, карантин. |
| [web-api.md](web-api.md) | Web UI API (опционально). |

---

План реализации десктопа (Tauri) — в корне docs: [../desktop-tauri-implementation-plan.md](../desktop-tauri-implementation-plan.md).

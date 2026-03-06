# Консолидация документации (2026-03)

Краткий отчёт об объединении похожих по смыслу документов в общие runbooks.

---

## Анализ до консолидации

- **Runbooks:** 30+ файлов в docs/runbooks/; дублирование по темам (security, dependencies, dependabot; release, rollback, чеклисты; repo governance, git practices).
- **Аудит:** audit.md (таблица статуса W1–W20) и audit-2026-03.md (полный отчёт на 72 строки) — два входа в одну тему.
- **Итог:** объединение по смыслу уменьшает количество точек входа и обновлений.

---

## Выполненные слияния

### 1. Безопасность и зависимости

| Было | Стало |
|------|--------|
| security.md, dependencies.md, dependabot-review.md | **security-and-dependencies.md** (один документ: секреты, pip-audit, CVE; политика pyproject/uv.lock; Dependabot). Исходные файлы — заглушки со ссылкой. |

### 2. Релизы и качество

| Было | Стало |
|------|--------|
| release.md, rollback-alpha-release.md, alpha2-checklist.md, alpha0.1-dod.md | **release-and-quality.md** (релиз, откат, чеклист альфа2, Alpha0.1 DoD). Исходные файлы — заглушки. |

### 3. Репозиторий и Git

| Было | Стало |
|------|--------|
| repo-governance.md, git-github-practices.md | **repo-and-git-governance.md** (main branch, security baseline, SonarCloud; коммиты, ветки, теги, issues, Project). Исходные файлы — заглушки. |

### 4. Аудит

| Было | Стало |
|------|--------|
| audit.md + audit-2026-03.md (отдельный полный отчёт) | **audit.md** дополнен разделом 5 «Подробный снимок 2026-03» (краткое содержание). Полный текст audit-2026-03 перенесён в **archive/audit/audit-2026-03-full.md**. В audit/ оставлена заглушка audit-2026-03.md со ссылкой на архив. |

---

## Обновлённые ссылки

Внутренние ссылки в runbooks и docs обновлены на новые документы: agent-context, planning, cursor, sonar-pr-cleanup, git-github-practices-rule, rag-formats, audit/README, docs/README, runbooks/en/dependabot-review. DOCS-INDEX и runbooks/README приведены в соответствие с новой структурой.

---

## Что не объединяли

- **Контекст и агент:** agent-context, next-iteration-focus, doc-governance, cursor — разные роли; объединение нецелесообразно.
- **Конфиг и среда:** config-env-contract, keyring-keys-reference, bootstrap, installation-guide, desktop-build-deps — разный уровень детализации; можно объединять в будущем при желании (например «установка и среда»).
- **ADR, architecture, history:** оставлены как есть (уже компактные или архивные).

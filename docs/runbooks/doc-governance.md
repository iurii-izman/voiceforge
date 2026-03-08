# Управление документацией (doc governance)

Единые правила: минимум источников правды, архив для устаревшего, актуализация после итераций.

---

## Источники правды (не дублировать)

- **Текущий план и задачи:** [next-iteration-focus.md](next-iteration-focus.md) + [audit/audit.md](../audit/audit.md). Единая точка входа по плану и канбану: [planning.md](planning.md). Для сводного live state и очереди batches использовать [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md), а не старые prompts/исторические очереди в runbook'ах.
- **Приоритеты фич и планы:** [plans.md](../plans.md).
- **Аудит:** снимок 2026-02-26 в [archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md](../archive/audit/PROJECT_AUDIT_AND_ROADMAP_2026.md); актуальный статус — [audit/audit.md](../audit/audit.md). Не плодить новые «планы по аудиту» — дополнять audit.md или переносить выполненное в архив.
- **Конфиг и ключи:** [config-env-contract.md](config-env-contract.md), [keyring-keys-reference.md](keyring-keys-reference.md).
- **Индекс:** [DOCS-INDEX.md](../DOCS-INDEX.md) — один перечень актуальных документов и архива.

---

## Архив (docs/archive/)

**Когда переносить:** план/аудит в основном выполнен; документ заменён другим; ADR superseded.

**Как:** скопировать файл в `docs/archive/plans/`, `docs/archive/adr/` или `docs/archive/runbooks/`; в исходном месте оставить короткую заглушку со ссылкой на архив. В коммите указать «архивирован: …».

**Структура:** см. [archive/README.md](../archive/README.md).

---

## После большой итерации (чеклист для агента)

1. **Обновить текущие доки:** next-iteration-focus (следующий шаг, дата), при изменении поведения — runbook’и (installation-guide, config-env-contract и т.д.), при необходимости [audit/audit.md](../audit/audit.md) (статус issues).
2. **Архивировать:** выполненный план или устаревший документ → docs/archive/; в старом месте — заглушка со ссылкой.
3. **Индекс:** при появлении/перемещении документа обновить DOCS-INDEX.md (раздел, статус).
4. **Не дублировать:** не создавать новый «план по аудиту» или «next steps» — дополнять существующие источники правды.

---

## Sweep: устаревшие ссылки и версии

**Версия (единый источник):** `pyproject.toml` (Python package), `desktop/package.json` и `desktop/src-tauri/tauri.conf.json` (desktop). При смене версии обновить release-and-quality.md, CHANGELOG и при необходимости примеры в runbook’ах (desktop-build-deps, desktop-updater). Не дублировать номер версии в тексте «Release readiness» — брать из release-and-quality.md.

**Устаревшие ссылки:** при sweep проверять DOCS-INDEX.md, `runbooks/README.md`, активные prompts в `agent-context.md` / `cursor.md` / `planning.md`, заглушки в docs/ (PROJECT_AUDIT_AND_ROADMAP.md → archive), пути audit/audit.md и plans.md (относительно docs/). Сломанные внутренние ссылки править в том же коммите, что и изменение целевого документа.

---

## Ссылки

- Полный индекс: [DOCS-INDEX.md](../DOCS-INDEX.md).
- Правило для Cursor: `.cursor/rules/doc-governance.mdc` — напоминание про архив и актуализацию после итерации.

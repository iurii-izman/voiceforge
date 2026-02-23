# Чеклист альфа2 (с десктопом)

Версия: **0.2.0a1** / тег **v0.2.0-alpha.1**.

## Перед тегом

1. Тесты CLI и демона проходят: `uv run pytest tests/ -q` (релевантные сьюты).
2. Десктоп собирается: `./scripts/check-desktop-deps.sh` → OK; `cd desktop && npm install && npm run build && cargo tauri build`.
3. Сценарий «запуск демона → запуск Tauri → анализ → просмотр сессии» выполняется вручную.
4. CHANGELOG обновлён (секция [0.2.0-alpha.1] или перенос из Unreleased).
5. Версия согласована: `pyproject.toml` (при переходе на 0.2.0a1), `desktop/package.json` и `desktop/src-tauri/tauri.conf.json` (0.2.0-alpha.1).

## Релиз

- Release runbook: [release.md](release.md) (включая шаг сборки десктопа для альфа2).
- Браузерное UI (`voiceforge web`) остаётся в дереве, но не в фокусе релиза.

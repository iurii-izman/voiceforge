# Maintenance Mode

VoiceForge сейчас в режиме **maintenance + bug-driven work**: активная инженерная очередь закрыта, а периодическая задача сводится к re-check release/docs/security drift.

Этот runbook фиксирует одну каноническую проверку, которая помогает быстро понять, что репо по-прежнему находится в здоровом состоянии.

## Каноническая команда

```bash
uv run python scripts/check_maintenance_state.py
```

Для машинного вывода:

```bash
uv run python scripts/check_maintenance_state.py --json
```

Проверка включает:

- release-proof boundary
- docs consistency
- `pip-audit` в обычном blocking-режиме
- краткую сводку по open issues через `gh`, если GitHub CLI доступен и авторизован

## Как интерпретировать

- `overall: ready`
  maintenance mode healthy; release/docs/security boundary не ушла в drift
- `pip-audit(raw): clean`
  текущее нормальное состояние: known CVE wait-state больше не активен
- `pip-audit(raw): unexpected-vulnerabilities`
  появился новый security drift
- `queue: new-work-present`
  в репо снова есть живая рабочая очередь; это не failure само по себе, но maintenance mode уже не “пустой”

## Weekly automation

В GitHub Actions есть workflow:

- `.github/workflows/maintenance-weekly.yml`

Он:

1. делает `uv sync --extra all`
2. запускает `uv run python scripts/check_maintenance_state.py --json`
3. сохраняет `maintenance-state.json` как artifact

## Если security state изменился

Если `pip-audit(raw)` перестал быть `clean`, перейти к:

- [security-and-dependencies.md](security-and-dependencies.md) раздел 4
- [security-decision-log.md](security-decision-log.md)

и затем:

1. зафиксировать новые CVE или dependency drift
2. обновить зависимости и CI/scripts при необходимости
3. оформить новую issue, если это не one-line maintenance fix
4. обновить `next-iteration-focus.md` и `PROJECT-STATUS-SUMMARY.md`

## Связанные документы

- [next-iteration-focus.md](next-iteration-focus.md)
- [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md)
- [security-decision-log.md](security-decision-log.md)
- [security-and-dependencies.md](security-and-dependencies.md)
- [release-and-quality.md](release-and-quality.md)

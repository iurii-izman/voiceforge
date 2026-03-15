# Quality Audit 2026-03

**Обновлено:** 2026-03-13.

Этот runbook фиксирует пост-Phase-E quality/security debt snapshot и переводит его в автономные блоки для Project. Источники сигнала: GitHub Security, CodeQL, SonarCloud, local gates (`preflight`, `ruff`, `mypy`, `bandit`, `pip-audit`).

---

## 1. Snapshot на 2026-03-09

### GitHub

- На момент snapshot 2026-03-09 repo queue фактически уже свелась к внешнему wait-state `#65`; по состоянию на 2026-03-13 этот wait-state снят, и runbook остаётся историческим снимком QA wave.
- Открытые GitHub Security alerts: `3` (Dependabot; CodeQL alert dismissed in QA1 [#152](https://github.com/iurii-izman/voiceforge/issues/152))
  - CodeQL `py/clear-text-logging-sensitive-data`: **dismissed** (false positive — Git credential helper protocol)
  - `3` Dependabot alerts (`serialize-javascript`, `time`, `glib`) — tracked, see security-decision-log.md

### Локальные quality gates

- `./scripts/preflight_repo.sh --with-tests` — зелёный
- `ruff` — зелёный
- `bandit` — без blocking findings
- `pip-audit` — зелёный
- `mypy` — зелёный (исправлено в QA2 [#153](https://github.com/iurii-izman/voiceforge/issues/153))

### SonarCloud

Главный объём долга сейчас в пяти корзинах:

1. GitHub-visible security/supply-chain issues
2. Local gate parity (`mypy`)
3. Python core/CLI hotspots (`main.py`, `daemon.py`, `status_helpers.py`, `setup.py`, `meeting.py`, `digest.py`, `pipeline.py`)
4. Test-only Sonar debt (пустые stubs, float equality, constant booleans, type mismatch smells)
5. DevOps/desktop script and frontend Sonar debt

Вывод: quality debt уже не “размазан по всему проекту”, а сводится к нескольким крупным, достаточно автономным remediation tracks.

---

## 2. Autopilot blocks

| Block | Issue | Priority | Area | Смысл |
|---|---|---|---|---|
| `QA1` | [#152](https://github.com/iurii-izman/voiceforge/issues/152) | P0 | Security | Закрыть или корректно отtriage’ить GitHub Security: CodeQL + Dependabot |
| `QA2` | [#153](https://github.com/iurii-izman/voiceforge/issues/153) | P0 | Backend | Вернуть local type gate в зелёное состояние (`mypy`) |
| `QA3` | [#154](https://github.com/iurii-izman/voiceforge/issues/154) ✓ | P1 | Backend | Разгрузить backend/core/CLI Sonar hotspots и duplicated literals (closed 2026-03-09) |
| `QA4` | [#155](https://github.com/iurii-izman/voiceforge/issues/155) ✓ | P1 | Testing | Снять test-only Sonar debt без потери coverage и читаемости (closed 2026-03-09) |
| `QA5` | [#156](https://github.com/iurii-izman/voiceforge/issues/156) ✓ | P1 | DevOps | Почистить shell/python utility scripts под Sonar (closed 2026-03-09) |
| `QA6` | [#157](https://github.com/iurii-izman/voiceforge/issues/157) ✓ | P2 | Frontend | Почистить desktop/frontend Sonar backlog (closed 2026-03-09) |

---

## 3. Recommended order

### Wave QA-A

- `QA1` → GitHub-visible security debt
- `QA2` → mypy / local gate parity

### Wave QA-B

- `QA3` → Python source hotspots
- `QA5` → script/devops cleanup

### Wave QA-C

- `QA4` → tests
- `QA6` → desktop/frontend

Логика простая: сначала внешне видимые и blocking debt-сигналы, потом core source, затем tests/desktop.

---

## 4. Practical rule

Для этой remediation wave:

- не добавлять новые feature tracks;
- не смешивать remediation с product feature work в одном batch;
- брать по одному QA-блоку, кроме случая, когда второй блок лежит в том же subsystem и закрывается тем же verification loop.

---

## 5. Source commands

Основные команды, которыми снимался snapshot:

```bash
gh issue list --repo iurii-izman/voiceforge --state open
gh api repos/iurii-izman/voiceforge/dependabot/alerts?state=open
gh api repos/iurii-izman/voiceforge/code-scanning/alerts?state=open
uv run python scripts/sonar_fetch_issues.py
./scripts/preflight_repo.sh --with-tests
uv run ruff check src tests scripts
uv run mypy src/voiceforge/core src/voiceforge/llm src/voiceforge/rag src/voiceforge/stt --ignore-missing-imports
uv run bandit -r src -ll -q --configfile .bandit.yaml
uv run pip-audit --desc
```

---

## 6. Wave completion (2026-03-09)

**QA wave #152–#157 завершена.** Все блоки QA1–QA6 закрыты. Historical wait-state `#65` тоже снят. Следующий приоритет для автопилота теперь только bug-driven maintenance или новые подтверждённые задачи пользователя.

---

## 7. Issue #165 (Sonar Sweep) — residual triage

**Контекст:** Local cleanup по QA3–QA6 выполнен. Для закрытия [#165](https://github.com/iurii-izman/voiceforge/issues/165) нужны: remote Sonar re-analysis (происходит при push в main через `sonar.yml`) и **residual triage** оставшихся замечаний.

**Чеклист закрытия #165:**

1. **Получить актуальный список открытых замечаний:**
   `uv run python scripts/sonar_fetch_issues.py`
   (Токен: keyring `voiceforge` / `sonar_token`. Без токена шаг пропустить; зафиксировать в комментарии к issue.)

2. **Triage:** по каждому замечанию — исправить (если быстро и безопасно), либо зафиксировать в issue/runbook как «принято» (accepted) с кратким обоснованием.

3. **Re-analysis:** после любого исправления — push в main, дождаться прохода SonarCloud job; при необходимости проверить: `./scripts/check_sonar_status.sh`.

4. **Закрыть #165:** когда критические/блокирующие устранены или осознанно приняты и задокументированы.

**Triage 2026-03-15 (автопилот):**

- **Исправлено:** BLOCKER S2083 `write_update_json.py` — ограничение пути вывода репозиторием (no path from user-controlled data). CRITICAL S1192 `daemon.py` — константы для дублирующихся display_name (Python/CLI, PipeWire, STT, Disk space, API keys, RAG index, PID file, Transcript DB, Audio permissions). S2583 `daemon.py` — убраны условия, всегда true (message: err_msg/warn_msg). S7682 `run_desktop_native_smoke.sh` — явный exit в конце.
- **Принято (остаток):** S3776 (cognitive complexity) в main.py, daemon.py, config.py, preflight.py, copilot-overlay.js, main.js — рефакторинг без смены поведения вынесен в отдельные итерации. S7924/S6819 (contrast, a11y) — решения по дизайну/устройству (см. what-user-must-do). S6582/S3358/S2486 и прочие desktop/main.js — батчами в следующих сессиях или приняты. S1244 (float equality) в тестах — оставлены для явных порогов. S2083/S1192/S2583/S7682 закрыты в коде.

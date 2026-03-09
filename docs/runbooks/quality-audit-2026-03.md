# Quality Audit 2026-03

**Обновлено:** 2026-03-09.

Этот runbook фиксирует пост-Phase-E quality/security debt snapshot и переводит его в автономные блоки для Project. Источники сигнала: GitHub Security, CodeQL, SonarCloud, local gates (`preflight`, `ruff`, `mypy`, `bandit`, `pip-audit`).

---

## 1. Snapshot на 2026-03-09

### GitHub

- Открытые repo issues по API: фактически остался внешний wait-state [#65](https://github.com/iurii-izman/voiceforge/issues/65).
- Открытые GitHub Security alerts: `3` (Dependabot; CodeQL alert dismissed in QA1 [#152](https://github.com/iurii-izman/voiceforge/issues/152))
  - CodeQL `py/clear-text-logging-sensitive-data`: **dismissed** (false positive — Git credential helper protocol)
  - `3` Dependabot alerts (`serialize-javascript`, `time`, `glib`) — tracked, see security-decision-log.md

### Локальные quality gates

- `./scripts/preflight_repo.sh --with-tests` — зелёный
- `ruff` — зелёный
- `bandit` — без blocking findings
- `pip-audit --ignore-vuln CVE-2025-69872` — зелёный
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
uv run pip-audit --desc --ignore-vuln CVE-2025-69872
```

---

## 6. Wave completion (2026-03-09)

**QA wave #152–#157 завершена.** Все блоки QA1–QA6 закрыты. Следующий приоритет для автопилота: roadmap (docs/plans.md), следующий P0/P1 из PROJECT-STATUS-SUMMARY по решению пользователя, или docs/governance / preflight sweep. Периодический re-check CVE #65 — по security-and-dependencies.md разд. 4.

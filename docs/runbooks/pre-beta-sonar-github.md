# Sonar и GitHub перед бета-релизом

Чеклист: привести в порядок SonarCloud и GitHub (PR, issues), затем закрыть оставшиеся проблемы в отдельном чате и выкатить следующую бету.

**Связь:** [release-and-quality.md](release-and-quality.md) (релиз), [sonar-pr-cleanup.md](sonar-pr-cleanup.md) (исторический runbook по очистке PR/Sonar), [security-and-dependencies.md](security-and-dependencies.md) (CVE, Dependabot).

---

## 1. SonarCloud

**Текущее состояние CI:** `.github/workflows/sonar.yml` — скан при push/PR в main; без `continue-on-error`; при отсутствии `SONAR_TOKEN` job не падает (skip). Quality Gate — Sonar way (Default).

**Перед бета-релизом:**

1. **Получить список открытых замечаний:**
   `uv run python scripts/sonar_fetch_issues.py`
   (Токен: keyring `voiceforge` / `sonar_token`. Без токена — пропустить шаг.)

2. **Исправить или задокументировать:** Критичные и блокирующие — починить; остальные — либо править, либо зафиксировать в next-iteration-focus как «принять по решению команды».

3. **Ветки/анализы:** При желании уменьшить шум в Sonar: [sonar-pr-cleanup.md](sonar-pr-cleanup.md) — закрыть старые PR, при необходимости вручную почистить Activity в SonarCloud.

**Итог:** Нет блокирующих замечаний по решению команды; актуальный main сканируется без падения job.

---

## 2. GitHub — Pull Request’ы

**Типичное состояние перед бета:** открыты Dependabot PR (actions, npm) и иногда pre-commit-ci.

**Действия:**

| Тип PR | Действие |
|--------|----------|
| **Dependabot (без CVE)** | Мержить по одному после прохода CI или батчем. После мержа: `gh pr merge N --delete-branch` (или кнопка «Delete branch»). |
| **Dependabot (historical CVE #65)** | Historical wait-state уже снят локально (`pip-audit` чист). Если remote alert ещё висит, закрыть как fixed/obsolete и синхронизировать `security-decision-log.md`. |
| **pre-commit-ci** | Мержить после проверки или закрыть, если не нужен автоапдейт. |

**Очистка устаревших PR (опционально):**
`uv run python scripts/cleanup_github_pr_sonar.py [--dry-run] [--days 90]` — закрывает PR без активности N+ дней и удаляет ветку; затем выводит список веток в Sonar.

**Команды:**
```bash
gh pr list --state open
gh pr merge <N> --delete-branch   # после мержа
gh pr close <N>                   # закрыть без мержа
```

---

## 3. GitHub — Issues

**Типичное состояние:**

| Issue | Тема | Действие перед бета |
|-------|------|----------------------|
| **#65** | CVE-2025-69872 (diskcache) | Historical issue закрыта; использовать только как reference в audit trail. |
| **#50** | macOS/WSL2 — исследование | По желанию: перевести в backlog или оставить открытым. |

**Итог:** Критичные issues закрыты или осознанно отложены; статус зафиксирован в next-iteration-focus.

---

## 4. Чеклист «Всё в порядке»

- [ ] Sonar: `sonar_fetch_issues.py` выполнен; критические замечания исправлены или приняты.
- [ ] GitHub PR: Dependabot без CVE — смержены или закрыты; historical CVE #65 не висит как open alert без объяснения.
- [ ] GitHub PR: pre-commit-ci и прочие — решены (merge/close).
- [ ] GitHub Issues: historical `#65` закрыт; #50 по решению (backlog или open).
- [ ] После порядка: в следующем чате — закрыть оставшиеся проблемы (если есть), затем релиз следующей беты по [release-and-quality.md](release-and-quality.md).

---

## 5. После приведения в порядок

1. Обновить `docs/runbooks/next-iteration-focus.md`: блок «Следующий шаг» = «Закрыть оставшиеся проблемы (см. pre-beta-sonar-github), затем релиз беты».
2. Релиз беты: версия и тег по [release-and-quality.md](release-and-quality.md); чеклист раздела 1 (verify_pr, smoke, check_cli_contract, теги, CHANGELOG).

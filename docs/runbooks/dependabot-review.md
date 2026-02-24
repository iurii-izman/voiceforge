# Dependabot: проверка и закрытие алертов

Один источник: **GitHub → Repository → Security → Dependabot alerts**.

## Шаги

1. Открыть [Dependabot alerts](https://github.com/iurii-izman/voiceforge/security/dependabot) (или репо → Security → Dependabot).
2. Для каждого алерта (например 1 moderate):
   - **Принять:** открыть предложенный PR (Dependabot создаёт PR с обновлением зависимости), проверить тесты, смержить.
   - **Отложить:** Dismiss alert с комментарием (e.g. "False positive", "Accept risk until next quarter").
3. После решения обновить этот runbook или next-iteration-focus: «Dependabot: закрыто (дата)» или «отложено до …».

## Текущий статус

- **CVE-2025-69872 (diskcache):** фиксирующей версии нет (transitive dependency, тянется через litellm). В CI уже используется `pip-audit --ignore-vuln CVE-2025-69872` (см. [security.md](security.md)). Рекомендуется **отложить алерт вручную**: Dependabot → Alert → Dismiss → «Accept risk», комментарий: «No fix version yet. See docs/runbooks/security.md. Revisit when upstream fixes.» После появления фикса в upstream — снять ignore в security.md и обновить зависимость.

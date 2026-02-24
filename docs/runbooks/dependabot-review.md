# Dependabot: проверка и закрытие алертов

Один источник: **GitHub → Repository → Security → Dependabot alerts**.

## Шаги

1. Открыть [Dependabot alerts](https://github.com/iurii-izman/voiceforge/security/dependabot) (или репо → Security → Dependabot).
2. Для каждого алерта (например 1 moderate):
   - **Принять:** открыть предложенный PR (Dependabot создаёт PR с обновлением зависимости), проверить тесты, смержить.
   - **Отложить:** Dismiss alert с комментарием (e.g. "False positive", "Accept risk until next quarter").
3. После решения обновить этот runbook или next-iteration-focus: «Dependabot: закрыто (дата)» или «отложено до …».

## Текущий статус

- На 2026-02-24: 1 moderate (см. ссылку в выводе `git push` или Security → Dependabot). Рекомендуется проверить и принять/отложить вручную.

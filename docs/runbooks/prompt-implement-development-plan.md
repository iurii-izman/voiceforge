# Промпт для реализации плана развития (новый чат)

Скопируй один из блоков ниже в начало нового чата.

---

## Вариант: сделать все оставшиеся пункты (W4, W6, roadmap #6/#8, smart trigger, PDF)

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Работай по нему без поиска по проекту. Приоритет фич — docs/roadmap-priority.md. Эффективно и дёшево; ключи в keyring; Fedora Atomic/toolbox/uv.

Сделать все оставшиеся пункты из плана развития и next-iteration-focus:

1. **W4:** GetSettings D-Bus — поле privacy_mode: либо убрать из ответа, либо явно задокументировать как алиас pii_mode (проверить контракт/доку).
2. **W6:** В main.py оставшиеся пользовательские строки (ошибки, заголовки) перевести на i18n t("key"); приоритет: сообщения об ошибках и ключевые подписи.
3. **Roadmap #6:** При необходимости углубить cost report — команда cost и/или status --detailed (проверить по коду).
4. **Roadmap #8:** Расширенные e2e — добавить/дополнить тесты на export, analyze --template, action-items update, history --output md.
5. **Smart trigger в демоне:** При срабатывании передавать template в run_analyze_pipeline (проверить daemon/smart_trigger, при необходимости добавить параметр).
6. **Экспорт PDF:** В quickstart и/или в доке явно указать, что PDF опционален и требует pandoc/pdflatex.

После каждой фичи: тесты при необходимости, config-env-contract.md при изменении контракта, CHANGELOG для user-facing. Не нарушать ADR-0001. В конце итерации обновить docs/runbooks/next-iteration-focus.md и дать промпт для следующего чата.
```

---

## Вариант: общий (сверка + план по порядку)

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md (правила, конфиг, приоритеты). Работай по нему без поиска по проекту. Приоритет фич — docs/roadmap-priority.md. Эффективно и дёшево; ключи в keyring; Fedora Atomic/toolbox/uv.

Реализовать план развития по аудиту февраля 2026: @docs/development-plan-post-audit-2026.md

Порядок:
1. Сверь пункты Части I и II с текущим кодом — что уже сделано (export, --template, Ollama, action-items update), не дублируй.
2. Часть I — задачи 1→10 по одной, начиная с первых нереализованных.
3. Часть II — W1, W2, W3, W8; затем W4, W5, W6, W7, W9, W10 по возможности.
4. После каждой фичи: тесты при необходимости, config-env-contract.md при изменении контракта, CHANGELOG для user-facing. Не нарушать ADR-0001.
```

---

Конец промпта.

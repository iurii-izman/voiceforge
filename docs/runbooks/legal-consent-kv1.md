# KV1: Legal & Consent Wording (System Audio & Retention)

Черновик формулировок для разрешения gate KV1 (#187) и включения KC11 (#183) в scope. Владелец репо утверждает или правит текст; после утверждения KV1 считается разрешённым.

**Обновлено:** 2026-03-14. **Утверждено:** 2026-03-14 (wording принят как есть; KV1 разрешён, KC11 в scope).

---

## 1. System audio — disclaimer и consent

**Где показывать:** перед первым включением записи системного звука (opt-in), в настройках и при смене источника на monitor.

**Текст (EN):**

- **Short (UI):** «System audio captures application and browser sound. Use only when you have the right to record.»
- **Consent checkbox / action:** «I understand that system audio may include third-party content and I use this feature at my own responsibility.»

**Текст (RU):**

- **Кратко (UI):** «Системный звук записывает звук приложений и браузера. Включайте только если вы имеете право на запись.»
- **Подтверждение:** «Я понимаю, что системный звук может содержать сторонний контент, и использую эту функцию на свою ответственность.»

**Поведение:** путь system audio по умолчанию выключен (`monitor_source` не задан); включение только через явный выбор источника и подтверждение (consent UX в KC11).

---

## 2. Запись по юрисдикциям

**Общее указание (docs / in-app help):**

- «Laws on recording conversations vary by jurisdiction. Ensure you have consent where required (e.g. two-party or one-party consent). VoiceForge does not provide legal advice.»
- «Требования к записи разговоров зависят от юрисдикции. Убедитесь, что у вас есть необходимое согласие. VoiceForge не даёт юридических консультаций.»

В KC11 не реализуем jurisdiction-specific логику — только универсальный disclaimer и ссылку на этот runbook.

---

## 3. Retention и хранение

**Фактическое поведение (уже в продукте):** аудио и транскрипты хранятся локально; срок хранения задаётся `retention_days` (по умолчанию 90); автоматическая очистка при старте демона и раз в 24 ч (#43, #63).

**Текст для UI/docs:**

- **EN:** «Audio and transcripts are stored locally. Retention is configurable (retention_days). Data is purged automatically beyond the retention period.»
- **RU:** «Аудио и транскрипты хранятся локально. Срок хранения настраивается (retention_days). Данные за пределами срока удаляются автоматически.»

Никаких изменений в логике retention для KV1 не требуется — только зафиксировать формулировку.

---

## 4. Решение по scope

**KC11 в scope:** да. После утверждения этого документа владелец считает KV1 разрешённым: формулировки по system audio, retention и юрисдикциям приняты; допустим старт KC11 (opt-in system audio, consent UX, scenario presets).

**Фиксация:** после утверждения — комментарий в issue #187 с текстом «KV1 разрешён: wording утверждён, KC11 в scope» и ссылкой на этот runbook; при необходимости закрытие #187.

# ADR-0006: Calendar integration (roadmap 17); CalDAV first

Status: Accepted

## Context

- Roadmap 17: интеграция с календарём — триггер «встреча началась» для listen/analyze, опционально метаданные встречи.
- Варианты: CalDAV (Nextcloud, Radicale, Apple), Google Calendar API, локальные календари. Требуется выбор первого провайдера и способа опроса (push редок для календарей).

## Decision

- **Первый провайдер:** CalDAV. Один протокол покрывает Nextcloud, Radicale, Apple Calendar и др.; не требует OAuth2 для базового сценария.
- **Аутентификация:** URL календаря, логин и пароль (или токен) хранятся в keyring (сервис `voiceforge`). Имена ключей — по [keyring-keys-reference.md](../runbooks/keyring-keys-reference.md) при добавлении (например `caldav_url`, `caldav_password`).
- **Опрос:** интервал опроса (например 1–2 минуты) «есть ли событие, начавшееся в последние N минут»; без изменения кода демона на первом шаге возможна отдельная подкоманда или флаг (например `voiceforge calendar watch` или интеграция в daemon — отдельное решение).
- **Маппинг «событие началось»:** при обнаружении — запуск записи (listen) или уведомление пользователю; автоматический старт vs. кнопка «Записать» — уточнить в следующей итерации (по отзывам).
- **Google / иные провайдеры:** при появлении спроса — отдельный ADR (OAuth2, ключи в keyring).

## Consequences

- Runbook [calendar-integration.md](../runbooks/calendar-integration.md) описывает исследование и настройку; реализация CalDAV-опроса и ключей keyring — следующие инкременты.
- При добавлении ключей календаря обновить keyring-keys-reference.md.

# ADR-0002: Отдельная таблица action_items и флаг history --action-items

## Статус

Принято (2026-02).

## Контекст

Action items сейчас хранятся только в JSON-колонке `analyses.action_items`. Для cross-session трекинга и вывода списка задач по всем сессиям нужна отдельная таблица с полем статуса (open/done/cancelled), обновляемым при `action-items update`.

## Решение

- **Миграция 005**: таблица `action_items` (id, session_id, idx_in_analysis, description, assignee, deadline, status). Миграция 004 уже занята под template (004_add_template.sql), поэтому новая миграция — 005.
- При записи сессии (`log_session`) дублировать action items в таблицу `action_items` (источник правды для списка и статусов — таблица; JSON в analyses остаётся для совместимости и деталей сессии).
- Команда **action-items update** при сохранении обновляет статусы в таблице (UPDATE action_items SET status=? WHERE session_id=? AND idx_in_analysis=?).
- **history --action-items** (флаг к существующей команде, ADR-0001 не нарушается): вывод списка action items из таблицы (cross-session), с указанием session_id и статуса.

## Последствия

- Старые сессии: в таблице записей не будет до следующих analyze; для них `history --action-items` покажет только новые. Опциональный backfill не делаем в первой итерации.
- Файл `action_item_status.json` остаётся для обратной совместимости; при наличии таблицы приоритет у БД.

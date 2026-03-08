# Architecture

- **overview.md** — пайплайн, модули, runtime flow (mermaid). Раньше runtime flow был отдельным файлом — сейчас включён сюда.
- **voiceforge-arch.jsx** — интерактивный визуал (пайплайн, UI-слои, RAM, roadmap); для просмотра нужен React-рантайм.

## Ключевые решения (блок 93)

Архитектурные решения зафиксированы в **ADR**: [../adr/README.md](../adr/README.md).

| Тема | Где |
|------|-----|
| D-Bus как единственный бэкенд десктопа | ADR 0004 |
| Keyring для секретов (API, CalDAV, Telegram) | ADR 0005, 0006; [runbooks/keyring-keys-reference.md](../runbooks/keyring-keys-reference.md) |
| Хранение настроек десктопа | tauri-plugin-store (файл в данных приложения); см. план блоков 21–30 |
| Контракт D-Bus (envelope, версии) | [core/contracts.py](../../src/voiceforge/core/contracts.py), GetApiVersion / GetVersion |

Операционные доки (ТЗ для Cursor, сверка с планом) — в `docs/runbooks/`.

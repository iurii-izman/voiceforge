# KV5: Platform Expansion Gate — решение

**Issue:** [#191](https://github.com/iurii-izman/voiceforge/issues/191)
**Обновлено:** 2026-03-14.

---

## Решение (go/no-go)

**Остаёмся Linux-only.** Расширение на Windows/macOS не начинаем; платформенная граница — только Linux (PipeWire, Tauri desktop на Linux).

- **Go/no-go:** no-go на platform expansion в текущей фазе.
- **Support boundary:** поддерживаемый десктоп — Linux; Windows/macOS не в scope.
- **Experimental vs supported:** экспериментальной кроссплатформы нет; при необходимости вернуться к вопросу — только после явного нового решения (revisit в issue #191 или новом gate).

---

## Следствие для программы

- **KV5 разрешён:** gate снят решением «Linux-only».
- **KC13 · Adaptive intelligence and extensibility** разблокирован: агент может брать в работу без ожидания расширения на другие ОС. Scope KC13 — адаптивная логика, расширяемость, плагины/API в рамках Linux; портирование десктопа на другие ОС в KC13 не входит.

См. также: [phase-e-decision-log.md](phase-e-decision-log.md) (E21 macOS/Windows = Defer), [copilot-program-map.md](copilot-program-map.md).

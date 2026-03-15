# Аудит vs код: что сделано, что не сделано (2026-03)

Сравнение планов/аудита с реальным состоянием кода по состоянию на релиз 1.0.0-beta.1.

---

## 1. Knowledge Copilot Program (главный трек)

| Блок | Issue | В коде | % | Примечание |
|------|------|--------|---|------------|
| KD1–KD3 | #170–#172 | Done | 100 | Решения зафиксированы, контракты в архитектуре |
| KC1 | #173 | Done | 100 | Bootstrap, program map, traceability |
| KC2 | #174 | Done | 100 | Overlay, second window, hotkey, recording indicator |
| KC3 | #175 | Done | 100 | Capture runtime, pre-roll, 30s, stt_ambiguous |
| KC4 | #176 | Done | 100 | Tiny STT copilot path |
| KC5 | #177 | Done | 100 | Evidence-first RAG, groundedness, citations |
| KC6 | #178 | Done | 100 | Fast-track: Answer, Do/Don't, Clarify |
| KC7 | #179 | Done | 100 | Deep track, Risk/Strategy/Emotion |
| KC8 | #180 | Done | 100 | Main-window copilot, settings |
| KC9 | #181 | Done | 100 | Knowledge UI, context packs |
| KC10 | #182 | Done | 100 | Mode cloud/hybrid/offline, get_effective_llm |
| KC11 | #183 | **Не сделан** | 0 | Заблокирован KV1 (legal/consent) |
| KC12 | #184 | Done | 100 | Pro cards, objections, follow-up, refine |
| KC13 | #185 | **Не сделан** | 0 | Заблокирован KV5 (platform gate) |
| KC14 | #186 | Done | 100 | Release gate, latency doc, failure UX, idle-unload |

**Итого по программе:** 13 из 15 KC реализованы в коде (~87%). 2 блока (KC11, KC13) не начаты из-за user gates.

---

## 2. Phase E (Productization) и предшествующие планы

| Область | По плану | В коде | % | Не сделано / отложено |
|---------|----------|--------|---|------------------------|
| W1–W20 (audit steps) | 20 | 20 | 100 | — |
| Phase E E1–E19 (#124–#142) | 19 | 19 | 100 | — |
| Desktop stabilization DS1–DS7 | 7 | 7 | 100 | — |
| Knowledge Copilot KD+KC+KV | 3+14+5 | 3+13+0 | — | KC11, KC13; KV не «реализуются» кодом |

---

## 3. Что в коде не доведено или частично

| Компонент | Статус | % | Детали |
|-----------|--------|---|--------|
| SonarCloud замечания | Частично | ~15 | Исправлены S1192 (константы); остаются S3776 (cognitive complexity), S7924 (contrast), S1244 (float equality), S3516 (capture.py), S6819/S7785 и др. — см. `sonar_fetch_issues.py` |
| Coverage (omit) | Частично | ~70 | main.py, daemon.py, diarizer, часть rag/llm — всё ещё в omit; целевой fail_under=75 |
| System audio / scenario presets | Не сделано | 0 | KC11; ждёт KV1 |
| Adaptive intelligence / extensibility | Не сделано | 0 | KC13; ждёт KV5 |
| Stealth mode, card history | Не сделано | 0 | Явно вынесены за KC10; отдельные блоки |
| Web UI / Telegram / RAG watcher | Freeze | — | Maintenance-only по phase-e-decision-log |
| Dependabot / security alerts | Есть открытые | — | 3 vulnerabilities (1 high, 2 moderate) в репо; не блокируют релиз по текущей политике |

---

## 4. Процент «общей готовности» (оценочно)

- **По Knowledge Copilot (продуктовый трек):** ~87% (13/15 KC; 2 заблокированы gates).
- **По инженерному аудиту (Phase A–D, E, desktop):** реализованные блоки закрыты; остаются долг (Sonar, часть coverage, security alerts).
- **По «Daily Driver» (PROJECT-STATUS-SUMMARY):** оценка 35/100 против эталона 85 — разрыв в онбординге, одномодовом сценарии, явной обработке ошибок; часть закрыта E1–E19 и Copilot, но не всё.

---

## 5. Сводка «что вообще не сделано»

1. **KC11** — system audio, scenario presets (блокирует KV1).
2. **KC13** — adaptive intelligence, extensibility (блокирует KV5).
3. **KV1–KV5** — не «реализация», а решения/подписи пользователя; без них часть функционала не включается.
4. **Полное прохождение Sonar** — остаются complexity, contrast, float equality, отдельные BLOCKER/MAJOR.
5. **Снятие omit с main/daemon/diarizer** — требует дополнительных тестов без OOM.
6. **Закрытие Dependabot alerts** — по решению команды (allowlist или обновление зависимостей).
7. **Stealth mode, card history** — запланированы после KC10, отдельными задачами.
8. **Platform expansion (Windows/macOS)** — отложено до разрешения KV5.

---

## 6. Связанные документы

- [PROJECT-STATUS-SUMMARY.md](PROJECT-STATUS-SUMMARY.md) — оценки Engineering / Daily Driver.
- [copilot-program-map.md](copilot-program-map.md) — карта KD/KC/KV.
- [phase-e-decision-log.md](phase-e-decision-log.md) — scope guard, freeze, defer.
- [pre-beta-sonar-github.md](pre-beta-sonar-github.md) — чеклист Sonar/GitHub перед бета.

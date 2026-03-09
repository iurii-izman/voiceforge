# VoiceForge: Project Status & Productization Roadmap

**Обновлено:** 2026-03-09. **Версия:** 0.2.0-alpha.2. **Стадия:** Phase E — Daily Driver.
**Предыдущий цикл (#97-#123):** закрыт полностью; архив: [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md).

---

## 1. Текущее состояние: Engineering Score vs Daily Driver Score

Проект прошёл Phase A-D (Stabilize → Hardening → Scale → Productize). Техническая база зрелая. Главный gap — **продуктовый, не технический.**

### Engineering Score (оценка по коду/инфраструктуре)

Предыдущий clean-room audit: **~80.0/100** (эталон ~86.5/100).

| Направление | Текущее | Эталон | Gap | Ключевой вывод |
|---|---|---|---|---|
| Core architecture & modules | 67 | 84 | 17 | Hotspots в main.py, server.py, main.js; после #114 glue компактнее |
| Audio / STT / diarization | 80 | 86 | 6 | diarizer.py остаётся heavy boundary; streaming STT работает |
| RAG / data / storage | 81 | 88 | 7 | Index/search/restore lifecycle проверен; ONNX-heavy paths — manual |
| LLM / prompts / PII | 78 | 87 | 9 | Router coverage 91%; non-Claude caching — research |
| Interfaces & integrations | 76 | 85 | 9 | Sync/async glue тоньше; drift risk при изменениях |
| Testing & QA | 82 | 86 | 4 | Coverage 60% (target 75%); targeted suites для ключевых модулей |
| Security & dependency hygiene | 82 | 89 | 7 | fs.py 0700/0600 baseline; #65 CVE — external wait |
| Observability & runtime ops | 79 | 88 | 9 | OTel + Prometheus + Jaeger proof path; live execution manual |
| CI/CD & release / packaging | 81 | 87 | 6 | Release proof scripts; updater disabled |
| Documentation & governance | 75 | 86 | 11 | 15+ runbooks, 6 ADR; residual drift |

### Daily Driver Score (оценка «тихий помощник»)

**Новый аудит (Phase E lens): 35/100** (эталон: 85/100).

| Направление | Текущее (%) | Эталон (%) | Gap | Вес |
|---|---|---|---|---|
| **Daily Driver Readiness** | 35 | 85 | 50 | Критичный |
| **User Flow Completeness** | 55 | 90 | 35 | Критичный |
| **Error Resilience** | 60 | 85 | 25 | Критичный |
| **Onboarding & Setup** | 45 | 85 | 40 | Средний |
| **Core Logic (STT/diarization/RAG/LLM)** | 80 | 90 | 10 | Средний |
| **CLI & API** | 75 | 85 | 10 | Средний |
| **Desktop UI** | 40 | 75 | 35 | Средний |
| **Testing** | 55 | 80 | 25 | Средний |
| **CI/CD & DevOps** | 80 | 90 | 10 | Низкий |
| **Security** | 82 | 90 | 8 | Низкий |
| **Documentation** | 92 | 95 | 3 | Низкий |
| **Observability** | 70 | 85 | 15 | Низкий |
| **Performance** | 65 | 80 | 15 | Средний |

### Интегральные показатели

| Метрика | Значение | Расчёт |
|---|---|---|
| **Engineering Score** | 80/100 | Взвешенное среднее по 10 техническим направлениям |
| **Daily Driver Score** | 35/100 | DDR × 2 + UF × 2 + ER × 2 + остальные × 1 |
| **Общая оценка** | 58/100 | (Engineering + Daily Driver) / 2, adjusted |
| **100% (идеал)** | Полностью автономный local-first AI assistant: setup за 2 мин, запустил и забыл, ноль ручных шагов, graceful при любых сбоях, обновляется сам |
| **Эталон (реалистичный max)** | ~85/100 | Максимум для solo-dev, Linux-only, local-first, alpha-stage проекта |
| **Текущее от эталона** | **68%** (58/85) | |
| **Текущее от идеала** | **58%** (58/100) | |

**Ключевой вывод:** Технически проект на 80/100, но продуктово — на 35/100. Разрыв закрывается не новыми фичами, а **productization: setup wizard, one-shot mode, sensible defaults, explicit error feedback, auto-start.**

---

## 2. Phase E: Productization Roadmap (21 блок)

**Доска:** [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1)
**Phase:** E · Daily Driver | **Labels:** `productization`, `autopilot` / `user-decision`

### Autopilot Blocks (Cursor реализует автономно)

| # | Issue | Блок | Priority | Effort | Area | Impact |
|---|---|---|---|---|---|---|
| E1 | [#124](https://github.com/iurii-izman/voiceforge/issues/124) | Quick Wins: Sensible Defaults & Notifications | P0 | S | Backend | +10% DDR ✓ |
| E2 | [#125](https://github.com/iurii-izman/voiceforge/issues/125) | One-Shot Meeting Mode: `voiceforge meeting` | P0 | M | Backend | +15% DDR ✓ |
| E3 | [#126](https://github.com/iurii-izman/voiceforge/issues/126) | Error Pre-Flight Checks: PipeWire, Disk, Network | P0 | M | Backend | +15% ER ✓ |
| E4 | [#127](https://github.com/iurii-izman/voiceforge/issues/127) | Explicit Failure Feedback: Diarization, RAG, Models | P0 | S | Backend | +12% ER ✓ |
| E5 | [#128](https://github.com/iurii-izman/voiceforge/issues/128) | Daemon Hardening: Auto-Start, Watchdog, Log, Shutdown | P0 | M | Backend | +12% DDR ✓ |
| E6 | [#129](https://github.com/iurii-izman/voiceforge/issues/129) | Ollama Zero-Config Fallback | P1 | S | Backend | +7% DDR ✓ |
| E7 | [#130](https://github.com/iurii-izman/voiceforge/issues/130) | Setup Wizard: `voiceforge setup` & First-Run | P1 | L | Backend | +15% Onboard ✓ |
| E8 | [#131](https://github.com/iurii-izman/voiceforge/issues/131) | Model Pre-Download & Bootstrap | P1 | S | Backend | +8% Onboard ✓ |
| E9 | [#132](https://github.com/iurii-izman/voiceforge/issues/132) | Post-Listen Auto-Analyze & Cost Estimate | P1 | M | Backend | +10% UF |
| E10 | [#133](https://github.com/iurii-izman/voiceforge/issues/133) | Output Polish: History, Export, Daily Digest | P1 | M | Backend | +10% UF |
| E11 | [#134](https://github.com/iurii-izman/voiceforge/issues/134) | Calendar Auto-Analyze & Notification Automation | P2 | L | Backend | +8% UF |
| E12 | [#135](https://github.com/iurii-izman/voiceforge/issues/135) | Testing Hardening: Coverage 75%, Real Audio, Concurrent | P1 | L | Testing | +20% Test |
| E13 | [#136](https://github.com/iurii-izman/voiceforge/issues/136) | Core Logic: Prompt Cache, Streaming CLI, Whisper Turbo | P1 | L | AI/ML | +10% Core |
| E14 | [#137](https://github.com/iurii-izman/voiceforge/issues/137) | CLI & API Polish: Rich Output, Config Show, Error Catalog | P1 | M | Backend | +10% CLI |
| E15 | [#138](https://github.com/iurii-izman/voiceforge/issues/138) | Observability: Grafana Dashboard, Alert Rules | P1 | M | DevOps | +15% Obs |
| E16 | [#139](https://github.com/iurii-izman/voiceforge/issues/139) | CI/CD Polish: Auto-Release, Nightly Smoke | P2 | M | DevOps | +10% CICD |
| E17 | [#140](https://github.com/iurii-izman/voiceforge/issues/140) | Security: SQLite Encryption, Audit Log, AppArmor | P2 | M | Security | +8% Sec |
| E18 | [#141](https://github.com/iurii-izman/voiceforge/issues/141) | Performance: SQLite WAL, Ring Buffer, Adaptive Models | P1 | M | Backend | +15% Perf |

### User Decision Blocks (требуют решения пользователя)

| # | Issue | Блок | Что решить |
|---|---|---|---|
| E19 | [#142](https://github.com/iurii-izman/voiceforge/issues/142) | Desktop UI Strategy | Invest (E2E + tray + hotkeys) vs Freeze vs Replace with SPA |
| E20 | [#143](https://github.com/iurii-izman/voiceforge/issues/143) | Surface Area Freeze | Web UI / Telegram / Calendar / RAG Watcher: freeze vs invest |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | Beyond Boundaries | macOS, SaaS, GPU, browser extension, PostgreSQL и др. |

### Порядок выполнения (рекомендуемый)

**Wave 1 — P0 блокеры (2-3 недели, DDR 35→55):**
```
E1 ✓ → E2 ✓ → E3 ✓ → E4 ✓ → E5 ✓
```

**Wave 2 — P1 core (3-4 недели, DDR 55→70):**
```
E6 ✓ → E7 ✓ → E8 ✓ → E9 → E10 → E18
```

**Wave 3 — P1 quality (2-3 недели):**
```
E12 → E13 → E14 → E15
```

**Wave 4 — P2 polish (2-3 недели, DDR 70→78):**
```
E11 → E16 → E17
```

**Параллельно:** E19, E20, E21 — user decisions, влияют на scope Wave 3-4.

---

## 3. Confidence Checklist

| Функция | Работает? | Без ручных шагов? | При сбоях? | С хорошим UX? | Verdict |
|---|---|---|---|---|---|
| Audio capture (PipeWire) | ✅ | ⚠️ | ⚠️ | ⚠️ | Almost |
| STT (Whisper) | ✅ | ⚠️ | ✅ | ⚠️ | Almost |
| Diarization (pyannote) | ✅ | ❌ | ⚠️ | ❌ | WIP |
| LLM analysis | ✅ | ⚠️ | ✅ | ✅ | Almost |
| RAG search | ✅ | ❌ | ✅ | ⚠️ | WIP |
| History/search | ✅ | ✅ | ✅ | ⚠️ | Almost |
| Export (MD/PDF) | ✅ | ⚠️ | ✅ | ✅ | Almost |
| Daemon mode | ✅ | ❌ | ⚠️ | ✅ | WIP |
| Web UI | ✅ | ✅ | ✅ | ⚠️ | Almost |
| Desktop (Tauri) | ⚠️ | ❌ | ❓ | ⚠️ | WIP |
| Calendar (CalDAV) | ✅ | ❌ | ✅ | ⚠️ | WIP |
| Telegram bot | ✅ | ⚠️ | ✅ | ✅ | Almost |
| Cost tracking | ✅ | ✅ | ✅ | ✅ | **Ready** |
| Backup | ✅ | ✅ | ✅ | ✅ | **Ready** |
| PII redaction | ✅ | ✅ | ✅ | ✅ | **Ready** |

---

## 4. Friction Map (12 точек трения)

| # | Friction | Severity | Решается блоком |
|---|----------|----------|-----------------|
| F1 | Keyring setup — 3+ ручных команды + HF license | 🟢 | E7 (wizard) ✓ |
| F2 | Первый download моделей без прогресса | 🟢 | E8 ✓, E3 |
| F3 | Два терминала для daemon + listen | 🟢 | E2 (meeting) ✓ |
| F4 | Нет guided wizard / post-install guidance | 🟢 | E7 (setup) ✓ |
| F5 | OOM при diarization — тихий skip | 🟡 | E4 (feedback) |
| F6 | Нет auto-start daemon | 🟢 | E5 (systemd) ✓ |
| F7 | Нет cost estimate до analyze | 🟡 | E9 |
| F8 | PipeWire check отсутствует в bootstrap | 🟡 | E1, E3 |
| F9 | Обновление только ручное (git pull) | 🟡 | E16 (CI/CD) |
| F10 | Log rotation отсутствует для daemon | 🟢 | E5 (journald) ✓ |
| F11 | Нет fallback на Ollama | 🟢 | E6 ✓ |
| F12 | ring.raw не чистится при остановке | 🟢 | E5 ✓ |

---

## 5. Риски «кажется готовее, чем есть»

1. **🔴 Desktop UI:** Tauri app существует, но E2E flow не проверен
2. **🔴 Diarization:** Тихо пропускается у 70% пользователей (нет HF token)
3. **🟡 RAG:** Требует ручного index; analyze не сообщает о пустом контексте
4. **🟡 Offline packaging:** Flatpak/AppImage скрипты есть, GA не проверен в CI
5. **🟡 Smart trigger:** Реализован, но выключен по умолчанию

---

## 6. Прогноз

| Сценарий | Daily Driver Score | Время | Что получаем |
|---|---|---|---|
| **Сейчас** | 35 | — | Мощный engineering prototype |
| **Wave 1 (P0 блокеры)** | 55 | 2-3 нед | «Могу пользоваться каждый день без боли» |
| **Wave 1+2 (beta)** | 70 | 6-8 нед | «Могу показать коллеге, настроит за 10 мин» |
| **All waves (target)** | 78 | 3-4 мес | Тихий ежедневный помощник |
| **Эталон (max)** | 85 | — | Реалистичный max для solo/Linux/local-first |
| **Идеал (100%)** | 100 | — | Полностью автономный AI assistant |

---

## 7. External Risks & Wait States

| Item | Статус | Действие |
|---|---|---|
| **#65 CVE-2025-69872** | Waiting upstream | Снять `--ignore-vuln` после fix в diskcache/instructor |
| **Sonar S3776 hotspots** | 8 мест | Будет решаться в рамках E-блоков при рефакторинге |
| **Pre-commit на хосте** | Python 3.12 в toolbox 43 | `git commit --no-verify` на хосте без 3.12 |

---

## 8. Cursor Autopilot: как работать с E-блоками

**Формат:** каждый E-блок = 1 GitHub issue с чеклистом, labels `autopilot` + `phase:E`.

**Batching discipline:**
- Брать 1 E-блок за сессию (max 2 если в одном subsystem)
- E1-E5 — строго по порядку (Wave 1)
- E6-E18 — по priority, можно параллелить несвязанные
- E19-E21 — только после решения пользователя

**В конце каждой сессии:**
1. Targeted tests по изменённой поверхности
2. Commit + push (Conventional Commits, `Closes #N`)
3. Обновить этот документ (таблица issue numbers, score progress)
4. Обновить [next-iteration-focus.md](next-iteration-focus.md)
5. Выдать prompt для следующего чата

---

## 9. Промпт для старта Phase E

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md.

Режим: максимальный автопилот, Phase E productization. Реализовать блоки E1-E18 по порядку Wave 1→2→3→4. Каждый блок — отдельный GitHub issue с label `autopilot` и `phase:E`. Брать 1 блок за сессию, доводить до конца: код, тесты, docs sync, commit + push, обновить PROJECT-STATUS-SUMMARY и next-iteration-focus.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring. Тесты: targeted subset, не полный pytest (OOM risk). Pre-commit в toolbox.

Задача: взять верхний незакрытый E-блок из Wave 1 (E1→E5). Открыть issue на GitHub, перевести в In Progress, реализовать по чеклисту, targeted tests, commit с `Closes #N`, Done на доске. Обновить docs. Выдать prompt для следующего чата.
```

---

## Архив предыдущих циклов

**Phase A-D (#55-#73):** [plans.md](../plans.md), [audit/audit.md](../audit/audit.md)
**Score-to-100 (#97-#123):** [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md)
**Старый PROJECT-STATUS-SUMMARY:** [archive/runbooks/PROJECT-STATUS-SUMMARY-pre-E.md](../archive/runbooks/PROJECT-STATUS-SUMMARY-pre-E.md)

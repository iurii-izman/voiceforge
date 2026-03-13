# VoiceForge: Project Status & Productization Roadmap

**Обновлено:** 2026-03-13 (Knowledge Copilot program bootstrapped; `KD1-KD3` and `KC1` seeded/closed; next active block = `KC2`; `#164/#165` remain background hardening). **Версия:** 0.2.0-alpha.2. **Стадия:** Knowledge Copilot program active / maintenance hardening in background.
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
| Testing & QA | 82 | 86 | 4 | Coverage target 75% (fail_under=75); E12 real-audio, concurrent, failure injection, CLI snapshots |
| Security & dependency hygiene | 84 | 89 | 5 | fs.py 0700/0600 baseline; `pip-audit` снова чист; remaining alerts tracked in security-decision-log |
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

## 2. Knowledge Copilot Program

**Главный source of truth:** [voiceforge-copilot-architecture.md](../voiceforge-copilot-architecture.md)
**Операционная карта:** [copilot-program-map.md](copilot-program-map.md)
**Доска:** [GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1)
**Labels:** `copilot-program`, `decision-locked`, `autopilot`, `primary-track`, `user-decision`

### Program Shape

Новый главный трек поверх maintenance режима:

- `KD` — decision-locked policy issues; создаются и закрываются сразу
- `KC` — большие autopilot implementation blocks; это основной execution track
- `KV` — user/external gates; в проекте существуют сразу, но не реализуются кодом до явного решения

### Decision / Bootstrap Blocks

| Prefix | Issue | Статус | Роль |
| --- | --- | --- | --- |
| KD1 | [#170](https://github.com/iurii-izman/voiceforge/issues/170) | Done | Product charter: Knowledge Copilot positioning, personas, scenarios |
| KD2 | [#171](https://github.com/iurii-izman/voiceforge/issues/171) | Done | UX contract: push-to-capture, calm technology, max 3 cards |
| KD3 | [#172](https://github.com/iurii-izman/voiceforge/issues/172) | Done | Architecture contract: RAG-first, hybrid default, single orchestrator |
| KC1 | [#173](https://github.com/iurii-izman/voiceforge/issues/173) | Done | Program bootstrap & traceability |

### Main Execution Order

**Следующий executable block:** [#174](https://github.com/iurii-izman/voiceforge/issues/174) `KC2 · Overlay Shell & Input Model`

| Wave | Issues | Статус | Что реализуем |
| --- | --- | --- | --- |
| Wave 1 MVP Core | [#174](https://github.com/iurii-izman/voiceforge/issues/174) → [#175](https://github.com/iurii-izman/voiceforge/issues/175) → [#176](https://github.com/iurii-izman/voiceforge/issues/176) → [#177](https://github.com/iurii-izman/voiceforge/issues/177) → [#178](https://github.com/iurii-izman/voiceforge/issues/178) | Active | Overlay shell, capture runtime, streaming STT, evidence-first RAG, fast-track cards |
| Wave 2 MVP Complete | [#179](https://github.com/iurii-izman/voiceforge/issues/179) → [#180](https://github.com/iurii-izman/voiceforge/issues/180) | Todo | Deep track/session memory, main-window copilot integration |
| Wave 2 V2 Surface | [#181](https://github.com/iurii-izman/voiceforge/issues/181) | Todo | Knowledge management and context packs |
| Wave 3 V2 Expansion | [#182](https://github.com/iurii-izman/voiceforge/issues/182) → [#183](https://github.com/iurii-izman/voiceforge/issues/183) | Todo | Explicit mode system, offline/hybrid maturity, system audio and scenario presets |
| Wave 4 V3 / Pro / Frontier | [#184](https://github.com/iurii-izman/voiceforge/issues/184) → [#185](https://github.com/iurii-izman/voiceforge/issues/185) → [#186](https://github.com/iurii-izman/voiceforge/issues/186) | Todo | Pro cards, adaptive intelligence, copilot QA/reliability/release evidence |

### Manual / External Gates

| Gate | Issue | Timing | Why it cannot be auto-completed |
| --- | --- | --- | --- |
| KV1 | [#187](https://github.com/iurii-izman/voiceforge/issues/187) | Before KC11 | Legal/consent wording for system audio and retention |
| KV2 | [#188](https://github.com/iurii-izman/voiceforge/issues/188) | Before KC2 completion | Overlay visual sign-off and intrusiveness review |
| KV3 | [#189](https://github.com/iurii-izman/voiceforge/issues/189) | After KC6 | Real pilot validation with the primary persona |
| KV4 | [#190](https://github.com/iurii-izman/voiceforge/issues/190) | Before commercial packaging | Business/pricing/packaging direction |
| KV5 | [#191](https://github.com/iurii-izman/voiceforge/issues/191) | Before KC13 | Explicit platform expansion go/no-go |

### Maintenance Backlog (Background Only)

- [#165](https://github.com/iurii-izman/voiceforge/issues/165) — Sonar sweep residual triage
- [#164](https://github.com/iurii-izman/voiceforge/issues/164) — remaining Linux desktop `glib` alert

Они остаются открытыми, но больше не определяют основной execution order, пока не появится blocking regression.

---

## 3. Phase E: Productization Roadmap (21 блок)

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
| E9 | [#132](https://github.com/iurii-izman/voiceforge/issues/132) | Post-Listen Auto-Analyze & Cost Estimate | P1 | M | Backend | +10% UF ✓ |
| E10 | [#133](https://github.com/iurii-izman/voiceforge/issues/133) | Output Polish: History, Export, Daily Digest | P1 | M | Backend | +10% UF ✓ |
| E11 | [#134](https://github.com/iurii-izman/voiceforge/issues/134) | Calendar Auto-Analyze & Notification Automation | P2 | L | Backend | +8% UF ✓ |
| E12 | [#135](https://github.com/iurii-izman/voiceforge/issues/135) | Testing Hardening: Coverage 75%, Real Audio, Concurrent | P1 | L | Testing | +20% Test ✓ |
| E13 | [#136](https://github.com/iurii-izman/voiceforge/issues/136) | Core Logic: Prompt Cache, Streaming CLI, Whisper Turbo | P1 | L | AI/ML | +10% Core ✓ |
| E14 | [#137](https://github.com/iurii-izman/voiceforge/issues/137) | CLI & API Polish: Rich Output, Config Show, Error Catalog | P1 | M | Backend | +10% CLI ✓ |
| E15 | [#138](https://github.com/iurii-izman/voiceforge/issues/138) | Observability: Grafana Dashboard, Alert Rules | P1 | M | DevOps | +15% Obs ✓ |
| E16 | [#139](https://github.com/iurii-izman/voiceforge/issues/139) | CI/CD Polish: Auto-Release, Nightly Smoke | P2 | M | DevOps | +10% CICD ✓ |
| E17 | [#140](https://github.com/iurii-izman/voiceforge/issues/140) | Security: SQLite Encryption, Audit Log, AppArmor | P2 | M | Security | +8% Sec ✓ |
| E18 | [#141](https://github.com/iurii-izman/voiceforge/issues/141) | Performance: SQLite WAL, Ring Buffer, Adaptive Models | P1 | M | Backend | +15% Perf ✓ |

### Decision Outcomes (зафиксировано 2026-03-09)

Подробный policy-документ: [phase-e-decision-log.md](phase-e-decision-log.md).

| # | Issue | Решение | Что это значит для автопилота |
|---|---|---|---|
| E19 | [#142](https://github.com/iurii-izman/voiceforge/issues/142) | **Invest in Tauri** | Tauri становится primary GUI surface. После Wave 3 брать desktop-first track: E2E flow, tray, hotkeys, packaging verification. |
| E20 | [#143](https://github.com/iurii-izman/voiceforge/issues/143) | **Web UI / Telegram / RAG Watcher = Freeze** | Эти surfaces переводятся в maintenance-only: bugfix, contract parity, reliability. Без SPA/bot-first/management-UI expansion. |
| E20 | [#143](https://github.com/iurii-izman/voiceforge/issues/143) | **Calendar = Invest narrow** | Разрешён только узкий scope: CalDAV auto-listen / auto-analyze / notify. Без новых providers и platform expansion. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Managed packaging = Accept later** | Отдельный будущий трек после Linux beta / stable desktop release proof. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Defer:** macOS/Windows, browser extension, GPU, Whisper.cpp/MLX | Вернуться только при достижении конкретных триггеров из decision log. |
| E21 | [#144](https://github.com/iurii-izman/voiceforge/issues/144) | **Reject for current phase:** SaaS, Web-only main UI, collaborative notes, PostgreSQL, fine-tuning | Не открывать эти направления в Phase E без нового решения пользователя. |

**Project markers:** `#142 = decision-locked + primary-track`, `#143 = decision-locked + freeze + maintenance-only`, `#144 = decision-locked` + future `defer/accept-later` placeholders. Рабочие фильтры и taxonomy описаны в [planning.md](planning.md).

**Future placeholders on board:** `#148` managed packaging, `#149` macOS/Windows, `#150` browser extension, `#151` GPU / Whisper.cpp / MLX.

### Порядок выполнения (рекомендуемый)

**Wave 1 — P0 блокеры (2-3 недели, DDR 35→55):**
```
E1 ✓ → E2 ✓ → E3 ✓ → E4 ✓ → E5 ✓
```

**Wave 2 — P1 core (3-4 недели, DDR 55→70):**
```
E6 ✓ → E7 ✓ → E8 ✓ → E9 ✓ → E10 ✓ → E18 ✓
```

**Wave 3 — P1 quality (2-3 недели):**
```
E12 ✓ → E13 ✓ → E14 ✓ → E15 ✓
```

**Wave 3.5 — Desktop-first frontend (после E15):**
```
E19 (#142) ✓ → Tauri E2E flow, tray, hotkeys, packaging verification
```

**Entry gate для E19:** перед стартом desktop-first track должны быть закрыты E13, E14 и E15, а scope policy из [phase-e-decision-log.md](phase-e-decision-log.md) обязан оставаться без расширения Web UI / Telegram / RAG watcher beyond maintenance-only.

**Wave 4 — P2 polish (2-3 недели, DDR 70→78):**
```
E11 (narrow CalDAV scope) ✓ → E16 ✓ → E17 ✓
```

**Scope guard:** E20/E21 больше не требуют решения пользователя; их policy уже зафиксирован в [phase-e-decision-log.md](phase-e-decision-log.md). QA-wave не должна открывать новые feature tracks.

**Post–Wave 4 (2026-03-09):** Все autopilot E-блоки (E1–E19, #124–#142) закрыты. Feature-track автопилот на этом завершён. Дальше идёт отдельная remediation wave QA1-QA6 по security, Sonar и local gates. Placeholders #148–#151 не активировать.

### Post-QA: Desktop Stabilization Wave

После закрытия QA wave следующий практический приоритет определяется уже не Sonar/quality debt, а реальными desktop UX bugs и честным desktop regression policy.

| DS | Issue | Блок | Priority | Effort | Area | Зачем |
|---|---|---|---|---|---|---|
| DS1 | [#159](https://github.com/iurii-izman/voiceforge/issues/159) ✓ | Desktop UX Stabilization · onboarding dismissal and mode recovery | P0 | M | Frontend | Убрать реальные stuck-state UX bugs из Tauri UI |
| DS2 | [#160](https://github.com/iurii-izman/voiceforge/issues/160) ✓ | Desktop Test Policy · stabilize native smoke and release evidence | P1 | M | Testing | Закреплены две канонические команды: blocking `e2e:release-gate` и advisory `e2e:native:headless` |
| DS3 | [#161](https://github.com/iurii-izman/voiceforge/issues/161) ✓ | Desktop Regression Matrix · cover state persistence and navigation recovery | P1 | M | Testing | User-visible regressions закрыты regression-тестами |
| DS4 | [#166](https://github.com/iurii-izman/voiceforge/issues/166) ✓ | Desktop GUI Audit · i18n polish and recovery consistency | P1 | M | Frontend | Runtime i18n и dashboard refresh после recovery/analyze закреплены кодом и regression coverage |
| DS5 | [#167](https://github.com/iurii-izman/voiceforge/issues/167) ✓ | Desktop Exit UX · explicit quit path and close-to-tray clarity | P1 | S | Frontend | Добавлен явный выход из приложения и regression coverage для сценария `hide to tray -> quit` |
| DS6 | [#168](https://github.com/iurii-izman/voiceforge/issues/168) ✓ | Desktop Session Detail UX · modeless detail and navigation recovery | P1 | S | Frontend | Detail view больше не блокирует навигацию после quick analyze; release gate снова стабилен |
| DS7 | [#169](https://github.com/iurii-izman/voiceforge/issues/169) ✓ | Desktop QA Plan · operationalize GUI quality loop | P1 | S | Testing | Единый operational plan для blocking gate, advisory native smoke, manual UX checklist и bug intake policy |

**Рекомендуемый порядок:**
```
desktop stabilization wave complete
```

**Почему так:** реальные stuck-state UX bugs закрыты в `#159`, policy/evidence вокруг native smoke закрыта в `#160`, regression matrix для desktop daily-driver path закрыта в `#161`, runtime GUI polish и recovery consistency добиты в `#166`, explicit quit / close-to-tray clarity закрыты в `#167`, а session-detail navigation trap закрыт в `#168`. Historical CVE wait-state `#65` тоже снят. Дальше — только новые конкретные баг-репорты.

### Maintenance / Security Follow-up

| MH | Issue | Блок | Priority | Effort | Area | Зачем |
|---|---|---|---|---|---|---|
| MH1 | [#162](https://github.com/iurii-izman/voiceforge/issues/162) ✓ | Maintenance Hardening · maintenance-mode checks and wait-state recheck | P1 | S | DevOps | Добавлен weekly maintenance re-check и канонический `check_maintenance_state.py` |
| MH2 | [#163](https://github.com/iurii-izman/voiceforge/issues/163) ✓ | Security Hardening · npm alert resolution and Rust rebaseline | P1 | S | Security | Закрыт npm native-e2e alert (`serialize-javascript`) через safe override/lock refresh |
| MH3 | [#164](https://github.com/iurii-izman/voiceforge/issues/164) | Desktop Linux GTK Refresh · resolve remaining glib Dependabot alert | P1 | M | Security | `time` alert already closed; remaining coordinated refresh = transitive `glib 0.18.5` in Linux desktop chain |
| MH4 | [#165](https://github.com/iurii-izman/voiceforge/issues/165) | Sonar Sweep · low-risk desktop and script cleanup | P1 | M | Quality | Local cleanup готов; нужен remote Sonar re-analysis и residual triage before closure |

**Рекомендуемый порядок:**
```
#165 → #164
```

### Post-Phase-E: Quality Remediation Wave

Подробный аудит: [quality-audit-2026-03.md](quality-audit-2026-03.md).

| QA | Issue | Блок | Priority | Effort | Area | Зачем |
|---|---|---|---|---|---|---|
| QA1 | [#152](https://github.com/iurii-izman/voiceforge/issues/152) ✓ | Security & Supply Chain Remediation | P0 | M | Security | Закрыть CodeQL + Dependabot, убрать GitHub-visible security debt |
| QA2 | [#153](https://github.com/iurii-izman/voiceforge/issues/153) ✓ | Local Gate Recovery | P0 | S | Backend | Вернуть `mypy` и verify-pr parity в честно зелёное состояние |
| QA3 | [#154](https://github.com/iurii-izman/voiceforge/issues/154) ✓ | Python Core/CLI Sonar Hotspots | P1 | L | Backend | Разгрузить main/daemon/CLI hotspots |
| QA4 | [#155](https://github.com/iurii-izman/voiceforge/issues/155) ✓ | Test Suite Sonar Cleanup | P1 | L | Testing | Снять test-only Sonar debt (stubs, float equality, constant booleans) |
| QA5 | [#156](https://github.com/iurii-izman/voiceforge/issues/156) ✓ | DevOps & Utility Script Sonar Cleanup | P1 | M | DevOps | Почистить bootstrap/preflight/create-issues/helper scripts |
| QA6 | [#157](https://github.com/iurii-izman/voiceforge/issues/157) ✓ | Desktop Sonar Cleanup | P2 | M | Frontend | Разобрать desktop/frontend Sonar backlog (closed 2026-03-09) |

**Рекомендуемый порядок:**
```
Wave QA-A: #152 → #153
Wave QA-B: #154 → #156
Wave QA-C: #155 → #157
```

**Почему так:** сначала GitHub-visible security debt и красные локальные quality gates, потом backend/scripts, затем tests/frontend.

---

## 4. Confidence Checklist

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
| Desktop (Tauri) | ✅ | ⚠️ | ✅ | ⚠️ | E2E flow + tray + hotkeys + packaging verify |
| Calendar (CalDAV) | ✅ | ❌ | ✅ | ⚠️ | WIP |
| Telegram bot | ✅ | ⚠️ | ✅ | ✅ | Almost |
| Cost tracking | ✅ | ✅ | ✅ | ✅ | **Ready** |
| Backup | ✅ | ✅ | ✅ | ✅ | **Ready** |
| PII redaction | ✅ | ✅ | ✅ | ✅ | **Ready** |

---

## 5. Friction Map (12 точек трения)

| # | Friction | Severity | Решается блоком |
|---|----------|----------|-----------------|
| F1 | Keyring setup — 3+ ручных команды + HF license | 🟢 | E7 (wizard) ✓ |
| F2 | Первый download моделей без прогресса | 🟢 | E8 ✓, E3 |
| F3 | Два терминала для daemon + listen | 🟢 | E2 (meeting) ✓ |
| F4 | Нет guided wizard / post-install guidance | 🟢 | E7 (setup) ✓ |
| F5 | OOM при diarization — тихий skip | 🟡 | E4 (feedback) |
| F6 | Нет auto-start daemon | 🟢 | E5 (systemd) ✓ |
| F7 | Нет cost estimate до analyze | 🟢 | E9 ✓ |
| F8 | PipeWire check отсутствует в bootstrap | 🟡 | E1, E3 |
| F9 | Обновление только ручное (git pull) | 🟡 | E16 (CI/CD) |
| F10 | Log rotation отсутствует для daemon | 🟢 | E5 (journald) ✓ |
| F11 | Нет fallback на Ollama | 🟢 | E6 ✓ |
| F12 | ring.raw не чистится при остановке | 🟢 | E5 ✓ |

---

## 6. Риски «кажется готовее, чем есть»

1. **🟢 Desktop UI:** E2E meeting flow (Record→Analyze→View→Export), tray, hotkeys, packaging verification (E19 #142)
2. **🔴 Diarization:** Тихо пропускается у 70% пользователей (нет HF token)
3. **🟡 RAG:** Требует ручного index; analyze не сообщает о пустом контексте
4. **🟡 Offline packaging:** Flatpak/AppImage скрипты есть, GA не проверен в CI
5. **🟡 Smart trigger:** Реализован, но выключен по умолчанию

---

## 7. Прогноз

| Сценарий | Daily Driver Score | Время | Что получаем |
|---|---|---|---|
| **Сейчас** | 35 | — | Мощный engineering prototype |
| **Wave 1 (P0 блокеры)** | 55 | 2-3 нед | «Могу пользоваться каждый день без боли» |
| **Wave 1+2 (beta)** | 70 | 6-8 нед | «Могу показать коллеге, настроит за 10 мин» |
| **All waves (target)** | 78 | 3-4 мес | Тихий ежедневный помощник |
| **Эталон (max)** | 85 | — | Реалистичный max для solo/Linux/local-first |
| **Идеал (100%)** | 100 | — | Полностью автономный AI assistant |

---

## 8. External Risks & Wait States

| Item | Статус | Действие |
|---|---|---|
| **#65 CVE-2025-69872** | Resolved | `pip-audit` снова чист; historical issue можно закрыть |
| **QA1 #152** | Done | CodeQL dismissed (false positive); Dependabot tracked в security-decision-log |
| **QA2 #153** | Done | mypy зелёный (transcriber: BaseException + assert; transcript_log: убрано переопределение _sqlcipher) |
| **QA3 #154** | Done | fs: get_cache_home; config→voiceforge_data_dir; status_helpers→get_cache_home; daemon: _notify_analyze_done, _calendar_try_start_listen; caldav_poll: credentials helpers |
| **QA5 #156** | Done | DevOps/scripts Sonar: bootstrap.sh, preflight_repo.sh, create_productization_issues.sh — `[[` style, explicit exit; check_docs_consistency.py path.exists; dependabot_dismiss_moderate.py explicit sys.exit(0) |
| **QA6 #157** | Done | Desktop/frontend Sonar: main.js i18n status_ready/status_analyzing, compact_daemon_ok/off via t(); platform.js JSDoc; desktopHarness envelope(); native-smoke timeouts/assert.ok |
| **Pre-commit на хосте** | Python 3.12 в toolbox 43 | `git commit --no-verify` на хосте без 3.12 |

---

## 9. Maintenance Mode: как работать после закрытия очереди

**Формат:** feature-track Phase E закрыт. QA wave `#152-#157` завершена. Desktop stabilization `#159-#161` завершена. Репо находится в maintenance mode без активного open blocker.

**Каноническая проверка:**

```bash
uv run python scripts/check_maintenance_state.py
```

Что она подтверждает:

- release-proof boundary не ушла в drift
- docs consistency остаётся зелёной
- `pip-audit` остаётся чистым и не появился новый security drift

**Если новых багов нет:**
- не разворачивать новый feature-track
- не создавать новые placeholder issues
- ограничиться periodic maintenance re-check и фиксацией состояния в [next-iteration-focus.md](next-iteration-focus.md)

**Если появляется новый подтверждённый баг:**
1. оформить issue на GitHub Project
2. перевести в `In Progress`
3. починить bug + добавить regression coverage
4. commit + push (`Closes #N`)
5. обновить этот документ и [next-iteration-focus.md](next-iteration-focus.md)

---

## Архив предыдущих циклов

**Phase A-D (#55-#73):** [plans.md](../plans.md), [audit/audit.md](../audit/audit.md)
**Score-to-100 (#97-#123):** [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md)
**Старый PROJECT-STATUS-SUMMARY:** [archive/runbooks/PROJECT-STATUS-SUMMARY-pre-E.md](../archive/runbooks/PROJECT-STATUS-SUMMARY-pre-E.md)

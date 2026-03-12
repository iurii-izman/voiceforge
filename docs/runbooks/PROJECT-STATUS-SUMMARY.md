# VoiceForge: Project Status & Productization Roadmap

**Обновлено:** 2026-03-13 (DS1 closed; release gate green; native evidence policy next). **Версия:** 0.2.0-alpha.2. **Стадия:** Post-Phase-E desktop stabilization + UX hardening.
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
| DS3 | [#161](https://github.com/iurii-izman/voiceforge/issues/161) | Desktop Regression Matrix · cover state persistence and navigation recovery | P1 | M | Testing | Закрыть user-visible regressions regression-тестами |

**Рекомендуемый порядок:**
```
#161
```

**Почему так:** реальные stuck-state UX bugs уже закрыты в `#159`, а policy/evidence вокруг native smoke теперь закрыта в `#160`; следующий логичный шаг — превращать оставшиеся user-visible desktop regressions в regression matrix в `#161`.

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
| Desktop (Tauri) | ✅ | ⚠️ | ✅ | ⚠️ | E2E flow + tray + hotkeys + packaging verify |
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
| F7 | Нет cost estimate до analyze | 🟢 | E9 ✓ |
| F8 | PipeWire check отсутствует в bootstrap | 🟡 | E1, E3 |
| F9 | Обновление только ручное (git pull) | 🟡 | E16 (CI/CD) |
| F10 | Log rotation отсутствует для daemon | 🟢 | E5 (journald) ✓ |
| F11 | Нет fallback на Ollama | 🟢 | E6 ✓ |
| F12 | ring.raw не чистится при остановке | 🟢 | E5 ✓ |

---

## 5. Риски «кажется готовее, чем есть»

1. **🟢 Desktop UI:** E2E meeting flow (Record→Analyze→View→Export), tray, hotkeys, packaging verification (E19 #142)
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
| **QA1 #152** | Done | CodeQL dismissed (false positive); Dependabot tracked в security-decision-log |
| **QA2 #153** | Done | mypy зелёный (transcriber: BaseException + assert; transcript_log: убрано переопределение _sqlcipher) |
| **QA3 #154** | Done | fs: get_cache_home; config→voiceforge_data_dir; status_helpers→get_cache_home; daemon: _notify_analyze_done, _calendar_try_start_listen; caldav_poll: credentials helpers |
| **QA5 #156** | Done | DevOps/scripts Sonar: bootstrap.sh, preflight_repo.sh, create_productization_issues.sh — `[[` style, explicit exit; check_docs_consistency.py path.exists; dependabot_dismiss_moderate.py explicit sys.exit(0) |
| **QA6 #157** | Done | Desktop/frontend Sonar: main.js i18n status_ready/status_analyzing, compact_daemon_ok/off via t(); platform.js JSDoc; desktopHarness envelope(); native-smoke timeouts/assert.ok |
| **Pre-commit на хосте** | Python 3.12 в toolbox 43 | `git commit --no-verify` на хосте без 3.12 |

---

## 8. Cursor Autopilot: как работать после Phase E

**Формат:** feature-track Phase E уже закрыт. QA wave `#152-#157` завершена. Новый источник очереди для автопилота — desktop stabilization wave `#159-#161`.

**Batching discipline:**
- Брать 1 desktop block за сессию (max 2 только если это один subsystem и один verification loop)
- Текущий execution order: `#159 → #160 → #161`
- `#160` и `#161` не должны обходить `#159`: сначала реальные UX bugs, потом policy/evidence и расширение regression matrix
- E20/E21 остаются policy-слоем; desktop stabilization не повод активировать placeholders или новые feature tracks

**В конце каждой сессии:**
1. Targeted tests по изменённой поверхности
2. Commit + push (Conventional Commits, `Closes #N`)
3. Обновить этот документ (таблица issue numbers, score progress)
4. Обновить [next-iteration-focus.md](next-iteration-focus.md)
5. Выдать prompt для следующего чата

---

## 9. Промпт для старта quality remediation wave

```
Проект VoiceForge. Контекст: @docs/runbooks/agent-context.md. Фокус: @docs/runbooks/next-iteration-focus.md. Статус: @docs/runbooks/PROJECT-STATUS-SUMMARY.md. Quality audit: @docs/runbooks/quality-audit-2026-03.md. Scope guard: @docs/runbooks/phase-e-decision-log.md. AI/tooling source of truth: @docs/runbooks/ai-tooling-setup.md.

Режим: максимальный автопилот, post-Phase-E quality remediation wave. Работать по QA-блокам `#152-#157` в порядке `QA-A → QA-B → QA-C`. Новые feature issues не создавать без отдельной задачи пользователя. Брать 1 QA-блок за сессию, доводить до конца: код, targeted tests, docs sync, GitHub Project status, commit + push, обновить PROJECT-STATUS-SUMMARY и next-iteration-focus.

Среда: Fedora Atomic, toolbox 43, uv sync --extra all. Ключи в keyring. Тесты: targeted subset, не полный pytest (OOM risk). Для infra/docs/governance cleanup сначала прогонять `./scripts/preflight_repo.sh --with-tests`. Pre-commit в toolbox.

Задача: взять верхний открытый QA-блок из next-iteration-focus, перевести issue в In Progress, реализовать по чеклисту, targeted checks, commit с `Closes #N`, Done на доске. Строго соблюдать phase-e-decision-log и не активировать policy placeholders #148-#151. Обновить docs. Выдать prompt для следующего чата.
```

---

## Архив предыдущих циклов

**Phase A-D (#55-#73):** [plans.md](../plans.md), [audit/audit.md](../audit/audit.md)
**Score-to-100 (#97-#123):** [history/closed-plans-and-roadmap.md](../history/closed-plans-and-roadmap.md)
**Старый PROJECT-STATUS-SUMMARY:** [archive/runbooks/PROJECT-STATUS-SUMMARY-pre-E.md](../archive/runbooks/PROJECT-STATUS-SUMMARY-pre-E.md)

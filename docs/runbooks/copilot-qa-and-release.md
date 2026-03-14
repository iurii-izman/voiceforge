# Copilot QA, Release & Performance (KC14)

Честный release gate, latency budgets, failure UX и политика battery/CPU для copilot path.

---

## 1. Copilot-specific release gate

**Gate:** тот же blocking desktop UI gate, что и для всего приложения: `cd desktop && npm run e2e:release-gate`. Он включает:

- Autopilot suite (в т.ч. copilot shortcut pressed/released, overlay state, capture_release, analyzing)
- Nav/sessions/settings/costs/knowledge
- A11y и visual regression по ключевым экранам

**Честная граница:** overlay и hotkey в E2E работают через mocked D-Bus; реальный глобальный shortcut и поведение overlay в native shell проверяются только advisory native smoke (`npm run e2e:native:headless`) или вручную. Матрица: [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md).

**Минимум перед релизом с copilot:** шаги 1–4 из [release-and-quality.md](release-and-quality.md) § 1.2; для copilot-специфики — e2e:release-gate проходит, включая сценарий copilot shortcut → overlay → capture_release → analyzing.

---

## 2. Latency and performance budgets

Ориентиры из [voiceforge-copilot-architecture.md](../voiceforge-copilot-architecture.md):

| Этап | Бюджет (типично) | Примечание |
|------|-------------------|------------|
| STT (tiny, 10s audio) | 0.5–1.5 s | Streaming ASR; слабый CPU до 2–3 s |
| RAG (evidence) | &lt;1 s | Локальный FTS/vector |
| LLM (fast cards, cloud) | 0.3–0.8 s TTFT | Сетевые задержки, rate limits |
| **First card (Evidence)** | **~2 s** | RAG-first |
| **Answer/Do/Don't/Clarify** | **3–5 s** (cloud) / 8–15 s (Ollama) | После STT finalize |

**Измерение:** логи daemon (structlog) и при необходимости метрики Prometheus (`voiceforge_stt_duration_seconds`, pipeline steps). Для ad-hoc замера: засечь время от CaptureStateChanged("recording") до появления карточек в overlay (по логам или вручную).

---

## 3. Failure UX (risk model)

Состояния отказа и реакция UI заданы в архитектуре, раздел «Error / Loading / Fallback states»:

| Риск | Поведение UI | Где |
|------|----------------|-----|
| Daemon down | Banner «Daemon not running», retry | Main window |
| No LLM backend (no keys, Ollama down) | Сообщение об ошибке в pipeline, overlay без LLM-карточек | Status text / overlay state |
| STT failed / silence | Сообщение «тишина» или stt_ambiguous, hint «Проверьте транскрипт» | Overlay |
| No documents | Hint «Add documents for better answers» | Overlay / Knowledge tab |
| LLM failed | Evidence Card only + «AI unavailable, showing documents only» | Overlay |

Failure UX остаётся явным в рамках этой модели; расширения (например, retry-кнопки в overlay) — отдельные задачи.

---

## 4. Battery/CPU controls and idle-unload policy

**Конфиг:** `copilot_stt_idle_unload_seconds` (по умолчанию 300). Через N секунд после последнего `capture_release` при следующем `capture_start` daemon выгружает STT-модель перед загрузкой tiny, чтобы снизить RAM/CPU при простое.

**Поведение:**

- При `capture_start`: если с момента последнего `capture_release` прошло ≥ `copilot_stt_idle_unload_seconds`, вызывается `model_manager.unload_stt()`, затем при необходимости загружается tiny.
- Значение `0` отключает idle-unload (модель не выгружается по таймауту).
- Документация конфига: [config-env-contract.md](config-env-contract.md).

---

## 5. Связанные документы

- [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md) — матрица automated/native/manual для desktop и copilot
- [release-and-quality.md](release-and-quality.md) — общий release runbook и desktop gate
- [voiceforge-copilot-architecture.md](../voiceforge-copilot-architecture.md) — latency, режимы, Error/Loading/Fallback states

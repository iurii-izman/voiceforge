# VoiceForge: Продуктово-технический и архитектурный проект для AI-суфлёра в живых разговорах

---

## Executive Summary

**VoiceForge** — real-time AI-суфлёр: удержал горячую клавишу → записал реплику/вопрос → отпустил → через 3-5 секунд получил мгновенно-глядимые карточки подсказок, построенные на ваших документах (RAG-first).

Проект уже имеет сильную базу для desktop-реализации: Tauri shell + системный трей + глобальные хоткеи + daemon-backend + IPC (D-Bus) + streaming STT + RAG (SQLite FTS5 + sqlite-vec) + LLM routing (LiteLLM + Instructor). **90% инфраструктуры уже построено.**

Ключевая «недостающая часть» — не запись как таковая, а режим **«ответ-сейчас»**: push-to-capture как UX, быстрый ASR+RAG, генерация карточек (не длинного отчёта), маркировка groundedness и работа с latency через прогрессивную выдачу.

### Рекомендуемая стратегия

- **Базовый режим:** Hybrid — локальный захват + локальный RAG + облачный LLM; при отсутствии ключей/сети — Ollama fallback.
- **MVP:** single-orchestrator с 2 параллельными LLM-вызовами (fast + deep track), один card-deck, без «зоопарка агентов».
- **RAG-first** не как лозунг, а как UI-контракт: пользователь всегда видит (а) из каких источников, (б) насколько уверенно, (в) что «модель додумала».

### Нереалистичные ожидания для управления

- «Мгновенно» после 30 секунд аудио на CPU — чаще 2-8 с. MVP опирается на стриминг ASR во время удержания и Evidence Card (RAG-only, без LLM) за 2-2.5 с.
- Whisper-семейство может «галлюцинировать» (вставлять не сказанное). Нужен «ask-to-confirm», показ transcript snippet и UX-ограничители.

---

## 1. Суть продукта и философия

### Одна сильная фраза

VoiceForge — ненавязчивый desktop-copilot, который превращает услышанный вопрос в «ответ-сейчас» за одну горячую клавишу, отдавая приоритет вашим документам.

### Core Value Proposition

1. **Сокращение когнитивного переключения.** В живом разговоре пользователь не «гуглит» и не «листает PDF», а получает 2-5 коротких карточек, которые можно прочитать за 2 секунды.
2. **Усиление качества ответа:** фактологичность через RAG-first; управляемый тон; предупреждение рисков; следующий шаг.
3. **Приватность как конкурентное преимущество:** offline-friendly, local-first, аудио никогда не покидает машину. STT всегда локальный. В облако уходит только текст (при Hybrid/Cloud режимах).

### Философия: суфлёр, не автопилот

Принципы:

1. **Пользователь — ведущий разговора.** Продукт предлагает варианты, не диктует.
2. **Invisible until needed.** В трее, без фокуса, без окна. Включение только через hotkey.
3. **Push, not pull.** Пользователь сам решает, когда записать. Система не слушает постоянно (privacy by design).
4. **Glanceable, not readable.** 1-2 предложения за 2 секунды, не теряя зрительного контакта.
5. **Documents first, model second.** Ответ из документов > ответ модели. Модель без документов — галлюцинация с красивым форматированием.
6. **Calm technology.** Максимум 3 карточки одновременно. Auto-dismiss через 60 с.

### Граница «подсказать» vs «перехватить управление»

- VoiceForge **никогда не говорит за пользователя** (нет TTS, нет auto-response).
- VoiceForge **никогда не записывает без явного действия** (нет always-on recording).
- VoiceForge **не подсказывает манипулятивные техники** (но может предупреждать о манипуляциях собеседника).
- Граница: **информация и контекст — да; скрипты поведения — нет.**

---

## 2. Целевые персоны и сценарии

### Primary Persona

**Presales-инженер / Solution Architect** — проводит демо и защищает решение перед заказчиком. Знает продукт, но не может держать в голове все детали: pricing, SLA, edge cases, compliance. Документы есть, но искать во время разговора невозможно.

### Secondary Personas

| Persona | Сценарий | Ключевая потребность |
|---|---|---|
| Account Manager | Переговоры по контракту | Risk/Objection cards, стратегия аргументации |
| Tech Lead / Architect | Архитектурные ревью, защита решений | Factual accuracy, ссылки на документацию |
| Trainer / Lecturer | Q&A после лекции | Быстрые точные ответы из материалов курса |
| Support Engineer / CSM | Escalation calls | Поиск по KB, Do/Don't по процедурам |
| Founder / Exec | Стратегические встречи | Сверхкороткие подсказки, без перегруза |

### Ключевые сценарии

1. **Demo Q&A:** заказчик задаёт вопрос → push-to-capture → карточки: короткий ответ + нюансы + «что не обещать» + «уточнить». VoiceForge находит ответ в презентации/документации за 2-3 с.
2. **Negotiation / Objection handling:** фиксируем возражение → 2-3 линии ответа + «позиция/рамка» + возможная уступка. Карточки Risk + Do/Don't.
3. **Knowledge recall:** пользователь не помнит деталь из своих документов — VoiceForge находит за 2 с через Evidence Card.
4. **Internal alignment:** спорный тезис → «риски/контр-аргументы/следующий шаг».
5. **Training assist:** преподаватель получает подсказки из учебных материалов при неожиданных вопросах.

---

## 3. Продуктовые концепции и выбор

| Концепция | Плюсы | Минусы/риски | Монетизация | Сложность |
|---|---|---|---|---|
| **A. Knowledge Copilot (push-to-capture + RAG-first)** | RAG-first = меньше галлюцинаций; privacy-friendly; enterprise-ready; core value — «ваши документы, ваши ответы» | Требует загрузки документов (onboarding friction); без документов ценность ниже | SaaS ($20-50/seat/mo), self-hosted enterprise | Средняя — RAG уже построена |
| B. Negotiation Copilot | Высокая perceived value для sales | Высокий риск плохих советов; этические вопросы | Premium ($50-100/seat/mo), узкий рынок | Высокая |
| C. Meeting Intelligence | Полный цикл записи и анализа | Красный океан (Otter, Fireflies); размывает фокус | Freemium, сложно конкурировать | Очень высокая |
| D. Offline-first Private Assistant | Уникальная ниша; defense/gov | Качество local LLM пока недостаточно; latency 5-15 с | Enterprise license, узкий TAM | Средняя |

### Выбор: Концепция A — Knowledge Copilot с push-to-capture

**Почему:** единственная концепция, где RAG-first архитектура (уже построена) — конкурентное преимущество, а не фича. Решает конкретную проблему: «я знаю, что ответ есть в моих документах, но не могу найти за 5 секунд». Минимизирует hallucination, имеет ясный путь к монетизации. Элементы Концепции B (strategy, risk cards) добавляются как Pro-mode в V2.

**Позиционирование:** «Ваши документы, ваши ответы, в реальном времени.»

---

## 4. UX и основной пользовательский флоу

### Ideal Flow: Push-to-Capture

```
[Tray idle] → [Hotkey down: запись] → [Hotkey up: анализ] → [Cards appear] → [Auto-dismiss]
     ↑                                                                              |
     └──────────────────────── цикл повторяется ────────────────────────────────────┘
```

### Пошагово с реалистичными задержками

**1. Tray-mode (idle)**
- Приложение запущено, демон работает, иконка в трее. Системный трей уже реализован (Tauri).
- Daemon-backend готов к capture/ASR/RAG/LLM без холодного старта (user service).
- Визуально: состояние idle / armed / recording / analyzing / error (маленькие статусы).
- Документы проиндексированы (RAG ready). Никакого UI на экране.

**2. Hotkey activation (Pressed)**
- Глобальные шорткаты уже поддерживают Pressed/Released в Tauri plugin.
- Новая модель: **одна клавиша** (например `Ctrl+Shift+Space`):
  - Pressed → start capture-segment
  - Released → stop capture-segment + auto-analyze
- Появляется микро-индикатор записи (красная точка 12px, пульсация).

**3. Push-to-record (удержание клавиши)**

**Критическое решение: ring buffer vs простой старт.**

| Вариант | Описание | Плюсы | Минусы |
|---|---|---|---|
| **A. Простой старт** | Pressed → реально стартуем захват; Released → стоп | Простота, приватность | Первые 100-500мс могут пропасть |
| **B. Armed + ring buffer (рекомендуется)** | ARM → ring buffer 60-120с в памяти; Pressed → start marker + pre-roll 0.5-1.5с; Released → end marker, фиксация, pipeline | Лучший UX, нет потери начала | Сложнее, privacy ring в памяти |

Рекомендация: **Вариант B** — ring buffer уже есть в коде (буферизация в памяти и получение чанков). Pre-roll 1с из ring убирает фрустрацию «пропустил начало вопроса». Автоотпускание через 30с с визуальным предупреждением на 25-й.

**4. Streaming ASR во время удержания**

Критически важно: если ASR стартует только после Release, «мгновенность» не получится. Решение: **стриминг ASR во время удержания** + finalize после Release.

В репозитории уже есть StreamingTranscriber и UI-хук для стриминга. При удержании:
- Streaming STT пишет partial транскрипт
- UI показывает текст «что слышит» (пользователь мгновенно понимает: «система услышала правильно или нет»)
- RAG search может стартовать параллельно по partial transcript

**5. Analysis-on-release flow**

| Время | Что происходит |
|---|---|
| t=0ms | Hotkey UP → read audio from RingBuffer (in-memory, 0ms I/O) |
| t=0-1500ms | STT finalize (tiny model: 10s audio → ~1s, 30s → ~2.5s). При streaming — уже есть ~95% текста |
| t=500ms | RAG search стартует параллельно (по partial transcript) |
| t=1500ms | STT завершён, RAG завершён → **Evidence Card рендерится** (RAG-only, без LLM) |
| t=1500ms | LLM fast-track call стартует (Haiku 4.5, streaming) |
| t=2000-2500ms | Первые токены LLM → Answer Card начинает заполняться |
| t=3000-4000ms | Fast-track complete → Answer + Do/Don't + Clarify cards |
| t=3500ms | (Optional) LLM deep-track call стартует |
| t=5000ms | Deep-track complete → Risk + Strategy cards |

**6. Card delivery (progressive)**

- **T+0.0s:** UI показывает overlay «Analyzing…» + transcript snippet (1-2 строки).
- **T+1.5-2.5s:** Evidence Card (RAG-only, без LLM). Пользователь уже видит ответ из документов.
- **T+3-4s:** Answer + Do/Don't + Clarify cards (LLM fast-track).
- **T+4-6s:** Risk/Strategy cards (LLM deep-track, догрузка).
- **T+>6s:** если latency высокая, остальные карточки уходят в background.

**7. Follow-up cycle**

Карточки видны 60 с, затем auto-fade. Следующий вопрос → снова hotkey → новый цикл. Предыдущие карточки заменяются.

### Критические точки задержки и UX-узкие места

| Точка | Бюджет | Риск | Mitigation |
|---|---|---|---|
| STT (tiny, 10s audio) | 500-1500ms | На слабом CPU 2-3s | Streaming ASR; tiny model для copilot |
| RAG search | 50-200ms | При >10K chunks 500ms | RRF score threshold; keyword optimization |
| LLM TTFT (cloud) | 300-800ms | Сетевые задержки; rate limits | Evidence Card first; circuit breaker |
| LLM full response | 1500-3000ms | Зависит от длины ответа | Structured output + short token limits |
| **Total first card** | **1500-2500ms** | Evidence Card (RAG-only) | — |
| **Total answer card** | **3000-5000ms** | С LLM streaming | — |
| Overlay focus steal | — | Wayland always-on-top | Layer-shell / notification fallback |
| Multiple captures | — | Очередь | Priority latest; debounce |
| Ложное ожидание мгновенности | — | Пользователь ждёт <1s | Evidence Card за 2s «закрывает» ожидание |

---

## 5. Режимы записи

### Матрица режимов

| Режим | Описание | Privacy риск | MVP? |
|---|---|---|---|
| **Mic only + Push-to-capture** | Только микрофон, запись пока зажата клавиша | Низкий | **Да** |
| System audio only | Звук приложений (Zoom/Teams) через PipeWire | Средний | V2 (opt-in) |
| Mic + System | Оба канала | Высокий | Нет |
| Toggle mode | Нажал — пишет, нажал — стоп | Средний | Уже есть |
| Auto mode (smart trigger) | По VAD | Высокий | Уже есть, не для copilot |

### Для MVP: Push-to-capture + Mic only

Причины: самый низкий privacy-риск; PipeWire capture уже работает; system audio поднимает consent-вопросы; push-to-capture — core UX-паттерн.

### Что отложить

- **System audio** → V2 с явным opt-in и предупреждением о privacy.
- **Speaker diarization в copilot mode** → не нужна для коротких фрагментов (5-15s обычно один спикер).
- **Auto mode** → V3, после валидации основного сценария.

### OS и аудиостек: честные ограничения

- **Linux/PipeWire:** можно нацеливаться на конкретные ноды (`--target`). Целевой стек для MVP.
- **Windows:** WASAPI loopback — стандартный путь, но DRM-ограничения.
- **macOS:** ScreenCaptureKit требует Screen Recording Permission.

**Кроссплатформенный системный звук — не «галочка», а отдельный roadmap. В MVP фокус на одной ОС (Linux/PipeWire).**

---

## 6. Архитектура подсказок: система карточек

### Общие принципы

1. **Одна карточка = один тип решения.** Не смешивать «ответ + риски + эмоции».
2. **Лимит текста:** glanceable = 1-3 строки (240-400 знаков); expanded = до 900-1400 знаков по клику.
3. **Визуальная семантика:** цвет = тип/статус, не «красота».
4. **Максимум 3 карточки одновременно.** Vertical stack (не grid). Сканирование глазами только вертикальное.
5. **Progressive disclosure:** 1-2 строки видны, развёрнутый контент по клику.
6. **Auto-dismiss:** 60 с для информационных, 30 с для эмоциональных.
7. **Priority trumping:** новая карточка с высшим приоритетом → нижняя сворачивается.
8. **Pin:** двойной клик закрепляет до ручного закрытия.

### Полная система карточек

| Карточка | Назначение | Когда показывать | Приоритет | Формат | Цвет (dark) | Скрытие | Версия |
|---|---|---|---|---|---|---|---|
| **Evidence** | Релевантный фрагмент из документа + источник | Всегда при RAG score > 0.03 | 1 (высший) | Цитата + source + page | `#2e7d32` зелёный | 60s / next capture | MVP |
| **Answer** | Прямой ответ «сказать вслух сейчас» | Всегда, если распознали вопрос | 2 | 1-2 предложения + 1 факт/цифра | `#1565c0` синий | 60s | MVP |
| **Do/Don't** | Фразы-табу и safe-phrases | Всегда | 3 | 2 «Do» + 2 «Don't» | `#e65100` янтарный | 60s | MVP |
| **Clarify** | 1-3 уточняющих вопроса | Если модель не уверена или retrieval слабый | 4 | Список 1-3 вопросов, каждый ≤80 зн. | `#757575` серый | 60s | MVP |
| **Risk** | Ограничения, условия, юридические риски | При вопросах про обещания/сроки/цены | 5 | 2-4 буллета, каждый ≤90 зн. | `#c62828` красный | 60s | V2 |
| **Strategy** | «Куда вести разговор дальше» | По запросу или авто | 6 | 1-2 шага, привязка к цели | `#6a1b9a` фиолетовый | 60s | V2 |
| **Emotion** | Тон/эмоциональный фон + рекомендуемый тон | При высокой уверенности | 7 | Индикатор + описание | `#00838f` teal | 30s | Pro |
| **Objection** | Вероятные возражения + контр-ходы | При спорных темах | 8 | 1-3 objections + ответ в 1 строку | `#ef6c00` оранжевый | 60s | V2 |
| **Deep Answer** | Развёрнутый ответ для follow-up | Только по клику на Answer | 10 | Абзац 5-10 строк | `#1565c0` light | По закрытию | Pro |

### Иерархия по версиям

**MVP (v0.3):** Evidence, Answer, Do/Don't, Clarify — 4 карточки, покрывают 90% сценария «мне задали вопрос, что ответить».

**V2 (v0.4):** + Risk, Strategy, Emotion — 7 карточек, переговорные сценарии.

**Pro (v0.5+):** + Objection, Deep Answer — полный набор. Опциональный, включается в настройках.

### Правила отображения (анти-перегруз)

- Максимум 3 карточки одновременно: Evidence + Answer + одна из остальных.
- Overflow indicator: «+2 more» pill снизу.
- Dismiss: свайп вправо или кнопка ✕.

---

## 7. RAG-first архитектура

### Текущее состояние

RAG уже работает: HybridSearcher (BM25 + vector + RRF fusion) в `rag/searcher.py`, MiniLM ONNX embeddings в `rag/embedder.py`, инкрементальная индексация в `rag/incremental.py`. Поддерживаются PDF, DOCX, ODT, RTF, TXT, MD, HTML.

### Knowledge Pipeline: ingestion → index → retrieval

**Типы файлов:** PDF, DOCX, MD/Markdown, HTML, TXT, ODT, RTF. CLI индексатор уже есть.

**Извлечение текста:**
- PDF: по страницам, page-number как metadata (обязателен).
- DOCX/HTML/MD: структура заголовков (H1/H2/H3), чтобы chunk можно было показать человеку.

**Chunking (для b2b docs):**
- Базовый chunk: 400-900 токенов (1-2 абзаца), overlap 10-15%.
- Структурный split: сначала по заголовкам/страницам, потом по абзацам.
- Каждый chunk: стабильный `chunk_id = hash(source_path + page + offset)` для цитирования.

**Metadata (минимум):** source, source_type, page, section_path, created_at, updated_at, language, product_version.

**Индексирование:**
- FTS5 для лексического поиска (BM25).
- sqlite-vec vec0 (KNN) для vector search.
- Hybrid retrieval = BM25 + vector → **Reciprocal Rank Fusion (RRF)** — простой, устойчивый метод.

### Confidence scoring и маркировка

Три уровня:

| RAG Score (RRF) | Уровень | Маркировка для пользователя | LLM hint |
|---|---|---|---|
| > 0.03 | **Grounded** (зелёный) | «Из документов» + источник | «Answer based on provided documents» |
| 0.01 - 0.03 | **Semi-grounded** (жёлтый) | «Частично из документов» | «Use documents as reference but supplement» |
| < 0.01 | **Ungrounded** (серый) | «Ответ модели (не из документов)» | «No relevant documents found; use general knowledge» |
| Нет RAG DB | **No KB** (серый) | «База знаний не загружена» | Standard analysis prompt |

### Citation model

- Каждая grounded-карточка обязана возвращать: `[{source, page, chunk_id, snippet_hash}]`.
- UI показывает 1-3 source chips: `Док: Pricing_v5.pdf · стр. 7` + expand → сниппет.

### Fallback logic: правила принятия решения

```
1. Есть RAG DB + есть результаты (score > 0.01)?
   → Включить в LLM context, показать Evidence Card

2. Если intent = «факт из документов/условия/цены/спеки» и retrieval < 0.01:
   → НЕ отвечать уверенно:
     (a) Clarify Card
     (b) «В документах не вижу подтверждения»
     (c) безопасная формулировка

3. Если retrieval есть, но документы конфликтуют:
   → Evidence Card с 2 источниками
   → Answer: «В версии X сказано…, в версии Y — …»

4. Есть RAG DB + нет результатов?
   → LLM без контекста, маркировать «Ungrounded»

5. Нет RAG DB?
   → LLM без контекста, onboarding hint «Загрузите документы»

6. Нет LLM (offline, no Ollama)?
   → Только Evidence Card (RAG results as-is), без генерации
```

### Что добавлено (KC5 #177)

1. **`confidence_from_results()`** — в `rag/groundedness.py`: нормализация RRF score, уровни grounded / semi_grounded / ungrounded / no_kb.
2. Timestamp в metadata при индексации — сортировка по свежести (остаётся на будущее).
3. **Query от STT** — `extract_keyword_queries(..., for_short_capture=True)` и порог `SHORT_CAPTURE_MAX_CHARS` для коротких фрагментов (5–15s).
4. **Citation format** — `format_evidence_citations()`: basename файла + page + snippet в Evidence Card; конфликты источников — `get_conflict_hint()`.

---

## 8. Single-agent vs Multi-agent: честная оценка

### Стоимостной анализ

| Фактор | Single orchestrator (2 calls) | Multi-agent (5-7 agents) |
|---|---|---|
| Latency | 3-5s (2 parallel calls) | 3-5s parallel, но overhead координации |
| Cost per capture | $0.002-0.005 | $0.005-0.015 |
| Cost per month (50 captures/day) | $3-7.5 | $7.5-22.5 |
| Budget fit ($75/mo) | Комфортно | На грани |
| Debugging | 2 промпта + RAG | 5-7 промптов + координатор |
| Reliability | 2 failure points | 5-7 failure points |
| Consistency | Один контекст → консистентные карточки | Разные агенты могут противоречить |

### Рекомендуемая архитектура: 2 параллельных LLM-вызова + RAG-only Evidence

```
                    [STT result + RAG context]
                              │
                    ┌─────────┴──────────┐
                    │                    │
            [Fast Track]          [Deep Track]
            Haiku 4.5             Haiku 4.5
            ~2s                   ~3-4s
                    │                    │
         ┌─────────┤              ┌─────┤
         │         │              │     │
      Answer    Do/Don't       Risk  Strategy
      Card      Card           Card  Card
         │         │              │     │
         └─────┬───┘              └──┬──┘
               │                    │
        [Render immediately]  [Render when ready]
```

**Evidence Track** — без LLM, чистый RAG: `HybridSearcher.search()` → форматирование → карточка. Самая быстрая карточка.

**Fast Track** — один вызов `complete_structured`:
```python
class CopilotFastCards(BaseModel):
    answer: list[str]     # 1-2 items
    dos: list[str]        # 1-2 items
    donts: list[str]      # 1-2 items
    clarify: list[str]    # 0-2 items
    confidence: float     # 0-1
```

**Deep Track** — один вызов:
```python
class CopilotDeepCards(BaseModel):
    risks: list[str]      # 0-3 items
    strategy: str         # 1-2 sentences
    emotion: str | None   # optional
    objections: list[str] # 0-2 items (V2)
```

### Когда переходить на multi-agent

**Не раньше V3**, и только если:
1. LLM стоимость упадёт так, что 7 вызовов ≈ 1 текущий.
2. Доказано A/B-тестом, что специализированные промпты дают значимо лучше.
3. Появится потребность в независимом scaling отдельных карточек.

| Версия | Архитектура |
|---|---|
| MVP | 1 LLM call (fast track) + RAG |
| V2 | 2 parallel LLM (fast + deep) + RAG |
| V3+ | Рассмотреть multi-agent при доказанной необходимости |

---

## 9. Техническая архитектура desktop-приложения

### High-level архитектура (целевая)

```
┌─────────────────────────────────────────────────────┐
│                    Tauri Desktop Shell               │
│  ┌──────────────┐  ┌─────────────────────────────┐  │
│  │  Main Window  │  │    Copilot Overlay Window   │  │
│  │  (Sessions,   │  │  (Cards, Recording status)  │  │
│  │   Settings,   │  │  Always-on-top, no focus    │  │
│  │   Costs)      │  │  400x300px, decorations off │  │
│  └──────┬───────┘  └─────────────┬───────────────┘  │
│         │ Tauri Commands          │ Tauri Events     │
│  ┌──────┴────────────────────────┴───────────────┐  │
│  │              Rust D-Bus Bridge                 │  │
│  └──────────────────┬────────────────────────────┘  │
└─────────────────────┼───────────────────────────────┘
                      │ D-Bus IPC
┌─────────────────────┼───────────────────────────────┐
│              Python Daemon (voiceforge)              │
│  ┌─────────┐ ┌──────┴──────┐ ┌────────────────┐    │
│  │ Audio   │ │  Copilot    │ │  Legacy        │    │
│  │ Capture │ │  Pipeline   │ │  Pipeline      │    │
│  │ (PW)   │ │  (new)      │ │  (existing)    │    │
│  └────┬────┘ └──────┬──────┘ └────────────────┘    │
│       │             │                               │
│  ┌────┴────┐  ┌─────┴──────────────────────────┐   │
│  │ Ring    │  │    Processing Pipeline          │   │
│  │ Buffer  │  │  STT(tiny) → RAG → LLM(fast)   │   │
│  └─────────┘  │              ↘ LLM(deep)        │   │
│               └─────────────────────────────────┘   │
│                                                     │
│  ┌──────────┐ ┌───────────┐ ┌──────────────────┐   │
│  │ SQLite   │ │ RAG Index │ │ LLM Router       │   │
│  │ Sessions │ │ (FTS5 +   │ │ (LiteLLM +       │   │
│  │ + FTS    │ │ sqlite-vec)│ │ Instructor +     │   │
│  └──────────┘ └───────────┘ │ CircuitBreaker)   │   │
│                             └──────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Ключевые свойства:**
- Daemon orchestrator управляет SLA и очередями (2 быстрых нажатия не запускают 2 тяжёлых анализа).
- Ring buffer по умолчанию in-memory; запись на диск — опция для history/enterprise.
- LLM Router — provider-agnostic через LiteLLM. Текущая прослойка уже заточена под structured output + fallback + budget check + response cache.
- STT и RAG всегда локально.

### Event flow: Push-to-Capture

```
t=0ms    Hotkey DOWN → Tauri global-shortcut → D-Bus CaptureStart()
         → daemon marks ring buffer timestamp_start
         → emit CaptureStateChanged(true)
         → overlay shows red recording dot

t=Ns     Hotkey UP → Tauri global-shortcut → D-Bus CaptureRelease()
         → daemon reads RingBuffer(timestamp_start → now) = audio chunk
         → spawn CopilotPipeline:

t+0ms      Step 1: STT tiny (parallel: keyword extraction from partial)
t+1500ms   Step 2: STT complete → RAG search (50-200ms)
           Step 2b: Emit EvidenceCard via D-Bus CopilotCardsReady
t+1700ms   Step 3: LLM fast-track starts (transcript + RAG context, streaming)
t+2200ms   Step 3b: First LLM tokens → partial Answer Card
t+3500ms   Step 3c: Fast-track complete → Answer + Do/Don't + Clarify
t+3500ms   Step 4: (optional) LLM deep-track starts
t+5000ms   Step 4b: Deep-track → Risk + Strategy

         Overlay renders each card as signals arrive
         Previous capture's cards replaced
         Store: transcript + cards → session in SQLite
```

### Что локально vs что в облако

| Компонент | Локально | Облако | Interchangeable |
|---|---|---|---|
| Audio capture | Всегда | Никогда | Нет |
| STT | Всегда (faster-whisper) | Опционально (OpenAI API) | Да, через stt_backend config |
| RAG search | Всегда (SQLite) | Никогда | Нет |
| Embedding | Всегда (MiniLM ONNX) | Никогда | Нет |
| LLM | Ollama (fallback) | Cloud API (primary) | Да, через LiteLLM router |
| Storage | Всегда (SQLite) | Никогда | Нет |

---

## 10. Режимы deployment

| Характеристика | Cloud-only | Hybrid (рекомендуется) | Offline-first |
|---|---|---|---|
| **Приватность** | Средняя (текст уходит) | Хорошая (аудио локально) | Отличная |
| **Стоимость** | $3-8/мес | $1-4/мес | $0 (hardware costs) |
| **Latency first card** | 2-3s | 2-3s | 2-3s |
| **Latency answer** | 3-5s | 3-5s cloud / 8-15s local | 8-15s |
| **Качество** | Высокое (Haiku 4.5+) | Высокое / Среднее | Низкое (phi3:mini) |
| **System requirements** | 4GB RAM | 4GB RAM | 8GB RAM (Ollama) |
| **Enterprise** | Средняя | Хорошая | Отличная |

**Важно:** STT всегда локальный — аудио никогда не покидает машину. В облако уходит только текстовый транскрипт. Это ключевое privacy-преимущество.

**Режим в UI:**
- ☁ Cloud (синий) — всё через API
- ⚡ Hybrid (зелёный) — оптимальный
- 🔒 Offline (серый) — Evidence + базовый ответ Ollama

**Explicit mode selection** в конфиге:
```yaml
copilot_mode: "hybrid"  # "cloud" | "hybrid" | "offline"
```

**KC10 scope guard:** Stealth mode (reduced overlay) и card history scrollback явно вынесены за пределы KC10 и будут реализованы в последующих блоках.

---

## 11. UX/UI концепция

### Design principles

1. **Tray-first** — 99% времени невидимо.
2. **Keyboard-first** — все действия через hotkeys.
3. **AI-first** — UI показывает результаты AI, не формы.
4. **Minimal-friction** — от нажатия до результата: 0 кликов.
5. **Glanceable** — 2 секунды = достаточно для чтения подсказки.
6. **Calm design** — никаких modals/popups при нормальной работе.
7. **Layered disclosure** — 1 строка → клик → полный текст → клик → источник.

### Copilot Overlay (НОВОЕ, приоритет #1)

- **Реализация:** отдельное окно Tauri: `decorations: false, alwaysOnTop: true, skipTaskbar: true, transparent: true`.
- **Размер:** 400×300px (resizable), позиция: bottom-right.
- **Фон:** полупрозрачный (`rgba(26,26,26,0.92)` dark / `rgba(245,245,245,0.92)` light).
- **Округление:** 12px, тень: `0 8px 32px rgba(0,0,0,0.3)`.
- Без title bar, без window controls.
- Закрытие: Escape или auto-hide через 60s.
- **Без кражи фокуса** — критично для live conversation.

### Карточка (Card component)

- Левый border 4px цвета типа.
- Header: иконка + метка типа (12px, muted) + confidence indicator.
- Body: 1-2 строки (14px).
- Footer (при раскрытии): source attribution, timestamp.
- Expand: клик → полный текст.
- Pin: двойной клик.
- Dismiss: свайп вправо или ✕.

### Recording Indicator

- Красный кружок 12px, пульсация (CSS animation).
- Top-right overlay. Текст: «Recording… 5s» (обратный отсчёт от 30).

### Анимации

| Действие | Анимация | Длительность |
|---|---|---|
| Card appears | Slide up + fade in | 200ms ease-out |
| Card dismiss | Slide right + fade out | 150ms ease-in |
| Card expand | Height transition | 200ms ease-out |
| Recording start | Red dot fade in + pulse | 100ms + infinite |
| Overlay appear | Fade in | 150ms |
| Overlay auto-hide | Fade out | 300ms |

### Error / Loading / Fallback states

| State | UI |
|---|---|
| STT processing | Три пульсирующие точки + «Analyzing...» |
| LLM generating | Skeleton card с shimmer |
| LLM failed | Evidence Card only + «AI unavailable, showing documents only» |
| No mic | Toast «Microphone not available» |
| Daemon down | Banner «Daemon not running» (уже есть) |
| No documents | Hint «Add documents for better answers» |
| Offline mode | Mode icon change + label |

---

## 12. MVP (v0.3.0)

### Входит в MVP (Must)

1. **Push-to-capture** — зажал hotkey → запись → отпустил → анализ (Pressed/Released).
2. **4 карточки:** Evidence, Answer, Do/Don't, Clarify.
3. **Copilot overlay** — отдельное окно Tauri, always-on-top, без фокуса.
4. **RAG-first** — Evidence Card из документов за 2s, LLM cards за 3-5s.
5. **Confidence scoring** — grounded / semi-grounded / ungrounded маркировка.
6. **Session context** — накопление контекста через последовательные captures.
7. **Mic-only capture** — только микрофон, без system audio.
8. **Streaming ASR** во время удержания + finalize после Release.
9. **Cloud mode primary** — работа через API (Haiku 4.5), Evidence Card offline.
10. **Max 3 visible cards** + auto-dismiss 60s + progressive disclosure.

### НЕ входит в MVP

- Risk, Strategy, Emotion, Objection cards → V2
- Multi-agent → V3+
- System audio → V2
- Knowledge Manager UI → V2
- Scenario presets → V2
- Speaker profiles → V3
- Auto mode для copilot → V3
- Offline LLM cards (Ollama) → V2
- Deep Answer Card → V2

### Как выглядит первый релиз

1. Пользователь устанавливает VoiceForge, запускает daemon.
2. Загружает документы через CLI (`voiceforge rag index ~/docs/project/`).
3. Открывает презентацию / Zoom / Teams.
4. Зажимает `Ctrl+Shift+Space` когда собеседник задаёт вопрос.
5. Через 2-3 с в правом нижнем углу overlay:
   - Evidence Card: «Согласно 'pricing-2026.pdf' стр.12: Enterprise план — $45K/год»
   - Answer Card: «Enterprise лицензия стоит $45K в год, включает SLA 99.9% и dedicated support»
   - Do/Don't: «✓ Упомяните включённый SLA. ✗ Не обсуждайте скидки без согласования»
6. Карточки исчезают через 60 с.
7. Следующий вопрос → повторяет цикл.

---

## 13. V2 и V3

### V2 (v0.4.0) — «Deep Copilot»

| Что добавляется | Зачем |
|---|---|
| Risk + Strategy + Emotion cards | Переговорные сценарии |
| Deep Track (второй параллельный LLM call) | Генерация глубоких карточек |
| Knowledge Manager UI | Управление документами в GUI |
| Knowledge packs (project contexts) | Переключение между проектами |
| System audio capture (opt-in) | Запись собеседника через Zoom/Teams |
| Scenario presets | Demo / Sales / Tech defense / Support профили |
| Stealth mode (reduced overlay) | Для живых встреч |
| Card history scrollback | Просмотр предыдущих captures |
| Explicit mode selector | Cloud / hybrid / offline |
| Offline LLM (Ollama cards) | Автономная работа |
| Improved retrieval (metadata, chunking, rerank) | Качество RAG |

### V3 (v0.5.0) — «Adaptive Copilot»

| Что добавляется | Зачем |
|---|---|
| Objection + Deep Answer cards | Полный набор |
| Card effectiveness feedback | ML на полезности |
| Adaptive model selection | Auto-switch по latency budget |
| Speaker profiles | Распознавание говорящих |
| Contradiction detection | Конфликты в документах |
| Auto-save snippets | Коллекция полезных ответов |
| Plugin / API system | Enterprise extensibility |
| Windows/macOS port investigation | Кроссплатформенность |

---

## 14. Roadmap по горизонтам

### 0-3 месяца: MVP-суфлёр

**Цели:** работающий push-to-capture copilot с 4 карточками и RAG-first.

**Deliverables:**
- CopilotPipeline (Python): STT tiny → RAG → LLM fast track
- CopilotCards Pydantic schema + copilot prompt templates
- D-Bus: CaptureStart, CaptureRelease, CopilotCardsReady signal
- Tauri: copilot overlay window (always-on-top, no focus steal)
- Card renderer с цветовым кодированием (4 card types)
- Push-to-capture hotkey (key-down/key-up)
- RAG confidence scorer + grounded/ungrounded labels
- Session context accumulation
- Dual STT slot in ModelManager (tiny + small)

**Технические вехи:**
- W1-2: Backend pipeline + schemas
- W3-4: D-Bus integration + Tauri overlay
- W5-6: Card UI + hotkey handling
- W7-8: Integration testing, latency tuning, RAG threshold calibration

**Критерии готовности:**
- Push-to-capture → 4 cards в overlay за <5s end-to-end.
- Evidence Card за <2.5s.
- RAG confidence correctly classifies grounded vs ungrounded.
- No focus stealing on Linux (X11 + Wayland GNOME).

### 3-6 месяцев: переговорная ценность

**Deliverables:**
- Risk + Strategy + Emotion cards + Deep Track
- Knowledge Manager tab + packs
- System audio (opt-in) + Scenario presets
- Stealth mode + Card history
- Explicit mode selector + Ollama offline
- Caching: embeddings, быстрые повторные вопросы

**Критерии готовности:**
- 7 card types working. Knowledge packs switching <1s.
- ≤4 карточек по умолчанию. Низкий «card spam».

### 6-12 месяцев: масштабируемость и enterprise

**Deliverables:**
- Hardened privacy panel
- Шифрование, экспорт/удаление данных
- Кроссплатформенный системный звук (Windows WASAPI, macOS ScreenCaptureKit)
- Optional diarization
- Enterprise deployment (MSI/pkg, managed updates, policy)
- Offline card generation via Ollama (7B model)
- Full 10-card set + feedback + adaptive models

---

## 15. MoSCoW приоритизация

### Must Have (MVP)

- Push-to-capture hotkey (key-down/key-up)
- Copilot overlay window (always-on-top, no focus steal)
- Evidence Card (RAG-only, no LLM)
- Answer Card (LLM fast track)
- Do/Don't Card
- Clarify Card
- RAG confidence scoring + grounded labels
- Session context accumulation
- Streaming ASR during capture
- Recording indicator in overlay
- Auto-dismiss cards (60s)
- Max 3 cards visible rule
- Стабильный daemon + очередь задач

### Should Have (V2)

- Risk Card, Strategy Card, Emotion Card
- Knowledge Manager UI + packs
- Scenario presets (demo/sales/tech)
- System audio capture (opt-in)
- Stealth mode + Card history scrollback
- Deep Track (parallel LLM call)
- Offline fallback LLM
- Explicit mode selector
- Question intent classification

### Could Have (V2-V3)

- Deep Answer Card
- Objection Card
- Quick rewrite
- Executive summary after session
- Auto-save snippets
- Answer tone switch
- Meeting mode

### Won't Have Yet (V3+)

- Full multi-agent architecture
- Speaker profiles + recognition
- Contradiction detection
- TTS (reading cards aloud)
- Mobile app / Browser extension
- Always-on recording for copilot
- macOS / Windows port

---

## 16. Ограничения и риски

| Риск | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **Latency >5s** — пользователь уже ответил | Высокий | Средняя | Streaming ASR; Evidence Card за 2s; 2-фазная выдача |
| **Hallucination в live разговоре** | Критический | Средняя | RAG-first; confidence scoring; «Ungrounded» маркировка; Do/Don't предупреждает |
| **Ошибки STT** (неверная транскрипция → неверный совет) | Высокий | Средняя | Tiny model достаточен для keywords; transcript snippet в overlay для проверки; «ask-to-confirm» при низкой уверенности |
| **Захват аудио на Wayland** | Средний | Низкая | PipeWire работает; layer-shell для overlay требует проверки |
| **Always-on-top на Wayland** | Средний | Средняя | Compositor может игнорировать; fallback: notification-style popup |
| **Privacy — запись собеседника** | Высокий | Средняя | Push-to-capture (не continuous); аудио никогда не в облако; disclaimer |
| **Перегруз карточками** | Средний | Средняя | Max 3 visible; auto-dismiss; priority ordering |
| **API rate limits** | Средний | Низкая | Circuit breaker уже есть; local Evidence fallback; batch debouncing |
| **Battery/CPU drain** | Средний | Средняя | Tiny model = 75MB RAM; unload after 5min idle; lazy load |
| **Offline quality деградация** | Средний | Высокая | Честная коммуникация: «Offline: document lookup only»; Evidence Card без LLM |
| **System audio = legal risk** | Высокий | Средняя | Opt-in only; default OFF; per-session consent; не в MVP |
| **False positive карточки** | Средний | Средняя | RRF threshold; dismiss; feedback loop (V3) |
| **Compliance (GDPR)** | Высокий | Средняя | Privacy panel + «no audio retention» по умолчанию; enterprise policy; visual recording indicators |
| **Multi-agent слишком рано** | Средний | Средняя | MVP single-orchestrator; параллелизация только измеряемая |

---

## 17. Последовательность разработки (MVP)

1. **CopilotCards schema + prompts** (Python) — Pydantic models для fast/deep tracks.
2. **CopilotPipeline** (Python) — reuse STT + RAG + LLM infrastructure.
3. **D-Bus interface extension** — CaptureStart, CaptureRelease, CopilotCardsReady signal.
4. **Tauri overlay window** (Rust + JS) — second window, always-on-top.
5. **Card renderer + recording indicator** (JS/CSS) — 4 card types с цветовым кодированием.
6. **Push-to-capture hotkey** (Tauri global-shortcut key-down/key-up).
7. **RAG confidence scoring** — нормализация, thresholds, labels.
8. **Integration testing + latency tuning** — end-to-end на целевом железе.

---

## 18. Финальная рекомендация

### Продуктовая стратегия

**Knowledge Copilot** — real-time AI-суфлёр: push-to-capture → instant cards → RAG-first. «Ваши документы, ваши ответы, в реальном времени.» Meeting assistant функции — вторичные режимы, не разрушающие calm-UX.

### Архитектура

Single orchestrator + 2 parallel LLM calls (fast + deep track) + RAG-only Evidence Card. Не multi-agent. Существующий стек (LiteLLM + Instructor + HybridSearcher) полностью переиспользуется. Добавляется CopilotPipeline, CopilotCards schema, overlay window.

### MVP

4 карточки (Evidence, Answer, Do/Don't, Clarify) + push-to-capture + copilot overlay. Mic only. Cloud mode. 4-8 недель разработки.

### UI/UX модель

Tray-first + keyboard-first + calm design. Отдельное overlay-окно Tauri (400×300, always-on-top, без decorations). Стек из max 3 карточек. Цветовое кодирование по типу. Auto-dismiss 60s. Progressive disclosure. Без кражи фокуса.

### RAG / Fallback

RAG-first: Evidence Card всегда первый (2-2.5s). RRF score > 0.03 = grounded (зелёная метка), 0.01-0.03 = semi-grounded (жёлтая), < 0.01 = ungrounded (серая). Жёсткие guardrails: при intent «факт/цена/условие» и слабом retrieval — НЕ отвечать уверенно, а Clarify + безопасная формулировка.

### Online / Hybrid / Offline

Базовый: **Hybrid**. STT и RAG всегда локально. LLM: cloud primary (Haiku 4.5), Ollama fallback. Аудио никогда не покидает машину. В offline: Evidence Card + базовый ответ Ollama.

---

## 19. Top-10 решений, которые нельзя принять неверно

| # | Решение | Рекомендация | Почему критично |
|---|---|---|---|
| 1 | Single vs Multi-agent | Single orchestrator, 2 calls | Cost ($75/mo), reliability, consistency |
| 2 | STT model для copilot | Tiny (отдельный слот) | 1s vs 5s latency; keyword accuracy достаточна |
| 3 | Overlay vs panel in main window | Отдельное overlay-окно | Нельзя красть фокус при live conversation |
| 4 | RAG-first vs LLM-first | RAG-first | Меньше hallucinations, быстрее first card, core value |
| 5 | System audio в MVP | Нет — только mic | Privacy risk; consent UX; усложняет MVP |
| 6 | Количество карточек MVP | 4 (Evidence, Answer, Do/Don't, Clarify) | 90% use case; >4 = cognitive overload |
| 7 | Max visible cards | 3 одновременно | Glanceability; 2 секунды на чтение |
| 8 | Capture модель | Armed ring buffer + pre-roll | Пропуск первых слов фатален для UX |
| 9 | Streaming ASR | Обязателен во время удержания | Без него «мгновенность» не получится |
| 10 | Данные по умолчанию | Не хранить аудио; хранить транскрипты локально | Privacy + compliance vs utility |

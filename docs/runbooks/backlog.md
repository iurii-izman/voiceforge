# Backlog (зеркало GitHub Project)

Канбан и приоритеты ведутся в **[GitHub Project VoiceForge](https://github.com/users/iurii-izman/projects/1)**. Этот файл — краткое зеркало для тех, кто смотрит только в репо.

**Текущий фокус (In Progress):** [#32 A1 Eval harness](https://github.com/iurii-izman/voiceforge/issues/32) (Phase A P0)

## Phase A · Stabilize (Todo)

| # | Задача | Effort |
|---|--------|--------|
| [#32](https://github.com/iurii-izman/voiceforge/issues/32) | A1 Eval harness — DeepEval/ROUGE-L тест-жгут для LLM (P0) | M |
| [#33](https://github.com/iurii-izman/voiceforge/issues/33) | A2 Instructor retry loop в complete_structured() (P0) | S |
| [#34](https://github.com/iurii-izman/voiceforge/issues/34) | A3 Unit tests: daemon, streaming, smart_trigger | M |
| [#35](https://github.com/iurii-izman/voiceforge/issues/35) | A4 WAV integration tests (STT→Analysis pipeline) | M |
| ~~#27~~ | A5 AppImage — полная сборка в toolbox (**Done**) | L |

## Phase B · Hardening (Todo)

| # | Задача | Effort |
|---|--------|--------|
| [#36](https://github.com/iurii-izman/voiceforge/issues/36) | B1 Observability: Prometheus metrics + OpenTelemetry (P0) | L |
| [#37](https://github.com/iurii-izman/voiceforge/issues/37) | B2 pyannote memory guard (P0) | S |
| [#38](https://github.com/iurii-izman/voiceforge/issues/38) | B3 Budget enforcement pre-call | S |
| [#39](https://github.com/iurii-izman/voiceforge/issues/39) | B4 IPC D-Bus envelope (on по умолчанию) | S |
| [#40](https://github.com/iurii-izman/voiceforge/issues/40) | B5 CI ML-deps cache (GitHub Actions) | XS |

## Phase C · Scale (Todo)

| # | Задача | Effort |
|---|--------|--------|
| [#41](https://github.com/iurii-izman/voiceforge/issues/41) | C1 Prompt management (вынести из кода) | M |
| [#42](https://github.com/iurii-izman/voiceforge/issues/42) | C2 RAG query context расширение | S |
| [#43](https://github.com/iurii-izman/voiceforge/issues/43) | C3 Data retention policy | S |
| [#44](https://github.com/iurii-izman/voiceforge/issues/44) | C4 Response caching layer | M |
| [#45](https://github.com/iurii-izman/voiceforge/issues/45) | C5 Healthcheck endpoint | XS |

## Phase D · Productize (Todo)

| # | Задача | Effort |
|---|--------|--------|
| [#46](https://github.com/iurii-izman/voiceforge/issues/46) | D1 Desktop D-Bus signals | S |
| [#47](https://github.com/iurii-izman/voiceforge/issues/47) | D2 Telegram bot расширение | M |
| [#48](https://github.com/iurii-izman/voiceforge/issues/48) | D3 Calendar integration (CalDAV) | L |
| [#49](https://github.com/iurii-izman/voiceforge/issues/49) | D4 Flatpak packaging | L |

## Operational (Todo)

| # | Задача |
|---|--------|
| [#29](https://github.com/iurii-izman/voiceforge/issues/29) | RAG ODT/RTF — тесты при добавлении |
| [#30](https://github.com/iurii-izman/voiceforge/issues/30) | Dependabot — закрыть 1 moderate вручную |
| [#51](https://github.com/iurii-izman/voiceforge/issues/51) | QW1 scipy в base deps |
| [#52](https://github.com/iurii-izman/voiceforge/issues/52) | QW2 i18n (убрать хардкод рус. строк) |
| [#53](https://github.com/iurii-izman/voiceforge/issues/53) | QW3 ThreadPoolExecutor singleton в pipeline |

**Done (недавно):** [#26 CalDAV](https://github.com/iurii-izman/voiceforge/issues/26) (voiceforge calendar poll). [#28 EN runbook](https://github.com/iurii-izman/voiceforge/issues/28) (dependabot-review-en, telegram-bot-setup-en).

При выполнении задачи: коммит в формате Conventional Commits с `Closes #N` (см. [git-github-practices.md](git-github-practices.md)); на доске перевести карточку в Done (агент может через `gh project item-edit`).

См. также [next-iteration-focus.md](next-iteration-focus.md) и [planning-and-tools.md](planning-and-tools.md).

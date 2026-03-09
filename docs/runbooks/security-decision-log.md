# Security Decision Log

**Обновлено:** 2026-03-09.

Этот документ фиксирует открытые security wait states и принятые решения, чтобы remote alerts не выглядели как “фон без владельца”. Подробная политика зависимостей и секретов — в [security-and-dependencies.md](security-and-dependencies.md).

---

## 1. Активные wait states

| Item | Источник | Статус на 2026-03-09 | Решение | Когда пересматривать |
|---|---|---|---|---|
| `#65` / `CVE-2025-69872` (`diskcache` via `instructor`) | `pip-audit`, issue [#65](https://github.com/iurii-izman/voiceforge/issues/65) | Исправляющей версии upstream нет | Временно держать `--ignore-vuln CVE-2025-69872` в локальных/CI проверках. Не считать закрытым, не забывать про weekly re-check. | Как только upstream выпустит fix и `pip-audit` начнёт видеть патч |
| Dependabot alert `#4` / `serialize-javascript` | GitHub Dependabot, `desktop/e2e-native/package-lock.json` | `high`, transitive dev dependency | Не блокирует текущий backend/productization wave, но должен быть перепроверен до следующего desktop-native dependency refresh и до managed packaging track. | Перед активной desktop packaging работой и при следующем обновлении `desktop/e2e-native` |
| Dependabot alert `#3` / `time` | GitHub Dependabot, `desktop/src-tauri/Cargo.lock` | `medium`, transitive through Rust graph | Не трогать отдельным emergency branch без верификации Tauri dependency chain. Держать как tracked wait state. | При следующем Rust/Tauri dependency refresh и до beta packaging proof |
| Dependabot alert `#2` / `glib` | GitHub Dependabot, `desktop/src-tauri/Cargo.lock` | `medium`, transitive through Rust graph | Аналогично `time`: держать видимым, не игнорировать молча, пересматривать вместе с desktop dependency refresh. | При следующем Rust/Tauri dependency refresh и до beta packaging proof |

---

## 2. Операционное правило

Для VoiceForge допустимы только три состояния:

- `fixed`
- `tracked wait state`
- `explicitly accepted risk with revisit trigger`

Недопустимое состояние: открытый remote alert без записи в этом журнале или без ссылки на issue/runbook.

---

## 3. Что это значит для Phase E

- Security wait states не меняют зафиксированный scope из [phase-e-decision-log.md](phase-e-decision-log.md).
- Они **не** открывают новые feature tracks.
- Они должны учитываться перед:
  - desktop-first активной фазой `E19`;
  - managed packaging future track;
  - beta packaging/release proof.

Если desktop dependency refresh начинается раньше, журнал нужно обновить в той же сессии.

---

## 4. Сопутствующие документы

- Политика зависимостей: [security-and-dependencies.md](security-and-dependencies.md)
- Repo governance и security baseline: [repo-and-git-governance.md](repo-and-git-governance.md)
- Scope guard: [phase-e-decision-log.md](phase-e-decision-log.md)

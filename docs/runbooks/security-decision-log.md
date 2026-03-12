# Security Decision Log

**Обновлено:** 2026-03-13.

Этот документ фиксирует открытые security wait states и принятые решения, чтобы remote alerts не выглядели как “фон без владельца”. Подробная политика зависимостей и секретов — в [security-and-dependencies.md](security-and-dependencies.md).

---

## 1. Активные tracked alerts / wait states

| Item | Источник | Статус на 2026-03-09 | Решение | Когда пересматривать |
|---|---|---|---|---|
| CodeQL alert `py/clear-text-storage-sensitive-data` | GitHub Code Scanning, `src/voiceforge/cli/setup.py` | **Dismissed** (2026-03-13) | False positive: wizard writes only non-secret config defaults (`model_size`, `language`) to `voiceforge.yaml`; secrets go only to keyring. Alert dismissed with rationale in GitHub UI; code comment added in `setup.py`. | — |
| Dependabot alert `#3` / `time` | GitHub Dependabot, `desktop/src-tauri/Cargo.lock` | `medium`, transitive Rust | 2026-03-13 lock locally refreshed to `time 0.3.47` via coordinated `cargo update`, with `cargo tauri build` and desktop release gate passing. Remote alert should clear after push/rescan. | После push/rescan; если не закроется — перепроверить remote lock ingestion |
| Dependabot alert `#2` / `glib` | GitHub Dependabot, `desktop/src-tauri/Cargo.lock` | `medium`, transitive Rust | Tracked. В Cargo.toml закреплён glib 0.20 (RUSTSEC-2024-0429), но transitive `glib 0.18.5` остаётся глубоко в GTK/Tauri/wry Linux chain. Требуется coordinated ecosystem refresh, а не patch-level fix. | Следующий targeted hardening block `#164` |

`#65` / `CVE-2025-69872` больше не является активным wait-state: 2026-03-13 `uv run pip-audit --desc` проходит без `--ignore-vuln`.

Dependabot alert `#4` / `serialize-javascript` больше не является активным tracked alert: 2026-03-13 в `desktop/e2e-native` добавлен npm override до `serialize-javascript@7.0.4`, `npm audit` для native-e2e workspace снова чист, а remote Dependabot alert уже перешёл в `fixed`.

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

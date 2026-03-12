# Desktop Release Gate Matrix

Честный release gate для desktop delivery на Linux: что закрывается автоматикой, что требует native smoke, а что остаётся manual/environment-specific проверкой.

---

## 1. Цель

Playwright/autopilot и visual/a11y suite дают сильный regression signal, но они не доказывают все свойства реального Tauri shell. Этот runbook фиксирует минимальный набор evidence перед desktop release и убирает двусмысленность между `tests green` и `desktop ready`.

---

## 2. Матрица покрытия

| Surface | Automated mocked | Native smoke | Manual / environment-specific | Evidence |
|---------|------------------|--------------|-------------------------------|----------|
| Main navigation, widgets, session flows | Yes | Yes | No | Playwright HTML report + native smoke log |
| Accessibility regressions on key screens | Yes | No | Optional spot-check | `desktop/e2e/a11y.spec.js`, Playwright report |
| Visual regressions on key screens | Yes | No | Optional human review on changed baselines | screenshot baselines + Playwright report |
| Tauri window launches and app shell renders | No | Yes | No | native smoke output |
| D-Bus unavailable state / retry path | Partial | Yes | No | native smoke output |
| Settings panel / local desktop toggles | Yes | Yes | No | Playwright + native smoke |
| Tray icon/menu behavior | No | Partial | Yes | manual release checklist |
| Close-to-tray hide/show semantics | No | Partial | Yes | manual release checklist |
| Global shortcuts in background | No | No | Yes | manual release checklist |
| Notifications UX | Partial mocked only | No | Yes | manual release checklist |
| Updater install flow | Mocked only | No | Yes | updater checklist + release proof |
| Wayland/X11 quirks | No | No | Yes | per-environment manual proof |
| Multi-monitor / window restore | No | No | Yes | manual proof |

---

## 3. Minimum evidence before desktop release

Обязательный минимум:

1. `uv run python scripts/check_release_metadata.py`
2. `uv run python scripts/check_release_proof.py`
3. `cd desktop && npm run e2e`
4. `cd desktop && npm run e2e:gate`
5. `cd desktop && npm run e2e:release-gate`
6. (Advisory) `cd desktop && npm run e2e:native`
6. `cd desktop && npm run e2e:native`
7. `cd desktop && npm run tauri build`
8. `./scripts/verify-desktop-packaging.sh` (E19: проверка .deb/.AppImage в bundle)

Дополнительно для релиза с updater:

- пройти checklist из [desktop-updater.md](desktop-updater.md)
- приложить proof для signed artifact / update endpoint

`check_release_proof.py` нужен здесь как честная фиксация boundary: что blocking, что advisory, и требуется ли updater evidence вообще.

---

## 4. Manual release checklist

Нужно пройти руками на целевой Linux-среде:

- tray icon виден и меняется по теме
- tray menu открывает окно, toggle recording и quit
- close-to-tray реально скрывает окно, а не завершает приложение
- глобальные shortcuts работают, когда окно не в фокусе
- notifications понятны и не ломаются на реальной DE
- Wayland и X11 не имеют blocking visual/input regressions
- updater flow проверен отдельно, если он не отключён

---

## 5. CI policy

- `desktop-e2e` с mocked runtime остаётся CI baseline и блокирующим regression signal
- `desktop-a11y` и visual regression используются как automated quality signal
- `npm run e2e:gate` — обязательный бесплатный CI/local regression gate
- `npm run e2e:release-gate` — минимальный бесплатный локальный desktop release gate
- native smoke через `tauri-driver` пока считается **advisory Linux shell smoke**, а не обязательным CI job:
  причина: runner должен иметь `tauri-driver`, `WebKitWebDriver`, GUI-capable environment и более дорогую поддержку Linux desktop stack
- если в будущем появится стабильный Linux desktop runner, native smoke можно переводить в отдельный blocking job без замены mocked suite

---

## 6. Связанные документы

- [desktop-gui-testing.md](desktop-gui-testing.md)
- [desktop-updater.md](desktop-updater.md)
- [release-and-quality.md](release-and-quality.md)

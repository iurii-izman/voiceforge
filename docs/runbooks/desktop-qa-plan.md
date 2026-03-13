# Desktop QA Plan

Единый operational plan для качества десктопного GUI VoiceForge. Этот документ не заменяет детальные runbooks, а связывает их в один понятный цикл: что запускать всегда, что проверять перед релизом, что делать руками и как превращать найденные UX-баги в постоянное regression coverage.

Связанные документы:

- [desktop-gui-testing.md](desktop-gui-testing.md)
- [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md)
- [release-and-quality.md](release-and-quality.md)
- [desktop/README.md](../../desktop/README.md)

## 1. Цель

Наша цель не "потыкать UI", а сделать desktop quality loop предсказуемым:

- большинство регрессий ловятся автоматикой до ручной проверки;
- native Linux/Tauri риски проверяются отдельным узким smoke-слоем;
- каждый найденный руками UI/UX-баг превращается в issue, фикс и regression test;
- release readiness определяется не интуитивно, а по понятному evidence set.

## 2. Канонические уровни проверки

| Уровень | Статус | Когда запускать | Команда | Что даёт |
|---|---|---|---|---|
| Blocking UI gate | Обязательный | После каждого заметного desktop UI change | `cd desktop && npm run e2e:release-gate` | Основной regression signal: flows, a11y, visuals, state recovery |
| Native shell smoke | Advisory | Перед release, после Tauri/native/system-level changes | `cd desktop && npm run e2e:native:headless` | Подтверждает реальный Tauri shell path, пишет native artifacts |
| Headed native smoke | Optional | Локально при странном Linux/UI behaviour | `cd desktop && npm run e2e:native` | Ручное подтверждение реального shell поведения |
| Exploratory UI mode | Optional | Когда нужно быстро исследовать сценарий | `cd desktop && npm run e2e:ui` | Ускоряет локальный UX triage |
| Manual UX pass | Обязательный для релизов | Перед релизной сборкой и после значимых UX-фиксов | См. раздел 5 | Ловит реальные продуктовые шероховатости, которых нет в mocks |

## 3. Что считается blocking

`npm run e2e:release-gate` должен быть зелёным, прежде чем считать desktop-изменение готовым.

В blocking gate входят:

- навигация между `Главная / Сессии / Затраты / Настройки`;
- onboarding, compact/full recovery, settings persistence;
- session flows: open detail, close, back, export-related states;
- desktop-first flow `Record -> Analyze -> View -> Export`;
- daemon-off / retry recovery;
- accessibility smoke на ключевых экранах;
- visual baselines на ключевых экранах.

Если blocking gate падает, работа не считается завершённой, даже если баг "выглядит мелким".

## 4. Что считается advisory

`npm run e2e:native:headless` нужен как честная Linux/Tauri проверка, но пока не является blocking.

Причина:

- native stack зависит от `tauri-driver`, `WebKitWebDriver`, GUI-capable environment и Linux desktop specifics;
- runner всё ещё хрупче mocked Playwright suite;
- для triage native smoke важны артефакты, а не просто pass/fail.

Артефакты искать в:

```text
desktop/e2e-native/artifacts/latest/
```

Минимум смотреть:

- `summary.txt`
- `wdio.log`
- `tauri-driver.log`
- `tauri-driver.stderr.log`

Если blocking gate зелёный, а native smoke красный, это отдельный targeted hardening bug, а не повод вслепую откатывать рабочий UI change.

## 5. Обязательный ручной UX checklist

Перед релизом или после заметного GUI/UX-изменения пройти руками:

1. Главная открывается в корректном состоянии и показывает статус демона.
2. `Сессии` открываются, detail view закрывается и не trap'ит навигацию.
3. `Затраты` и `Настройки` открываются без stale state.
4. Onboarding можно закрыть; `Не показывать снова` переживает перезапуск.
5. Compact mode и возврат в full mode работают без trap-state.
6. `Close-to-tray`, крестик окна, `Alt+F4` и явный `Выйти из VoiceForge` ведут себя предсказуемо.
7. Запись, анализ и просмотр последней сессии работают в реальном runtime.
8. Поведение при `daemon unavailable` восстанавливается через retry.
9. RU/EN строки выглядят целостно и не смешиваются хаотично.
10. Окно адекватно переживает resize и повторный запуск.

## 6. Bug intake policy

Любой найденный GUI/UX-баг должен пройти один и тот же цикл:

1. Сначала зафиксировать evidence.
   Evidence: скриншот, trace, video, шаги воспроизведения, лог `npm run e2e:ui` или native artifacts.
2. Создать GitHub issue.
   Для desktop UX обычно использовать labels: `bug`, `fix`, `area:frontend`, при необходимости `area:testing`, `autopilot`.
3. Исправить баг.
4. Добавить regression protection.
   Это либо Playwright-spec, либо обновление существующего regression/autopilot spec, либо documented native-smoke expectation.
5. Прогнать `npm run e2e:release-gate`.
6. Обновить docs/handoff.
7. Только после этого закрывать issue.

Правило простое: ручной баг без regression coverage считается не закрытым до конца.

## 7. Рекомендуемый рабочий цикл

Для обычной desktop-итерации:

```bash
cd /home/user/Projects/voiceforge/desktop
npm run e2e:release-gate
```

Если правка касается Tauri/native/system window behaviour:

```bash
cd /home/user/Projects/voiceforge/desktop
npm run e2e:release-gate
npm run e2e:native:headless
```

Если нужно локально исследовать UX-аномалию:

```bash
cd /home/user/Projects/voiceforge/desktop
npm run e2e:ui
```

## 8. Release readiness

Desktop release считается обоснованным, когда:

- blocking gate зелёный;
- advisory native smoke либо зелёный, либо имеет понятный documented failure mode с артефактами;
- ручной UX checklist пройден;
- release artifacts (`binary`, `rpm`, `AppImage`) собираются;
- новый GUI/UX bug backlog после smoke не остался без issue.

## 9. Источник правды

Если документы расходятся:

- policy по запуску тестов и blocking/advisory boundary хранится здесь;
- детали mocked/native test setup — в [desktop-gui-testing.md](desktop-gui-testing.md);
- release evidence boundary — в [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md).

# KV2: Overlay UX Sign-Off — чеклист

**Issue:** [#188](https://github.com/iurii-izman/voiceforge/issues/188).
После прохождения чеклиста можно закрыть KV2 с комментарием «Sign-off пройден по чеклисту».

---

## 0. Подготовка: как запустить для проверки (в toolbox)

Все команды ниже — **внутри toolbox** (путь к репо: `/var/home/user/Projects/voiceforge`). Демон и десктоп должны работать в **одном и том же** toolbox.

**Нужно ли пересобирать и запускать из бинарника?** Для итогового sign-off **рекомендуется** запустить собранное приложение (как у пользователя). Для быстрой проверки достаточно `npm run tauri dev`.

| Вариант | Когда использовать | Команды (всё в toolbox) |
|--------|---------------------|--------------------------|
| **Из бинарника (рекомендуется)** | Итоговая проверка overlay: позиция, размер, анимации в release-сборке | **Терминал 1:** `toolbox enter` → `cd /var/home/user/Projects/voiceforge` → `uv run voiceforge daemon`. **Терминал 2:** `toolbox enter` → `cd /var/home/user/Projects/voiceforge/desktop` → `npm run build && npm run tauri build` → запуск: `/var/home/user/Projects/voiceforge/desktop/src-tauri/target/release/voiceforge-desktop` (или установленный из `bundle/deb/` пакет — команда `voiceforge-desktop`). |
| **Dev-режим** | Быстрая проверка, что overlay появляется | **Терминал 1:** `toolbox enter` → `cd /var/home/user/Projects/voiceforge` → `uv run voiceforge daemon`. **Терминал 2:** `toolbox enter` → `cd /var/home/user/Projects/voiceforge/desktop` → `npm run tauri dev`. |

**Пути в вашей системе (toolbox):**

- Корень репо: `/var/home/user/Projects/voiceforge`
- Бинарник после сборки: `/var/home/user/Projects/voiceforge/desktop/src-tauri/target/release/voiceforge-desktop`
- Пакеты: `desktop/src-tauri/target/release/bundle/deb/`, `bundle/rpm/` — после установки приложение запускается как `voiceforge-desktop`

Полная последовательность пересборки и тестов: [rebuild-run-test-guide.md](rebuild-run-test-guide.md).

---

## 1. Позиция и размер

- [ ] Окно overlay не перекрывает критичные элементы типичного рабочего экрана (например, центр экрана при 1920×1080).
- [ ] Размер карточек и шрифтов читаем без напряжения (минимальная высота текста ~14px или по вашему порогу).
- [ ] При 3 карточках (max_visible_cards=3) overlay не занимает больше 1/4–1/3 высоты экрана (или приемлемый для вас предел).

## 2. Интрузивность

- [ ] Во время обычной работы (браузер, IDE) overlay не отвлекает постоянно; достаточно боковым зрением или короткого взгляда.
- [ ] Анимации появления/обновления карточек не слишком резкие (если есть — оценить длительность и easing).
- [ ] Режим «только микрофон» vs «system audio» и бейдж режима (cloud/hybrid/offline) не создают визуального шума.

## 3. Плотность и контент

- [ ] Карточки Answer / Do–Don't / Clarify (и при наличии Risk, Strategy, Objections) не перегружены текстом; при необходимости можно сократить вывод в настройках/промптах.
- [ ] Цвета и контраст достаточны для вашего монитора и темы (светлая/тёмная).

## 4. Финальное решение

- [ ] После живого просмотра: **одобряю текущее направление overlay UX** / **требуются правки** (опишите в комментарии к #188).

Если ставите «требуются правки» — перечислите пункты (позиция, размер, анимация, контраст и т.д.) и при желании откройте отдельные issues под конкретные доработки.

---

## 5. Как закрыть KV2

1. Запустите desktop-приложение в toolbox, откройте overlay (push-to-capture или через меню).
2. Пройдите пункты 1–4 выше и отметьте галочки.
3. В [issue #188](https://github.com/iurii-izman/voiceforge/issues/188) оставьте комментарий: «Sign-off пройден по [kv2-overlay-signoff-checklist.md](kv2-overlay-signoff-checklist.md)» или перечислите требуемые правки.
4. Закройте issue #188 (или оставьте открытым до внесения правок).

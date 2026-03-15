# GitHub: профиль и репозиторий — чеклист на 100%

Чеклист, чтобы довести профиль и репозиторий VoiceForge до полного порядка.

---

## 1. Профиль пользователя (github.com/iurii-izman)

| Шаг | Где | Действие |
|-----|-----|----------|
| Фото профиля | [Settings → Profile](https://github.com/settings/profile) | Загрузить аватар (файл в репо: `.github/assets/profile-avatar.png` или свой). |
| Имя | Profile | Указать имя (или псевдоним). |
| Bio | Profile | Краткая строка, например: «Building VoiceForge — local-first AI for meetings» или о себе. |
| URL (сайт/блог) | Profile | Ссылка на сайт, LinkedIn или репозиторий voiceforge. |
| Прочие ссылки | Profile | Twitter/X, компания — по желанию. |

**Профиль-README (лента на главной профиля):** если нужна кастомная карточка с пином репо и текстом — создать репозиторий с именем **ровно как логин**: `iurii-izman/iurii-izman`. В корне добавить единственный файл `README.md`. Его содержимое GitHub покажет на странице профиля. Пример минимального README:

```markdown
### Hi
Building [VoiceForge](https://github.com/iurii-izman/voiceforge) — local-first AI assistant for audio meetings.
```

---

## 2. Репозиторий VoiceForge

| Шаг | Где | Статус / действие |
|-----|-----|-------------------|
| Description | About (карандаш справа от About) | Заполнено: «Local-first AI assistant for audio meetings…» |
| Topics | About → Topics | Добавлены: linux, python, tauri, rag, speech-to-text, local-first, meeting-assistant |
| Website | About | По желанию: ссылка на docs или сайт проекта. |
| Social preview | [Settings → General](https://github.com/iurii-izman/voiceforge/settings) → Social preview | Загрузить `.github/assets/social-preview.png` (1280×640). |
| Default branch | Settings → General | Обычно `main`. |
| Issues / Projects | Settings → General | Включены, если используете. |
| Wiki | По желанию | Чаще выключен, если всё в `docs/`. |

---

## 3. Файлы в репо (уже есть)

- **README.md** — главная страница продукта.
- **CONTRIBUTING.md** — как контрибьютить.
- **SECURITY.md** — как сообщать об уязвимостях.
- **LICENSE** — MIT.
- **.github/assets/** — аватар профиля и social preview; инструкция в [.github/ASSETS-README.md](../../.github/ASSETS-README.md).

---

## 4. Опционально

- **Pin репозиториев:** на профиле нажать «Customize your pins» и закрепить voiceforge.
- **Stars / Sponsor:** при желании включить кнопку Sponsor (Settings → Sponsor).
- **Discussions:** включить в репо, если нужен форум вместо части issues.

После прохода чеклиста профиль и репо будут доведены до «100%» по визуалу и метаданным.

# Runbook: обновления десктопа (Updater)

Настройка проверки и установки обновлений для десктопного приложения VoiceForge (Tauri 2, tauri-plugin-updater).

**Связанные документы:** [desktop-build-deps.md](desktop-build-deps.md), [release.md](release.md). План блоков: [plans/roadmap-100-blocks.md](plans/roadmap-100-blocks.md) (блок 90–92).

---

## 1. Требования

- Подпись обновлений **обязательна** (Tauri не позволяет отключить проверку подписи).
- Нужны два ключа: **приватный** (для подписи артефактов при сборке) и **публичный** (прописывается в `tauri.conf.json` и в приложении у пользователя).

---

## 2. Генерация ключей

На машине разработчика (один раз):

```bash
cd desktop && npm run tauri signer generate -- -w ~/.tauri/voiceforge.key
```

- Сохраните **приватный** ключ в безопасном месте (потеря = невозможность выпускать обновления для уже установленных копий).
- **Публичный** ключ (содержимое `.pub` или вывод команды) нужно прописать в конфиге (см. ниже).

---

## 3. Конфигурация в репозитории

В `desktop/src-tauri/tauri.conf.json` в секции `plugins.updater`:

```json
{
  "plugins": {
    "updater": {
      "pubkey": "СОДЕРЖИМОЕ_PUBLICKEY_ИЗ_КОМАНДЫ_GENERATE",
      "endpoints": [
        "https://your-server.com/updates/{{target}}/{{arch}}/{{current_version}}"
      ]
    }
  }
}
```

- `endpoints` — массив URL. Поддерживаются переменные: `{{target}}` (linux/windows/darwin), `{{arch}}` (x86_64, aarch64, …), `{{current_version}}` (текущая версия приложения).
- Сервер должен отдавать **204 No Content**, если обновления нет, или **200 OK** с JSON (см. [Tauri Updater](https://v2.tauri.app/plugin/updater/)).

---

## 4. Сборка с подписью

При сборке артефактов для обновления **приватный ключ** должен быть доступен (не коммитить в репо).

**Linux/macOS:**

```bash
export TAURI_SIGNING_PRIVATE_KEY="$(cat ~/.tauri/voiceforge.key)"
# или путь к файлу:
# export TAURI_SIGNING_PRIVATE_KEY="path/to/voiceforge.key"
cd desktop && npm run tauri build
```

В `tauri.conf.json` для генерации updater-артефактов:

```json
{
  "bundle": {
    "createUpdaterArtifacts": true
  }
}
```

После сборки появятся файлы вида `*.sig` и обновляемые пакеты (например, `.AppImage` + `.AppImage.sig`).

---

## 5. Сервер обновлений

Варианты:

1. **Статический JSON** (GitHub Releases, S3, любой хостинг): по URL отдаётся JSON с полями `version`, `url`, `signature`, `notes` и т.д. (см. документацию Tauri).
2. **Динамический сервер**: по запросу с `{{current_version}}` в URL сервер решает, есть ли обновление, и возвращает 204 или 200 + JSON.

Пример минимального JSON для статики (одна платформа):

```json
{
  "version": "0.2.0-alpha.2",
  "notes": "Release notes",
  "pub_date": "2026-03-08T12:00:00Z",
  "platforms": {
    "linux-x86_64": {
      "signature": "СОДЕРЖИМОЕ_ФАЙЛА_.AppImage.sig",
      "url": "https://example.com/releases/VoiceForge_0.2.0_alpha.2.AppImage"
    }
  }
}
```

---

## 6. CI (GitHub Actions)

- В секретах репозитория сохранить `TAURI_SIGNING_PRIVATE_KEY` (приватный ключ).
- В workflow сборки десктопа перед `npm run tauri build` задать переменную окружения из секрета. В `.github/workflows/release.yml` job `flatpak` уже использует `env.TAURI_SIGNING_PRIVATE_KEY: ${{ secrets.TAURI_SIGNING_PRIVATE_KEY }}` (блок 90).
- Артефакты сборки (включая `.sig`) загружать в Release или на сервер обновлений.

**Важно:** `.env` в репо не подходит для ключа — только переменные окружения CI или защищённое хранилище.

---

## 7. Проверка в приложении

В настройках десктопа уже есть:

- «Проверять обновления при запуске» (сохраняется в localStorage).
- Кнопка «Проверить сейчас».

Если endpoints не настроены или сервер недоступен, пользователь увидит: «Обновления отключены или недоступны».

---

## 8. Чеклист перед первым релизом с updater

- [ ] Ключи сгенерированы, приватный ключ сохранён в безопасном месте.
- [ ] В `tauri.conf.json` прописан `pubkey` и `endpoints`.
- [ ] `createUpdaterArtifacts: true` в `bundle`.
- [ ] Сборка с `TAURI_SIGNING_PRIVATE_KEY` выполняется (локально или в CI).
- [ ] Сервер обновлений отдаёт корректный JSON или 204.
- [ ] Проверка обновления в установленном приложении (кнопка «Проверить сейчас») проходит без ошибок.

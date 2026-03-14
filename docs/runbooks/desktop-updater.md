# Runbook: обновления десктопа (Updater)

Настройка проверки и установки обновлений для десктопного приложения VoiceForge (Tauri 2, tauri-plugin-updater).

**Связанные документы:** [desktop-build-deps.md](desktop-build-deps.md), [release-and-quality.md](release-and-quality.md). План блоков: [plans/roadmap-100-blocks.md](../plans/roadmap-100-blocks.md) (блок 90–92).

---

## 0. Текущее состояние (honest status)

**Updater можно включить скриптом.** В репозитории: `bundle.createUpdaterArtifacts: true` уже установлен; `pubkey` и `endpoints` по умолчанию пустые (режим «обновления отключены»). Чтобы включить обновления: сгенерировать ключи и прописать pubkey/endpoints (вручную или скриптом `scripts/enable_updater.py`). Манифест обновлений — статический JSON в `updates/update.json` (обновляется при каждом релизе).

Текущее состояние можно быстро проверить командой `uv run python scripts/check_release_proof.py --json`: поле `updater.state` должно быть либо `disabled`, либо `ready`; `invalid` означает смешанный и недопустимый repo state.

**Контракт упаковки (packaging contract):** допустимы только два состояния:
- **Отключён:** `pubkey: ""` и `endpoints: []`.
- **Готов к обновлениям:** `pubkey` непустой и `endpoints` — непустой массив URL.

Смешанное состояние (например, pubkey задан, endpoints пустой) считается недопустимым и ломает скрипт проверки `scripts/check_release_metadata.py` при релизе.

---

## 1. Требования

- Подпись обновлений **обязательна** (Tauri не позволяет отключить проверку подписи).
- Нужны два ключа: **приватный** (для подписи артефактов при сборке) и **публичный** (прописывается в `tauri.conf.json` и в приложении у пользователя).

---

## 2. Включение updater (один раз)

Из корня репозитория (нужны Node/npm и `npm ci` в `desktop/`):

```bash
uv run python scripts/enable_updater.py
```

Скрипт: при пустом `pubkey` генерирует ключ в `~/.tauri/voiceforge.key` и обновляет `tauri.conf.json` (pubkey + endpoints на статический URL `updates/update.json` в репо). Если `pubkey` уже задан — только дописывает `endpoints` и `createUpdaterArtifacts`. После первого запуска: сохраните **приватный** ключ, добавьте `TAURI_SIGNING_PRIVATE_KEY` в GitHub Secrets для CI и закоммитьте изменённый `tauri.conf.json` (pubkey и endpoints), чтобы updater был включён в репо.

Ручная генерация ключей (альтернатива):

```bash
cd desktop && npm run tauri signer generate -- -w ~/.tauri/voiceforge.key
```

- Сохраните **приватный** ключ в безопасном месте (потеря = невозможность выпускать обновления для уже установленных копий).
- Публичный ключ (файл `~/.tauri/voiceforge.key.pub`) вставьте в `tauri.conf.json` и задайте `endpoints` (см. ниже).

---

## 3. Конфигурация в репозитории

В `desktop/src-tauri/tauri.conf.json` должна быть секция `plugins.updater` (объект с полями `pubkey` и `endpoints`). Без неё приложение падает при старте с ошибкой десериализации. Для режима «обновления отключены» достаточно пустых значений: `"pubkey": ""`, `"endpoints": []`. Для работы обновлений укажите публичный ключ и URL сервера (см. ниже).

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

**Endpoint по умолчанию (после `enable_updater.py`):** статический файл в репо — `https://raw.githubusercontent.com/<owner>/<repo>/main/updates/update.json`. При каждом релизе этот файл нужно обновлять (см. раздел «Манифест при релизе» ниже).

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

После сборки появятся файлы вида `*.sig` и обновляемые пакеты (например, `.AppImage` + `.AppImage.sig`, или `.deb` + `.deb.sig` в `bundle/deb/`).

---

## 4.1. Манифест при релизе (update.json)

Файл `updates/update.json` должен содержать актуальные `version`, `url` и `signature` для каждой платформы. После подписанной сборки выполните (из корня репо):

```bash
uv run python scripts/write_update_json.py --version 1.0.0-beta.1 \
  --url "https://github.com/<owner>/<repo>/releases/download/v1.0.0-beta.1/VoiceForge_1.0.0-beta.1_amd64.deb" \
  --signature-file desktop/src-tauri/target/release/bundle/deb/VoiceForge_1.0.0-beta.1_amd64.deb.sig
```

Затем закоммитьте и запушьте `updates/update.json`. Либо настройте шаг в release workflow: собрать Tauri с ключом, вызвать `write_update_json.py`, закоммитить и пушнуть `updates/` в ветку по умолчанию (требует прав на запись в репо из CI).

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

## 7. Проверка в приложении (install flow)

В настройках десктопа уже есть:

- «Проверять обновления при запуске» (сохраняется в localStorage).
- Кнопка «Проверить сейчас».

Если endpoints не настроены или сервер недоступен, пользователь увидит: «Обновления отключены или недоступны».

**Проверка install flow после включения updater:**

1. Собрать приложение с `TAURI_SIGNING_PRIVATE_KEY`, убедиться, что созданы артефакты `.sig`.
2. Обновить `updates/update.json` через `write_update_json.py` (или вручную с реальной подписью и URL).
3. Установить текущую (старую) сборку, запустить приложение.
4. В настройках нажать «Проверить сейчас» — должно появиться предложение обновления (если версия в `update.json` выше текущей).
5. Установить обновление и перезапустить — убедиться, что версия изменилась и приложение работает.

---

## 8. Чеклист перед первым релизом с updater

- [ ] Запущен `scripts/enable_updater.py` (или вручную заданы ключи и endpoints).
- [ ] Ключи сгенерированы, приватный ключ сохранён в безопасном месте; `TAURI_SIGNING_PRIVATE_KEY` добавлен в GitHub Secrets при сборке в CI.
- [ ] В `tauri.conf.json` прописан `pubkey` и `endpoints`.
- [ ] `createUpdaterArtifacts: true` в `bundle` (уже включено в репо).
- [ ] Сборка с `TAURI_SIGNING_PRIVATE_KEY` выполняется (локально или в CI).
- [ ] При релизе обновлён `updates/update.json` (скрипт `write_update_json.py` или вручную).
- [ ] Проверка install flow в установленном приложении (кнопка «Проверить сейчас» → установка обновления) проходит без ошибок.

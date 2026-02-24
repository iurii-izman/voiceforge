# Порядок в SonarCloud и Pull Request’ах

Как навести порядок, когда в Sonar висит много анализов по веткам/PR и хочется уменьшить шум.

**Быстрый чеклист:**
1. `gh pr list --state open` — посмотреть открытые PR, закрыть или смержить устаревшие.
2. После мержа PR — удалить ветку (кнопка в GitHub или `gh pr merge N --delete-branch`).
3. `uv run python scripts/sonar_list_branches.py` — посмотреть ветки в Sonar (опционально).
4. В SonarCloud → Project → Pull Requests — при желании ориентироваться, что там висит; удалять старые анализы можно только вручную в Activity (если план даёт такую возможность).

## Что копится

- **GitHub:** каждый открытый PR и каждая ветка, в которую пушат.
- **SonarCloud:** при каждом `push` в `main` и при каждом `pull_request` в `main` запускается workflow SonarCloud — в проекте появляется анализ для этой ветки/PR. В интерфейсе: вкладка **Branches** (долгоживущие ветки) и **Pull Requests** (анализы по PR). Старые анализы никуда не исчезают сами.

Итого: много закрытых/устаревших PR в GitHub и много записей во вкладке «Pull Requests» в SonarCloud.

## 1. Посмотреть, что есть

### GitHub — открытые PR и ветки

```bash
# Список открытых PR
gh pr list --state open

# Список удалённых веток (на origin), кроме main
git fetch --prune && git branch -r | grep -v main
```

### SonarCloud — какие ветки/анализы есть

```bash
uv run python scripts/sonar_list_branches.py
# С опцией --json — полный ответ API
uv run python scripts/sonar_list_branches.py --json
```

Токен берётся из keyring: `voiceforge` / `sonar_token` (см. `keyring-keys-reference.md`).

## 2. Навести порядок в GitHub

- **Закрыть устаревшие PR:** в веб-интерфейсе или `gh pr close <number>`.
- **Удалить ветки после мержа:** при мерже через GitHub можно включить «Delete branch». Или вручную:
  ```bash
  gh pr merge <N> --delete-branch   # если мержите через CLI
  git push origin --delete <branch>  # удалить ветку на remote
  ```
- **Локально почистить ссылки на удалённые ветки:** `git fetch --prune`.

Так уменьшится число веток, по которым в будущем будет запускаться Sonar.

## 3. SonarCloud — что можно сделать

- **Удаление анализов:** в SonarCloud нет публичного API для удаления ветки/анализа. В интерфейсе: **Project → Activity** — там можно удалять старые снимки (если план и настройки это позволяют). Само наличие многих «веток» в списке на работу репо не влияет (см. `repo-governance.md`: Sonar только справочно).
- **Ограничение по веткам:** в **Project Settings → General → Main Branch** задаётся main; анализы PR привязаны к этому проекту. Отключить анализ PR через API/конфиг в нашем workflow без потери проверки main — нельзя без изменения `sonar.yml`.

Итого: основной порядок — в GitHub (закрыть старые PR, удалить ветки). В Sonar — по желанию почистить Activity вручную.

## 4. Рекомендуемый ритм

- Периодически: `gh pr list --state open` — закрывать или мержить то, что не нужно.
- После мержа PR: удалять ветку (`gh pr merge N --delete-branch` или кнопка в GitHub).
- При желании уменьшить список в Sonar: раз в какое-то время заходить в SonarCloud → Project → Activity и удалять старые снимки (если интерфейс даёт такую возможность).

## См. также

- `repo-governance.md` — политика репо, Sonar только как справочник.
- `scripts/sonar_fetch_issues.py` — список открытых issues по коду.
- `scripts/sonar_list_branches.py` — список веток/анализов в SonarCloud.

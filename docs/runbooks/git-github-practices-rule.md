# Правило Git/GitHub (копия для репо)

**Чтобы правило применялось в Cursor:** скопируйте содержимое ниже в `.cursor/rules/git-github-practices.mdc` (каталог `.cursor/` в .gitignore).

Полный runbook: [git-github-practices.md](git-github-practices.md).

```yaml
---
description: Современные практики Git и GitHub — коммиты, теги, issues, Projects
alwaysApply: true
---

# Git и GitHub: практики VoiceForge

Агент при коммитах, пушах и работе с issues/Projects следует этим правилам.

## Коммиты (Conventional Commits)

- **Формат:** type(scope): краткое описание. Типы: feat, fix, docs, chore, refactor, test, ci.
- **Связь с issue:** Closes #N или Refs #N в теле/сообщении.

## Теги

- Формат v0.2.0-alpha.1, только аннотированные. Когда ставить: по release.md.

## GitHub Issues и Project

- Одна задача — один issue; проставлять labels (roadmap, docs, feat, chore, p0/p1/p2).
- Project: VoiceForge Board. При Closes #N — перенести карточку в Done; при старте по issue — In Progress.

## Ссылки

- docs/runbooks/release.md, repo-governance.md, planning-and-tools.md, backlog.md
```

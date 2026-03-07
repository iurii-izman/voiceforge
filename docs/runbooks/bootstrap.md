# Bootstrap Runbook

Recommended bootstrap:

```bash
./scripts/bootstrap.sh
```

Bootstrap вызывает `scripts/ensure_precommit_env.sh`: при отсутствии python3.12 в Fedora/toolbox ставится `dnf install python3.12`, затем `pre-commit clean` и установка хуков. Так pre-commit использует Python 3.12 и не ломается из-за расхождения 3.14.2/3.14.3. **Fedora Atomic Cosmic:** выполняйте bootstrap внутри toolbox. **Python 3.12 и 3.14 установлены в toolbox-43** (fedora-toolbox-43; в других образах Fedora 39+ — как минимум 3.12); для pre-commit и uv используйте окружение внутри toolbox.

Manual path (если python3.12 уже есть):

```bash
uv sync --extra all
uv run pre-commit clean
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
./scripts/doctor.sh
uv run voiceforge status
./scripts/smoke_clean_env.sh
```

Optional service mode:

```bash
uv run voiceforge install-service
uv run voiceforge daemon
```

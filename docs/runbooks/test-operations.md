# Test Operations

## Локальный прогон (Cursor / слабая машина)

Полный `pytest tests/` может вызвать OOM (pyannote/torch). Запускайте подмножество лёгких тестов, см. [next-iteration-focus.md](next-iteration-focus.md) (раздел «Актуальные напоминания»). Пример: `uv run pytest tests/test_prompt_loader.py tests/test_core_metrics.py tests/test_llm_circuit_breaker.py tests/test_tracing.py -q --tb=line`.

### Coverage в toolbox (#56)

Полный отчёт покрытия (`make coverage`) лучше запускать в toolbox (больше памяти, стабильнее). При достижении ≥75% выставить в `pyproject.toml` `fail_under = 75`. Команда из хоста:

```bash
toolbox run -c fedora-toolbox-43 bash -c 'cd /var/home/user/Projects/voiceforge && uv sync --extra all && make coverage'
```

(Путь в контейнере заменить на свой, если репозиторий смонтирован иначе.)

## Flaky test policy

1. Any flaky test must be triaged within 24h.
2. Do not merge with silent flakes on required checks.
3. Temporary quarantine must be explicit in PR and linked to an issue.
4. Quarantined tests must have a removal deadline.

## CI baseline metrics

Track weekly:
1. Green rate for required checks.
2. Median CI duration.
3. Number of flaky incidents.

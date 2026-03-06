# Оставшееся до 100% и план поблочной дореализации (2026)

Снимок на 2026-03-04. **Актуальный единый план:** [docs/plans.md](../../plans.md) (разделы 3–5). Статус W1–W20: [docs/audit/audit.md](../../audit/audit.md).

---

## Недоделанное (точный список)

- **W2/#56 Coverage:** fail_under=69 (цель 70→80%); в omit: main.py, audio/buffer, capture, dbus_service, web/server, diarizer, rag/*, local_llm. Действие: выводить из omit по одному с тестами, поднимать fail_under.
- **W7/#66 Async web (полный):** только ThreadingMixIn; миграция на Starlette/Litestar опциональна.
- **W13/#65 CVE-2025-69872:** pip-audit с --ignore-vuln в CI до фикса upstream (diskcache via instructor).
- **W17 S3776:** do_GET/do_POST if-chains; отложить до #66 или рефакторить точечно.
- **Phase D:** #70 A/B testing, #71 OTel, #72 plugins, #73 packaging GA — бэклог следующих итераций.

---

## План до 100% по блокам

1. **Блок 1 (#56):** fail_under 70→75→80; сократить omit, документировать обоснованные исключения.
2. **Блок 7 (#65):** после фикса upstream — убрать ignore во всех workflow и runbooks.
3. **Блок 8 (#66 полный):** опционально; минимальный 100% (ThreadingMixIn) уже есть.
4. **Блок 10:** синхронизировать доки и таблицы после закрытия #56/#65.
5. **Phase D:** по приоритету при следующих итерациях.

Блоки 2–6, 8 (мин.), 9 реализованы (circuit breaker, purge, backup, monitoring, error format, prompt hash, benchmarks, trace IDs, /ready).

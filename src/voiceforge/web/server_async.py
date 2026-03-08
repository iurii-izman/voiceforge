"""Optional async web server (Starlette + uvicorn). Phase C #66. Use with uv sync --extra web-async and VOICEFORGE_WEB_ASYNC=1 or voiceforge web --async."""

from __future__ import annotations

import asyncio
import contextlib
import json
import threading
from typing import Any

from voiceforge.core.tracing import bind_trace_id, clear_trace_context, get_trace_id

_CONTENT_TYPE_JSON = "application/json; charset=utf-8"
_ERR_INVALID_JSON = "invalid JSON"
_HTTP_STATUS_TO_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    404: "NOT_FOUND",
    422: "UNPROCESSABLE_ENTITY",
    500: "INTERNAL_ERROR",
    501: "NOT_IMPLEMENTED",
    503: "SERVICE_UNAVAILABLE",
}


def _err(status: int, message: str) -> tuple[int, str, bytes]:
    code = _HTTP_STATUS_TO_CODE.get(status, "ERROR")
    body = json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False).encode("utf-8")
    return (status, _CONTENT_TYPE_JSON, body)


def _invalid_json_body() -> bytes:
    return json.dumps({"error": {"code": "BAD_REQUEST", "message": _ERR_INVALID_JSON}}).encode("utf-8")


def _validate_analyze_request(data: dict[str, Any]) -> tuple[int, str | None] | tuple[None, tuple[int, str, bytes]]:
    try:
        seconds = int(data.get("seconds", 30))
    except (TypeError, ValueError):
        return None, _err(400, "seconds must be 1..600")
    if seconds < 1 or seconds > 600:
        return None, _err(400, "seconds must be 1..600")
    template = (data.get("template") or "").strip() or None
    valid = ("standup", "sprint_review", "one_on_one", "brainstorm", "interview")
    if template is not None and template not in valid:
        return None, _err(400, f"template must be one of: {', '.join(valid)}")
    return seconds, template


def _response_from_sync_result(response_cls: Any, result: tuple[int, str, bytes]):
    status, content_type, body = result
    return response_cls(body, status_code=status, media_type=content_type)


async def _to_thread_response(response_cls: Any, sync_fn: Any, *args: Any):
    result = await asyncio.to_thread(sync_fn, *args)
    return _response_from_sync_result(response_cls, result)


async def _json_request_to_response(request: Any, response_cls: Any, sync_fn: Any):
    try:
        data = await request.json()
    except Exception:
        return response_cls(_invalid_json_body(), status_code=400, media_type=_CONTENT_TYPE_JSON)
    return await _to_thread_response(response_cls, sync_fn, data)


def _sync_index() -> tuple[int, str, bytes]:
    from voiceforge.web.server import _html_index

    return (200, "text/html; charset=utf-8", _html_index().encode("utf-8"))


def _sync_status() -> tuple[int, str, bytes]:
    try:
        from voiceforge.cli.status_helpers import get_status_data

        body = json.dumps(get_status_data(), ensure_ascii=False).encode("utf-8")
        return (200, _CONTENT_TYPE_JSON, body)
    except Exception as e:
        return _err(500, str(e))


def _sync_sessions() -> tuple[int, str, bytes]:
    try:
        from voiceforge.cli.history_helpers import build_sessions_payload
        from voiceforge.core.transcript_log import TranscriptLog

        log_db = TranscriptLog()
        try:
            sessions = log_db.get_sessions(last_n=50)
            payload = build_sessions_payload(sessions)
        finally:
            log_db.close()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return (200, _CONTENT_TYPE_JSON, body)
    except Exception as e:
        return _err(500, str(e))


def _sync_session_by_id(sid: str) -> tuple[int, str, bytes]:
    try:
        from voiceforge.cli.history_helpers import build_session_detail_payload, session_not_found_message
        from voiceforge.core.transcript_log import TranscriptLog

        if not sid.isdigit():
            return _err(400, "invalid session id")
        log_db = TranscriptLog()
        try:
            detail = log_db.get_session_detail(int(sid))
            if detail is None:
                return _err(404, session_not_found_message(int(sid)))
            segments, analysis = detail
            payload = build_session_detail_payload(int(sid), segments, analysis)
        finally:
            log_db.close()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return (200, _CONTENT_TYPE_JSON, body)
    except Exception as e:
        return _err(500, str(e))


def _sync_cost(days_str: str, from_str: str, to_str: str) -> tuple[int, str, bytes]:
    try:
        from datetime import date

        from voiceforge.core.metrics import get_stats, get_stats_range

        if from_str and to_str:
            fd = date.fromisoformat(from_str)
            td = date.fromisoformat(to_str)
            if fd > td:
                return _err(400, "from must be <= to")
            data = get_stats_range(fd, td)
        else:
            days = max(1, min(365, int(days_str) if days_str.isdigit() else 30))
            data = get_stats(days=days)
        out = {
            "total_cost_usd": data.get("total_cost_usd", 0),
            "total_calls": data.get("total_calls", 0),
            "by_day": data.get("by_day", []),
        }
        body = json.dumps(out, ensure_ascii=False).encode("utf-8")
        return (200, _CONTENT_TYPE_JSON, body)
    except ValueError as e:
        return _err(400, "invalid date: " + str(e))
    except Exception as e:
        return _err(500, str(e))


def _sync_health() -> tuple[int, str, bytes]:
    body = json.dumps({"status": "ok"}).encode("utf-8")
    return (200, _CONTENT_TYPE_JSON, body)


def _sync_ready() -> tuple[int, str, bytes]:
    try:
        from voiceforge.core.transcript_log import TranscriptLog

        log_db = TranscriptLog()
        try:
            log_db.get_sessions(last_n=1)
        finally:
            log_db.close()
        body = json.dumps({"ready": True}).encode("utf-8")
        return (200, _CONTENT_TYPE_JSON, body)
    except Exception:
        body = json.dumps({"ready": False}).encode("utf-8")
        return (503, _CONTENT_TYPE_JSON, body)


def _sync_metrics() -> tuple[int, str, bytes]:
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        try:
            from voiceforge.core.observability import set_circuit_breaker_states
            from voiceforge.llm.circuit_breaker import get_circuit_breaker

            set_circuit_breaker_states(get_circuit_breaker().get_all_states())
        except ImportError:
            pass
        body = generate_latest()
        return (200, CONTENT_TYPE_LATEST, body)
    except ImportError:
        return (501, "text/plain; charset=utf-8", b"Prometheus client not available")


def _sync_export(sid_str: str, fmt: str) -> tuple[int, str, bytes]:
    if not sid_str or not sid_str.strip().isdigit():
        return _err(400, "id required and must be numeric")
    if fmt not in ("md", "pdf"):
        return _err(400, "format must be md or pdf")
    session_id = int(sid_str.strip())
    try:
        from voiceforge.cli.history_helpers import build_session_markdown, session_not_found_message
        from voiceforge.core.transcript_log import TranscriptLog

        log_db = TranscriptLog()
        try:
            detail = log_db.get_session_detail(session_id)
            if detail is None:
                return _err(404, session_not_found_message(session_id))
            segments, analysis = detail
            md_text = build_session_markdown(session_id, segments, analysis)
        finally:
            log_db.close()
    except Exception as e:
        return _err(500, str(e))
    if fmt == "md":
        return (
            200,
            "text/markdown; charset=utf-8",
            md_text.encode("utf-8"),
        )
    import os as _os
    import subprocess  # nosec B404
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        tmp.write(md_text.encode("utf-8"))
        tmp_md = tmp.name
    out_pdf_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as out_pdf:
            out_pdf_path = out_pdf.name
        subprocess.run(
            ["pandoc", tmp_md, "-o", out_pdf_path, "--pdf-engine=pdflatex"],
            check=True,
            capture_output=True,
        )
        with open(out_pdf_path, "rb") as f:
            body = f.read()
        return (200, "application/pdf", body)
    except FileNotFoundError:
        return _err(501, "Для PDF установите pandoc и pdflatex.")
    except subprocess.CalledProcessError:
        return _err(500, "Ошибка pandoc при создании PDF.")
    finally:
        for p in (tmp_md, out_pdf_path):
            if p:
                with contextlib.suppress(OSError):
                    _os.unlink(p)


def _sync_analyze(data: dict[str, Any]) -> tuple[int, str, bytes]:
    seconds, validation = _validate_analyze_request(data)
    if seconds is None:
        return validation
    template = validation
    try:
        from voiceforge.core.transcript_log import TranscriptLog
        from voiceforge.main import run_analyze_pipeline

        display_text, segments_for_log, analysis_for_log = run_analyze_pipeline(seconds, template=template)
        try:
            from voiceforge.core.contracts import extract_error_message

            err_msg = extract_error_message(display_text, legacy_prefix="Ошибка:")
            if err_msg:
                return _err(422, err_msg)
        except Exception:
            pass
        session_id = None
        try:
            log_db = TranscriptLog()
            session_id = log_db.log_session(
                segments=segments_for_log,
                duration_sec=seconds,
                model=analysis_for_log.get("model", ""),
                questions=analysis_for_log.get("questions"),
                answers=analysis_for_log.get("answers"),
                recommendations=analysis_for_log.get("recommendations"),
                action_items=analysis_for_log.get("action_items"),
                cost_usd=analysis_for_log.get("cost_usd", 0.0),
                template=analysis_for_log.get("template") or template,
            )
            log_db.close()
        except Exception:
            pass
        out = {"session_id": session_id, "display_text": display_text, "analysis": analysis_for_log}
        body = json.dumps(out, ensure_ascii=False).encode("utf-8")
        return (200, _CONTENT_TYPE_JSON, body)
    except Exception as e:
        return _err(500, str(e))


def _sync_action_items_update(data: dict) -> tuple[int, str, bytes]:
    from_session = data.get("from_session")
    next_session = data.get("next_session")
    if from_session is None or next_session is None:
        return _err(400, "from_session and next_session required")
    try:
        from_session = int(from_session)
        next_session = int(next_session)
    except (TypeError, ValueError):
        return _err(400, "from_session and next_session must be integers")
    try:
        from voiceforge.core.transcript_log import TranscriptLog
        from voiceforge.llm.router import update_action_item_statuses
        from voiceforge.main import _get_config, _load_action_item_status, _save_action_item_status
    except ImportError as e:
        return _err(500, str(e))
    log_db = TranscriptLog()
    try:
        detail_from = log_db.get_session_detail(from_session)
        detail_next = log_db.get_session_detail(next_session)
    finally:
        log_db.close()
    if detail_from is None:
        return _err(404, "session not found: " + str(from_session))
    if detail_next is None:
        return _err(404, "session not found: " + str(next_session))
    segments_next, _ = detail_next
    analysis_from = detail_from[1]
    if analysis_from is None:
        return _err(400, "no analysis (action items) in session " + str(from_session))
    action_items = analysis_from.action_items
    if not action_items:
        body = json.dumps({"updates": [], "cost_usd": 0.0}, ensure_ascii=False).encode("utf-8")
        return (200, _CONTENT_TYPE_JSON, body)
    transcript_next = "\n".join(s.text for s in segments_next).strip()
    if not transcript_next:
        return _err(400, "no segment text in session " + str(next_session))
    cfg = _get_config()
    try:
        response, cost_usd = update_action_item_statuses(
            action_items, transcript_next, model=cfg.default_llm, pii_mode=cfg.pii_mode
        )
    except Exception as e:
        return _err(500, str(e))
    updates = [(u.id, u.status) for u in response.updates]
    status_data = _load_action_item_status()
    for idx, status in updates:
        status_data[f"{from_session}:{idx}"] = status
    if updates:
        _save_action_item_status(status_data)
    out = {
        "from_session": from_session,
        "next_session": next_session,
        "updates": [{"id": i, "status": s} for i, s in updates],
        "cost_usd": cost_usd,
    }
    body = json.dumps(out, ensure_ascii=False).encode("utf-8")
    return (200, _CONTENT_TYPE_JSON, body)


def _sync_telegram_webhook(body_bytes: bytes) -> tuple[int, str, bytes]:
    from voiceforge.core.secrets import get_api_key

    token = get_api_key("webhook_telegram")
    if not token:
        return (503, _CONTENT_TYPE_JSON, b'{"ok":false,"error":"webhook_telegram not in keyring"}')
    try:
        data = json.loads(body_bytes.decode("utf-8") if body_bytes else "{}")
    except json.JSONDecodeError:
        return _err(400, _ERR_INVALID_JSON)
    from voiceforge.web.server import _telegram_send_message, _telegram_webhook_reply

    message = (data or {}).get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    if chat_id is None:
        return (200, _CONTENT_TYPE_JSON, b'{"ok":true}')
    if text == "/subscribe":
        from voiceforge.core.telegram_notify import set_telegram_chat_id

        set_telegram_chat_id(chat_id)
        reply = "Push notifications enabled. You'll get a message when analyze completes."
    else:
        reply = _telegram_webhook_reply(text)
    _telegram_send_message(token, chat_id, reply)
    return (200, _CONTENT_TYPE_JSON, b'{"ok":true}')


def _build_app():  # NOSONAR S3776 — single place wiring all async routes; splitting would scatter routing
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route

    async def add_trace_id(request: Request, call_next):
        clear_trace_context()
        tid = (request.headers.get("x-trace-id") or "").strip() or None
        bind_trace_id(tid)
        response = await call_next(request)
        if get_trace_id() and "x-trace-id" not in response.headers:
            response.headers["x-trace-id"] = get_trace_id()
        return response

    async def get_index(_request: Request) -> Response:
        return await _to_thread_response(Response, _sync_index)

    async def get_status(_request: Request) -> Response:
        return await _to_thread_response(Response, _sync_status)

    async def get_sessions(_request: Request) -> Response:
        return await _to_thread_response(Response, _sync_sessions)

    async def get_session_id(request: Request) -> Response:
        sid = request.path_params["sid"]
        return await _to_thread_response(Response, _sync_session_by_id, sid)

    async def get_cost(request: Request) -> Response:
        q = request.query_params
        return await _to_thread_response(
            Response,
            _sync_cost,
            q.get("days", "30") or "30",
            q.get("from", "") or "",
            q.get("to", "") or "",
        )

    async def get_export(request: Request) -> Response:
        q = request.query_params
        return await _to_thread_response(
            Response,
            _sync_export,
            q.get("id", "") or "",
            (q.get("format", "md") or "md").lower(),
        )

    async def get_health(_request: Request) -> Response:
        return await _to_thread_response(Response, _sync_health)

    async def get_ready(_request: Request) -> Response:
        return await _to_thread_response(Response, _sync_ready)

    async def get_metrics(_request: Request) -> Response:
        return await _to_thread_response(Response, _sync_metrics)

    async def post_analyze(request: Request) -> Response:
        return await _json_request_to_response(request, Response, _sync_analyze)

    async def post_analyze_stream(request: Request):
        """SSE stream of LLM analyze output (#91). POST body: {seconds, template?}."""
        try:
            data = await request.json()
        except Exception:
            return Response(
                json.dumps({"error": {"code": "BAD_REQUEST", "message": _ERR_INVALID_JSON}}).encode("utf-8"),
                status_code=400,
                media_type=_CONTENT_TYPE_JSON,
            )
        seconds, validation = _validate_analyze_request(data)
        if seconds is None:
            return _response_from_sync_result(Response, validation)
        template = validation
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def put(chunk: str | None) -> None:
            loop.call_soon_threadsafe(queue.put_nowait, chunk)

        def run() -> None:
            try:
                from voiceforge.main import run_analyze_pipeline

                run_analyze_pipeline(seconds, template=template, stream_callback=put)
            finally:
                put(None)

        threading.Thread(target=run, daemon=True).start()

        async def event_stream():
            while True:
                chunk = await queue.get()
                if chunk is None:
                    yield "event: done\ndata: {}\n\n"
                    break
                yield f"data: {json.dumps({'delta': chunk}, ensure_ascii=False)}\n\n"

        from starlette.responses import StreamingResponse

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async def post_action_items(request: Request) -> Response:
        return await _json_request_to_response(request, Response, _sync_action_items_update)

    async def post_telegram_webhook(request: Request) -> Response:
        body_bytes = await request.body()
        return await _to_thread_response(Response, _sync_telegram_webhook, body_bytes)

    from starlette.middleware.base import BaseHTTPMiddleware

    class TraceMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            return await add_trace_id(request, call_next)

    routes = [
        Route("/", get_index),
        Route("/index.html", get_index),
        Route("/api/status", get_status),
        Route("/api/sessions", get_sessions),
        Route("/api/sessions/{sid}", get_session_id),
        Route("/api/cost", get_cost),
        Route("/api/export", get_export),
        Route("/health", get_health),
        Route("/ready", get_ready),
        Route("/metrics", get_metrics),
        Route("/api/analyze", post_analyze, methods=["POST"]),
        Route("/api/analyze/stream", post_analyze_stream, methods=["POST"]),
        Route("/api/action-items/update", post_action_items, methods=["POST"]),
        Route("/api/telegram/webhook", post_telegram_webhook, methods=["POST"]),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(TraceMiddleware)
    return app


def run_async_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    import uvicorn

    app = _build_app()
    print(f"VoiceForge Web UI (async): http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")

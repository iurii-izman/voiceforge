"""Block 12: Simple local Web UI — stdlib HTTP server, no extra deps. ADR-0005: Telegram webhook."""

from __future__ import annotations

import contextlib
import json
import logging
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

_log = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"
_CONTENT_TYPE_JSON = "application/json; charset=utf-8"
_ERR_INVALID_JSON = "invalid JSON"


def _telegram_send_message(token: str, chat_id: int | str, text: str) -> None:
    """Send Telegram sendMessage. ADR-0005."""
    url = f"{_TELEGRAM_API}/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", _CONTENT_TYPE_JSON)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status >= 400:
                _log.warning("telegram.sendMessage failed", status=r.status, body=r.read())
    except Exception as e:
        _log.warning("telegram.sendMessage error", error=str(e))


def _html_index() -> str:
    return """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VoiceForge</title>
  <style>
    :root { --bg: #0f0f12; --card: #1a1a1f; --text: #e4e4e7; --muted: #71717a; --accent: #a78bfa; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 1rem; line-height: 1.5; }
    h1 { font-size: 1.25rem; margin: 0 0 1rem; }
    .card { background: var(--card); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
    .muted { color: var(--muted); font-size: 0.875rem; }
    button { background: var(--accent); color: var(--bg); border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    #sessions { list-style: none; padding: 0; margin: 0; }
    #sessions li { padding: 0.5rem 0; border-bottom: 1px solid var(--muted); }
    #sessions a { color: var(--accent); text-decoration: none; }
    #result { white-space: pre-wrap; font-size: 0.875rem; }
    .err { color: #f87171; }
  </style>
</head>
<body>
  <h1>VoiceForge</h1>
  <div class="card">
    <div id="status" class="muted">Загрузка…</div>
    <p style="margin: 0.5rem 0 0;">
      <label>Последние <input type="number" id="analyzeSeconds" min="1" max="600" value="30" style="width:4em;"> с</label>
      <label style="margin-left:0.5rem;">Шаблон <select id="analyzeTemplate"><option value="">—</option><option value="standup">standup</option><option value="sprint_review">sprint_review</option><option value="one_on_one">one_on_one</option><option value="brainstorm">brainstorm</option><option value="interview">interview</option></select></label>
      <button id="analyzeBtn">Анализ</button>
      <span id="analyzeStatus" class="muted"></span>
    </p>
  </div>
  <div class="card">
    <h2 style="font-size: 1rem; margin: 0 0 0.5rem;">Затраты</h2>
    <p class="muted"><label>Дней <input type="number" id="costDays" min="1" max="365" value="30" style="width:3em;"></label> <button id="costBtn">Показать</button></p>
    <div id="costResult" class="muted"></div>
  </div>
  <div class="card">
    <h2 style="font-size: 1rem; margin: 0 0 0.5rem;">Обновить статусы action items</h2>
    <p class="muted"><label>Сессия с action items <input type="number" id="aiFromSession" min="1" style="width:4em;"></label> <label style="margin-left:0.5rem;">Сессия встречи <input type="number" id="aiNextSession" min="1" style="width:4em;"></label> <button id="aiUpdateBtn">Обновить</button></p>
    <div id="aiUpdateStatus" class="muted"></div>
  </div>
  <div class="card">
    <h2 style="font-size: 1rem; margin: 0 0 0.5rem;">Сессии</h2>
    <ul id="sessions"></ul>
  </div>
  <div class="card" id="resultCard" style="display:none;">
    <h2 style="font-size: 1rem; margin: 0 0 0.5rem;">Результат</h2>
    <p id="exportLinks" class="muted" style="margin: 0 0 0.5rem; display:none;"></p>
    <div id="result"></div>
  </div>
  <script>
    async function api(path, opts) {
      const r = await fetch(path, opts);
      const text = await r.text();
      if (!r.ok) throw new Error(text || r.statusText);
      try { return JSON.parse(text); } catch (_) { return text; }
    }
    async function loadStatus() {
      try {
        const d = await api('/api/status');
        document.getElementById('status').textContent =
          'RAM: ' + d.ram.used_gb + '/' + d.ram.total_gb + ' GB, Сегодня: $' + d.cost_today_usd + ', Ollama: ' + (d.ollama_available ? 'да' : 'нет');
      } catch (e) {
        document.getElementById('status').textContent = 'Ошибка: ' + e.message;
        document.getElementById('status').className = 'err';
      }
    }
    async function loadSessions() {
      const ul = document.getElementById('sessions');
      try {
        const d = await api('/api/sessions');
        ul.innerHTML = '';
        if (!d.sessions || d.sessions.length === 0) {
          ul.innerHTML = '<li class="muted">Нет сессий. Запустите анализ.</li>';
        } else {
          d.sessions.forEach(s => {
            const li = document.createElement('li');
            li.style.cursor = 'pointer';
            li.innerHTML = '<span style="color: var(--accent);">#' + s.id + '</span> ' + (s.started_at || '') + ' — ' + (s.duration_sec || 0) + ' с';
            li.onclick = () => { fetch('/api/sessions/' + s.id).then(r => r.json()).then(d => showResult(d)); };
            ul.appendChild(li);
          });
        }
      } catch (e) {
        ul.innerHTML = '<li class="err">Ошибка: ' + e.message + '</li>';
      }
    }
    function showResult(data) {
      const card = document.getElementById('resultCard');
      const el = document.getElementById('result');
      const exportLinks = document.getElementById('exportLinks');
      if (data.segments && data.session_id) {
        exportLinks.style.display = 'block';
        exportLinks.innerHTML = 'Скачать: <a href="/api/export?id=' + data.session_id + '&format=md" download="session_' + data.session_id + '.md">Markdown</a> | <a href="/api/export?id=' + data.session_id + '&format=pdf" download="session_' + data.session_id + '.pdf">PDF</a>';
        let t = '';
        (data.segments || []).forEach(s => t += (s.speaker ? '[' + s.speaker + '] ' : '') + (s.text || '') + '\\n');
        if (data.analysis) t += '\\n--- Анализ ---\\n' + JSON.stringify(data.analysis, null, 2);
        el.textContent = t;
      } else {
        exportLinks.style.display = 'none';
        exportLinks.innerHTML = '';
        el.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
      }
      card.style.display = 'block';
    }
    document.getElementById('analyzeBtn').onclick = async function() {
      const btn = this;
      const st = document.getElementById('analyzeStatus');
      const secEl = document.getElementById('analyzeSeconds');
      const tmplEl = document.getElementById('analyzeTemplate');
      const seconds = Math.max(1, Math.min(600, parseInt(secEl.value, 10) || 30));
      const template = (tmplEl.value || '').trim() || null;
      btn.disabled = true;
      st.textContent = 'Выполняю…';
      try {
        const body = { seconds };
        if (template) body.template = template;
        const d = await api('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
        st.textContent = 'session_id=' + (d.session_id || '-');
        if (d.display_text) showResult({ display_text: d.display_text });
        loadSessions();
      } catch (e) {
        st.textContent = 'Ошибка';
        st.className = 'err';
        showResult({ err: e.message });
      }
      btn.disabled = false;
    };
    async function loadCost() {
      const days = Math.max(1, Math.min(365, parseInt(document.getElementById('costDays').value, 10) || 30));
      try {
        const d = await api('/api/cost?days=' + days);
        const el = document.getElementById('costResult');
        let html = 'Итого: $' + (d.total_cost_usd || 0).toFixed(4) + ' (вызовов: ' + (d.total_calls || 0) + ')';
        if (d.by_day && d.by_day.length) {
          html += '<br>По дням (последние 10):<br>';
          d.by_day.slice(-10).reverse().forEach(r => {
            html += '  ' + (r.date || '') + ': $' + (r.cost_usd || 0).toFixed(4) + ' (' + (r.calls || 0) + ')<br>';
          });
        }
        el.innerHTML = html;
      } catch (e) {
        document.getElementById('costResult').innerHTML = 'Ошибка: ' + e.message;
      }
    }
    document.getElementById('costBtn').onclick = loadCost;
    document.getElementById('aiUpdateBtn').onclick = async function() {
      const fromId = parseInt(document.getElementById('aiFromSession').value, 10);
      const nextId = parseInt(document.getElementById('aiNextSession').value, 10);
      const st = document.getElementById('aiUpdateStatus');
      if (!fromId || !nextId) { st.textContent = 'Укажите оба ID сессий'; return; }
      st.textContent = 'Выполняю…';
      try {
        const d = await api('/api/action-items/update', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ from_session: fromId, next_session: nextId }) });
        st.textContent = 'Обновлено: ' + (d.updates && d.updates.length ? d.updates.length : 0) + ', cost $' + (d.cost_usd || 0).toFixed(4);
      } catch (e) {
        st.textContent = 'Ошибка: ' + e.message;
      }
    };
    loadStatus();
    loadSessions();
  </script>
</body>
</html>
"""


class _VoiceForgeHandler(BaseHTTPRequestHandler):
    def _send_json(self, obj: Any, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", _CONTENT_TYPE_JSON)
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _send_html(self, html: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _send_error_json(self, message: str, status: int = 400) -> None:
        self._send_json({"error": message}, status=status)

    def _parse_path(self) -> tuple[str, dict[str, str]]:
        path = urllib.parse.unquote(self.path)
        if "?" in path:
            path, qs = path.split("?", 1)
            params = urllib.parse.parse_qs(qs)
            return path.rstrip("/"), {k: v[0] if v else "" for k, v in params.items()}
        return path.rstrip("/") or "/", {}

    def _handle_get_index(self) -> None:
        self._send_html(_html_index())

    def _handle_get_status(self) -> None:
        try:
            from voiceforge.cli.status_helpers import get_status_data

            self._send_json(get_status_data())
        except Exception as e:
            self._send_error_json(str(e), 500)

    def _handle_get_sessions(self) -> None:
        try:
            from voiceforge.cli.history_helpers import build_sessions_payload
            from voiceforge.core.transcript_log import TranscriptLog

            log_db = TranscriptLog()
            try:
                sessions = log_db.get_sessions(last_n=50)
                self._send_json(build_sessions_payload(sessions))
            finally:
                log_db.close()
        except Exception as e:
            self._send_error_json(str(e), 500)

    def _handle_get_session_by_id(self, sid: str) -> None:
        try:
            from voiceforge.cli.history_helpers import build_session_detail_payload
            from voiceforge.core.transcript_log import TranscriptLog

            log_db = TranscriptLog()
            try:
                detail = log_db.get_session_detail(int(sid))
                if detail is None:
                    self._send_error_json("session not found", 404)
                    return
                segments, analysis = detail
                payload = build_session_detail_payload(int(sid), segments, analysis)
                self._send_json(payload)
            finally:
                log_db.close()
        except Exception as e:
            self._send_error_json(str(e), 500)

    def _handle_get_cost(self, params: dict[str, str]) -> None:
        days_str = (params.get("days") or "30").strip()
        from_str = params.get("from", "").strip()
        to_str = params.get("to", "").strip()
        try:
            from datetime import date

            from voiceforge.core.metrics import get_stats, get_stats_range

            if from_str and to_str:
                fd = date.fromisoformat(from_str)
                td = date.fromisoformat(to_str)
                if fd > td:
                    self._send_error_json("from must be <= to", 400)
                    return
                data = get_stats_range(fd, td)
            else:
                days = max(1, min(365, int(days_str) if days_str.isdigit() else 30))
                data = get_stats(days=days)
            self._send_json(
                {
                    "total_cost_usd": data.get("total_cost_usd", 0),
                    "total_calls": data.get("total_calls", 0),
                    "by_day": data.get("by_day", []),
                }
            )
        except ValueError as e:
            self._send_error_json("invalid date: " + str(e), 400)
        except Exception as e:
            self._send_error_json(str(e), 500)

    def _handle_get_export(self, params: dict[str, str]) -> None:
        sid_str = params.get("id", "").strip()
        fmt = (params.get("format", "md") or "md").lower()
        if not sid_str.isdigit():
            self._send_error_json("id required and must be numeric", 400)
            return
        if fmt not in ("md", "pdf"):
            self._send_error_json("format must be md or pdf", 400)
            return
        session_id = int(sid_str)
        try:
            from voiceforge.cli.history_helpers import build_session_markdown, session_not_found_message
            from voiceforge.core.transcript_log import TranscriptLog

            log_db = TranscriptLog()
            try:
                detail = log_db.get_session_detail(session_id)
                if detail is None:
                    self._send_error_json(session_not_found_message(session_id), 404)
                    return
                segments, analysis = detail
                md_text = build_session_markdown(session_id, segments, analysis)
            finally:
                log_db.close()
        except Exception as e:
            self._send_error_json(str(e), 500)
            return
        if fmt == "md":
            self.send_response(200)
            self.send_header("Content-Type", "text/markdown; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="session_{session_id}.md"')
            self.end_headers()
            self.wfile.write(md_text.encode("utf-8"))
            return
        import os as _os
        import subprocess  # nosec B404 -- pandoc for PDF export
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp.write(md_text.encode("utf-8"))
            tmp_md = tmp.name
        out_pdf_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as out_pdf:
                out_pdf_path = out_pdf.name
            if out_pdf_path is None:
                self._send_error_json("Failed to create temp PDF file.", 500)
                return
            subprocess.run(  # nosec B603 B607 -- pandoc from PATH, paths from our request
                ["pandoc", tmp_md, "-o", out_pdf_path, "--pdf-engine=pdflatex"],
                check=True,
                capture_output=True,
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'attachment; filename="session_{session_id}.pdf"')
            self.end_headers()
            with open(out_pdf_path, "rb") as f:
                self.wfile.write(f.read())
        except FileNotFoundError:
            self._send_error_json("Для PDF установите pandoc и pdflatex.", 501)
        except subprocess.CalledProcessError:
            self._send_error_json("Ошибка pandoc при создании PDF.", 500)
        finally:
            for p in (tmp_md, out_pdf_path):
                if p:
                    with contextlib.suppress(OSError):
                        _os.unlink(p)

    def do_GET(self) -> None:
        path, params = self._parse_path()
        if path == "/" or path == "/index.html":
            self._handle_get_index()
            return
        if path == "/api/status":
            self._handle_get_status()
            return
        if path == "/api/sessions":
            self._handle_get_sessions()
            return
        if path.startswith("/api/sessions/"):
            sid = path.split("/")[-1]
            if not sid.isdigit():
                self._send_error_json("invalid session id", 400)
                return
            self._handle_get_session_by_id(sid)
            return
        if path == "/api/cost":
            self._handle_get_cost(params)
            return
        if path == "/api/export":
            self._handle_get_export(params)
            return
        self.send_error(404, "Not found")

    def _handle_action_items_update(self, data: dict) -> None:
        """Handle POST /api/action-items/update: from_session, next_session."""
        from_session = data.get("from_session")
        next_session = data.get("next_session")
        if from_session is None or next_session is None:
            self._send_error_json("from_session and next_session required", 400)
            return
        try:
            from_session = int(from_session)
            next_session = int(next_session)
        except (TypeError, ValueError):
            self._send_error_json("from_session and next_session must be integers", 400)
            return
        try:
            from voiceforge.core.transcript_log import TranscriptLog
            from voiceforge.llm.router import update_action_item_statuses
            from voiceforge.main import _get_config, _load_action_item_status, _save_action_item_status
        except ImportError as e:
            self._send_error_json(str(e), 500)
            return
        log_db = TranscriptLog()
        try:
            detail_from = log_db.get_session_detail(from_session)
            detail_next = log_db.get_session_detail(next_session)
        finally:
            log_db.close()
        if detail_from is None:
            self._send_error_json("session not found: " + str(from_session), 404)
            return
        if detail_next is None:
            self._send_error_json("session not found: " + str(next_session), 404)
            return
        segments_next, analysis_from = detail_next, detail_from[1]
        if analysis_from is None:
            self._send_error_json("no analysis (action items) in session " + str(from_session), 400)
            return
        action_items = analysis_from.action_items
        if not action_items:
            self._send_json({"updates": [], "cost_usd": 0.0})
            return
        transcript_next = "\n".join(s.text for s in segments_next).strip()
        if not transcript_next:
            self._send_error_json("no segment text in session " + str(next_session), 400)
            return
        cfg = _get_config()
        try:
            response, cost_usd = update_action_item_statuses(
                action_items,
                transcript_next,
                model=cfg.default_llm,
                pii_mode=cfg.pii_mode,
            )
        except Exception as e:
            self._send_error_json(str(e), 500)
            return
        updates = [(u.id, u.status) for u in response.updates]
        status_data = _load_action_item_status()
        for idx, status in updates:
            status_data[f"{from_session}:{idx}"] = status
        if updates:
            _save_action_item_status(status_data)
        self._send_json(
            {
                "from_session": from_session,
                "next_session": next_session,
                "updates": [{"id": i, "status": s} for i, s in updates],
                "cost_usd": cost_usd,
            }
        )

    def _handle_post_analyze(self, data: dict[str, Any]) -> None:
        seconds = int(data.get("seconds", 30))
        if seconds < 1 or seconds > 600:
            self._send_error_json("seconds must be 1..600", 400)
            return
        template = (data.get("template") or "").strip() or None
        _VALID_TEMPLATES = ("standup", "sprint_review", "one_on_one", "brainstorm", "interview")
        if template is not None and template not in _VALID_TEMPLATES:
            self._send_error_json(f"template must be one of: {', '.join(_VALID_TEMPLATES)}", 400)
            return
        try:
            from voiceforge.core.transcript_log import TranscriptLog
            from voiceforge.main import run_analyze_pipeline

            display_text, segments_for_log, analysis_for_log = run_analyze_pipeline(seconds, template=template)
            error_message = None
            try:
                from voiceforge.core.contracts import extract_error_message

                error_message = extract_error_message(display_text, legacy_prefix="Ошибка:")
            except Exception as _e:
                _log.debug("extract_error_message failed", exc_info=_e)
            if error_message:
                self._send_json({"error": error_message, "display_text": display_text}, 200)
                return
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
            except Exception as _e:
                _log.debug("log_session/close failed", exc_info=_e)
            self._send_json(
                {
                    "session_id": session_id,
                    "display_text": display_text,
                    "analysis": analysis_for_log,
                }
            )
        except Exception as e:
            self._send_error_json(str(e), 500)

    def _handle_telegram_webhook(self, body: bytes) -> None:
        """POST /api/telegram/webhook: Telegram Update. ADR-0005. Key: webhook_telegram."""
        from voiceforge.core.secrets import get_api_key

        token = get_api_key("webhook_telegram")
        if not token:
            self.send_response(503)
            self.send_header("Content-Type", _CONTENT_TYPE_JSON)
            self.end_headers()
            self.wfile.write(b'{"ok":false,"error":"webhook_telegram not in keyring"}')
            return
        try:
            data = json.loads(body.decode("utf-8") if body else "{}")
        except json.JSONDecodeError:
            self._send_error_json(_ERR_INVALID_JSON, 400)
            return
        message = (data or {}).get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = (message.get("text") or "").strip()
        if chat_id is None:
            self.send_response(200)
            self.end_headers()
            return
        if text == "/start":
            reply = "VoiceForge bot. Commands: /start /status /sessions /cost [days]"
        elif text == "/status":
            try:
                from voiceforge.cli.status_helpers import get_status_data

                d = get_status_data()
                ram = d.get("ram") or {}
                reply = (
                    f"RAM: {ram.get('used_gb', 0)}/{ram.get('total_gb', 0)} GB | "
                    f"Today: ${d.get('cost_today_usd', 0):.4f} | "
                    f"Ollama: {'yes' if d.get('ollama_available') else 'no'}"
                )
            except Exception as e:
                _log.debug("telegram status failed", exc_info=e)
                reply = f"Status error: {e!s}"
        elif text == "/sessions":
            try:
                from voiceforge.cli.history_helpers import build_sessions_payload
                from voiceforge.core.transcript_log import TranscriptLog

                log_db = TranscriptLog()
                try:
                    sessions = log_db.get_sessions(last_n=10)
                    payload = build_sessions_payload(sessions)
                finally:
                    log_db.close()
                lines = []
                for s in payload.get("sessions") or []:
                    sid = s.get("id")
                    started = (s.get("started_at") or "")[:19]
                    dur = s.get("duration_sec", 0)
                    lines.append(f"#{sid} {started} {dur:.0f}s")
                reply = "\n".join(lines) if lines else "No sessions"
            except Exception as e:
                _log.debug("telegram sessions failed", exc_info=e)
                reply = f"Sessions error: {e!s}"
        elif text.startswith("/cost"):
            try:
                days = 7
                parts = text.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    days = max(1, min(365, int(parts[1])))
                from voiceforge.core.metrics import get_stats

                data = get_stats(days=days)
                total = data.get("total_cost_usd") or 0
                calls = data.get("total_calls") or 0
                reply = f"Cost last {days} days: ${total:.4f} ({calls} calls)"
            except Exception as e:
                _log.debug("telegram cost failed", exc_info=e)
                reply = f"Cost error: {e!s}"
        else:
            reply = "Use /start, /status, /sessions, /cost [days]"
        _telegram_send_message(token, chat_id, reply)
        self.send_response(200)
        self.send_header("Content-Type", _CONTENT_TYPE_JSON)
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_POST(self) -> None:
        path, _ = self._parse_path()
        if path == "/api/telegram/webhook":
            content_length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(content_length) if content_length else b"{}"
            self._handle_telegram_webhook(body)
            return
        if path == "/api/analyze":
            content_length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            try:
                data = json.loads(body) if body.strip() else {}
            except json.JSONDecodeError:
                self._send_error_json(_ERR_INVALID_JSON, 400)
                return
            self._handle_post_analyze(data)
            return
        if path == "/api/action-items/update":
            content_length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
            try:
                data = json.loads(body) if body.strip() else {}
            except json.JSONDecodeError:
                self._send_error_json(_ERR_INVALID_JSON, 400)
                return
            self._handle_action_items_update(data)
            return
        self.send_error(404, "Not found")

    def log_message(self, format: str, *args: Any) -> None:
        pass  # quiet by default; set log_request=True on server to enable


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    with HTTPServer((host, port), _VoiceForgeHandler) as httpd:
        print(f"VoiceForge Web UI: http://{host}:{port}")
        httpd.serve_forever()

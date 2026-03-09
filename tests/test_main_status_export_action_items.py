from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest


@dataclass
class _FakeSegment:
    text: str


@dataclass
class _FakeAnalysis:
    action_items: list[dict[str, str]] | None = None


class _FakeValidateLogDb:
    def __init__(self, detail_from, detail_next) -> None:
        self._detail_from = detail_from
        self._detail_next = detail_next

    def get_session_detail(self, session_id: int):
        if session_id == 1:
            return self._detail_from
        if session_id == 2:
            return self._detail_next
        return None


def test_main_status_text_and_json_branches(monkeypatch) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))
    monkeypatch.setattr(main, "get_doctor_text", lambda: "doctor text")
    monkeypatch.setattr(main, "get_status_detailed_text", lambda budget: f"detailed text {budget}")
    monkeypatch.setattr(main, "get_status_text", lambda: "status text")
    monkeypatch.setattr(main, "get_status_detailed_data", lambda budget: {"budget_limit_usd": budget, "stats_7d": {}})
    monkeypatch.setattr(main, "get_doctor_data", lambda: {"checks": [], "errors": 0})
    monkeypatch.setattr(main, "_get_config", lambda: SimpleNamespace(budget_limit_usd=12.5))

    main.status(output="text", doctor=True, detailed=False)
    main.status(output="text", detailed=True, doctor=False)
    main.status(output="text", doctor=False, detailed=False)
    main.status(output="json", detailed=True, doctor=False)
    main.status(output="json", doctor=True, detailed=False)

    text_messages = [message for message, _ in echoed[:3]]
    assert "doctor text" in text_messages
    assert "detailed text 12.5" in text_messages
    assert "status text" in text_messages
    json_payloads = [json.loads(message) for message, _ in echoed[3:]]
    detailed_payload = next(payload for payload in json_payloads if "budget_limit_usd" in payload["data"])
    doctor_payload = next(payload for payload in json_payloads if "checks" in payload["data"])
    assert detailed_payload["ok"] is True
    assert detailed_payload["data"]["budget_limit_usd"] == pytest.approx(12.5)
    assert doctor_payload["data"] == {"checks": [], "errors": 0}


def test_main_cli_payload_and_hint_helpers() -> None:
    from voiceforge import main

    err_payload = main._cli_error_payload("E1", "boom", retryable=True)
    ok_payload = main._cli_success_payload({"x": 1})

    assert err_payload["error"]["code"] == "E1"
    assert err_payload["error"]["retryable"] is True
    assert ok_payload["data"] == {"x": 1}
    assert "keyring" in (main._hint_for_error("missing keyring secrets") or "").lower()
    assert "PipeWire" in (main._hint_for_error("audio capture failed") or "")
    assert "voiceforge daemon" in (main._hint_for_error("daemon unavailable") or "")
    assert main._extract_error_message('{"error":{"message":"nested"}}') == "nested"


def test_main_ical_and_session_helpers(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    class _FakeLogDb:
        def get_sessions_in_range(self, from_date, to_date):
            return [SimpleNamespace(id=1, started_at="2026-03-08T10:00:00+00:00", duration_sec=60)]

        def get_sessions(self, last_n: int, offset: int):
            return [SimpleNamespace(id=2, started_at="2026-03-08T11:00:00+00:00", duration_sec=120)]

    sessions = main._sessions_to_ical_fetch_sessions(_FakeLogDb(), "2026-03-01", "2026-03-02", 5)
    assert sessions[0].id == 1
    sessions_latest = main._sessions_to_ical_fetch_sessions(_FakeLogDb(), None, None, 5)
    assert sessions_latest[0].id == 2

    with pytest.raises(SystemExit) as exc_invalid:
        main._sessions_to_ical_fetch_sessions(_FakeLogDb(), "bad-date", "2026-03-02", 5)
    assert exc_invalid.value.code == 1
    assert echoed[-1][1] is True

    assert main._iso_to_ical_utc("2026-03-08T10:00:00Z") == "20260308T100000Z"
    assert main._iso_to_ical_utc("not-a-date") == ""

    session = SimpleNamespace(id=7, started_at="2026-03-08T10:00:00+00:00", duration_sec=90)
    vevent = main._session_to_vevent_lines(session)
    assert "BEGIN:VEVENT" in vevent
    assert "UID:session-7@voiceforge" in vevent
    assert "DTEND:20260308T100130Z" in vevent


def test_main_template_and_speaker_helpers() -> None:
    from voiceforge import main

    diar_segments = [
        SimpleNamespace(start=0.0, end=1.0, speaker="S1"),
        SimpleNamespace(start=1.0, end=2.0, speaker="S2"),
    ]
    assert main._speaker_for_interval(1.1, 1.8, diar_segments) == "S2"
    assert main._speaker_for_interval(2.5, 3.0, diar_segments) == ""

    lines, analysis = main._format_template_result(
        "standup",
        SimpleNamespace(model_dump=lambda mode="json": {"done": ["a"], "planned": ["b"], "blockers": ["c"]}),
    )
    assert any("Сделано" in line for line in lines)
    assert analysis["answers"] == ["a", "b", "c"]

    lines_one_on_one, analysis_one_on_one = main._format_template_result(
        "one_on_one",
        SimpleNamespace(
            model_dump=lambda mode="json": {
                "mood": "good",
                "growth": ["grow"],
                "blockers": ["none"],
                "action_items": [{"description": "Ship", "assignee": "A"}],
            }
        ),
    )
    assert any("Ship" in line for line in lines_one_on_one)
    assert analysis_one_on_one["action_items"] == [{"description": "Ship", "assignee": "A"}]

    unknown_lines, unknown_analysis = main._format_template_result(
        "unknown",
        SimpleNamespace(model_dump=lambda mode="json": {"x": 1}),
    )
    assert unknown_lines == []
    assert unknown_analysis["answers"] == []


def test_main_action_items_update_validate_error_branches(monkeypatch) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    missing_from = _FakeValidateLogDb(None, ([_FakeSegment("done")], None))
    with pytest.raises(SystemExit) as exc_missing_from:
        main._action_items_update_validate(missing_from, 1, 2)
    assert exc_missing_from.value.code == 1

    missing_next = _FakeValidateLogDb(([_FakeSegment("x")], _FakeAnalysis(action_items=[{"description": "Ship"}])), None)
    with pytest.raises(SystemExit) as exc_missing_next:
        main._action_items_update_validate(missing_next, 1, 2)
    assert exc_missing_next.value.code == 1

    no_analysis = _FakeValidateLogDb(([_FakeSegment("x")], None), ([_FakeSegment("done")], None))
    with pytest.raises(SystemExit) as exc_no_analysis:
        main._action_items_update_validate(no_analysis, 1, 2)
    assert exc_no_analysis.value.code == 1

    no_items = _FakeValidateLogDb(([_FakeSegment("x")], _FakeAnalysis(action_items=[])), ([_FakeSegment("done")], None))
    with pytest.raises(SystemExit) as exc_no_items:
        main._action_items_update_validate(no_items, 1, 2)
    assert exc_no_items.value.code == 0

    assert len(echoed) == 4
    assert all(err is True for _, err in echoed)


def test_main_action_items_update_persist_and_echo(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    status_path = tmp_path / "action_item_status.json"
    echoed: list[tuple[str, bool]] = []
    debugged: list[object] = []
    closed: list[bool] = []

    class _HappyTranscriptLog:
        def update_action_item_statuses_in_db(self, from_session: int, updates: list[tuple[int, str]]) -> None:
            return None

        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(main, "_action_item_status_path", lambda: status_path)
    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _HappyTranscriptLog)
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    main._action_items_update_persist(7, [(0, "done"), (1, "todo")])
    persisted = json.loads(status_path.read_text(encoding="utf-8"))
    assert persisted == {"7:0": "done", "7:1": "todo"}
    assert closed == [True]

    class _FailingTranscriptLog:
        def update_action_item_statuses_in_db(self, from_session: int, updates: list[tuple[int, str]]) -> None:
            raise RuntimeError(f"db boom {from_session} {updates}")

        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FailingTranscriptLog)
    monkeypatch.setattr(
        main.structlog, "get_logger", lambda: SimpleNamespace(debug=lambda *args, **kwargs: debugged.append((args, kwargs)))
    )

    main._action_items_update_persist(7, [(0, "done"), (1, "todo")])
    assert debugged

    main._action_items_update_echo("json", 7, 8, [(0, "done")], 0.25, save=False)
    payload = json.loads(echoed[0][0])
    assert payload["data"]["from_session"] == 7
    assert payload["data"]["updates"] == [{"id": 0, "status": "done"}]

    echoed.clear()
    main._action_items_update_echo("text", 7, 8, [(0, "done")], 0.25, save=True)
    assert echoed[0] == ("  [0] done", False)
    assert "action_item_status.json" in echoed[1][0]


def test_main_action_items_update_handles_budget_and_llm_errors(monkeypatch) -> None:
    from voiceforge import main
    from voiceforge.core.contracts import BudgetExceeded

    echoed: list[tuple[str, bool]] = []

    class _FakeTranscriptLog:
        def close(self) -> None:
            return None

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeTranscriptLog)
    monkeypatch.setattr(
        main,
        "_action_items_update_validate",
        lambda log_db, from_session, next_session: (None, None, [{"description": "Ship"}], "done"),
    )
    monkeypatch.setattr(
        main,
        "_get_config",
        lambda: SimpleNamespace(
            default_llm="m1",
            pii_mode="OFF",
            get_effective_llm=lambda: ("m1", False),
        ),
    )
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    monkeypatch.setattr(
        "voiceforge.llm.router.update_action_item_statuses",
        lambda *args, **kwargs: (_ for _ in ()).throw(BudgetExceeded("budget cap")),
    )
    with pytest.raises(SystemExit) as exc_budget:
        main.action_items_update(from_session=1, next_session=2, output="json", save=False)
    assert exc_budget.value.code == 1

    monkeypatch.setattr(
        "voiceforge.llm.router.update_action_item_statuses",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("llm exploded")),
    )
    with pytest.raises(SystemExit) as exc_llm:
        main.action_items_update(from_session=1, next_session=2, output="json", save=False)
    assert exc_llm.value.code == 1

    assert len(echoed) == 2
    assert all(err is True for _, err in echoed)


def test_main_export_session_invalid_format_and_otter_success(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))
    monkeypatch.setattr(main.sys.stderr, "isatty", lambda: False)

    with pytest.raises(SystemExit) as exc_invalid:
        main.export_session(session_id=1, format="html", output=tmp_path / "ignored.txt")
    assert exc_invalid.value.code == 1
    assert echoed[-1][1] is True

    class _FakeTranscriptLog:
        def get_session_detail(self, session_id: int):
            assert session_id == 9
            return ([SimpleNamespace(text="hello")], SimpleNamespace(model="m1"))

        def get_session_meta(self, session_id: int):
            assert session_id == 9
            return ("2026-03-08T10:00:00+00:00",)

        def close(self) -> None:
            return None

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeTranscriptLog)
    monkeypatch.setattr(main, "build_session_export_otter", lambda *args, **kwargs: "OTTER EXPORT")

    out_path = tmp_path / "session_9.txt"
    main.export_session(session_id=9, format="otter", output=out_path, clipboard=False)

    assert out_path.read_text(encoding="utf-8") == "OTTER EXPORT"
    assert any(str(out_path) in message for message, _ in echoed)


def test_main_export_via_pandoc_handles_missing_and_failure(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    out_pdf = tmp_path / "session.pdf"
    monkeypatch.setattr(
        main.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("pandoc missing")),
    )
    with pytest.raises(SystemExit) as exc_missing:
        main._export_via_pandoc("pdf", out_pdf, "# Report")
    assert exc_missing.value.code == 1
    fallback_md = out_pdf.with_suffix(".md")
    assert fallback_md.exists()
    assert any("pandoc" in message.lower() for message, _ in echoed)

    echoed.clear()
    monkeypatch.setattr(
        main.subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            subprocess.CalledProcessError(returncode=2, cmd=["pandoc"], stderr=b"pdf failed")
        ),
    )
    with pytest.raises(SystemExit) as exc_failed:
        main._export_via_pandoc("docx", tmp_path / "session.docx", "# Report")
    assert exc_failed.value.code == 1
    assert any("pdf failed" in message for message, _ in echoed)


def test_main_sessions_to_ical_command_writes_calendar(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []

    class _FakeTranscriptLog:
        def close(self) -> None:
            return None

    sessions = [
        SimpleNamespace(id=1, started_at="2026-03-08T10:00:00+00:00", duration_sec=60),
        SimpleNamespace(id=2, started_at="2026-03-08T11:00:00+00:00", duration_sec=120),
    ]

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeTranscriptLog)
    monkeypatch.setattr(main, "_sessions_to_ical_fetch_sessions", lambda log_db, from_date, to_date, limit: sessions)
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    output = tmp_path / "exports" / "sessions.ics"
    main.sessions_to_ical(output=output, limit=5, from_date="2026-03-01", to_date="2026-03-02")

    content = output.read_text(encoding="utf-8")
    assert "BEGIN:VCALENDAR" in content
    assert content.count("BEGIN:VEVENT") == 2
    assert any("Exported 2 sessions" in message for message, _ in echoed)


def test_main_weekly_report_formats_and_stats_fallback(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []

    class _FakeTranscriptLog:
        def get_sessions_in_range(self, from_date, to_date):
            return [SimpleNamespace(id=11), SimpleNamespace(id=12)]

        def get_action_items(self, limit: int):
            return [
                SimpleNamespace(session_id=11, description="Ship feature", status="done"),
                SimpleNamespace(session_id=99, description="Ignore", status="todo"),
            ]

        def close(self) -> None:
            return None

    monkeypatch.setattr("voiceforge.core.transcript_log.TranscriptLog", _FakeTranscriptLog)
    monkeypatch.setattr("voiceforge.core.metrics.get_stats_range", lambda from_date, to_date: {"total_cost_usd": 3.5})
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))

    main.weekly_report(output=None, days=7, format="json")
    payload = json.loads(echoed[-1][0])
    assert payload["sessions_count"] == 2
    assert payload["action_items_count"] == 1
    assert payload["action_items"][0]["description"] == "Ship feature"

    echoed.clear()
    md_output = tmp_path / "weekly.md"
    main.weekly_report(output=md_output, days=7, format="md")
    md_text = md_output.read_text(encoding="utf-8")
    assert "# Отчёт за 7 дн." in md_text
    assert "Ship feature" in md_text
    assert any(str(md_output) in message for message, _ in echoed)

    echoed.clear()
    monkeypatch.setattr(
        "voiceforge.core.metrics.get_stats_range", lambda from_date, to_date: (_ for _ in ()).throw(RuntimeError("stats down"))
    )
    main.weekly_report(output=None, days=3, format="text")
    assert "Cost (LLM): $0.00" in echoed[-1][0]


def test_main_backup_data_dir_and_backup_cmd(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    data_home = tmp_path / "data-home"
    monkeypatch.setenv("XDG_DATA_HOME", str(data_home))
    assert main._backup_data_dir() == data_home / "voiceforge"

    echoed: list[tuple[str, bool]] = []
    copied: list[tuple[str, str]] = []
    rotated: list[str] = []

    data_dir = data_home / "voiceforge"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "transcripts.db").write_text("t", encoding="utf-8")
    (data_dir / "metrics.db").write_text("m", encoding="utf-8")
    rag_db = tmp_path / "rag.db"
    rag_db.write_text("r", encoding="utf-8")
    backups_root = tmp_path / "backups"
    old_backup = backups_root / "voiceforge-backup-20240101-000000"
    older_backup = backups_root / "voiceforge-backup-20230101-000000"
    old_backup.mkdir(parents=True, exist_ok=True)
    older_backup.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(main, "_get_config", lambda: SimpleNamespace(get_rag_db_path=lambda: str(rag_db)))
    monkeypatch.setattr(main.time, "strftime", lambda fmt: "20260308-130000")
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))
    monkeypatch.setattr(main.shutil, "copy2", lambda src, dest: copied.append((str(src), str(dest))))
    monkeypatch.setattr(main.shutil, "rmtree", lambda path, ignore_errors=True: rotated.append(str(path)))
    monkeypatch.setattr(main.log, "info", lambda *args, **kwargs: None)

    main.backup_cmd(output_dir=backups_root, keep=2)

    assert len(copied) == 3
    assert any("voiceforge-backup-20260308-130000" in dest for _, dest in copied)
    assert rotated == [str(older_backup)]
    assert echoed and echoed[0][1] is False


def test_main_backup_cmd_no_files_and_history_resolve_purge(monkeypatch, tmp_path: Path) -> None:
    from voiceforge import main

    echoed: list[tuple[str, bool]] = []
    monkeypatch.setattr("typer.echo", lambda message, err=False: echoed.append((str(message), err)))
    monkeypatch.setattr(main, "_get_config", lambda: SimpleNamespace(get_rag_db_path=lambda: str(tmp_path / "missing-rag.db")))
    monkeypatch.setattr(main.time, "strftime", lambda fmt: "20260308-130100")
    monkeypatch.setattr(main, "_backup_data_dir", lambda: tmp_path / "empty-data")

    with pytest.raises(SystemExit) as exc_no_files:
        main.backup_cmd(output_dir=tmp_path / "backups", keep=0)
    assert exc_no_files.value.code == 1
    assert echoed[-1][1] is True

    class _FakePurgeLogDb:
        def purge_before(self, cutoff):
            assert cutoff.isoformat() == "2026-03-01"
            return 4

    result = main._history_resolve(
        _FakePurgeLogDb(),
        "2026-03-01",
        False,
        None,
        None,
        None,
        None,
        None,
        10,
        "text",
    )
    assert result is None
    assert echoed[-1][1] is False

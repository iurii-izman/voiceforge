from __future__ import annotations

from typer.testing import CliRunner

from voiceforge.main import app

runner = CliRunner()


def test_help_exposes_only_core_commands() -> None:
    expected = {
        "listen",
        "analyze",
        "status",
        "history",
        "index",
        "watch",
        "daemon",
        "install-service",
        "uninstall-service",
    }
    removed = {"dashboard", "analytics", "privacy", "update", "prefetch", "tasks", "summary", "export", "plugin", "speaker"}
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, result.stdout
    for command in sorted(expected):
        assert command in result.stdout
    for command in sorted(removed):
        assert command not in result.stdout


def test_non_core_command_is_unknown() -> None:
    result = runner.invoke(app, ["tasks"])
    assert result.exit_code != 0
    output = f"{result.stdout}\n{result.stderr}"
    assert "No such command" in output

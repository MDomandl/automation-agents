from pathlib import Path

from app.infrastructure.process.subprocess_runner import ProcessResult
from app.tools.process.run_runner_tool import RunRunnerTool, RunRunnerToolInput


class FakeSubprocessRunner:
    def __init__(self, result: ProcessResult):
        self.result = result
        self.last_command = None
        self.last_cwd = None
        self.last_timeout = None

    def run(self, command, *, cwd=None, timeout_seconds=None):
        self.last_command = command
        self.last_cwd = cwd
        self.last_timeout = timeout_seconds
        return self.result


def test_run_runner_tool_delegates_to_subprocess_runner() -> None:
    fake_runner = FakeSubprocessRunner(
        ProcessResult(
            command=("python", "runner.py"),
            returncode=0,
            stdout="ok",
            stderr="",
            cwd="C:/tmp",
            duration_seconds=0.5,
            timed_out=False,
        )
    )

    tool = RunRunnerTool(fake_runner)

    response = tool.execute(
        RunRunnerToolInput(
            command=("python", "runner.py"),
            cwd="C:/tmp",
            timeout_seconds=120,
            config_path=Path("runner.yaml"),
        )
    )

    assert response.success is True
    assert fake_runner.last_command == ("python", "runner.py")
    assert fake_runner.last_cwd == "C:/tmp"
    assert fake_runner.last_timeout == 120


def test_run_runner_tool_appends_as_of_override_to_command() -> None:
    fake_runner = FakeSubprocessRunner(
        ProcessResult(
            command=("python", "runner.py", "--as-of", "2025-03-31"),
            returncode=0,
            stdout="ok",
            stderr="",
            cwd="C:/tmp",
            duration_seconds=0.5,
            timed_out=False,
        )
    )

    tool = RunRunnerTool(fake_runner)

    tool.execute(
        RunRunnerToolInput(
            command=("python", "runner.py"),
            cwd="C:/tmp",
            timeout_seconds=120,
            config_path=Path("runner.yaml"),
            as_of_override="2025-03-31",
        )
    )

    assert fake_runner.last_command == ("python", "runner.py", "--as-of", "2025-03-31")


def test_run_runner_tool_keeps_explicit_command_as_of() -> None:
    fake_runner = FakeSubprocessRunner(
        ProcessResult(
            command=("python", "runner.py", "--as-of", "2025-04-01"),
            returncode=0,
            stdout="ok",
            stderr="",
            cwd="C:/tmp",
            duration_seconds=0.5,
            timed_out=False,
        )
    )

    tool = RunRunnerTool(fake_runner)

    tool.execute(
        RunRunnerToolInput(
            command=("python", "runner.py", "--as-of", "2025-04-01"),
            cwd="C:/tmp",
            timeout_seconds=120,
            config_path=Path("runner.yaml"),
            as_of_override="2025-03-31",
        )
    )

    assert fake_runner.last_command == ("python", "runner.py", "--as-of", "2025-04-01")

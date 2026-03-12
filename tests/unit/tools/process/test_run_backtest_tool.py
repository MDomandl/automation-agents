from app.infrastructure.process.subprocess_runner import ProcessResult
from app.tools.process.run_backtest_tool import (
    RunBacktestTool,
    RunBacktestToolInput,
)


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


def test_run_backtest_tool_delegates_to_subprocess_runner() -> None:
    fake_runner = FakeSubprocessRunner(
        ProcessResult(
            command=("python", "script.py"),
            returncode=0,
            stdout="ok",
            stderr="",
        )
    )

    tool = RunBacktestTool(fake_runner)

    response = tool.execute(
        RunBacktestToolInput(
            command=("python", "script.py"),
            cwd="C:/tmp",
            timeout_seconds=120,
        )
    )

    assert response.success is True
    assert fake_runner.last_command == ("python", "script.py")
    assert fake_runner.last_cwd == "C:/tmp"
    assert fake_runner.last_timeout == 120
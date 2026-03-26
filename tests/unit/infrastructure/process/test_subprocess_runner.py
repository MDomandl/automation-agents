import sys

from app.infrastructure.process.subprocess_runner import SubprocessRunner


def test_subprocess_runner_executes_command_successfully() -> None:
    runner = SubprocessRunner()

    result = runner.run((sys.executable, "-c", "print('hello')"), cwd=".")

    assert result.succeeded is True
    assert result.returncode == 0
    assert "hello" in result.stdout
    assert result.cwd == "."
    assert result.duration_seconds >= 0.0
    assert result.timed_out is False


def test_subprocess_runner_returns_timeout_result() -> None:
    runner = SubprocessRunner()

    result = runner.run(
        (sys.executable, "-c", "import time; print('start'); time.sleep(0.2)"),
        timeout_seconds=0.01,
    )

    assert result.succeeded is False
    assert result.returncode is None
    assert result.timed_out is True
    assert result.duration_seconds >= 0.0

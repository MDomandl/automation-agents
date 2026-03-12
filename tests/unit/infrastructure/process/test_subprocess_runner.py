import sys

from app.infrastructure.process.subprocess_runner import SubprocessRunner


def test_subprocess_runner_executes_command_successfully() -> None:
    runner = SubprocessRunner()

    result = runner.run((sys.executable, "-c", "print('hello')"))

    assert result.succeeded is True
    assert result.returncode == 0
    assert "hello" in result.stdout
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.infrastructure.process.subprocess_runner import ProcessResult, SubprocessRunner


@dataclass(frozen=True, slots=True)
class RunRunnerToolInput:
    command: tuple[str, ...]
    config_path: Path
    cwd: str | Path | None = None
    timeout_seconds: int | None = None
    as_of_override: str | None = None
    execution_as_of_override: str | None = None


@dataclass(frozen=True, slots=True)
class RunRunnerToolResult:
    success: bool
    process_result: ProcessResult


class RunRunnerTool:
    """
    Führt den Runner-Prozess aus.
    """

    def __init__(self, process_runner: SubprocessRunner):
        self._process_runner = process_runner

    def execute(self, tool_input: RunRunnerToolInput) -> RunRunnerToolResult:
        command = self._build_command(tool_input)
        result = self._process_runner.run(
            command,
            cwd=tool_input.cwd,
            timeout_seconds=tool_input.timeout_seconds,
        )

        return RunRunnerToolResult(
            success=result.succeeded,
            process_result=result,
        )

    @staticmethod
    def _build_command(tool_input: RunRunnerToolInput) -> tuple[str, ...]:
        command = tool_input.command
        explicit_signal = runner_option(command, "--as-of")
        if tool_input.as_of_override is not None and explicit_signal is None:
            command += ("--as-of", tool_input.as_of_override)
        if (
            tool_input.execution_as_of_override is not None
            and runner_option(command, "--execution-as-of") is None
            and (explicit_signal is None or explicit_signal == tool_input.as_of_override)
        ):
            command += ("--execution-as-of", tool_input.execution_as_of_override)
        return command


def runner_option(command: tuple[str, ...], option: str) -> str | None:
    for index in range(len(command) - 1, -1, -1):
        arg = command[index]
        if arg == option:
            return command[index + 1] if index + 1 < len(command) else ""
        if arg.startswith(f"{option}="):
            return arg.split("=", 1)[1]
    return None

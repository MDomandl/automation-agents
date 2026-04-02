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
        if tool_input.as_of_override is None or "--as-of" in tool_input.command:
            return tool_input.command

        return tool_input.command + ("--as-of", tool_input.as_of_override)

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.infrastructure.process.subprocess_runner import ProcessResult, SubprocessRunner


@dataclass(frozen=True, slots=True)
class RunBacktestToolInput:
    command: tuple[str, ...]
    cwd: str | Path | None = None
    timeout_seconds: int | None = None


@dataclass(frozen=True, slots=True)
class RunBacktestToolResult:
    success: bool
    process_result: ProcessResult


class RunBacktestTool:
    """
    Führt den Backtest-Prozess aus.
    """

    def __init__(self, process_runner: SubprocessRunner):
        self._process_runner = process_runner

    def execute(self, tool_input: RunBacktestToolInput) -> RunBacktestToolResult:
        result = self._process_runner.run(
            tool_input.command,
            cwd=tool_input.cwd,
            timeout_seconds=tool_input.timeout_seconds,
        )

        return RunBacktestToolResult(
            success=result.succeeded,
            process_result=result,
        )
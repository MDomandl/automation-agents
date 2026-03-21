from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from app.application.bt_run.ports import ProcessRunner
from app.common.result import Result


@dataclass(frozen=True, slots=True)
class RunBacktestToolInput:
    command: tuple[str, ...]
    config_path: Path | None = None
    cwd: str | Path | None = None
    timeout_seconds: int | None = None


class RunBacktestTool:
    def __init__(self, process_runner: ProcessRunner, command: Sequence[str]) -> None:
        self._process_runner = process_runner
        self._command = command

    def execute(self, cwd: str | None = None) -> Result[None]:
        return self._process_runner.run(self._command, cwd=cwd)

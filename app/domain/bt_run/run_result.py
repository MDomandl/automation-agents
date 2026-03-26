from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class StepResult:
    success: bool
    command: tuple[str, ...] = ()
    cwd: str | None = None
    returncode: int | None = None
    duration_seconds: float | None = None
    timed_out: bool = False
    stdout: str = ""
    stderr: str = ""
    message: Optional[str] = None


@dataclass(frozen=True, slots=True)
class CompareResult:
    success: bool
    matched: Optional[bool] = None
    message: Optional[str] = None


@dataclass(frozen=True, slots=True)
class RunResult:
    success: bool
    backtest: StepResult
    runner: StepResult
    compare: CompareResult
    warnings: tuple[str, ...] = ()

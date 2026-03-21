from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class StepResult:
    success: bool
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
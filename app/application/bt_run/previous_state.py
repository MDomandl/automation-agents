from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RunnerPreviousSeedRequest:
    backtest_config_path: Path
    backtest_cwd: str | Path | None
    runner_config_path: Path
    runner_cwd: str | Path | None
    runner_as_of: str
    decisions_dir: Path | None


@dataclass(frozen=True, slots=True)
class RunnerPreviousSeedResult:
    seeded: bool
    message: str
    previous_as_of: str | None = None
    row_count: int = 0


class RunnerPreviousStateSeeder(Protocol):
    def seed(self, request: RunnerPreviousSeedRequest) -> RunnerPreviousSeedResult: ...

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path


class RunProfile(str, Enum):
    SHORT = "short"
    PROBLEM = "problem"
    MEDIUM = "medium"
    LONG = "long"


class CompareMode(str, Enum):
    LATEST = "latest"
    ALL = "all"


class RunnerMode(str, Enum):
    ANALYSIS = "analysis"
    PAPER = "paper"


@dataclass(frozen=True, slots=True)
class RunContext:
    run_id: str
    run_timestamp: datetime
    run_label: str

    profile: RunProfile
    compare_mode: CompareMode

    ai_agents_dir: Path
    aktien_oop_dir: Path
    decisions_dir: Path
    output_dir: Path

    backtest_config_path: Path
    runner_config_path: Path

    runner_mode: RunnerMode = RunnerMode.ANALYSIS
    bps_tolerance: float = 5.0
    ignore_cash: bool = True

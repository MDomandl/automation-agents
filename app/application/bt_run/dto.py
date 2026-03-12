from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.domain.bt_run.models import ComparisonSummary


@dataclass(slots=True)
class CompareLatestRunsRequest:
    """
    Request-Parameter für den Vergleich.
    """
    bps_tolerance: float = 5.0
    ignore_cash: bool = True


@dataclass(slots=True)
class CompareLatestRunsResponse:
    """
    Ergebnis des Use Cases.
    """
    success: bool
    summary: Optional[ComparisonSummary] = None
    message: Optional[str] = None

@dataclass(slots=True)
class CompareAllRunsRequest:
    bps_tolerance: float = 5.0
    ignore_cash: bool = True


@dataclass(slots=True)
class CompareAllRunsResponse:
    success: bool
    summaries: list[ComparisonSummary] = field(default_factory=list)
    message: Optional[str] = None

    @property
    def matched_count(self) -> int:
        return sum(1 for summary in self.summaries if summary.matched)

    @property
    def mismatched_count(self) -> int:
        return sum(1 for summary in self.summaries if not summary.matched)
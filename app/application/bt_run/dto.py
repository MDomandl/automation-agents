from __future__ import annotations

from dataclasses import dataclass
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
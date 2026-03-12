from __future__ import annotations

from dataclasses import dataclass

from app.application.bt_run.dto import CompareLatestRunsRequest, CompareLatestRunsResponse
from app.application.bt_run.use_cases import CompareLatestRunsUseCase


@dataclass(slots=True)
class CompareLatestRunsToolInput:
    bps_tolerance: float = 5.0
    ignore_cash: bool = True


class CompareLatestRunsTool:
    """
    Tool-Adapter für den Use Case CompareLatestRunsUseCase.
    """

    def __init__(self, use_case: CompareLatestRunsUseCase):
        self._use_case = use_case

    def execute(self, tool_input: CompareLatestRunsToolInput) -> CompareLatestRunsResponse:
        request = CompareLatestRunsRequest(
            bps_tolerance=tool_input.bps_tolerance,
            ignore_cash=tool_input.ignore_cash,
        )
        return self._use_case.execute(request)
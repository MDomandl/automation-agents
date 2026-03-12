from __future__ import annotations

from dataclasses import dataclass

from app.application.bt_run.dto import CompareAllRunsRequest, CompareAllRunsResponse
from app.application.bt_run.use_cases import CompareAllRunsUseCase


@dataclass(slots=True)
class CompareAllRunsToolInput:
    bps_tolerance: float = 5.0
    ignore_cash: bool = True


class CompareAllRunsTool:
    """
    Tool-Adapter für den Use Case CompareAllRunsUseCase.

    Aufgabe:
    - Tool-Input entgegennehmen
    - Request DTO bauen
    - Use Case ausführen
    - Response zurückgeben
    """

    def __init__(self, use_case: CompareAllRunsUseCase):
        self._use_case = use_case

    def execute(self, tool_input: CompareAllRunsToolInput) -> CompareAllRunsResponse:
        request = CompareAllRunsRequest(
            bps_tolerance=tool_input.bps_tolerance,
            ignore_cash=tool_input.ignore_cash,
        )
        return self._use_case.execute(request)
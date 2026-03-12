from app.application.bt_run.dto import CompareAllRunsResponse
from app.domain.bt_run.models import ComparisonSummary
from app.tools.compare.compare_all_runs_tool import (
    CompareAllRunsTool,
    CompareAllRunsToolInput,
)


class FakeCompareAllRunsUseCase:
    def __init__(self):
        self.last_request = None

    def execute(self, request):
        self.last_request = request
        return CompareAllRunsResponse(
            success=True,
            summaries=[
                ComparisonSummary(
                    as_of_bt="2025-03-31",
                    as_of_run="2025-03-31",
                    matched=True,
                )
            ],
        )


def test_compare_all_runs_tool_passes_input_to_use_case() -> None:
    use_case = FakeCompareAllRunsUseCase()
    tool = CompareAllRunsTool(use_case)

    response = tool.execute(
        CompareAllRunsToolInput(
            bps_tolerance=7.5,
            ignore_cash=False,
        )
    )

    assert response.success is True
    assert len(response.summaries) == 1
    assert use_case.last_request is not None
    assert use_case.last_request.bps_tolerance == 7.5
    assert use_case.last_request.ignore_cash is False
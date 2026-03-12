from app.application.bt_run.dto import CompareAllRunsRequest
from app.application.bt_run.ports import DecisionBundleStorePort
from app.application.bt_run.use_cases import CompareAllRunsUseCase
from app.domain.bt_run.models import RunArtifact


class FakeStore(DecisionBundleStorePort):
    def get_latest_pair(self):
        return None

    def get_all_pairs(self):
        return [("bt1", "run1"), ("bt2", "run2")]

    def load_artifact(self, artifact_id: str) -> RunArtifact:
        data = {
            "bt1": RunArtifact(
                source="BT",
                as_of="2025-03-31",
                weights={"AAPL": 0.7, "CASH": 0.3},
            ),
            "run1": RunArtifact(
                source="RUN",
                as_of="2025-03-31",
                weights={"AAPL": 0.7, "CASH": 0.3},
            ),
            "bt2": RunArtifact(
                source="BT",
                as_of="2025-04-30",
                weights={"MSFT": 0.6, "CASH": 0.4},
            ),
            "run2": RunArtifact(
                source="RUN",
                as_of="2025-04-30",
                weights={"MSFT": 0.5, "CASH": 0.5},
            ),
        }
        return data[artifact_id]


def test_compare_all_runs_use_case_returns_all_summaries() -> None:
    use_case = CompareAllRunsUseCase(FakeStore())

    response = use_case.execute(
        CompareAllRunsRequest(
            bps_tolerance=5.0,
            ignore_cash=True,
        )
    )

    assert response.success is True
    assert len(response.summaries) == 2
    assert response.matched_count == 1
    assert response.mismatched_count == 1
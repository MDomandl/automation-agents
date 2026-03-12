from app.application.bt_run.dto import CompareLatestRunsRequest
from app.application.bt_run.use_cases import CompareLatestRunsUseCase
from app.application.bt_run.ports import DecisionBundleStorePort
from app.domain.bt_run.models import RunArtifact


class FakeStore(DecisionBundleStorePort):

    def get_latest_pair(self):
        return ("bt1", "run1")

    def load_artifact(self, artifact_id: str):

        if artifact_id == "bt1":
            return RunArtifact(
                source="BT",
                as_of="2025-10-10",
                weights={"AAPL": 0.6, "MSFT": 0.4},
            )

        return RunArtifact(
            source="RUN",
            as_of="2025-10-10",
            weights={"AAPL": 0.6, "MSFT": 0.4},
        )


def test_compare_latest_runs_use_case_matches():

    store = FakeStore()

    use_case = CompareLatestRunsUseCase(store)

    response = use_case.execute(
        CompareLatestRunsRequest()
    )

    assert response.success
    assert response.summary.matched
from __future__ import annotations

from app.application.bt_run.dto import (
    CompareLatestRunsRequest,
    CompareLatestRunsResponse,
)
from app.application.bt_run.ports import DecisionBundleStorePort
from app.domain.bt_run.compare import compare_run_artifacts


class CompareLatestRunsUseCase:
    """
    Orchestriert den Vergleich des neuesten BT/RUN-Paares.
    """

    def __init__(self, bundle_store: DecisionBundleStorePort):
        self._bundle_store = bundle_store

    def execute(self, request: CompareLatestRunsRequest) -> CompareLatestRunsResponse:

        pair = self._bundle_store.get_latest_pair()

        if pair is None:
            return CompareLatestRunsResponse(
                success=False,
                message="No BT/RUN pair found",
            )

        bt_id, run_id = pair

        bt_artifact = self._bundle_store.load_artifact(bt_id)
        run_artifact = self._bundle_store.load_artifact(run_id)

        summary = compare_run_artifacts(
            bt_artifact,
            run_artifact,
            bps_tolerance=request.bps_tolerance,
            ignore_cash=request.ignore_cash,
        )

        return CompareLatestRunsResponse(
            success=True,
            summary=summary,
        )
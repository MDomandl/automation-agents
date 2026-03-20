from __future__ import annotations

from app.application.bt_run.dto import (
    CompareAllRunsRequest,
    CompareAllRunsResponse,
    CompareLatestRunsRequest,
    CompareLatestRunsResponse,
)
from app.application.bt_run.ports import DecisionBundleStorePort
from app.domain.bt_run.compare import compare_run_artifacts
from app.domain.bt_run.config_compare import compare_configs, ConfigCompareResult


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

class CompareAllRunsUseCase:
    def __init__(self, bundle_store: DecisionBundleStorePort):
        self._bundle_store = bundle_store

    def execute(self, request: CompareAllRunsRequest) -> CompareAllRunsResponse:
        pairs = self._bundle_store.get_all_pairs()

        if not pairs:
            return CompareAllRunsResponse(
                success=False,
                message="No BT/RUN pairs found",
            )

        summaries = []

        for bt_id, run_id in pairs:
            bt_artifact = self._bundle_store.load_artifact(bt_id)
            run_artifact = self._bundle_store.load_artifact(run_id)

            summary = compare_run_artifacts(
                bt_artifact,
                run_artifact,
                bps_tolerance=request.bps_tolerance,
                ignore_cash=request.ignore_cash,
            )
            summaries.append(summary)

        return CompareAllRunsResponse(
            success=True,
            summaries=summaries,
        )
class CompareConfigUseCase:

    def __init__(self, loader):
        self._loader = loader

    def execute(self, bt_path, run_path) -> ConfigCompareResult:
        bt_config = self._loader.load(bt_path)
        run_config = self._loader.load(run_path)

        return compare_configs(bt_config, run_config)
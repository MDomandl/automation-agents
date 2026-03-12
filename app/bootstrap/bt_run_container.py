from pathlib import Path

from app.application.bt_run.use_cases import CompareAllRunsUseCase
from app.infrastructure.storage.decision_bundle_store import FileDecisionBundleStore
from app.tools.compare.compare_all_runs_tool import CompareAllRunsTool


def build_compare_all_runs_tool(decisions_dir: str | Path) -> CompareAllRunsTool:

    store = FileDecisionBundleStore(decisions_dir)

    use_case = CompareAllRunsUseCase(store)

    tool = CompareAllRunsTool(use_case)

    return tool
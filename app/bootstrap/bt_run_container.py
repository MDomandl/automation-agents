from __future__ import annotations

from pathlib import Path

from app.agents.bt_run_agent import BtRunAgent
from app.application.bt_run.use_cases import (
    CompareAllRunsUseCase,
    CompareConfigUseCase,
    CompareLatestRunsUseCase,
)
from app.infrastructure.process.subprocess_runner import SubprocessRunner
from app.infrastructure.storage.config_loader import ConfigLoader
from app.infrastructure.storage.decision_bundle_store import FileDecisionBundleStore
from app.infrastructure.storage.portfolio_store_previous_state_seeder import (
    PortfolioStorePreviousStateSeeder,
)
from app.tools.compare.compare_all_runs_tool import CompareAllRunsTool
from app.tools.compare.compare_config_tool import CompareConfigTool
from app.tools.compare.compare_latest_runs_tool import CompareLatestRunsTool
from app.tools.process.run_backtest_tool import RunBacktestTool
from app.tools.process.run_runner_tool import RunRunnerTool


def build_bt_run_agent(decisions_dir: str | Path) -> BtRunAgent:
    process_runner = SubprocessRunner()

    store = FileDecisionBundleStore(decisions_dir)
    compare_use_case = CompareLatestRunsUseCase(store)
    compare_all_use_case = CompareAllRunsUseCase(store)

    config_loader = ConfigLoader()
    compare_config_use_case = CompareConfigUseCase(config_loader)
    compare_config_tool = CompareConfigTool(compare_config_use_case)

    run_backtest_tool = RunBacktestTool(process_runner)
    run_runner_tool = RunRunnerTool(process_runner)
    compare_latest_runs_tool = CompareLatestRunsTool(compare_use_case)
    compare_all_runs_tool = CompareAllRunsTool(compare_all_use_case)

    return BtRunAgent(
        run_backtest_tool=run_backtest_tool,
        run_runner_tool=run_runner_tool,
        compare_latest_runs_tool=compare_latest_runs_tool,
        compare_all_runs_tool=compare_all_runs_tool,
        compare_config_tool=compare_config_tool,
        decisions_dir=decisions_dir,
        runner_previous_state_seeder=PortfolioStorePreviousStateSeeder(),
    )

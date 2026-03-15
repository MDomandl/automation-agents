from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.tools.compare.compare_all_runs_tool import CompareAllRunsToolInput, CompareAllRunsTool
from app.tools.compare.compare_latest_runs_tool import (
    CompareLatestRunsTool,
    CompareLatestRunsToolInput,
)
from app.tools.process.run_backtest_tool import (
    RunBacktestTool,
    RunBacktestToolInput,
)
from app.tools.process.run_runner_tool import (
    RunRunnerTool,
    RunRunnerToolInput,
)

RunMode = Literal["latest", "all"]

@dataclass(frozen=True, slots=True)
class BtRunAgentInput:
    backtest_input: RunBacktestToolInput
    runner_input: RunRunnerToolInput
    compare_input: CompareLatestRunsToolInput
    compare_mode: RunMode = "latest"


@dataclass(frozen=True, slots=True)
class BtRunAgentResult:
    success: bool
    backtest_success: bool
    runner_success: bool
    compare_success: bool
    backtest_stdout: str
    backtest_stderr: str
    runner_stdout: str
    runner_stderr: str
    compare_message: str | None = None
    compare_matched: bool | None = None


class BtRunAgent:
    """
    Orchestriert einen vollständigen BT/RUN-Durchlauf:
    1. Backtest starten
    2. Runner starten
    3. Latest-Runs vergleichen
    """

    def __init__(
        self,
            run_backtest_tool: RunBacktestTool,
            run_runner_tool: RunRunnerTool,
            compare_latest_runs_tool: CompareLatestRunsTool,
            compare_all_runs_tool: CompareAllRunsTool,
    ):
        self._run_backtest_tool = run_backtest_tool
        self._run_runner_tool = run_runner_tool
        self._compare_latest_runs_tool = compare_latest_runs_tool
        self._compare_all_runs_tool = compare_all_runs_tool

    def execute(self, agent_input: BtRunAgentInput) -> BtRunAgentResult:
        backtest_result = self._run_backtest_tool.execute(agent_input.backtest_input)

        if not backtest_result.success:
            return BtRunAgentResult(
                success=False,
                backtest_success=False,
                runner_success=False,
                compare_success=False,
                backtest_stdout=backtest_result.process_result.stdout,
                backtest_stderr=backtest_result.process_result.stderr,
                runner_stdout="",
                runner_stderr="",
                compare_message="Backtest failed",
                compare_matched=None,
            )

        runner_result = self._run_runner_tool.execute(agent_input.runner_input)

        if not runner_result.success:
            return BtRunAgentResult(
                success=False,
                backtest_success=True,
                runner_success=False,
                compare_success=False,
                backtest_stdout=backtest_result.process_result.stdout,
                backtest_stderr=backtest_result.process_result.stderr,
                runner_stdout=runner_result.process_result.stdout,
                runner_stderr=runner_result.process_result.stderr,
                compare_message="Runner failed",
                compare_matched=None,
            )

        if agent_input.compare_mode == "latest":
            compare_result = self._compare_latest_runs_tool.execute(
                agent_input.compare_input
            )

            compare_success = compare_result.success
            compare_matched = (
                compare_result.summary.matched if compare_result.summary else None
            )
            compare_message = compare_result.message

        else:
            compare_result = self._compare_all_runs_tool.execute(
                CompareAllRunsToolInput(
                    bps_tolerance=agent_input.compare_input.bps_tolerance,
                    ignore_cash=agent_input.compare_input.ignore_cash,
                )
            )

            compare_success = compare_result.success
            compare_matched = compare_result.mismatched_count == 0
            compare_message = (
                f"{compare_result.matched_count} matched, "
                f"{compare_result.mismatched_count} mismatched"
            )

        return BtRunAgentResult(
            success=compare_success,
            backtest_success=True,
            runner_success=True,
            compare_success=compare_success,
            backtest_stdout=backtest_result.process_result.stdout,
            backtest_stderr=backtest_result.process_result.stderr,
            runner_stdout=runner_result.process_result.stdout,
            runner_stderr=runner_result.process_result.stderr,
            compare_message=compare_message,
            compare_matched=compare_matched,
        )

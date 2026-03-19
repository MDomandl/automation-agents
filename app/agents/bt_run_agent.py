from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domain.bt_run.run_result import RunResult, StepResult, CompareResult
from app.domain.bt_run.run_context import CompareMode
from app.tools.compare.compare_all_runs_tool import CompareAllRunsToolInput, CompareAllRunsTool
from app.tools.compare.compare_latest_runs_tool import (
    CompareLatestRunsTool,
    CompareLatestRunsToolInput,
)
from app.tools.process.run_backtest_tool import (
    RunBacktestTool,
    RunBacktestToolInput,
)
from app.tools.process.run_runner_tool import RunRunnerTool, RunRunnerToolInput

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

    def execute(self, agent_input: BtRunAgentInput) -> RunResult:
        backtest_result = self._run_backtest_tool.execute(agent_input.backtest_input)

        if not backtest_result.success:
            return RunResult(
                success=False,
                backtest=StepResult(
                    success=False,
                    stdout=backtest_result.process_result.stdout,
                    stderr=backtest_result.process_result.stderr,
                    message="Backtest failed",
                ),
                runner=StepResult(
                    success=False,
                    message="Runner not executed",
                ),
                compare=CompareResult(
                    success=False,
                    matched=None,
                    message="Compare not executed because backtest failed",
                ),
            )

        runner_result = self._run_runner_tool.execute(agent_input.runner_input)

        if not runner_result.success:
            return RunResult(
                success=False,
                backtest=StepResult(
                    success=True,
                    stdout=backtest_result.process_result.stdout,
                    stderr=backtest_result.process_result.stderr,
                ),
                runner=StepResult(
                    success=False,
                    stdout=runner_result.process_result.stdout,
                    stderr=runner_result.process_result.stderr,
                    message="Runner failed",
                ),
                compare=CompareResult(
                    success=False,
                    matched=None,
                    message="Compare not executed because runner failed",
                ),
            )

        if agent_input.compare_mode == CompareMode.LATEST:
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

        return RunResult(
            success=compare_success,
            backtest=StepResult(
                success=True,
                stdout=backtest_result.process_result.stdout,
                stderr=backtest_result.process_result.stderr,
            ),
            runner=StepResult(
                success=True,
                stdout=runner_result.process_result.stdout,
                stderr=runner_result.process_result.stderr,
            ),
            compare=CompareResult(
                success=compare_success,
                matched=compare_matched,
                message=compare_message,
            ),
        )

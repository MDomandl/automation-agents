from __future__ import annotations

from dataclasses import dataclass

from app.domain.bt_run.run_result import RunResult, StepResult, CompareResult
from app.domain.bt_run.run_context import CompareMode
from app.tools.compare.compare_all_runs_tool import CompareAllRunsToolInput, CompareAllRunsTool
from app.tools.compare.compare_config_tool import CompareConfigTool, CompareConfigToolInput
from app.tools.compare.compare_latest_runs_tool import (
    CompareLatestRunsTool,
    CompareLatestRunsToolInput,
)
from app.tools.process.run_backtest_tool import (
    RunBacktestTool,
    RunBacktestToolInput,
)
from app.tools.process.run_runner_tool import RunRunnerTool, RunRunnerToolInput

@dataclass(frozen=True, slots=True)
class BtRunCompareInput:
    bps_tolerance: float = 5.0
    ignore_cash: bool = True


@dataclass(frozen=True, slots=True)
class BtRunAgentInput:
    backtest_input: RunBacktestToolInput
    runner_input: RunRunnerToolInput
    compare_input: BtRunCompareInput
    compare_mode: CompareMode = CompareMode.LATEST


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
        compare_config_tool: CompareConfigTool,
    ):
        self._run_backtest_tool = run_backtest_tool
        self._run_runner_tool = run_runner_tool
        self._compare_latest_runs_tool = compare_latest_runs_tool
        self._compare_all_runs_tool = compare_all_runs_tool
        self._compare_config_tool = compare_config_tool

    def execute(self, agent_input: BtRunAgentInput) -> RunResult:
        warnings: list[str] = []
        config_result = None

        def step_result(process_result, *, success: bool, message: str | None = None) -> StepResult:
            return StepResult(
                success=success,
                stdout=process_result.stdout,
                stderr=process_result.stderr,
                message=message,
            )

        def failed_run_result(
            *,
            backtest: StepResult,
            runner: StepResult,
            compare_message: str,
        ) -> RunResult:
            return RunResult(
                success=False,
                backtest=backtest,
                runner=runner,
                compare=CompareResult(
                    success=False,
                    matched=None,
                    message=compare_message,
                ),
                warnings=tuple(warnings),
            )

        def latest_compare_input() -> CompareLatestRunsToolInput:
            return CompareLatestRunsToolInput(
                bps_tolerance=agent_input.compare_input.bps_tolerance,
                ignore_cash=agent_input.compare_input.ignore_cash,
            )

        def all_compare_input() -> CompareAllRunsToolInput:
            return CompareAllRunsToolInput(
                bps_tolerance=agent_input.compare_input.bps_tolerance,
                ignore_cash=agent_input.compare_input.ignore_cash,
            )

        def compare_result(
            *,
            success: bool,
            matched: bool | None,
            message: str | None,
        ) -> CompareResult:
            return CompareResult(
                success=success,
                matched=matched,
                message=message,
            )

        if (
                agent_input.backtest_input.config_path is not None
                and agent_input.runner_input.config_path is not None
        ):
            config_result = self._compare_config_tool.execute(
                CompareConfigToolInput(
                    bt_config_path=agent_input.backtest_input.config_path,
                    runner_config_path=agent_input.runner_input.config_path,
                )
            )

            if not config_result.matched and config_result.has_critical_differences:
                warnings.append(f"[WARN] Config drift detected: {config_result.message}")
                warnings.extend(config_result.formatted_differences)

        backtest_result = self._run_backtest_tool.execute(agent_input.backtest_input)

        if not backtest_result.success:
            return failed_run_result(
                backtest=step_result(
                    backtest_result.process_result,
                    success=False,
                    message="Backtest failed",
                ),
                runner=StepResult(
                    success=False,
                    message="Runner not executed",
                ),
                compare_message="Compare not executed because backtest failed",
            )

        runner_result = self._run_runner_tool.execute(agent_input.runner_input)

        if not runner_result.success:
            return failed_run_result(
                backtest=step_result(backtest_result.process_result, success=True),
                runner=step_result(
                    runner_result.process_result,
                    success=False,
                    message="Runner failed",
                ),
                compare_message="Compare not executed because runner failed",
            )

        if config_result is not None and not config_result.matched:
            print(f"[WARN] Config drift: {config_result.message}")

        if agent_input.compare_mode == CompareMode.LATEST:
            compare_response = self._compare_latest_runs_tool.execute(latest_compare_input())

            compare_success = compare_response.success
            compare_matched = (
                compare_response.summary.matched if compare_response.summary else None
            )
            compare_message = compare_response.message

        else:
            compare_response = self._compare_all_runs_tool.execute(all_compare_input())

            compare_success = compare_response.success
            compare_matched = compare_response.mismatched_count == 0
            compare_message = (
                f"{compare_response.matched_count} matched, "
                f"{compare_response.mismatched_count} mismatched"
            )

        return RunResult(
            success=compare_success,
            backtest=step_result(backtest_result.process_result, success=True),
            runner=step_result(runner_result.process_result, success=True),
            compare=compare_result(
                success=compare_success,
                matched=compare_matched,
                message=compare_message,
            ),
            warnings=tuple(warnings),
        )

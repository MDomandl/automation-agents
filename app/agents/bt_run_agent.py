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
                warnings=tuple(warnings),
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
                warnings=tuple(warnings),
            )

        if config_result is not None and not config_result.matched:
            print(f"[WARN] Config drift: {config_result.message}")

        if agent_input.compare_mode == CompareMode.LATEST:
            compare_result = self._compare_latest_runs_tool.execute(
                CompareLatestRunsToolInput(
                    bps_tolerance=agent_input.compare_input.bps_tolerance,
                    ignore_cash=agent_input.compare_input.ignore_cash,
                )
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
            warnings=tuple(warnings),
        )

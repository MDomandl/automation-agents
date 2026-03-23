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
        config_result, warnings = self._collect_config_warnings(agent_input)

        backtest_result = self._run_backtest_tool.execute(agent_input.backtest_input)

        if not backtest_result.success:
            return self._failed_run_result(
                backtest=self._step_result(
                    backtest_result.process_result,
                    success=False,
                    message="Backtest failed",
                ),
                runner=StepResult(
                    success=False,
                    message="Runner not executed",
                ),
                compare_message="Compare not executed because backtest failed",
                warnings=warnings,
            )

        runner_result = self._run_runner_tool.execute(agent_input.runner_input)

        if not runner_result.success:
            return self._failed_run_result(
                backtest=self._step_result(backtest_result.process_result, success=True),
                runner=self._step_result(
                    runner_result.process_result,
                    success=False,
                    message="Runner failed",
                ),
                compare_message="Compare not executed because runner failed",
                warnings=warnings,
            )

        if config_result is not None and not config_result.matched:
            self._emit_config_warning(config_result.message)

        compare_result = self._execute_compare(agent_input)

        return RunResult(
            success=compare_result.success,
            backtest=self._step_result(backtest_result.process_result, success=True),
            runner=self._step_result(runner_result.process_result, success=True),
            compare=compare_result,
            warnings=warnings,
        )

    def _collect_config_warnings(
        self,
        agent_input: BtRunAgentInput,
    ) -> tuple[object | None, tuple[str, ...]]:
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

        return config_result, tuple(warnings)

    def _execute_compare(self, agent_input: BtRunAgentInput) -> CompareResult:
        if agent_input.compare_mode == CompareMode.LATEST:
            response = self._compare_latest_runs_tool.execute(
                CompareLatestRunsToolInput(
                    bps_tolerance=agent_input.compare_input.bps_tolerance,
                    ignore_cash=agent_input.compare_input.ignore_cash,
                )
            )
            return CompareResult(
                success=response.success,
                matched=response.summary.matched if response.summary else None,
                message=response.message,
            )

        response = self._compare_all_runs_tool.execute(
            CompareAllRunsToolInput(
                bps_tolerance=agent_input.compare_input.bps_tolerance,
                ignore_cash=agent_input.compare_input.ignore_cash,
            )
        )
        return CompareResult(
            success=response.success,
            matched=response.mismatched_count == 0,
            message=f"{response.matched_count} matched, {response.mismatched_count} mismatched",
        )

    @staticmethod
    def _step_result(process_result, *, success: bool, message: str | None = None) -> StepResult:
        return StepResult(
            success=success,
            stdout=process_result.stdout,
            stderr=process_result.stderr,
            message=message,
        )

    @staticmethod
    def _failed_run_result(
        *,
        backtest: StepResult,
        runner: StepResult,
        compare_message: str,
        warnings: tuple[str, ...],
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
            warnings=warnings,
        )

    @staticmethod
    def _emit_config_warning(message: str) -> None:
        print(f"[WARN] Config drift: {message}")

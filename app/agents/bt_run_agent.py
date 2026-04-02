from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import tomllib

from app.domain.bt_run.config_compare import ConfigDifference, ConfigDiffSeverity
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


@dataclass(frozen=True, slots=True)
class AsOfResolution:
    backtest_as_of: str | None
    runner_as_of: str | None
    runner_as_of_override: str | None

    @property
    def runner_auto_aligned(self) -> bool:
        return self.runner_as_of_override is not None


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
        as_of_resolution = self._resolve_effective_as_of(agent_input)
        config_result, warnings = self._collect_config_warnings(agent_input, as_of_resolution)

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

        runner_result = self._run_runner_tool.execute(
            replace(
                agent_input.runner_input,
                as_of_override=as_of_resolution.runner_as_of_override,
            )
        )

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
        as_of_resolution: AsOfResolution,
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

            differences = self._filter_reported_config_differences(
                config_result.differences,
                as_of_resolution,
            )

            if any(diff.severity == ConfigDiffSeverity.CRITICAL for diff in differences):
                warnings.append(
                    f"[WARN] Config drift detected: {self._build_config_drift_message(differences)}"
                )
                warnings.extend(self._format_config_difference(diff) for diff in differences)

        if as_of_resolution.runner_auto_aligned:
            warnings.append(
                f"[INFO] Runner as_of auto-aligned to backtest as_of: "
                f"{as_of_resolution.runner_as_of_override}"
            )

        return config_result, tuple(warnings)

    def _resolve_effective_as_of(self, agent_input: BtRunAgentInput) -> AsOfResolution:
        backtest_as_of = self._load_config_as_of(agent_input.backtest_input.config_path)
        runner_as_of = self._load_config_as_of(agent_input.runner_input.config_path)
        runner_as_of_override = None

        if runner_as_of is None and backtest_as_of is not None:
            runner_as_of_override = backtest_as_of

        return AsOfResolution(
            backtest_as_of=backtest_as_of,
            runner_as_of=runner_as_of,
            runner_as_of_override=runner_as_of_override,
        )

    @staticmethod
    def _load_config_as_of(config_path: Path | None) -> str | None:
        if config_path is None or not config_path.exists():
            return None

        with config_path.open("rb") as file_obj:
            payload = tomllib.load(file_obj)

        as_of = payload.get("as_of")
        if not isinstance(as_of, str):
            return None

        normalized = as_of.strip()
        return normalized or None

    @staticmethod
    def _filter_reported_config_differences(
        differences: tuple[ConfigDifference, ...],
        as_of_resolution: AsOfResolution,
    ) -> tuple[ConfigDifference, ...]:
        if not as_of_resolution.runner_auto_aligned:
            return differences

        return tuple(
            diff
            for diff in differences
            if not (
                diff.key == "as_of"
                and diff.bt_value == as_of_resolution.backtest_as_of
                and diff.run_value is None
            )
        )

    @staticmethod
    def _build_config_drift_message(differences: tuple[ConfigDifference, ...]) -> str:
        critical_count = sum(1 for diff in differences if diff.severity == ConfigDiffSeverity.CRITICAL)
        warning_count = sum(1 for diff in differences if diff.severity == ConfigDiffSeverity.WARNING)
        info_count = sum(1 for diff in differences if diff.severity == ConfigDiffSeverity.INFO)
        return (
            f"{len(differences)} differences found "
            f"({critical_count} critical, {warning_count} warning, {info_count} info)"
        )

    @staticmethod
    def _format_config_difference(diff: ConfigDifference) -> str:
        return (
            f"- [{diff.severity.value.upper()}] {diff.key}: "
            f"BT={diff.bt_value!r} | RUN={diff.run_value!r}"
        )

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
            command=process_result.command,
            cwd=process_result.cwd,
            returncode=process_result.returncode,
            duration_seconds=process_result.duration_seconds,
            timed_out=process_result.timed_out,
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

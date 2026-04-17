from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import csv
import hashlib
import json
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
    seed_runner_previous_from_backtest: bool = False
    compare_point_count: int = 1


@dataclass(frozen=True, slots=True)
class AsOfResolution:
    backtest_as_of: str | None
    runner_as_of: str | None
    runner_as_of_override: str | None

    @property
    def runner_auto_aligned(self) -> bool:
        return self.runner_as_of_override is not None

    @property
    def effective_runner_as_of(self) -> str | None:
        return self.runner_as_of_override or self.runner_as_of or self.backtest_as_of


@dataclass(frozen=True, slots=True)
class RunnerPreviousSeedResult:
    seeded: bool
    message: str
    previous_as_of: str | None = None
    row_count: int = 0


@dataclass(frozen=True, slots=True)
class UniverseFingerprint:
    count: int
    digest: str


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
        decisions_dir: str | Path | None = None,
    ):
        self._run_backtest_tool = run_backtest_tool
        self._run_runner_tool = run_runner_tool
        self._compare_latest_runs_tool = compare_latest_runs_tool
        self._compare_all_runs_tool = compare_all_runs_tool
        self._compare_config_tool = compare_config_tool
        self._decisions_dir = Path(decisions_dir) if decisions_dir is not None else None

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

        runner_as_of_points = self._resolve_runner_as_of_points(agent_input, as_of_resolution)
        if not runner_as_of_points:
            return self._failed_run_result(
                backtest=self._step_result(backtest_result.process_result, success=True),
                runner=StepResult(success=False, message="Runner not executed"),
                compare_message="Compare not executed because no runner as_of could be resolved",
                warnings=warnings,
            )

        warnings = warnings + (
            f"[INFO] Runner compare points: count={len(runner_as_of_points)}, "
            f"as_of={','.join(point or 'config' for point in runner_as_of_points)}",
        )

        runner_process_results = []
        for index, runner_as_of in enumerate(runner_as_of_points):
            point_resolution = replace(as_of_resolution, runner_as_of_override=runner_as_of)
            should_seed = agent_input.seed_runner_previous_from_backtest and index == 0
            if should_seed:
                seed_result = self._seed_runner_previous_from_backtest(agent_input, point_resolution)
                warnings = warnings + (seed_result.message,)
            elif agent_input.seed_runner_previous_from_backtest and len(runner_as_of_points) > 1 and index == 1:
                warnings = warnings + (
                    "[INFO] Runner previous-state seed skipped for subsequent compare points",
                )

            runner_result = self._run_runner_tool.execute(
                replace(
                    agent_input.runner_input,
                    as_of_override=runner_as_of,
                )
            )
            runner_process_results.append(runner_result.process_result)

            if not runner_result.success:
                return self._failed_run_result(
                    backtest=self._step_result(backtest_result.process_result, success=True),
                    runner=self._step_result(
                        runner_result.process_result,
                        success=False,
                        message=f"Runner failed for as_of={runner_as_of or 'config'}",
                    ),
                    compare_message="Compare not executed because runner failed",
                    warnings=warnings,
                )

        compare_result = self._execute_compare(agent_input)
        runner_step = self._combined_runner_step_result(runner_process_results)

        return RunResult(
            success=compare_result.success,
            backtest=self._step_result(backtest_result.process_result, success=True),
            runner=runner_step,
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
            universe_message = self._compare_configured_universes(agent_input)
            if universe_message is not None:
                warnings.append(universe_message)

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

    def _resolve_runner_as_of_points(
        self,
        agent_input: BtRunAgentInput,
        as_of_resolution: AsOfResolution,
    ) -> tuple[str | None, ...]:
        count = max(int(agent_input.compare_point_count or 1), 1)
        bt_as_ofs = self._load_bt_as_ofs_from_current_run()

        if bt_as_ofs:
            return tuple(bt_as_ofs[-count:])

        if as_of_resolution.runner_as_of_override is not None:
            return (as_of_resolution.runner_as_of_override,)
        if as_of_resolution.runner_as_of is not None:
            return (None,)
        if as_of_resolution.backtest_as_of is not None:
            return (as_of_resolution.backtest_as_of,)
        return (None,)

    def _load_bt_as_ofs_from_current_run(self) -> list[str]:
        if self._decisions_dir is None or not self._decisions_dir.exists():
            return []

        as_ofs: set[str] = set()
        for path in self._decisions_dir.glob("BT_*.json"):
            try:
                with path.open("r", encoding="utf-8") as file_obj:
                    payload = json.load(file_obj)
            except (OSError, json.JSONDecodeError):
                continue

            as_of = payload.get("as_of")
            if isinstance(as_of, str) and as_of.strip():
                as_ofs.add(as_of.strip())

        return sorted(as_ofs)

    @classmethod
    def _compare_configured_universes(cls, agent_input: BtRunAgentInput) -> str | None:
        if (
            not agent_input.backtest_input.config_path.exists()
            or not agent_input.runner_input.config_path.exists()
        ):
            return None

        try:
            bt_config = cls._load_toml(agent_input.backtest_input.config_path)
            runner_config = cls._load_toml(agent_input.runner_input.config_path)
            if "tickers_file" not in bt_config or "tickers_file" not in runner_config:
                return None

            bt_universe = cls._load_universe_fingerprint(agent_input.backtest_input)
            runner_universe = cls._load_universe_fingerprint(agent_input.runner_input)
        except Exception as exc:
            return f"[WARN] Universe check failed: {exc}"

        if bt_universe == runner_universe:
            return (
                "[INFO] Universe match: "
                f"count={bt_universe.count}, hash={bt_universe.digest}"
            )

        return (
            "[WARN] Universe drift detected: "
            f"BT count={bt_universe.count}, hash={bt_universe.digest}; "
            f"RUN count={runner_universe.count}, hash={runner_universe.digest}"
        )

    @classmethod
    def _load_universe_fingerprint(
        cls,
        tool_input: RunBacktestToolInput | RunRunnerToolInput,
    ) -> UniverseFingerprint:
        config = cls._load_toml(tool_input.config_path)
        tickers_path = cls._resolve_path(
            config.get("tickers_file", "aktien_oop/sp500_tickers.txt"),
            base_cwd=tool_input.cwd,
            config_path=tool_input.config_path,
        )
        tickers = cls._read_tickers(tickers_path)
        digest = hashlib.sha1(",".join(sorted(tickers)).encode("utf-8")).hexdigest()
        return UniverseFingerprint(count=len(tickers), digest=digest)

    @staticmethod
    def _read_tickers(path: Path) -> list[str]:
        tickers: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            ticker = line.strip()
            if ticker and not ticker.startswith("#"):
                tickers.append(ticker)
        return tickers

    def _seed_runner_previous_from_backtest(
        self,
        agent_input: BtRunAgentInput,
        as_of_resolution: AsOfResolution,
    ) -> RunnerPreviousSeedResult:
        runner_as_of = as_of_resolution.effective_runner_as_of
        if runner_as_of is None:
            return RunnerPreviousSeedResult(
                seeded=False,
                message="[INFO] Runner previous-state seed skipped: no effective runner as_of",
            )

        try:
            bt_positions_path = self._infer_backtest_positions_path(agent_input.backtest_input)
            runner_positions_path = self._infer_runner_positions_path(agent_input.runner_input)
            seed_result = self._seed_runner_positions_from_backtest_positions(
                bt_positions_path=bt_positions_path,
                runner_positions_path=runner_positions_path,
                runner_as_of=runner_as_of,
            )
        except Exception as exc:
            return RunnerPreviousSeedResult(
                seeded=False,
                message=f"[WARN] Runner previous-state seed failed: {exc}",
            )

        return seed_result

    @classmethod
    def _infer_backtest_positions_path(cls, tool_input: RunBacktestToolInput) -> Path:
        config = cls._load_toml(tool_input.config_path)
        save_dir = cls._resolve_path(
            config.get("save_dir", "aktien_oop"),
            base_cwd=tool_input.cwd,
            config_path=tool_input.config_path,
        )
        frequency = str(config.get("rebalance", {}).get("frequency", config.get("frequency", "monthly")))
        top_k = int(config.get("topk", {}).get("top_k", config.get("top_k")))
        buffer_k = int(config.get("topk", {}).get("buffer_k", config.get("buffer_k")))
        return save_dir / f"bt_{frequency}_{top_k}x{buffer_k}_positions.csv"

    @classmethod
    def _infer_runner_positions_path(cls, tool_input: RunRunnerToolInput) -> Path:
        config = cls._load_toml(tool_input.config_path)
        save_dir = cls._resolve_path(
            config.get("save_dir", "aktien_oop"),
            base_cwd=tool_input.cwd,
            config_path=tool_input.config_path,
        )
        return save_dir / "portfolio_positions.csv"

    @staticmethod
    def _load_toml(config_path: Path) -> dict:
        with config_path.open("rb") as file_obj:
            return tomllib.load(file_obj)

    @staticmethod
    def _resolve_path(value: object, *, base_cwd: str | Path | None, config_path: Path) -> Path:
        path = Path(str(value))
        if path.is_absolute():
            return path
        if base_cwd is not None:
            return Path(base_cwd) / path
        return config_path.parent / path

    @classmethod
    def _seed_runner_positions_from_backtest_positions(
        cls,
        *,
        bt_positions_path: Path,
        runner_positions_path: Path,
        runner_as_of: str,
    ) -> RunnerPreviousSeedResult:
        if not bt_positions_path.exists():
            return RunnerPreviousSeedResult(
                seeded=False,
                message=f"[INFO] Runner previous-state seed skipped: BT positions not found: {bt_positions_path}",
            )

        bt_rows = cls._read_csv_rows(bt_positions_path)
        if not bt_rows:
            return RunnerPreviousSeedResult(
                seeded=False,
                message=f"[INFO] Runner previous-state seed skipped: BT positions empty: {bt_positions_path}",
            )

        previous_rows = cls._latest_rows_before(bt_rows, runner_as_of)
        if not previous_rows:
            return RunnerPreviousSeedResult(
                seeded=False,
                message=f"[INFO] Runner previous-state seed skipped: no BT snapshot before {runner_as_of}",
            )

        previous_as_of = previous_rows[0]["as_of"]
        existing_rows = cls._read_csv_rows(runner_positions_path) if runner_positions_path.exists() else []
        combined_rows = cls._dedupe_position_rows(existing_rows + previous_rows)
        fieldnames = cls._merged_fieldnames(existing_rows + previous_rows)

        runner_positions_path.parent.mkdir(parents=True, exist_ok=True)
        cls._write_csv_rows(runner_positions_path, combined_rows, fieldnames)

        return RunnerPreviousSeedResult(
            seeded=True,
            previous_as_of=previous_as_of,
            row_count=len(previous_rows),
            message=(
                "[INFO] Runner previous-state seeded from backtest positions: "
                f"prev_as_of={previous_as_of}, rows={len(previous_rows)}"
            ),
        )

    @staticmethod
    def _read_csv_rows(path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as file_obj:
            lines = (line for line in file_obj if line.strip() and not line.lstrip().startswith("#"))
            return list(csv.DictReader(lines))

    @classmethod
    def _latest_rows_before(cls, rows: list[dict[str, str]], as_of: str) -> list[dict[str, str]]:
        candidates = [
            row
            for row in rows
            if row.get("as_of") and row.get("ticker") and row["as_of"] < as_of
        ]
        if not candidates:
            return []

        previous_as_of = max(row["as_of"] for row in candidates)
        return sorted(
            (dict(row) for row in candidates if row["as_of"] == previous_as_of),
            key=lambda row: row["ticker"],
        )

    @staticmethod
    def _dedupe_position_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        by_key: dict[tuple[str, str], dict[str, str]] = {}
        for row in rows:
            as_of = row.get("as_of")
            ticker = row.get("ticker")
            if not as_of or not ticker:
                continue
            by_key[(as_of, ticker)] = dict(row)

        return [by_key[key] for key in sorted(by_key)]

    @staticmethod
    def _merged_fieldnames(rows: list[dict[str, str]]) -> list[str]:
        preferred = ["as_of", "ticker", "weight", "score", "rank", "allocation_pct", "sector"]
        seen = {key for row in rows for key in row}
        return [key for key in preferred if key in seen] + sorted(seen - set(preferred))

    @staticmethod
    def _write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
        with path.open("w", encoding="utf-8", newline="") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

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
            matched=response.success and response.matched_count > 0 and response.mismatched_count == 0,
            message=response.message or f"{response.matched_count} matched, {response.mismatched_count} mismatched",
        )

    @staticmethod
    def _combined_runner_step_result(process_results) -> StepResult:
        if not process_results:
            return StepResult(success=False, message="Runner not executed")

        last = process_results[-1]
        stdout = "\n".join(result.stdout for result in process_results if result.stdout)
        stderr = "\n".join(result.stderr for result in process_results if result.stderr)
        return StepResult(
            success=True,
            command=last.command,
            cwd=last.cwd,
            returncode=last.returncode,
            duration_seconds=sum(float(result.duration_seconds or 0.0) for result in process_results),
            timed_out=any(result.timed_out for result in process_results),
            stdout=stdout,
            stderr=stderr,
            message=f"Runner executed {len(process_results)} compare point(s)",
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

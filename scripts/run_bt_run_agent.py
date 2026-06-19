from __future__ import annotations

import argparse
import calendar
import csv
import json
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path

from app.agents.bt_run_agent import BtRunAgentInput, BtRunCompareInput
from app.bootstrap.bt_run_container import build_bt_run_agent
from app.domain.bt_run.run_context import CompareMode, RunContext, RunnerMode, RunProfile
from app.domain.bt_run.run_result import RunResult, StepResult
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput
from scripts.strategy_profiles import (
    StrategyProfile,
    StrategyProfileError,
    available_strategy_profile_names,
    load_strategy_profile_arg,
    strategy_profile_manifest_fields,
    write_strategy_profile_overlay,
)

OUTPUT_PATH_RE = re.compile(
    r"^(?P<label>Equity|Positions|Trades|Bench|Summary):\s*(?P<path>.+?)\s*$",
    re.MULTILINE,
)
PROPOSAL_DELTA_TOLERANCE = 0.00001


@dataclass(frozen=True, slots=True)
class ProfileBehavior:
    compare_mode: CompareMode
    runner_extra_args: tuple[str, ...] = ()
    backtest_lookback_months: int | None = None
    compare_point_count: int = 1
    description: str = ""


class PortfolioFileError(ValueError):
    pass


def resolve_profile_behavior(profile: RunProfile) -> ProfileBehavior:
    if profile == RunProfile.SHORT:
        return ProfileBehavior(
            compare_mode=CompareMode.LATEST,
            backtest_lookback_months=18,
            compare_point_count=1,
            description="fast smoke test: latest compare, 18-month backtest scope",
        )

    if profile == RunProfile.PROBLEM:
        return ProfileBehavior(
            compare_mode=CompareMode.ALL,
            runner_extra_args=("--dump-selection", "--dump-weights"),
            backtest_lookback_months=18,
            compare_point_count=1,
            description=(
                "focused debug run: all compare, 18-month backtest scope, "
                "runner selection/weight dumps"
            ),
        )

    if profile == RunProfile.MEDIUM:
        return ProfileBehavior(
            compare_mode=CompareMode.ALL,
            backtest_lookback_months=30,
            compare_point_count=3,
            description=(
                "development run: all compare, 30-month backtest scope, last 3 BT as_of points"
            ),
        )

    return ProfileBehavior(
        compare_mode=CompareMode.ALL,
        backtest_lookback_months=None,
        compare_point_count=6,
        description=(
            "deep validation run: all compare, full configured backtest scope, "
            "last 6 BT as_of points"
        ),
    )


def build_backtest_profile_args(
    behavior: ProfileBehavior,
    *,
    backtest_config_path: Path,
    start_override: str | None = None,
    end_override: str | None = None,
) -> tuple[str, ...]:
    args: list[str] = []

    if start_override is not None:
        args.extend(("--start", start_override))
    elif behavior.backtest_lookback_months is not None:
        as_of = _load_backtest_as_of(backtest_config_path)
        if as_of is not None:
            start = _subtract_months(as_of, behavior.backtest_lookback_months)
            args.extend(("--start", start.isoformat()))

    if end_override is not None:
        args.extend(("--end", end_override))

    return tuple(args)


def build_backtest_command(
    *,
    config_path: Path,
    decisions_dir: Path,
    profile_args: tuple[str, ...],
) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        "aktien_oop.backtest",
        "--config",
        str(config_path),
        "--decisions-dir",
        str(decisions_dir),
    ) + profile_args


def extract_backtest_arg(
    args: tuple[str, ...],
    flag: str,
) -> str | None:
    try:
        index = args.index(flag)
    except ValueError:
        return None
    value_index = index + 1
    if value_index >= len(args):
        return None
    return args[value_index]


def _load_backtest_as_of(config_path: Path) -> date | None:
    if not config_path.exists():
        return None

    with config_path.open("rb") as file_obj:
        payload = tomllib.load(file_obj)

    raw_as_of = payload.get("as_of")
    if raw_as_of is None and isinstance(payload.get("core"), dict):
        raw_as_of = payload["core"].get("as_of")

    if not isinstance(raw_as_of, str) or not raw_as_of.strip():
        return None

    return date.fromisoformat(raw_as_of.strip())


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year = month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def build_run_context(
    profile: RunProfile,
    runner_mode: RunnerMode = RunnerMode.ANALYSIS,
) -> RunContext:
    ai_agents_dir = Path(
        r"D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents"
    )
    aktien_oop_dir = ai_agents_dir / "aktien_oop"

    now = datetime.now()

    run_id = now.strftime("%Y%m%d_%H%M%S")
    run_label = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{profile.value}_{runner_mode.value}"

    output_dir = ai_agents_dir / "automation_runs" / run_label
    decisions_dir = aktien_oop_dir / "decisions" / run_id

    backtest_config_path = aktien_oop_dir / "backtest_config.toml"
    runner_config_path = aktien_oop_dir / "configs" / "runner_config.toml"

    profile_behavior = resolve_profile_behavior(profile)

    return RunContext(
        run_id=run_id,
        run_timestamp=now,
        run_label=run_label,
        profile=profile,
        compare_mode=profile_behavior.compare_mode,
        ai_agents_dir=ai_agents_dir,
        aktien_oop_dir=aktien_oop_dir,
        decisions_dir=decisions_dir,
        output_dir=output_dir,
        backtest_config_path=backtest_config_path,
        runner_config_path=runner_config_path,
        runner_mode=runner_mode,
        bps_tolerance=5.0,
        ignore_cash=True,
    )


def _step_result_to_dict(step_result: StepResult) -> dict:
    return {
        "success": step_result.success,
        "command": list(step_result.command),
        "cwd": step_result.cwd,
        "returncode": step_result.returncode,
        "duration_seconds": step_result.duration_seconds,
        "timed_out": step_result.timed_out,
        "stdout": step_result.stdout,
        "stderr": step_result.stderr,
        "message": step_result.message,
    }


def build_run_manifest(
    context: RunContext,
    result: RunResult,
    *,
    strategy_profile: StrategyProfile | None = None,
    effective_backtest_config_path: Path | None = None,
    effective_runner_config_path: Path | None = None,
    phase_name: str | None = None,
    warmup_start: str | None = None,
    phase_start: str | None = None,
    phase_end: str | None = None,
    explicit_time_window: bool = False,
    effective_backtest_start: str | None = None,
    effective_backtest_end: str | None = None,
) -> dict:
    manifest = {
        "run_id": context.run_id,
        "run_label": context.run_label,
        "run_timestamp": context.run_timestamp.isoformat(),
        "profile": context.profile.value,
        "runner_mode": context.runner_mode.value,
        "execution": _runner_mode_execution_fields(context.runner_mode),
        "phase_name": phase_name,
        "warmup_start": warmup_start,
        "phase_start": phase_start,
        "phase_end": phase_end,
        "explicit_time_window": explicit_time_window,
        "effective_backtest_start": effective_backtest_start,
        "effective_backtest_end": effective_backtest_end,
        "profile_behavior": resolve_profile_behavior(context.profile).description,
        "compare_point_count": resolve_profile_behavior(context.profile).compare_point_count,
        "compare_mode": context.compare_mode.value,
        "output_dir": str(context.output_dir),
        "decisions_dir": str(context.decisions_dir),
        "backtest_config_path": str(context.backtest_config_path),
        "runner_config_path": str(context.runner_config_path),
        "effective_backtest_config_path": str(
            effective_backtest_config_path or context.backtest_config_path
        ),
        "effective_runner_config_path": str(
            effective_runner_config_path or context.runner_config_path
        ),
        "success": result.success,
        "warnings": list(result.warnings),
        "backtest": _step_result_to_dict(result.backtest),
        "runner": _step_result_to_dict(result.runner),
        "compare": {
            "success": result.compare.success,
            "matched": result.compare.matched,
            "message": result.compare.message,
        },
    }
    manifest.update(_strategy_profile_manifest_fields(strategy_profile))
    return manifest


def _runner_mode_execution_fields(runner_mode: RunnerMode) -> dict[str, object]:
    return {
        "mode": runner_mode.value,
        "approval_status": (
            "manual_approval_required"
            if runner_mode == RunnerMode.PAPER
            else "not_required_for_analysis"
        ),
        "orders_executed": False,
        "broker_connected": False,
        "live_trading_enabled": False,
        "note": (
            "Paper mode only creates proposals, artifacts, and reports; no orders are executed."
            if runner_mode == RunnerMode.PAPER
            else "Analysis mode only creates validation artifacts; no orders are executed."
        ),
    }


def _strategy_profile_manifest_fields(
    strategy_profile: StrategyProfile | None,
) -> dict[str, object]:
    keys = (
        "strategy_profile_name",
        "strategy_profile_label",
        "strategy_profile_file",
        "universe",
        "top_k",
        "use_sector_limits",
        "max_per_sector",
        "max_turnover_cap",
        "require_above_sma",
        "regime_below_action",
        "include_cash",
        "cash_yield_annual",
        "regime_sma_days",
        "benchmark_ticker",
    )
    if strategy_profile is None:
        return dict.fromkeys(keys)
    return strategy_profile_manifest_fields(strategy_profile)


def copy_referenced_backtest_artifacts(context: RunContext, result: RunResult) -> dict[str, str]:
    copied: dict[str, str] = {}
    text = "\n".join((result.backtest.stdout, result.backtest.stderr))
    for match in OUTPUT_PATH_RE.finditer(text):
        label = match.group("label").lower()
        raw_path = match.group("path").strip()
        source_path = Path(raw_path)
        if not source_path.is_absolute():
            source_path = context.ai_agents_dir / source_path
        if not source_path.exists() or not source_path.is_file():
            continue

        try:
            relative_path = source_path.resolve().relative_to(context.ai_agents_dir.resolve())
        except ValueError:
            relative_path = Path(source_path.name)
        target_path = context.output_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied[label] = str(target_path)
    return copied


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=("short", "problem", "medium", "long"),
        default="short",
    )
    parser.add_argument(
        "--strategy-profile",
        help=(
            "Strategy profile name from configs/profiles, e.g. balanced_v1, "
            "or a path to a .toml profile file."
        ),
    )
    parser.add_argument(
        "--runner-mode",
        choices=(RunnerMode.ANALYSIS.value, RunnerMode.PAPER.value),
        default=RunnerMode.ANALYSIS.value,
        help=(
            "Operational runner mode. 'paper' creates proposal/report artifacts only and "
            "never executes orders."
        ),
    )
    parser.add_argument(
        "--portfolio-file",
        help=(
            "Optional CSV with symbol,weight columns for paper-mode previous weights. "
            "This is a local report input only and never triggers order execution."
        ),
    )
    parser.add_argument(
        "--portfolio-name",
        help=(
            "Optional local label for the portfolio baseline shown in paper reports. "
            "This is metadata only and does not affect proposals."
        ),
    )
    parser.add_argument(
        "--warmup-start",
        type=_parse_iso_date,
        help=(
            "Optional warmup data start date YYYY-MM-DD. If set, this is passed to "
            "aktien_oop.backtest as --start while --start remains the phase start."
        ),
    )
    parser.add_argument(
        "--start",
        type=_parse_iso_date,
        help=(
            "Explicit phase start date YYYY-MM-DD. Without --warmup-start this is also "
            "passed as the backtest start."
        ),
    )
    parser.add_argument(
        "--end",
        type=_parse_iso_date,
        help="Explicit backtest end date YYYY-MM-DD.",
    )
    parser.add_argument(
        "--phase-name",
        help="Optional descriptive market phase name for reports and manifest metadata.",
    )
    args = parser.parse_args(argv)
    _validate_time_window(args, parser)
    return args


def _parse_iso_date(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD date, got {value!r}") from exc
    return value


def _validate_time_window(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    values = {
        "warmup_start": args.warmup_start,
        "start": args.start,
        "end": args.end,
    }

    if values["warmup_start"] and values["start"] and values["warmup_start"] > values["start"]:
        parser.error(
            "--warmup-start must be <= --start "
            f"(got {values['warmup_start']} > {values['start']})"
        )
    if values["start"] and values["end"] and values["start"] > values["end"]:
        parser.error(f"--start must be <= --end (got {values['start']} > {values['end']})")
    if values["warmup_start"] and values["end"] and values["warmup_start"] > values["end"]:
        parser.error(
            "--warmup-start must be <= --end "
            f"(got {values['warmup_start']} > {values['end']})"
        )


def load_strategy_profile_for_cli(value: str) -> StrategyProfile:
    return load_strategy_profile_arg(value)


def write_strategy_profile_config_overlays(
    context: RunContext,
    strategy_profile: StrategyProfile,
) -> tuple[Path, Path]:
    overlay_dir = context.output_dir / "config_overlays"
    backtest_overlay_path = overlay_dir / "backtest_config.toml"
    runner_overlay_path = overlay_dir / "runner_config.toml"
    write_strategy_profile_overlay(
        context.backtest_config_path,
        backtest_overlay_path,
        strategy_profile,
    )
    write_strategy_profile_overlay(
        context.runner_config_path,
        runner_overlay_path,
        strategy_profile,
    )
    return backtest_overlay_path, runner_overlay_path


def build_paper_run_artifact(
    context: RunContext,
    result: RunResult,
    *,
    strategy_profile: StrategyProfile | None = None,
    portfolio_file: Path | None = None,
    portfolio_name: str | None = None,
) -> dict[str, object]:
    latest_bundle = _load_latest_decision_bundle(context.decisions_dir, "RUN")
    target_positions = _extract_weights(latest_bundle["payload"]) if latest_bundle else {}
    if portfolio_file is not None:
        previous_positions = load_portfolio_positions_csv(portfolio_file)
        portfolio_source = "portfolio_file"
        portfolio_file_path = str(portfolio_file)
    else:
        previous_positions = (
            _extract_previous_weights(latest_bundle["payload"]) if latest_bundle else {}
        )
        portfolio_source = "runner_previous_state"
        portfolio_file_path = None
    proposals = _build_weight_change_proposals(previous_positions, target_positions)
    proposal_delta_basis = (
        "local portfolio file"
        if portfolio_source == "portfolio_file"
        else "runner previous-state"
    )
    technical_info = [
        warning for warning in result.warnings if warning.strip().startswith("[INFO]")
    ]
    result_warnings = [
        warning
        for warning in result.warnings
        if not warning.strip().startswith("[INFO]")
    ]

    return {
        "run_id": context.run_id,
        "run_label": context.run_label,
        "run_timestamp": context.run_timestamp.isoformat(),
        "runner_mode": context.runner_mode.value,
        "approval_status": "manual_approval_required",
        "orders_executed": False,
        "broker_connected": False,
        "live_trading_enabled": False,
        "execution": {
            "approval_status": "manual_approval_required",
            "orders_executed": False,
            "broker_connected": False,
            "live_trading_enabled": False,
        },
        "strategy_profile_name": strategy_profile.name if strategy_profile else None,
        "strategy_profile_label": strategy_profile.label if strategy_profile else None,
        "universe": strategy_profile.universe if strategy_profile else None,
        "decision_bundle": latest_bundle["path"] if latest_bundle else None,
        "portfolio_name": portfolio_name,
        "portfolio_source": portfolio_source,
        "portfolio_file": portfolio_file_path,
        "proposal_delta_tolerance": PROPOSAL_DELTA_TOLERANCE,
        "proposal_delta_basis": proposal_delta_basis,
        "as_of": latest_bundle["payload"].get("as_of") if latest_bundle else None,
        "target_positions": target_positions,
        "cash_weight": _cash_weight(target_positions),
        "buy_proposals": proposals["buy"],
        "sell_proposals": proposals["sell"],
        "hold_proposals": proposals["hold"],
        "human_review_required": {
            "required": True,
            "reason": "Paper mode creates proposals only. Manual review and approval are required.",
            "checklist": [
                "current market data",
                "actual portfolio positions",
                "available liquidity",
                "order costs and spreads",
                "tax effects",
                "personal risk capacity",
            ],
        },
        "warnings": [
            "No real order was executed.",
            "No broker connection was used.",
            "This report is a proposal only.",
            "Manual approval is required before any future live-trading implementation.",
            *result_warnings,
        ],
        "technical_info": technical_info,
    }


def write_paper_run_report(context: RunContext, artifact: dict[str, object]) -> Path:
    json_path = context.output_dir / "paper_run_report.json"
    txt_path = context.output_dir / "paper_run_report.txt"
    json_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")

    buy_count = len(artifact.get("buy_proposals", []))
    sell_count = len(artifact.get("sell_proposals", []))
    target_positions = artifact.get("target_positions", {})
    target_lines = _format_position_lines(target_positions)
    buy_lines = _format_proposal_lines(artifact.get("buy_proposals", []))
    sell_lines = _format_proposal_lines(artifact.get("sell_proposals", []))
    hold_lines = _format_proposal_lines(artifact.get("hold_proposals", []))
    warnings = artifact.get("warnings", [])
    warning_lines = "\n".join(f"- {warning}" for warning in warnings)
    technical_info = artifact.get("technical_info", [])
    technical_info_lines = "\n".join(f"- {info}" for info in technical_info)
    review = artifact.get("human_review_required", {})
    checklist = review.get("checklist", []) if isinstance(review, dict) else []
    checklist_lines = "\n".join(f"- Check {item}." for item in checklist)
    portfolio_name_lines = (
        [f"portfolio_name: {artifact.get('portfolio_name')}"]
        if artifact.get("portfolio_name")
        else []
    )
    txt_path.write_text(
        "\n".join(
            [
                "Paper Run Report",
                "",
                "Execution Safety",
                "This report contains paper-mode proposals only. It is not an order list.",
                "No real orders were executed.",
                "No broker connection was used.",
                "Live trading was not enabled.",
                "",
                f"run_id: {artifact['run_id']}",
                f"run_label: {artifact.get('run_label')}",
                f"runner_mode: {artifact['runner_mode']}",
                f"strategy_profile_name: {artifact['strategy_profile_name']}",
                f"strategy_profile_label: {artifact['strategy_profile_label']}",
                f"universe: {artifact['universe']}",
                f"as_of: {artifact['as_of']}",
                f"approval_status: {artifact['approval_status']}",
                "orders_executed: false",
                "broker_connected: false",
                "live_trading_enabled: false",
                f"decision_bundle: {artifact['decision_bundle']}",
                *portfolio_name_lines,
                f"portfolio_source: {artifact.get('portfolio_source')}",
                f"portfolio_file: {artifact.get('portfolio_file')}",
                f"proposal_delta_tolerance: {artifact.get('proposal_delta_tolerance')}",
                f"proposal_delta_basis: {artifact.get('proposal_delta_basis')}",
                (
                    "proposal_delta_note: Proposal deltas are calculated against the "
                    f"{artifact.get('proposal_delta_basis')}."
                ),
                f"cash_weight: {artifact['cash_weight']}",
                f"buy_proposals_count: {buy_count}",
                f"sell_proposals_count: {sell_count}",
                "",
                "Target Positions",
                target_lines or "- None",
                "",
                "Buy Proposals",
                buy_lines or "- None",
                "",
                "Sell Proposals",
                sell_lines or "- None",
                "",
                "Hold Proposals",
                hold_lines or "- None",
                "",
                "Warnings",
                warning_lines or "- None",
                "",
                "Technical Info",
                technical_info_lines or "- None",
                "",
                "Human Review Required",
                (
                    "Before any real implementation, a human must manually review "
                    "and approve this proposal."
                ),
                checklist_lines or "- Check current market data.",
                "",
                "NO REAL ORDER WAS EXECUTED.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return json_path


def _format_position_lines(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    return "\n".join(
        f"- {ticker}: {_format_weight(weight)}"
        for ticker, weight in sorted(value.items())
        if isinstance(weight, int | float)
    )


def _format_proposal_lines(value: object) -> str:
    if not isinstance(value, list):
        return ""
    lines = []
    for item in value:
        if not isinstance(item, dict):
            continue
        ticker = item.get("ticker")
        previous = item.get("previous_weight")
        target = item.get("target_weight")
        delta = item.get("delta_weight")
        if ticker is None:
            continue
        if all(isinstance(weight, int | float) for weight in (previous, target, delta)):
            lines.append(
                f"- {ticker}: previous {_format_weight(previous)}, "
                f"target {_format_weight(target)}, delta {_format_weight(delta)}"
            )
        else:
            lines.append(f"- {ticker}")
    return "\n".join(lines)


def _format_weight(value: int | float) -> str:
    return f"{float(value):.6f}"


def _load_latest_decision_bundle(decisions_dir: Path, kind: str) -> dict[str, object] | None:
    if not decisions_dir.exists():
        return None

    candidates: list[tuple[str, str, Path, dict]] = []
    for path in decisions_dir.glob(f"{kind}_*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        as_of = payload.get("as_of")
        candidates.append((str(as_of or ""), path.name, path, payload))

    if not candidates:
        return None

    _, _, path, payload = sorted(candidates)[-1]
    return {"path": str(path), "payload": payload}


def _extract_weights(payload: dict) -> dict[str, float]:
    for field in ("new_weights", "weights", "positions"):
        value = payload.get(field)
        normalized = _normalize_weights(value)
        if normalized is not None:
            return normalized
    return {}


def _extract_previous_weights(payload: dict) -> dict[str, float]:
    for field in ("old_weights", "previous_weights", "current_weights"):
        value = payload.get(field)
        normalized = _normalize_weights(value)
        if normalized is not None:
            return normalized
    return {}


def _normalize_weights(value: object) -> dict[str, float] | None:
    if isinstance(value, dict):
        return {str(ticker): float(weight) for ticker, weight in value.items()}
    if isinstance(value, list):
        weights: dict[str, float] = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            ticker = item.get("ticker")
            weight = item.get("weight", item.get("allocation_pct"))
            if ticker is not None and weight is not None:
                weights[str(ticker)] = float(weight)
        return weights
    return None


def load_portfolio_positions_csv(path: Path) -> dict[str, float]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as file_obj:
            reader = csv.DictReader(file_obj)
            fieldnames = set(reader.fieldnames or ())
            missing = {"symbol", "weight"} - fieldnames
            if missing:
                missing_fields = ", ".join(sorted(missing))
                raise PortfolioFileError(
                    f"Invalid portfolio file {path}: missing required column(s): "
                    f"{missing_fields}"
                )

            positions: dict[str, float] = {}
            for line_number, row in enumerate(reader, start=2):
                symbol = str(row.get("symbol", "")).strip().upper()
                if not symbol:
                    raise PortfolioFileError(
                        f"Invalid portfolio file {path}: empty symbol in line {line_number}"
                    )
                if symbol in positions:
                    raise PortfolioFileError(
                        f"Invalid portfolio file {path}: duplicate symbol {symbol!r}"
                    )

                raw_weight = str(row.get("weight", "")).strip()
                if not raw_weight:
                    raise PortfolioFileError(
                        f"Invalid portfolio file {path}: empty weight for {symbol!r} "
                        f"in line {line_number}"
                    )
                try:
                    weight = float(raw_weight)
                except ValueError as exc:
                    raise PortfolioFileError(
                        f"Invalid portfolio file {path}: invalid weight for {symbol!r} "
                        f"in line {line_number}: {raw_weight!r}"
                    ) from exc
                if weight < 0:
                    raise PortfolioFileError(
                        f"Invalid portfolio file {path}: negative weight for {symbol!r} "
                        f"in line {line_number}"
                    )
                positions[symbol] = weight
    except FileNotFoundError as exc:
        raise PortfolioFileError(f"Portfolio file not found: {path}") from exc
    except OSError as exc:
        raise PortfolioFileError(f"Could not read portfolio file {path}: {exc}") from exc

    return positions


def _build_weight_change_proposals(
    previous_weights: dict[str, float],
    target_weights: dict[str, float],
) -> dict[str, list[dict[str, float | str]]]:
    proposals: dict[str, list[dict[str, float | str]]] = {
        "buy": [],
        "sell": [],
        "hold": [],
    }
    for ticker in sorted(set(previous_weights) | set(target_weights)):
        previous = previous_weights.get(ticker, 0.0)
        target = target_weights.get(ticker, 0.0)
        delta = target - previous
        item = {
            "ticker": ticker,
            "previous_weight": previous,
            "target_weight": target,
            "delta_weight": delta,
        }
        if delta > PROPOSAL_DELTA_TOLERANCE:
            proposals["buy"].append(item)
        elif delta < -PROPOSAL_DELTA_TOLERANCE:
            proposals["sell"].append(item)
        else:
            proposals["hold"].append(item)
    return proposals


def _cash_weight(weights: dict[str, float]) -> float:
    for ticker, weight in weights.items():
        if ticker.upper() in {"CASH", "EUR", "USD"}:
            return weight
    return max(0.0, 1.0 - sum(weights.values())) if weights else 0.0


def main() -> None:
    args = parse_args()
    strategy_profile = None
    if args.strategy_profile:
        try:
            strategy_profile = load_strategy_profile_for_cli(args.strategy_profile)
        except StrategyProfileError as exc:
            known = ", ".join(available_strategy_profile_names()) or "none"
            raise SystemExit(f"error: {exc}\nSupported strategy profiles: {known}") from exc

    profile = RunProfile(args.profile)
    runner_mode = RunnerMode(args.runner_mode)
    portfolio_file = Path(args.portfolio_file) if args.portfolio_file else None
    if runner_mode == RunnerMode.PAPER and portfolio_file is not None:
        try:
            load_portfolio_positions_csv(portfolio_file)
        except PortfolioFileError as exc:
            raise SystemExit(f"error: {exc}") from exc
    context = build_run_context(profile, runner_mode)
    profile_behavior = resolve_profile_behavior(profile)
    context.output_dir.mkdir(parents=True, exist_ok=True)
    context.decisions_dir.mkdir(parents=True, exist_ok=True)
    effective_backtest_config_path = context.backtest_config_path
    effective_runner_config_path = context.runner_config_path
    if strategy_profile is not None:
        effective_backtest_config_path, effective_runner_config_path = (
            write_strategy_profile_config_overlays(context, strategy_profile)
        )
    backtest_start_override = args.warmup_start or args.start
    backtest_profile_args = build_backtest_profile_args(
        profile_behavior,
        backtest_config_path=effective_backtest_config_path,
        start_override=backtest_start_override,
        end_override=args.end,
    )
    effective_backtest_start = extract_backtest_arg(backtest_profile_args, "--start")
    effective_backtest_end = extract_backtest_arg(backtest_profile_args, "--end")
    explicit_time_window = bool(args.start or args.end or args.phase_name or args.warmup_start)

    print("run_id:", context.run_id)
    print("run_label:", context.run_label)
    print("profile:", context.profile)
    print("runner_mode:", context.runner_mode.value)
    print("orders_executed:", False)
    print("phase_name:", args.phase_name)
    print("warmup_start:", args.warmup_start)
    print("phase_start:", args.start)
    print("phase_end:", args.end)
    print("compare_mode:", context.compare_mode)
    print("profile_behavior:", profile_behavior.description)
    print("output_dir:", context.output_dir)
    print("ai_agents_dir:", context.ai_agents_dir)
    print("aktien_oop_dir:", context.aktien_oop_dir)
    print("backtest config exists:", context.backtest_config_path.exists())
    print("runner config exists:", context.runner_config_path.exists())
    if strategy_profile is not None:
        print("strategy_profile_name:", strategy_profile.name)
        print("strategy_profile_label:", strategy_profile.label)
        print("strategy_profile_file:", strategy_profile.source_path.as_posix())
        print("effective_backtest_config:", effective_backtest_config_path)
        print("effective_runner_config:", effective_runner_config_path)
    print("decisions dir exists:", context.decisions_dir.exists())

    agent = build_bt_run_agent(context.decisions_dir)

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=build_backtest_command(
                    config_path=effective_backtest_config_path,
                    decisions_dir=context.decisions_dir,
                    profile_args=backtest_profile_args,
                ),
                cwd=context.ai_agents_dir,
                config_path=effective_backtest_config_path,
            ),
            runner_input=RunRunnerToolInput(
                command=(
                    sys.executable,
                    "-m",
                    "aktien_oop.main",
                    "--config",
                    str(effective_runner_config_path),
                    "--decisions-dir",
                    str(context.decisions_dir),
                )
                + profile_behavior.runner_extra_args,
                cwd=context.ai_agents_dir,
                config_path=effective_runner_config_path,
            ),
            compare_input=BtRunCompareInput(
                bps_tolerance=context.bps_tolerance,
                ignore_cash=context.ignore_cash,
            ),
            compare_mode=context.compare_mode,
            seed_runner_previous_from_backtest=True,
            compare_point_count=profile_behavior.compare_point_count,
            require_bt_bundles_for_compare=explicit_time_window,
            explicit_time_window_start=args.start,
            explicit_time_window_end=args.end,
            explicit_warmup_start=args.warmup_start,
            explicit_phase_name=args.phase_name,
        )
    )
    result = replace(
        result,
        warnings=(
            f"[INFO] Using run-specific decisions directory: {context.decisions_dir}",
            f"[INFO] Profile behavior: {profile_behavior.description}",
            *(
                (
                    f"[INFO] Strategy profile: {strategy_profile.name} "
                    f"({strategy_profile.source_path})",
                )
                if strategy_profile is not None
                else ()
            ),
            *result.warnings,
        ),
    )

    (context.output_dir / "backtest_stdout.txt").write_text(
        result.backtest.stdout,
        encoding="utf-8",
    )
    (context.output_dir / "backtest_stderr.txt").write_text(
        result.backtest.stderr,
        encoding="utf-8",
    )
    (context.output_dir / "runner_stdout.txt").write_text(result.runner.stdout, encoding="utf-8")
    (context.output_dir / "runner_stderr.txt").write_text(result.runner.stderr, encoding="utf-8")
    artifact_paths = copy_referenced_backtest_artifacts(context, result)
    warnings_text = "\n".join(result.warnings) if result.warnings else "None"
    effective_start_text = effective_backtest_start if effective_backtest_start else "None"
    effective_end_text = effective_backtest_end if effective_backtest_end else "None"
    regime_action = strategy_profile.regime_below_action if strategy_profile else "None"
    profile_args_text = " ".join(backtest_profile_args) if backtest_profile_args else "None"
    approval_status = _runner_mode_execution_fields(context.runner_mode)["approval_status"]

    summary_text = (
        f"run_id: {context.run_id}\n"
        f"profile: {context.profile.value}\n"
        f"runner_mode: {context.runner_mode.value}\n"
        f"approval_status: {approval_status}\n"
        f"orders_executed: false\n"
        f"phase_name: {args.phase_name if args.phase_name else 'None'}\n"
        f"warmup_start: {args.warmup_start if args.warmup_start else 'None'}\n"
        f"phase_start: {args.start if args.start else 'None'}\n"
        f"phase_end: {args.end if args.end else 'None'}\n"
        f"effective_backtest_start: {effective_start_text}\n"
        f"effective_backtest_end: {effective_end_text}\n"
        f"profile_behavior: {profile_behavior.description}\n"
        f"strategy_profile_name: {strategy_profile.name if strategy_profile else 'None'}\n"
        f"strategy_profile_label: {strategy_profile.label if strategy_profile else 'None'}\n"
        f"strategy_profile_file: "
        f"{strategy_profile.source_path.as_posix() if strategy_profile else 'None'}\n"
        f"universe: {strategy_profile.universe if strategy_profile else 'None'}\n"
        f"top_k: {strategy_profile.top_k if strategy_profile else 'None'}\n"
        f"use_sector_limits: {strategy_profile.use_sector_limits if strategy_profile else 'None'}\n"
        f"max_per_sector: {strategy_profile.max_per_sector if strategy_profile else 'None'}\n"
        f"max_turnover_cap: {strategy_profile.max_turnover_cap if strategy_profile else 'None'}\n"
        f"require_above_sma: {strategy_profile.require_above_sma if strategy_profile else 'None'}\n"
        f"regime_below_action: {regime_action}\n"
        f"include_cash: {strategy_profile.include_cash if strategy_profile else 'None'}\n"
        f"cash_yield_annual: {strategy_profile.cash_yield_annual if strategy_profile else 'None'}\n"
        f"regime_sma_days: {strategy_profile.regime_sma_days if strategy_profile else 'None'}\n"
        f"benchmark_ticker: {strategy_profile.benchmark_ticker if strategy_profile else 'None'}\n"
        f"backtest_profile_args: {profile_args_text}\n"
        f"compare_point_count: {profile_behavior.compare_point_count}\n"
        f"compare_mode: {context.compare_mode.value}\n"
        f"success: {result.success}\n"
        f"backtest_success: {result.backtest.success}\n"
        f"runner_success: {result.runner.success}\n"
        f"compare_success: {result.compare.success}\n"
        f"compare_matched: {result.compare.matched}\n"
        f"compare_message: {result.compare.message}\n"
        f"warnings: {warnings_text}\n"
    )
    (context.output_dir / "summary.txt").write_text(summary_text, encoding="utf-8")

    print("=== BT RUN AGENT RESULT ===")
    print(f"success: {result.success}")
    print(f"backtest_success: {result.backtest.success}")
    print(f"runner_success: {result.runner.success}")
    print(f"compare_success: {result.compare.success}")
    print(f"compare_matched: {result.compare.matched}")
    print(f"compare_message: {result.compare.message}")
    print()
    print("--- backtest stdout ---")
    print(result.backtest.stdout)
    print("--- backtest stderr ---")
    print(result.backtest.stderr)
    print()
    print("--- runner stdout ---")
    print(result.runner.stdout)
    print("--- runner stderr ---")
    print(result.runner.stderr)

    manifest = build_run_manifest(
        context,
        result,
        strategy_profile=strategy_profile,
        effective_backtest_config_path=effective_backtest_config_path,
        effective_runner_config_path=effective_runner_config_path,
        phase_name=args.phase_name,
        warmup_start=args.warmup_start,
        phase_start=args.start,
        phase_end=args.end,
        explicit_time_window=explicit_time_window,
        effective_backtest_start=effective_backtest_start,
        effective_backtest_end=effective_backtest_end,
    )
    manifest["artifacts"] = artifact_paths
    if context.runner_mode == RunnerMode.PAPER:
        paper_artifact = build_paper_run_artifact(
            context,
            result,
            strategy_profile=strategy_profile,
            portfolio_file=portfolio_file,
            portfolio_name=args.portfolio_name,
        )
        paper_report_path = write_paper_run_report(context, paper_artifact)
        manifest["paper"] = paper_artifact
        manifest["artifacts"]["paper_report"] = str(paper_report_path)
    (context.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

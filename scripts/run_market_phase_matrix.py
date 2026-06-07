from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from scripts.compare_runs import default_decisions_root, default_runs_root, load_run_snapshot
from scripts.run_profile_compare_v1 import _fmt_num, _fmt_pct, _md_table
from scripts.run_profile_robustness_matrix import (
    empty_metrics,
    excerpt,
    extract_run_id,
    find_run_output_dir,
    metrics_from_snapshot,
    missing_fields,
    parse_csv_arg,
    validate_known_strategy_profiles,
)

DEFAULT_PROFILE = "medium"
DEFAULT_STRATEGY_PROFILES = ("conservative_v1", "balanced_v1", "offensive_v1")
REPORT_DIR = Path("reports") / "strategy_analysis" / "market_phase_matrix"
SUMMARY_MD_NAME = "market_phase_matrix_summary.md"
SUMMARY_JSON_NAME = "market_phase_matrix_summary.json"
PHASE_METRICS_NOTE = (
    "Note: Performance metrics are currently extracted from the run summary/artifacts and may "
    "include the warmup path. Phase-only metrics should be added in a later step by segmenting "
    "equity and benchmark curves to phase_start..phase_end."
)


@dataclass(frozen=True, slots=True)
class MarketPhase:
    phase_name: str
    type: str
    warmup_start: str
    phase_start: str
    phase_end: str


DEFAULT_PHASES = (
    MarketPhase(
        phase_name="bear_market_2022",
        type="Bärenmarkt / Zinsphase",
        warmup_start="2020-07-01",
        phase_start="2022-01-01",
        phase_end="2022-12-31",
    ),
    MarketPhase(
        phase_name="recovery_2023",
        type="Erholung / Momentum",
        warmup_start="2021-07-01",
        phase_start="2023-01-01",
        phase_end="2023-12-31",
    ),
    MarketPhase(
        phase_name="recent_2024_2025",
        type="jüngere Marktphase",
        warmup_start="2022-07-01",
        phase_start="2024-01-01",
        phase_end="2025-10-08",
    ),
)


@dataclass(frozen=True, slots=True)
class MarketPhaseCell:
    phase: MarketPhase
    strategy_profile: str
    profile: str = DEFAULT_PROFILE


@dataclass(frozen=True, slots=True)
class MarketPhaseRunResult:
    phase_name: str
    phase_type: str
    strategy_profile: str
    profile: str
    command: tuple[str, ...]
    returncode: int | None
    run_id: str | None
    run_dir: str | None
    manifest_path: str | None
    summary_path: str | None
    success: bool
    compare_success: bool | None
    compare_matched: bool | None
    compare_message: str | None
    runner_compare_points: tuple[str, ...]
    warmup_start: str
    phase_start: str
    phase_end: str
    effective_backtest_start: str | None
    effective_backtest_end: str | None
    metrics: dict[str, float | None]
    warnings: tuple[str, ...]
    error: str | None
    stdout_excerpt: str | None
    stderr_excerpt: str | None
    missing: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the market phase matrix via scripts.run_bt_run_agent."
    )
    parser.add_argument(
        "--strategy-profiles",
        default=",".join(DEFAULT_STRATEGY_PROFILES),
        help=(
            "Comma-separated strategy profiles. Defaults to "
            "conservative_v1,balanced_v1,offensive_v1."
        ),
    )
    parser.add_argument(
        "--phases",
        default=",".join(phase.phase_name for phase in DEFAULT_PHASES),
        help=(
            "Comma-separated market phases. Defaults to "
            "bear_market_2022,recovery_2023,recent_2024_2025."
        ),
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help="Run profile passed to scripts.run_bt_run_agent. Defaults to medium.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(REPORT_DIR),
        help="Directory for market phase matrix reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    strategy_profiles = parse_csv_arg(args.strategy_profiles)
    phases = resolve_phases(parse_csv_arg(args.phases))
    validate_known_strategy_profiles(strategy_profiles)
    report_dir = Path(args.report_dir)

    results = run_matrix(build_matrix(phases, strategy_profiles, profile=args.profile))
    write_reports(results, phases=phases, profile=args.profile, report_dir=report_dir)

    failed_count = sum(1 for result in results if not result.success)
    mismatched_count = sum(1 for result in results if result.compare_matched is False)
    print(
        "Market phase matrix completed: "
        f"{len(results) - failed_count} succeeded, {failed_count} failed, "
        f"{mismatched_count} compare mismatched"
    )
    print(f"Markdown report: {(report_dir / SUMMARY_MD_NAME).as_posix()}")
    print(f"JSON report: {(report_dir / SUMMARY_JSON_NAME).as_posix()}")


def resolve_phases(phase_names: Sequence[str]) -> tuple[MarketPhase, ...]:
    phases_by_name = {phase.phase_name: phase for phase in DEFAULT_PHASES}
    unknown = sorted(set(phase_names) - set(phases_by_name))
    if unknown:
        raise SystemExit(
            "Unknown market phases: "
            f"{', '.join(unknown)}. Known phases: {', '.join(sorted(phases_by_name))}"
        )
    return tuple(phases_by_name[name] for name in phase_names)


def build_matrix(
    phases: Sequence[MarketPhase] = DEFAULT_PHASES,
    strategy_profiles: Sequence[str] = DEFAULT_STRATEGY_PROFILES,
    *,
    profile: str = DEFAULT_PROFILE,
) -> list[MarketPhaseCell]:
    return [
        MarketPhaseCell(phase=phase, strategy_profile=strategy_profile, profile=profile)
        for phase in phases
        for strategy_profile in strategy_profiles
    ]


def build_command(cell: MarketPhaseCell) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        "scripts.run_bt_run_agent",
        "--profile",
        cell.profile,
        "--strategy-profile",
        cell.strategy_profile,
        "--warmup-start",
        cell.phase.warmup_start,
        "--start",
        cell.phase.phase_start,
        "--end",
        cell.phase.phase_end,
        "--phase-name",
        cell.phase.phase_name,
    )


def run_matrix(cells: Sequence[MarketPhaseCell]) -> list[MarketPhaseRunResult]:
    return [run_cell(cell) for cell in cells]


def run_cell(cell: MarketPhaseCell) -> MarketPhaseRunResult:
    command = build_command(cell)
    print(f"=== {cell.phase.phase_name} {cell.strategy_profile} ===")
    completed = subprocess.run(
        command,
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    run_id = extract_run_id(completed.stdout)
    if completed.returncode != 0:
        return failed_result(
            cell,
            command=command,
            returncode=completed.returncode,
            run_id=run_id,
            error=f"run_bt_run_agent failed with returncode {completed.returncode}",
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    if run_id is None:
        return failed_result(
            cell,
            command=command,
            returncode=completed.returncode,
            run_id=None,
            error="Could not extract run_id from run_bt_run_agent stdout",
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    try:
        snapshot = load_run_snapshot(
            run_id,
            runs_root=default_runs_root(),
            decisions_root=default_decisions_root(),
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return failed_result(
            cell,
            command=command,
            returncode=completed.returncode,
            run_id=run_id,
            error=f"Could not load run snapshot: {exc}",
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    run_dir = snapshot.output_dir
    manifest_path = run_dir / "run_manifest.json" if run_dir is not None else None
    summary_path = run_dir / "summary.txt" if run_dir is not None else None
    manifest = load_manifest(manifest_path)
    metrics = metrics_from_snapshot(snapshot)
    missing = missing_fields(run_dir, manifest_path, summary_path, metrics)

    return result_from_manifest(
        cell,
        command=command,
        returncode=completed.returncode,
        run_id=run_id,
        run_dir=run_dir,
        manifest_path=manifest_path,
        summary_path=summary_path,
        manifest=manifest,
        metrics=metrics,
        missing=missing,
        error=None,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def failed_result(
    cell: MarketPhaseCell,
    *,
    command: tuple[str, ...],
    returncode: int | None,
    run_id: str | None,
    error: str,
    stdout: str,
    stderr: str,
) -> MarketPhaseRunResult:
    run_dir = find_run_output_dir(run_id, default_runs_root()) if run_id is not None else None
    manifest_path = run_dir / "run_manifest.json" if run_dir is not None else None
    summary_path = run_dir / "summary.txt" if run_dir is not None else None
    manifest = load_manifest(manifest_path)
    metrics = empty_metrics()
    return result_from_manifest(
        cell,
        command=command,
        returncode=returncode,
        run_id=run_id,
        run_dir=run_dir,
        manifest_path=manifest_path,
        summary_path=summary_path,
        manifest=manifest,
        metrics=metrics,
        missing=missing_fields(run_dir, manifest_path, summary_path, metrics),
        error=error,
        stdout=stdout,
        stderr=stderr,
        force_failed=True,
    )


def result_from_manifest(
    cell: MarketPhaseCell,
    *,
    command: tuple[str, ...],
    returncode: int | None,
    run_id: str | None,
    run_dir: Path | None,
    manifest_path: Path | None,
    summary_path: Path | None,
    manifest: dict[str, Any],
    metrics: dict[str, float | None],
    missing: tuple[str, ...],
    error: str | None,
    stdout: str,
    stderr: str,
    force_failed: bool = False,
) -> MarketPhaseRunResult:
    compare = manifest.get("compare") if isinstance(manifest.get("compare"), dict) else {}
    compare_success = _bool_or_none(compare.get("success"))
    compare_matched = _bool_or_none(compare.get("matched"))
    manifest_success = _bool_or_none(manifest.get("success"))
    warnings = tuple(
        str(warning) for warning in manifest.get("warnings", ()) if isinstance(warning, str)
    )
    success = (
        False
        if force_failed
        else bool(manifest_success if manifest_success is not None else returncode == 0)
        and compare_success is not False
        and compare_matched is not False
    )

    return MarketPhaseRunResult(
        phase_name=cell.phase.phase_name,
        phase_type=cell.phase.type,
        strategy_profile=cell.strategy_profile,
        profile=cell.profile,
        command=command,
        returncode=returncode,
        run_id=run_id,
        run_dir=str(run_dir) if run_dir is not None else None,
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        summary_path=str(summary_path) if summary_path is not None else None,
        success=success,
        compare_success=compare_success,
        compare_matched=compare_matched,
        compare_message=compare.get("message") if isinstance(compare.get("message"), str) else None,
        runner_compare_points=extract_runner_compare_points(warnings),
        warmup_start=_str_or_default(manifest.get("warmup_start"), cell.phase.warmup_start),
        phase_start=_str_or_default(manifest.get("phase_start"), cell.phase.phase_start),
        phase_end=_str_or_default(manifest.get("phase_end"), cell.phase.phase_end),
        effective_backtest_start=_str_or_none(manifest.get("effective_backtest_start")),
        effective_backtest_end=_str_or_none(manifest.get("effective_backtest_end")),
        metrics=metrics,
        warnings=warnings,
        error=error,
        stdout_excerpt=excerpt(stdout),
        stderr_excerpt=excerpt(stderr),
        missing=missing,
    )


def load_manifest(manifest_path: Path | None) -> dict[str, Any]:
    if manifest_path is None or not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_runner_compare_points(warnings: Sequence[str]) -> tuple[str, ...]:
    prefix = "[INFO] Runner compare points:"
    for warning in warnings:
        if not warning.startswith(prefix):
            continue
        marker = "as_of="
        if marker not in warning:
            continue
        raw_points = warning.split(marker, 1)[1]
        return tuple(point.strip() for point in raw_points.split(",") if point.strip())
    return ()


def write_reports(
    results: Sequence[MarketPhaseRunResult],
    *,
    phases: Sequence[MarketPhase],
    profile: str,
    report_dir: Path,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().isoformat(timespec="seconds")
    (report_dir / SUMMARY_MD_NAME).write_text(
        build_markdown_report(results, phases=phases, generated_at=generated_at),
        encoding="utf-8",
    )
    (report_dir / SUMMARY_JSON_NAME).write_text(
        json.dumps(
            build_json_report(results, phases=phases, profile=profile, generated_at=generated_at),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def build_markdown_report(
    results: Sequence[MarketPhaseRunResult],
    *,
    phases: Sequence[MarketPhase],
    generated_at: str,
) -> str:
    lines = [
        "# Market Phase Matrix",
        "",
        f"Generated at: {generated_at}",
        "",
        PHASE_METRICS_NOTE,
        "",
        "## Executed Phases",
        _md_table(
            ("Phase", "Type", "Warmup Start", "Phase Start", "Phase End"),
            tuple(
                (
                    phase.phase_name,
                    phase.type,
                    phase.warmup_start,
                    phase.phase_start,
                    phase.phase_end,
                )
                for phase in phases
            ),
        ),
        "",
        "## Executed Matrix",
        _md_table(
            (
                "Phase",
                "Strategy Profile",
                "Run ID",
                "Success",
                "Compare matched",
                "Compare message",
            ),
            tuple(
                (
                    result.phase_name,
                    result.strategy_profile,
                    result.run_id or "n/a",
                    _bool_or_na(result.success),
                    _bool_or_na(result.compare_matched),
                    result.compare_message or "n/a",
                )
                for result in results
            ),
        ),
        "",
        "## Technical Details",
        _md_table(
            (
                "Phase",
                "Strategy Profile",
                "Runner Compare Points",
                "Effective Backtest Start",
                "Effective Backtest End",
            ),
            tuple(
                (
                    result.phase_name,
                    result.strategy_profile,
                    ", ".join(result.runner_compare_points) or "n/a",
                    result.effective_backtest_start or "n/a",
                    result.effective_backtest_end or "n/a",
                )
                for result in results
            ),
        ),
        "",
        "## Metrics",
        _md_table(
            (
                "Phase",
                "Strategy Profile",
                "Total Return",
                "CAGR",
                "Max Drawdown",
                "Sharpe",
                "Volatility",
                "Turnover",
                "Benchmark CAGR",
                "Benchmark Max DD",
                "Compare matched",
            ),
            tuple(_metrics_row(result) for result in results),
        ),
        "",
        "## Summary",
        *build_hints(results),
        "",
    ]
    return "\n".join(lines)


def _metrics_row(result: MarketPhaseRunResult) -> tuple[object, ...]:
    metrics = result.metrics
    return (
        result.phase_name,
        result.strategy_profile,
        _fmt_pct(metrics["total_return"]),
        _fmt_pct(metrics["cagr"]),
        _fmt_pct(metrics["max_drawdown"]),
        _fmt_num(metrics["sharpe"]),
        _fmt_pct(metrics["volatility"]),
        _fmt_pct(metrics["turnover"]),
        _fmt_pct(metrics["benchmark_cagr"]),
        _fmt_pct(metrics["benchmark_max_drawdown"]),
        _bool_or_na(result.compare_matched),
    )


def build_hints(results: Sequence[MarketPhaseRunResult]) -> list[str]:
    successful = sum(1 for result in results if result.success)
    failed = sum(1 for result in results if not result.success)
    mismatched = sum(1 for result in results if result.compare_matched is False)
    hints = [
        f"- Runs: {len(results)} total, {successful} successful, {failed} failed, "
        f"{mismatched} compare mismatched."
    ]
    for result in results:
        label = f"{result.phase_name}/{result.strategy_profile}"
        if result.compare_matched is False:
            hints.append(f"- {label}: compare.matched = false")
        if result.error:
            hints.append(f"- {label}: error: {result.error}")
        if result.missing:
            hints.append(f"- {label}: missing: {', '.join(result.missing)}")
        if result.warnings:
            hints.append(f"- {label}: warnings: {_single_line(' | '.join(result.warnings))}")
        if result.stderr_excerpt:
            hints.append(f"- {label}: stderr excerpt: `{_single_line(result.stderr_excerpt)}`")
    return hints


def build_json_report(
    results: Sequence[MarketPhaseRunResult],
    *,
    phases: Sequence[MarketPhase],
    profile: str,
    generated_at: str,
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "profile": profile,
        "phases": [asdict(phase) for phase in phases],
        "summary": {
            "total": len(results),
            "success": sum(1 for result in results if result.success),
            "failed": sum(1 for result in results if not result.success),
            "compare_mismatched": sum(1 for result in results if result.compare_matched is False),
        },
        "matrix": [asdict(result) for result in results],
    }


def _bool_or_none(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _bool_or_na(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "true" if value else "false"


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _str_or_default(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


if __name__ == "__main__":
    main()

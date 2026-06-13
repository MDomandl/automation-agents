from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence

from scripts.compare_runs import default_decisions_root, default_runs_root, load_run_snapshot
from scripts.phase_metrics import compute_phase_metrics, phase_metrics_warnings
from scripts.run_profile_compare_v1 import _fmt_num, _fmt_pct, _md_table
from scripts.run_profile_robustness_matrix import (
    excerpt,
    extract_run_id,
    find_run_output_dir,
    parse_csv_arg,
    validate_known_strategy_profiles,
)

DEFAULT_PROFILE = "medium"
DEFAULT_STRATEGY_PROFILE = "balanced_v1"
DEFAULT_WINDOW_MODE = "yearly"
DEFAULT_AS_OF = "2025-10-08"
REPORT_DIR = Path("reports") / "strategy_analysis" / "walk_forward"
SUMMARY_MD_NAME = "walk_forward_summary.md"
SUMMARY_JSON_NAME = "walk_forward_summary.json"
MEDIUM_COMPARE_NOTE = (
    "Profile medium compares only the last 3 BT as_of points; OOS metrics use the full "
    "equity/benchmark segment."
)
PROFILE_MATRIX_NOTE = (
    "Multiple strategy profiles are a stability comparison only, not after-the-fact "
    "profile optimization."
)


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    window_name: str
    warmup_start: str
    oos_start: str
    oos_end: str


@dataclass(frozen=True, slots=True)
class WalkForwardCell:
    window: WalkForwardWindow
    strategy_profile: str
    profile: str = DEFAULT_PROFILE


@dataclass(frozen=True, slots=True)
class WalkForwardRunResult:
    window_name: str
    strategy_profile: str
    profile: str
    warmup_start: str
    oos_start: str
    oos_end: str
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
    runner_compare_point_count: int | None
    effective_backtest_start: str | None
    effective_backtest_end: str | None
    phase_metrics: dict[str, float | bool | int | str | None]
    warnings: tuple[str, ...]
    error: str | None
    stdout_excerpt: str | None
    stderr_excerpt: str | None
    missing: tuple[str, ...]


YEARLY_WINDOWS = (
    WalkForwardWindow("oos_2022", "2020-07-01", "2022-01-01", "2022-12-31"),
    WalkForwardWindow("oos_2023", "2021-07-01", "2023-01-01", "2023-12-31"),
    WalkForwardWindow("oos_2024", "2022-07-01", "2024-01-01", "2024-12-31"),
    WalkForwardWindow("oos_2025_ytd", "2023-01-01", "2025-01-01", "2025-10-08"),
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run predefined walk-forward/OOS windows via scripts.run_bt_run_agent."
    )
    parser.add_argument(
        "--strategy-profile",
        default=DEFAULT_STRATEGY_PROFILE,
        help="Single strategy profile to run. Defaults to balanced_v1.",
    )
    parser.add_argument(
        "--strategy-profiles",
        help=(
            "Optional comma-separated strategy profiles. Stability comparison only, not "
            "after-the-fact profile optimization."
        ),
    )
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        choices=("short", "problem", "medium", "long"),
        help="Run profile passed to scripts.run_bt_run_agent. Defaults to medium.",
    )
    parser.add_argument(
        "--window-mode",
        default=DEFAULT_WINDOW_MODE,
        choices=(DEFAULT_WINDOW_MODE,),
        help="Window definition mode. Defaults to yearly.",
    )
    parser.add_argument(
        "--as-of",
        default=DEFAULT_AS_OF,
        type=_parse_iso_date,
        help="Last available OOS date YYYY-MM-DD. Defaults to 2025-10-08.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPORT_DIR),
        help="Directory for walk-forward reports.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    strategy_profiles = resolve_strategy_profiles(args)
    validate_known_strategy_profiles(strategy_profiles)
    windows = resolve_windows(args.window_mode, args.as_of)
    results = run_matrix(build_matrix(windows, strategy_profiles, profile=args.profile))
    write_reports(
        results,
        windows=windows,
        window_mode=args.window_mode,
        profile=args.profile,
        strategy_profiles=strategy_profiles,
        as_of=args.as_of,
        report_dir=Path(args.output_dir),
    )

    summary = summarize_results(results, windows=windows)
    print(
        "Walk-forward matrix completed: "
        f"{summary['runs_successful']} succeeded, {summary['runs_failed']} failed, "
        f"{summary['compare_mismatched']} compare mismatched"
    )
    print(f"Markdown report: {(Path(args.output_dir) / SUMMARY_MD_NAME).as_posix()}")
    print(f"JSON report: {(Path(args.output_dir) / SUMMARY_JSON_NAME).as_posix()}")


def resolve_strategy_profiles(args: argparse.Namespace) -> tuple[str, ...]:
    if args.strategy_profiles:
        return parse_csv_arg(args.strategy_profiles)
    return (args.strategy_profile,)


def resolve_windows(window_mode: str, as_of: str) -> tuple[WalkForwardWindow, ...]:
    if window_mode != DEFAULT_WINDOW_MODE:
        raise SystemExit(f"Unknown window-mode: {window_mode}. Known modes: yearly")
    cutoff = date.fromisoformat(as_of)
    windows: list[WalkForwardWindow] = []
    for window in YEARLY_WINDOWS:
        oos_start = date.fromisoformat(window.oos_start)
        oos_end = date.fromisoformat(window.oos_end)
        if oos_start > cutoff:
            continue
        effective_end = min(oos_end, cutoff).isoformat()
        windows.append(
            WalkForwardWindow(
                window.window_name,
                window.warmup_start,
                window.oos_start,
                effective_end,
            )
        )
    return tuple(windows)


def build_matrix(
    windows: Sequence[WalkForwardWindow],
    strategy_profiles: Sequence[str],
    *,
    profile: str = DEFAULT_PROFILE,
) -> list[WalkForwardCell]:
    return [
        WalkForwardCell(window=window, strategy_profile=strategy_profile, profile=profile)
        for window in windows
        for strategy_profile in strategy_profiles
    ]


def build_command(cell: WalkForwardCell) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        "scripts.run_bt_run_agent",
        "--profile",
        cell.profile,
        "--strategy-profile",
        cell.strategy_profile,
        "--warmup-start",
        cell.window.warmup_start,
        "--start",
        cell.window.oos_start,
        "--end",
        cell.window.oos_end,
        "--phase-name",
        cell.window.window_name,
    )


def run_matrix(cells: Sequence[WalkForwardCell]) -> list[WalkForwardRunResult]:
    return [run_cell(cell) for cell in cells]


def run_cell(cell: WalkForwardCell) -> WalkForwardRunResult:
    command = build_command(cell)
    print(f"=== {cell.window.window_name} {cell.strategy_profile} ===")
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
        run_dir = snapshot.output_dir
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        run_dir = find_run_output_dir(run_id, default_runs_root())
        if run_dir is None:
            return failed_result(
                cell,
                command=command,
                returncode=completed.returncode,
                run_id=run_id,
                error=f"Could not load run snapshot: {exc}",
                stdout=completed.stdout,
                stderr=completed.stderr,
            )

    return result_from_run_dir(
        cell,
        command=command,
        returncode=completed.returncode,
        run_id=run_id,
        run_dir=run_dir,
        error=None,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def failed_result(
    cell: WalkForwardCell,
    *,
    command: tuple[str, ...],
    returncode: int | None,
    run_id: str | None,
    error: str,
    stdout: str,
    stderr: str,
) -> WalkForwardRunResult:
    run_dir = find_run_output_dir(run_id, default_runs_root()) if run_id is not None else None
    return result_from_run_dir(
        cell,
        command=command,
        returncode=returncode,
        run_id=run_id,
        run_dir=run_dir,
        error=error,
        stdout=stdout,
        stderr=stderr,
        force_failed=True,
    )


def result_from_run_dir(
    cell: WalkForwardCell,
    *,
    command: tuple[str, ...],
    returncode: int | None,
    run_id: str | None,
    run_dir: Path | None,
    error: str | None,
    stdout: str,
    stderr: str,
    force_failed: bool = False,
) -> WalkForwardRunResult:
    manifest_path = run_dir / "run_manifest.json" if run_dir is not None else None
    summary_path = run_dir / "summary.txt" if run_dir is not None else None
    manifest = load_manifest(manifest_path)
    warnings = tuple(
        str(warning) for warning in manifest.get("warnings", ()) if isinstance(warning, str)
    )
    if manifest_path is None or not manifest_path.exists():
        warnings += ("[WARN] Missing run_manifest.json.",)

    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    phase_metrics = compute_phase_metrics(
        artifacts,
        _str_or_default(manifest.get("phase_start"), cell.window.oos_start),
        _str_or_default(manifest.get("phase_end"), cell.window.oos_end),
    )
    warnings += phase_metrics_warnings(phase_metrics, artifacts)

    compare = manifest.get("compare") if isinstance(manifest.get("compare"), dict) else {}
    compare_success = _bool_or_none(compare.get("success"))
    compare_matched = _bool_or_none(compare.get("matched"))
    manifest_success = _bool_or_none(manifest.get("success"))
    missing = missing_fields(run_dir, manifest_path, summary_path, artifacts)
    success = (
        False
        if force_failed
        else bool(manifest_success if manifest_success is not None else returncode == 0)
        and compare_success is not False
        and compare_matched is not False
        and "manifest" not in missing
    )

    return WalkForwardRunResult(
        window_name=cell.window.window_name,
        strategy_profile=cell.strategy_profile,
        profile=cell.profile,
        warmup_start=_str_or_default(manifest.get("warmup_start"), cell.window.warmup_start),
        oos_start=_str_or_default(manifest.get("phase_start"), cell.window.oos_start),
        oos_end=_str_or_default(manifest.get("phase_end"), cell.window.oos_end),
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
        runner_compare_point_count=_int_or_none(manifest.get("compare_point_count")),
        effective_backtest_start=_str_or_none(manifest.get("effective_backtest_start")),
        effective_backtest_end=_str_or_none(manifest.get("effective_backtest_end")),
        phase_metrics=phase_metrics,
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


def missing_fields(
    run_dir: Path | None,
    manifest_path: Path | None,
    summary_path: Path | None,
    artifacts: dict[str, Any],
) -> tuple[str, ...]:
    missing = []
    if run_dir is None or not run_dir.exists():
        missing.append("run_dir")
    if manifest_path is None or not manifest_path.exists():
        missing.append("manifest")
    if summary_path is None or not summary_path.exists():
        missing.append("summary")
    for key in ("equity", "bench"):
        value = artifacts.get(key)
        if not isinstance(value, str) or not Path(value).exists():
            missing.append(f"artifact_{key}")
    return tuple(missing)


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
    results: Sequence[WalkForwardRunResult],
    *,
    windows: Sequence[WalkForwardWindow],
    window_mode: str,
    profile: str,
    strategy_profiles: Sequence[str],
    as_of: str,
    report_dir: Path,
) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().isoformat(timespec="seconds")
    (report_dir / SUMMARY_MD_NAME).write_text(
        build_markdown_report(
            results,
            windows=windows,
            generated_at=generated_at,
            strategy_profiles=strategy_profiles,
        ),
        encoding="utf-8",
    )
    (report_dir / SUMMARY_JSON_NAME).write_text(
        json.dumps(
            build_json_report(
                results,
                windows=windows,
                window_mode=window_mode,
                profile=profile,
                strategy_profiles=strategy_profiles,
                as_of=as_of,
                generated_at=generated_at,
            ),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def build_json_report(
    results: Sequence[WalkForwardRunResult],
    *,
    windows: Sequence[WalkForwardWindow],
    window_mode: str,
    profile: str,
    strategy_profiles: Sequence[str],
    as_of: str,
    generated_at: str,
) -> dict[str, Any]:
    warnings = [MEDIUM_COMPARE_NOTE] if profile == "medium" else []
    if len(strategy_profiles) > 1:
        warnings.append(PROFILE_MATRIX_NOTE)
    return {
        "generated_at": generated_at,
        "window_mode": window_mode,
        "profile": profile,
        "strategy_profiles": list(strategy_profiles),
        "as_of": as_of,
        "windows": [asdict(window) for window in windows],
        "matrix": [asdict(result) for result in results],
        "summary": summarize_results(results, windows=windows),
        "warnings": warnings,
    }


def build_markdown_report(
    results: Sequence[WalkForwardRunResult],
    *,
    windows: Sequence[WalkForwardWindow],
    generated_at: str,
    strategy_profiles: Sequence[str],
) -> str:
    lines = [
        "# Walk-forward / OOS Summary",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Note",
        "",
        (
            "This report uses predefined OOS windows. Strategy parameters are not changed "
            "between windows. OOS results are descriptive and must not be used for "
            "after-the-fact parameter selection."
        ),
        "",
        MEDIUM_COMPARE_NOTE,
    ]
    if len(strategy_profiles) > 1:
        lines.extend(("", PROFILE_MATRIX_NOTE))
    lines.extend(
        [
            "",
            "## Windows",
            _md_table(
                ("Window", "Warmup Start", "OOS Start", "OOS End"),
                tuple(
                    (window.window_name, window.warmup_start, window.oos_start, window.oos_end)
                    for window in windows
                ),
            ),
            "",
            "## Executed Matrix",
            _md_table(
                (
                    "Window",
                    "Strategy Profile",
                    "Run ID",
                    "Success",
                    "Compare matched",
                    "Compare message",
                ),
                tuple(
                    (
                        result.window_name,
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
                    "Window",
                    "Runner Compare Points",
                    "Compare Point Count",
                    "Effective Backtest Start",
                    "Effective Backtest End",
                ),
                tuple(
                    (
                        result.window_name,
                        ", ".join(result.runner_compare_points) or "n/a",
                        result.runner_compare_point_count
                        if result.runner_compare_point_count is not None
                        else "n/a",
                        result.effective_backtest_start or "n/a",
                        result.effective_backtest_end or "n/a",
                    )
                    for result in results
                ),
            ),
            "",
            "## OOS Metrics",
            _md_table(
                (
                    "Window",
                    "Portfolio Return",
                    "Benchmark Return",
                    "Relative Return",
                    "Outperformed",
                    "Portfolio CAGR",
                    "Benchmark CAGR",
                    "Relative CAGR",
                    "Portfolio MaxDD",
                    "Benchmark MaxDD",
                    "DD Better",
                    "Sharpe",
                    "Turnover",
                ),
                tuple(_metrics_row(result) for result in results),
            ),
            "",
            "## Summary",
            *summary_lines(summarize_results(results, windows=windows)),
            "",
            "## Interpretation Notes",
            "",
            "* OOS windows are predefined.",
            "* No strategy parameters are changed per window.",
            "* Phase metrics are computed from equity/benchmark segments clipped to OOS windows.",
            (
                "* Compare points show technical BT/RUN parity checks but may not cover every "
                "rebalance when using profile `medium`."
            ),
            "* Risk-metrics integration is a follow-up; this report uses phase_metrics only.",
            *result_notes(results),
            "",
        ]
    )
    return "\n".join(lines)


def _metrics_row(result: WalkForwardRunResult) -> tuple[object, ...]:
    metrics = result.phase_metrics
    return (
        result.window_name,
        _fmt_pct(metrics["portfolio_total_return"]),
        _fmt_pct(metrics["benchmark_total_return"]),
        _fmt_pct(metrics["relative_total_return"]),
        _bool_or_na(_bool_or_none(metrics["outperformed_benchmark"])),
        _fmt_pct(metrics["portfolio_cagr"]),
        _fmt_pct(metrics["benchmark_cagr"]),
        _fmt_pct(metrics["relative_cagr"]),
        _fmt_pct(metrics["portfolio_max_drawdown"]),
        _fmt_pct(metrics["benchmark_max_drawdown"]),
        _bool_or_na(_bool_or_none(metrics["drawdown_better_than_benchmark"])),
        _fmt_num(metrics["portfolio_sharpe"]),
        _fmt_pct(metrics["turnover"]),
    )


def summarize_results(
    results: Sequence[WalkForwardRunResult],
    *,
    windows: Sequence[WalkForwardWindow],
) -> dict[str, Any]:
    relative_values = [
        (result.phase_metrics.get("relative_total_return"), result.window_name)
        for result in results
        if isinstance(result.phase_metrics.get("relative_total_return"), float)
    ]
    worst_relative_return = None
    worst_window = None
    if relative_values:
        worst_relative_return, worst_window = min(relative_values, key=lambda item: item[0])
    return {
        "runs_total": len(results),
        "runs_successful": sum(1 for result in results if result.success),
        "runs_failed": sum(1 for result in results if not result.success),
        "compare_mismatched": sum(1 for result in results if result.compare_matched is False),
        "outperformed_windows": sum(
            1 for result in results if result.phase_metrics.get("outperformed_benchmark") is True
        ),
        "windows_total": len(windows),
        "worst_relative_return": worst_relative_return,
        "worst_window": worst_window,
    }


def summary_lines(summary: dict[str, Any]) -> list[str]:
    return [
        f"* Runs total: {summary['runs_total']}",
        f"* Runs successful: {summary['runs_successful']}",
        f"* Runs failed: {summary['runs_failed']}",
        f"* Compare mismatched: {summary['compare_mismatched']}",
        f"* Outperformed windows: {summary['outperformed_windows']}",
        f"* Worst relative return: {_fmt_pct(summary['worst_relative_return'])}",
        f"* Worst window: {summary['worst_window'] or 'n/a'}",
    ]


def result_notes(results: Sequence[WalkForwardRunResult]) -> list[str]:
    notes = []
    for result in results:
        label = f"{result.window_name}/{result.strategy_profile}"
        if result.error:
            notes.append(f"* {label}: error: {result.error}")
        if result.missing:
            notes.append(f"* {label}: missing: {', '.join(result.missing)}")
        if result.warnings:
            notes.append(f"* {label}: warnings: {_single_line(' | '.join(result.warnings))}")
        if result.stderr_excerpt:
            notes.append(f"* {label}: stderr excerpt: `{_single_line(result.stderr_excerpt)}`")
    return notes


def _parse_iso_date(value: str) -> str:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD date, got {value!r}") from exc
    return value


def _bool_or_none(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _bool_or_na(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "true" if value else "false"


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _single_line(value: str) -> str:
    return " ".join(value.split())


def _str_or_default(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from scripts.compare_runs import (
    default_decisions_root,
    default_runs_root,
    find_run_output_dir,
    load_run_snapshot,
)
from scripts.run_profile_compare_v1 import _fmt_num, _fmt_pct, _md_table
from scripts.strategy_profiles import available_strategy_profile_names

DEFAULT_PROFILES = ("short", "medium", "long")
DEFAULT_STRATEGY_PROFILES = ("conservative_v1", "balanced_v1", "offensive_v1")
REPORT_DIR = Path("reports") / "strategy_analysis" / "profile_robustness_matrix"
SUMMARY_MD_NAME = "profile_robustness_matrix_summary.md"
SUMMARY_JSON_NAME = "profile_robustness_matrix_summary.json"


@dataclass(frozen=True, slots=True)
class MatrixCell:
    profile: str
    strategy_profile: str


@dataclass(frozen=True, slots=True)
class MatrixRunResult:
    profile: str
    strategy_profile: str
    command: tuple[str, ...]
    returncode: int | None
    run_id: str | None
    run_dir: str | None
    manifest_path: str | None
    summary_path: str | None
    compare_matched: bool | None
    success: bool
    error: str | None
    stdout_excerpt: str | None
    stderr_excerpt: str | None
    metrics: dict[str, float | None]
    missing: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the profile robustness matrix via scripts.run_bt_run_agent."
    )
    parser.add_argument(
        "--profiles",
        default=",".join(DEFAULT_PROFILES),
        help="Comma-separated period profiles. Defaults to short,medium,long.",
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
        "--report-dir",
        default=str(REPORT_DIR),
        help="Directory for robustness matrix reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profiles = parse_csv_arg(args.profiles)
    strategy_profiles = parse_csv_arg(args.strategy_profiles)
    validate_known_strategy_profiles(strategy_profiles)
    report_dir = Path(args.report_dir)

    results = run_matrix(build_matrix(profiles, strategy_profiles))
    write_reports(results, report_dir=report_dir)

    failed_count = sum(1 for result in results if not result.success)
    print(f"Matrix runs completed: {len(results) - failed_count} succeeded, {failed_count} failed")
    print(f"Markdown report: {(report_dir / SUMMARY_MD_NAME).as_posix()}")
    print(f"JSON report: {(report_dir / SUMMARY_JSON_NAME).as_posix()}")


def parse_csv_arg(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.replace(" ", ",").split(",") if item.strip())


def build_matrix(
    profiles: Sequence[str] = DEFAULT_PROFILES,
    strategy_profiles: Sequence[str] = DEFAULT_STRATEGY_PROFILES,
) -> list[MatrixCell]:
    return [
        MatrixCell(profile=profile, strategy_profile=strategy_profile)
        for profile in profiles
        for strategy_profile in strategy_profiles
    ]


def build_command(cell: MatrixCell) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        "scripts.run_bt_run_agent",
        "--profile",
        cell.profile,
        "--strategy-profile",
        cell.strategy_profile,
    )


def run_matrix(cells: Sequence[MatrixCell]) -> list[MatrixRunResult]:
    return [run_cell(cell) for cell in cells]


def run_cell(cell: MatrixCell) -> MatrixRunResult:
    command = build_command(cell)
    print(f"=== {cell.profile.upper()} {cell.strategy_profile} ===")
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
    compare_matched = load_compare_matched(manifest_path)
    metrics = metrics_from_snapshot(snapshot)
    missing = missing_fields(run_dir, manifest_path, summary_path, metrics)

    return MatrixRunResult(
        profile=cell.profile,
        strategy_profile=cell.strategy_profile,
        command=command,
        returncode=completed.returncode,
        run_id=run_id,
        run_dir=str(run_dir) if run_dir is not None else None,
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        summary_path=str(summary_path) if summary_path is not None else None,
        compare_matched=compare_matched,
        success=completed.returncode == 0 and compare_matched is not False,
        error=None,
        stdout_excerpt=excerpt(completed.stdout),
        stderr_excerpt=excerpt(completed.stderr),
        metrics=metrics,
        missing=missing,
    )


def failed_result(
    cell: MatrixCell,
    *,
    command: tuple[str, ...],
    returncode: int | None,
    run_id: str | None,
    error: str,
    stdout: str,
    stderr: str,
) -> MatrixRunResult:
    run_dir = find_run_output_dir(run_id, default_runs_root()) if run_id is not None else None
    manifest_path = run_dir / "run_manifest.json" if run_dir is not None else None
    summary_path = run_dir / "summary.txt" if run_dir is not None else None
    return MatrixRunResult(
        profile=cell.profile,
        strategy_profile=cell.strategy_profile,
        command=command,
        returncode=returncode,
        run_id=run_id,
        run_dir=str(run_dir) if run_dir is not None else None,
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        summary_path=str(summary_path) if summary_path is not None else None,
        compare_matched=load_compare_matched(manifest_path),
        success=False,
        error=error,
        stdout_excerpt=excerpt(stdout),
        stderr_excerpt=excerpt(stderr),
        metrics=empty_metrics(),
        missing=missing_fields(run_dir, manifest_path, summary_path, empty_metrics()),
    )


def extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("run_id:"):
            return line.split(":", 1)[1].strip()
    return None


def load_compare_matched(manifest_path: Path | None) -> bool | None:
    if manifest_path is None or not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    compare = payload.get("compare")
    if not isinstance(compare, dict):
        return None
    matched = compare.get("matched")
    return matched if isinstance(matched, bool) else None


def metrics_from_snapshot(snapshot: Any) -> dict[str, float | None]:
    return {
        "total_return": snapshot.performance.total_return_pct,
        "cagr": snapshot.performance.cagr_pct,
        "max_drawdown": snapshot.performance.max_drawdown_pct,
        "sharpe": snapshot.performance.sharpe_ratio,
        "volatility": snapshot.performance.volatility_pct,
        "turnover": snapshot.performance.turnover_pct,
        "benchmark_cagr": snapshot.benchmark.benchmark_cagr_pct,
        "benchmark_max_drawdown": snapshot.benchmark.benchmark_max_drawdown_pct,
    }


def empty_metrics() -> dict[str, float | None]:
    return {
        "total_return": None,
        "cagr": None,
        "max_drawdown": None,
        "sharpe": None,
        "volatility": None,
        "turnover": None,
        "benchmark_cagr": None,
        "benchmark_max_drawdown": None,
    }


def missing_fields(
    run_dir: Path | None,
    manifest_path: Path | None,
    summary_path: Path | None,
    metrics: dict[str, float | None],
) -> tuple[str, ...]:
    missing = []
    if run_dir is None or not run_dir.exists():
        missing.append("run_dir")
    if manifest_path is None or not manifest_path.exists():
        missing.append("manifest")
    if summary_path is None or not summary_path.exists():
        missing.append("summary")
    missing.extend(key for key, value in metrics.items() if value is None)
    return tuple(missing)


def write_reports(results: Sequence[MatrixRunResult], *, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().isoformat(timespec="seconds")
    (report_dir / SUMMARY_MD_NAME).write_text(
        build_markdown_report(results, generated_at=generated_at),
        encoding="utf-8",
    )
    (report_dir / SUMMARY_JSON_NAME).write_text(
        json.dumps(
            build_json_report(results, generated_at=generated_at),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def build_markdown_report(results: Sequence[MatrixRunResult], *, generated_at: str) -> str:
    lines = [
        "# Profile Robustness Matrix",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Executed Matrix",
        _md_table(
            ("Zeitraumprofil", "Strategieprofil", "Run ID", "Compare matched"),
            tuple(
                (
                    result.profile,
                    result.strategy_profile,
                    result.run_id or "n/a",
                    _bool_or_na(result.compare_matched),
                )
                for result in results
            ),
        ),
        "",
        "## Metrics",
        _md_table(
            (
                "Zeitraumprofil",
                "Strategieprofil",
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
        "## Hinweise",
        *build_hints(results),
        "",
    ]
    return "\n".join(lines)


def _metrics_row(result: MatrixRunResult) -> tuple[object, ...]:
    metrics = result.metrics
    return (
        result.profile,
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


def build_hints(results: Sequence[MatrixRunResult]) -> list[str]:
    hints = []
    for result in results:
        label = f"{result.profile}/{result.strategy_profile}"
        if result.compare_matched is False:
            hints.append(f"- {label}: compare.matched = false")
        if result.error:
            hints.append(f"- {label}: error: {result.error}")
        if result.missing:
            hints.append(f"- {label}: missing: {', '.join(result.missing)}")
        if result.stderr_excerpt:
            hints.append(f"- {label}: stderr excerpt: `{_single_line(result.stderr_excerpt)}`")
    return hints or ["- Keine automatischen Hinweise."]


def build_json_report(results: Sequence[MatrixRunResult], *, generated_at: str) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "profiles": sorted({result.profile for result in results}),
        "strategy_profiles": sorted({result.strategy_profile for result in results}),
        "summary": {
            "total": len(results),
            "success": sum(1 for result in results if result.success),
            "failed": sum(1 for result in results if not result.success),
            "compare_mismatched": sum(1 for result in results if result.compare_matched is False),
        },
        "matrix": [asdict(result) for result in results],
    }


def excerpt(text: str, *, max_chars: int = 500) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None
    return stripped[-max_chars:]


def _bool_or_na(value: bool | None) -> str:
    if value is None:
        return "n/a"
    return "true" if value else "false"


def _single_line(value: str) -> str:
    return " ".join(value.split())


def validate_known_strategy_profiles(strategy_profiles: Sequence[str]) -> None:
    known = set(available_strategy_profile_names())
    unknown = sorted(set(strategy_profiles) - known)
    if unknown:
        raise SystemExit(
            "Unknown strategy profiles: "
            f"{', '.join(unknown)}. Known profiles: {', '.join(sorted(known)) or 'none'}"
        )


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import csv
import io
import json
import pstats
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from app.agents.bt_run_agent import BtRunAgentInput, BtRunCompareInput
from app.bootstrap.bt_run_container import build_bt_run_agent
from app.domain.bt_run.run_context import RunProfile
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput
from scripts.run_bt_run_agent import (
    build_backtest_profile_args,
    build_run_manifest,
    copy_referenced_backtest_artifacts,
    resolve_profile_behavior,
)
from scripts.run_bt_run_agent import build_run_context as build_default_run_context


OUTPUT_PATH_LABELS = ("Equity", "Positions", "Trades", "Bench", "Summary")


@dataclass(frozen=True, slots=True)
class ProfileFiles:
    backtest_stats: Path
    runner_stats: Path
    backtest_metrics: Path
    runner_metrics: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile aktien_oop Backtester, Runner, Compare and report generation."
    )
    parser.add_argument(
        "--profile",
        choices=("short", "problem", "medium", "long"),
        default="short",
        help="Existing BT/RUN profile to execute. Defaults to short.",
    )
    parser.add_argument(
        "--ai-agents-dir",
        type=Path,
        default=None,
        help="Override AiAgents root. Defaults to the path used by scripts.run_bt_run_agent.",
    )
    parser.add_argument(
        "--top-functions",
        type=int,
        default=20,
        help="Number of cProfile functions to include in the raw report files.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = RunProfile(args.profile)
    context = build_default_run_context(profile)
    if args.ai_agents_dir is not None:
        context = _context_with_ai_agents_dir(context, args.ai_agents_dir)

    behavior = resolve_profile_behavior(profile)
    backtest_profile_args = build_backtest_profile_args(
        behavior,
        backtest_config_path=context.backtest_config_path,
    )

    context.output_dir.mkdir(parents=True, exist_ok=True)
    context.decisions_dir.mkdir(parents=True, exist_ok=True)
    profile_dir = context.output_dir / "runtime_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    files = ProfileFiles(
        backtest_stats=profile_dir / "backtest.cprofile",
        runner_stats=profile_dir / "runner.cprofile",
        backtest_metrics=profile_dir / "backtest_metrics.json",
        runner_metrics=profile_dir / "runner_metrics.json",
    )

    backtest_command = _profiled_python_command(
        files.backtest_stats,
        files.backtest_metrics,
        "aktien_oop.backtest",
        (
            "--config",
            str(context.backtest_config_path),
            "--decisions-dir",
            str(context.decisions_dir),
            *backtest_profile_args,
        ),
    )
    runner_command = _profiled_python_command(
        files.runner_stats,
        files.runner_metrics,
        "aktien_oop.main",
        (
            "--config",
            str(context.runner_config_path),
            "--decisions-dir",
            str(context.decisions_dir),
            *behavior.runner_extra_args,
        ),
    )

    print("run_id:", context.run_id)
    print("profile:", profile.value)
    print("output_dir:", context.output_dir)
    print("profile_dir:", profile_dir)
    print("aktien_oop_dir:", context.aktien_oop_dir)

    agent = build_bt_run_agent(context.decisions_dir)
    started_at = perf_counter()
    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=backtest_command,
                cwd=context.ai_agents_dir,
                config_path=context.backtest_config_path,
            ),
            runner_input=RunRunnerToolInput(
                command=runner_command,
                cwd=context.ai_agents_dir,
                config_path=context.runner_config_path,
            ),
            compare_input=BtRunCompareInput(
                bps_tolerance=context.bps_tolerance,
                ignore_cash=context.ignore_cash,
            ),
            compare_mode=context.compare_mode,
            seed_runner_previous_from_backtest=True,
            compare_point_count=behavior.compare_point_count,
        )
    )
    execute_seconds = perf_counter() - started_at

    report_started_at = perf_counter()
    (context.output_dir / "backtest_stdout.txt").write_text(result.backtest.stdout, encoding="utf-8")
    (context.output_dir / "backtest_stderr.txt").write_text(result.backtest.stderr, encoding="utf-8")
    (context.output_dir / "runner_stdout.txt").write_text(result.runner.stdout, encoding="utf-8")
    (context.output_dir / "runner_stderr.txt").write_text(result.runner.stderr, encoding="utf-8")
    artifact_paths = copy_referenced_backtest_artifacts(context, result)
    manifest = build_run_manifest(context, result)
    manifest["artifacts"] = artifact_paths
    (context.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    report_seconds = perf_counter() - report_started_at
    total_seconds = execute_seconds + report_seconds

    backtest_metrics = _read_json(files.backtest_metrics)
    runner_metrics = _read_json(files.runner_metrics)
    phase_seconds = _build_phase_seconds(
        total_seconds=total_seconds,
        execute_seconds=execute_seconds,
        report_seconds=report_seconds,
        result=result,
        backtest_metrics=backtest_metrics,
        runner_metrics=runner_metrics,
    )
    dimensions = _collect_dimensions(
        context=context,
        result=result,
        artifact_paths={k: Path(v) for k, v in artifact_paths.items()},
        backtest_metrics=backtest_metrics,
        runner_metrics=runner_metrics,
    )
    hotspots = _top_hotspots((files.backtest_stats, files.runner_stats), limit=5)

    _write_pstats_report(files.backtest_stats, profile_dir / "backtest_pstats.txt", args.top_functions)
    _write_pstats_report(files.runner_stats, profile_dir / "runner_pstats.txt", args.top_functions)
    report = _build_markdown_report(
        context=context,
        result=result,
        total_seconds=total_seconds,
        phase_seconds=phase_seconds,
        dimensions=dimensions,
        hotspots=hotspots,
        profile_dir=profile_dir,
    )
    report_path = profile_dir / "runtime_report.md"
    report_path.write_text(report, encoding="utf-8")
    summary_path = profile_dir / "runtime_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_id": context.run_id,
                "success": result.success,
                "total_seconds": total_seconds,
                "phase_seconds": phase_seconds,
                "dimensions": dimensions,
                "hotspots": hotspots,
                "profile_dir": str(profile_dir),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(report)
    print("Runtime report:", report_path)
    print("Runtime JSON:", summary_path)


def _context_with_ai_agents_dir(context: Any, ai_agents_dir: Path) -> Any:
    from dataclasses import replace

    aktien_oop_dir = ai_agents_dir / "aktien_oop"
    return replace(
        context,
        ai_agents_dir=ai_agents_dir,
        aktien_oop_dir=aktien_oop_dir,
        decisions_dir=aktien_oop_dir / "decisions" / context.run_id,
        output_dir=ai_agents_dir / "automation_runs" / context.run_label,
        backtest_config_path=aktien_oop_dir / "backtest_config.toml",
        runner_config_path=aktien_oop_dir / "configs" / "runner_config.toml",
    )


def _profiled_python_command(
    stats_path: Path,
    metrics_path: Path,
    module: str,
    module_args: tuple[str, ...],
) -> tuple[str, ...]:
    child_path = Path(__file__).with_name("_profile_child.py").resolve()
    return (
        sys.executable,
        "-B",
        "-m",
        "cProfile",
        "-o",
        str(stats_path),
        str(child_path),
        "--module",
        module,
        "--metrics-out",
        str(metrics_path),
        "--",
        *module_args,
    )


def _build_phase_seconds(
    *,
    total_seconds: float,
    execute_seconds: float,
    report_seconds: float,
    result: Any,
    backtest_metrics: dict[str, Any],
    runner_metrics: dict[str, Any],
) -> dict[str, float]:
    backtest_seconds = float(result.backtest.duration_seconds or 0.0)
    runner_seconds = float(result.runner.duration_seconds or 0.0)
    compare_seconds = max(execute_seconds - backtest_seconds - runner_seconds, 0.0)
    phase_seconds = {
        "total": total_seconds,
        "backtester_process": backtest_seconds,
        "runner_process": runner_seconds,
        "compare_and_orchestration": compare_seconds,
        "report_manifest_artifacts": report_seconds,
    }
    child_phase_names = (
        "data_loading",
        "scoring",
        "benchmark",
        "rebalance_loop",
        "finalization",
        "report_decision_bundles",
    )
    for phase_name in child_phase_names:
        phase_seconds[phase_name] = _metric_phase(backtest_metrics, phase_name) + _metric_phase(
            runner_metrics, phase_name
        )
    return {key: round(value, 6) for key, value in phase_seconds.items()}


def _metric_phase(metrics: dict[str, Any], phase: str) -> float:
    value = (metrics.get("phase_seconds") or {}).get(phase, 0.0)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _collect_dimensions(
    *,
    context: Any,
    result: Any,
    artifact_paths: dict[str, Path],
    backtest_metrics: dict[str, Any],
    runner_metrics: dict[str, Any],
) -> dict[str, Any]:
    price_shapes = list(backtest_metrics.get("price_shapes") or []) + list(
        runner_metrics.get("price_shapes") or []
    )
    largest_shape = max(price_shapes, key=lambda item: int(item.get("rows", 0)) * int(item.get("columns", 0)), default={})
    return {
        "ticker_count": _ticker_count(context.backtest_config_path, context.ai_agents_dir),
        "price_rows": largest_shape.get("rows"),
        "price_columns": largest_shape.get("columns"),
        "price_shape_source": largest_shape.get("source"),
        "price_shape_samples": price_shapes[:10],
        "rebalance_dates": _count_decision_bundles(context.decisions_dir, "BT_"),
        "bt_decision_bundles": _count_decision_bundles(context.decisions_dir, "BT_"),
        "run_decision_bundles": _count_decision_bundles(context.decisions_dir, "RUN_"),
        "equity_rows": _csv_data_rows(artifact_paths.get("equity")),
        "benchmark_rows": _csv_data_rows(artifact_paths.get("bench")),
        "positions_rows": _csv_data_rows(artifact_paths.get("positions")),
        "trades_rows": _csv_data_rows(artifact_paths.get("trades")),
        "compare_success": result.compare.success,
        "compare_matched": result.compare.matched,
    }


def _ticker_count(config_path: Path, ai_agents_dir: Path) -> int | None:
    if not config_path.exists():
        return None
    with config_path.open("rb") as file_obj:
        config = tomllib.load(file_obj)
    universe = config.get("universe") if isinstance(config.get("universe"), dict) else {}
    tickers_file = universe.get("tickers_file") or config.get("tickers_file")
    if not tickers_file:
        return None
    path = Path(str(tickers_file))
    if not path.is_absolute():
        path = ai_agents_dir / path
    if not path.exists():
        return None
    return sum(
        1
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def _count_decision_bundles(path: Path, prefix: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.glob(f"{prefix}*.json") if item.is_file())


def _csv_data_rows(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    count = 0
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        for row in csv.reader(line for line in file_obj if not line.lstrip().startswith("#")):
            if row:
                count += 1
    return max(count - 1, 0)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _top_hotspots(stats_paths: tuple[Path, ...], *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stats_path in stats_paths:
        if not stats_path.exists():
            continue
        stats = pstats.Stats(str(stats_path))
        process_name = stats_path.stem
        for (filename, line_no, func_name), (_, _, total_time, cumulative_time, _) in stats.stats.items():
            if func_name in {"<module>", "<built-in method builtins.exec>"}:
                continue
            if Path(filename).name in {"_profile_child.py", "cProfile.py", "profile.py"}:
                continue
            if "site-packages" in filename and "pandas" not in filename and "yfinance" not in filename:
                continue
            rows.append(
                {
                    "process": process_name,
                    "function": f"{Path(filename).name}:{line_no}:{func_name}",
                    "total_seconds": round(float(total_time), 6),
                    "cumulative_seconds": round(float(cumulative_time), 6),
                }
            )
    return sorted(rows, key=lambda item: item["cumulative_seconds"], reverse=True)[:limit]


def _write_pstats_report(stats_path: Path, output_path: Path, limit: int) -> None:
    if not stats_path.exists():
        return
    stream = io.StringIO()
    stats = pstats.Stats(str(stats_path), stream=stream).sort_stats("cumtime")
    stats.print_stats(limit)
    output_path.write_text(stream.getvalue(), encoding="utf-8")


def _build_markdown_report(
    *,
    context: Any,
    result: Any,
    total_seconds: float,
    phase_seconds: dict[str, float],
    dimensions: dict[str, Any],
    hotspots: list[dict[str, Any]],
    profile_dir: Path,
) -> str:
    lines = [
        "# Runtime Profiling Report",
        "",
        f"run_id: {context.run_id}",
        f"profile: {context.profile.value}",
        f"success: {result.success}",
        f"total_seconds: {total_seconds:.3f}",
        f"profile_dir: {profile_dir}",
        "",
        "## Dimensions",
        _table(("Metric", "Value"), tuple((key, value) for key, value in dimensions.items() if key != "price_shape_samples")),
        "",
        "## Phase Timings",
        _table(
            ("Phase", "Seconds"),
            tuple((key, f"{value:.3f}") for key, value in phase_seconds.items()),
        ),
        "",
        "## Top 5 Hotspots",
        _table(
            ("Process", "Function", "Cum seconds", "Own seconds"),
            tuple(
                (
                    item["process"],
                    item["function"],
                    f"{item['cumulative_seconds']:.3f}",
                    f"{item['total_seconds']:.3f}",
                )
                for item in hotspots
            ),
        ),
        "",
        "## Assessment",
        *_assessment_lines(phase_seconds, hotspots),
    ]
    return "\n".join(lines)


def _assessment_lines(phase_seconds: dict[str, float], hotspots: list[dict[str, Any]]) -> list[str]:
    sorted_phases = sorted(
        ((key, value) for key, value in phase_seconds.items() if key != "total"),
        key=lambda item: item[1],
        reverse=True,
    )
    biggest = ", ".join(f"{key}={value:.2f}s" for key, value in sorted_phases[:5])
    hotspot_text = ", ".join(str(item["function"]) for item in hotspots[:3]) or "n/a"
    return [
        f"- Top phase candidates: {biggest}",
        f"- Likely causes: repeated market-data loads, repeated scoring per rebalance/as_of, CSV/JSON artifact writes, and compare bundle parsing. Check the raw pstats before changing code.",
        f"- Concrete optimization candidates: cache immutable price/benchmark data per matrix run; reuse score windows across repeated BT/RUN runs; batch decision/report writes where parity does not depend on intermediate files; reduce repeated config/universe parsing.",
        f"- Low-risk optimizations: read-only cache for downloaded price frames keyed by tickers/date/adjusted, avoiding duplicate benchmark downloads, and report generation after all matrix runs.",
        f"- Parity-risk optimizations: changing rebalance-loop order, scoring/vectorization details, rank tie-breaks, volatility windows, previous-position seeding, or decision-bundle schema/timing.",
        f"- Current cProfile leaders: {hotspot_text}",
    ]


def _table(headers: tuple[str, ...], rows: tuple[tuple[Any, ...], ...]) -> str:
    if not rows:
        return "n/a"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_display(value) for value in row) + " |")
    return "\n".join(lines)


def _display(value: Any) -> str:
    return "n/a" if value is None else str(value)


if __name__ == "__main__":
    main()

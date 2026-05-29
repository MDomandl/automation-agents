from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.compare_runs import (
    default_decisions_root,
    default_runs_root,
    load_run_snapshot,
)
from scripts.run_max_per_sector_testmatrix import (
    SectorMetrics,
    _format_sector_distribution,
    build_sector_metrics,
    replace_sector_limits,
)
from scripts.run_sp500_testmatrix import (
    PROFILE_NAMES,
    UNIVERSES,
    _replace_universe_section,
    default_ai_agents_root,
)
from scripts.run_top_k_testmatrix import (
    _fmt_num,
    _fmt_pct,
    _md_table,
    _snapshot_success,
    replace_top_k,
)


BALANCED_TOP_K = 15
BALANCED_MAX_PER_SECTOR = 2
BALANCED_BENCHMARK = "SXR8.DE"
REPORT_DIR = Path("reports") / "strategy_analysis" / "max_turnover_cap"
TURNOVER_VARIANTS = (
    ("sehr ruhig", 0.20, "turnover_020"),
    ("ausgewogen", 0.35, "turnover_035"),
    ("flexibel", 0.50, "turnover_050"),
    ("off", 0.0, "turnover_off"),
)


@dataclass(frozen=True, slots=True)
class TurnoverVariant:
    name: str
    max_turnover_cap: float
    file_stem: str


@dataclass(frozen=True, slots=True)
class TurnoverRunResult:
    test_id: str
    turnover_variant: str
    max_turnover_cap: float
    profile: str
    run_id: str
    report_path: Path
    total_return_pct: float | None
    cagr_pct: float | None
    alpha_pct: float | None
    max_drawdown_pct: float | None
    volatility_pct: float | None
    sharpe_ratio: float | None
    turnover_pct: float | None
    trades_count: int | None
    benchmark_cagr_pct: float | None
    benchmark_max_drawdown_pct: float | None
    benchmark_sharpe_ratio: float | None
    up_capture_ratio: float | None
    down_capture_ratio: float | None
    success: bool
    sector_metrics: SectorMetrics = field(default_factory=SectorMetrics)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sp500 top_k=15 max_turnover_cap sensitivity matrix."
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=PROFILE_NAMES,
        default=list(PROFILE_NAMES),
        help="Profiles to run. Defaults to short medium long.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(REPORT_DIR),
        help="Directory for max_turnover_cap reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ai_agents_dir = default_ai_agents_root()
    aktien_oop_dir = ai_agents_dir / "aktien_oop"
    backtest_config_path = aktien_oop_dir / "backtest_config.toml"
    runner_config_path = aktien_oop_dir / "configs" / "runner_config.toml"
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    original_backtest_config = backtest_config_path.read_text(encoding="utf-8")
    original_runner_config = runner_config_path.read_text(encoding="utf-8")

    results: list[TurnoverRunResult] = []
    try:
        test_index = 1
        for variant in _variants():
            for profile in args.profiles:
                test_id = f"T{test_index}"
                test_index += 1
                print(
                    f"=== {test_id} {variant.name} "
                    f"max_turnover_cap={_turnover_value(variant.max_turnover_cap)} "
                    f"{profile.upper()} ==="
                )
                run_id = _run_for_turnover_variant(
                    profile=profile,
                    variant=variant,
                    backtest_config_path=backtest_config_path,
                    runner_config_path=runner_config_path,
                )
                snapshot = load_run_snapshot(
                    run_id,
                    runs_root=default_runs_root(),
                    decisions_root=default_decisions_root(),
                )
                report_path = report_dir / f"{variant.file_stem}_{profile.upper()}.md"
                report_path.write_text(
                    build_run_report(
                        test_id=test_id,
                        variant=variant,
                        profile=profile,
                        snapshot=snapshot,
                    ),
                    encoding="utf-8",
                )
                result = _build_result(
                    test_id=test_id,
                    variant=variant,
                    profile=profile,
                    run_id=run_id,
                    report_path=report_path,
                    snapshot=snapshot,
                )
                results.append(result)
                print(f"run_id: {run_id}")
                print(f"report: {report_path.as_posix()}")
                print()
    finally:
        backtest_config_path.write_text(original_backtest_config, encoding="utf-8")
        runner_config_path.write_text(original_runner_config, encoding="utf-8")

    summary_path = report_dir / "max_turnover_cap_summary.md"
    summary_path.write_text(build_summary(results), encoding="utf-8")
    print("Summary written:")
    print(summary_path.as_posix())


def _variants() -> tuple[TurnoverVariant, ...]:
    return tuple(TurnoverVariant(*variant) for variant in TURNOVER_VARIANTS)


def _run_for_turnover_variant(
    *,
    profile: str,
    variant: TurnoverVariant,
    backtest_config_path: Path,
    runner_config_path: Path,
) -> str:
    _write_matrix_config(backtest_config_path, variant)
    _write_matrix_config(runner_config_path, variant)

    command = [sys.executable, "-B", "-m", "scripts.run_bt_run_agent", "--profile", profile]
    print(
        f"Running {profile.upper()} sp500 top_k={BALANCED_TOP_K} "
        f"max_turnover_cap={_turnover_value(variant.max_turnover_cap)}: {' '.join(command)}"
    )
    completed = subprocess.run(
        command,
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Run failed for profile={profile} variant={variant.name}\n"
            f"returncode={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    run_id = _extract_run_id(completed.stdout)
    if run_id is None:
        raise RuntimeError(
            f"Could not extract run_id for profile={profile} variant={variant.name}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    return run_id


def _write_matrix_config(path: Path, variant: TurnoverVariant) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_universe_section(text, UNIVERSES["sp500"])
    text = replace_top_k(text, BALANCED_TOP_K)
    text = replace_sector_limits(
        text,
        use_sector_limits=True,
        max_per_sector=BALANCED_MAX_PER_SECTOR,
    )
    text = replace_max_turnover_cap(text, variant.max_turnover_cap)
    text = replace_benchmark(text, BALANCED_BENCHMARK)
    path.write_text(text, encoding="utf-8")


def replace_max_turnover_cap(text: str, max_turnover_cap: float) -> str:
    lines = text.splitlines()
    result: list[str] = []
    section = ""
    replaced_root = False
    inserted_root = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if not replaced_root and not inserted_root:
                result.append(f"max_turnover_cap = {max_turnover_cap:.2f}")
                inserted_root = True
            section = stripped.strip("[]").strip().lower()
            result.append(line)
            continue
        if stripped.startswith("max_turnover_cap"):
            prefix, _, rest = line.partition("=")
            result.append(f"{prefix}= {max_turnover_cap:.2f}{_comment(rest)}")
            if section == "":
                replaced_root = True
            continue
        result.append(line)
    if not replaced_root and not inserted_root:
        result.extend(["", f"max_turnover_cap = {max_turnover_cap:.2f}"])
    return "\n".join(result) + "\n"


def replace_benchmark(text: str, benchmark: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("benchmark_ticker"):
            prefix, _, rest = line.partition("=")
            result.append(f'{prefix}= "{benchmark}"{_comment(rest)}')
            continue
        if stripped.startswith("benchmark2"):
            prefix, _, rest = line.partition("=")
            result.append(f'{prefix}= "{benchmark}"{_comment(rest)}')
            continue
        result.append(line)
    return "\n".join(result) + "\n"


def _comment(rest: str) -> str:
    if "#" not in rest:
        return ""
    _, _, comment_tail = rest.partition("#")
    return "  #" + comment_tail


def _extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("run_id:"):
            return line.split(":", 1)[1].strip()
    return None


def _build_result(
    *,
    test_id: str,
    variant: TurnoverVariant,
    profile: str,
    run_id: str,
    report_path: Path,
    snapshot: Any,
) -> TurnoverRunResult:
    perf = snapshot.performance
    bench = snapshot.benchmark
    behavior = snapshot.behavior
    return TurnoverRunResult(
        test_id=test_id,
        turnover_variant=variant.name,
        max_turnover_cap=variant.max_turnover_cap,
        profile=profile.upper(),
        run_id=run_id,
        report_path=report_path,
        total_return_pct=perf.total_return_pct,
        cagr_pct=perf.cagr_pct,
        alpha_pct=perf.alpha_pct,
        max_drawdown_pct=perf.max_drawdown_pct,
        volatility_pct=perf.volatility_pct,
        sharpe_ratio=perf.sharpe_ratio,
        turnover_pct=perf.turnover_pct,
        trades_count=behavior.trades_count,
        benchmark_cagr_pct=bench.benchmark_cagr_pct,
        benchmark_max_drawdown_pct=bench.benchmark_max_drawdown_pct,
        benchmark_sharpe_ratio=bench.benchmark_sharpe_ratio,
        up_capture_ratio=bench.up_capture_ratio,
        down_capture_ratio=bench.down_capture_ratio,
        success=_snapshot_success(snapshot),
        sector_metrics=build_sector_metrics(snapshot),
    )


def build_run_report(
    *,
    test_id: str,
    variant: TurnoverVariant,
    profile: str,
    snapshot: Any,
) -> str:
    perf = snapshot.performance
    bench = snapshot.benchmark
    behavior = snapshot.behavior
    sector_metrics = build_sector_metrics(snapshot)
    lines = [
        "# max_turnover_cap Run Report",
        "",
        "## Run",
        _md_table(
            ("Metric", "Value"),
            (
                ("test_id", test_id),
                ("universe", "sp500"),
                ("top_k", BALANCED_TOP_K),
                ("use_sector_limits", "true"),
                ("max_per_sector", BALANCED_MAX_PER_SECTOR),
                ("turnover_variant", variant.name),
                ("max_turnover_cap", _turnover_value(variant.max_turnover_cap)),
                ("profile", profile.upper()),
                ("benchmark", BALANCED_BENCHMARK),
                ("run_id", snapshot.run_id),
            ),
        ),
        "",
        "## Performance",
        _md_table(
            ("Metric", "Value"),
            (
                ("total_return_pct", _fmt_pct(perf.total_return_pct)),
                ("cagr_pct", _fmt_pct(perf.cagr_pct)),
                ("alpha_pct", _fmt_pct(perf.alpha_pct)),
                ("max_drawdown_pct", _fmt_pct(perf.max_drawdown_pct)),
                ("volatility_pct", _fmt_pct(perf.volatility_pct)),
                ("sharpe_ratio", _fmt_num(perf.sharpe_ratio)),
                ("turnover_pct", _fmt_pct(perf.turnover_pct)),
                ("trades_count", behavior.trades_count),
            ),
        ),
        "",
        f"## Benchmark ({bench.benchmark_name or 'n/a'})",
        _md_table(
            ("Metric", "Value"),
            (
                ("benchmark_cagr_pct", _fmt_pct(bench.benchmark_cagr_pct)),
                ("benchmark_max_drawdown_pct", _fmt_pct(bench.benchmark_max_drawdown_pct)),
                ("benchmark_sharpe_ratio", _fmt_num(bench.benchmark_sharpe_ratio)),
            ),
        ),
        "",
        "## Benchmark Relation",
        "_Daily return relations; capture ratios use arithmetic mean returns in positive/negative benchmark periods._",
        "",
        _md_table(
            ("Metric", "Value"),
            (
                ("correlation_to_benchmark", _fmt_num(bench.correlation_to_benchmark)),
                ("up_capture_ratio", _fmt_num(bench.up_capture_ratio)),
                ("down_capture_ratio", _fmt_num(bench.down_capture_ratio)),
            ),
        ),
        "",
        "## Sector Metrics",
        _md_table(
            ("Metric", "Value"),
            (
                ("max_sector_weight", _fmt_pct(sector_metrics.max_sector_weight_pct)),
                ("dominant_sector", sector_metrics.dominant_sector or "n/a"),
                ("sector_count", sector_metrics.sector_count),
                ("sector_distribution", _format_sector_distribution(sector_metrics)),
                ("max_sector_positions", sector_metrics.max_sector_positions),
                ("dominant_sector_positions", sector_metrics.dominant_sector_positions),
                ("source", sector_metrics.source),
                ("warning", sector_metrics.warning or "n/a"),
            ),
        ),
        "",
    ]
    return "\n".join(lines)


def build_summary(results: list[TurnoverRunResult]) -> str:
    lines = [
        "# max_turnover_cap Sensitivity Matrix",
        "",
        "Universe: sp500",
        f"top_k: {BALANCED_TOP_K}",
        "use_sector_limits: true",
        f"max_per_sector: {BALANCED_MAX_PER_SECTOR}",
        f"Benchmark: {BALANCED_BENCHMARK}",
        "",
        "## Runs",
        _md_table(
            (
                "turnover_variant",
                "max_turnover_cap",
                "Profile",
                "Run ID",
                "Total Return",
                "CAGR",
                "Alpha",
                "Max Drawdown",
                "Volatility",
                "Sharpe",
                "Turnover",
                "Trades Count",
                "Benchmark CAGR",
                "Benchmark Drawdown",
                "Benchmark Sharpe",
                "Up Capture",
                "Down Capture",
                "Max Sector Weight",
                "Dominant Sector",
                "Sector Count",
            ),
            tuple(_summary_row(result) for result in results),
        ),
        "",
        "## Profile Winners",
        _md_table(
            (
                "Profile",
                "Best Return",
                "Best Drawdown",
                "Best Sharpe",
                "Lowest Turnover",
                "First Assessment",
            ),
            tuple(_winner_row(profile, results) for profile in ("SHORT", "MEDIUM", "LONG")),
        ),
        "",
        "## Reports",
        _md_table(
            ("Test", "Variant", "max_turnover_cap", "Profile", "Run ID", "Report"),
            tuple(
                (
                    result.test_id,
                    result.turnover_variant,
                    _turnover_value(result.max_turnover_cap),
                    result.profile,
                    result.run_id,
                    result.report_path.as_posix(),
                )
                for result in results
            ),
        ),
        "",
        "Raw matrix JSON:",
        "```json",
        json.dumps(_json_results(results), indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def _summary_row(result: TurnoverRunResult) -> tuple[object, ...]:
    sector_metrics = result.sector_metrics
    return (
        result.turnover_variant,
        _turnover_value(result.max_turnover_cap),
        result.profile,
        result.run_id,
        _fmt_pct(result.total_return_pct),
        _fmt_pct(result.cagr_pct),
        _fmt_pct(result.alpha_pct),
        _fmt_pct(result.max_drawdown_pct),
        _fmt_pct(result.volatility_pct),
        _fmt_num(result.sharpe_ratio),
        _fmt_pct(result.turnover_pct),
        result.trades_count if result.trades_count is not None else "n/a",
        _fmt_pct(result.benchmark_cagr_pct),
        _fmt_pct(result.benchmark_max_drawdown_pct),
        _fmt_num(result.benchmark_sharpe_ratio),
        _fmt_num(result.up_capture_ratio),
        _fmt_num(result.down_capture_ratio),
        _fmt_pct(sector_metrics.max_sector_weight_pct),
        sector_metrics.dominant_sector or "n/a",
        sector_metrics.sector_count if sector_metrics.sector_count is not None else "n/a",
    )


def _winner_row(profile: str, results: list[TurnoverRunResult]) -> tuple[object, ...]:
    profile_results = [result for result in results if result.profile == profile]
    best_return = _best_variant(profile_results, "total_return_pct", higher=True)
    best_drawdown = _best_variant(profile_results, "max_drawdown_pct", drawdown=True)
    best_sharpe = _best_variant(profile_results, "sharpe_ratio", higher=True)
    lowest_turnover = _best_variant(profile_results, "turnover_pct", higher=False)
    assessment = _assessment(best_return, best_drawdown, best_sharpe, lowest_turnover)
    return (profile, best_return, best_drawdown, best_sharpe, lowest_turnover, assessment)


def _best_variant(
    results: list[TurnoverRunResult],
    field_name: str,
    *,
    higher: bool = True,
    drawdown: bool = False,
) -> str:
    candidates = []
    for result in results:
        value = getattr(result, field_name)
        if value is None:
            continue
        score = abs(value) if drawdown else value
        candidates.append((score, _variant_label(result)))
    if not candidates:
        return "n/a"
    _, label = min(candidates) if (drawdown or not higher) else max(candidates)
    return label


def _assessment(best_return: str, best_drawdown: str, best_sharpe: str, lowest_turnover: str) -> str:
    if len({best_drawdown, best_sharpe, lowest_turnover}) == 1 and best_drawdown != "n/a":
        return f"{best_drawdown} leads on risk/efficiency."
    if best_return != "n/a" and best_return != best_drawdown:
        return f"Return favors {best_return}; risk favors {best_drawdown}."
    return "Mixed; inspect report details."


def _variant_label(result: TurnoverRunResult) -> str:
    return result.turnover_variant


def _turnover_value(value: float) -> str:
    return "off" if value <= 0 else f"{value:.2f}"


def _json_results(results: list[TurnoverRunResult]) -> list[dict[str, Any]]:
    payload = []
    for result in results:
        item = asdict(result)
        item["max_turnover_cap_label"] = _turnover_value(result.max_turnover_cap)
        item["report_path"] = result.report_path.as_posix()
        payload.append(item)
    return payload


if __name__ == "__main__":
    main()

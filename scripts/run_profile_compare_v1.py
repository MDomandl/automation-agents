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
)
from scripts.run_regime_cash_testmatrix import CashMetrics, build_cash_metrics
from scripts.run_sp500_testmatrix import (
    PROFILE_NAMES,
    default_ai_agents_root,
)
from scripts.run_top_k_testmatrix import (
    _fmt_num,
    _fmt_pct,
    _md_table,
    _snapshot_success,
)
from scripts.strategy_profiles import (
    PROFILE_CONFIG_PATHS,
    StrategyProfile,
    apply_strategy_profile_overlay,
    load_strategy_profile,
)

REPORT_DIR = Path("reports") / "strategy_analysis" / "profile_compare_v1"


@dataclass(frozen=True, slots=True)
class ProfileRunResult:
    test_id: str
    profile_name: str
    profile_label: str
    require_above_sma: bool
    regime_below_action: str
    include_cash: bool
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
    cash_metrics: CashMetrics = field(default_factory=CashMetrics)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run profile comparison v1 for Conservative, Balanced, Offensive."
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=PROFILE_NAMES,
        default=list(PROFILE_NAMES),
        help="Backtest periods to run. Defaults to short medium long.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(REPORT_DIR),
        help="Directory for profile comparison reports.",
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

    results: list[ProfileRunResult] = []
    try:
        test_index = 1
        strategy_profiles = _strategy_profiles()
        for strategy_profile in strategy_profiles:
            for profile in args.profiles:
                test_id = f"P{test_index}"
                test_index += 1
                print(f"=== {test_id} {strategy_profile.label} {profile.upper()} ===")
                run_id = _run_for_strategy_profile(
                    profile=profile,
                    strategy_profile=strategy_profile,
                    backtest_config_path=backtest_config_path,
                    runner_config_path=runner_config_path,
                )
                snapshot = load_run_snapshot(
                    run_id,
                    runs_root=default_runs_root(),
                    decisions_root=default_decisions_root(),
                )
                report_path = report_dir / f"{strategy_profile.file_stem}_{profile.upper()}.md"
                report_path.write_text(
                    build_run_report(
                        test_id=test_id,
                        strategy_profile=strategy_profile,
                        profile=profile,
                        snapshot=snapshot,
                    ),
                    encoding="utf-8",
                )
                result = _build_result(
                    test_id=test_id,
                    strategy_profile=strategy_profile,
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

    summary_path = report_dir / "profile_compare_v1_summary.md"
    summary_path.write_text(
        build_summary(results, strategy_profiles=strategy_profiles),
        encoding="utf-8",
    )
    print("Summary written:")
    print(summary_path.as_posix())


def _strategy_profiles(
    profile_paths: tuple[Path, ...] = PROFILE_CONFIG_PATHS,
) -> tuple[StrategyProfile, ...]:
    return tuple(load_strategy_profile(path) for path in profile_paths)


def _run_for_strategy_profile(
    *,
    profile: str,
    strategy_profile: StrategyProfile,
    backtest_config_path: Path,
    runner_config_path: Path,
) -> str:
    _write_matrix_config(backtest_config_path, strategy_profile)
    _write_matrix_config(runner_config_path, strategy_profile)

    command = [sys.executable, "-B", "-m", "scripts.run_bt_run_agent", "--profile", profile]
    print(f"Running {profile.upper()} {strategy_profile.label}: {' '.join(command)}")
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
            f"Run failed for profile={profile} strategy_profile={strategy_profile.label}\n"
            f"returncode={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    run_id = _extract_run_id(completed.stdout)
    if run_id is None:
        raise RuntimeError(
            f"Could not extract run_id for profile={profile} "
            f"strategy_profile={strategy_profile.label}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    return run_id


def _write_matrix_config(path: Path, strategy_profile: StrategyProfile) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(apply_strategy_profile_overlay(text, strategy_profile), encoding="utf-8")


def build_run_report(
    *,
    test_id: str,
    strategy_profile: StrategyProfile,
    profile: str,
    snapshot: Any,
) -> str:
    result = _build_result(
        test_id=test_id,
        strategy_profile=strategy_profile,
        profile=profile,
        run_id=snapshot.run_id,
        report_path=Path(),
        snapshot=snapshot,
    )
    perf = snapshot.performance
    bench = snapshot.benchmark
    behavior = snapshot.behavior
    sector_metrics = result.sector_metrics
    cash_metrics = result.cash_metrics
    lines = [
        "# Profile Compare v1 Run Report",
        "",
        "## Run",
        _md_table(
            ("Metric", "Value"),
            (
                ("test_id", test_id),
                ("profile", strategy_profile.label),
                ("universe", strategy_profile.universe),
                ("top_k", strategy_profile.top_k),
                ("use_sector_limits", _bool_text(strategy_profile.use_sector_limits)),
                ("max_per_sector", strategy_profile.max_per_sector),
                ("max_turnover_cap", f"{strategy_profile.max_turnover_cap:.2f}"),
                ("benchmark", strategy_profile.benchmark_ticker),
                ("require_above_sma", _bool_text(strategy_profile.require_above_sma)),
                ("regime_below_action", strategy_profile.regime_below_action),
                ("include_cash", _bool_text(strategy_profile.include_cash)),
                ("cash_yield_annual", f"{strategy_profile.cash_yield_annual:.2f}"),
                ("regime_sma_days", strategy_profile.regime_sma_days),
                ("period_profile", profile.upper()),
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
                ("up_capture_ratio", _fmt_num(bench.up_capture_ratio)),
                ("down_capture_ratio", _fmt_num(bench.down_capture_ratio)),
            ),
        ),
        "",
        "## Cash Metrics",
        _md_table(
            ("Metric", "Value"),
            (
                ("average_cash_pct", _fmt_pct(cash_metrics.average_cash_pct)),
                ("max_cash_pct", _fmt_pct(cash_metrics.max_cash_pct)),
                ("time_in_market_pct", _fmt_pct(cash_metrics.time_in_market_pct)),
                ("time_in_cash_pct", _fmt_pct(cash_metrics.time_in_cash_pct)),
                ("warning", cash_metrics.warning or "n/a"),
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
            ),
        ),
        "",
    ]
    return "\n".join(lines)


def _build_result(
    *,
    test_id: str,
    strategy_profile: StrategyProfile,
    profile: str,
    run_id: str,
    report_path: Path,
    snapshot: Any,
) -> ProfileRunResult:
    perf = snapshot.performance
    bench = snapshot.benchmark
    behavior = snapshot.behavior
    return ProfileRunResult(
        test_id=test_id,
        profile_name=strategy_profile.name,
        profile_label=strategy_profile.label,
        require_above_sma=strategy_profile.require_above_sma,
        regime_below_action=strategy_profile.regime_below_action,
        include_cash=strategy_profile.include_cash,
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
        cash_metrics=build_cash_metrics(snapshot),
    )


def build_summary(
    results: list[ProfileRunResult],
    *,
    strategy_profiles: tuple[StrategyProfile, ...] | None = None,
) -> str:
    profile_configs = strategy_profiles or _strategy_profiles()
    first_profile = profile_configs[0]
    lines = [
        "# Profile Compare v1",
        "",
        f"Universe: {first_profile.universe}",
        f"top_k: {first_profile.top_k}",
        f"use_sector_limits: {_bool_text(first_profile.use_sector_limits)}",
        f"max_per_sector: {first_profile.max_per_sector}",
        f"max_turnover_cap: {first_profile.max_turnover_cap:.2f}",
        f"cash_yield_annual: {first_profile.cash_yield_annual:.2f}",
        f"regime_sma_days: {first_profile.regime_sma_days}",
        f"Benchmark: {first_profile.benchmark_ticker}",
        "",
        "## Runs",
        _md_table(
            (
                "profile",
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
                "Average Cash",
                "Max Cash",
                "Time in Market",
                "Time in Cash",
            ),
            tuple(_summary_row(result) for result in results),
        ),
        "",
        "## Bewertung",
        _md_table(
            (
                "Zeitraum",
                "Best Return",
                "Best Drawdown",
                "Best Sharpe",
                "Lowest Down Capture",
                "Lowest Turnover",
                "Erste Einschaetzung",
            ),
            tuple(_winner_row(profile, results) for profile in ("SHORT", "MEDIUM", "LONG")),
        ),
        "",
        "## Config Overrides",
        _md_table(
            ("Profile", "require_above_sma", "regime_below_action", "include_cash"),
            tuple(
                (
                    profile.label,
                    _bool_text(profile.require_above_sma),
                    profile.regime_below_action,
                    _bool_text(profile.include_cash),
                )
                for profile in profile_configs
            ),
        ),
        "",
        "## Reports",
        _md_table(
            ("Test", "profile", "Profile", "Run ID", "Report"),
            tuple(
                (
                    result.test_id,
                    result.profile_label,
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


def _summary_row(result: ProfileRunResult) -> tuple[object, ...]:
    sector_metrics = result.sector_metrics
    cash_metrics = result.cash_metrics
    return (
        result.profile_label,
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
        _fmt_pct(cash_metrics.average_cash_pct),
        _fmt_pct(cash_metrics.max_cash_pct),
        _fmt_pct(cash_metrics.time_in_market_pct),
        _fmt_pct(cash_metrics.time_in_cash_pct),
    )


def _winner_row(profile: str, results: list[ProfileRunResult]) -> tuple[object, ...]:
    profile_results = [result for result in results if result.profile == profile]
    best_return = _best_profile(profile_results, "total_return_pct", higher=True)
    best_drawdown = _best_profile(profile_results, "max_drawdown_pct", drawdown=True)
    best_sharpe = _best_profile(profile_results, "sharpe_ratio", higher=True)
    lowest_down_capture = _best_profile(profile_results, "down_capture_ratio", higher=False)
    lowest_turnover = _best_profile(profile_results, "turnover_pct", higher=False)
    assessment = _assessment(profile_results)
    return (
        profile,
        best_return,
        best_drawdown,
        best_sharpe,
        lowest_down_capture,
        lowest_turnover,
        assessment,
    )


def _best_profile(
    results: list[ProfileRunResult],
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
        candidates.append((score, result.profile_label))
    if not candidates:
        return "n/a"
    _, label = min(candidates) if (drawdown or not higher) else max(candidates)
    return label


def _assessment(results: list[ProfileRunResult]) -> str:
    by_name = {_base_profile_name(result.profile_name): result for result in results}
    conservative = by_name.get("conservative")
    balanced = by_name.get("balanced")
    offensive = by_name.get("offensive")
    if conservative is None or balanced is None or offensive is None:
        return "n/a"

    if _between(
        conservative.cagr_pct,
        balanced.cagr_pct,
        offensive.cagr_pct,
    ) and _between(
        conservative.max_drawdown_pct,
        balanced.max_drawdown_pct,
        offensive.max_drawdown_pct,
        drawdown=True,
    ):
        return "Balanced liegt zwischen Conservative und Offensive."
    if _same_best(balanced, offensive, "max_drawdown_pct", drawdown=True):
        return "Balanced ist beim Drawdown nah an Offensive; Risiko pruefen."
    if _same_best(balanced, conservative, "cagr_pct", drawdown=False):
        return "Balanced ist bei CAGR nah an Conservative; Rendite pruefen."
    return "Gemischt; Detailreports pruefen."


def _between(
    left: float | None,
    middle: float | None,
    right: float | None,
    *,
    drawdown: bool = False,
) -> bool:
    if left is None or middle is None or right is None:
        return False
    values = (abs(left), abs(middle), abs(right)) if drawdown else (left, middle, right)
    low = min(values[0], values[2])
    high = max(values[0], values[2])
    return low <= values[1] <= high


def _same_best(
    left: ProfileRunResult,
    right: ProfileRunResult,
    field_name: str,
    *,
    drawdown: bool,
) -> bool:
    left_value = getattr(left, field_name)
    right_value = getattr(right, field_name)
    if left_value is None or right_value is None:
        return False
    left_score = abs(left_value) if drawdown else left_value
    right_score = abs(right_value) if drawdown else right_value
    tolerance = max(1.0, abs(right_score) * 0.10)
    return abs(left_score - right_score) <= tolerance


def _json_results(results: list[ProfileRunResult]) -> list[dict[str, Any]]:
    payload = []
    for result in results:
        item = asdict(result)
        item["report_path"] = result.report_path.as_posix()
        payload.append(item)
    return payload


def _extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("run_id:"):
            return line.split(":", 1)[1].strip()
    return None


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _profile_file_stem(profile_name: str) -> str:
    return f"profile_{_base_profile_name(profile_name)}"


def _base_profile_name(profile_name: str) -> str:
    return profile_name.removesuffix("_v1")


def _replace_cash_yield_annual(text: str, cash_yield_annual: float) -> str:
    return _replace_top_level_scalar(text, "cash_yield_annual", f"{cash_yield_annual:.2f}")


def _replace_regime_sma_days(text: str, regime_sma_days: int) -> str:
    return _replace_section_scalar(text, "regime", "regime_sma_days", str(regime_sma_days))


def _replace_top_level_scalar(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.strip("[]").strip().lower()
            result.append(line)
            continue
        if section == "" and stripped.startswith(key):
            prefix, _, rest = line.partition("=")
            result.append(f"{prefix}= {value}{_comment(rest)}")
            continue
        result.append(line)
    return "\n".join(result) + "\n"


def _replace_section_scalar(text: str, section_name: str, key: str, value: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.strip("[]").strip().lower()
            result.append(line)
            continue
        if section == section_name and stripped.startswith(key):
            prefix, _, rest = line.partition("=")
            result.append(f"{prefix}= {value}{_comment(rest)}")
            continue
        result.append(line)
    return "\n".join(result) + "\n"


def _comment(rest: str) -> str:
    if "#" not in rest:
        return ""
    _, _, comment_tail = rest.partition("#")
    return "  #" + comment_tail


if __name__ == "__main__":
    main()

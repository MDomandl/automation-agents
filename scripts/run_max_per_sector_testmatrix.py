from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.compare_runs import (
    default_decisions_root,
    default_runs_root,
    load_run_snapshot,
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
REPORT_DIR = Path("reports") / "strategy_analysis" / "max_per_sector"
SECTOR_VARIANTS = (
    ("strict", True, 2, "sector_02"),
    ("standard", True, 3, "sector_03"),
    ("loose", True, 4, "sector_04"),
    ("off", False, None, "sector_off"),
)


@dataclass(frozen=True, slots=True)
class SectorVariant:
    name: str
    use_sector_limits: bool
    max_per_sector: int | None
    file_stem: str


@dataclass(frozen=True, slots=True)
class SectorRunResult:
    test_id: str
    sector_variant: str
    max_per_sector: int | None
    use_sector_limits: bool
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
    benchmark_cagr_pct: float | None
    benchmark_max_drawdown_pct: float | None
    benchmark_sharpe_ratio: float | None
    up_capture_ratio: float | None
    down_capture_ratio: float | None
    success: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sp500 top_k=15 max_per_sector sensitivity matrix."
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
        help="Directory for max_per_sector reports.",
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

    results: list[SectorRunResult] = []
    try:
        test_index = 1
        for variant in _variants():
            for profile in args.profiles:
                test_id = f"S{test_index}"
                test_index += 1
                print(
                    f"=== {test_id} {variant.name} "
                    f"use_sector_limits={variant.use_sector_limits} "
                    f"max_per_sector={variant.max_per_sector or 'n/a'} "
                    f"{profile.upper()} ==="
                )
                run_id = _run_for_sector_variant(
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

    summary_path = report_dir / "max_per_sector_summary.md"
    summary_path.write_text(build_summary(results), encoding="utf-8")
    print("Summary written:")
    print(summary_path.as_posix())


def _variants() -> tuple[SectorVariant, ...]:
    return tuple(SectorVariant(*variant) for variant in SECTOR_VARIANTS)


def _run_for_sector_variant(
    *,
    profile: str,
    variant: SectorVariant,
    backtest_config_path: Path,
    runner_config_path: Path,
) -> str:
    _write_matrix_config(backtest_config_path, variant)
    _write_matrix_config(runner_config_path, variant)

    command = [sys.executable, "-B", "-m", "scripts.run_bt_run_agent", "--profile", profile]
    print(f"Running {profile.upper()} sp500 top_k={BALANCED_TOP_K}: {' '.join(command)}")
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


def _write_matrix_config(path: Path, variant: SectorVariant) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_universe_section(text, UNIVERSES["sp500"])
    text = replace_top_k(text, BALANCED_TOP_K)
    text = replace_sector_limits(
        text,
        use_sector_limits=variant.use_sector_limits,
        max_per_sector=variant.max_per_sector,
    )
    path.write_text(text, encoding="utf-8")


def replace_sector_limits(
    text: str,
    *,
    use_sector_limits: bool,
    max_per_sector: int | None,
) -> str:
    lines = text.splitlines()
    result: list[str] = []
    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.strip("[]").strip().lower()
            result.append(line)
            continue
        if section == "limits" and stripped.startswith("use_sector_limits"):
            prefix, _, rest = line.partition("=")
            result.append(f"{prefix}= {_bool_text(use_sector_limits)}{_comment(rest)}")
            continue
        if section == "limits" and stripped.startswith("max_per_sector"):
            prefix, _, rest = line.partition("=")
            value = 0 if max_per_sector is None else max_per_sector
            result.append(f"{prefix}= {value}{_comment(rest)}")
            continue
        result.append(line)
    return "\n".join(result) + "\n"


def _comment(rest: str) -> str:
    if "#" not in rest:
        return ""
    _, _, comment_tail = rest.partition("#")
    return "  #" + comment_tail


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("run_id:"):
            return line.split(":", 1)[1].strip()
    return None


def _build_result(
    *,
    test_id: str,
    variant: SectorVariant,
    profile: str,
    run_id: str,
    report_path: Path,
    snapshot: Any,
) -> SectorRunResult:
    perf = snapshot.performance
    bench = snapshot.benchmark
    return SectorRunResult(
        test_id=test_id,
        sector_variant=variant.name,
        max_per_sector=variant.max_per_sector,
        use_sector_limits=variant.use_sector_limits,
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
        benchmark_cagr_pct=bench.benchmark_cagr_pct,
        benchmark_max_drawdown_pct=bench.benchmark_max_drawdown_pct,
        benchmark_sharpe_ratio=bench.benchmark_sharpe_ratio,
        up_capture_ratio=bench.up_capture_ratio,
        down_capture_ratio=bench.down_capture_ratio,
        success=_snapshot_success(snapshot),
    )


def build_run_report(*, test_id: str, variant: SectorVariant, profile: str, snapshot: Any) -> str:
    perf = snapshot.performance
    bench = snapshot.benchmark
    lines = [
        "# max_per_sector Run Report",
        "",
        "## Run",
        _md_table(
            ("Metric", "Value"),
            (
                ("test_id", test_id),
                ("universe", "sp500"),
                ("top_k", BALANCED_TOP_K),
                ("sector_variant", variant.name),
                ("use_sector_limits", _bool_text(variant.use_sector_limits)),
                ("max_per_sector", variant.max_per_sector if variant.max_per_sector is not None else "n/a"),
                ("profile", profile.upper()),
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
        "TODO: Derive Max Sector Weight, Dominant Sector, and Sector Count from existing portfolio/decision artifacts.",
        "",
    ]
    return "\n".join(lines)


def build_summary(results: list[SectorRunResult]) -> str:
    lines = [
        "# max_per_sector Sensitivity Matrix",
        "",
        "Universe: sp500",
        f"top_k: {BALANCED_TOP_K}",
        "",
        "## Runs",
        _md_table(
            (
                "sector_variant",
                "max_per_sector",
                "use_sector_limits",
                "Profile",
                "Run ID",
                "Total Return",
                "CAGR",
                "Alpha",
                "Max Drawdown",
                "Volatility",
                "Sharpe",
                "Turnover",
                "Benchmark CAGR",
                "Benchmark Drawdown",
                "Benchmark Sharpe",
                "Up Capture",
                "Down Capture",
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
        "## Sector Metrics",
        "TODO: Max Sector Weight, Dominant Sector, and Sector Count are not included yet.",
        "",
        "## Reports",
        _md_table(
            ("Test", "Variant", "max_per_sector", "use_sector_limits", "Profile", "Run ID", "Report"),
            tuple(
                (
                    result.test_id,
                    result.sector_variant,
                    _sector_value(result.max_per_sector),
                    _bool_text(result.use_sector_limits),
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


def _summary_row(result: SectorRunResult) -> tuple[object, ...]:
    return (
        result.sector_variant,
        _sector_value(result.max_per_sector),
        _bool_text(result.use_sector_limits),
        result.profile,
        result.run_id,
        _fmt_pct(result.total_return_pct),
        _fmt_pct(result.cagr_pct),
        _fmt_pct(result.alpha_pct),
        _fmt_pct(result.max_drawdown_pct),
        _fmt_pct(result.volatility_pct),
        _fmt_num(result.sharpe_ratio),
        _fmt_pct(result.turnover_pct),
        _fmt_pct(result.benchmark_cagr_pct),
        _fmt_pct(result.benchmark_max_drawdown_pct),
        _fmt_num(result.benchmark_sharpe_ratio),
        _fmt_num(result.up_capture_ratio),
        _fmt_num(result.down_capture_ratio),
    )


def _winner_row(profile: str, results: list[SectorRunResult]) -> tuple[object, ...]:
    profile_results = [result for result in results if result.profile == profile]
    best_return = _best_variant(profile_results, "total_return_pct", higher=True)
    best_drawdown = _best_variant(profile_results, "max_drawdown_pct", drawdown=True)
    best_sharpe = _best_variant(profile_results, "sharpe_ratio", higher=True)
    lowest_turnover = _best_variant(profile_results, "turnover_pct", higher=False)
    assessment = _assessment(best_return, best_drawdown, best_sharpe, lowest_turnover)
    return (profile, best_return, best_drawdown, best_sharpe, lowest_turnover, assessment)


def _best_variant(
    results: list[SectorRunResult],
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


def _variant_label(result: SectorRunResult) -> str:
    if not result.use_sector_limits:
        return "off"
    return f"{result.max_per_sector}"


def _sector_value(value: int | None) -> str:
    return "n/a" if value is None else str(value)


def _json_results(results: list[SectorRunResult]) -> list[dict[str, Any]]:
    payload = []
    for result in results:
        item = asdict(result)
        item["report_path"] = result.report_path.as_posix()
        payload.append(item)
    return payload


if __name__ == "__main__":
    main()

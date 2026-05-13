from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from scripts.compare_runs import (
    build_markdown_report,
    compare_runs,
    default_decisions_root,
    default_runs_root,
    winner_drawdown,
    winner_higher_is_better,
    winner_lower_is_better,
)


PROFILE_NAMES = ("short", "medium", "long")
REPORT_DIR = Path("reports") / "strategy_analysis"


@dataclass(frozen=True, slots=True)
class UniverseConfig:
    name: str
    tickers_file: str
    meta_file: str


@dataclass(frozen=True, slots=True)
class MatrixResult:
    test_id: str
    profile: str
    run_a: str
    run_b: str
    report_path: Path
    return_winner: str
    risk_winner: str
    sharpe_winner: str
    turnover_winner: str
    benchmark_assessment: str
    success: bool


UNIVERSES = {
    "sp500": UniverseConfig(
        name="sp500",
        tickers_file="aktien_oop/universes/sp500_tickers.txt",
        meta_file="aktien_oop/universes/sp500_meta.csv",
    ),
    "sp500_top100": UniverseConfig(
        name="sp500_top100",
        tickers_file="aktien_oop/universes/sp500_tickers_top100.txt",
        meta_file="aktien_oop/universes/sp500_meta_top100.csv",
    ),
}


def default_ai_agents_root() -> Path:
    return Path.cwd().parent / "AiAgents"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sp500 vs sp500_top100 test matrix for SHORT, MEDIUM, LONG."
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
        help="Directory for matrix reports.",
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

    results: list[MatrixResult] = []
    try:
        for index, profile in enumerate(args.profiles, start=1):
            test_id = f"T{index}"
            print(f"=== {test_id} {profile.upper()} ===")
            run_a = _run_for_universe(
                profile=profile,
                universe=UNIVERSES["sp500"],
                backtest_config_path=backtest_config_path,
                runner_config_path=runner_config_path,
            )
            run_b = _run_for_universe(
                profile=profile,
                universe=UNIVERSES["sp500_top100"],
                backtest_config_path=backtest_config_path,
                runner_config_path=runner_config_path,
            )
            comparison = compare_runs(
                run_a,
                run_b,
                runs_root=default_runs_root(),
                decisions_root=default_decisions_root(),
            )
            report_path = report_dir / f"compare_sp500_vs_top100_{profile.upper()}.md"
            report_path.write_text(build_markdown_report(comparison), encoding="utf-8")
            result = _build_matrix_result(
                test_id=test_id,
                profile=profile,
                run_a=run_a,
                run_b=run_b,
                report_path=report_path,
                comparison=comparison,
            )
            results.append(result)
            print(f"run_a: {run_a}")
            print(f"run_b: {run_b}")
            print(f"report: {report_path.as_posix()}")
            print()
    finally:
        backtest_config_path.write_text(original_backtest_config, encoding="utf-8")
        runner_config_path.write_text(original_runner_config, encoding="utf-8")

    summary_path = report_dir / "testmatrix_summary.md"
    summary_path.write_text(_build_summary(results), encoding="utf-8")
    print("Summary written:")
    print(summary_path.as_posix())


def _run_for_universe(
    *,
    profile: str,
    universe: UniverseConfig,
    backtest_config_path: Path,
    runner_config_path: Path,
) -> str:
    _write_universe_config(backtest_config_path, universe)
    _write_universe_config(runner_config_path, universe)

    command = [sys.executable, "-B", "-m", "scripts.run_bt_run_agent", "--profile", profile]
    print(f"Running {profile.upper()} {universe.name}: {' '.join(command)}")
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
            f"Run failed for profile={profile} universe={universe.name}\n"
            f"returncode={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    run_id = _extract_run_id(completed.stdout)
    if run_id is None:
        raise RuntimeError(
            f"Could not extract run_id for profile={profile} universe={universe.name}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    return run_id


def _write_universe_config(path: Path, universe: UniverseConfig) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(_replace_universe_section(text, universe), encoding="utf-8")


def _replace_universe_section(text: str, universe: UniverseConfig) -> str:
    lines = text.splitlines()
    result: list[str] = []
    in_universe = False
    seen_universe = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_universe:
                result.extend(_universe_lines(universe))
                in_universe = False
            if stripped == "[universe]":
                seen_universe = True
                in_universe = True
                result.append(line)
                continue
        if in_universe:
            continue
        result.append(line)

    if in_universe:
        result.extend(_universe_lines(universe))
    elif not seen_universe:
        result.extend(["", "[universe]", *_universe_lines(universe)])

    return "\n".join(result) + "\n"


def _universe_lines(universe: UniverseConfig) -> list[str]:
    return [
        f'name = "{universe.name}"',
        f'tickers_file = "{universe.tickers_file}"',
        f'meta_file = "{universe.meta_file}"',
    ]


def _extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("run_id:"):
            return line.split(":", 1)[1].strip()
    return None


def _build_matrix_result(
    *,
    test_id: str,
    profile: str,
    run_a: str,
    run_b: str,
    report_path: Path,
    comparison: dict,
) -> MatrixResult:
    run_a_data = comparison["run_a"]
    run_b_data = comparison["run_b"]
    perf_a = run_a_data["performance"]
    perf_b = run_b_data["performance"]
    bench_b = run_b_data["benchmark"]

    return_winner = winner_higher_is_better(
        perf_a.get("total_return_pct"),
        perf_b.get("total_return_pct"),
    )
    risk_winner = winner_drawdown(
        perf_a.get("max_drawdown_pct"),
        perf_b.get("max_drawdown_pct"),
    )
    sharpe_winner = winner_higher_is_better(
        perf_a.get("sharpe_ratio"),
        perf_b.get("sharpe_ratio"),
    )
    turnover_winner = winner_lower_is_better(
        perf_a.get("turnover_pct"),
        perf_b.get("turnover_pct"),
    )

    benchmark_assessment = _benchmark_assessment(
        candidate_name="sp500_top100",
        candidate=perf_b,
        benchmark=bench_b,
    )
    success = all(value != "n/a" for value in (return_winner, risk_winner, sharpe_winner))

    return MatrixResult(
        test_id=test_id,
        profile=profile.upper(),
        run_a=run_a,
        run_b=run_b,
        report_path=report_path,
        return_winner=return_winner,
        risk_winner=risk_winner,
        sharpe_winner=sharpe_winner,
        turnover_winner=turnover_winner,
        benchmark_assessment=benchmark_assessment,
        success=success,
    )


def _benchmark_assessment(*, candidate_name: str, candidate: dict, benchmark: dict) -> str:
    cagr_winner = winner_higher_is_better(
        benchmark.get("benchmark_cagr_pct"),
        candidate.get("cagr_pct"),
    )
    sharpe_winner = winner_higher_is_better(
        benchmark.get("benchmark_sharpe_ratio"),
        candidate.get("sharpe_ratio"),
    )
    drawdown_winner = winner_drawdown(
        benchmark.get("benchmark_max_drawdown_pct"),
        candidate.get("max_drawdown_pct"),
    )

    parts = []
    if drawdown_winner == "B":
        parts.append(f"{candidate_name} has lower drawdown than benchmark")
    elif drawdown_winner == "A":
        parts.append(f"{candidate_name} has higher drawdown than benchmark")

    if cagr_winner == "A" and sharpe_winner == "A":
        parts.append("but stays behind benchmark on CAGR and Sharpe")
    elif cagr_winner == "A":
        parts.append("but stays behind benchmark on CAGR")
    elif sharpe_winner == "A":
        parts.append("but stays behind benchmark on Sharpe")
    elif cagr_winner == "B" and sharpe_winner == "B":
        parts.append("and beats benchmark on CAGR and Sharpe")

    return "; ".join(parts) + "." if parts else "Benchmark assessment n/a."


def _build_summary(results: list[MatrixResult]) -> str:
    lines = [
        "# sp500 vs sp500_top100 Testmatrix",
        "",
        "| Test | Profile | Run A | Run B | Return Winner | Risk Winner | Sharpe Winner | Turnover Winner | Benchmark Assessment | Report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            + " | ".join(
                (
                    result.test_id,
                    result.profile,
                    result.run_a,
                    result.run_b,
                    result.return_winner,
                    result.risk_winner,
                    result.sharpe_winner,
                    result.turnover_winner,
                    result.benchmark_assessment,
                    result.report_path.as_posix(),
                )
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Universe A: sp500",
            "Universe B: sp500_top100",
            "",
            "Profiles:",
            "- SHORT: latest compare, 18-month backtest scope",
            "- MEDIUM: all compare, 30-month backtest scope, last 3 BT as_of points",
            "- LONG: all compare, full configured backtest scope, last 6 BT as_of points",
            "",
            "Raw matrix JSON:",
            "```json",
            _results_json(results),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _results_json(results: list[MatrixResult]) -> str:
    payload = []
    for result in results:
        item = asdict(result)
        item["report_path"] = result.report_path.as_posix()
        payload.append(item)
    return json.dumps(payload, indent=2)


if __name__ == "__main__":
    main()

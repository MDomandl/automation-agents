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
    winner_drawdown,
    winner_higher_is_better,
    winner_lower_is_better,
)
from scripts.run_sp500_testmatrix import (
    PROFILE_NAMES,
    UNIVERSES,
    _replace_universe_section,
    default_ai_agents_root,
)


TOP_K_VALUES = (8, 12, 15, 20)
REPORT_DIR = Path("reports") / "strategy_analysis" / "top_k"


@dataclass(frozen=True, slots=True)
class TopKRunResult:
    test_id: str
    top_k: int
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
        description="Run sp500 top_k sensitivity matrix for SHORT, MEDIUM, LONG."
    )
    parser.add_argument(
        "--top-k",
        nargs="+",
        type=int,
        default=list(TOP_K_VALUES),
        help="top_k values to run. Defaults to 8 12 15 20.",
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
        help="Directory for top_k reports.",
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

    results: list[TopKRunResult] = []
    try:
        test_index = 1
        for top_k in args.top_k:
            for profile in args.profiles:
                test_id = f"K{test_index}"
                test_index += 1
                print(f"=== {test_id} top_k={top_k} {profile.upper()} ===")
                run_id = _run_for_top_k(
                    profile=profile,
                    top_k=top_k,
                    backtest_config_path=backtest_config_path,
                    runner_config_path=runner_config_path,
                )
                snapshot = load_run_snapshot(
                    run_id,
                    runs_root=default_runs_root(),
                    decisions_root=default_decisions_root(),
                )
                report_path = report_dir / f"top_k_{top_k:02d}_{profile.upper()}.md"
                report_path.write_text(
                    build_run_report(
                        test_id=test_id,
                        top_k=top_k,
                        profile=profile,
                        snapshot=snapshot,
                    ),
                    encoding="utf-8",
                )
                result = _build_result(
                    test_id=test_id,
                    top_k=top_k,
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

    summary_path = report_dir / "top_k_summary.md"
    summary_path.write_text(build_summary(results), encoding="utf-8")
    print("Summary written:")
    print(summary_path.as_posix())


def _run_for_top_k(
    *,
    profile: str,
    top_k: int,
    backtest_config_path: Path,
    runner_config_path: Path,
) -> str:
    _write_matrix_config(backtest_config_path, top_k)
    _write_matrix_config(runner_config_path, top_k)

    command = [sys.executable, "-B", "-m", "scripts.run_bt_run_agent", "--profile", profile]
    print(f"Running {profile.upper()} sp500 top_k={top_k}: {' '.join(command)}")
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
            f"Run failed for profile={profile} top_k={top_k}\n"
            f"returncode={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    run_id = _extract_run_id(completed.stdout)
    if run_id is None:
        raise RuntimeError(
            f"Could not extract run_id for profile={profile} top_k={top_k}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    return run_id


def _write_matrix_config(path: Path, top_k: int) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_universe_section(text, UNIVERSES["sp500"])
    text = replace_top_k(text, top_k)
    path.write_text(text, encoding="utf-8")


def replace_top_k(text: str, top_k: int) -> str:
    lines = text.splitlines()
    result: list[str] = []
    section = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped.strip("[]").strip().lower()
            result.append(line)
            continue
        if stripped.startswith("top_k") and (section == "" or section == "topk"):
            prefix, _, rest = line.partition("=")
            comment = ""
            if "#" in rest:
                _, _, comment_tail = rest.partition("#")
                comment = "  #" + comment_tail
            result.append(f"{prefix}= {top_k}{comment}")
            continue
        result.append(line)
    return "\n".join(result) + "\n"


def _extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("run_id:"):
            return line.split(":", 1)[1].strip()
    return None


def _build_result(
    *,
    test_id: str,
    top_k: int,
    profile: str,
    run_id: str,
    report_path: Path,
    snapshot: Any,
) -> TopKRunResult:
    perf = snapshot.performance
    bench = snapshot.benchmark
    return TopKRunResult(
        test_id=test_id,
        top_k=top_k,
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


def _snapshot_success(snapshot: Any) -> bool:
    if snapshot.output_dir is None:
        return False
    manifest_path = snapshot.output_dir / "run_manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(payload.get("success"))


def build_run_report(*, test_id: str, top_k: int, profile: str, snapshot: Any) -> str:
    perf = snapshot.performance
    bench = snapshot.benchmark
    lines = [
        "# top_k Run Report",
        "",
        "## Run",
        _md_table(
            ("Metric", "Value"),
            (
                ("test_id", test_id),
                ("universe", "sp500"),
                ("top_k", top_k),
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
    ]
    return "\n".join(lines)


def build_summary(results: list[TopKRunResult]) -> str:
    lines = [
        "# top_k Sensitivity Matrix",
        "",
        "Universe: sp500",
        "",
        "## Runs",
        _md_table(
            (
                "top_k",
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
        "## Reports",
        _md_table(
            ("Test", "top_k", "Profile", "Run ID", "Report"),
            tuple(
                (
                    result.test_id,
                    result.top_k,
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


def _summary_row(result: TopKRunResult) -> tuple[object, ...]:
    return (
        result.top_k,
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


def _winner_row(profile: str, results: list[TopKRunResult]) -> tuple[object, ...]:
    profile_results = [result for result in results if result.profile == profile]
    best_return = _best_top_k(profile_results, "total_return_pct", higher=True)
    best_drawdown = _best_top_k(profile_results, "max_drawdown_pct", drawdown=True)
    best_sharpe = _best_top_k(profile_results, "sharpe_ratio", higher=True)
    lowest_turnover = _best_top_k(profile_results, "turnover_pct", higher=False)
    assessment = _assessment(profile_results, best_return, best_drawdown, best_sharpe, lowest_turnover)
    return (profile, best_return, best_drawdown, best_sharpe, lowest_turnover, assessment)


def _best_top_k(
    results: list[TopKRunResult],
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
        candidates.append((score, result.top_k))
    if not candidates:
        return "n/a"
    _, top_k = min(candidates) if (drawdown or not higher) else max(candidates)
    return str(top_k)


def _assessment(
    results: list[TopKRunResult],
    best_return: str,
    best_drawdown: str,
    best_sharpe: str,
    lowest_turnover: str,
) -> str:
    if not results:
        return "n/a"
    if len({best_drawdown, best_sharpe, lowest_turnover}) == 1 and best_drawdown != "n/a":
        return f"top_k={best_drawdown} leads on risk/efficiency."
    if best_return != "n/a" and best_return != best_drawdown:
        return f"Return favors top_k={best_return}; risk favors top_k={best_drawdown}."
    return "Mixed; inspect report details."


def _json_results(results: list[TopKRunResult]) -> list[dict[str, Any]]:
    payload = []
    for result in results:
        item = asdict(result)
        item["report_path"] = result.report_path.as_posix()
        payload.append(item)
    return payload


def _md_table(headers: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_display(value) for value in row) + " |")
    return "\n".join(lines)


def _fmt_pct(value: object) -> str:
    numeric = _to_float(value)
    return "n/a" if numeric is None else f"{numeric:.2f}%"


def _fmt_num(value: object) -> str:
    numeric = _to_float(value)
    return "n/a" if numeric is None else f"{numeric:.4f}"


def _display(value: object) -> str:
    return "n/a" if value is None else str(value)


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip().replace("%", ""))
    except ValueError:
        return None


if __name__ == "__main__":
    main()

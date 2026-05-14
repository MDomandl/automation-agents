import json
import math
from pathlib import Path

from scripts.compare_runs import (
    build_console_report,
    build_markdown_report,
    calc_delta,
    compare_runs,
    format_delta,
    markdown_report_path,
    read_benchmark_relation_metrics,
    winner_drawdown,
    winner_higher_is_better,
    winner_lower_is_better,
)


def test_compare_runs_reads_existing_outputs_without_running_anything(tmp_path: Path) -> None:
    runs_root = tmp_path / "automation_runs"
    decisions_root = tmp_path / "decisions"

    _write_run(
        runs_root,
        decisions_root,
        run_id="20260501_004942",
        label="2026-05-01_00-49-42_medium",
        universe_name="sp500",
        universe_file="aktien_oop/universes/sp500_tickers.txt",
        universe_len=503,
        universe_hash="hash-sp500",
        total_return=30.5,
        max_dd=-12.2,
        volatility=18.3,
        sharpe=1.12,
        turnover=34.5,
        equity_values=(1.00, 1.10, 0.90),
        portfolios=(
            ("2025-09-30", {"AAPL": 0.5, "MSFT": 0.5}),
            ("2025-10-08", {"AAPL": 0.5, "NVDA": 0.5}),
        ),
    )
    _write_run(
        runs_root,
        decisions_root,
        run_id="20260501_120332",
        label="2026-05-01_12-03-32_medium",
        universe_name="sp500_top100",
        universe_file="aktien_oop/universes/sp500_tickers_top100.txt",
        universe_len=100,
        universe_hash="hash-top100",
        total_return=20.6,
        max_dd=-16.0,
        volatility=17.7,
        sharpe=0.83,
        turnover=34.2,
        equity_values=(1.00, 1.20, 1.05),
        portfolios=(
            ("2025-09-30", {"AAPL": 0.5, "MSFT": 0.5}),
            ("2025-10-08", {"AAPL": 0.5, "AVGO": 0.5}),
        ),
    )

    comparison = compare_runs(
        "20260501_004942",
        "20260501_120332",
        runs_root=runs_root,
        decisions_root=decisions_root,
    )

    assert comparison["run_a"]["universe"]["universe_name"] == "sp500"
    assert comparison["run_a"]["universe"]["universe_len"] == 503
    assert comparison["run_b"]["universe"]["universe_name"] == "sp500_top100"
    assert comparison["run_b"]["performance"]["total_return_pct"] == 20.6
    assert comparison["run_b"]["benchmark"]["benchmark_name"] == "SXR8.DE"
    assert comparison["run_b"]["benchmark"]["benchmark_return_pct"] == 22.85
    assert comparison["run_b"]["benchmark"]["benchmark_cagr_pct"] == 15.36
    assert math.isclose(
        comparison["run_b"]["benchmark"]["benchmark_max_drawdown_pct"],
        -20.0,
        abs_tol=1e-12,
    )
    assert comparison["run_b"]["benchmark"]["benchmark_volatility_pct"] == 16.9
    assert comparison["run_b"]["benchmark"]["benchmark_sharpe_ratio"] == 0.93
    assert math.isclose(
        comparison["run_b"]["benchmark"]["correlation_to_benchmark"],
        1.0,
        abs_tol=1e-12,
    )
    assert math.isclose(
        comparison["run_b"]["benchmark"]["up_capture_ratio"],
        0.8,
        abs_tol=1e-12,
    )
    assert math.isclose(
        comparison["run_b"]["benchmark"]["down_capture_ratio"],
        0.625,
        abs_tol=1e-12,
    )
    assert (
        comparison["run_a"]["benchmark"]["up_capture_ratio"]
        != comparison["run_b"]["benchmark"]["up_capture_ratio"]
    )
    assert comparison["run_a"]["performance"]["max_drawdown_pct"] == -12.2
    assert comparison["run_a"]["performance"]["volatility_pct"] == 18.3
    assert comparison["run_a"]["performance"]["sharpe_ratio"] == 1.12
    assert comparison["run_a"]["behavior"]["avg_positions"] == 2.0
    assert comparison["run_a"]["behavior"]["last_as_of"] == "2025-10-08"
    assert comparison["last_decision_tickers"]["common"] == ["AAPL"]
    assert comparison["last_decision_tickers"]["only_in_a"] == ["NVDA"]
    assert comparison["last_decision_tickers"]["only_in_b"] == ["AVGO"]
    assert comparison["last_decision_tickers"]["overlap_count"] == 1
    assert comparison["last_decision_tickers"]["overlap_denominator"] == 2
    assert comparison["last_decision_tickers"]["overlap_pct"] == 50.0


def test_console_report_is_human_readable(tmp_path: Path) -> None:
    runs_root = tmp_path / "automation_runs"
    decisions_root = tmp_path / "decisions"
    _write_run(
        runs_root,
        decisions_root,
        run_id="20260501_004942",
        label="2026-05-01_00-49-42_medium",
        universe_name="sp500",
        universe_file="sp500.txt",
        universe_len=503,
        universe_hash="hash-a",
        total_return=10.0,
        max_dd=-5.0,
        volatility=11.0,
        sharpe=0.9,
        turnover=20.0,
        equity_values=(1.00, 1.10, 0.90),
        portfolios=(("2025-10-08", {"AAPL": 1.0}),),
    )
    _write_run(
        runs_root,
        decisions_root,
        run_id="20260501_120332",
        label="2026-05-01_12-03-32_medium",
        universe_name="sp500_top100",
        universe_file="sp500_top100.txt",
        universe_len=100,
        universe_hash="hash-b",
        total_return=8.0,
        max_dd=-7.0,
        volatility=12.0,
        sharpe=0.7,
        turnover=21.0,
        equity_values=(1.00, 1.20, 1.05),
        portfolios=(("2025-10-08", {"MSFT": 1.0}),),
    )

    report = build_console_report(
        compare_runs(
            "20260501_004942",
            "20260501_120332",
            runs_root=runs_root,
            decisions_root=decisions_root,
        )
    )

    assert "Config / Universe" in report
    assert "Performance" in report
    assert "Delta=-2.00pp" in report
    assert "Benchmark (SXR8.DE)" in report
    assert "benchmark_return_pct" in report
    assert "benchmark_max_drawdown_pct" in report
    assert "Benchmark Relation" in report
    assert "correlation_to_benchmark" in report
    assert "up_capture_ratio" in report
    assert "down_capture_ratio" in report
    assert "Performance / Trading Verdict" in report
    assert "return" in report
    assert "Return winner: A." in report
    assert "Trading / Portfolio" in report
    assert "overlap_count        0 / 1" in report
    assert "overlap_pct          0.00%" in report
    assert "only in A (1): AAPL" in report
    assert "Interpretation" in report
    assert "Different universe detected: portfolio differences are expected." in report


def test_delta_and_winner_helpers() -> None:
    assert calc_delta(20.34, 20.66) == 0.3200000000000003
    assert format_delta(20.34, 20.66, percent_points=True) == "+0.32pp"
    assert format_delta(0.64, 0.83, percent_points=False) == "+0.1900"
    assert format_delta(None, 0.83, percent_points=False) == "n/a"

    assert winner_higher_is_better(20.34, 20.66) == "B"
    assert winner_lower_is_better(48.83, 34.21) == "B"
    assert winner_drawdown(-24.45, -16.04) == "B"
    assert winner_drawdown(-16.04, -16.04) == "tie"


def test_markdown_report_uses_report_structure(tmp_path: Path) -> None:
    runs_root = tmp_path / "automation_runs"
    decisions_root = tmp_path / "decisions"
    _write_run(
        runs_root,
        decisions_root,
        run_id="20260505_230805",
        label="2026-05-05_23-08-05_medium",
        universe_name="sp500",
        universe_file="sp500.txt",
        universe_len=503,
        universe_hash="hash-a",
        total_return=20.34,
        max_dd=-24.45,
        volatility=25.30,
        sharpe=0.64,
        turnover=48.83,
        equity_values=(1.00, 1.10, 0.90),
        portfolios=(("2025-10-08", {"APH": 0.5, "AVGO": 0.5}),),
    )
    _write_run(
        runs_root,
        decisions_root,
        run_id="20260505_205318",
        label="2026-05-05_20-53-18_medium",
        universe_name="sp500_top100",
        universe_file="sp500_top100.txt",
        universe_len=100,
        universe_hash="hash-b",
        total_return=20.66,
        max_dd=-16.04,
        volatility=17.70,
        sharpe=0.83,
        turnover=34.21,
        equity_values=(1.00, 1.20, 1.05),
        portfolios=(("2025-10-08", {"APH": 0.5, "CHRW": 0.5}),),
    )

    comparison = compare_runs(
        "20260505_230805",
        "20260505_205318",
        runs_root=runs_root,
        decisions_root=decisions_root,
    )
    markdown = build_markdown_report(comparison)

    assert "# Run Comparison Report" in markdown
    assert "| Side | Run ID |" in markdown
    assert "| A | 20260505_230805 |" in markdown
    assert "| total_return_pct | 20.34% | 20.66% | +0.32pp |" in markdown
    assert "## Benchmark (SXR8.DE)" in markdown
    assert "| benchmark_return_pct | 22.85% | 22.85% | 0.00pp |" in markdown
    assert "| benchmark_sharpe_ratio | 0.9300 | 0.9300 | 0.0000 |" in markdown
    assert "## Benchmark Relation" in markdown
    assert "| correlation_to_benchmark | 1.0000 | 1.0000 | 0.0000 |" in markdown
    assert "| up_capture_ratio | 0.4000 | 0.8000 | +0.4000 |" in markdown
    assert "## Performance / Trading Verdict" in markdown
    assert "overlap_count: 1 / 2" in markdown
    assert "| Group | Count | Tickers |" in markdown
    assert "| Common | 1 | APH |" in markdown
    assert markdown_report_path(tmp_path, "A", "B") == tmp_path / "compare_A_vs_B.md"


def test_benchmark_relation_metrics_missing_data_returns_none() -> None:
    assert read_benchmark_relation_metrics(None, None) == {
        "correlation_to_benchmark": None,
        "up_capture_ratio": None,
        "down_capture_ratio": None,
    }


def test_benchmark_relation_metrics_rejects_mismatched_run_csv(tmp_path: Path) -> None:
    equity_path = tmp_path / "equity.csv"
    benchmark_path = tmp_path / "benchmark.csv"
    equity_path.write_text(
        "# run_id=20260505_111111\n"
        "date,equity\n"
        "2025-01-31,1.00\n"
        "2025-02-28,1.10\n"
        "2025-03-31,0.90\n",
        encoding="utf-8",
    )
    benchmark_path.write_text(
        "# run_id=20260505_111111\n"
        "date,equity,BM1_SXR8.DE\n"
        "2025-01-31,1.00,1.00\n"
        "2025-02-28,1.10,1.25\n"
        "2025-03-31,0.90,1.00\n",
        encoding="utf-8",
    )

    assert read_benchmark_relation_metrics(
        equity_path,
        benchmark_path,
        benchmark_name="SXR8.DE",
        run_id="20260505_222222",
    ) == {
        "correlation_to_benchmark": None,
        "up_capture_ratio": None,
        "down_capture_ratio": None,
    }


def _write_run(
    runs_root: Path,
    decisions_root: Path,
    *,
    run_id: str,
    label: str,
    universe_name: str,
    universe_file: str,
    universe_len: int,
    universe_hash: str,
    total_return: float,
    max_dd: float,
    volatility: float,
    sharpe: float,
    turnover: float,
    portfolios: tuple[tuple[str, dict[str, float]], ...],
    equity_values: tuple[float, float, float] = (1.00, 1.10, 0.90),
) -> None:
    output_dir = runs_root / label
    decisions_dir = decisions_root / run_id
    output_dir.mkdir(parents=True)
    decisions_dir.mkdir(parents=True)

    stdout = (
        f"[LOCKSTEP][BT ] as_of=2025-10-08 top_k=12 universe_name={universe_name} "
        f"universe_file={universe_file} universe_len={universe_len} universe_hash={universe_hash}\n"
        f"Total Return:  {total_return:.2f}%   |  CAGR:  13.93%\n"
        f"Volatility:   {volatility:.2f}% |  Sharpe(0%): {sharpe:.2f}\n"
        f"Max DD:       {max_dd:.2f}%   [2024-11-26 -> 2025-03-13]\n"
        f"Avg Turnover: {turnover:.2f}% |  Avg Cost: 0.0005\n"
        "Benchmark:     SXR8.DE\n"
        "BM Total Ret:    22.85%   |  BM CAGR:   15.36%\n"
        "BM Volatility:  16.90% |  BM Sharpe(0%):  0.93\n"
        "BM2 Volatility:  99.99% |  BM2 Sharpe(0%):  9.99\n"
        "Equity: equity.csv\n"
        "Bench: benchmark.csv\n"
    )
    manifest = {
        "run_id": run_id,
        "run_label": label,
        "decisions_dir": str(decisions_dir),
        "warnings": [],
        "backtest": {"stdout": stdout, "stderr": "", "cwd": str(tmp_root(output_dir))},
        "runner": {"stdout": "", "stderr": "", "cwd": str(tmp_root(output_dir))},
    }
    (output_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (output_dir / "benchmark.csv").write_text(
        f"# run_id={run_id}\n"
        "date,equity,BM1_SXR8.DE\n"
        f"2025-01-31,{equity_values[0]},1.00\n"
        f"2025-02-28,{equity_values[1]},1.25\n"
        f"2025-03-31,{equity_values[2]},1.00\n",
        encoding="utf-8",
    )
    (output_dir / "equity.csv").write_text(
        f"# run_id={run_id}\n"
        "date,equity\n"
        f"2025-01-31,{equity_values[0]}\n"
        f"2025-02-28,{equity_values[1]}\n"
        f"2025-03-31,{equity_values[2]}\n",
        encoding="utf-8",
    )

    for index, (as_of, weights) in enumerate(portfolios):
        payload = {
            "kind": "RUN",
            "as_of": as_of,
            "new_weights": weights,
            "universe_name": universe_name,
            "universe_file": universe_file,
            "universe_len": universe_len,
            "universe_hash": universe_hash,
        }
        (decisions_dir / f"RUN_{index}_{as_of}.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )


def tmp_root(path: Path) -> Path:
    return path.parent.parent

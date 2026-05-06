import json
from pathlib import Path

from scripts.compare_runs import build_console_report, compare_runs


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
    assert comparison["run_a"]["performance"]["max_drawdown_pct"] == -12.2
    assert comparison["run_a"]["performance"]["volatility_pct"] == 18.3
    assert comparison["run_a"]["performance"]["sharpe_ratio"] == 1.12
    assert comparison["run_a"]["behavior"]["avg_positions"] == 2.0
    assert comparison["run_a"]["behavior"]["last_as_of"] == "2025-10-08"
    assert comparison["last_decision_tickers"]["common"] == ["AAPL"]
    assert comparison["last_decision_tickers"]["only_in_a"] == ["NVDA"]
    assert comparison["last_decision_tickers"]["only_in_b"] == ["AVGO"]


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
    assert "Trading / Portfolio" in report
    assert "only in A (1): AAPL" in report


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
        "BM Volatility:  99.99% |  BM Sharpe(0%):  9.99\n"
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

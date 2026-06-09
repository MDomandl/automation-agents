from __future__ import annotations

import math
from pathlib import Path

import pytest

from scripts.phase_metrics import compute_phase_metrics


def test_phase_metrics_ignore_comments_segment_and_compute_core_values(tmp_path: Path) -> None:
    artifacts = _write_artifacts(
        tmp_path,
        equity_rows=[
            ("2022-01-01", 10.0),
            ("2022-01-02", 11.0),
            ("2022-01-03", 8.8),
            ("2022-01-04", 13.2),
        ],
        benchmark_rows=[
            ("2022-01-01", 10.0, 100.0),
            ("2022-01-02", 11.0, 100.0),
            ("2022-01-03", 8.8, 110.0),
            ("2022-01-04", 13.2, 121.0),
        ],
        trade_rows=[
            ("2021-12-31", 0.9),
            ("2022-01-02", 0.1),
            ("2022-01-04", 0.3),
        ],
    )

    metrics = compute_phase_metrics(artifacts, "2022-01-02", "2022-01-04")

    assert metrics["phase_start_actual"] == "2022-01-02"
    assert metrics["phase_end_actual"] == "2022-01-04"
    assert metrics["observation_count"] == 3
    assert metrics["portfolio_total_return"] == pytest.approx(20.0)
    assert metrics["portfolio_cagr"] == pytest.approx(((1.2) ** (365.25 / 2) - 1.0) * 100)
    assert metrics["portfolio_max_drawdown"] == pytest.approx(-20.0)
    assert metrics["benchmark_total_return"] == pytest.approx(21.0)
    assert metrics["relative_total_return"] == pytest.approx(-1.0)
    assert metrics["outperformed_benchmark"] is False
    assert metrics["turnover"] == pytest.approx(20.0)
    assert metrics["turnover_is_phase_only"] is True
    assert metrics["turnover_source"] == "trades_csv_in_phase_rows"


def test_first_available_date_after_phase_start_is_actual_start(tmp_path: Path) -> None:
    artifacts = _write_artifacts(
        tmp_path,
        equity_rows=[("2022-01-03", 1.0), ("2022-01-04", 1.1)],
        benchmark_rows=[("2022-01-03", 1.0, 1.0), ("2022-01-04", 1.0, 1.0)],
    )

    metrics = compute_phase_metrics(artifacts, "2022-01-01", "2022-01-04")

    assert metrics["phase_start_actual"] == "2022-01-03"
    assert metrics["portfolio_total_return"] == pytest.approx(10.0)


def test_drawdown_for_increasing_falling_and_v_shaped_series(tmp_path: Path) -> None:
    increasing = _write_artifacts(
        tmp_path / "increasing",
        equity_rows=[("2022-01-01", 1.0), ("2022-01-02", 1.1), ("2022-01-03", 1.2)],
    )
    falling = _write_artifacts(
        tmp_path / "falling",
        equity_rows=[("2022-01-01", 1.0), ("2022-01-02", 0.8), ("2022-01-03", 0.6)],
    )
    v_shaped = _write_artifacts(
        tmp_path / "v_shaped",
        equity_rows=[("2022-01-01", 1.0), ("2022-01-02", 0.7), ("2022-01-03", 1.2)],
    )

    assert compute_phase_metrics(increasing, "2022-01-01", "2022-01-03")[
        "portfolio_max_drawdown"
    ] == pytest.approx(0.0)
    assert compute_phase_metrics(falling, "2022-01-01", "2022-01-03")[
        "portfolio_max_drawdown"
    ] == pytest.approx(-40.0)
    assert compute_phase_metrics(v_shaped, "2022-01-01", "2022-01-03")[
        "portfolio_max_drawdown"
    ] == pytest.approx(-30.0)


def test_volatility_and_sharpe_match_daily_return_semantics(tmp_path: Path) -> None:
    artifacts = _write_artifacts(
        tmp_path,
        equity_rows=[("2022-01-01", 1.0), ("2022-01-02", 1.1), ("2022-01-03", 1.21)],
    )

    metrics = compute_phase_metrics(artifacts, "2022-01-01", "2022-01-03")

    returns = [0.0, 0.1, 0.1]
    mean = sum(returns) / len(returns)
    std = math.sqrt(sum((value - mean) ** 2 for value in returns) / (len(returns) - 1))
    volatility = std * math.sqrt(252.0)
    sharpe = (mean * 252.0) / (volatility + 1e-12)
    assert metrics["portfolio_volatility"] == pytest.approx(volatility * 100.0)
    assert metrics["portfolio_sharpe"] == pytest.approx(sharpe)


def test_benchmark_uses_bm1_column_not_equity_column(tmp_path: Path) -> None:
    artifacts = _write_artifacts(
        tmp_path,
        equity_rows=[("2022-01-01", 1.0), ("2022-01-02", 1.0)],
        benchmark_rows=[("2022-01-01", 1.0, 10.0), ("2022-01-02", 9.0, 11.0)],
    )

    metrics = compute_phase_metrics(artifacts, "2022-01-01", "2022-01-02")

    assert metrics["benchmark_total_return"] == pytest.approx(10.0)


def test_relative_cagr_and_outperformance_booleans(tmp_path: Path) -> None:
    artifacts = _write_artifacts(
        tmp_path,
        equity_rows=[("2022-01-01", 1.0), ("2023-01-01", 1.2)],
        benchmark_rows=[("2022-01-01", 1.0, 1.0), ("2023-01-01", 1.0, 1.1)],
    )

    metrics = compute_phase_metrics(artifacts, "2022-01-01", "2023-01-01")

    assert metrics["relative_cagr"] == pytest.approx(
        metrics["portfolio_cagr"] - metrics["benchmark_cagr"]
    )
    assert metrics["outperformed_benchmark"] is True
    assert metrics["cagr_outperformed_benchmark"] is True
    assert metrics["drawdown_better_than_benchmark"] is False


def test_drawdown_better_than_benchmark_when_portfolio_is_less_negative(tmp_path: Path) -> None:
    artifacts = _write_artifacts(
        tmp_path,
        equity_rows=[("2022-01-01", 1.0), ("2022-01-02", 0.88), ("2022-01-03", 1.0)],
        benchmark_rows=[
            ("2022-01-01", 1.0, 1.0),
            ("2022-01-02", 1.0, 0.82),
            ("2022-01-03", 1.0, 1.0),
        ],
    )

    metrics = compute_phase_metrics(artifacts, "2022-01-01", "2022-01-03")

    assert metrics["portfolio_max_drawdown"] == pytest.approx(-12.0)
    assert metrics["benchmark_max_drawdown"] == pytest.approx(-18.0)
    assert metrics["drawdown_better_than_benchmark"] is True


def test_missing_artifacts_and_too_short_segments_return_null_values(tmp_path: Path) -> None:
    missing = compute_phase_metrics({}, "2022-01-01", "2022-01-02")
    assert missing["portfolio_total_return"] is None
    assert missing["benchmark_total_return"] is None
    assert missing["turnover"] is None
    assert missing["turnover_is_phase_only"] is False

    artifacts = _write_artifacts(tmp_path, equity_rows=[("2022-01-01", 1.0)])
    too_short = compute_phase_metrics(artifacts, "2022-01-01", "2022-01-02")
    assert too_short["phase_start_actual"] == "2022-01-01"
    assert too_short["observation_count"] == 1
    assert too_short["portfolio_total_return"] is None
    assert too_short["portfolio_cagr"] is None


def _write_artifacts(
    root: Path,
    *,
    equity_rows: list[tuple[str, float]],
    benchmark_rows: list[tuple[str, float, float]] | None = None,
    trade_rows: list[tuple[str, float]] | None = None,
) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    equity = root / "equity.csv"
    equity.write_text(
        "# run_id=test\n"
        "date,equity\n"
        + "".join(f"{date_value},{equity_value}\n" for date_value, equity_value in equity_rows),
        encoding="utf-8",
    )
    artifacts = {"equity": str(equity)}

    if benchmark_rows is not None:
        bench = root / "benchmark.csv"
        bench.write_text(
            "# run_id=test\n"
            "date,equity,BM1_SXR8.DE\n"
            + "".join(
                f"{date_value},{equity_value},{benchmark_value}\n"
                for date_value, equity_value, benchmark_value in benchmark_rows
            ),
            encoding="utf-8",
        )
        artifacts["bench"] = str(bench)

    if trade_rows is not None:
        trades = root / "trades.csv"
        trades.write_text(
            "# run_id=test\n"
            "date,turnover,trade_cost,enter,exit\n"
            + "".join(f"{date_value},{turnover},0.0,,\n" for date_value, turnover in trade_rows),
            encoding="utf-8",
        )
        artifacts["trades"] = str(trades)

    return artifacts

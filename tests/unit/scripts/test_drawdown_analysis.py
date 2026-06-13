from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from scripts import drawdown_analysis as dda


def test_csv_comment_line_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "equity.csv"
    path.write_text("# run_id=test\ndate,equity\n2022-01-01,100\n", encoding="utf-8")

    rows = dda.read_csv_rows(path)

    assert rows == [{"date": "2022-01-01", "equity": "100"}]


def test_drawdown_series_is_computed_from_cummax() -> None:
    series = _series([("2022-01-01", 100), ("2022-01-02", 110), ("2022-01-03", 99)])

    drawdown = dda.compute_drawdown_series(series)

    assert [row["drawdown"] for row in drawdown] == pytest.approx([0.0, 0.0, -0.1])


def test_single_drawdown_episode_has_start_trough_recovery_depth_and_duration() -> None:
    series = _series(
        [
            ("2022-01-01", 100),
            ("2022-01-02", 80),
            ("2022-01-03", 90),
            ("2022-01-04", 100),
        ]
    )

    episodes = dda.detect_drawdown_episodes(series, top_n=3)

    assert episodes == [
        {
            "drawdown_start": "2022-01-01",
            "drawdown_trough": "2022-01-02",
            "drawdown_recovery": "2022-01-04",
            "drawdown_depth": pytest.approx(-20.0),
            "drawdown_duration_days": 1,
            "drawdown_duration_observations": 4,
            "recovered": True,
        }
    ]


def test_non_recovered_drawdown_has_null_recovery() -> None:
    episodes = dda.detect_drawdown_episodes(
        _series([("2022-01-01", 100), ("2022-01-02", 95), ("2022-01-03", 90)]),
        top_n=3,
    )

    assert episodes[0]["drawdown_recovery"] is None
    assert episodes[0]["recovered"] is False
    assert episodes[0]["drawdown_depth"] == pytest.approx(-10.0)


def test_top_n_drawdowns_are_distinct_episodes() -> None:
    episodes = dda.detect_drawdown_episodes(
        _series(
            [
                ("2022-01-01", 100),
                ("2022-01-02", 90),
                ("2022-01-03", 80),
                ("2022-01-04", 100),
                ("2022-01-05", 95),
                ("2022-01-06", 100),
            ]
        ),
        top_n=2,
    )

    assert [episode["drawdown_trough"] for episode in episodes] == [
        "2022-01-03",
        "2022-01-05",
    ]


def test_benchmark_column_uses_bm1_prefix(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.csv"
    path.write_text(
        "# run_id=test\n" "date,equity,BM1_SXR8.DE\n" "2022-01-01,1,100\n",
        encoding="utf-8",
    )

    assert dda.benchmark_column_from_csv(path) == "BM1_SXR8.DE"


def test_benchmark_same_window_metrics_are_computed() -> None:
    benchmark_dd = dda.compute_drawdown_series(
        _series(
            [
                ("2022-01-01", 100),
                ("2022-01-02", 98),
                ("2022-01-03", 90),
                ("2022-01-04", 95),
            ]
        )
    )
    episode = {
        "drawdown_start": "2022-01-01",
        "drawdown_trough": "2022-01-02",
        "drawdown_depth": -20.0,
    }

    comparison = dda.benchmark_comparison(
        episode,
        benchmark_dd=benchmark_dd,
        window_end=datetime.fromisoformat("2022-01-04"),
    )

    assert comparison["benchmark_drawdown_at_portfolio_trough"] == pytest.approx(-2.0)
    assert comparison["benchmark_max_drawdown_same_window"] == pytest.approx(-10.0)
    assert comparison["benchmark_trough_same_window"] == "2022-01-03"
    assert comparison["drawdown_vs_benchmark_at_trough"] == pytest.approx(-18.0)
    assert comparison["drawdown_vs_benchmark_window"] == pytest.approx(-10.0)


def test_positions_snapshots_tickers_sectors_and_concentration_are_aggregated() -> None:
    rows = [
        _position("2022-01-01", "AAA", 0.2, 1, 10, "Tech"),
        _position("2022-01-01", "BBB", 0.1, 2, 9, "Health"),
        _position("2022-01-02", "AAA", 0.3, 1, 11, "Tech"),
        _position("2022-01-02", "CCC", 0.2, 3, 8, "Tech"),
    ]

    positions = dda.analyze_positions(
        rows,
        drawdown_start=datetime.fromisoformat("2022-01-01"),
        drawdown_end=datetime.fromisoformat("2022-01-02"),
        top_n=3,
    )

    assert positions["snapshot_count"] == 2
    assert positions["top_tickers"][0]["ticker"] == "AAA"
    assert positions["top_tickers"][0]["avg_weight"] == pytest.approx(25.0)
    tech = positions["sector_exposure"][0]
    assert tech["sector"] == "Tech"
    assert tech["avg_weight_sum"] == pytest.approx(35.0)
    concentration = positions["concentration"]
    assert concentration["avg_position_count"] == pytest.approx(2.0)
    assert concentration["avg_top1_weight"] == pytest.approx(25.0)
    assert concentration["avg_top3_weight"] == pytest.approx(40.0)
    assert concentration["max_single_weight"] == pytest.approx(30.0)
    assert concentration["avg_max_sector_weight"] == pytest.approx(35.0)
    assert concentration["max_sector_weight"] == pytest.approx(50.0)


def test_last_pre_drawdown_snapshot_is_used_when_window_has_no_snapshot() -> None:
    positions = dda.analyze_positions(
        [_position("2021-12-31", "AAA", 0.2, 1, 10, "Tech")],
        drawdown_start=datetime.fromisoformat("2022-01-01"),
        drawdown_end=datetime.fromisoformat("2022-01-02"),
        top_n=3,
    )

    assert positions["used_pre_drawdown_snapshot"] is True
    assert positions["snapshot_count"] == 1
    assert positions["top_tickers"][0]["ticker"] == "AAA"


def test_trades_are_aggregated_in_window() -> None:
    trades = dda.analyze_trades(
        [
            {
                "date": "2021-12-31",
                "turnover": "0.9",
                "trade_cost": "9",
                "enter": "OLD",
                "exit": "",
            },
            {
                "date": "2022-01-01",
                "turnover": "0.1",
                "trade_cost": "1",
                "enter": "AAA",
                "exit": "",
            },
            {
                "date": "2022-01-02",
                "turnover": "0.3",
                "trade_cost": "2",
                "enter": "",
                "exit": "BBB",
            },
        ],
        drawdown_start=datetime.fromisoformat("2022-01-01"),
        drawdown_end=datetime.fromisoformat("2022-01-02"),
    )

    assert trades["trade_count"] == 2
    assert trades["turnover_sum"] == pytest.approx(0.4)
    assert trades["turnover_avg"] == pytest.approx(0.2)
    assert trades["trade_cost_sum"] == pytest.approx(3.0)
    assert trades["enter"] == ["AAA"]
    assert trades["exit"] == ["BBB"]


def test_missing_positions_and_trades_warn_but_do_not_abort(tmp_path: Path) -> None:
    matrix_path = _write_run_fixture(tmp_path, include_positions=False, include_trades=False)

    report = dda.build_drawdown_report(matrix_summary_path=matrix_path)

    assert len(report["phases"]) == 1
    assert report["phases"][0]["drawdowns"]
    assert any("missing positions artifact" in warning for warning in report["warnings"])
    assert any("missing trades artifact" in warning for warning in report["warnings"])


def test_json_structure_and_markdown_sections(tmp_path: Path) -> None:
    report = dda.build_drawdown_report(matrix_summary_path=_write_run_fixture(tmp_path))
    markdown = dda.build_markdown_report(report)

    assert report["strategy_profile"] == "balanced_v1"
    assert report["top_n"] == 3
    assert report["phases"][0]["phase"] == "bear_market_2022"
    assert report["phases"][0]["drawdowns"][0]["positions"]["top_tickers"]
    assert "# Drawdown Analysis - balanced_v1" in markdown
    assert "## Summary" in markdown
    assert "### Top Drawdowns" in markdown
    assert dda.SNAPSHOT_NOTE in markdown
    assert dda.ATTRIBUTION_NOTE in markdown


def _write_run_fixture(
    tmp_path: Path,
    *,
    include_positions: bool = True,
    include_trades: bool = True,
) -> Path:
    run_dir = tmp_path / "run"
    artifact_dir = run_dir / "aktien_oop"
    artifact_dir.mkdir(parents=True)
    equity = artifact_dir / "bt_monthly_15x3_equity_curve.csv"
    equity.write_text(
        "# run_id=test\n"
        "date,equity\n"
        "2022-01-01,100\n"
        "2022-01-02,80\n"
        "2022-01-03,100\n",
        encoding="utf-8",
    )
    benchmark = artifact_dir / "bt_monthly_15x3_benchmark.csv"
    benchmark.write_text(
        "# run_id=test\n"
        "date,equity,BM1_SXR8.DE\n"
        "2022-01-01,1,100\n"
        "2022-01-02,1,90\n"
        "2022-01-03,1,100\n",
        encoding="utf-8",
    )
    positions = artifact_dir / "bt_monthly_15x3_positions.csv"
    if include_positions:
        positions.write_text(
            "# run_id=test\n"
            "as_of,ticker,weight,score,rank,sector\n"
            "2022-01-01,AAA,0.2,10,1,Tech\n",
            encoding="utf-8",
        )
    trades = artifact_dir / "bt_monthly_15x3_trades.csv"
    if include_trades:
        trades.write_text(
            "# run_id=test\n"
            "date,turnover,trade_cost,enter,exit\n"
            "2022-01-02,0.1,1,AAA,\n",
            encoding="utf-8",
        )
    manifest = run_dir / "run_manifest.json"
    artifacts = {
        "equity": str(equity),
        "bench": str(benchmark),
    }
    if include_positions:
        artifacts["positions"] = str(positions)
    if include_trades:
        artifacts["trades"] = str(trades)
    manifest.write_text(json.dumps({"artifacts": artifacts}), encoding="utf-8")
    matrix = tmp_path / "matrix.json"
    matrix.write_text(
        json.dumps(
            {
                "matrix": [
                    {
                        "phase_name": "bear_market_2022",
                        "strategy_profile": "balanced_v1",
                        "phase_start": "2022-01-01",
                        "phase_end": "2022-12-31",
                        "run_id": "test",
                        "run_dir": str(run_dir),
                        "manifest_path": str(manifest),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return matrix


def _series(rows: list[tuple[str, float]]) -> list[tuple[datetime, float]]:
    return [(datetime.fromisoformat(date_value), value) for date_value, value in rows]


def _position(
    as_of: str,
    ticker: str,
    weight: float,
    rank: int,
    score: float,
    sector: str,
) -> dict[str, str]:
    return {
        "as_of": as_of,
        "ticker": ticker,
        "weight": str(weight),
        "score": str(score),
        "rank": str(rank),
        "sector": sector,
    }

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import pytest

from scripts import risk_metrics as rm


def test_csv_comment_line_is_ignored(tmp_path: Path) -> None:
    path = tmp_path / "equity.csv"
    path.write_text("# run_id=test\ndate,equity\n2022-01-01,100\n", encoding="utf-8")

    assert rm.read_csv_rows(path) == [{"date": "2022-01-01", "equity": "100"}]


def test_benchmark_column_uses_bm1_prefix_not_equity(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.csv"
    path.write_text(
        "# run_id=test\n" "date,equity,BM1_SXR8.DE\n" "2022-01-01,1,100\n",
        encoding="utf-8",
    )

    assert rm.benchmark_column_from_csv(path) == "BM1_SXR8.DE"


def test_segmenting_and_inner_join_alignment(tmp_path: Path) -> None:
    paths = _write_artifacts(
        tmp_path,
        equity_rows=[("2021-12-31", 90), ("2022-01-01", 100), ("2022-01-02", 110)],
        benchmark_rows=[
            ("2022-01-01", 1, 100),
            ("2022-01-03", 1, 130),
            ("2022-01-02", 1, 120),
        ],
    )

    portfolio = rm.load_series(
        paths["equity"], "date", "equity", start=_date("2022-01-01"), end=_date("2022-01-03")
    )
    benchmark = rm.load_series(
        paths["benchmark"],
        "date",
        "BM1_SXR8.DE",
        start=_date("2022-01-01"),
        end=_date("2022-01-03"),
    )

    aligned_p, aligned_b = rm.align_series(portfolio, benchmark)

    assert [date.date().isoformat() for date, _ in aligned_p] == ["2022-01-01", "2022-01-02"]
    assert [value for _, value in aligned_p] == [100, 110]
    assert [value for _, value in aligned_b] == [100, 120]


def test_total_return_cagr_maxdd_calmar_ulcer_pain_tuw_downside_sortino() -> None:
    series = _series(
        [
            ("2022-01-01", 100),
            ("2022-01-02", 110),
            ("2022-01-03", 88),
            ("2022-01-04", 132),
        ]
    )

    metrics = rm.series_risk_metrics(
        series,
        min_drawdown_depth_pct=-1.0,
        phase_end=_date("2022-01-04"),
    )

    cagr = (1.32 ** (365.25 / 3)) - 1.0
    drawdowns = [0.0, 0.0, -0.2, 0.0]
    downside_vol = math.sqrt((min(0.1, 0) ** 2 + min(-0.2, 0) ** 2 + min(0.5, 0) ** 2) / 3)
    downside_vol *= math.sqrt(252.0)
    assert metrics["total_return_pct"] == pytest.approx(32.0)
    assert metrics["cagr_pct"] == pytest.approx(cagr * 100.0)
    assert metrics["max_drawdown_pct"] == pytest.approx(-20.0)
    assert metrics["calmar_ratio"] == pytest.approx(cagr / 0.2)
    assert metrics["ulcer_index_pct"] == pytest.approx(
        math.sqrt(sum(value * value for value in drawdowns) / 4) * 100.0
    )
    assert metrics["pain_index_pct"] == pytest.approx(5.0)
    assert metrics["time_under_water_observations"] == 1
    assert metrics["time_under_water_pct"] == pytest.approx(25.0)
    assert metrics["downside_volatility_pct"] == pytest.approx(downside_vol * 100.0)
    assert metrics["sortino_ratio"] == pytest.approx(cagr / downside_vol)


def test_calmar_allows_negative_cagr_and_returns_null_for_zero_drawdown() -> None:
    assert rm.calmar_ratio(-0.10, -0.20) == pytest.approx(-0.5)
    assert rm.calmar_ratio(0.10, 0.0) is None


def test_time_under_water_uses_eps() -> None:
    metrics = rm.series_risk_metrics(
        _series([("2022-01-01", 1.0), ("2022-01-02", 1.0 - rm.EPS / 2)]),
        min_drawdown_depth_pct=-1.0,
        phase_end=_date("2022-01-02"),
    )

    assert metrics["time_under_water_observations"] == 0


def test_recovery_duration_and_unrecovered_distribution() -> None:
    distribution = rm.drawdown_distribution(
        _series(
            [
                ("2022-01-01", 100),
                ("2022-01-02", 80),
                ("2022-01-03", 100),
                ("2022-01-04", 90),
            ]
        ),
        min_drawdown_depth_pct=-1.0,
        phase_end=_date("2022-01-05"),
    )

    assert distribution["drawdown_count"] == 2
    assert distribution["recovered_drawdown_count"] == 1
    assert distribution["unrecovered_drawdown_count"] == 1
    assert distribution["avg_recovery_duration_days"] == pytest.approx(1.0)
    assert distribution["current_unrecovered_duration_days"] == 2


def test_distribution_ignores_mini_drawdowns_above_threshold() -> None:
    distribution = rm.drawdown_distribution(
        _series(
            [
                ("2022-01-01", 100),
                ("2022-01-02", 99.5),
                ("2022-01-03", 100),
                ("2022-01-04", 98),
            ]
        ),
        min_drawdown_depth_pct=-1.0,
        phase_end=_date("2022-01-04"),
    )

    assert distribution["drawdown_count"] == 1
    assert distribution["max_drawdown_depth_pct"] == pytest.approx(-2.0)


def test_downside_and_upside_capture() -> None:
    portfolio = _series([("2022-01-01", 100), ("2022-01-02", 95), ("2022-01-03", 104.5)])
    benchmark = _series([("2022-01-01", 100), ("2022-01-02", 90), ("2022-01-03", 99)])

    capture, warnings = rm.capture_ratios(portfolio, benchmark)

    assert warnings == []
    assert capture["downside_capture"] == pytest.approx(0.5)
    assert capture["upside_capture"] == pytest.approx(1.0)


def test_turnover_during_and_outside_drawdowns(tmp_path: Path) -> None:
    trades = tmp_path / "trades.csv"
    trades.write_text(
        "# run_id=test\n"
        "date,turnover,trade_cost,enter,exit\n"
        "2022-01-02,0.2,0,,\n"
        "2022-01-04,0.4,0,,\n",
        encoding="utf-8",
    )

    turnover = rm.turnover_stress_check(
        trades_path=trades,
        portfolio_series=_series(
            [
                ("2022-01-01", 100),
                ("2022-01-02", 80),
                ("2022-01-03", 100),
                ("2022-01-04", 110),
            ]
        ),
        min_drawdown_depth_pct=-1.0,
        phase_start=_date("2022-01-01"),
        phase_end=_date("2022-01-04"),
    )

    assert turnover["avg_during_drawdowns"] == pytest.approx(0.2)
    assert turnover["avg_outside_drawdowns"] == pytest.approx(0.4)
    assert turnover["ratio_drawdown_vs_outside"] == pytest.approx(0.5)
    assert turnover["trade_count_during_drawdowns"] == 1
    assert turnover["trade_count_outside_drawdowns"] == 1


def test_missing_benchmark_data_is_robust(tmp_path: Path) -> None:
    matrix = _write_run_fixture(tmp_path, include_benchmark=False)

    report = rm.build_risk_metrics_report(matrix_summary_path=matrix)
    phase = report["phases"][0]

    assert phase["portfolio"]["total_return_pct"] == pytest.approx(20.0)
    assert phase["benchmark"]["total_return_pct"] is None
    assert phase["relative"]["total_return_delta_pct"] is None
    assert any("missing benchmark artifact" in warning for warning in phase["warnings"])


def test_too_short_series_returns_nulls() -> None:
    metrics = rm.series_risk_metrics(
        _series([("2022-01-01", 100)]),
        min_drawdown_depth_pct=-1.0,
        phase_end=_date("2022-01-01"),
    )

    assert metrics["total_return_pct"] is None
    assert metrics["cagr_pct"] is None
    assert metrics["observation_count"] == 1


def test_json_structure_and_markdown_sections(tmp_path: Path) -> None:
    report = rm.build_risk_metrics_report(
        matrix_summary_path=_write_run_fixture(tmp_path),
        generated_at="2026-06-13T10:00:00",
    )
    markdown = rm.build_markdown_report(report)

    assert report["strategy_profile"] == "balanced_v1"
    assert report["settings"]["drawdown_episode_min_depth_pct"] == -1.0
    assert report["phases"][0]["portfolio"]["drawdown_distribution"]
    assert "## Risk Summary" in markdown
    assert "## Drawdown Duration Distribution" in markdown
    assert "## Turnover Stress Check" in markdown


def _write_run_fixture(
    tmp_path: Path,
    *,
    include_benchmark: bool = True,
) -> Path:
    run_dir = tmp_path / "run"
    artifact_dir = run_dir / "aktien_oop"
    artifact_dir.mkdir(parents=True)
    paths = _write_artifacts(
        artifact_dir,
        equity_rows=[("2022-01-01", 100), ("2022-01-02", 80), ("2022-01-03", 120)],
        benchmark_rows=(
            [("2022-01-01", 1, 100), ("2022-01-02", 1, 90), ("2022-01-03", 1, 110)]
            if include_benchmark
            else None
        ),
        trade_rows=[("2022-01-02", 0.2), ("2022-01-03", 0.4)],
    )
    artifacts = {"equity": str(paths["equity"]), "trades": str(paths["trades"])}
    if include_benchmark:
        artifacts["bench"] = str(paths["benchmark"])
    manifest = run_dir / "run_manifest.json"
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
                        "phase_end": "2022-01-03",
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


def _write_artifacts(
    root: Path,
    *,
    equity_rows: list[tuple[str, float]],
    benchmark_rows: list[tuple[str, float, float]] | None = None,
    trade_rows: list[tuple[str, float]] | None = None,
) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    equity = root / "bt_monthly_15x3_equity_curve.csv"
    equity.write_text(
        "# run_id=test\n"
        "date,equity\n"
        + "".join(f"{date_value},{equity_value}\n" for date_value, equity_value in equity_rows),
        encoding="utf-8",
    )
    result = {"equity": equity}
    if benchmark_rows is not None:
        benchmark = root / "bt_monthly_15x3_benchmark.csv"
        benchmark.write_text(
            "# run_id=test\n"
            "date,equity,BM1_SXR8.DE\n"
            + "".join(
                f"{date_value},{equity_value},{benchmark_value}\n"
                for date_value, equity_value, benchmark_value in benchmark_rows
            ),
            encoding="utf-8",
        )
        result["benchmark"] = benchmark
    if trade_rows is not None:
        trades = root / "bt_monthly_15x3_trades.csv"
        trades.write_text(
            "# run_id=test\n"
            "date,turnover,trade_cost,enter,exit\n"
            + "".join(f"{date_value},{turnover},0,,\n" for date_value, turnover in trade_rows),
            encoding="utf-8",
        )
        result["trades"] = trades
    return result


def _series(rows: list[tuple[str, float]]) -> list[tuple[datetime, float]]:
    return [(datetime.fromisoformat(date_value), value) for date_value, value in rows]


def _date(value: str) -> datetime:
    return datetime.fromisoformat(value)

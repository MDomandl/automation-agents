from pathlib import Path

from scripts.run_max_per_sector_testmatrix import (
    SectorMetrics,
    SectorRunResult,
    build_summary,
    calculate_sector_metrics_from_positions_csv,
    calculate_sector_metrics_from_weights,
    replace_sector_limits,
)


def test_replace_sector_limits_updates_limits_section_only() -> None:
    text = "\n".join(
        [
            "[limits]",
            "use_sector_limits = true",
            "max_per_sector = 3           # 0 oder negativ = deaktiviert",
            "",
            "[other]",
            "use_sector_limits = true",
            "max_per_sector = 99",
        ]
    )

    updated = replace_sector_limits(text, use_sector_limits=False, max_per_sector=None)

    assert "use_sector_limits = false" in updated
    assert "max_per_sector = 0  # 0 oder negativ = deaktiviert" in updated
    assert "[other]\nuse_sector_limits = true\nmax_per_sector = 99" in updated


def test_build_summary_contains_sector_settings_and_winners() -> None:
    results = [
        SectorRunResult(
            test_id="S1",
            sector_variant="strict",
            max_per_sector=2,
            use_sector_limits=True,
            profile="SHORT",
            run_id="20260519_010101",
            report_path=Path("reports/sector_02_SHORT.md"),
            total_return_pct=8.0,
            cagr_pct=16.0,
            alpha_pct=-2.0,
            max_drawdown_pct=-8.0,
            volatility_pct=14.0,
            sharpe_ratio=1.0,
            turnover_pct=25.0,
            benchmark_cagr_pct=15.0,
            benchmark_max_drawdown_pct=-20.0,
            benchmark_sharpe_ratio=0.7,
            up_capture_ratio=0.8,
            down_capture_ratio=0.4,
            success=True,
        ),
        SectorRunResult(
            test_id="S2",
            sector_variant="off",
            max_per_sector=None,
            use_sector_limits=False,
            profile="SHORT",
            run_id="20260519_020202",
            report_path=Path("reports/sector_off_SHORT.md"),
            total_return_pct=10.0,
            cagr_pct=20.0,
            alpha_pct=-1.0,
            max_drawdown_pct=-12.0,
            volatility_pct=18.0,
            sharpe_ratio=0.8,
            turnover_pct=40.0,
            benchmark_cagr_pct=15.0,
            benchmark_max_drawdown_pct=-20.0,
            benchmark_sharpe_ratio=0.7,
            up_capture_ratio=0.9,
            down_capture_ratio=0.6,
            success=True,
        ),
    ]

    summary = build_summary(results)

    assert "sector_variant" in summary
    assert "use_sector_limits" in summary
    assert "Max Sector Weight" in summary
    assert "Dominant Sector" in summary
    assert "Sector Count" in summary
    assert "Sector Distribution" in summary
    assert "| strict | 2 | true | SHORT |" in summary
    assert "| SHORT | off | 2 | 2 | 2 |" in summary


def test_calculate_sector_metrics_from_weights_and_meta() -> None:
    metrics = calculate_sector_metrics_from_weights(
        {"AAPL": 0.30, "MSFT": 0.20, "JPM": 0.10, "CASH": 0.40},
        {
            "AAPL": "Information Technology",
            "MSFT": "Information Technology",
            "JPM": "Financials",
        },
        source="decision_bundle_final_weights",
    )

    assert metrics.max_sector_weight_pct == 50.0
    assert metrics.dominant_sector == "Information Technology"
    assert metrics.sector_count == 2
    assert metrics.sector_distribution_pct == {
        "Information Technology": 50.0,
        "Financials": 10.0,
    }
    assert metrics.max_sector_positions == 2
    assert metrics.dominant_sector_positions == 2
    assert metrics.source == "decision_bundle_final_weights"


def test_calculate_sector_metrics_uses_unknown_for_missing_sector() -> None:
    metrics = calculate_sector_metrics_from_weights(
        {"AAPL": 0.25, "MISSING": 0.35},
        {"AAPL": "Information Technology"},
        source="decision_bundle_final_weights",
    )

    assert metrics.dominant_sector == "Unknown"
    assert metrics.sector_distribution_pct == {
        "Unknown": 35.0,
        "Information Technology": 25.0,
    }


def test_calculate_sector_metrics_from_positions_csv_missing_weight_is_na(tmp_path: Path) -> None:
    path = tmp_path / "positions.csv"
    path.write_text(
        "\n".join(
            [
                "as_of,ticker,weight,sector",
                "2025-10-08,AAPL,,Information Technology",
                "2025-10-08,JPM,0.2,Financials",
            ]
        ),
        encoding="utf-8",
    )

    metrics = calculate_sector_metrics_from_positions_csv(path)

    assert metrics.max_sector_weight_pct is None
    assert metrics.dominant_sector is None
    assert metrics.sector_count is None
    assert metrics.warning == "missing weight data"


def test_build_summary_renders_sector_metrics() -> None:
    result = SectorRunResult(
        test_id="S1",
        sector_variant="strict",
        max_per_sector=2,
        use_sector_limits=True,
        profile="MEDIUM",
        run_id="20260519_010101",
        report_path=Path("reports/sector_02_MEDIUM.md"),
        total_return_pct=8.0,
        cagr_pct=16.0,
        alpha_pct=-2.0,
        max_drawdown_pct=-8.0,
        volatility_pct=14.0,
        sharpe_ratio=1.0,
        turnover_pct=25.0,
        benchmark_cagr_pct=15.0,
        benchmark_max_drawdown_pct=-20.0,
        benchmark_sharpe_ratio=0.7,
        up_capture_ratio=0.8,
        down_capture_ratio=0.4,
        success=True,
        sector_metrics=SectorMetrics(
            max_sector_weight_pct=28.5,
            dominant_sector="Information Technology",
            sector_count=6,
            sector_distribution_pct={
                "Information Technology": 28.5,
                "Financials": 18.2,
            },
            max_sector_positions=3,
            dominant_sector_positions=3,
            source="decision_bundle_final_weights",
        ),
    )

    summary = build_summary([result])

    assert "28.50%" in summary
    assert "Information Technology" in summary
    assert "Information Technology=28.50%; Financials=18.20%" in summary

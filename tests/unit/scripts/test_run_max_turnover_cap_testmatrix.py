from pathlib import Path

from scripts.run_max_per_sector_testmatrix import SectorMetrics
from scripts.run_max_turnover_cap_testmatrix import (
    TurnoverRunResult,
    build_summary,
    replace_benchmark,
    replace_max_turnover_cap,
)


def test_replace_max_turnover_cap_updates_existing_lines() -> None:
    text = "\n".join(
        [
            "top_k = 15",
            "max_turnover_cap = 0.40   # root value",
            "",
            "[limits]",
            "max_turnover_cap   = 0.40",
            "max_per_sector = 2",
        ]
    )

    updated = replace_max_turnover_cap(text, 0.20)

    assert updated.startswith("top_k = 15\nmax_turnover_cap = 0.20")
    assert "max_turnover_cap = 0.20  # root value" in updated
    assert "max_turnover_cap   = 0.20" in updated
    assert "max_per_sector = 2" in updated


def test_replace_max_turnover_cap_inserts_missing_root_value_before_first_section() -> None:
    updated = replace_max_turnover_cap("[limits]\nmax_per_sector = 2\n", 0.0)

    assert updated.startswith("max_turnover_cap = 0.00\n[limits]")


def test_replace_benchmark_updates_known_benchmark_keys_only() -> None:
    text = "\n".join(
        [
            'benchmark_ticker  = "SPY"   # primary',
            'benchmark2 = "SPY"',
            'other_benchmark_ticker = "QQQ"',
        ]
    )

    updated = replace_benchmark(text, "SXR8.DE")

    assert 'benchmark_ticker  = "SXR8.DE"  # primary' in updated
    assert 'benchmark2 = "SXR8.DE"' in updated
    assert 'other_benchmark_ticker = "QQQ"' in updated


def test_build_summary_contains_turnover_columns_sector_metrics_and_winners() -> None:
    results = [
        TurnoverRunResult(
            test_id="T1",
            turnover_variant="sehr ruhig",
            max_turnover_cap=0.20,
            profile="SHORT",
            run_id="20260528_010101",
            report_path=Path("reports/turnover_020_SHORT.md"),
            total_return_pct=8.0,
            cagr_pct=16.0,
            alpha_pct=-2.0,
            max_drawdown_pct=-8.0,
            volatility_pct=14.0,
            sharpe_ratio=1.0,
            turnover_pct=20.0,
            trades_count=12,
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
            ),
        ),
        TurnoverRunResult(
            test_id="T2",
            turnover_variant="off",
            max_turnover_cap=0.0,
            profile="SHORT",
            run_id="20260528_020202",
            report_path=Path("reports/turnover_off_SHORT.md"),
            total_return_pct=10.0,
            cagr_pct=20.0,
            alpha_pct=-1.0,
            max_drawdown_pct=-12.0,
            volatility_pct=18.0,
            sharpe_ratio=0.8,
            turnover_pct=40.0,
            trades_count=18,
            benchmark_cagr_pct=15.0,
            benchmark_max_drawdown_pct=-20.0,
            benchmark_sharpe_ratio=0.7,
            up_capture_ratio=0.9,
            down_capture_ratio=0.6,
            success=True,
            sector_metrics=SectorMetrics(
                max_sector_weight_pct=30.0,
                dominant_sector="Financials",
                sector_count=5,
            ),
        ),
    ]

    summary = build_summary(results)

    assert "max_turnover_cap Sensitivity Matrix" in summary
    assert "Trades Count" in summary
    assert "Max Sector Weight" in summary
    assert "Dominant Sector" in summary
    assert "Sector Count" in summary
    assert "| sehr ruhig | 0.20 | SHORT | 20260528_010101 |" in summary
    assert "| off | off | SHORT | 20260528_020202 |" in summary
    assert "| SHORT | off | sehr ruhig | sehr ruhig | sehr ruhig |" in summary

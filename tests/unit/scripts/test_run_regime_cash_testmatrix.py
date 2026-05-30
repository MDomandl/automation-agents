from pathlib import Path

from scripts.run_max_per_sector_testmatrix import SectorMetrics
from scripts.run_regime_cash_testmatrix import (
    CashMetrics,
    RegimeRunResult,
    RegimeVariant,
    build_summary,
    replace_regime_cash,
)


def test_replace_regime_cash_updates_root_and_regime_section() -> None:
    text = "\n".join(
        [
            'benchmark_ticker = "SPY"',
            "include_cash = false",
            "",
            "[regime]",
            "require_above_sma = false",
            "regime_sma_days = 100",
            'regime_below_action = "HOLD"',
        ]
    )
    variant = RegimeVariant(
        name="defensiv_cash",
        file_stem="regime_defensive_cash",
        require_above_sma=True,
        regime_below_action="SELL",
        include_cash=True,
        character="risk-off cash",
    )

    updated = replace_regime_cash(text, variant)

    assert "include_cash = true" in updated
    assert "cash_yield_annual = 0.00" in updated
    assert "require_above_sma = true" in updated
    assert "regime_sma_days = 200" in updated
    assert 'regime_below_action = "SELL"' in updated


def test_replace_regime_cash_inserts_missing_regime_section() -> None:
    variant = RegimeVariant(
        name="immer_investiert",
        file_stem="regime_always_invested",
        require_above_sma=False,
        regime_below_action="HOLD",
        include_cash=False,
        character="always invested",
    )

    updated = replace_regime_cash("top_k = 15\n", variant)

    assert "include_cash = false" in updated
    assert "[regime]" in updated
    assert "require_above_sma = false" in updated
    assert 'regime_below_action = "HOLD"' in updated


def test_build_summary_contains_requested_regime_cash_columns_and_skips() -> None:
    result = RegimeRunResult(
        test_id="R1",
        regime_variant="defensiv_cash",
        require_above_sma=True,
        regime_below_action="SELL",
        include_cash=True,
        profile="SHORT",
        run_id="20260530_010101",
        report_path=Path("reports/regime_defensive_cash_SHORT.md"),
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
        cash_metrics=CashMetrics(
            average_cash_pct=10.0,
            max_cash_pct=100.0,
            time_in_market_pct=90.0,
            time_in_cash_pct=10.0,
            regime_off_count=2,
            regime_switch_count=1,
        ),
    )
    skipped = [
        RegimeVariant(
            name="cash_variante",
            file_stem="regime_cash_variant",
            require_above_sma=False,
            regime_below_action="HOLD",
            include_cash=True,
            character="cash without regime",
            skip_reason="unsupported",
        )
    ]

    summary = build_summary([result], skipped)

    assert "Regime/Cash Sensitivity Matrix" in summary
    assert "Average Cash" in summary
    assert "Time in Market" in summary
    assert "Regime Off Count" in summary
    assert "| defensiv_cash | true | SELL | true | SHORT | 20260530_010101 |" in summary
    assert "| cash_variante | unsupported |" in summary

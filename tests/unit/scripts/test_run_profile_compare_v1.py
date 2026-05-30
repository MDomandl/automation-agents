from pathlib import Path

from scripts.run_max_per_sector_testmatrix import SectorMetrics
from scripts.run_profile_compare_v1 import (
    PROFILE_CONFIG_PATHS,
    ProfileRunResult,
    StrategyProfile,
    _write_matrix_config,
    build_summary,
    load_strategy_profile,
)
from scripts.run_regime_cash_testmatrix import CashMetrics


def test_write_matrix_config_applies_profile_compare_baseline(tmp_path: Path) -> None:
    config_path = tmp_path / "backtest_config.toml"
    config_path.write_text(
        "\n".join(
            [
                'benchmark_ticker = "SPY"',
                "benchmark2 = \"SPY\"",
                "top_k = 8",
                "max_turnover_cap = 0.35",
                "include_cash = false",
                "",
                "[universe]",
                'name = "sp500_top100"',
                'tickers_file = "aktien_oop/universes/sp500_tickers_top100.txt"',
                'meta_file = "aktien_oop/universes/sp500_meta_top100.csv"',
                "",
                "[limits]",
                "use_sector_limits = false",
                "max_per_sector = 4",
                "",
                "[regime]",
                "require_above_sma = false",
                "regime_sma_days = 100",
                'regime_below_action = "HOLD"',
            ]
        ),
        encoding="utf-8",
    )
    profile = StrategyProfile(
        name="conservative_v1",
        label="Conservative v1",
        file_stem="profile_conservative",
        universe="sp500",
        top_k=15,
        use_sector_limits=True,
        max_per_sector=2,
        max_turnover_cap=0.20,
        require_above_sma=True,
        regime_below_action="SELL",
        include_cash=True,
        cash_yield_annual=0.00,
        regime_sma_days=200,
        benchmark_ticker="SXR8.DE",
    )

    _write_matrix_config(config_path, profile)

    updated = config_path.read_text(encoding="utf-8")
    assert 'name = "sp500"' in updated
    assert 'tickers_file = "aktien_oop/universes/sp500_tickers.txt"' in updated
    assert "top_k = 15" in updated
    assert "use_sector_limits = true" in updated
    assert "max_per_sector = 2" in updated
    assert "max_turnover_cap = 0.20" in updated
    assert 'benchmark_ticker = "SXR8.DE"' in updated
    assert 'benchmark2 = "SXR8.DE"' in updated
    assert "include_cash = true" in updated
    assert "cash_yield_annual = 0.00" in updated
    assert "require_above_sma = true" in updated
    assert "regime_sma_days = 200" in updated
    assert 'regime_below_action = "SELL"' in updated


def test_all_profile_files_can_be_loaded() -> None:
    profiles = [load_strategy_profile(path) for path in PROFILE_CONFIG_PATHS]

    assert [profile.label for profile in profiles] == [
        "Conservative v1",
        "Balanced v1",
        "Offensive v1",
    ]
    assert [profile.name for profile in profiles] == [
        "conservative_v1",
        "balanced_v1",
        "offensive_v1",
    ]


def test_load_strategy_profile_validates_required_keys(tmp_path: Path) -> None:
    profile_path = tmp_path / "broken.toml"
    profile_path.write_text('profile_name = "broken"\n', encoding="utf-8")

    try:
        load_strategy_profile(profile_path)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected invalid profile to raise ValueError")

    assert "missing required keys" in message
    assert "profile_label" in message
    assert "benchmark_ticker" in message


def test_load_strategy_profile_rejects_invalid_regime_below_action(tmp_path: Path) -> None:
    profile_path = tmp_path / "invalid_action.toml"
    profile_path.write_text(
        "\n".join(
            [
                'profile_name = "invalid"',
                'profile_label = "Invalid"',
                'universe = "sp500"',
                "top_k = 15",
                "use_sector_limits = true",
                "max_per_sector = 2",
                "max_turnover_cap = 0.20",
                "require_above_sma = true",
                'regime_below_action = "CASH"',
                "include_cash = true",
                "cash_yield_annual = 0.00",
                "regime_sma_days = 200",
                'benchmark_ticker = "SXR8.DE"',
            ]
        ),
        encoding="utf-8",
    )

    try:
        load_strategy_profile(profile_path)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected invalid regime_below_action to raise ValueError")

    assert "regime_below_action" in message
    assert "SELL" in message
    assert "HOLD" in message


def test_build_summary_contains_requested_columns_and_winner_overview() -> None:
    results = [
        _result(
            "P1",
            "conservative",
            "Conservative v1",
            "SHORT",
            "20260530_010001",
            total_return=8.0,
            cagr=5.0,
            drawdown=-6.0,
            sharpe=0.8,
            down_capture=0.4,
            turnover=12.0,
            average_cash=20.0,
        ),
        _result(
            "P4",
            "balanced",
            "Balanced v1",
            "SHORT",
            "20260530_010002",
            total_return=10.0,
            cagr=7.0,
            drawdown=-8.0,
            sharpe=1.0,
            down_capture=0.55,
            turnover=15.0,
            average_cash=0.0,
        ),
        _result(
            "P7",
            "offensive",
            "Offensive v1",
            "SHORT",
            "20260530_010003",
            total_return=12.0,
            cagr=9.0,
            drawdown=-12.0,
            sharpe=0.9,
            down_capture=0.8,
            turnover=18.0,
            average_cash=0.0,
        ),
    ]

    summary = build_summary(results)

    assert "# Profile Compare v1" in summary
    assert "Average Cash" in summary
    assert "Time in Market" in summary
    assert "Lowest Down Capture" in summary
    assert "Lowest Turnover" in summary
    assert "| Conservative v1 | SHORT | 20260530_010001 |" in summary
    assert (
        "| SHORT | Offensive v1 | Conservative v1 | Balanced v1 | "
        "Conservative v1 | Conservative v1 |"
    ) in summary
    assert "| Conservative v1 | true | SELL | true |" in summary
    assert "| Balanced v1 | true | HOLD | false |" in summary
    assert "| Offensive v1 | false | HOLD | false |" in summary


def _result(
    test_id: str,
    profile_name: str,
    profile_label: str,
    profile: str,
    run_id: str,
    *,
    total_return: float,
    cagr: float,
    drawdown: float,
    sharpe: float,
    down_capture: float,
    turnover: float,
    average_cash: float,
) -> ProfileRunResult:
    return ProfileRunResult(
        test_id=test_id,
        profile_name=profile_name,
        profile_label=profile_label,
        require_above_sma=profile_name != "offensive",
        regime_below_action="SELL" if profile_name == "conservative" else "HOLD",
        include_cash=profile_name == "conservative",
        profile=profile,
        run_id=run_id,
        report_path=Path(f"reports/{profile_label}_{profile}.md"),
        total_return_pct=total_return,
        cagr_pct=cagr,
        alpha_pct=1.0,
        max_drawdown_pct=drawdown,
        volatility_pct=11.0,
        sharpe_ratio=sharpe,
        turnover_pct=turnover,
        trades_count=10,
        benchmark_cagr_pct=6.0,
        benchmark_max_drawdown_pct=-10.0,
        benchmark_sharpe_ratio=0.7,
        up_capture_ratio=0.9,
        down_capture_ratio=down_capture,
        success=True,
        sector_metrics=SectorMetrics(
            max_sector_weight_pct=20.0,
            dominant_sector="Information Technology",
            sector_count=8,
        ),
        cash_metrics=CashMetrics(
            average_cash_pct=average_cash,
            max_cash_pct=100.0 if average_cash else 0.0,
            time_in_market_pct=80.0 if average_cash else 100.0,
            time_in_cash_pct=20.0 if average_cash else 0.0,
        ),
    )

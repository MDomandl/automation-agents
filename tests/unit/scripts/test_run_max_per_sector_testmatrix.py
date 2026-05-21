from pathlib import Path

from scripts.run_max_per_sector_testmatrix import (
    SectorRunResult,
    build_summary,
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
    assert "| strict | 2 | true | SHORT |" in summary
    assert "| SHORT | off | 2 | 2 | 2 |" in summary

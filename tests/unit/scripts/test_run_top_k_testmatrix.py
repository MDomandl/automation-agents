from pathlib import Path

from scripts.run_top_k_testmatrix import TopKRunResult, build_summary, replace_top_k


def test_replace_top_k_updates_root_and_topk_section_only() -> None:
    text = "\n".join(
        [
            "top_k = 12",
            "buffer_k = 3",
            "",
            "[topk]",
            "top_k         = 12           # Anzahl Aktien im Portfolio",
            "buffer_k = 3",
            "",
            "[other]",
            "top_k = 99",
        ]
    )

    updated = replace_top_k(text, 15)

    assert "top_k = 15" in updated
    assert "top_k         = 15  # Anzahl Aktien im Portfolio" in updated
    assert "[other]\ntop_k = 99" in updated


def test_build_summary_contains_metrics_and_winners() -> None:
    results = [
        TopKRunResult(
            test_id="K1",
            top_k=8,
            profile="SHORT",
            run_id="20260518_010101",
            report_path=Path("reports/top_k_08_SHORT.md"),
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
        TopKRunResult(
            test_id="K2",
            top_k=15,
            profile="SHORT",
            run_id="20260518_020202",
            report_path=Path("reports/top_k_15_SHORT.md"),
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
    ]

    summary = build_summary(results)

    assert "Total Return" in summary
    assert "Benchmark Drawdown" in summary
    assert "| SHORT | 8 | 15 | 15 | 15 |" in summary

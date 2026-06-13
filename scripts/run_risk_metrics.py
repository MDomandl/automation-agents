from __future__ import annotations

import argparse
from pathlib import Path

from scripts.risk_metrics import build_risk_metrics_report, write_reports

DEFAULT_MATRIX_SUMMARY = (
    Path("reports")
    / "strategy_analysis"
    / "market_phase_matrix"
    / "market_phase_matrix_summary.json"
)
DEFAULT_OUTPUT_DIR = Path("reports") / "strategy_analysis" / "risk_metrics"
DEFAULT_STRATEGY_PROFILE = "balanced_v1"
DEFAULT_MIN_DRAWDOWN_DEPTH_PCT = -1.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build phase-only risk metrics for a strategy profile."
    )
    parser.add_argument(
        "--matrix-summary",
        default=str(DEFAULT_MATRIX_SUMMARY),
        help="Path to market_phase_matrix_summary.json.",
    )
    parser.add_argument(
        "--strategy-profile",
        default=DEFAULT_STRATEGY_PROFILE,
        help="Strategy profile to analyze. Defaults to balanced_v1.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for risk metrics reports.",
    )
    parser.add_argument(
        "--min-drawdown-depth-pct",
        type=float,
        default=DEFAULT_MIN_DRAWDOWN_DEPTH_PCT,
        help="Drawdown episode threshold in percent points. Defaults to -1.0.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_risk_metrics_report(
        matrix_summary_path=Path(args.matrix_summary),
        strategy_profile=args.strategy_profile,
        min_drawdown_depth_pct=args.min_drawdown_depth_pct,
    )
    md_path, json_path = write_reports(report, Path(args.output_dir))
    print(f"Markdown report: {md_path.as_posix()}")
    print(f"JSON report: {json_path.as_posix()}")
    if report["warnings"]:
        print(f"Warnings: {len(report['warnings'])}")


if __name__ == "__main__":
    main()

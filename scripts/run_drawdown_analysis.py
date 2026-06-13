from __future__ import annotations

import argparse
from pathlib import Path

from scripts.drawdown_analysis import build_drawdown_report, write_reports

DEFAULT_MATRIX_SUMMARY = (
    Path("reports")
    / "strategy_analysis"
    / "market_phase_matrix"
    / "market_phase_matrix_summary.json"
)
DEFAULT_OUTPUT_DIR = Path("reports") / "strategy_analysis" / "drawdown_analysis"
DEFAULT_STRATEGY_PROFILE = "balanced_v1"
DEFAULT_TOP_N = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze drawdown episodes for a strategy profile."
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
        help="Directory for drawdown analysis reports.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=DEFAULT_TOP_N,
        help="Number of distinct drawdown episodes per phase. Defaults to 3.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_drawdown_report(
        matrix_summary_path=Path(args.matrix_summary),
        strategy_profile=args.strategy_profile,
        top_n=args.top_n,
    )
    md_path, json_path = write_reports(report, Path(args.output_dir))
    print(f"Markdown report: {md_path.as_posix()}")
    print(f"JSON report: {json_path.as_posix()}")
    if report["warnings"]:
        print(f"Warnings: {len(report['warnings'])}")


if __name__ == "__main__":
    main()

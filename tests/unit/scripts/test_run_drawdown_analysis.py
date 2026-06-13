from __future__ import annotations

import json
from pathlib import Path

from scripts import run_drawdown_analysis as runner


def test_cli_writes_markdown_and_json(tmp_path: Path, monkeypatch) -> None:
    matrix = tmp_path / "matrix.json"
    output_dir = tmp_path / "out"
    matrix.write_text('{"matrix": []}', encoding="utf-8")

    def fake_build_drawdown_report(*, matrix_summary_path, strategy_profile, top_n):
        assert matrix_summary_path == matrix
        assert strategy_profile == "balanced_v1"
        assert top_n == 3
        return {
            "generated_at": "2026-06-11T10:00:00",
            "strategy_profile": "balanced_v1",
            "matrix_summary": str(matrix),
            "top_n": 3,
            "phases": [],
            "warnings": [],
        }

    monkeypatch.setattr(runner, "build_drawdown_report", fake_build_drawdown_report)
    monkeypatch.setattr(
        runner,
        "parse_args",
        lambda: runner.argparse.Namespace(
            matrix_summary=str(matrix),
            strategy_profile="balanced_v1",
            output_dir=str(output_dir),
            top_n=3,
        ),
    )

    runner.main()

    json_path = output_dir / "balanced_v1_drawdown_analysis.json"
    md_path = output_dir / "balanced_v1_drawdown_analysis.md"
    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["strategy_profile"] == "balanced_v1"
    assert "# Drawdown Analysis - balanced_v1" in md_path.read_text(encoding="utf-8")

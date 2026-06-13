from __future__ import annotations

import json
from pathlib import Path

from scripts import run_risk_metrics as runner


def test_cli_writes_markdown_and_json(tmp_path: Path, monkeypatch) -> None:
    matrix = tmp_path / "matrix.json"
    output_dir = tmp_path / "out"
    matrix.write_text('{"matrix": []}', encoding="utf-8")

    def fake_build_risk_metrics_report(
        *,
        matrix_summary_path,
        strategy_profile,
        min_drawdown_depth_pct,
    ):
        assert matrix_summary_path == matrix
        assert strategy_profile == "balanced_v1"
        assert min_drawdown_depth_pct == -1.0
        return {
            "strategy_profile": "balanced_v1",
            "generated_at": "2026-06-13T10:00:00",
            "source_matrix_summary": str(matrix),
            "settings": {},
            "phases": [],
            "warnings": [],
        }

    monkeypatch.setattr(runner, "build_risk_metrics_report", fake_build_risk_metrics_report)
    monkeypatch.setattr(
        runner,
        "parse_args",
        lambda: runner.argparse.Namespace(
            matrix_summary=str(matrix),
            strategy_profile="balanced_v1",
            output_dir=str(output_dir),
            min_drawdown_depth_pct=-1.0,
        ),
    )

    runner.main()

    json_path = output_dir / "balanced_v1_risk_metrics.json"
    md_path = output_dir / "balanced_v1_risk_metrics.md"
    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8"))["strategy_profile"] == "balanced_v1"
    assert "# Risk Metrics - balanced_v1" in md_path.read_text(encoding="utf-8")

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from scripts.analyze_friction_eps import build_analysis
from scripts.analyze_friction_eps import main
from scripts.analyze_friction_eps import resolve_run_paths
from scripts.analyze_friction_eps import resolve_selected_as_ofs
from scripts.analyze_friction_eps import write_analysis_csv


def test_analyzer_builds_rows_from_current_run_artifacts(tmp_path: Path) -> None:
    run_dir = tmp_path / "automation_runs" / "2026-04-23_22-30-40_medium"
    manifest_path, aktien_oop_dir, decisions_dir = _build_sample_run(run_dir)

    run_paths = resolve_run_paths(manifest_path=manifest_path)
    as_ofs = resolve_selected_as_ofs(run_paths, None)
    rows = build_analysis(run_paths, as_ofs)

    assert as_ofs == ["2025-10-08"]
    assert rows
    by_ticker = {row.ticker: row for row in rows}

    cvs_row = by_ticker["CVS"]
    assert cvs_row.as_of == "2025-10-08"
    assert cvs_row.target_weight_bt == 0.08333333333333333
    assert cvs_row.target_weight_run is None
    assert cvs_row.abs_delta_bt == 0.08333333333333333
    assert cvs_row.friction_eps_bt == 0.1
    assert cvs_row.friction_eps_run == 0.0015
    assert cvs_row.bt_action == "suppressed_exact"
    assert cvs_row.run_action == "enter_inferred"
    assert cvs_row.final_weight_bt == cvs_row.final_weight_run
    assert "RUN target unavailable" in cvs_row.note

    avgo_row = by_ticker["AVGO"]
    assert avgo_row.bt_action == "suppressed_exact"
    assert "BT renorm/finalization changed target" in avgo_row.note
    assert "final BT/RUN equal" in avgo_row.note

    csv_path = write_analysis_csv(rows, run_dir / "analysis.csv")
    with csv_path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        headers = reader.fieldnames
        assert headers is not None
        assert "target_weight_bt" in headers
        assert "final_weight_run" in headers


def test_analyzer_cli_prints_summary_and_writes_default_csv(tmp_path: Path) -> None:
    run_dir = tmp_path / "automation_runs" / "2026-04-23_22-30-40_medium"
    manifest_path, aktien_oop_dir, decisions_dir = _build_sample_run(run_dir)

    output = io.StringIO()
    exit_code = main(["--run-dir", str(run_dir)], stdout=output)

    assert exit_code == 0
    rendered = output.getvalue()
    assert "=== friction_eps analyzer ===" in rendered
    assert "target_weight_bt" in rendered
    assert "friction_eps_run" in rendered
    assert (run_dir / "friction_eps_analysis.csv").exists()


def test_analyzer_uses_exact_runner_friction_dump_when_available(tmp_path: Path) -> None:
    run_dir = tmp_path / "automation_runs" / "2026-04-23_22-30-40_medium"
    manifest_path, aktien_oop_dir, decisions_dir = _build_sample_run(run_dir)
    debug_dir = aktien_oop_dir / "debug"
    (debug_dir / "RUN_friction_2025-10-08.csv").write_text(
        "\n".join(
            [
                "ticker,prev_weight,target_weight_before_friction,abs_delta,effective_friction_eps,friction_action,weight_after_friction,final_weight",
                "AVGO,0.1111111111111111,0.08333333333333333,0.02777777777777777,0.0015,reweighted_exact,0.08333333333333333,0.11111111111111113",
                "CVS,0.0,0.08333333333333333,0.08333333333333333,0.0015,enter_applied_exact,0.11111111111111113,0.11111111111111113",
                "NEM,0.1111111111111111,0.08333333333333333,0.02777777777777777,0.0015,reweighted_exact,0.08333333333333333,0.11111111111111113",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    run_paths = resolve_run_paths(manifest_path=manifest_path)
    rows = build_analysis(run_paths, ["2025-10-08"])
    by_ticker = {row.ticker: row for row in rows}

    cvs_row = by_ticker["CVS"]
    assert cvs_row.target_weight_run == 0.08333333333333333
    assert cvs_row.abs_delta_run == 0.08333333333333333
    assert cvs_row.run_action == "enter_applied_exact"
    assert "RUN target unavailable" not in cvs_row.note
    assert "final BT/RUN equal" in cvs_row.note


def _build_sample_run(run_dir: Path) -> tuple[Path, Path, Path]:
    aktien_oop_dir = run_dir.parent.parent / "aktien_oop"
    decisions_dir = aktien_oop_dir / "decisions" / "20260423_223040"
    dumps_dir = aktien_oop_dir / "dumps"
    debug_dir = aktien_oop_dir / "debug"
    configs_dir = aktien_oop_dir / "configs"

    decisions_dir.mkdir(parents=True)
    dumps_dir.mkdir(parents=True)
    debug_dir.mkdir(parents=True)
    configs_dir.mkdir(parents=True)
    run_dir.mkdir(parents=True)

    bt_config_path = aktien_oop_dir / "backtest_config.toml"
    runner_config_path = configs_dir / "runner_config.toml"
    bt_config_path.write_text('friction_eps = 0.1\n', encoding="utf-8")
    runner_config_path.write_text('friction_eps = 0.0015\n', encoding="utf-8")

    manifest = {
        "compare_point_count": 1,
        "decisions_dir": str(decisions_dir),
        "backtest_config_path": str(bt_config_path),
        "runner_config_path": str(runner_config_path),
    }
    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    bt_bundle = {
        "as_of": "2025-10-08",
        "old_weights": {
            "AVGO": 0.1111111111111111,
            "NEM": 0.1111111111111111,
        },
        "new_weights": {
            "AVGO": 0.11111111111111113,
            "CVS": 0.11111111111111113,
            "NEM": 0.11111111111111113,
        },
        "params": {"friction_eps": 0.1},
    }
    run_bundle = {
        "kind": "RUN",
        "as_of": "2025-10-08",
        "old_weights": {
            "AVGO": 0.1111111111111111,
            "NEM": 0.1111111111111111,
        },
        "new_weights": {
            "AVGO": 0.11111111111111113,
            "CVS": 0.11111111111111113,
            "NEM": 0.11111111111111113,
        },
    }

    (decisions_dir / "BT_20260423_223043_2025-10-08.json").write_text(
        json.dumps(bt_bundle),
        encoding="utf-8",
    )
    (decisions_dir / "RUN_20260423_224907_2025-10-08.json").write_text(
        json.dumps(run_bundle),
        encoding="utf-8",
    )

    (dumps_dir / "weights_BT_2025-10-08.csv").write_text(
        "\n".join(
            [
                "ticker,weight_raw,weight_after_round,weight_final,cash_weight",
                "AVGO,0.08333333333333333,0.08333333333333333,0.11111111111111113,0.0",
                "CVS,0.08333333333333333,0.08333333333333333,0.11111111111111113,0.0",
                "NEM,0.08333333333333333,0.08333333333333333,0.11111111111111113,0.0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (debug_dir / "RUN_weights_2025-10-08.csv").write_text(
        "\n".join(
            [
                "ticker,weight",
                "AVGO,0.11111111111111113",
                "CVS,0.11111111111111113",
                "NEM,0.11111111111111113",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (debug_dir / "RUN_CalcParams_2025-10-08.json").write_text(
        json.dumps({"friction_eps": 0.0015}),
        encoding="utf-8",
    )

    return manifest_path, aktien_oop_dir, decisions_dir

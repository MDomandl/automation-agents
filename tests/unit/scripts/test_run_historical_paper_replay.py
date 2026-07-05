import json
from pathlib import Path

from scripts.run_historical_paper_replay import (
    JSON_REPORT_NAME,
    MANIFEST_NAME,
    MARKDOWN_REPORT_NAME,
    build_manifest,
    build_snapshot,
    classify_proposal,
    compare_snapshots,
    generate_monthly_as_of_dates,
    run_historical_paper_replay,
)


def test_generate_monthly_as_of_dates_is_reproducible_and_preserves_month_end() -> None:
    dates = generate_monthly_as_of_dates("2024-01-31", "2024-04-30")

    assert dates == ["2024-01-31", "2024-02-29", "2024-03-31", "2024-04-30"]


def test_compare_snapshots_detects_new_removed_and_common_symbols() -> None:
    previous = build_snapshot(
        as_of="2024-01-31",
        strategy_profile="balanced_v1",
        profile="short",
        positions={"AAPL": 0.3, "MSFT": 0.2},
    )
    current = build_snapshot(
        as_of="2024-02-29",
        strategy_profile="balanced_v1",
        profile="short",
        positions={"AAPL": 0.4, "NVDA": 0.1},
    )

    comparison = compare_snapshots(
        previous,
        current,
        tolerance=0.00001,
        target_weight_jump_threshold=0.05,
    )

    assert comparison["new_symbols"] == ["NVDA"]
    assert comparison["removed_symbols"] == ["MSFT"]
    assert comparison["common_symbols"] == ["AAPL"]
    assert comparison["new_symbols_count"] == 1
    assert comparison["removed_symbols_count"] == 1
    assert comparison["common_symbols_count"] == 1


def test_compare_snapshots_calculates_weight_deltas_and_jumps() -> None:
    previous = build_snapshot(
        as_of="2024-01-31",
        strategy_profile="balanced_v1",
        profile="short",
        positions={"AAPL": 0.3, "MSFT": 0.2},
    )
    current = build_snapshot(
        as_of="2024-02-29",
        strategy_profile="balanced_v1",
        profile="short",
        positions={"AAPL": 0.37, "MSFT": 0.18},
    )

    comparison = compare_snapshots(
        previous,
        current,
        tolerance=0.00001,
        target_weight_jump_threshold=0.05,
    )

    assert round(comparison["total_abs_weight_delta"], 6) == 0.09
    assert round(comparison["max_abs_weight_delta"], 6) == 0.07
    assert comparison["target_weight_jump_count"] == 1


def test_classify_proposal_uses_tolerance_for_hold() -> None:
    assert classify_proposal(0.300004, 0.3, 0.00001) == "Hold"
    assert classify_proposal(0.30002, 0.3, 0.00001) == "Buy"
    assert classify_proposal(0.29998, 0.3, 0.00001) == "Sell"


def test_compare_snapshots_counts_proposal_changes() -> None:
    previous = build_snapshot(
        as_of="2024-01-31",
        strategy_profile="balanced_v1",
        profile="short",
        positions={"AAPL": 0.0, "MSFT": 0.2},
    )
    current = build_snapshot(
        as_of="2024-02-29",
        strategy_profile="balanced_v1",
        profile="short",
        positions={"AAPL": 0.1, "MSFT": 0.0},
    )

    comparison = compare_snapshots(
        previous,
        current,
        tolerance=0.00001,
        target_weight_jump_threshold=0.05,
    )

    proposals = {
        item["symbol"]: item["current_proposal"]
        for item in comparison["symbol_changes"]
    }
    assert proposals == {"AAPL": "Buy", "MSFT": "Sell"}
    assert comparison["proposal_change_count"] == 2


def test_build_manifest_keeps_safety_fields_false() -> None:
    manifest = build_manifest(
        start="2024-01-31",
        end="2024-02-29",
        warmup_start="2023-01-01",
        strategy_profile="balanced_v1",
        profile="short",
        frequency="monthly",
        tolerance=0.00001,
        as_of_dates=["2024-01-31", "2024-02-29"],
        positions_file=None,
        target_weight_jump_threshold=0.05,
    )

    assert manifest["runner_mode"] == "historical_paper_replay"
    assert manifest["broker_connected"] is False
    assert manifest["live_trading_enabled"] is False
    assert manifest["orders_executed"] is False
    assert manifest["investment_recommendation_generated"] is False
    assert manifest["position_sizing_enabled"] is False
    assert manifest["euro_amounts_calculated"] is False
    assert manifest["share_quantities_calculated"] is False


def test_run_historical_paper_replay_writes_json_markdown_and_manifest(
    tmp_path: Path,
) -> None:
    positions_file = tmp_path / "positions.json"
    positions_file.write_text(
        json.dumps(
            {
                "positions_by_as_of": {
                    "2024-01-31": {"AAPL": 0.3, "MSFT": 0.2},
                    "2024-02-29": {"AAPL": 0.31, "MSFT": 0.19},
                }
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "replay"

    report = run_historical_paper_replay(
        start="2024-01-31",
        end="2024-02-29",
        output_dir=out_dir,
        positions_file=positions_file,
    )

    assert report["runner_mode"] == "historical_paper_replay"
    assert (out_dir / JSON_REPORT_NAME).exists()
    assert (out_dir / MARKDOWN_REPORT_NAME).exists()
    assert (out_dir / MANIFEST_NAME).exists()
    json_report = json.loads((out_dir / JSON_REPORT_NAME).read_text(encoding="utf-8"))
    manifest = json.loads((out_dir / MANIFEST_NAME).read_text(encoding="utf-8"))
    markdown = (out_dir / MARKDOWN_REPORT_NAME).read_text(encoding="utf-8")
    assert json_report["snapshots"][0]["positions"][0]["target_weight"] == 0.3
    assert manifest["frequency"] == "monthly"
    assert "## Sicherheitsstatus" in markdown
    assert "## Proposal-Hinweis" in markdown


def test_missing_positions_create_visible_warnings(tmp_path: Path) -> None:
    positions_file = tmp_path / "positions.json"
    positions_file.write_text(
        json.dumps({"positions_by_as_of": {"2024-01-31": {"AAPL": 0.3}}}),
        encoding="utf-8",
    )

    report = run_historical_paper_replay(
        start="2024-01-31",
        end="2024-02-29",
        output_dir=tmp_path / "out",
        positions_file=positions_file,
    )

    assert report["snapshots"][1]["data_status"] == "missing_positions"
    assert report["snapshots"][1]["warnings"]
    assert any(warning["reason"] == "missing_positions" for warning in report["warnings"])

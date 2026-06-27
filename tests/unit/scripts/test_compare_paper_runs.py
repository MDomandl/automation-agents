import json
from pathlib import Path

from scripts.compare_paper_runs import ReportLoadError, compare_paper_runs


def test_valid_reports_are_compared(tmp_path: Path) -> None:
    previous = _write_report(tmp_path / "previous.json")
    current = _write_report(tmp_path / "current.json")

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    assert comparison["previous_run_id"] == "previous_run"
    assert comparison["current_run_id"] == "current_run"
    assert comparison["common_symbols_count"] == 3
    assert comparison["warnings"] == []


def test_added_symbol_is_detected(tmp_path: Path) -> None:
    previous = _write_report(tmp_path / "previous.json", target_positions={"AAA": 0.1})
    current = _write_report(
        tmp_path / "current.json",
        target_positions={"AAA": 0.1, "BBB": 0.2},
        buy_proposals=[_proposal("AAA", "buy", 0.1, 0.0), _proposal("BBB", "buy", 0.2, 0.2)],
    )

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    assert comparison["added_symbols"] == ["BBB"]


def test_removed_symbol_is_detected(tmp_path: Path) -> None:
    previous = _write_report(
        tmp_path / "previous.json",
        target_positions={"AAA": 0.1, "BBB": 0.2},
        buy_proposals=[_proposal("AAA", "buy", 0.1, 0.0), _proposal("BBB", "buy", 0.2, 0.0)],
    )
    current = _write_report(tmp_path / "current.json", target_positions={"AAA": 0.1})

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    assert comparison["removed_symbols"] == ["BBB"]


def test_common_symbol_is_detected(tmp_path: Path) -> None:
    previous = _write_report(tmp_path / "previous.json", target_positions={"AAA": 0.1})
    current = _write_report(tmp_path / "current.json", target_positions={"AAA": 0.2})

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    assert comparison["symbol_comparisons"][0]["symbol"] == "AAA"


def test_proposal_change_is_detected(tmp_path: Path) -> None:
    previous = _write_report(
        tmp_path / "previous.json",
        buy_proposals=[_proposal("AAA", "buy", 0.1, 0.05)],
        sell_proposals=[],
    )
    current = _write_report(
        tmp_path / "current.json",
        buy_proposals=[],
        sell_proposals=[_proposal("AAA", "sell", 0.1, -0.05)],
    )

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    row = comparison["symbol_comparisons"][0]
    assert row["previous_proposal"] == "buy"
    assert row["current_proposal"] == "sell"
    assert row["proposal_changed"] is True
    assert comparison["proposal_changes_count"] == 1


def test_target_weight_directions_are_detected(tmp_path: Path) -> None:
    previous = _write_report(
        tmp_path / "previous.json",
        target_positions={"UP": 0.1, "DOWN": 0.2, "SAME": 0.3},
        buy_proposals=[
            _proposal("UP", "buy", 0.1, 0.0),
            _proposal("DOWN", "buy", 0.2, 0.0),
            _proposal("SAME", "buy", 0.3, 0.0),
        ],
    )
    current = _write_report(
        tmp_path / "current.json",
        target_positions={"UP": 0.2, "DOWN": 0.1, "SAME": 0.3},
        buy_proposals=[
            _proposal("UP", "buy", 0.2, 0.0),
            _proposal("DOWN", "buy", 0.1, 0.0),
            _proposal("SAME", "buy", 0.3, 0.0),
        ],
    )

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    directions = {
        row["symbol"]: row["target_weight_direction"]
        for row in comparison["symbol_comparisons"]
    }
    assert directions == {"DOWN": "decreased", "SAME": "unchanged", "UP": "increased"}


def test_delta_change_is_detected(tmp_path: Path) -> None:
    previous = _write_report(
        tmp_path / "previous.json",
        buy_proposals=[_proposal("AAA", "buy", 0.1, 0.01)],
    )
    current = _write_report(
        tmp_path / "current.json",
        buy_proposals=[_proposal("AAA", "buy", 0.1, 0.04)],
    )

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    row = comparison["symbol_comparisons"][0]
    assert row["delta_change"] == 0.03
    assert row["delta_direction"] == "increased"
    assert comparison["delta_changes_count"] == 1


def test_large_target_weight_jump_is_detected(tmp_path: Path) -> None:
    previous = _write_report(tmp_path / "previous.json", target_positions={"AAA": 0.1})
    current = _write_report(tmp_path / "current.json", target_positions={"AAA": 0.2})

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
        max_jump_threshold=0.05,
    )

    assert comparison["symbol_comparisons"][0]["large_target_weight_jump"] is True
    assert comparison["large_target_weight_jumps_count"] == 1


def test_metadata_difference_creates_warning(tmp_path: Path) -> None:
    previous = _write_report(tmp_path / "previous.json", as_of="2025-10-08")
    current = _write_report(tmp_path / "current.json", as_of="2025-10-09")

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    assert any(warning["reason"] == "different_as_of" for warning in comparison["warnings"])


def test_missing_optional_fields_do_not_crash(tmp_path: Path) -> None:
    previous = _write_report(
        tmp_path / "previous.json",
        target_positions=None,
        buy_proposals=None,
        sell_proposals=None,
        hold_proposals=None,
    )
    current = _write_report(tmp_path / "current.json")

    comparison = compare_paper_runs(
        previous_report=previous,
        current_report=current,
        out_dir=tmp_path / "out",
    )

    assert comparison["common_symbols_count"] == 0
    assert any(
        warning["reason"] == "missing_positions_previous"
        for warning in comparison["warnings"]
    )


def test_invalid_json_raises_controlled_error(tmp_path: Path) -> None:
    previous = tmp_path / "previous.json"
    previous.write_text("{not-json", encoding="utf-8")
    current = _write_report(tmp_path / "current.json")

    try:
        compare_paper_runs(
            previous_report=previous,
            current_report=current,
            out_dir=tmp_path / "out",
        )
    except ReportLoadError as exc:
        assert "Ungueltiges JSON" in str(exc)
    else:
        raise AssertionError("ReportLoadError was not raised")


def test_json_output_is_written(tmp_path: Path) -> None:
    previous = _write_report(tmp_path / "previous.json")
    current = _write_report(tmp_path / "current.json")

    compare_paper_runs(previous_report=previous, current_report=current, out_dir=tmp_path / "out")

    payload = json.loads((tmp_path / "out" / "paper_run_comparison.json").read_text("utf-8"))
    assert payload["common_symbols_count"] == 3


def test_markdown_output_is_written(tmp_path: Path) -> None:
    previous = _write_report(tmp_path / "previous.json")
    current = _write_report(tmp_path / "current.json")

    compare_paper_runs(previous_report=previous, current_report=current, out_dir=tmp_path / "out")

    markdown = (tmp_path / "out" / "paper_run_comparison.md").read_text("utf-8")
    assert "# Paper-Run-Vergleich" in markdown
    assert "Keine Investitionsfreigabe." in markdown


def _write_report(path: Path, **overrides: object) -> Path:
    target_positions = overrides.get(
        "target_positions",
        {"AAA": 0.1, "BBB": 0.2, "CCC": 0.3},
    )
    default_buy_proposals = []
    if isinstance(target_positions, dict):
        default_buy_proposals = [
            _proposal(str(symbol), "buy", float(weight), 0.0)
            for symbol, weight in target_positions.items()
        ]
    payload = {
        "run_id": "previous_run" if "previous" in path.name else "current_run",
        "run_label": path.stem,
        "runner_mode": "paper",
        "orders_executed": False,
        "broker_connected": False,
        "live_trading_enabled": False,
        "execution": {
            "orders_executed": False,
            "broker_connected": False,
            "live_trading_enabled": False,
        },
        "strategy_profile_name": "balanced_v1",
        "strategy_profile_label": "Balanced v1",
        "profile": "short",
        "as_of": "2025-10-08",
        "portfolio_source": "portfolio_file",
        "portfolio_file": "portfolios/example_local_portfolio.csv",
        "portfolio_file_name": "example_local_portfolio.csv",
        "portfolio_file_display": "portfolios/example_local_portfolio.csv",
        "portfolio_name": "example_local",
        "proposal_delta_tolerance": 0.00001,
        "target_positions": target_positions,
        "buy_proposals": default_buy_proposals,
        "sell_proposals": [],
        "hold_proposals": [],
        "human_review_required": {"required": True},
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _proposal(
    ticker: str,
    _proposal_class: str,
    target_weight: float,
    delta_weight: float,
) -> dict[str, float | str]:
    return {
        "ticker": ticker,
        "previous_weight": target_weight - delta_weight,
        "target_weight": target_weight,
        "delta_weight": delta_weight,
    }

import json
from pathlib import Path

from scripts.collect_paper_run_history import collect_paper_run_history


def test_valid_paper_report_is_read(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    _write_report(runs_dir / "2026-06-01_10-00-00_short_paper")

    history = collect_paper_run_history(runs_dir=runs_dir, out_dir=tmp_path / "reports")

    assert history["total_reports_found"] == 1
    assert history["total_reports_included"] == 1
    assert history["runs"][0]["runner_mode"] == "paper"
    assert history["runs"][0]["profile"] == "short"
    assert history["runs"][0]["strategy_profile"] == "balanced_v1"
    assert history["runs"][0]["buy_proposals_count"] == 1
    assert history["runs"][0]["sell_proposals_count"] == 1
    assert history["runs"][0]["hold_proposals_count"] == 1


def test_multiple_reports_are_collected(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    _write_report(runs_dir / "2026-06-01_10-00-00_short_paper")
    _write_report(runs_dir / "nested" / "2026-06-02_10-00-00_medium_paper")

    history = collect_paper_run_history(runs_dir=runs_dir, out_dir=tmp_path / "reports")

    assert history["total_reports_found"] == 2
    assert history["total_reports_included"] == 2
    assert {run["profile"] for run in history["runs"]} == {"short", "medium"}


def test_strategy_profile_filter(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    _write_report(
        runs_dir / "2026-06-01_10-00-00_short_paper",
        strategy_profile_name="balanced_v1",
    )
    _write_report(
        runs_dir / "2026-06-02_10-00-00_short_paper",
        strategy_profile_name="offensive_v1",
    )

    history = collect_paper_run_history(
        runs_dir=runs_dir,
        out_dir=tmp_path / "reports",
        strategy_profile="balanced_v1",
    )

    assert history["total_reports_included"] == 1
    assert history["total_reports_skipped"] == 1
    assert history["runs"][0]["strategy_profile"] == "balanced_v1"


def test_profile_filter(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    _write_report(runs_dir / "2026-06-01_10-00-00_short_paper", run_label="run_short_paper")
    _write_report(runs_dir / "2026-06-02_10-00-00_medium_paper", run_label="run_medium_paper")

    history = collect_paper_run_history(
        runs_dir=runs_dir,
        out_dir=tmp_path / "reports",
        profile="medium",
    )

    assert history["total_reports_included"] == 1
    assert history["runs"][0]["profile"] == "medium"


def test_missing_optional_fields_do_not_crash(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    _write_report(
        runs_dir / "2026-06-01_10-00-00_short_paper",
        portfolio_file=None,
        portfolio_file_name=None,
        portfolio_file_display=None,
        portfolio_name=None,
        portfolio_checks=None,
        target_positions=None,
        buy_proposals=None,
        sell_proposals=None,
        hold_proposals=None,
    )

    history = collect_paper_run_history(runs_dir=runs_dir, out_dir=tmp_path / "reports")

    run = history["runs"][0]
    assert run["portfolio_file"] is None
    assert run["positions_count"] == 0
    assert run["proposal_rows_count"] == 0
    assert run["has_portfolio_checks"] is False


def test_invalid_json_is_skipped_and_counted_as_warning(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    report_path = runs_dir / "bad" / "paper_run_report.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text("{not-json", encoding="utf-8")

    history = collect_paper_run_history(runs_dir=runs_dir, out_dir=tmp_path / "reports")

    assert history["total_reports_found"] == 1
    assert history["total_reports_included"] == 0
    assert history["total_reports_skipped"] == 1
    assert history["warnings"][0]["reason"] == "invalid_json"


def test_json_output_is_written(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    out_dir = tmp_path / "reports"
    _write_report(runs_dir / "2026-06-01_10-00-00_short_paper")

    collect_paper_run_history(runs_dir=runs_dir, out_dir=out_dir)

    payload = json.loads((out_dir / "paper_run_history.json").read_text(encoding="utf-8"))
    assert payload["total_reports_included"] == 1


def test_markdown_output_is_written(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    out_dir = tmp_path / "reports"
    _write_report(runs_dir / "2026-06-01_10-00-00_short_paper")

    collect_paper_run_history(runs_dir=runs_dir, out_dir=out_dir)

    markdown = (out_dir / "paper_run_history.md").read_text(encoding="utf-8")
    assert "# Paper-Run-History" in markdown
    assert "Keine Orders." in markdown
    assert "balanced_v1" in markdown


def test_non_paper_report_is_skipped_when_recognizable(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    _write_report(runs_dir / "analysis_run", runner_mode="analysis")

    history = collect_paper_run_history(runs_dir=runs_dir, out_dir=tmp_path / "reports")

    assert history["total_reports_found"] == 1
    assert history["total_reports_included"] == 0
    assert history["total_reports_skipped"] == 1
    assert history["warnings"][0]["reason"] == "not_paper_report"


def test_missing_filter_field_skips_with_warning(tmp_path: Path) -> None:
    runs_dir = tmp_path / "automation_runs"
    _write_report(runs_dir / "2026-06-01_10-00-00_paper", strategy_profile_name=None)

    history = collect_paper_run_history(
        runs_dir=runs_dir,
        out_dir=tmp_path / "reports",
        strategy_profile="balanced_v1",
    )

    assert history["total_reports_included"] == 0
    assert history["total_reports_skipped"] == 1
    assert history["warnings"][0]["reason"] == "missing_strategy_profile_for_filter"


def _write_report(run_dir: Path, **overrides: object) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": "20260601_100000",
        "run_label": run_dir.name,
        "runner_mode": "paper",
        "approval_status": "manual_approval_required",
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
        "as_of": "2025-10-08",
        "portfolio_source": "portfolio_file",
        "portfolio_file": "portfolios/example.csv",
        "portfolio_file_name": "example.csv",
        "portfolio_file_display": "portfolios/example.csv",
        "portfolio_name": "example_local",
        "portfolio_checks": {"position_count": 2},
        "proposal_delta_tolerance": 0.00001,
        "target_positions": {"AAPL": 0.5, "MSFT": 0.5},
        "buy_proposals": [{"ticker": "AAPL"}],
        "sell_proposals": [{"ticker": "MSFT"}],
        "hold_proposals": [{"ticker": "CASH"}],
        "human_review_required": {"required": True},
    }
    payload.update(overrides)
    (run_dir / "paper_run_report.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

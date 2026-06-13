import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_walk_forward_matrix as wf


def test_yearly_windows_are_created() -> None:
    assert wf.resolve_windows("yearly", "2025-10-08") == (
        wf.WalkForwardWindow("oos_2022", "2020-07-01", "2022-01-01", "2022-12-31"),
        wf.WalkForwardWindow("oos_2023", "2021-07-01", "2023-01-01", "2023-12-31"),
        wf.WalkForwardWindow("oos_2024", "2022-07-01", "2024-01-01", "2024-12-31"),
        wf.WalkForwardWindow("oos_2025_ytd", "2023-01-01", "2025-01-01", "2025-10-08"),
    )


def test_as_of_caps_current_window() -> None:
    windows = wf.resolve_windows("yearly", "2024-06-30")

    assert windows[-1] == wf.WalkForwardWindow(
        "oos_2024",
        "2022-07-01",
        "2024-01-01",
        "2024-06-30",
    )


def test_windows_after_as_of_are_skipped() -> None:
    windows = wf.resolve_windows("yearly", "2023-06-30")

    assert [window.window_name for window in windows] == ["oos_2022", "oos_2023"]
    assert windows[-1].oos_end == "2023-06-30"


def test_default_values_are_correct() -> None:
    args = wf.parse_args([])

    assert args.strategy_profile == "balanced_v1"
    assert args.profile == "medium"
    assert args.window_mode == "yearly"
    assert args.as_of == "2025-10-08"
    assert args.output_dir == str(wf.REPORT_DIR)


def test_build_command_contains_required_window_args() -> None:
    cell = wf.WalkForwardCell(wf.YEARLY_WINDOWS[0], "balanced_v1", "medium")

    command = wf.build_command(cell)

    assert command == (
        sys.executable,
        "-m",
        "scripts.run_bt_run_agent",
        "--profile",
        "medium",
        "--strategy-profile",
        "balanced_v1",
        "--warmup-start",
        "2020-07-01",
        "--start",
        "2022-01-01",
        "--end",
        "2022-12-31",
        "--phase-name",
        "oos_2022",
    )


def test_strategy_profiles_are_combined_with_windows() -> None:
    windows = wf.YEARLY_WINDOWS[:2]

    cells = wf.build_matrix(
        windows,
        ("conservative_v1", "balanced_v1"),
        profile="medium",
    )

    assert cells == [
        wf.WalkForwardCell(windows[0], "conservative_v1", "medium"),
        wf.WalkForwardCell(windows[0], "balanced_v1", "medium"),
        wf.WalkForwardCell(windows[1], "conservative_v1", "medium"),
        wf.WalkForwardCell(windows[1], "balanced_v1", "medium"),
    ]


def test_failed_single_runs_do_not_break_matrix(monkeypatch) -> None:
    cells = [
        wf.WalkForwardCell(wf.YEARLY_WINDOWS[0], "balanced_v1", "medium"),
        wf.WalkForwardCell(wf.YEARLY_WINDOWS[1], "balanced_v1", "medium"),
    ]

    def fake_run_cell(cell):
        return _result(
            window=cell.window,
            success=cell.window.window_name == "oos_2022",
            error=None
            if cell.window.window_name == "oos_2022"
            else "run_bt_run_agent failed with returncode 2",
        )

    monkeypatch.setattr(wf, "run_cell", fake_run_cell)

    results = wf.run_matrix(cells)
    report = wf.build_json_report(
        results,
        windows=wf.YEARLY_WINDOWS[:2],
        window_mode="yearly",
        profile="medium",
        strategy_profiles=("balanced_v1",),
        as_of="2025-10-08",
        generated_at="2026-06-14T10:00:00",
    )

    assert len(results) == 2
    assert report["summary"]["runs_successful"] == 1
    assert report["summary"]["runs_failed"] == 1
    assert report["matrix"][1]["error"] == "run_bt_run_agent failed with returncode 2"


def test_manifest_compare_status_runner_points_and_phase_metrics_are_used(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run_dir = tmp_path / "automation_runs" / "run"
    run_dir.mkdir(parents=True)
    artifacts = _write_artifacts(run_dir)
    (run_dir / "summary.txt").write_text("summary", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "success": True,
                "warmup_start": "2020-07-01",
                "phase_start": "2022-01-01",
                "phase_end": "2022-12-31",
                "effective_backtest_start": "2020-07-01",
                "effective_backtest_end": "2022-12-31",
                "compare_point_count": 3,
                "warnings": [
                    "[INFO] Runner compare points: count=3, "
                    "as_of=2022-10-31,2022-11-30,2022-12-30"
                ],
                "compare": {
                    "success": True,
                    "matched": True,
                    "message": "3 matched, 0 mismatched",
                },
                "artifacts": artifacts,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        wf.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="run_id: 20260614_100000\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(wf, "load_run_snapshot", lambda *args, **kwargs: _snapshot(run_dir))

    result = wf.run_cell(wf.WalkForwardCell(wf.YEARLY_WINDOWS[0], "balanced_v1", "medium"))

    assert result.run_id == "20260614_100000"
    assert result.compare_matched is True
    assert result.compare_message == "3 matched, 0 mismatched"
    assert result.runner_compare_points == ("2022-10-31", "2022-11-30", "2022-12-30")
    assert result.runner_compare_point_count == 3
    assert result.phase_metrics["portfolio_total_return"] == pytest.approx(10.0)
    assert result.phase_metrics["benchmark_total_return"] == pytest.approx(5.0)


def test_compute_phase_metrics_is_called(monkeypatch) -> None:
    calls = []

    def fake_compute_phase_metrics(artifacts, phase_start, phase_end):
        calls.append((artifacts, phase_start, phase_end))
        return _phase_metrics(success=True)

    monkeypatch.setattr(wf, "compute_phase_metrics", fake_compute_phase_metrics)
    monkeypatch.setattr(wf, "phase_metrics_warnings", lambda *args: ())

    result = wf.result_from_run_dir(
        wf.WalkForwardCell(wf.YEARLY_WINDOWS[0], "balanced_v1", "medium"),
        command=("python",),
        returncode=0,
        run_id=None,
        run_dir=None,
        error=None,
        stdout="",
        stderr="",
    )

    assert calls == [({}, "2022-01-01", "2022-12-31")]
    assert result.phase_metrics["relative_total_return"] == 5.0


def test_json_contains_expected_structure() -> None:
    report = wf.build_json_report(
        [_result()],
        windows=(wf.YEARLY_WINDOWS[0],),
        window_mode="yearly",
        profile="medium",
        strategy_profiles=("balanced_v1",),
        as_of="2025-10-08",
        generated_at="2026-06-14T10:00:00",
    )

    assert report["generated_at"] == "2026-06-14T10:00:00"
    assert report["window_mode"] == "yearly"
    assert report["profile"] == "medium"
    assert report["strategy_profiles"] == ["balanced_v1"]
    assert report["as_of"] == "2025-10-08"
    assert report["windows"][0]["window_name"] == "oos_2022"
    assert report["matrix"][0]["phase_metrics"]["outperformed_benchmark"] is True
    assert report["summary"]["runs_total"] == 1
    assert wf.MEDIUM_COMPARE_NOTE in report["warnings"]


def test_markdown_contains_required_sections() -> None:
    report = wf.build_markdown_report(
        [_result()],
        windows=(wf.YEARLY_WINDOWS[0],),
        generated_at="2026-06-14T10:00:00",
        strategy_profiles=("balanced_v1",),
    )

    assert "## Windows" in report
    assert "## Executed Matrix" in report
    assert "## Technical Details" in report
    assert "## OOS Metrics" in report
    assert "## Interpretation Notes" in report


def test_summary_counts_runs_and_mismatches() -> None:
    results = [
        _result(window=wf.YEARLY_WINDOWS[0], success=True, compare_matched=True),
        _result(window=wf.YEARLY_WINDOWS[1], success=False, compare_matched=False),
    ]

    summary = wf.summarize_results(results, windows=wf.YEARLY_WINDOWS[:2])

    assert summary["runs_total"] == 2
    assert summary["runs_successful"] == 1
    assert summary["runs_failed"] == 1
    assert summary["compare_mismatched"] == 1
    assert summary["outperformed_windows"] == 1
    assert summary["windows_total"] == 2


def test_run_cell_does_not_mutate_config_files(tmp_path: Path, monkeypatch) -> None:
    backtest_config = tmp_path / "backtest_config.toml"
    runner_config = tmp_path / "configs" / "runner_config.toml"
    runner_config.parent.mkdir()
    backtest_config.write_text("top_k = 8\n", encoding="utf-8")
    runner_config.write_text("top_k = 8\n", encoding="utf-8")
    run_dir = tmp_path / "automation_runs" / "run"
    run_dir.mkdir(parents=True)
    artifacts = _write_artifacts(run_dir)
    (run_dir / "summary.txt").write_text("summary", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "success": True,
                "compare": {"success": True, "matched": True},
                "artifacts": artifacts,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        wf.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="run_id: 20260614_100000\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(wf, "load_run_snapshot", lambda *args, **kwargs: _snapshot(run_dir))

    wf.run_cell(wf.WalkForwardCell(wf.YEARLY_WINDOWS[0], "balanced_v1", "medium"))

    assert backtest_config.read_text(encoding="utf-8") == "top_k = 8\n"
    assert runner_config.read_text(encoding="utf-8") == "top_k = 8\n"


def test_no_base_config_or_profile_paths_are_written(tmp_path: Path) -> None:
    report_dir = tmp_path / "reports"
    result = _result()

    wf.write_reports(
        [result],
        windows=(wf.YEARLY_WINDOWS[0],),
        window_mode="yearly",
        profile="medium",
        strategy_profiles=("balanced_v1",),
        as_of="2025-10-08",
        report_dir=report_dir,
    )

    written = {path.name for path in report_dir.iterdir()}
    assert written == {"walk_forward_summary.md", "walk_forward_summary.json"}


def _snapshot(run_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(output_dir=run_dir)


def _write_artifacts(root: Path) -> dict[str, str]:
    equity = root / "equity.csv"
    equity.write_text(
        "# run_id=test\n"
        "date,equity\n"
        "2022-01-01,100\n"
        "2022-12-31,110\n",
        encoding="utf-8",
    )
    bench = root / "benchmark.csv"
    bench.write_text(
        "# run_id=test\n"
        "date,equity,BM1_TEST\n"
        "2022-01-01,100,100\n"
        "2022-12-31,100,105\n",
        encoding="utf-8",
    )
    trades = root / "trades.csv"
    trades.write_text(
        "# run_id=test\n"
        "date,turnover\n"
        "2022-06-30,0.2\n",
        encoding="utf-8",
    )
    return {"equity": str(equity), "bench": str(bench), "trades": str(trades)}


def _result(
    *,
    window: wf.WalkForwardWindow = wf.YEARLY_WINDOWS[0],
    success: bool = True,
    compare_matched: bool | None = True,
    error: str | None = None,
) -> wf.WalkForwardRunResult:
    return wf.WalkForwardRunResult(
        window_name=window.window_name,
        strategy_profile="balanced_v1",
        profile="medium",
        warmup_start=window.warmup_start,
        oos_start=window.oos_start,
        oos_end=window.oos_end,
        command=("python", "-m", "scripts.run_bt_run_agent"),
        returncode=0 if success else 2,
        run_id="20260614_100000" if success else None,
        run_dir="runs/example" if success else None,
        manifest_path="runs/example/run_manifest.json" if success else None,
        summary_path="runs/example/summary.txt" if success else None,
        success=success,
        compare_success=True if compare_matched is not False else False,
        compare_matched=compare_matched,
        compare_message="3 matched, 0 mismatched" if compare_matched else None,
        runner_compare_points=("2022-10-31", "2022-11-30", "2022-12-30") if success else (),
        runner_compare_point_count=3 if success else None,
        effective_backtest_start=window.warmup_start if success else None,
        effective_backtest_end=window.oos_end if success else None,
        phase_metrics=_phase_metrics(success=success),
        warnings=(),
        error=error,
        stdout_excerpt=None,
        stderr_excerpt=None,
        missing=() if success else ("manifest",),
    )


def _phase_metrics(*, success: bool) -> dict[str, float | bool | int | str | None]:
    return {
        "portfolio_total_return": 10.0 if success else None,
        "portfolio_cagr": 11.0 if success else None,
        "portfolio_max_drawdown": -4.0 if success else None,
        "portfolio_volatility": 12.0 if success else None,
        "portfolio_sharpe": 1.5 if success else None,
        "benchmark_total_return": 5.0 if success else None,
        "benchmark_cagr": 6.0 if success else None,
        "benchmark_max_drawdown": -5.0 if success else None,
        "benchmark_volatility": 9.0 if success else None,
        "benchmark_sharpe": 1.1 if success else None,
        "relative_total_return": 5.0 if success else None,
        "relative_cagr": 5.0 if success else None,
        "outperformed_benchmark": True if success else None,
        "cagr_outperformed_benchmark": True if success else None,
        "drawdown_better_than_benchmark": True if success else None,
        "turnover": 20.0 if success else None,
        "turnover_is_phase_only": success,
        "turnover_source": "trades_csv_in_phase_rows" if success else None,
        "turnover_note": "Computed from trade rows inside phase window." if success else None,
        "phase_start_actual": "2022-01-01" if success else None,
        "phase_end_actual": "2022-12-31" if success else None,
        "observation_count": 2 if success else 0,
    }

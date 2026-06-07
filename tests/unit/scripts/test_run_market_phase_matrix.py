import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from scripts import run_market_phase_matrix as matrix


def test_default_phases_are_defined() -> None:
    assert matrix.DEFAULT_PHASES == (
        matrix.MarketPhase(
            phase_name="bear_market_2022",
            type="Bärenmarkt / Zinsphase",
            warmup_start="2020-07-01",
            phase_start="2022-01-01",
            phase_end="2022-12-31",
        ),
        matrix.MarketPhase(
            phase_name="recovery_2023",
            type="Erholung / Momentum",
            warmup_start="2021-07-01",
            phase_start="2023-01-01",
            phase_end="2023-12-31",
        ),
        matrix.MarketPhase(
            phase_name="recent_2024_2025",
            type="jüngere Marktphase",
            warmup_start="2022-07-01",
            phase_start="2024-01-01",
            phase_end="2025-10-08",
        ),
    )


def test_build_matrix_creates_phase_strategy_combinations() -> None:
    phases = matrix.DEFAULT_PHASES[:2]

    cells = matrix.build_matrix(
        phases=phases,
        strategy_profiles=("conservative_v1", "balanced_v1"),
        profile="medium",
    )

    assert cells == [
        matrix.MarketPhaseCell(phases[0], "conservative_v1", "medium"),
        matrix.MarketPhaseCell(phases[0], "balanced_v1", "medium"),
        matrix.MarketPhaseCell(phases[1], "conservative_v1", "medium"),
        matrix.MarketPhaseCell(phases[1], "balanced_v1", "medium"),
    ]


def test_build_command_contains_phase_window_args() -> None:
    cell = matrix.MarketPhaseCell(matrix.DEFAULT_PHASES[0], "balanced_v1", "medium")

    command = matrix.build_command(cell)

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
        "bear_market_2022",
    )


def test_json_report_contains_phase_run_compare_and_runner_points() -> None:
    result = _result()

    report = matrix.build_json_report(
        [result],
        phases=(matrix.DEFAULT_PHASES[0],),
        profile="medium",
        generated_at="2026-06-07T10:00:00",
    )

    row = report["matrix"][0]
    assert report["profile"] == "medium"
    assert report["phases"][0]["phase_name"] == "bear_market_2022"
    assert row["phase_name"] == "bear_market_2022"
    assert row["strategy_profile"] == "balanced_v1"
    assert row["run_id"] == "20260607_100000"
    assert row["compare_success"] is True
    assert row["compare_matched"] is True
    assert row["runner_compare_points"] == (
        "2022-10-31",
        "2022-11-30",
        "2022-12-30",
    )

    encoded = json.dumps(report)
    decoded = json.loads(encoded)
    assert decoded["matrix"][0]["runner_compare_points"] == [
        "2022-10-31",
        "2022-11-30",
        "2022-12-30",
    ]


def test_markdown_report_contains_phase_metrics_note() -> None:
    report = matrix.build_markdown_report(
        [_result()],
        phases=(matrix.DEFAULT_PHASES[0],),
        generated_at="2026-06-07T10:00:00",
    )

    assert "# Market Phase Matrix" in report
    assert matrix.PHASE_METRICS_NOTE in report
    assert "| bear_market_2022 | balanced_v1 | 20260607_100000 | true | true |" in report


def test_failed_single_runs_are_documented_without_breaking_matrix(monkeypatch) -> None:
    cells = [
        matrix.MarketPhaseCell(matrix.DEFAULT_PHASES[0], "balanced_v1", "medium"),
        matrix.MarketPhaseCell(matrix.DEFAULT_PHASES[1], "offensive_v1", "medium"),
    ]

    def fake_run_cell(cell):
        if cell.strategy_profile == "offensive_v1":
            return _result(
                phase=cell.phase,
                strategy_profile=cell.strategy_profile,
                success=False,
                compare_success=False,
                compare_matched=None,
                error="run_bt_run_agent failed with returncode 2",
                returncode=2,
            )
        return _result(phase=cell.phase, strategy_profile=cell.strategy_profile)

    monkeypatch.setattr(matrix, "run_cell", fake_run_cell)

    results = matrix.run_matrix(cells)
    report = matrix.build_json_report(
        results,
        phases=matrix.DEFAULT_PHASES[:2],
        profile="medium",
        generated_at="2026-06-07T10:00:00",
    )

    assert len(results) == 2
    assert report["summary"]["success"] == 1
    assert report["summary"]["failed"] == 1
    assert report["matrix"][1]["error"] == "run_bt_run_agent failed with returncode 2"


def test_run_cell_does_not_mutate_config_files(tmp_path: Path, monkeypatch) -> None:
    backtest_config = tmp_path / "backtest_config.toml"
    runner_config = tmp_path / "configs" / "runner_config.toml"
    runner_config.parent.mkdir()
    backtest_config.write_text("top_k = 8\n", encoding="utf-8")
    runner_config.write_text("top_k = 8\n", encoding="utf-8")
    run_dir = tmp_path / "automation_runs" / "2026-06-07_10-00-00_medium"
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "success": True,
                "warmup_start": "2020-07-01",
                "phase_start": "2022-01-01",
                "phase_end": "2022-12-31",
                "effective_backtest_start": "2020-07-01",
                "effective_backtest_end": "2022-12-31",
                "warnings": [
                    "[INFO] Runner compare points: count=3, "
                    "as_of=2022-10-31,2022-11-30,2022-12-30"
                ],
                "compare": {
                    "success": True,
                    "matched": True,
                    "message": "3 matched, 0 mismatched",
                },
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "summary.txt").write_text("summary", encoding="utf-8")

    monkeypatch.setattr(
        matrix.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="run_id: 20260607_100000\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(matrix, "load_run_snapshot", lambda *args, **kwargs: _snapshot(run_dir))

    result = matrix.run_cell(
        matrix.MarketPhaseCell(matrix.DEFAULT_PHASES[0], "balanced_v1", "medium")
    )

    assert result.run_id == "20260607_100000"
    assert result.runner_compare_points == ("2022-10-31", "2022-11-30", "2022-12-30")
    assert backtest_config.read_text(encoding="utf-8") == "top_k = 8\n"
    assert runner_config.read_text(encoding="utf-8") == "top_k = 8\n"


def _snapshot(run_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(
        output_dir=run_dir,
        performance=SimpleNamespace(
            total_return_pct=12.3,
            cagr_pct=8.4,
            max_drawdown_pct=-6.7,
            sharpe_ratio=1.2,
            volatility_pct=11.1,
            turnover_pct=17.5,
        ),
        benchmark=SimpleNamespace(
            benchmark_cagr_pct=5.6,
            benchmark_max_drawdown_pct=-9.8,
        ),
    )


def _result(
    *,
    phase: matrix.MarketPhase = matrix.DEFAULT_PHASES[0],
    strategy_profile: str = "balanced_v1",
    success: bool = True,
    compare_success: bool | None = True,
    compare_matched: bool | None = True,
    error: str | None = None,
    returncode: int | None = 0,
) -> matrix.MarketPhaseRunResult:
    return matrix.MarketPhaseRunResult(
        phase_name=phase.phase_name,
        phase_type=phase.type,
        strategy_profile=strategy_profile,
        profile="medium",
        command=("python", "-m", "scripts.run_bt_run_agent"),
        returncode=returncode,
        run_id="20260607_100000" if success else None,
        run_dir="runs/example" if success else None,
        manifest_path="runs/example/run_manifest.json" if success else None,
        summary_path="runs/example/summary.txt" if success else None,
        success=success,
        compare_success=compare_success,
        compare_matched=compare_matched,
        compare_message="3 matched, 0 mismatched" if compare_success else None,
        runner_compare_points=("2022-10-31", "2022-11-30", "2022-12-30") if success else (),
        warmup_start=phase.warmup_start,
        phase_start=phase.phase_start,
        phase_end=phase.phase_end,
        effective_backtest_start=phase.warmup_start,
        effective_backtest_end=phase.phase_end,
        metrics={
            "total_return": 12.3 if success else None,
            "cagr": 8.4 if success else None,
            "max_drawdown": -6.7 if success else None,
            "sharpe": 1.2 if success else None,
            "volatility": 11.1 if success else None,
            "turnover": 17.5 if success else None,
            "benchmark_cagr": 5.6 if success else None,
            "benchmark_max_drawdown": -9.8 if success else None,
        },
        warnings=(),
        error=error,
        stdout_excerpt=None,
        stderr_excerpt=None,
        missing=() if success else ("run_dir", "manifest"),
    )

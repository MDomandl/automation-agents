import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from scripts import run_profile_robustness_matrix as matrix


def test_build_matrix_creates_all_combinations() -> None:
    cells = matrix.build_matrix(
        profiles=("short", "medium"),
        strategy_profiles=("conservative_v1", "balanced_v1"),
    )

    assert cells == [
        matrix.MatrixCell("short", "conservative_v1"),
        matrix.MatrixCell("short", "balanced_v1"),
        matrix.MatrixCell("medium", "conservative_v1"),
        matrix.MatrixCell("medium", "balanced_v1"),
    ]


def test_build_command_uses_strategy_profile() -> None:
    command = matrix.build_command(matrix.MatrixCell("medium", "balanced_v1"))

    assert command == (
        sys.executable,
        "-m",
        "scripts.run_bt_run_agent",
        "--profile",
        "medium",
        "--strategy-profile",
        "balanced_v1",
    )


def test_run_cell_does_not_mutate_config_files(tmp_path: Path, monkeypatch) -> None:
    backtest_config = tmp_path / "backtest_config.toml"
    runner_config = tmp_path / "configs" / "runner_config.toml"
    runner_config.parent.mkdir()
    backtest_config.write_text("top_k = 8\n", encoding="utf-8")
    runner_config.write_text("top_k = 8\n", encoding="utf-8")
    run_dir = tmp_path / "automation_runs" / "2026-05-31_10-00-00_medium"
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(
        '{"compare": {"matched": true}}',
        encoding="utf-8",
    )
    (run_dir / "summary.txt").write_text("summary", encoding="utf-8")

    monkeypatch.setattr(
        matrix.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="run_id: 20260531_100000\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        matrix,
        "load_run_snapshot",
        lambda *args, **kwargs: _snapshot(run_dir),
    )

    result = matrix.run_cell(matrix.MatrixCell("medium", "balanced_v1"))

    assert result.run_id == "20260531_100000"
    assert backtest_config.read_text(encoding="utf-8") == "top_k = 8\n"
    assert runner_config.read_text(encoding="utf-8") == "top_k = 8\n"


def test_markdown_report_contains_profile_strategy_run_id_and_compare_status() -> None:
    result = _result(
        profile="medium",
        strategy_profile="balanced_v1",
        run_id="20260531_100000",
        compare_matched=True,
    )

    report = matrix.build_markdown_report([result], generated_at="2026-05-31T10:00:00")

    assert "# Profile Robustness Matrix" in report
    assert "2026-05-31T10:00:00" in report
    assert "| medium | balanced_v1 | 20260531_100000 | true |" in report
    assert "| medium | balanced_v1 | 12.30% | 8.40% | -6.70% |" in report


def test_failed_runs_are_visible_in_report() -> None:
    result = _result(
        profile="long",
        strategy_profile="offensive_v1",
        run_id=None,
        compare_matched=None,
        success=False,
        error="run_bt_run_agent failed with returncode 2",
        stderr_excerpt="boom",
        missing=("run_dir", "manifest"),
    )

    report = matrix.build_markdown_report([result], generated_at="2026-05-31T10:00:00")

    assert "| long | offensive_v1 | n/a | n/a |" in report
    assert "long/offensive_v1: error: run_bt_run_agent failed with returncode 2" in report
    assert "long/offensive_v1: missing: run_dir, manifest" in report
    assert "stderr excerpt: `boom`" in report


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
    profile: str,
    strategy_profile: str,
    run_id: str | None,
    compare_matched: bool | None,
    success: bool = True,
    error: str | None = None,
    stderr_excerpt: str | None = None,
    missing: tuple[str, ...] = (),
) -> matrix.MatrixRunResult:
    return matrix.MatrixRunResult(
        profile=profile,
        strategy_profile=strategy_profile,
        command=("python", "-m", "scripts.run_bt_run_agent"),
        returncode=0 if success else 2,
        run_id=run_id,
        run_dir="runs/example" if run_id else None,
        manifest_path="runs/example/run_manifest.json" if run_id else None,
        summary_path="runs/example/summary.txt" if run_id else None,
        compare_matched=compare_matched,
        success=success,
        error=error,
        stdout_excerpt=None,
        stderr_excerpt=stderr_excerpt,
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
        missing=missing,
    )

import json
from datetime import datetime
from pathlib import Path

from app.application.bt_run.dto import CompareAllRunsRequest
from app.application.bt_run.use_cases import CompareAllRunsUseCase
from app.domain.bt_run.run_context import CompareMode, RunContext, RunProfile
from app.domain.bt_run.run_result import CompareResult, RunResult, StepResult
from app.infrastructure.storage.decision_bundle_store import FileDecisionBundleStore
from scripts.run_bt_run_agent import (
    build_backtest_profile_args,
    build_run_context,
    build_run_manifest,
    resolve_profile_behavior,
)


def test_run_profile_compare_modes() -> None:
    assert resolve_profile_behavior(RunProfile.SHORT).compare_mode == CompareMode.LATEST
    assert resolve_profile_behavior(RunProfile.MEDIUM).compare_mode == CompareMode.ALL
    assert resolve_profile_behavior(RunProfile.LONG).compare_mode == CompareMode.ALL
    assert resolve_profile_behavior(RunProfile.PROBLEM).compare_mode == CompareMode.ALL


def test_run_profiles_define_backtest_scope() -> None:
    assert resolve_profile_behavior(RunProfile.SHORT).backtest_lookback_months == 18
    assert resolve_profile_behavior(RunProfile.MEDIUM).backtest_lookback_months == 30
    assert resolve_profile_behavior(RunProfile.LONG).backtest_lookback_months is None
    assert resolve_profile_behavior(RunProfile.PROBLEM).backtest_lookback_months == 18


def test_run_profiles_define_compare_point_counts() -> None:
    assert resolve_profile_behavior(RunProfile.SHORT).compare_point_count == 1
    assert resolve_profile_behavior(RunProfile.PROBLEM).compare_point_count == 1
    assert resolve_profile_behavior(RunProfile.MEDIUM).compare_point_count == 3
    assert resolve_profile_behavior(RunProfile.LONG).compare_point_count == 6
    assert (
        resolve_profile_behavior(RunProfile.LONG).compare_point_count
        > resolve_profile_behavior(RunProfile.MEDIUM).compare_point_count
    )


def test_backtest_profile_args_apply_limited_scope(tmp_path: Path) -> None:
    config_path = tmp_path / "bt.toml"
    config_path.write_text('as_of = "2025-10-08"\n', encoding="utf-8")

    args = build_backtest_profile_args(
        resolve_profile_behavior(RunProfile.SHORT),
        backtest_config_path=config_path,
    )

    assert args == ("--start", "2024-04-08")


def test_backtest_profile_args_keep_full_scope_for_long(tmp_path: Path) -> None:
    config_path = tmp_path / "bt.toml"
    config_path.write_text('as_of = "2025-10-08"\n', encoding="utf-8")

    args = build_backtest_profile_args(
        resolve_profile_behavior(RunProfile.LONG),
        backtest_config_path=config_path,
    )

    assert args == ()


def test_problem_profile_enables_runner_debug_dump_flags() -> None:
    behavior = resolve_profile_behavior(RunProfile.PROBLEM)

    assert behavior.runner_extra_args == ("--dump-selection", "--dump-weights")


def test_non_problem_profiles_do_not_add_runner_debug_dump_flags() -> None:
    assert resolve_profile_behavior(RunProfile.SHORT).runner_extra_args == ()
    assert resolve_profile_behavior(RunProfile.MEDIUM).runner_extra_args == ()
    assert resolve_profile_behavior(RunProfile.LONG).runner_extra_args == ()


def test_build_run_context_uses_profile_behavior_for_compare_mode() -> None:
    assert build_run_context(RunProfile.SHORT).compare_mode == CompareMode.LATEST
    assert build_run_context(RunProfile.MEDIUM).compare_mode == CompareMode.ALL
    assert build_run_context(RunProfile.LONG).compare_mode == CompareMode.ALL
    assert build_run_context(RunProfile.PROBLEM).compare_mode == CompareMode.ALL


def test_build_run_context_uses_run_specific_decisions_directory() -> None:
    context = build_run_context(RunProfile.LONG)

    assert context.decisions_dir.name == context.run_id
    assert context.decisions_dir.parent.name == "decisions"


def test_compare_all_uses_only_current_run_decisions_directory(tmp_path: Path) -> None:
    old_run_dir = tmp_path / "decisions" / "old-run"
    current_run_dir = tmp_path / "decisions" / "current-run"
    old_run_dir.mkdir(parents=True)
    current_run_dir.mkdir(parents=True)

    _write_decision_bundle(old_run_dir / "BT_old_2025-01-31.json", "BT", "2025-01-31", {"AAPL": 1.0})
    _write_decision_bundle(old_run_dir / "RUN_old_2025-01-31.json", "RUN", "2025-01-31", {"MSFT": 1.0})
    _write_decision_bundle(current_run_dir / "BT_current_2025-01-31.json", "BT", "2025-01-31", {"AAPL": 1.0})
    _write_decision_bundle(current_run_dir / "RUN_current_2025-01-31.json", "RUN", "2025-01-31", {"AAPL": 1.0})

    response = CompareAllRunsUseCase(FileDecisionBundleStore(current_run_dir)).execute(
        CompareAllRunsRequest()
    )

    assert response.success is True
    assert response.matched_count == 1
    assert response.mismatched_count == 0


def _write_decision_bundle(path: Path, kind: str, as_of: str, weights: dict[str, float]) -> None:
    path.write_text(
        json.dumps(
            {
                "kind": kind,
                "as_of": as_of,
                "new_weights": weights,
            }
        ),
        encoding="utf-8",
    )


def test_build_run_manifest_includes_full_step_result_fields() -> None:
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=Path("D:/ai_agents"),
        aktien_oop_dir=Path("D:/ai_agents/aktien_oop"),
        decisions_dir=Path("D:/ai_agents/aktien_oop/decisions"),
        output_dir=Path("D:/ai_agents/automation_runs/2026-03-29_12-34-56_short"),
        backtest_config_path=Path("D:/ai_agents/aktien_oop/backtest_config.toml"),
        runner_config_path=Path("D:/ai_agents/aktien_oop/configs/runner_config.toml"),
    )
    result = RunResult(
        success=True,
        backtest=StepResult(
            success=True,
            command=("python", "-m", "aktien_oop.backtest"),
            cwd="D:/ai_agents",
            returncode=0,
            duration_seconds=12.5,
            timed_out=False,
            stdout="backtest ok",
            stderr="",
            message="Backtest completed",
        ),
        runner=StepResult(
            success=False,
            command=("python", "-m", "aktien_oop.main"),
            cwd="D:/ai_agents",
            returncode=2,
            duration_seconds=3.2,
            timed_out=False,
            stdout="runner out",
            stderr="runner err",
            message="Runner failed",
        ),
        compare=CompareResult(success=False, matched=None, message="Compare skipped"),
        warnings=("warning-1",),
    )

    manifest = build_run_manifest(context, result)

    assert manifest["profile_behavior"] == "fast smoke test: latest compare, 18-month backtest scope"
    assert manifest["compare_point_count"] == 1
    assert manifest["backtest"]["command"] == ["python", "-m", "aktien_oop.backtest"]
    assert manifest["backtest"]["returncode"] == 0
    assert manifest["backtest"]["duration_seconds"] == 12.5
    assert manifest["backtest"]["stdout"] == "backtest ok"
    assert manifest["backtest"]["stderr"] == ""
    assert manifest["backtest"]["cwd"] == "D:/ai_agents"
    assert manifest["backtest"]["timed_out"] is False
    assert manifest["backtest"]["message"] == "Backtest completed"
    assert manifest["runner"]["command"] == ["python", "-m", "aktien_oop.main"]
    assert manifest["runner"]["returncode"] == 2
    assert manifest["runner"]["duration_seconds"] == 3.2
    assert manifest["runner"]["stdout"] == "runner out"
    assert manifest["runner"]["stderr"] == "runner err"
    assert manifest["runner"]["cwd"] == "D:/ai_agents"
    assert manifest["runner"]["timed_out"] is False
    assert manifest["runner"]["message"] == "Runner failed"

    encoded = json.dumps(manifest)
    decoded = json.loads(encoded)

    assert decoded["backtest"]["command"] == ["python", "-m", "aktien_oop.backtest"]
    assert decoded["runner"]["command"] == ["python", "-m", "aktien_oop.main"]

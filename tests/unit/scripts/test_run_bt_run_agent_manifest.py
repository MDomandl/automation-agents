import json
from datetime import datetime
from pathlib import Path

from app.domain.bt_run.run_context import CompareMode, RunContext, RunProfile
from app.domain.bt_run.run_result import CompareResult, RunResult, StepResult
from scripts.run_bt_run_agent import build_run_manifest


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

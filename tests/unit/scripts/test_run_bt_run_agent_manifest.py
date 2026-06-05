import json
from datetime import datetime
from pathlib import Path

from app.application.bt_run.dto import CompareAllRunsRequest
from app.application.bt_run.use_cases import CompareAllRunsUseCase
from app.domain.bt_run.run_context import CompareMode, RunContext, RunProfile
from app.domain.bt_run.run_result import CompareResult, RunResult, StepResult
from app.infrastructure.storage.decision_bundle_store import FileDecisionBundleStore
from scripts.run_bt_run_agent import (
    build_backtest_command,
    build_backtest_profile_args,
    build_run_context,
    build_run_manifest,
    load_strategy_profile_for_cli,
    parse_args,
    resolve_profile_behavior,
    write_strategy_profile_config_overlays,
)
from scripts.strategy_profiles import StrategyProfileError


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


def test_parse_args_accepts_phase_window_options() -> None:
    args = parse_args(
        [
            "--profile",
            "medium",
            "--strategy-profile",
            "balanced_v1",
            "--start",
            "2022-01-01",
            "--end",
            "2022-12-31",
            "--phase-name",
            "bear_market_2022",
        ]
    )

    assert args.profile == "medium"
    assert args.strategy_profile == "balanced_v1"
    assert args.start == "2022-01-01"
    assert args.end == "2022-12-31"
    assert args.phase_name == "bear_market_2022"


def test_backtest_profile_args_pass_explicit_start_and_end(tmp_path: Path) -> None:
    config_path = tmp_path / "bt.toml"
    config_path.write_text('as_of = "2025-10-08"\n', encoding="utf-8")

    args = build_backtest_profile_args(
        resolve_profile_behavior(RunProfile.MEDIUM),
        backtest_config_path=config_path,
        start_override="2022-01-01",
        end_override="2022-12-31",
    )

    assert args == ("--start", "2022-01-01", "--end", "2022-12-31")


def test_backtest_profile_args_explicit_start_overrides_profile_lookback(tmp_path: Path) -> None:
    config_path = tmp_path / "bt.toml"
    config_path.write_text('as_of = "2025-10-08"\n', encoding="utf-8")

    args = build_backtest_profile_args(
        resolve_profile_behavior(RunProfile.MEDIUM),
        backtest_config_path=config_path,
        start_override="2022-01-01",
    )

    assert args == ("--start", "2022-01-01")
    assert "2023-04-08" not in args


def test_build_backtest_command_includes_phase_window_args(tmp_path: Path) -> None:
    config_path = tmp_path / "bt.toml"
    decisions_dir = tmp_path / "decisions"

    command = build_backtest_command(
        config_path=config_path,
        decisions_dir=decisions_dir,
        profile_args=("--start", "2022-01-01", "--end", "2022-12-31"),
    )

    assert command[-4:] == ("--start", "2022-01-01", "--end", "2022-12-31")
    assert "--config" in command
    assert str(config_path) in command
    assert "--decisions-dir" in command
    assert str(decisions_dir) in command


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

    _write_decision_bundle(
        old_run_dir / "BT_old_2025-01-31.json",
        "BT",
        "2025-01-31",
        {"AAPL": 1.0},
    )
    _write_decision_bundle(
        old_run_dir / "RUN_old_2025-01-31.json",
        "RUN",
        "2025-01-31",
        {"MSFT": 1.0},
    )
    _write_decision_bundle(
        current_run_dir / "BT_current_2025-01-31.json",
        "BT",
        "2025-01-31",
        {"AAPL": 1.0},
    )
    _write_decision_bundle(
        current_run_dir / "RUN_current_2025-01-31.json",
        "RUN",
        "2025-01-31",
        {"AAPL": 1.0},
    )

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

    assert (
        manifest["profile_behavior"] == "fast smoke test: latest compare, 18-month backtest scope"
    )
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


def test_build_run_manifest_includes_phase_window_metadata() -> None:
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_medium",
        profile=RunProfile.MEDIUM,
        compare_mode=CompareMode.ALL,
        ai_agents_dir=Path("D:/ai_agents"),
        aktien_oop_dir=Path("D:/ai_agents/aktien_oop"),
        decisions_dir=Path("D:/ai_agents/aktien_oop/decisions"),
        output_dir=Path("D:/ai_agents/automation_runs/2026-03-29_12-34-56_medium"),
        backtest_config_path=Path("D:/ai_agents/aktien_oop/backtest_config.toml"),
        runner_config_path=Path("D:/ai_agents/aktien_oop/configs/runner_config.toml"),
    )
    result = RunResult(
        success=True,
        backtest=StepResult(True, (), None, 0, 0.0, False, "", "", ""),
        runner=StepResult(True, (), None, 0, 0.0, False, "", "", ""),
        compare=CompareResult(success=True, matched=True, message="ok"),
    )

    manifest = build_run_manifest(
        context,
        result,
        phase_name="bear_market_2022",
        phase_start="2022-01-01",
        phase_end="2022-12-31",
        explicit_time_window=True,
        effective_backtest_start="2022-01-01",
        effective_backtest_end="2022-12-31",
    )

    assert manifest["phase_name"] == "bear_market_2022"
    assert manifest["phase_start"] == "2022-01-01"
    assert manifest["phase_end"] == "2022-12-31"
    assert manifest["explicit_time_window"] is True
    assert manifest["effective_backtest_start"] == "2022-01-01"
    assert manifest["effective_backtest_end"] == "2022-12-31"


def test_strategy_profile_name_loads_profile_config() -> None:
    profile = load_strategy_profile_for_cli("balanced_v1")

    assert profile.name == "balanced_v1"
    assert profile.label == "Balanced v1"
    assert profile.source_path == Path("configs/profiles/balanced_v1.toml")


def test_strategy_profile_path_loads_same_profile_config() -> None:
    by_name = load_strategy_profile_for_cli("balanced_v1")
    by_path = load_strategy_profile_for_cli("configs/profiles/balanced_v1.toml")

    assert by_path == by_name


def test_invalid_strategy_profile_name_has_clear_error() -> None:
    try:
        load_strategy_profile_for_cli("does_not_exist_v1")
    except StrategyProfileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected invalid strategy profile name to raise")

    assert "Unknown strategy profile" in message
    assert "balanced_v1" in message


def test_invalid_strategy_profile_file_has_clear_error(tmp_path: Path) -> None:
    profile_path = tmp_path / "broken.toml"
    profile_path.write_text("profile_name = [", encoding="utf-8")

    try:
        load_strategy_profile_for_cli(str(profile_path))
    except StrategyProfileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected invalid strategy profile file to raise")

    assert "Invalid profile TOML" in message
    assert str(profile_path) in message


def test_strategy_profile_overlay_writes_run_specific_config_copies(tmp_path: Path) -> None:
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=tmp_path / "aktien_oop" / "decisions" / "20260329_123456",
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_short",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
    )
    base_config = "\n".join(
        [
            'benchmark_ticker = "SPY"',
            'benchmark2 = "SPY"',
            "top_k = 8",
            "max_turnover_cap = 0.35",
            "include_cash = true",
            "cash_yield_annual = 0.02",
            "",
            "[universe]",
            'name = "sp500_top100"',
            'tickers_file = "aktien_oop/universes/sp500_tickers_top100.txt"',
            'meta_file = "aktien_oop/universes/sp500_meta_top100.csv"',
            "",
            "[limits]",
            "use_sector_limits = false",
            "max_per_sector = 4",
            "",
            "[regime]",
            "require_above_sma = false",
            "regime_sma_days = 100",
            'regime_below_action = "SELL"',
        ]
    )
    context.backtest_config_path.parent.mkdir(parents=True)
    context.runner_config_path.parent.mkdir(parents=True)
    context.backtest_config_path.write_text(base_config, encoding="utf-8")
    context.runner_config_path.write_text(base_config, encoding="utf-8")
    profile = load_strategy_profile_for_cli("balanced_v1")

    backtest_overlay, runner_overlay = write_strategy_profile_config_overlays(context, profile)

    assert context.backtest_config_path.read_text(encoding="utf-8") == base_config
    assert context.runner_config_path.read_text(encoding="utf-8") == base_config
    for overlay in (backtest_overlay, runner_overlay):
        updated = overlay.read_text(encoding="utf-8")
        assert 'name = "sp500"' in updated
        assert "top_k = 15" in updated
        assert "use_sector_limits = true" in updated
        assert "max_per_sector = 2" in updated
        assert "max_turnover_cap = 0.20" in updated
        assert 'benchmark_ticker = "SXR8.DE"' in updated
        assert "include_cash = false" in updated
        assert "cash_yield_annual = 0.00" in updated
        assert "require_above_sma = true" in updated
        assert "regime_sma_days = 200" in updated
        assert 'regime_below_action = "HOLD"' in updated


def test_strategy_profile_overlay_works_with_start_end_command_args(tmp_path: Path) -> None:
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_medium",
        profile=RunProfile.MEDIUM,
        compare_mode=CompareMode.ALL,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=tmp_path / "aktien_oop" / "decisions" / "20260329_123456",
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_medium",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
    )
    base_config = "\n".join(
        [
            'as_of = "2025-10-08"',
            'benchmark_ticker = "SPY"',
            "top_k = 8",
            "max_turnover_cap = 0.35",
            "",
            "[universe]",
            'name = "sp500_top100"',
            'tickers_file = "aktien_oop/universes/sp500_tickers_top100.txt"',
            'meta_file = "aktien_oop/universes/sp500_meta_top100.csv"',
            "",
            "[limits]",
            "use_sector_limits = false",
            "max_per_sector = 4",
            "",
            "[regime]",
            "require_above_sma = false",
            "regime_sma_days = 100",
            'regime_below_action = "SELL"',
        ]
    )
    context.backtest_config_path.parent.mkdir(parents=True)
    context.runner_config_path.parent.mkdir(parents=True)
    context.backtest_config_path.write_text(base_config, encoding="utf-8")
    context.runner_config_path.write_text(base_config, encoding="utf-8")
    profile = load_strategy_profile_for_cli("balanced_v1")

    backtest_overlay, _ = write_strategy_profile_config_overlays(context, profile)
    profile_args = build_backtest_profile_args(
        resolve_profile_behavior(RunProfile.MEDIUM),
        backtest_config_path=backtest_overlay,
        start_override="2022-01-01",
        end_override="2022-12-31",
    )
    command = build_backtest_command(
        config_path=backtest_overlay,
        decisions_dir=context.decisions_dir,
        profile_args=profile_args,
    )

    assert context.backtest_config_path.read_text(encoding="utf-8") == base_config
    assert "--config" in command
    assert str(backtest_overlay) in command
    assert command[-4:] == ("--start", "2022-01-01", "--end", "2022-12-31")


def test_build_run_manifest_includes_strategy_profile_metadata() -> None:
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
        backtest=StepResult(True, (), None, 0, 0.0, False, "", "", ""),
        runner=StepResult(True, (), None, 0, 0.0, False, "", "", ""),
        compare=CompareResult(success=True, matched=True, message="ok"),
    )
    profile = load_strategy_profile_for_cli("balanced_v1")

    manifest = build_run_manifest(context, result, strategy_profile=profile)

    assert manifest["strategy_profile_name"] == "balanced_v1"
    assert manifest["strategy_profile_label"] == "Balanced v1"
    assert manifest["strategy_profile_file"] == "configs/profiles/balanced_v1.toml"
    assert manifest["universe"] == "sp500"
    assert manifest["top_k"] == 15
    assert manifest["use_sector_limits"] is True
    assert manifest["max_per_sector"] == 2
    assert manifest["max_turnover_cap"] == 0.20
    assert manifest["require_above_sma"] is True
    assert manifest["regime_below_action"] == "HOLD"
    assert manifest["include_cash"] is False
    assert manifest["cash_yield_annual"] == 0.00
    assert manifest["regime_sma_days"] == 200
    assert manifest["benchmark_ticker"] == "SXR8.DE"

import json
from datetime import datetime
from pathlib import Path

from app.application.bt_run.dto import CompareAllRunsRequest
from app.application.bt_run.use_cases import CompareAllRunsUseCase
from app.domain.bt_run.run_context import CompareMode, RunContext, RunnerMode, RunProfile
from app.domain.bt_run.run_result import CompareResult, RunResult, StepResult
from app.infrastructure.storage.decision_bundle_store import FileDecisionBundleStore
from scripts.run_bt_run_agent import (
    PROPOSAL_DELTA_TOLERANCE,
    PortfolioFileError,
    build_backtest_command,
    build_backtest_profile_args,
    build_paper_run_artifact,
    build_run_context,
    build_run_manifest,
    load_portfolio_positions_csv,
    load_strategy_profile_for_cli,
    parse_args,
    resolve_profile_behavior,
    write_paper_run_report,
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
            "--warmup-start",
            "2020-07-01",
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
    assert args.warmup_start == "2020-07-01"
    assert args.start == "2022-01-01"
    assert args.end == "2022-12-31"
    assert args.phase_name == "bear_market_2022"


def test_parse_args_accepts_runner_mode_paper() -> None:
    args = parse_args(["--runner-mode", "paper"])

    assert args.runner_mode == "paper"


def test_parse_args_accepts_portfolio_file() -> None:
    args = parse_args(["--runner-mode", "paper", "--portfolio-file", "positions.csv"])

    assert args.runner_mode == "paper"
    assert args.portfolio_file == "positions.csv"


def test_parse_args_accepts_portfolio_name() -> None:
    args = parse_args(["--runner-mode", "paper", "--portfolio-name", "example_previous_state"])

    assert args.runner_mode == "paper"
    assert args.portfolio_name == "example_previous_state"
    assert args.portfolio_file is None


def test_parse_args_defaults_runner_mode_to_analysis() -> None:
    args = parse_args([])

    assert args.runner_mode == "analysis"
    assert args.portfolio_file is None
    assert args.portfolio_name is None


def test_parse_args_rejects_invalid_warmup_phase_order() -> None:
    try:
        parse_args(
            [
                "--warmup-start",
                "2022-02-01",
                "--start",
                "2022-01-01",
                "--end",
                "2022-12-31",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected invalid warmup/start order to fail")


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


def test_backtest_profile_args_use_warmup_start_as_effective_backtest_start(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "bt.toml"
    config_path.write_text('as_of = "2025-10-08"\n', encoding="utf-8")

    args = build_backtest_profile_args(
        resolve_profile_behavior(RunProfile.MEDIUM),
        backtest_config_path=config_path,
        start_override="2020-07-01",
        end_override="2022-12-31",
    )

    assert args == ("--start", "2020-07-01", "--end", "2022-12-31")


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


def test_build_run_context_defaults_to_analysis_mode() -> None:
    context = build_run_context(RunProfile.SHORT)

    assert context.runner_mode == RunnerMode.ANALYSIS
    assert context.run_label.endswith("_short_analysis")


def test_build_run_context_accepts_paper_mode() -> None:
    context = build_run_context(RunProfile.SHORT, RunnerMode.PAPER)

    assert context.runner_mode == RunnerMode.PAPER
    assert context.run_label.endswith("_short_paper")


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
        runner_mode=RunnerMode.PAPER,
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
    assert manifest["runner_mode"] == "paper"
    assert manifest["execution"]["approval_status"] == "manual_approval_required"
    assert manifest["execution"]["orders_executed"] is False
    assert manifest["execution"]["broker_connected"] is False
    assert manifest["execution"]["live_trading_enabled"] is False
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
        warmup_start="2020-07-01",
        phase_start="2022-01-01",
        phase_end="2022-12-31",
        explicit_time_window=True,
        effective_backtest_start="2020-07-01",
        effective_backtest_end="2022-12-31",
    )

    assert manifest["phase_name"] == "bear_market_2022"
    assert manifest["warmup_start"] == "2020-07-01"
    assert manifest["phase_start"] == "2022-01-01"
    assert manifest["phase_end"] == "2022-12-31"
    assert manifest["explicit_time_window"] is True
    assert manifest["effective_backtest_start"] == "2020-07-01"
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


def test_build_paper_run_artifact_uses_latest_runner_decision_bundle(tmp_path: Path) -> None:
    decisions_dir = tmp_path / "decisions"
    decisions_dir.mkdir()
    (decisions_dir / "RUN_old_2025-09-30.json").write_text(
        json.dumps(
            {
                "kind": "RUN",
                "as_of": "2025-09-30",
                "new_weights": {"OLD": 1.0},
            }
        ),
        encoding="utf-8",
    )
    latest_path = decisions_dir / "RUN_latest_2025-10-08.json"
    latest_path.write_text(
        json.dumps(
            {
                "kind": "RUN",
                "as_of": "2025-10-08",
                "previous_weights": {"AAPL": 0.10, "MSFT": 0.20},
                "new_weights": {"AAPL": 0.15, "NVDA": 0.25, "CASH": 0.60},
            }
        ),
        encoding="utf-8",
    )
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short_paper",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=decisions_dir,
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_short_paper",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
        runner_mode=RunnerMode.PAPER,
    )
    result = RunResult(
        success=True,
        backtest=StepResult(True),
        runner=StepResult(True),
        compare=CompareResult(success=True, matched=True, message="ok"),
        warnings=("[WARN] example",),
    )
    profile = load_strategy_profile_for_cli("balanced_v1")

    artifact = build_paper_run_artifact(context, result, strategy_profile=profile)

    assert artifact["runner_mode"] == "paper"
    assert artifact["approval_status"] == "manual_approval_required"
    assert artifact["orders_executed"] is False
    assert artifact["broker_connected"] is False
    assert artifact["live_trading_enabled"] is False
    assert artifact["execution"]["orders_executed"] is False
    assert artifact["execution"]["broker_connected"] is False
    assert artifact["execution"]["live_trading_enabled"] is False
    assert artifact["strategy_profile_name"] == "balanced_v1"
    assert artifact["universe"] == "sp500"
    assert artifact["decision_bundle"] == str(latest_path)
    assert artifact["portfolio_name"] is None
    assert artifact["portfolio_source"] == "runner_previous_state"
    assert artifact["portfolio_file"] is None
    assert artifact["proposal_delta_tolerance"] == PROPOSAL_DELTA_TOLERANCE
    assert artifact["proposal_delta_basis"] == "runner previous-state"
    assert artifact["as_of"] == "2025-10-08"
    assert artifact["target_positions"] == {"AAPL": 0.15, "NVDA": 0.25, "CASH": 0.60}
    assert artifact["cash_weight"] == 0.60
    assert {
        "ticker": "NVDA",
        "previous_weight": 0.0,
        "target_weight": 0.25,
        "delta_weight": 0.25,
    } in artifact["buy_proposals"]
    assert {
        "ticker": "MSFT",
        "previous_weight": 0.20,
        "target_weight": 0.0,
        "delta_weight": -0.20,
    } in artifact["sell_proposals"]
    assert artifact["human_review_required"]["required"] is True
    assert "current market data" in artifact["human_review_required"]["checklist"]
    assert "No real order was executed." in artifact["warnings"]
    assert "No broker connection was used." in artifact["warnings"]
    assert "This report is a proposal only." in artifact["warnings"]
    assert "[WARN] example" in artifact["warnings"]


def test_load_portfolio_positions_csv_reads_normalized_weights(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\n aapl ,0.12\nMSFT,0.08\n", encoding="utf-8")

    positions = load_portfolio_positions_csv(portfolio_path)

    assert positions == {"AAPL": 0.12, "MSFT": 0.08}


def test_load_portfolio_positions_csv_tolerates_weight_whitespace(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\nAAPL, 0.12 \nMSFT,\t0.08\t\n", encoding="utf-8")

    positions = load_portfolio_positions_csv(portfolio_path)

    assert positions == {"AAPL": 0.12, "MSFT": 0.08}


def test_load_portfolio_positions_csv_allows_weights_not_summing_to_one(
    tmp_path: Path,
) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\nAAPL,0.30\nMSFT,0.20\n", encoding="utf-8")

    positions = load_portfolio_positions_csv(portfolio_path)

    assert positions == {"AAPL": 0.30, "MSFT": 0.20}
    assert sum(positions.values()) == 0.50


def test_load_portfolio_positions_csv_keeps_symbols_outside_target_portfolio(
    tmp_path: Path,
) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\nUNKNOWN,0.10\nAAPL,0.20\n", encoding="utf-8")

    positions = load_portfolio_positions_csv(portfolio_path)

    assert positions == {"UNKNOWN": 0.10, "AAPL": 0.20}


def test_load_portfolio_positions_csv_ignores_empty_lines(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\n\nAAPL,0.10\n\nMSFT,0.20\n", encoding="utf-8")

    positions = load_portfolio_positions_csv(portfolio_path)

    assert positions == {"AAPL": 0.10, "MSFT": 0.20}


def test_load_portfolio_positions_csv_rejects_missing_file(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "missing.csv"

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected missing portfolio file to raise")

    assert "Portfolio file not found" in message
    assert str(portfolio_path) in message


def test_load_portfolio_positions_csv_rejects_missing_symbol_column(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("ticker,weight\nAAPL,0.10\n", encoding="utf-8")

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected missing symbol column to raise")

    assert "missing required column" in message
    assert "symbol" in message


def test_load_portfolio_positions_csv_rejects_missing_weight_column(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,allocation\nAAPL,0.10\n", encoding="utf-8")

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected missing weight column to raise")

    assert "missing required column" in message
    assert "weight" in message


def test_load_portfolio_positions_csv_rejects_empty_symbol(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\n ,0.10\n", encoding="utf-8")

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected empty symbol to raise")

    assert "empty symbol" in message


def test_load_portfolio_positions_csv_rejects_empty_weight(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\nAAPL, \n", encoding="utf-8")

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected empty weight to raise")

    assert "empty weight" in message
    assert "AAPL" in message


def test_load_portfolio_positions_csv_rejects_non_numeric_weight(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\nAAPL,not-a-number\n", encoding="utf-8")

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected non-numeric weight to raise")

    assert "invalid weight" in message
    assert "AAPL" in message


def test_load_portfolio_positions_csv_rejects_negative_weight(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\nAAPL,-0.01\n", encoding="utf-8")

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected negative weight to raise")

    assert "negative weight" in message
    assert "AAPL" in message


def test_load_portfolio_positions_csv_rejects_duplicate_symbol(tmp_path: Path) -> None:
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\n aapl ,0.10\nAAPL,0.20\n", encoding="utf-8")

    try:
        load_portfolio_positions_csv(portfolio_path)
    except PortfolioFileError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected duplicate symbol to raise")

    assert "duplicate symbol" in message
    assert "AAPL" in message


def test_build_paper_run_artifact_uses_portfolio_file_for_previous_weights(
    tmp_path: Path,
) -> None:
    decisions_dir = tmp_path / "decisions"
    decisions_dir.mkdir()
    latest_path = decisions_dir / "RUN_latest_2025-10-08.json"
    latest_path.write_text(
        json.dumps(
            {
                "kind": "RUN",
                "as_of": "2025-10-08",
                "previous_weights": {"AAPL": 0.99},
                "new_weights": {"AAPL": 0.15, "NVDA": 0.25},
            }
        ),
        encoding="utf-8",
    )
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text("symbol,weight\naapl,0.10\nMSFT,0.20\n", encoding="utf-8")
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short_paper",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=decisions_dir,
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_short_paper",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
        runner_mode=RunnerMode.PAPER,
    )
    result = RunResult(
        success=True,
        backtest=StepResult(True),
        runner=StepResult(True),
        compare=CompareResult(success=True, matched=True, message="ok"),
        warnings=(
            "[INFO] Runner previous-state seeded from backtest positions: rows=2",
            "[WARN] example",
        ),
    )

    artifact = build_paper_run_artifact(
        context,
        result,
        portfolio_file=portfolio_path,
        portfolio_name="example_previous_state",
    )

    assert artifact["decision_bundle"] == str(latest_path)
    assert artifact["portfolio_name"] == "example_previous_state"
    assert artifact["portfolio_source"] == "portfolio_file"
    assert artifact["portfolio_file"] == str(portfolio_path)
    assert artifact["proposal_delta_tolerance"] == PROPOSAL_DELTA_TOLERANCE
    assert artifact["proposal_delta_basis"] == "local portfolio file"
    assert "[WARN] example" in artifact["warnings"]
    assert not any("previous-state seeded" in warning for warning in artifact["warnings"])
    assert artifact["technical_info"] == [
        "[INFO] Runner previous-state seeded from backtest positions: rows=2"
    ]
    assert {
        "ticker": "AAPL",
        "previous_weight": 0.10,
        "target_weight": 0.15,
        "delta_weight": 0.04999999999999999,
    } in artifact["buy_proposals"]
    assert {
        "ticker": "NVDA",
        "previous_weight": 0.0,
        "target_weight": 0.25,
        "delta_weight": 0.25,
    } in artifact["buy_proposals"]
    assert {
        "ticker": "MSFT",
        "previous_weight": 0.20,
        "target_weight": 0.0,
        "delta_weight": -0.20,
    } in artifact["sell_proposals"]
    assert artifact["orders_executed"] is False
    assert artifact["execution"]["orders_executed"] is False
    assert artifact["execution"]["broker_connected"] is False
    assert artifact["execution"]["live_trading_enabled"] is False


def test_build_paper_run_artifact_classifies_proposals_with_tolerance(
    tmp_path: Path,
) -> None:
    decisions_dir = tmp_path / "decisions"
    decisions_dir.mkdir()
    (decisions_dir / "RUN_latest_2025-10-08.json").write_text(
        json.dumps(
            {
                "kind": "RUN",
                "as_of": "2025-10-08",
                "new_weights": {
                    "BUY": 0.10002,
                    "SELL": 0.09998,
                    "HOLD_POS": 0.100009,
                    "HOLD_NEG": 0.099991,
                },
            }
        ),
        encoding="utf-8",
    )
    portfolio_path = tmp_path / "positions.csv"
    portfolio_path.write_text(
        "symbol,weight\nBUY,0.10\nSELL,0.10\nHOLD_POS,0.10\nHOLD_NEG,0.10\n",
        encoding="utf-8",
    )
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short_paper",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=decisions_dir,
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_short_paper",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
        runner_mode=RunnerMode.PAPER,
    )
    result = RunResult(
        success=True,
        backtest=StepResult(True),
        runner=StepResult(True),
        compare=CompareResult(success=True, matched=True, message="ok"),
    )

    artifact = build_paper_run_artifact(context, result, portfolio_file=portfolio_path)

    assert [item["ticker"] for item in artifact["buy_proposals"]] == ["BUY"]
    assert [item["ticker"] for item in artifact["sell_proposals"]] == ["SELL"]
    assert [item["ticker"] for item in artifact["hold_proposals"]] == [
        "HOLD_NEG",
        "HOLD_POS",
    ]
    hold_deltas = {
        item["ticker"]: item["delta_weight"] for item in artifact["hold_proposals"]
    }
    assert hold_deltas["HOLD_POS"] > 0
    assert hold_deltas["HOLD_NEG"] < 0


def test_build_paper_run_artifact_keeps_runner_previous_state_with_tolerance(
    tmp_path: Path,
) -> None:
    decisions_dir = tmp_path / "decisions"
    decisions_dir.mkdir()
    (decisions_dir / "RUN_latest_2025-10-08.json").write_text(
        json.dumps(
            {
                "kind": "RUN",
                "as_of": "2025-10-08",
                "previous_weights": {"TINY": 0.111111},
                "new_weights": {"TINY": 0.1111111111111111},
            }
        ),
        encoding="utf-8",
    )
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short_paper",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=decisions_dir,
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_short_paper",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
        runner_mode=RunnerMode.PAPER,
    )
    result = RunResult(
        success=True,
        backtest=StepResult(True),
        runner=StepResult(True),
        compare=CompareResult(success=True, matched=True, message="ok"),
    )

    artifact = build_paper_run_artifact(context, result)

    assert artifact["portfolio_source"] == "runner_previous_state"
    assert artifact["portfolio_name"] is None
    assert artifact["buy_proposals"] == []
    assert artifact["sell_proposals"] == []
    assert [item["ticker"] for item in artifact["hold_proposals"]] == ["TINY"]


def test_write_paper_run_report_writes_json_and_text(tmp_path: Path) -> None:
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short_paper",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=tmp_path / "decisions",
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_short_paper",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
        runner_mode=RunnerMode.PAPER,
    )
    context.output_dir.mkdir(parents=True)
    artifact = {
        "run_id": context.run_id,
        "runner_mode": "paper",
        "strategy_profile_name": "balanced_v1",
        "strategy_profile_label": "Balanced v1",
        "universe": "sp500",
        "as_of": "2025-10-08",
        "approval_status": "manual_approval_required",
        "orders_executed": False,
        "broker_connected": False,
        "live_trading_enabled": False,
        "execution": {
            "approval_status": "manual_approval_required",
            "orders_executed": False,
            "broker_connected": False,
            "live_trading_enabled": False,
        },
        "decision_bundle": "RUN_latest.json",
        "portfolio_name": "example_previous_state",
        "portfolio_source": "portfolio_file",
        "portfolio_file": str(tmp_path / "positions.csv"),
        "proposal_delta_tolerance": PROPOSAL_DELTA_TOLERANCE,
        "proposal_delta_basis": "local portfolio file",
        "cash_weight": 0.1,
        "target_positions": {"AAPL": 0.9, "CASH": 0.1},
        "buy_proposals": [
            {
                "ticker": "AAPL",
                "previous_weight": 0.5,
                "target_weight": 0.9,
                "delta_weight": 0.4,
            }
        ],
        "sell_proposals": [
            {
                "ticker": "MSFT",
                "previous_weight": 0.4,
                "target_weight": 0.0,
                "delta_weight": -0.4,
            }
        ],
        "hold_proposals": [
            {
                "ticker": "CASH",
                "previous_weight": 0.1,
                "target_weight": 0.1,
                "delta_weight": 0.0,
            }
        ],
        "human_review_required": {
            "required": True,
            "checklist": [
                "current market data",
                "actual portfolio positions",
                "available liquidity",
                "order costs and spreads",
                "tax effects",
                "personal risk capacity",
            ],
        },
        "warnings": [
            "No real order was executed.",
            "No broker connection was used.",
            "This report is a proposal only.",
        ],
        "technical_info": [
            "[INFO] Runner previous-state seeded from backtest positions: rows=2",
        ],
    }

    report_path = write_paper_run_report(context, artifact)

    assert report_path == context.output_dir / "paper_run_report.json"
    decoded = json.loads(report_path.read_text(encoding="utf-8"))
    assert decoded["orders_executed"] is False
    assert decoded["execution"]["orders_executed"] is False
    assert decoded["broker_connected"] is False
    assert decoded["live_trading_enabled"] is False
    assert decoded["portfolio_name"] == "example_previous_state"
    assert decoded["portfolio_source"] == "portfolio_file"
    assert decoded["portfolio_file"] == str(tmp_path / "positions.csv")
    assert decoded["proposal_delta_tolerance"] == PROPOSAL_DELTA_TOLERANCE
    assert decoded["proposal_delta_basis"] == "local portfolio file"
    assert decoded["target_positions"] == {"AAPL": 0.9, "CASH": 0.1}
    assert decoded["buy_proposals"][0]["delta_weight"] == 0.4
    assert decoded["sell_proposals"][0]["delta_weight"] == -0.4
    assert decoded["human_review_required"]["required"] is True
    text = (context.output_dir / "paper_run_report.txt").read_text(encoding="utf-8")
    assert "Paper Run Report" in text
    assert "This report contains paper-mode proposals only. It is not an order list." in text
    assert "runner_mode: paper" in text
    assert "strategy_profile_name: balanced_v1" in text
    assert "approval_status: manual_approval_required" in text
    assert "orders_executed: false" in text
    assert "broker_connected: false" in text
    assert "live_trading_enabled: false" in text
    assert "portfolio_name: example_previous_state" in text
    assert "portfolio_source: portfolio_file" in text
    assert f"portfolio_file: {tmp_path / 'positions.csv'}" in text
    assert f"proposal_delta_tolerance: {PROPOSAL_DELTA_TOLERANCE}" in text
    assert "proposal_delta_basis: local portfolio file" in text
    assert (
        "proposal_delta_note: Proposal deltas are calculated against the "
        "local portfolio file."
    ) in text
    assert "Target Positions" in text
    assert "- AAPL: 0.900000" in text
    assert "Buy Proposals" in text
    assert "- AAPL: previous 0.500000, target 0.900000, delta 0.400000" in text
    assert "Sell Proposals" in text
    assert "- MSFT: previous 0.400000, target 0.000000, delta -0.400000" in text
    assert "Hold Proposals" in text
    assert "Technical Info" in text
    assert "Runner previous-state seeded from backtest positions" in text
    assert "Human Review Required" in text
    assert "- Check current market data." in text
    assert "- Check actual portfolio positions." in text
    assert "NO REAL ORDER WAS EXECUTED." in text


def test_write_paper_run_report_omits_text_portfolio_name_when_unset(tmp_path: Path) -> None:
    context = RunContext(
        run_id="20260329_123456",
        run_timestamp=datetime(2026, 3, 29, 12, 34, 56),
        run_label="2026-03-29_12-34-56_short_paper",
        profile=RunProfile.SHORT,
        compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path,
        aktien_oop_dir=tmp_path / "aktien_oop",
        decisions_dir=tmp_path / "decisions",
        output_dir=tmp_path / "automation_runs" / "2026-03-29_12-34-56_short_paper",
        backtest_config_path=tmp_path / "aktien_oop" / "backtest_config.toml",
        runner_config_path=tmp_path / "aktien_oop" / "configs" / "runner_config.toml",
        runner_mode=RunnerMode.PAPER,
    )
    context.output_dir.mkdir(parents=True)
    artifact = {
        "run_id": context.run_id,
        "runner_mode": "paper",
        "strategy_profile_name": "balanced_v1",
        "strategy_profile_label": "Balanced v1",
        "universe": "sp500",
        "as_of": "2025-10-08",
        "approval_status": "manual_approval_required",
        "decision_bundle": "RUN_latest.json",
        "portfolio_name": None,
        "portfolio_source": "runner_previous_state",
        "portfolio_file": None,
        "proposal_delta_tolerance": PROPOSAL_DELTA_TOLERANCE,
        "proposal_delta_basis": "runner previous-state",
        "cash_weight": 0.0,
        "target_positions": {},
        "buy_proposals": [],
        "sell_proposals": [],
        "hold_proposals": [],
        "human_review_required": {"required": True, "checklist": []},
        "warnings": [
            "No real order was executed.",
            "No broker connection was used.",
            "This report is a proposal only.",
        ],
        "technical_info": [],
    }

    report_path = write_paper_run_report(context, artifact)

    decoded = json.loads(report_path.read_text(encoding="utf-8"))
    text = (context.output_dir / "paper_run_report.txt").read_text(encoding="utf-8")
    assert decoded["portfolio_name"] is None
    assert "portfolio_name:" not in text
    assert decoded["portfolio_source"] == "runner_previous_state"
    assert decoded["portfolio_file"] is None
    assert decoded["proposal_delta_tolerance"] == PROPOSAL_DELTA_TOLERANCE
    assert decoded["proposal_delta_basis"] == "runner previous-state"
    assert "No real orders were executed." in text
    assert "No broker connection was used." in text
    assert "Live trading was not enabled." in text


def test_all_strategy_profiles_remain_loadable() -> None:
    assert load_strategy_profile_for_cli("conservative_v1").name == "conservative_v1"
    assert load_strategy_profile_for_cli("balanced_v1").name == "balanced_v1"
    assert load_strategy_profile_for_cli("offensive_v1").name == "offensive_v1"

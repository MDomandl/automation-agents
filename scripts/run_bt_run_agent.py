from __future__ import annotations

import argparse
import calendar
import json
import re
import shutil
import sys
import tomllib
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path

from app.agents.bt_run_agent import BtRunAgentInput, BtRunCompareInput
from app.bootstrap.bt_run_container import build_bt_run_agent
from app.domain.bt_run.run_context import RunContext, CompareMode, RunProfile
from app.domain.bt_run.run_result import RunResult, StepResult
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput
from scripts.strategy_profiles import (
    StrategyProfile,
    StrategyProfileError,
    available_strategy_profile_names,
    load_strategy_profile_arg,
    strategy_profile_manifest_fields,
    write_strategy_profile_overlay,
)


OUTPUT_PATH_RE = re.compile(r"^(?P<label>Equity|Positions|Trades|Bench|Summary):\s*(?P<path>.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class ProfileBehavior:
    compare_mode: CompareMode
    runner_extra_args: tuple[str, ...] = ()
    backtest_lookback_months: int | None = None
    compare_point_count: int = 1
    description: str = ""


def resolve_profile_behavior(profile: RunProfile) -> ProfileBehavior:
    if profile == RunProfile.SHORT:
        return ProfileBehavior(
            compare_mode=CompareMode.LATEST,
            backtest_lookback_months=18,
            compare_point_count=1,
            description="fast smoke test: latest compare, 18-month backtest scope",
        )

    if profile == RunProfile.PROBLEM:
        return ProfileBehavior(
            compare_mode=CompareMode.ALL,
            runner_extra_args=("--dump-selection", "--dump-weights"),
            backtest_lookback_months=18,
            compare_point_count=1,
            description="focused debug run: all compare, 18-month backtest scope, runner selection/weight dumps",
        )

    if profile == RunProfile.MEDIUM:
        return ProfileBehavior(
            compare_mode=CompareMode.ALL,
            backtest_lookback_months=30,
            compare_point_count=3,
            description="development run: all compare, 30-month backtest scope, last 3 BT as_of points",
        )

    return ProfileBehavior(
        compare_mode=CompareMode.ALL,
        backtest_lookback_months=None,
        compare_point_count=6,
        description="deep validation run: all compare, full configured backtest scope, last 6 BT as_of points",
    )


def build_backtest_profile_args(
    behavior: ProfileBehavior,
    *,
    backtest_config_path: Path,
) -> tuple[str, ...]:
    if behavior.backtest_lookback_months is None:
        return ()

    as_of = _load_backtest_as_of(backtest_config_path)
    if as_of is None:
        return ()

    start = _subtract_months(as_of, behavior.backtest_lookback_months)
    return ("--start", start.isoformat())


def _load_backtest_as_of(config_path: Path) -> date | None:
    if not config_path.exists():
        return None

    with config_path.open("rb") as file_obj:
        payload = tomllib.load(file_obj)

    raw_as_of = payload.get("as_of")
    if raw_as_of is None and isinstance(payload.get("core"), dict):
        raw_as_of = payload["core"].get("as_of")

    if not isinstance(raw_as_of, str) or not raw_as_of.strip():
        return None

    return date.fromisoformat(raw_as_of.strip())


def _subtract_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 - months
    year = month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def build_run_context(profile: RunProfile) -> RunContext:
    ai_agents_dir = Path(r"D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents")
    aktien_oop_dir = ai_agents_dir / "aktien_oop"

    now = datetime.now()

    run_id = now.strftime("%Y%m%d_%H%M%S")
    run_label = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{profile.value}"

    output_dir = ai_agents_dir / "automation_runs" / run_label
    decisions_dir = aktien_oop_dir / "decisions" / run_id

    backtest_config_path = aktien_oop_dir / "backtest_config.toml"
    runner_config_path = aktien_oop_dir / "configs" / "runner_config.toml"

    profile_behavior = resolve_profile_behavior(profile)

    return RunContext(
        run_id=run_id,
        run_timestamp=now,
        run_label=run_label,
        profile=profile,
        compare_mode=profile_behavior.compare_mode,
        ai_agents_dir=ai_agents_dir,
        aktien_oop_dir=aktien_oop_dir,
        decisions_dir=decisions_dir,
        output_dir=output_dir,
        backtest_config_path=backtest_config_path,
        runner_config_path=runner_config_path,
        bps_tolerance=5.0,
        ignore_cash=True,
    )


def _step_result_to_dict(step_result: StepResult) -> dict:
    return {
        "success": step_result.success,
        "command": list(step_result.command),
        "cwd": step_result.cwd,
        "returncode": step_result.returncode,
        "duration_seconds": step_result.duration_seconds,
        "timed_out": step_result.timed_out,
        "stdout": step_result.stdout,
        "stderr": step_result.stderr,
        "message": step_result.message,
    }


def build_run_manifest(
    context: RunContext,
    result: RunResult,
    *,
    strategy_profile: StrategyProfile | None = None,
    effective_backtest_config_path: Path | None = None,
    effective_runner_config_path: Path | None = None,
) -> dict:
    manifest = {
        "run_id": context.run_id,
        "run_label": context.run_label,
        "run_timestamp": context.run_timestamp.isoformat(),
        "profile": context.profile.value,
        "profile_behavior": resolve_profile_behavior(context.profile).description,
        "compare_point_count": resolve_profile_behavior(context.profile).compare_point_count,
        "compare_mode": context.compare_mode.value,
        "output_dir": str(context.output_dir),
        "decisions_dir": str(context.decisions_dir),
        "backtest_config_path": str(context.backtest_config_path),
        "runner_config_path": str(context.runner_config_path),
        "effective_backtest_config_path": str(effective_backtest_config_path or context.backtest_config_path),
        "effective_runner_config_path": str(effective_runner_config_path or context.runner_config_path),
        "success": result.success,
        "warnings": list(result.warnings),
        "backtest": _step_result_to_dict(result.backtest),
        "runner": _step_result_to_dict(result.runner),
        "compare": {
            "success": result.compare.success,
            "matched": result.compare.matched,
            "message": result.compare.message,
        },
    }
    manifest.update(_strategy_profile_manifest_fields(strategy_profile))
    return manifest


def _strategy_profile_manifest_fields(
    strategy_profile: StrategyProfile | None,
) -> dict[str, object]:
    keys = (
        "strategy_profile_name",
        "strategy_profile_label",
        "strategy_profile_file",
        "universe",
        "top_k",
        "use_sector_limits",
        "max_per_sector",
        "max_turnover_cap",
        "require_above_sma",
        "regime_below_action",
        "include_cash",
        "cash_yield_annual",
        "regime_sma_days",
        "benchmark_ticker",
    )
    if strategy_profile is None:
        return dict.fromkeys(keys)
    return strategy_profile_manifest_fields(strategy_profile)


def copy_referenced_backtest_artifacts(context: RunContext, result: RunResult) -> dict[str, str]:
    copied: dict[str, str] = {}
    text = "\n".join((result.backtest.stdout, result.backtest.stderr))
    for match in OUTPUT_PATH_RE.finditer(text):
        label = match.group("label").lower()
        raw_path = match.group("path").strip()
        source_path = Path(raw_path)
        if not source_path.is_absolute():
            source_path = context.ai_agents_dir / source_path
        if not source_path.exists() or not source_path.is_file():
            continue

        try:
            relative_path = source_path.resolve().relative_to(context.ai_agents_dir.resolve())
        except ValueError:
            relative_path = Path(source_path.name)
        target_path = context.output_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        copied[label] = str(target_path)
    return copied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=("short", "problem", "medium", "long"),
        default="short",
    )
    parser.add_argument(
        "--strategy-profile",
        help=(
            "Strategy profile name from configs/profiles, e.g. balanced_v1, "
            "or a path to a .toml profile file."
        ),
    )
    return parser.parse_args()


def load_strategy_profile_for_cli(value: str) -> StrategyProfile:
    return load_strategy_profile_arg(value)


def write_strategy_profile_config_overlays(
    context: RunContext,
    strategy_profile: StrategyProfile,
) -> tuple[Path, Path]:
    overlay_dir = context.output_dir / "config_overlays"
    backtest_overlay_path = overlay_dir / "backtest_config.toml"
    runner_overlay_path = overlay_dir / "runner_config.toml"
    write_strategy_profile_overlay(
        context.backtest_config_path,
        backtest_overlay_path,
        strategy_profile,
    )
    write_strategy_profile_overlay(
        context.runner_config_path,
        runner_overlay_path,
        strategy_profile,
    )
    return backtest_overlay_path, runner_overlay_path


def main() -> None:
    args = parse_args()
    strategy_profile = None
    if args.strategy_profile:
        try:
            strategy_profile = load_strategy_profile_for_cli(args.strategy_profile)
        except StrategyProfileError as exc:
            known = ", ".join(available_strategy_profile_names()) or "none"
            raise SystemExit(f"error: {exc}\nSupported strategy profiles: {known}") from exc

    profile = RunProfile(args.profile)
    context = build_run_context(profile)
    profile_behavior = resolve_profile_behavior(profile)
    context.output_dir.mkdir(parents=True, exist_ok=True)
    context.decisions_dir.mkdir(parents=True, exist_ok=True)
    effective_backtest_config_path = context.backtest_config_path
    effective_runner_config_path = context.runner_config_path
    if strategy_profile is not None:
        effective_backtest_config_path, effective_runner_config_path = (
            write_strategy_profile_config_overlays(context, strategy_profile)
        )
    backtest_profile_args = build_backtest_profile_args(
        profile_behavior,
        backtest_config_path=effective_backtest_config_path,
    )

    print("run_id:", context.run_id)
    print("run_label:", context.run_label)
    print("profile:", context.profile)
    print("compare_mode:", context.compare_mode)
    print("profile_behavior:", profile_behavior.description)
    print("output_dir:", context.output_dir)
    print("ai_agents_dir:", context.ai_agents_dir)
    print("aktien_oop_dir:", context.aktien_oop_dir)
    print("backtest config exists:", context.backtest_config_path.exists())
    print("runner config exists:", context.runner_config_path.exists())
    if strategy_profile is not None:
        print("strategy_profile_name:", strategy_profile.name)
        print("strategy_profile_label:", strategy_profile.label)
        print("strategy_profile_file:", strategy_profile.source_path.as_posix())
        print("effective_backtest_config:", effective_backtest_config_path)
        print("effective_runner_config:", effective_runner_config_path)
    print("decisions dir exists:", context.decisions_dir.exists())

    agent = build_bt_run_agent(context.decisions_dir)

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=(
                    sys.executable,
                    "-m",
                    "aktien_oop.backtest",
                    "--config",
                    str(effective_backtest_config_path),
                    "--decisions-dir",
                    str(context.decisions_dir),
                ) + backtest_profile_args,
                cwd=context.ai_agents_dir,
                config_path=effective_backtest_config_path,
            ),
            runner_input=RunRunnerToolInput(
                command=(
                    sys.executable,
                    "-m",
                    "aktien_oop.main",
                    "--config",
                    str(effective_runner_config_path),
                    "--decisions-dir",
                    str(context.decisions_dir),
                ) + profile_behavior.runner_extra_args,
                cwd=context.ai_agents_dir,
                config_path=effective_runner_config_path,
            ),
            compare_input=BtRunCompareInput(
                bps_tolerance=context.bps_tolerance,
                ignore_cash=context.ignore_cash,
            ),
            compare_mode=context.compare_mode,
            seed_runner_previous_from_backtest=True,
            compare_point_count=profile_behavior.compare_point_count,
        )
    )
    result = replace(
        result,
        warnings=(
            f"[INFO] Using run-specific decisions directory: {context.decisions_dir}",
            f"[INFO] Profile behavior: {profile_behavior.description}",
            *(
                (
                    f"[INFO] Strategy profile: {strategy_profile.name} "
                    f"({strategy_profile.source_path})",
                )
                if strategy_profile is not None
                else ()
            ),
            *result.warnings,
        ),
    )

    (context.output_dir / "backtest_stdout.txt").write_text(result.backtest.stdout, encoding="utf-8")
    (context.output_dir / "backtest_stderr.txt").write_text(result.backtest.stderr, encoding="utf-8")
    (context.output_dir / "runner_stdout.txt").write_text(result.runner.stdout, encoding="utf-8")
    (context.output_dir / "runner_stderr.txt").write_text(result.runner.stderr, encoding="utf-8")
    artifact_paths = copy_referenced_backtest_artifacts(context, result)
    warnings_text = "\n".join(result.warnings) if result.warnings else "None"

    summary_text = (
        f"run_id: {context.run_id}\n"
        f"profile: {context.profile.value}\n"
        f"profile_behavior: {profile_behavior.description}\n"
        f"strategy_profile_name: {strategy_profile.name if strategy_profile else 'None'}\n"
        f"strategy_profile_label: {strategy_profile.label if strategy_profile else 'None'}\n"
        f"strategy_profile_file: "
        f"{strategy_profile.source_path.as_posix() if strategy_profile else 'None'}\n"
        f"universe: {strategy_profile.universe if strategy_profile else 'None'}\n"
        f"top_k: {strategy_profile.top_k if strategy_profile else 'None'}\n"
        f"use_sector_limits: {strategy_profile.use_sector_limits if strategy_profile else 'None'}\n"
        f"max_per_sector: {strategy_profile.max_per_sector if strategy_profile else 'None'}\n"
        f"max_turnover_cap: {strategy_profile.max_turnover_cap if strategy_profile else 'None'}\n"
        f"require_above_sma: {strategy_profile.require_above_sma if strategy_profile else 'None'}\n"
        f"regime_below_action: {strategy_profile.regime_below_action if strategy_profile else 'None'}\n"
        f"include_cash: {strategy_profile.include_cash if strategy_profile else 'None'}\n"
        f"cash_yield_annual: {strategy_profile.cash_yield_annual if strategy_profile else 'None'}\n"
        f"regime_sma_days: {strategy_profile.regime_sma_days if strategy_profile else 'None'}\n"
        f"benchmark_ticker: {strategy_profile.benchmark_ticker if strategy_profile else 'None'}\n"
        f"backtest_profile_args: {' '.join(backtest_profile_args) if backtest_profile_args else 'None'}\n"
        f"compare_point_count: {profile_behavior.compare_point_count}\n"
        f"compare_mode: {context.compare_mode.value}\n"
        f"success: {result.success}\n"
        f"backtest_success: {result.backtest.success}\n"
        f"runner_success: {result.runner.success}\n"
        f"compare_success: {result.compare.success}\n"
        f"compare_matched: {result.compare.matched}\n"
        f"compare_message: {result.compare.message}\n"
        f"warnings: {warnings_text}\n"
    )
    (context.output_dir / "summary.txt").write_text(summary_text, encoding="utf-8")

    print("=== BT RUN AGENT RESULT ===")
    print(f"success: {result.success}")
    print(f"backtest_success: {result.backtest.success}")
    print(f"runner_success: {result.runner.success}")
    print(f"compare_success: {result.compare.success}")
    print(f"compare_matched: {result.compare.matched}")
    print(f"compare_message: {result.compare.message}")
    print()
    print("--- backtest stdout ---")
    print(result.backtest.stdout)
    print("--- backtest stderr ---")
    print(result.backtest.stderr)
    print()
    print("--- runner stdout ---")
    print(result.runner.stdout)
    print("--- runner stderr ---")
    print(result.runner.stderr)

    manifest = build_run_manifest(
        context,
        result,
        strategy_profile=strategy_profile,
        effective_backtest_config_path=effective_backtest_config_path,
        effective_runner_config_path=effective_runner_config_path,
    )
    manifest["artifacts"] = artifact_paths
    (context.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

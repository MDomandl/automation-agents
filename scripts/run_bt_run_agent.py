from __future__ import annotations

import argparse
import calendar
import json
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


def build_run_manifest(context: RunContext, result: RunResult) -> dict:
    return {
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

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=("short", "problem", "medium", "long"),
        default="short",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    profile = RunProfile(args.profile)
    context = build_run_context(profile)
    profile_behavior = resolve_profile_behavior(profile)
    backtest_profile_args = build_backtest_profile_args(
        profile_behavior,
        backtest_config_path=context.backtest_config_path,
    )
    context.output_dir.mkdir(parents=True, exist_ok=True)
    context.decisions_dir.mkdir(parents=True, exist_ok=True)

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
                    str(context.backtest_config_path),
                    "--decisions-dir",
                    str(context.decisions_dir),
                ) + backtest_profile_args,
                cwd=context.ai_agents_dir,
                config_path=context.backtest_config_path,
            ),
            runner_input=RunRunnerToolInput(
                command=(
                    sys.executable,
                    "-m",
                    "aktien_oop.main",
                    "--config",
                    str(context.runner_config_path),
                    "--decisions-dir",
                    str(context.decisions_dir),
                ) + profile_behavior.runner_extra_args,
                cwd=context.ai_agents_dir,
                config_path=context.runner_config_path,
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
            *result.warnings,
        ),
    )

    (context.output_dir / "backtest_stdout.txt").write_text(result.backtest.stdout, encoding="utf-8")
    (context.output_dir / "backtest_stderr.txt").write_text(result.backtest.stderr, encoding="utf-8")
    (context.output_dir / "runner_stdout.txt").write_text(result.runner.stdout, encoding="utf-8")
    (context.output_dir / "runner_stderr.txt").write_text(result.runner.stderr, encoding="utf-8")
    warnings_text = "\n".join(result.warnings) if result.warnings else "None"

    summary_text = (
        f"run_id: {context.run_id}\n"
        f"profile: {context.profile.value}\n"
        f"profile_behavior: {profile_behavior.description}\n"
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

    manifest = build_run_manifest(context, result)
    (context.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

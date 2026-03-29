from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.agents.bt_run_agent import BtRunAgentInput, BtRunCompareInput
from app.bootstrap.bt_run_container import build_bt_run_agent
from app.domain.bt_run.run_context import RunContext, CompareMode, RunProfile
from app.domain.bt_run.run_result import RunResult
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput


def build_run_context(profile: RunProfile) -> RunContext:
    ai_agents_dir = Path(r"D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents")
    aktien_oop_dir = ai_agents_dir / "aktien_oop"
    decisions_dir = aktien_oop_dir / "decisions"

    now = datetime.now()

    run_id = now.strftime("%Y%m%d_%H%M%S")
    run_label = f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{profile.value}"

    output_dir = ai_agents_dir / "automation_runs" / run_label

    backtest_config_path = aktien_oop_dir / "backtest_config.toml"
    runner_config_path = aktien_oop_dir / "configs" / "runner_config.toml"

    compare_mode = (
        CompareMode.LATEST
        if profile == RunProfile.SHORT
        else CompareMode.ALL
    )

    return RunContext(
        run_id=run_id,
        run_timestamp=now,
        run_label=run_label,
        profile=profile,
        compare_mode=compare_mode,
        ai_agents_dir=ai_agents_dir,
        aktien_oop_dir=aktien_oop_dir,
        decisions_dir=decisions_dir,
        output_dir=output_dir,
        backtest_config_path=backtest_config_path,
        runner_config_path=runner_config_path,
        bps_tolerance=5.0,
        ignore_cash=True,
    )

def build_run_manifest(context: RunContext, result: RunResult) -> dict:
    return {
        "run_id": context.run_id,
        "run_label": context.run_label,
        "run_timestamp": context.run_timestamp.isoformat(),
        "profile": context.profile.value,
        "compare_mode": context.compare_mode.value,
        "output_dir": str(context.output_dir),
        "decisions_dir": str(context.decisions_dir),
        "backtest_config_path": str(context.backtest_config_path),
        "runner_config_path": str(context.runner_config_path),
        "success": result.success,
        "warnings": list(result.warnings),
        "backtest": asdict(result.backtest),
        "runner": asdict(result.runner),
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
    context.output_dir.mkdir(parents=True, exist_ok=True)

    print("run_id:", context.run_id)
    print("run_label:", context.run_label)
    print("profile:", context.profile)
    print("compare_mode:", context.compare_mode)
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
                ),
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
                ),
                cwd=context.ai_agents_dir,
                config_path=context.runner_config_path,
            ),
            compare_input=BtRunCompareInput(
                bps_tolerance=context.bps_tolerance,
                ignore_cash=context.ignore_cash,
            ),
            compare_mode=context.compare_mode,
        )
    )

    (context.output_dir / "backtest_stdout.txt").write_text(result.backtest.stdout, encoding="utf-8")
    (context.output_dir / "backtest_stderr.txt").write_text(result.backtest.stderr, encoding="utf-8")
    (context.output_dir / "runner_stdout.txt").write_text(result.runner.stdout, encoding="utf-8")
    (context.output_dir / "runner_stderr.txt").write_text(result.runner.stderr, encoding="utf-8")
    warnings_text = "\n".join(result.warnings) if result.warnings else "None"

    summary_text = (
        f"run_id: {context.run_id}\n"
        f"profile: {context.profile.value}\n"
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

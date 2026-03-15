from __future__ import annotations

import sys
from pathlib import Path

from app.agents.bt_run_agent import BtRunAgentInput
from app.bootstrap.bt_run_container import build_bt_run_agent
from app.tools.compare.compare_latest_runs_tool import CompareLatestRunsToolInput
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput


def main() -> None:
    ai_agents_dir = Path(r"D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents")
    aktien_oop_dir = ai_agents_dir / "aktien_oop"
    decisions_dir = aktien_oop_dir / "decisions"

    backtest_config = aktien_oop_dir /"backtest_config.toml"
    runner_config = aktien_oop_dir / "configs" / "runner_config.toml"

    print("ai_agents_dir:", ai_agents_dir)
    print("aktien_oop_dir:", aktien_oop_dir)
    print("backtest config exists:", backtest_config.exists())
    print("runner config exists:", runner_config.exists())

    agent = build_bt_run_agent(decisions_dir)

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=(
                    sys.executable,
                    "-m",
                    "aktien_oop.backtest",
                    "--config",
                    str(backtest_config),
                ),
                cwd=ai_agents_dir,
            ),
            runner_input=RunRunnerToolInput(
                command=(
                    sys.executable,
                    "-m",
                    "aktien_oop.main",
                    "--config",
                    str(runner_config),
                ),
                cwd=ai_agents_dir,
            ),
            compare_input=CompareLatestRunsToolInput(
                bps_tolerance=5.0,
                ignore_cash=True,
            ),
            compare_mode="all", #latest
        )
    )

    print("=== BT RUN AGENT RESULT ===")
    print(f"success: {result.success}")
    print(f"backtest_success: {result.backtest_success}")
    print(f"runner_success: {result.runner_success}")
    print(f"compare_success: {result.compare_success}")
    print(f"compare_matched: {result.compare_matched}")
    print(f"compare_message: {result.compare_message}")
    print()
    print("--- backtest stdout ---")
    print(result.backtest_stdout)
    print("--- backtest stderr ---")
    print(result.backtest_stderr)
    print()
    print("--- runner stdout ---")
    print(result.runner_stdout)
    print("--- runner stderr ---")
    print(result.runner_stderr)


if __name__ == "__main__":
    main()
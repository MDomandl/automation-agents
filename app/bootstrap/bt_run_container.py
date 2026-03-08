from app.infrastructure.process.subprocess_runner import SubprocessRunner
from app.tools.bt_run.run_backtest_tool import RunBacktestTool
from app.tools.bt_run.run_runner_tool import RunRunnerTool
from app.tools.bt_run.compare_latest_runs_tool import CompareLatestRunsTool
from app.tools.bt_run.write_bt_run_report_tool import WriteBtRunReportTool
from app.agents.bt_run_agent import BtRunAgent


def build_bt_run_agent() -> BtRunAgent:

    process_runner = SubprocessRunner()

    run_backtest = RunBacktestTool(process_runner)
    run_runner = RunRunnerTool(process_runner)

    compare_runs = CompareLatestRunsTool()
    write_report = WriteBtRunReportTool()

    return BtRunAgent(
        run_backtest,
        run_runner,
        compare_runs,
        write_report,
    )
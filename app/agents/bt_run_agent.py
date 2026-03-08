from app.tools.bt_run.run_backtest_tool import RunBacktestTool
from app.tools.bt_run.run_runner_tool import RunRunnerTool
from app.tools.bt_run.compare_latest_runs_tool import CompareLatestRunsTool
from app.tools.bt_run.write_bt_run_report_tool import WriteBtRunReportTool
from app.common.result import Result


class BtRunAgent:

    def __init__(
        self,
        run_backtest: RunBacktestTool,
        run_runner: RunRunnerTool,
        compare_runs: CompareLatestRunsTool,
        write_report: WriteBtRunReportTool,
    ):
        self.run_backtest = run_backtest
        self.run_runner = run_runner
        self.compare_runs = compare_runs
        self.write_report = write_report

    def execute(self) -> Result[str]:

        bt_result = self.run_backtest.execute()
        if not bt_result.is_ok:
            return Result.fail("Backtest failed")

        runner_result = self.run_runner.execute()
        if not runner_result.is_ok:
            return Result.fail("Runner failed")

        comparison = self.compare_runs.execute()
        if not comparison.is_ok:
            return Result.fail("Comparison failed")

        report = self.write_report.execute(comparison.value)
        if not report.is_ok:
            return Result.fail("Report generation failed")

        return Result.ok(report.value)
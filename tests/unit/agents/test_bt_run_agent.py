from app.agents.bt_run_agent import BtRunAgent, BtRunAgentInput
from app.application.bt_run.dto import CompareLatestRunsResponse
from app.domain.bt_run.models import ComparisonSummary
from app.infrastructure.process.subprocess_runner import ProcessResult
from app.tools.compare.compare_latest_runs_tool import CompareLatestRunsToolInput
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput


class FakeRunBacktestTool:
    def execute(self, tool_input):
        return type(
            "BacktestResult",
            (),
            {
                "success": True,
                "process_result": ProcessResult(
                    command=("python", "bt.py"),
                    returncode=0,
                    stdout="bt ok",
                    stderr="",
                ),
            },
        )()


class FakeRunRunnerTool:
    def execute(self, tool_input):
        return type(
            "RunnerResult",
            (),
            {
                "success": True,
                "process_result": ProcessResult(
                    command=("python", "runner.py"),
                    returncode=0,
                    stdout="run ok",
                    stderr="",
                ),
            },
        )()


class FakeCompareLatestRunsTool:
    def execute(self, tool_input):
        return CompareLatestRunsResponse(
            success=True,
            summary=ComparisonSummary(
                as_of_bt="2025-03-31",
                as_of_run="2025-03-31",
                matched=True,
            ),
            message=None,
        )


def test_bt_run_agent_executes_full_flow_successfully() -> None:
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py")),
            runner_input=RunRunnerToolInput(command=("python", "runner.py")),
            compare_input=CompareLatestRunsToolInput(),
        )
    )

    assert result.success is True
    assert result.backtest_success is True
    assert result.runner_success is True
    assert result.compare_success is True
    assert result.compare_matched is True
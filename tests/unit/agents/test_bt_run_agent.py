from pathlib import Path

from app.agents.bt_run_agent import BtRunAgent, BtRunAgentInput, BtRunCompareInput
from app.application.bt_run.dto import CompareLatestRunsResponse
from app.domain.bt_run.models import ComparisonSummary
from app.infrastructure.process.subprocess_runner import ProcessResult
from app.tools.compare.compare_config_tool import CompareConfigToolResult
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput


class FakeProcessToolResult:
    def __init__(self, command: tuple[str, str], stdout: str):
        self.success = True
        self.process_result = ProcessResult(
            command=command,
            returncode=0,
            stdout=stdout,
            stderr="",
        )


class FakeRunBacktestTool:
    def execute(self, tool_input):
        return FakeProcessToolResult(("python", "bt.py"), "bt ok")


class FakeRunRunnerTool:
    def execute(self, tool_input):
        return FakeProcessToolResult(("python", "runner.py"), "run ok")


class FakeCompareConfigTool:
    def execute(self, tool_input):
        return CompareConfigToolResult(
            differences=tuple(),
            success=True,
            matched=True,
            message="Configs match",
            formatted_differences=tuple(),
            has_critical_differences=False,
        )


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


class FakeCompareAllRunsTool:
    def execute(self, tool_input):
        raise AssertionError("compare_all_runs_tool should not be called in latest mode")

def test_bt_run_agent_executes_full_flow_successfully() -> None:
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=FakeCompareConfigTool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py"), config_path=Path("bt.yaml")),
            runner_input=RunRunnerToolInput(command=("python", "runner.py"), config_path=Path("runner.yaml")),
            compare_input=BtRunCompareInput(),
        )
    )

    assert result.success is True
    assert result.backtest.success is True
    assert result.runner.success is True
    assert result.compare.success is True
    assert result.compare.matched is True

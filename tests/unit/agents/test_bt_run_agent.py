from pathlib import Path

from app.agents.bt_run_agent import BtRunAgent, BtRunAgentInput, BtRunCompareInput
from app.application.bt_run.dto import CompareLatestRunsResponse
from app.domain.bt_run.models import ComparisonSummary
from app.domain.bt_run.run_context import CompareMode
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
            cwd="C:/work",
            duration_seconds=1.25,
            timed_out=False,
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
    def __init__(self):
        self.called = False

    def execute(self, tool_input):
        self.called = True
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
    def __init__(self):
        self.called = False

    def execute(self, tool_input):
        self.called = True
        raise AssertionError("compare_all_runs_tool should not be called in latest mode")


class FakeCompareConfigToolWithDrift:
    def execute(self, tool_input):
        return CompareConfigToolResult(
            success=True,
            matched=False,
            differences=(),
            message="2 differences found",
            formatted_differences=(
                "- [CRITICAL] period: BT='800d' | RUN='400d'",
                "- [WARNING] include_cash: BT=True | RUN=False",
            ),
            has_critical_differences=True,
        )


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
    assert result.backtest.command == ("python", "bt.py")
    assert result.backtest.cwd == "C:/work"
    assert result.backtest.returncode == 0
    assert result.backtest.duration_seconds == 1.25
    assert result.backtest.timed_out is False


def test_bt_run_agent_uses_compare_latest_mode() -> None:
    latest_tool = FakeCompareLatestRunsTool()
    all_tool = FakeCompareAllRunsTool()

    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=latest_tool,
        compare_all_runs_tool=all_tool,
        compare_config_tool=FakeCompareConfigTool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py"), config_path=Path("bt.yaml")),
            runner_input=RunRunnerToolInput(command=("python", "runner.py"), config_path=Path("runner.toml")),
            compare_input=BtRunCompareInput(),
            compare_mode=CompareMode.LATEST,
        )
    )

    assert result.success is True
    assert result.compare.success is True
    assert result.compare.matched is True
    assert latest_tool.called is True
    assert all_tool.called is False



def test_bt_run_agent_adds_config_drift_warnings_to_run_result(capsys) -> None:
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=FakeCompareConfigToolWithDrift(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=("python", "bt.py"),
                config_path=Path("bt.toml"),
            ),
            runner_input=RunRunnerToolInput(
                command=("python", "runner.py"),
                config_path=Path("runner.toml"),
            ),
            compare_input=BtRunCompareInput(),
            compare_mode=CompareMode.LATEST,
        )
    )

    assert len(result.warnings) == 3
    assert result.warnings[0] == "[WARN] Config drift detected: 2 differences found"
    assert "period" in result.warnings[1]
    assert "include_cash" in result.warnings[2]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

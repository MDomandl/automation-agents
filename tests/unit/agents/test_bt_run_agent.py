from pathlib import Path

from app.agents.bt_run_agent import BtRunAgent, BtRunAgentInput, BtRunCompareInput
from app.application.bt_run.use_cases import CompareConfigUseCase
from app.application.bt_run.dto import CompareAllRunsResponse, CompareLatestRunsResponse
from app.domain.bt_run.config_compare import ConfigDifference, ConfigDiffSeverity
from app.domain.bt_run.models import ComparisonSummary
from app.domain.bt_run.run_context import CompareMode
from app.infrastructure.process.subprocess_runner import ProcessResult
from app.infrastructure.storage.config_loader import ConfigLoader
from app.tools.compare.compare_config_tool import CompareConfigToolResult
from app.tools.compare.compare_config_tool import CompareConfigTool
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerToolInput


class FakeProcessToolResult:
    def __init__(self, command: tuple[str, ...], stdout: str):
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
    def __init__(self):
        self.last_input = None
        self.inputs = []

    def execute(self, tool_input):
        self.last_input = tool_input
        self.inputs.append(tool_input)
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


class FakeCompareAllRunsToolNoPairs:
    def execute(self, tool_input):
        return CompareAllRunsResponse(
            success=False,
            message="No BT/RUN pairs found",
        )


class FakeCompareAllRunsToolSuccess:
    def execute(self, tool_input):
        return CompareAllRunsResponse(
            success=True,
            summaries=[
                ComparisonSummary(
                    as_of_bt="2025-09-30",
                    as_of_run="2025-09-30",
                    matched=True,
                ),
                ComparisonSummary(
                    as_of_bt="2025-10-08",
                    as_of_run="2025-10-08",
                    matched=True,
                ),
            ],
        )


class FakeCompareConfigToolWithDrift:
    def execute(self, tool_input):
        return CompareConfigToolResult(
            success=True,
            matched=False,
            differences=(
                ConfigDifference(
                    key="period",
                    bt_value="800d",
                    run_value="400d",
                    severity=ConfigDiffSeverity.CRITICAL,
                ),
                ConfigDifference(
                    key="include_cash",
                    bt_value=True,
                    run_value=False,
                    severity=ConfigDiffSeverity.WARNING,
                ),
            ),
            message="2 differences found",
            formatted_differences=(
                "- [CRITICAL] period: BT='800d' | RUN='400d'",
                "- [WARNING] include_cash: BT=True | RUN=False",
            ),
            has_critical_differences=True,
        )


def write_config(path: Path, *, as_of: str | None = None, period: str | None = None) -> None:
    lines: list[str] = []

    if as_of is not None:
        lines.append(f'as_of = "{as_of}"')
    if period is not None:
        lines.append(f'period = "{period}"')

    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def build_real_compare_config_tool() -> CompareConfigTool:
    return CompareConfigTool(CompareConfigUseCase(ConfigLoader()))


def test_bt_run_agent_executes_full_flow_successfully() -> None:
    fake_run_runner_tool = FakeRunRunnerTool()
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=fake_run_runner_tool,
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
    assert fake_run_runner_tool.last_input.as_of_override is None


def test_bt_run_agent_uses_compare_latest_mode() -> None:
    latest_tool = FakeCompareLatestRunsTool()
    all_tool = FakeCompareAllRunsTool()
    fake_run_runner_tool = FakeRunRunnerTool()

    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=fake_run_runner_tool,
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
    assert fake_run_runner_tool.last_input.as_of_override is None


def test_bt_run_agent_all_compare_does_not_match_when_no_pairs_exist() -> None:
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsToolNoPairs(),
        compare_config_tool=FakeCompareConfigTool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py"), config_path=Path("bt.yaml")),
            runner_input=RunRunnerToolInput(command=("python", "runner.py"), config_path=Path("runner.toml")),
            compare_input=BtRunCompareInput(),
            compare_mode=CompareMode.ALL,
        )
    )

    assert result.success is False
    assert result.compare.success is False
    assert result.compare.matched is False
    assert result.compare.message == "No BT/RUN pairs found"


def test_bt_run_agent_runs_multiple_runner_points_from_current_bt_artifacts(tmp_path: Path) -> None:
    decisions_dir = tmp_path / "decisions"
    bt_save_dir = tmp_path / "bt_out"
    runner_save_dir = tmp_path / "runner_out"
    decisions_dir.mkdir()
    bt_save_dir.mkdir()
    runner_save_dir.mkdir()
    for as_of in ("2025-08-29", "2025-09-30", "2025-10-08"):
        (decisions_dir / f"BT_test_{as_of}.json").write_text(
            f'{{"kind": "BT", "as_of": "{as_of}", "new_weights": {{"AAPL": 1.0}}}}',
            encoding="utf-8",
        )
    (bt_save_dir / "bt_monthly_12x3_positions.csv").write_text(
        "\n".join(
            [
                "as_of,ticker,allocation_pct",
                "2025-08-29,MSFT,11.11",
                "2025-09-30,AAPL,11.11",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    bt_config_path.write_text(
        "\n".join(
            [
                f'save_dir = "{bt_save_dir.as_posix()}"',
                "top_k = 12",
                "buffer_k = 3",
                "[rebalance]",
                'frequency = "monthly"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner_config_path.write_text(
        f'save_dir = "{runner_save_dir.as_posix()}"\n',
        encoding="utf-8",
    )

    fake_run_runner_tool = FakeRunRunnerTool()
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=fake_run_runner_tool,
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsToolSuccess(),
        compare_config_tool=FakeCompareConfigTool(),
        decisions_dir=decisions_dir,
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py"), config_path=bt_config_path),
            runner_input=RunRunnerToolInput(command=("python", "runner.py"), config_path=runner_config_path),
            compare_input=BtRunCompareInput(),
            compare_mode=CompareMode.ALL,
            compare_point_count=2,
            seed_runner_previous_from_backtest=True,
        )
    )

    assert [tool_input.as_of_override for tool_input in fake_run_runner_tool.inputs] == [
        "2025-09-30",
        "2025-10-08",
    ]
    assert result.runner.message == "Runner executed 2 compare point(s)"
    assert result.compare.matched is True
    assert sum("seeded from backtest positions" in warning for warning in result.warnings) == 1
    assert "[INFO] Runner previous-state seed skipped for subsequent compare points" in result.warnings



def test_bt_run_agent_adds_config_drift_warnings_to_run_result(capsys) -> None:
    fake_run_runner_tool = FakeRunRunnerTool()
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=fake_run_runner_tool,
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

    assert len(result.warnings) == 4
    assert (
        result.warnings[0]
        == "[WARN] Config drift detected: 2 differences found (1 critical, 1 warning, 0 info)"
    )
    assert "period" in result.warnings[1]
    assert "include_cash" in result.warnings[2]
    assert result.warnings[3] == "[INFO] Runner compare points: count=1, as_of=config"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert fake_run_runner_tool.last_input.as_of_override is None


def test_bt_run_agent_auto_aligns_runner_as_of_when_runner_config_is_missing(tmp_path: Path) -> None:
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    write_config(bt_config_path, as_of="2025-03-31")
    write_config(runner_config_path)

    fake_run_runner_tool = FakeRunRunnerTool()
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=fake_run_runner_tool,
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=build_real_compare_config_tool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=("python", "bt.py"),
                config_path=bt_config_path,
            ),
            runner_input=RunRunnerToolInput(
                command=("python", "runner.py"),
                config_path=runner_config_path,
            ),
            compare_input=BtRunCompareInput(),
        )
    )

    assert fake_run_runner_tool.last_input.as_of_override == "2025-03-31"
    assert result.warnings == (
        "[INFO] Runner as_of auto-aligned to backtest as_of: 2025-03-31",
        "[INFO] Runner compare points: count=1, as_of=2025-03-31",
    )


def test_bt_run_agent_prefers_explicit_runner_as_of(tmp_path: Path) -> None:
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    write_config(bt_config_path, as_of="2025-03-31")
    write_config(runner_config_path, as_of="2025-04-01")

    fake_run_runner_tool = FakeRunRunnerTool()
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=fake_run_runner_tool,
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=build_real_compare_config_tool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=("python", "bt.py"),
                config_path=bt_config_path,
            ),
            runner_input=RunRunnerToolInput(
                command=("python", "runner.py"),
                config_path=runner_config_path,
            ),
            compare_input=BtRunCompareInput(),
        )
    )

    assert fake_run_runner_tool.last_input.as_of_override is None
    assert result.warnings[0].startswith("[WARN] Config drift detected:")
    assert "as_of" in result.warnings[1]


def test_bt_run_agent_still_reports_config_drift_when_both_as_of_values_differ(tmp_path: Path) -> None:
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    write_config(bt_config_path, as_of="2025-03-31", period="800d")
    write_config(runner_config_path, as_of="2025-04-01", period="800d")

    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=build_real_compare_config_tool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(
                command=("python", "bt.py"),
                config_path=bt_config_path,
            ),
            runner_input=RunRunnerToolInput(
                command=("python", "runner.py"),
                config_path=runner_config_path,
            ),
            compare_input=BtRunCompareInput(),
        )
    )

    assert result.warnings[0] == "[WARN] Config drift detected: 1 differences found (1 critical, 0 warning, 0 info)"
    assert result.warnings[1] == "- [CRITICAL] as_of: BT='2025-03-31' | RUN='2025-04-01'"


def test_bt_run_agent_reports_matching_universe(tmp_path: Path) -> None:
    universe_path = tmp_path / "tickers.txt"
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    universe_path.write_text("MSFT\nAAPL\n", encoding="utf-8")
    bt_config_path.write_text(f'tickers_file = "{universe_path.as_posix()}"\n', encoding="utf-8")
    runner_config_path.write_text(f'tickers_file = "{universe_path.as_posix()}"\n', encoding="utf-8")

    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=build_real_compare_config_tool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py"), config_path=bt_config_path),
            runner_input=RunRunnerToolInput(command=("python", "runner.py"), config_path=runner_config_path),
            compare_input=BtRunCompareInput(),
        )
    )

    assert result.warnings[0].startswith("[INFO] Universe match: count=2, hash=")


def test_bt_run_agent_warns_on_universe_drift(tmp_path: Path) -> None:
    bt_universe_path = tmp_path / "bt_tickers.txt"
    runner_universe_path = tmp_path / "runner_tickers.txt"
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    bt_universe_path.write_text("AAPL\nMSFT\n", encoding="utf-8")
    runner_universe_path.write_text("AAPL\nNVDA\n", encoding="utf-8")
    bt_config_path.write_text(f'tickers_file = "{bt_universe_path.as_posix()}"\n', encoding="utf-8")
    runner_config_path.write_text(f'tickers_file = "{runner_universe_path.as_posix()}"\n', encoding="utf-8")

    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=FakeRunRunnerTool(),
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=build_real_compare_config_tool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py"), config_path=bt_config_path),
            runner_input=RunRunnerToolInput(command=("python", "runner.py"), config_path=runner_config_path),
            compare_input=BtRunCompareInput(),
        )
    )

    assert result.warnings[0].startswith("[WARN] Universe drift detected: BT count=2, hash=")
    assert "RUN count=2, hash=" in result.warnings[0]


def test_bt_run_agent_seeds_runner_previous_snapshot_from_backtest_positions(tmp_path: Path) -> None:
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    bt_save_dir = tmp_path / "bt_out"
    runner_save_dir = tmp_path / "runner_out"
    bt_save_dir.mkdir()
    runner_save_dir.mkdir()
    write_config(bt_config_path, as_of="2025-10-08")
    bt_config_path.write_text(
        '\n'.join(
            [
                'as_of = "2025-10-08"',
                f'save_dir = "{bt_save_dir.as_posix()}"',
                'top_k = 12',
                'buffer_k = 3',
                '[rebalance]',
                'frequency = "monthly"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner_config_path.write_text(
        '\n'.join(
            [
                f'save_dir = "{runner_save_dir.as_posix()}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (bt_save_dir / "bt_monthly_12x3_positions.csv").write_text(
        "\n".join(
            [
                "# run_id=unit-test",
                "as_of,ticker,allocation_pct,sector",
                "2025-09-30,AVGO,11.11,Information Technology",
                "2025-09-30,STX,11.11,Information Technology",
                "2025-10-08,GLW,11.11,Information Technology",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    fake_run_runner_tool = FakeRunRunnerTool()
    agent = BtRunAgent(
        run_backtest_tool=FakeRunBacktestTool(),
        run_runner_tool=fake_run_runner_tool,
        compare_latest_runs_tool=FakeCompareLatestRunsTool(),
        compare_all_runs_tool=FakeCompareAllRunsTool(),
        compare_config_tool=build_real_compare_config_tool(),
    )

    result = agent.execute(
        BtRunAgentInput(
            backtest_input=RunBacktestToolInput(command=("python", "bt.py"), config_path=bt_config_path),
            runner_input=RunRunnerToolInput(command=("python", "runner.py"), config_path=runner_config_path),
            compare_input=BtRunCompareInput(),
            seed_runner_previous_from_backtest=True,
        )
    )

    seeded = (runner_save_dir / "portfolio_positions.csv").read_text(encoding="utf-8")
    assert "2025-09-30,AVGO" in seeded
    assert "2025-09-30,STX" in seeded
    assert "2025-10-08,GLW" not in seeded
    assert (
        "[INFO] Runner previous-state seeded from backtest positions: prev_as_of=2025-09-30, rows=2"
        in result.warnings
    )
    assert fake_run_runner_tool.last_input.as_of_override == "2025-10-08"


def test_bt_run_agent_seed_replaces_duplicate_runner_snapshot_rows(tmp_path: Path) -> None:
    bt_positions_path = tmp_path / "bt_positions.csv"
    runner_positions_path = tmp_path / "portfolio_positions.csv"
    bt_positions_path.write_text(
        "\n".join(
            [
                "as_of,ticker,allocation_pct",
                "2025-09-30,AVGO,11.11",
                "2025-09-30,STX,11.11",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner_positions_path.write_text(
        "\n".join(
            [
                "as_of,ticker,allocation_pct",
                "2025-09-30,AVGO,99.99",
                "2025-10-08,GLW,11.11",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    BtRunAgent._seed_runner_positions_from_backtest_positions(
        bt_positions_path=bt_positions_path,
        runner_positions_path=runner_positions_path,
        runner_as_of="2025-10-08",
    )

    persisted = runner_positions_path.read_text(encoding="utf-8")
    assert persisted.count("2025-09-30,AVGO") == 1
    assert "2025-09-30,AVGO,11.11" in persisted
    assert "2025-10-08,GLW,11.11" in persisted


def test_bt_run_agent_seed_skips_when_no_backtest_previous_snapshot_exists(tmp_path: Path) -> None:
    bt_positions_path = tmp_path / "bt_positions.csv"
    runner_positions_path = tmp_path / "portfolio_positions.csv"
    bt_positions_path.write_text(
        "\n".join(
            [
                "as_of,ticker,allocation_pct",
                "2025-10-08,GLW,11.11",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = BtRunAgent._seed_runner_positions_from_backtest_positions(
        bt_positions_path=bt_positions_path,
        runner_positions_path=runner_positions_path,
        runner_as_of="2025-10-08",
    )

    assert result.seeded is False
    assert result.message == "[INFO] Runner previous-state seed skipped: no BT snapshot before 2025-10-08"
    assert not runner_positions_path.exists()

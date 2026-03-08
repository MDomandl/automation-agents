from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


# =========================================================
# Common
# =========================================================

@dataclass(frozen=True)
class Result(Generic[T]):
    value: T | None = None
    error: str | None = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @staticmethod
    def ok(value: T) -> "Result[T]":
        return Result(value=value)

    @staticmethod
    def fail(error: str) -> "Result[T]":
        return Result(error=error)


# =========================================================
# Domain
# =========================================================

@dataclass(frozen=True)
class RunArtifacts:
    bt_names: list[str]
    run_names: list[str]
    bt_weights: dict[str, float]
    run_weights: dict[str, float]


@dataclass(frozen=True)
class ComparisonSummary:
    differing_names: int
    differing_weights: int
    note: str


def build_note(differing_names: int, differing_weights: int) -> str:
    if differing_names == 0 and differing_weights == 0:
        return "BT und RUN sind im Toleranzbereich."
    if differing_names > 0 and differing_weights == 0:
        return "Namensabweichungen gefunden."
    if differing_names == 0 and differing_weights > 0:
        return "Gewichtsabweichungen gefunden."
    return "Namens- und Gewichtsabweichungen gefunden."


def compare_artifacts(artifacts: RunArtifacts, tolerance: float = 0.01) -> ComparisonSummary:
    bt_name_set = set(artifacts.bt_names)
    run_name_set = set(artifacts.run_names)

    differing_names = len(bt_name_set.symmetric_difference(run_name_set))

    all_names = bt_name_set.union(run_name_set)
    differing_weights = 0

    for name in all_names:
        bt_weight = artifacts.bt_weights.get(name, 0.0)
        run_weight = artifacts.run_weights.get(name, 0.0)
        if abs(bt_weight - run_weight) > tolerance:
            differing_weights += 1

    note = build_note(differing_names, differing_weights)
    return ComparisonSummary(
        differing_names=differing_names,
        differing_weights=differing_weights,
        note=note,
    )


# =========================================================
# Tools
# =========================================================

class RunBacktestTool:
    def execute(self) -> Result[tuple[list[str], dict[str, float]]]:
        # Hier später echter Backtest-Aufruf
        names = ["AAPL", "MSFT", "NVDA"]
        weights = {"AAPL": 0.30, "MSFT": 0.35, "NVDA": 0.35}
        return Result.ok((names, weights))


class RunRunnerTool:
    def execute(self) -> Result[tuple[list[str], dict[str, float]]]:
        # Hier später echter Runner-Aufruf
        names = ["AAPL", "MSFT", "AMZN"]
        weights = {"AAPL": 0.31, "MSFT": 0.34, "AMZN": 0.35}
        return Result.ok((names, weights))


class CompareArtifactsTool:
    def execute(self, artifacts: RunArtifacts) -> Result[ComparisonSummary]:
        summary = compare_artifacts(artifacts)
        return Result.ok(summary)


class WriteReportTool:
    def execute(self, summary: ComparisonSummary) -> Result[str]:
        report = (
            "BT/RUN REPORT\n"
            "=============\n"
            f"Differing names   : {summary.differing_names}\n"
            f"Differing weights : {summary.differing_weights}\n"
            f"Note              : {summary.note}\n"
        )
        return Result.ok(report)


# =========================================================
# Agents
# =========================================================

class RunAgent:
    def __init__(
        self,
        backtest_tool: RunBacktestTool,
        runner_tool: RunRunnerTool,
    ) -> None:
        self._backtest_tool = backtest_tool
        self._runner_tool = runner_tool

    def execute(self) -> Result[RunArtifacts]:
        bt_result = self._backtest_tool.execute()
        if not bt_result.is_ok:
            return Result.fail(bt_result.error or "Backtest fehlgeschlagen")

        runner_result = self._runner_tool.execute()
        if not runner_result.is_ok:
            return Result.fail(runner_result.error or "Runner fehlgeschlagen")

        bt_names, bt_weights = bt_result.value
        run_names, run_weights = runner_result.value

        artifacts = RunArtifacts(
            bt_names=bt_names,
            run_names=run_names,
            bt_weights=bt_weights,
            run_weights=run_weights,
        )
        return Result.ok(artifacts)


class CompareAgent:
    def __init__(
        self,
        compare_tool: CompareArtifactsTool,
        report_tool: WriteReportTool,
    ) -> None:
        self._compare_tool = compare_tool
        self._report_tool = report_tool

    def execute(self, artifacts: RunArtifacts) -> Result[str]:
        compare_result = self._compare_tool.execute(artifacts)
        if not compare_result.is_ok:
            return Result.fail(compare_result.error or "Vergleich fehlgeschlagen")

        report_result = self._report_tool.execute(compare_result.value)
        if not report_result.is_ok:
            return Result.fail(report_result.error or "Report fehlgeschlagen")

        return Result.ok(report_result.value)


# =========================================================
# Workflow / Coordinator
# =========================================================

class BtRunWorkflow:
    def __init__(
        self,
        run_agent: RunAgent,
        compare_agent: CompareAgent,
    ) -> None:
        self._run_agent = run_agent
        self._compare_agent = compare_agent

    def execute(self) -> Result[str]:
        run_result = self._run_agent.execute()
        if not run_result.is_ok:
            return Result.fail(run_result.error or "RunAgent fehlgeschlagen")

        compare_result = self._compare_agent.execute(run_result.value)
        if not compare_result.is_ok:
            return Result.fail(compare_result.error or "CompareAgent fehlgeschlagen")

        return Result.ok(compare_result.value)


# =========================================================
# Bootstrap
# =========================================================

def build_workflow() -> BtRunWorkflow:
    run_agent = RunAgent(
        backtest_tool=RunBacktestTool(),
        runner_tool=RunRunnerTool(),
    )

    compare_agent = CompareAgent(
        compare_tool=CompareArtifactsTool(),
        report_tool=WriteReportTool(),
    )

    return BtRunWorkflow(
        run_agent=run_agent,
        compare_agent=compare_agent,
    )


# =========================================================
# Main
# =========================================================

def main() -> None:
    workflow = build_workflow()
    result = workflow.execute()

    if result.is_ok:
        print(result.value)
    else:
        print("FEHLER:", result.error)


if __name__ == "__main__":
    main()
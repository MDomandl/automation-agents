from dataclasses import dataclass
from pathlib import Path

from app.application.bt_run.use_cases import CompareConfigUseCase
from app.domain.bt_run.config_compare import ConfigDifference, ConfigDiffSeverity


@dataclass(frozen=True, slots=True)
class CompareConfigToolInput:
    bt_config_path: Path
    runner_config_path: Path


@dataclass(frozen=True, slots=True)
class CompareConfigToolResult:
    success: bool
    matched: bool
    differences: tuple[ConfigDifference, ...]
    message: str
    formatted_differences: tuple[str, ...] = ()
    has_critical_differences: bool = False


class CompareConfigTool:

    def __init__(self, use_case: CompareConfigUseCase):
        self._use_case = use_case

    def execute(self, tool_input: CompareConfigToolInput) -> CompareConfigToolResult:

        result = self._use_case.execute(
            tool_input.bt_config_path,
            tool_input.runner_config_path,
        )

        if result.matched:
            return CompareConfigToolResult(
                success=True,
                matched=True,
                differences=(),
                message="Configs match",
                formatted_differences=(),
                has_critical_differences=False,
            )

        formatted = tuple(
            self._format_difference(diff)
            for diff in result.differences
        )
        has_critical_differences = any(
            diff.severity == ConfigDiffSeverity.CRITICAL
            for diff in result.differences
        )

        message = (
            f"{len(result.differences)} differences found "
            f"({result.critical_count} critical, "
            f"{result.warning_count} warning, "
            f"{result.info_count} info)"
        )

        return CompareConfigToolResult(
            success=True,
            matched=False,
            differences=result.differences,
            message=message,
            formatted_differences=formatted,
            has_critical_differences=has_critical_differences,
        )

    @staticmethod
    def _format_difference(diff: ConfigDifference) -> str:
        return (
            f"- [{diff.severity.value.upper()}] {diff.key}: "
            f"BT={diff.bt_value!r} | RUN={diff.run_value!r}"
        )

from dataclasses import dataclass
from pathlib import Path

from app.application.bt_run.use_cases import CompareConfigUseCase


@dataclass(frozen=True, slots=True)
class CompareConfigToolInput:
    bt_config_path: Path
    runner_config_path: Path


@dataclass(frozen=True, slots=True)
class CompareConfigToolResult:
    success: bool
    matched: bool
    differences: tuple
    message: str


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
            )

        return CompareConfigToolResult(
            success=True,
            matched=False,
            differences=result.differences,
            message=f"{len(result.differences)} differences found",
        )
from typing import Protocol, Sequence

from app.common.result import Result


class ProcessRunner(Protocol):
    def run(self, command: Sequence[str], cwd: str | None = None) -> Result[None]:
        ...

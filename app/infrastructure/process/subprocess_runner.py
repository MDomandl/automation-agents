from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True, slots=True)
class ProcessResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class SubprocessRunner:
    """
    Führt externe Prozesse aus und liefert ein neutrales Ergebnisobjekt zurück.
    """

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: str | Path | None = None,
        timeout_seconds: int | None = None,
    ) -> ProcessResult:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )

        return ProcessResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
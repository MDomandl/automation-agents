from __future__ import annotations

import subprocess
from time import perf_counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True, slots=True)
class ProcessResult:
    command: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    cwd: str | None
    duration_seconds: float
    timed_out: bool = False

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
        timeout_seconds: float | None = None,
    ) -> ProcessResult:
        normalized_cwd = str(cwd) if cwd is not None else None
        started_at = perf_counter()

        try:
            completed = subprocess.run(
                list(command),
                cwd=normalized_cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            duration_seconds = perf_counter() - started_at
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""

            return ProcessResult(
                command=tuple(command),
                returncode=None,
                stdout=stdout,
                stderr=stderr,
                cwd=normalized_cwd,
                duration_seconds=duration_seconds,
                timed_out=True,
            )

        duration_seconds = perf_counter() - started_at

        return ProcessResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            cwd=normalized_cwd,
            duration_seconds=duration_seconds,
            timed_out=False,
        )

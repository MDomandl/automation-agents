
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.bt_run.models import RunArtifact
from typing import Protocol, Sequence

from app.common.result import Result


class ProcessRunner(Protocol):
    def run(self, command: Sequence[str], cwd: str | None = None) -> Result[None]:
        ...

class DecisionBundleStorePort(ABC):
    """
    Port zum Zugriff auf BT/RUN-Artefakte.
    """

    @abstractmethod
    def get_latest_pair(self) -> Optional[tuple[str, str]]:
        """
        Liefert Referenzen auf das neueste BT/RUN-Paar.

        Rückgabe:
            (bt_id, run_id)
        """
        raise NotImplementedError

    @abstractmethod
    def load_artifact(self, artifact_id: str) -> RunArtifact:
        """
        Lädt ein Artefakt als Domain-Objekt.
        """
        raise NotImplementedError
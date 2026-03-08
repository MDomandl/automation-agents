from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class RunArtifact:
    """
    Repräsentiert einen fachlich bereits geladenen Run-Zustand
    (z. B. aus einem Decision Bundle oder einem anderen Gateway).

    Die Domain kennt keine Dateipfade, kein JSON und keine IO-Details.
    """
    source: str
    as_of: str
    weights: Mapping[str, float]

    def normalized_weights(self) -> dict[str, float]:
        """
        Liefert die Gewichte als normales Dict zurück.
        Defensive Kopie, damit die Domain mit einer stabilen Struktur arbeitet.
        """
        return dict(self.weights)

    def non_cash_weights(self, cash_ticker: str = "CASH") -> dict[str, float]:
        """
        Liefert alle Positionen außer Cash.
        """
        return {
            ticker: weight
            for ticker, weight in self.weights.items()
            if ticker != cash_ticker
        }

    def cash_weight(self, cash_ticker: str = "CASH") -> float:
        """
        Liefert das Cash-Gewicht oder 0.0, falls keines vorhanden ist.
        """
        return float(self.weights.get(cash_ticker, 0.0))


@dataclass(frozen=True, slots=True)
class ComparisonSummary:
    """
    Ergebnis eines BT-vs-RUN-Vergleichs.
    """
    as_of_bt: str
    as_of_run: str
    names_only_in_bt: tuple[str, ...] = ()
    names_only_in_run: tuple[str, ...] = ()
    weight_deltas: Mapping[str, float] = field(default_factory=dict)
    cash_delta: float = 0.0
    matched: bool = False

    @property
    def has_name_differences(self) -> bool:
        return bool(self.names_only_in_bt or self.names_only_in_run)

    @property
    def has_weight_differences(self) -> bool:
        return bool(self.weight_deltas)

    @property
    def has_cash_difference(self) -> bool:
        return self.cash_delta != 0.0
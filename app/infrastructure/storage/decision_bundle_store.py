from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.application.bt_run.ports import DecisionBundleStorePort
from app.domain.bt_run.models import RunArtifact

class FileDecisionBundleStore(DecisionBundleStorePort):
    WEIGHT_FIELDS = ("new_weights", "weights", "positions")
    """
    Liest BT/RUN-Decision-Bundles aus einem Verzeichnis.

    Erwartung:
    - Dateien heißen z. B. BT_*.json und RUN_*.json
    - JSON enthält mindestens:
        - as_of
        - positions oder weights (siehe _extract_weights)
    """


    def __init__(self, decisions_dir: str | Path):
        self._decisions_dir = Path(decisions_dir)

    def get_latest_pair(self) -> Optional[tuple[str, str]]:
        pairs = self.get_all_pairs()
        if not pairs:
            return None
        return pairs[-1]

    def get_all_pairs(self) ->  list[tuple[str, str]]:
        if not self._decisions_dir.exists() or not self._decisions_dir.is_dir():
            return []

        bt_files = sorted(self._decisions_dir.glob("BT_*.json"))
        run_files = sorted(self._decisions_dir.glob("RUN_*.json"))

        if not bt_files or not run_files:
            return []

        bt_by_as_of = self._group_latest_by_as_of(bt_files)
        run_by_as_of = self._group_latest_by_as_of(run_files)

        common_as_ofs = sorted(set(bt_by_as_of) & set(run_by_as_of))
        pairs: list[tuple[str, str]] = []

        for as_of in common_as_ofs:
            bt_file = bt_by_as_of[as_of]
            run_file = run_by_as_of[as_of]
            pairs.append((str(bt_file), str(run_file)))

        return pairs

    def load_artifact(self, artifact_id: str) -> RunArtifact:
        path = Path(artifact_id)

        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        source = self._detect_source(payload, path)
        as_of = self._extract_as_of(payload, path)
        weights = self._extract_weights(self, payload)

        return RunArtifact(
            source=source,
            as_of=as_of,
            weights=weights,
        )

    def _group_latest_by_as_of(self, files: list[Path]) -> dict[str, Path]:
        latest_by_as_of: dict[str, Path] = {}

        for path in files:
            try:
                payload = self._load_json(path)
                as_of = self._extract_as_of(payload, path)
            except (OSError, json.JSONDecodeError, KeyError, ValueError):
                continue

            current = latest_by_as_of.get(as_of)
            if current is None or path.name > current.name:
                latest_by_as_of[as_of] = path

        return latest_by_as_of

    @staticmethod
    def _load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _detect_source(payload: dict, path: Path) -> str:
        kind = payload.get("kind")
        if isinstance(kind, str) and kind.strip():
            return kind.strip().upper()

        if path.name.startswith("BT_"):
            return "BT"
        if path.name.startswith("RUN_"):
            return "RUN"

        return "UNKNOWN"

    @staticmethod
    def _extract_as_of(payload: dict, path: Path) -> str:
        as_of = payload.get("as_of")
        if not isinstance(as_of, str) or not as_of.strip():
            raise KeyError(f"Missing or invalid 'as_of' in {path}")
        return as_of


    @staticmethod
    def _extract_weights(cls, payload: dict) -> dict[str, float]:
        """
        Extrahiert die fachlich relevanten Gewichte aus einem Decision Bundle.

        Priorität für aktien_oop:
        1. new_weights
        2. weights
        """
        for field in cls.WEIGHT_FIELDS:
            value = payload.get(field)

            if value is None:
                continue

            normalized = FileDecisionBundleStore._normalize_weights_value(value)

            if normalized:
                return normalized

        raise KeyError("No supported weights field found: new_weights, weights, positions")

    @staticmethod
    def _normalize_weights_value(value: object) -> dict[str, float]:
        # Fall 1: {"AAPL": 0.7, "CASH": 0.3}
        if isinstance(value, dict):
            return {
                str(ticker): float(weight)
                for ticker, weight in value.items()
            }

        # Fall 2: [{"ticker": "AAPL", "weight": 0.7}, ...]
        if isinstance(value, list):
            result: dict[str, float] = {}

            for item in value:
                if not isinstance(item, dict):
                    continue

                ticker = item.get("ticker")
                weight = item.get("weight")

                if ticker is None or weight is None:
                    continue

                result[str(ticker)] = float(weight)

            return result

        raise TypeError(f"Unsupported weights format: {type(value).__name__}")
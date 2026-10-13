from __future__ import annotations

import importlib
import json
import sys
import tempfile
import tomllib
from pathlib import Path

from app.application.bt_run.previous_state import (
    RunnerPreviousSeedRequest,
    RunnerPreviousSeedResult,
)


class PortfolioStorePreviousStateSeeder:
    """Seeds runner state through aktien_oop's authoritative snapshot store."""

    def __init__(
        self, portfolio_store_type: type | None = None, pandas_module: object | None = None
    ):
        self._portfolio_store_type = portfolio_store_type
        self._pandas_module = pandas_module

    def seed(self, request: RunnerPreviousSeedRequest) -> RunnerPreviousSeedResult:
        try:
            portfolio_store_type, pandas_module = self._portfolio_store_api(request)
            return self._seed(
                bt_positions_path=self._infer_backtest_positions_path(request),
                runner_positions_path=self._infer_runner_positions_path(request),
                runner_as_of=request.runner_as_of,
                bt_snapshots=self._load_bt_snapshots(request.decisions_dir),
                portfolio_store_type=portfolio_store_type,
                pandas_module=pandas_module,
            )
        except Exception as exc:
            return RunnerPreviousSeedResult(
                seeded=False,
                message=f"[WARN] Runner previous-state seed failed: {exc}",
            )

    def _portfolio_store_api(self, request: RunnerPreviousSeedRequest) -> tuple[type, object]:
        if self._portfolio_store_type is not None and self._pandas_module is not None:
            return self._portfolio_store_type, self._pandas_module

        roots: list[Path] = []
        for cwd, config_path in (
            (request.backtest_cwd, request.backtest_config_path),
            (request.runner_cwd, request.runner_config_path),
        ):
            if cwd is not None:
                roots.append(Path(cwd))
            for parent in config_path.parents:
                if (parent / "aktien_oop" / "store.py").exists():
                    roots.append(parent)
                    break

        for root in roots:
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)

        store_module = importlib.import_module("aktien_oop.store")
        pandas_module = importlib.import_module("pandas")
        return store_module.PortfolioStore, pandas_module

    @classmethod
    def _infer_backtest_positions_path(cls, request: RunnerPreviousSeedRequest) -> Path:
        config = cls._load_toml(request.backtest_config_path)
        save_dir = cls._resolve_path(
            config.get("save_dir", "aktien_oop"),
            base_cwd=request.backtest_cwd,
            config_path=request.backtest_config_path,
        )
        frequency = str(
            config.get("rebalance", {}).get("frequency", config.get("frequency", "monthly"))
        )
        top_k = int(config.get("topk", {}).get("top_k", config.get("top_k")))
        buffer_k = int(config.get("topk", {}).get("buffer_k", config.get("buffer_k")))
        return save_dir / f"bt_{frequency}_{top_k}x{buffer_k}_positions.csv"

    @classmethod
    def _infer_runner_positions_path(cls, request: RunnerPreviousSeedRequest) -> Path:
        config = cls._load_toml(request.runner_config_path)
        save_dir = cls._resolve_path(
            config.get("save_dir", "aktien_oop"),
            base_cwd=request.runner_cwd,
            config_path=request.runner_config_path,
        )
        return save_dir / "portfolio_positions.csv"

    @staticmethod
    def _load_toml(config_path: Path) -> dict:
        with config_path.open("rb") as file_obj:
            return tomllib.load(file_obj)

    @staticmethod
    def _resolve_path(value: object, *, base_cwd: str | Path | None, config_path: Path) -> Path:
        path = Path(str(value))
        if path.is_absolute():
            return path
        if base_cwd is not None:
            return Path(base_cwd) / path
        return config_path.parent / path

    @classmethod
    def _load_bt_snapshots(cls, decisions_dir: Path | None) -> dict[str, dict[str, float]]:
        """Return complete snapshots while preserving missing versus explicit empty."""
        if decisions_dir is None or not decisions_dir.exists():
            return {}

        snapshots: dict[str, dict[str, float]] = {}
        for path in sorted(decisions_dir.glob("BT_*.json")):
            try:
                with path.open("r", encoding="utf-8") as file_obj:
                    payload = json.load(file_obj)
            except (OSError, json.JSONDecodeError):
                continue

            as_of = payload.get("as_of")
            if not isinstance(as_of, str) or not as_of.strip():
                continue

            weights = cls._bundle_weights_value(payload)
            if weights is None:
                continue
            snapshots[as_of.strip()] = cls._normalize_bundle_weights(weights)

        return snapshots

    @staticmethod
    def _bundle_weights_value(payload: dict) -> dict | list | None:
        for field in ("new_weights", "weights", "positions"):
            value = payload.get(field)
            if isinstance(value, (dict, list)):
                return value
        return None

    @staticmethod
    def _normalize_bundle_weights(value: dict | list) -> dict[str, float]:
        if isinstance(value, dict):
            return {str(ticker): float(weight) for ticker, weight in value.items()}

        weights: dict[str, float] = {}
        for item in value:
            if not isinstance(item, dict):
                continue
            ticker = item.get("ticker")
            weight = item.get("weight")
            if ticker is not None and weight is not None:
                weights[str(ticker)] = float(weight)
        return weights

    @classmethod
    def _seed(
        cls,
        *,
        bt_positions_path: Path,
        runner_positions_path: Path,
        runner_as_of: str,
        bt_snapshots: dict[str, dict[str, float]],
        portfolio_store_type: type,
        pandas_module: object,
    ) -> RunnerPreviousSeedResult:
        if not bt_snapshots and not bt_positions_path.exists():
            return RunnerPreviousSeedResult(
                seeded=False,
                message=(
                    "[INFO] Runner previous-state seed skipped: "
                    f"BT positions not found: {bt_positions_path}"
                ),
            )

        with tempfile.TemporaryDirectory(prefix="automation-agents-bt-snapshots-") as temp_dir:
            bt_store = portfolio_store_type(Path(temp_dir))
            bt_frame = (
                pandas_module.read_csv(bt_positions_path, comment="#")
                if bt_positions_path.exists()
                else pandas_module.DataFrame(columns=["as_of", "ticker", "weight"])
            )
            for as_of, weights in sorted(bt_snapshots.items()):
                frame = cls._positions_for_snapshot(
                    bt_frame,
                    as_of=as_of,
                    weights=weights,
                    pandas_module=pandas_module,
                )
                bt_store.save_positions(frame, snapshot_as_of=as_of)

            previous_snapshot = bt_store.load_positions_snapshot_before(runner_as_of)

        if previous_snapshot is None:
            return RunnerPreviousSeedResult(
                seeded=False,
                message=(
                    "[INFO] Runner previous-state seed skipped: "
                    f"runner_as_of={runner_as_of}, no BT snapshot before runner_as_of"
                ),
            )

        runner_store = portfolio_store_type(runner_positions_path.parent)
        if Path(runner_store.positions_path) != runner_positions_path:
            raise ValueError(
                "Runner PortfolioStore path mismatch: "
                f"expected {runner_positions_path}, got {runner_store.positions_path}"
            )
        runner_store.save_positions(
            previous_snapshot.positions,
            snapshot_as_of=previous_snapshot.as_of,
        )

        previous_as_of = previous_snapshot.as_of.strftime("%Y-%m-%d")
        row_count = len(previous_snapshot.positions)
        return RunnerPreviousSeedResult(
            seeded=True,
            previous_as_of=previous_as_of,
            row_count=row_count,
            message=(
                "[INFO] Runner previous-state seeded from backtest positions: "
                f"runner_as_of={runner_as_of}, prev_as_of={previous_as_of}, rows={row_count}"
            ),
        )

    @staticmethod
    def _positions_for_snapshot(
        bt_frame: object,
        *,
        as_of: str,
        weights: dict[str, float],
        pandas_module: object,
    ) -> object:
        if not weights:
            return pandas_module.DataFrame(columns=["as_of", "ticker", "weight"])

        positions = bt_frame.iloc[0:0].copy()
        if "as_of" in bt_frame.columns:
            normalized_dates = pandas_module.to_datetime(
                bt_frame["as_of"], errors="coerce"
            ).dt.strftime("%Y-%m-%d")
            positions = bt_frame.loc[normalized_dates == as_of].copy()

        if "ticker" in positions.columns:
            positions["ticker"] = positions["ticker"].astype(str)
            positions = positions[positions["ticker"].isin(weights)]
            positions = positions.drop_duplicates(subset=["ticker"], keep="last")

        rows_by_ticker = {
            str(row["ticker"]): row.to_dict() for _, row in positions.iterrows() if "ticker" in row
        }
        has_allocation_pct = "allocation_pct" in bt_frame.columns
        reconciled_rows = []
        for ticker, weight in sorted(weights.items()):
            row = rows_by_ticker.get(ticker, {})
            row.update({"as_of": as_of, "ticker": ticker, "weight": weight})
            if has_allocation_pct:
                row["allocation_pct"] = weight * 100.0
            reconciled_rows.append(row)

        return pandas_module.DataFrame(reconciled_rows)

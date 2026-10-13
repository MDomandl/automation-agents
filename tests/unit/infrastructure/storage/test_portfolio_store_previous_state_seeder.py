from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pytest

from app.application.bt_run.previous_state import RunnerPreviousSeedRequest
from app.infrastructure.storage.portfolio_store_previous_state_seeder import (
    PortfolioStorePreviousStateSeeder,
)


@dataclass
class FakePositionsSnapshot:
    as_of: pd.Timestamp
    positions: pd.DataFrame


class FakePortfolioStore:
    _snapshots_by_dir: dict[Path, dict[str, pd.DataFrame]] = {}

    def __init__(self, save_dir: Path):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.positions_path = self.save_dir / "portfolio_positions.csv"
        self.snapshots_path = self.save_dir / "portfolio_snapshots.csv"
        self._snapshots = self._snapshots_by_dir.setdefault(self.save_dir, {})

    def save_positions(self, positions: pd.DataFrame, *, snapshot_as_of) -> None:
        as_of = pd.Timestamp(snapshot_as_of).strftime("%Y-%m-%d")
        frame = positions.copy()
        if not frame.empty:
            frame["as_of"] = pd.Timestamp(as_of)
            frame["ticker"] = frame["ticker"].astype(str)
        self._snapshots[as_of] = frame
        persisted = [snapshot for snapshot in self._snapshots.values() if not snapshot.empty]
        if persisted:
            pd.concat(persisted, ignore_index=True, sort=False).to_csv(
                self.positions_path, index=False
            )
        else:
            pd.DataFrame(columns=["as_of", "ticker", "weight"]).to_csv(
                self.positions_path, index=False
            )
        pd.DataFrame({"as_of": sorted(self._snapshots)}).to_csv(self.snapshots_path, index=False)

    def load_positions_snapshot_before(self, as_of: str) -> FakePositionsSnapshot | None:
        candidates = [
            snapshot_as_of for snapshot_as_of in self._snapshots if snapshot_as_of < as_of
        ]
        if not candidates:
            return None
        previous_as_of = max(candidates)
        return FakePositionsSnapshot(
            as_of=pd.Timestamp(previous_as_of),
            positions=self._snapshots[previous_as_of].copy(),
        )


@pytest.fixture
def portfolio_store_type():
    FakePortfolioStore._snapshots_by_dir.clear()
    return FakePortfolioStore


def test_missing_snapshot_does_not_change_runner_state(
    tmp_path: Path, portfolio_store_type
) -> None:
    seeder, request, runner_store = _arrange(
        tmp_path,
        portfolio_store_type,
        snapshots={"2025-10-08": {"FUTURE": 1.0}},
    )
    runner_store.save_positions(
        pd.DataFrame([{"as_of": "2025-08-29", "ticker": "EXISTING", "weight": 1.0}]),
        snapshot_as_of="2025-08-29",
    )
    positions_before = runner_store.positions_path.read_text(encoding="utf-8")
    snapshots_before = runner_store.snapshots_path.read_text(encoding="utf-8")

    result = seeder.seed(request)

    assert result.seeded is False
    assert "no BT snapshot before runner_as_of" in result.message
    assert runner_store.positions_path.read_text(encoding="utf-8") == positions_before
    assert runner_store.snapshots_path.read_text(encoding="utf-8") == snapshots_before


def test_explicit_empty_snapshot_removes_stale_runner_positions(
    tmp_path: Path, portfolio_store_type
) -> None:
    seeder, request, runner_store = _arrange(
        tmp_path,
        portfolio_store_type,
        snapshots={"2025-08-29": {"OLDER": 1.0}, "2025-09-30": {}},
    )
    runner_store.save_positions(
        pd.DataFrame([{"as_of": "2025-09-30", "ticker": "STALE", "weight": 1.0}]),
        snapshot_as_of="2025-09-30",
    )

    result = seeder.seed(request)

    assert result.seeded is True
    assert result.previous_as_of == "2025-09-30"
    assert result.row_count == 0
    snapshot = runner_store.load_positions_snapshot_before("2025-10-08")
    assert snapshot is not None and snapshot.positions.empty


def test_non_empty_snapshot_replaces_complete_runner_snapshot(
    tmp_path: Path, portfolio_store_type
) -> None:
    seeder, request, runner_store = _arrange(
        tmp_path,
        portfolio_store_type,
        snapshots={"2025-09-30": {"AAPL": 1.0}},
    )
    runner_store.save_positions(
        pd.DataFrame([{"as_of": "2025-09-30", "ticker": "STALE", "weight": 1.0}]),
        snapshot_as_of="2025-09-30",
    )

    result = seeder.seed(request)

    assert result.seeded is True
    snapshot = runner_store.load_positions_snapshot_before("2025-10-08")
    assert snapshot is not None
    assert snapshot.positions["ticker"].tolist() == ["AAPL"]


def test_mixed_history_does_not_fall_back_past_explicit_empty(
    tmp_path: Path, portfolio_store_type
) -> None:
    seeder, request, runner_store = _arrange(
        tmp_path,
        portfolio_store_type,
        snapshots={
            "2025-09-30": {"OLD": 1.0},
            "2025-10-31": {},
            "2025-11-30": {"NEW": 1.0},
        },
        runner_as_of="2025-11-15",
    )

    result = seeder.seed(request)

    assert result.seeded is True
    assert result.previous_as_of == "2025-10-31"
    snapshot = runner_store.load_positions_snapshot_before("2025-11-15")
    assert snapshot is not None and snapshot.positions.empty


def _arrange(
    tmp_path: Path,
    portfolio_store_type: type,
    *,
    snapshots: dict[str, dict[str, float]],
    runner_as_of: str = "2025-10-08",
) -> tuple[PortfolioStorePreviousStateSeeder, RunnerPreviousSeedRequest, object]:
    bt_save_dir = tmp_path / "bt"
    runner_save_dir = tmp_path / "runner"
    decisions_dir = tmp_path / "decisions"
    bt_save_dir.mkdir()
    runner_save_dir.mkdir()
    decisions_dir.mkdir()
    bt_config_path = tmp_path / "bt.toml"
    runner_config_path = tmp_path / "runner.toml"
    bt_config_path.write_text(
        "\n".join(
            [
                f'save_dir = "{bt_save_dir.as_posix()}"',
                "top_k = 12",
                "buffer_k = 3",
                "[rebalance]",
                'frequency = "monthly"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    runner_config_path.write_text(f'save_dir = "{runner_save_dir.as_posix()}"\n', encoding="utf-8")
    (bt_save_dir / "bt_monthly_12x3_positions.csv").write_text(
        "as_of,ticker,allocation_pct\n"
        "2025-08-29,OLDER,100.0\n"
        "2025-09-30,AAPL,100.0\n"
        "2025-10-31,STALE,100.0\n"
        "2025-11-30,NEW,100.0\n",
        encoding="utf-8",
    )
    for index, (as_of, weights) in enumerate(snapshots.items()):
        weights_json = ", ".join(f'"{ticker}": {weight}' for ticker, weight in weights.items())
        (decisions_dir / f"BT_{index:03d}.json").write_text(
            f'{{"as_of": "{as_of}", "new_weights": {{{weights_json}}}}}',
            encoding="utf-8",
        )

    seeder = PortfolioStorePreviousStateSeeder(portfolio_store_type, pd)
    request = RunnerPreviousSeedRequest(
        backtest_config_path=bt_config_path,
        backtest_cwd=None,
        runner_config_path=runner_config_path,
        runner_cwd=None,
        runner_as_of=runner_as_of,
        decisions_dir=decisions_dir,
    )
    return seeder, request, portfolio_store_type(runner_save_dir)

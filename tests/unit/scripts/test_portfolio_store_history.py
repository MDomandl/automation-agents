from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


AI_AGENTS_ROOT = Path(
    r"D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents"
)
if str(AI_AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_AGENTS_ROOT))

from aktien_oop.store import PortfolioStore
from aktien_oop.core_calc import CalcParams, select_topk_buffer


def test_save_positions_keeps_history_and_loads_latest_previous_snapshot(tmp_path: Path) -> None:
    store = PortfolioStore(tmp_path)

    store.save_positions(
        pd.DataFrame(
            [
                {"as_of": "2025-09-30", "ticker": "AVGO", "allocation_pct": 0.11},
                {"as_of": "2025-09-30", "ticker": "STX", "allocation_pct": 0.12},
            ]
        )
    )
    store.save_positions(
        pd.DataFrame(
            [
                {"as_of": "2025-10-08", "ticker": "GLW", "allocation_pct": 0.10},
                {"as_of": "2025-10-08", "ticker": "STX", "allocation_pct": 0.13},
            ]
        )
    )
    store.save_positions(
        pd.DataFrame(
            [
                {"as_of": "2025-10-31", "ticker": "MSFT", "allocation_pct": 0.14},
            ]
        )
    )

    prev = store.load_positions_before("2025-10-31")

    assert prev is not None
    assert prev["ticker"].tolist() == ["GLW", "STX"]
    assert prev["as_of"].dt.strftime("%Y-%m-%d").unique().tolist() == ["2025-10-08"]


def test_save_positions_replaces_duplicate_as_of_ticker(tmp_path: Path) -> None:
    store = PortfolioStore(tmp_path)

    store.save_positions(
        pd.DataFrame(
            [
                {"as_of": "2025-10-08", "ticker": "GLW", "allocation_pct": 0.10},
                {"as_of": "2025-10-08", "ticker": "STX", "allocation_pct": 0.13},
            ]
        )
    )
    store.save_positions(
        pd.DataFrame(
            [
                {"as_of": "2025-10-08", "ticker": "GLW", "allocation_pct": 0.20},
            ]
        )
    )

    persisted = pd.read_csv(store.positions_path)

    assert len(persisted[persisted["ticker"] == "GLW"]) == 1
    assert persisted.loc[persisted["ticker"] == "GLW", "allocation_pct"].item() == 0.20
    assert persisted["ticker"].tolist() == ["GLW", "STX"]


def test_historical_positions_feed_buffer_selection(tmp_path: Path) -> None:
    store = PortfolioStore(tmp_path)
    store.save_positions(
        pd.DataFrame(
            [
                {"as_of": "2025-09-30", "ticker": "STX", "allocation_pct": 0.11},
                {"as_of": "2025-09-30", "ticker": "WDC", "allocation_pct": 0.11},
                {"as_of": "2025-09-30", "ticker": "AVGO", "allocation_pct": 0.11},
            ]
        )
    )
    store.save_positions(
        pd.DataFrame(
            [
                {"as_of": "2025-10-08", "ticker": "STX", "allocation_pct": 0.11},
                {"as_of": "2025-10-08", "ticker": "WDC", "allocation_pct": 0.11},
                {"as_of": "2025-10-08", "ticker": "GLW", "allocation_pct": 0.11},
            ]
        )
    )

    prev = store.load_positions_before("2025-10-08")
    assert prev is not None
    prev_holdings = prev["ticker"].tolist()

    scores = pd.Series(
        [1.00, 0.99, 0.98, 0.97],
        index=["STX", "WDC", "GLW", "AVGO"],
        dtype=float,
    )
    params = CalcParams(
        as_of="2025-10-08",
        period="400d",
        adjusted=True,
        score_days=200,
        vol_days=63,
        top_k=3,
        buffer_k=1,
        use_sector_limits=True,
        max_per_sector=3,
    )

    selected = set(
        select_topk_buffer(
            scores,
            pd.Index(scores.index),
            {ticker: "Information Technology" for ticker in scores.index},
            params,
            prev_holdings=prev_holdings,
        )
    )

    assert "AVGO" in selected
    assert "GLW" not in selected

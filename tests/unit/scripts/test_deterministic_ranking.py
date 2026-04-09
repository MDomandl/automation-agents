from __future__ import annotations

import sys
from pathlib import Path


AI_AGENTS_ROOT = Path(
    r"D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents"
)
if str(AI_AGENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(AI_AGENTS_ROOT))

from aktien_oop.core_calc import CalcParams, _rank_desc_stable, select_topk_buffer


def test_rank_desc_stable_uses_ticker_as_tiebreaker() -> None:
    import pandas as pd

    scores = pd.Series(
        [1.0, 1.0, 1.0],
        index=["MSFT", "AAPL", "NVDA"],
        dtype=float,
    )

    ranks = _rank_desc_stable(scores)

    assert ranks.to_dict() == {
        "MSFT": 2,
        "AAPL": 1,
        "NVDA": 3,
    }


def test_select_topk_buffer_is_deterministic_for_equal_scores() -> None:
    import pandas as pd

    scores = pd.Series(
        [1.0, 1.0, 1.0, 1.0],
        index=["MSFT", "AAPL", "NVDA", "GOOG"],
        dtype=float,
    )
    keep = pd.Index(scores.index)
    sectors = {ticker: "TECH" for ticker in scores.index}
    params = CalcParams(
        as_of="2025-04-30",
        period="400d",
        adjusted=True,
        score_days=200,
        vol_days=63,
        top_k=3,
        buffer_k=1,
        use_sector_limits=False,
    )

    first = list(select_topk_buffer(scores, keep, sectors, params, prev_holdings=[]))
    second = list(select_topk_buffer(scores, keep, sectors, params, prev_holdings=[]))

    assert first == ["AAPL", "GOOG", "MSFT"]
    assert second == first

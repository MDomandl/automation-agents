from __future__ import annotations

import os

import pytest

from scripts.validate_ai_agents_test_environment import (
    audit_test_environment,
    import_ai_agents_module,
)

ai_agents_root_value = os.environ.get("AI_AGENTS_ROOT")
if not ai_agents_root_value:
    pytest.skip("requires AI_AGENTS_ROOT for KiAgents integration tests", allow_module_level=True)
AI_AGENTS_ROOT = audit_test_environment(ai_agents_root_value)
core_calc = import_ai_agents_module(AI_AGENTS_ROOT, "aktien_oop.core_calc")
CalcParams = core_calc.CalcParams
_rank_desc_stable = core_calc._rank_desc_stable
select_topk_buffer = core_calc.select_topk_buffer


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

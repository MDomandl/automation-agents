import pytest

from app.domain.bt_run.compare import compare_run_artifacts
from app.domain.bt_run.models import RunArtifact
from tests.helpers.helpers import approx


def test_compare_run_artifacts_matches_when_weights_are_equal_within_tolerance() -> None:
    bt = RunArtifact(
        source="BT",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.5000,
            "MSFT": 0.3000,
            "CASH": 0.2000,
        },
    )
    run = RunArtifact(
        source="RUN",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.5003,   # 3 bps
            "MSFT": 0.2998,   # 2 bps
            "CASH": 0.1999,
        },
    )

    summary = compare_run_artifacts(bt, run, bps_tolerance=5.0, ignore_cash=True)

    assert summary.matched is True
    assert summary.names_only_in_bt == ()
    assert summary.names_only_in_run == ()
    assert summary.weight_deltas == {}
    assert summary.cash_delta == 0.0


def test_compare_run_artifacts_detects_name_differences() -> None:
    bt = RunArtifact(
        source="BT",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.6,
            "MSFT": 0.4,
        },
    )
    run = RunArtifact(
        source="RUN",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.6,
            "NVDA": 0.4,
        },
    )

    summary = compare_run_artifacts(bt, run, bps_tolerance=5.0, ignore_cash=True)

    assert summary.matched is False
    assert summary.names_only_in_bt == ("MSFT",)
    assert summary.names_only_in_run == ("NVDA",)
    assert summary.weight_deltas == {}


def test_compare_run_artifacts_detects_weight_delta_above_tolerance() -> None:
    bt = RunArtifact(
        source="BT",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.55,
            "MSFT": 0.45,
        },
    )
    run = RunArtifact(
        source="RUN",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.56,
            "MSFT": 0.44,
        },
    )

    summary = compare_run_artifacts(bt, run, bps_tolerance=5.0, ignore_cash=True)

    assert summary.matched is False
    assert summary.names_only_in_bt == ()
    assert summary.names_only_in_run == ()
    assert "AAPL" in summary.weight_deltas
    assert "MSFT" in summary.weight_deltas


def test_compare_run_artifacts_can_include_cash_difference() -> None:
    bt = RunArtifact(
        source="BT",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.7,
            "CASH": 0.3,
        },
    )
    run = RunArtifact(
        source="RUN",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.7,
            "CASH": 0.25,
        },
    )

    summary = compare_run_artifacts(bt, run, bps_tolerance=5.0, ignore_cash=False)

    assert summary.matched is False
    assert summary.cash_delta == approx(0.05)

def test_compare_run_artifacts_ignores_tiny_float_noise_within_tolerance() -> None:
    bt = RunArtifact(
        source="BT",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.3333,
            "MSFT": 0.3333,
            "NVDA": 0.3334,
        },
    )
    run = RunArtifact(
        source="RUN",
        as_of="2025-10-10",
        weights={
            "AAPL": 0.3333000001,
            "MSFT": 0.3332999999,
            "NVDA": 0.3334,
        },
    )

    summary = compare_run_artifacts(bt, run, bps_tolerance=5.0, ignore_cash=True)

    assert summary.matched is True
    assert summary.weight_deltas == {}
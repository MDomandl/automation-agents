from __future__ import annotations

from app.domain.bt_run.models import ComparisonSummary, RunArtifact


def compare_run_artifacts(
    bt: RunArtifact,
    run: RunArtifact,
    *,
    bps_tolerance: float = 5.0,
    ignore_cash: bool = True,
    cash_ticker: str = "CASH",
) -> ComparisonSummary:
    """
    Vergleicht zwei Run-Artefakte fachlich.

    Regeln:
    - Namen werden als Mengen verglichen.
    - Gewichte werden nur für gemeinsame Ticker verglichen.
    - Ein Weight-Delta wird nur gemeldet, wenn es die Toleranz überschreitet.
    - Cash kann optional ignoriert werden.

    bps_tolerance:
        Toleranz in Basispunkten.
        Beispiel: 5.0 = 0.0005 absolute Gewichtsabweichung.
    """
    bt_weights = bt.normalized_weights()
    run_weights = run.normalized_weights()

    if ignore_cash:
        bt_weights.pop(cash_ticker, None)
        run_weights.pop(cash_ticker, None)

    bt_names = set(bt_weights.keys())
    run_names = set(run_weights.keys())

    names_only_in_bt = tuple(sorted(bt_names - run_names))
    names_only_in_run = tuple(sorted(run_names - bt_names))

    common_names = sorted(bt_names & run_names)

    tolerance = _bps_to_weight(bps_tolerance)
    weight_deltas: dict[str, float] = {}

    for ticker in common_names:
        delta = bt_weights[ticker] - run_weights[ticker]
        if abs(delta) > tolerance:
            weight_deltas[ticker] = delta

    cash_delta = 0.0
    if not ignore_cash:
        cash_delta = bt.cash_weight(cash_ticker) - run.cash_weight(cash_ticker)

    matched = (
        not names_only_in_bt
        and not names_only_in_run
        and not weight_deltas
        and (ignore_cash or cash_delta == 0.0)
    )

    return ComparisonSummary(
        as_of_bt=bt.as_of,
        as_of_run=run.as_of,
        names_only_in_bt=names_only_in_bt,
        names_only_in_run=names_only_in_run,
        weight_deltas=weight_deltas,
        cash_delta=cash_delta,
        matched=matched,
    )


def _bps_to_weight(bps: float) -> float:
    """
    Wandelt Basispunkte in absolute Gewichtsabweichung um.

    1 bp = 0.0001
    5 bp = 0.0005
    """
    return bps / 10_000.0

def build_note(differing_names: int, differing_weights: int) -> str:
    if differing_names == 0 and differing_weights == 0:
        return "BT und RUN sind im Toleranzbereich."
    if differing_names > 0 and differing_weights == 0:
        return "Namensabweichungen gefunden."
    if differing_names == 0 and differing_weights > 0:
        return "Gewichtsabweichungen gefunden."
    return "Namens- und Gewichtsabweichungen gefunden."
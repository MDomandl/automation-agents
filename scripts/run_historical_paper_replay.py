from __future__ import annotations

import argparse
import calendar
import json
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_OUT_DIR = Path("reports") / "historical_paper_replay"
JSON_REPORT_NAME = "historical_paper_replay.json"
MARKDOWN_REPORT_NAME = "historical_paper_replay.md"
MANIFEST_NAME = "historical_paper_replay_manifest.json"
DEFAULT_STRATEGY_PROFILE = "balanced_v1"
DEFAULT_PROFILE = "short"
DEFAULT_FREQUENCY = "monthly"
DEFAULT_TOLERANCE = 0.00001
DEFAULT_TARGET_WEIGHT_JUMP_THRESHOLD = 0.05
REPRODUCIBLE_GENERATED_AT = "not_recorded_for_reproducibility"

SAFETY_FIELDS = {
    "broker_connected": False,
    "live_trading_enabled": False,
    "orders_executed": False,
    "investment_recommendation_generated": False,
    "position_sizing_enabled": False,
    "euro_amounts_calculated": False,
    "share_quantities_calculated": False,
}


class ReplayInputError(ValueError):
    pass


def run_historical_paper_replay(
    *,
    start: str,
    end: str,
    warmup_start: str | None = None,
    strategy_profile: str = DEFAULT_STRATEGY_PROFILE,
    profile: str = DEFAULT_PROFILE,
    frequency: str = DEFAULT_FREQUENCY,
    output_dir: Path = DEFAULT_OUT_DIR,
    tolerance: float = DEFAULT_TOLERANCE,
    positions_file: Path | None = None,
    target_weight_jump_threshold: float = DEFAULT_TARGET_WEIGHT_JUMP_THRESHOLD,
) -> dict[str, Any]:
    _validate_inputs(
        start=start,
        end=end,
        warmup_start=warmup_start,
        strategy_profile=strategy_profile,
        frequency=frequency,
        tolerance=tolerance,
        target_weight_jump_threshold=target_weight_jump_threshold,
    )
    as_of_dates = generate_monthly_as_of_dates(start, end)
    positions_by_as_of = load_positions_by_as_of(positions_file) if positions_file else {}

    snapshots = [
        build_snapshot(
            as_of=as_of,
            strategy_profile=strategy_profile,
            profile=profile,
            positions=positions_by_as_of.get(as_of),
        )
        for as_of in as_of_dates
    ]
    comparisons = build_comparisons(
        snapshots,
        tolerance=tolerance,
        target_weight_jump_threshold=target_weight_jump_threshold,
    )
    manifest = build_manifest(
        start=start,
        end=end,
        warmup_start=warmup_start,
        strategy_profile=strategy_profile,
        profile=profile,
        frequency=frequency,
        tolerance=tolerance,
        as_of_dates=as_of_dates,
        positions_file=positions_file,
        target_weight_jump_threshold=target_weight_jump_threshold,
    )
    report = {
        "generated_at": REPRODUCIBLE_GENERATED_AT,
        "runner_mode": "historical_paper_replay",
        **SAFETY_FIELDS,
        "strategy_profile": strategy_profile,
        "profile": profile,
        "replay_start": start,
        "replay_end": end,
        "warmup_start": warmup_start,
        "frequency": frequency,
        "tolerance": tolerance,
        "target_weight_jump_threshold": target_weight_jump_threshold,
        "as_of_dates": as_of_dates,
        "snapshots": snapshots,
        "comparisons": comparisons,
        "warnings": _report_warnings(snapshots, comparisons),
        "proposal_note": (
            "Buy/Sell/Hold are technical delta checks only. They are not investment "
            "advice, not recommendations, and do not trigger orders."
        ),
        "limits": [
            "No benchmark calculation.",
            "No market phase detection.",
            "No performance analysis.",
            "No broker connection.",
            "No live trading.",
            "No orders or order proposals.",
            "No euro amounts or share quantities.",
            "No portfolio normalization.",
        ],
    }
    write_outputs(report, manifest, output_dir)
    return report


def generate_monthly_as_of_dates(start: str, end: str) -> list[str]:
    start_date = _parse_iso_date(start, "start")
    end_date = _parse_iso_date(end, "end")
    if start_date > end_date:
        raise ReplayInputError(f"start must be <= end (got {start} > {end})")

    dates: list[str] = []
    current = start_date
    while current <= end_date:
        dates.append(current.isoformat())
        current = _add_month_preserving_day(current, start_date.day)
    return dates


def load_positions_by_as_of(path: Path) -> dict[str, dict[str, float]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReplayInputError(f"Invalid positions JSON in {path}: {exc.msg}") from exc
    except OSError as exc:
        raise ReplayInputError(f"Could not read positions file {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ReplayInputError("positions file must contain a JSON object")

    raw_items = payload.get("positions_by_as_of", payload)
    if not isinstance(raw_items, dict):
        raise ReplayInputError("positions_by_as_of must be a JSON object")

    result: dict[str, dict[str, float]] = {}
    for raw_as_of, raw_positions in raw_items.items():
        as_of = _parse_iso_date(str(raw_as_of), "as_of").isoformat()
        if isinstance(raw_positions, dict) and isinstance(raw_positions.get("positions"), dict):
            raw_positions = raw_positions["positions"]
        result[as_of] = _coerce_positions(raw_positions, context=as_of)
    return result


def build_snapshot(
    *,
    as_of: str,
    strategy_profile: str,
    profile: str,
    positions: dict[str, float] | None,
) -> dict[str, Any]:
    warnings: list[dict[str, str]] = []
    if positions is None:
        warnings.append(
            {
                "reason": "missing_positions",
                "message": f"No target positions available for {as_of}.",
            }
        )
        positions = {}
        data_status = "missing_positions"
    else:
        data_status = "ok" if positions else "empty_positions"
        if not positions:
            warnings.append(
                {
                    "reason": "empty_positions",
                    "message": f"Target positions are empty for {as_of}.",
                }
            )

    return {
        "as_of": as_of,
        "strategy_profile": strategy_profile,
        "profile": profile,
        "data_status": data_status,
        "positions": [
            {"symbol": symbol, "target_weight": weight}
            for symbol, weight in sorted(positions.items())
        ],
        "target_weights": dict(sorted(positions.items())),
        "warnings": warnings,
    }


def build_comparisons(
    snapshots: list[dict[str, Any]],
    *,
    tolerance: float,
    target_weight_jump_threshold: float,
) -> list[dict[str, Any]]:
    comparisons = []
    for previous, current in zip(snapshots, snapshots[1:]):
        comparisons.append(
            compare_snapshots(
                previous,
                current,
                tolerance=tolerance,
                target_weight_jump_threshold=target_weight_jump_threshold,
            )
        )
    return comparisons


def compare_snapshots(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    tolerance: float,
    target_weight_jump_threshold: float,
) -> dict[str, Any]:
    previous_weights = _target_weights(previous)
    current_weights = _target_weights(current)
    previous_symbols = set(previous_weights)
    current_symbols = set(current_weights)
    new_symbols = sorted(current_symbols - previous_symbols)
    removed_symbols = sorted(previous_symbols - current_symbols)
    common_symbols = sorted(previous_symbols & current_symbols)
    all_symbols = sorted(previous_symbols | current_symbols)

    symbol_changes = [
        _compare_symbol(
            symbol=symbol,
            previous_weight=previous_weights.get(symbol, 0.0),
            current_weight=current_weights.get(symbol, 0.0),
            tolerance=tolerance,
            target_weight_jump_threshold=target_weight_jump_threshold,
        )
        for symbol in all_symbols
    ]
    proposal_change_count = sum(
        1
        for item in symbol_changes
        if item["previous_proposal"] != item["current_proposal"]
    )
    target_weight_jump_count = sum(
        1 for item in symbol_changes if item["target_weight_jump"] is True
    )
    total_abs_weight_delta = sum(item["abs_weight_delta"] for item in symbol_changes)
    max_abs_weight_delta = max(
        (item["abs_weight_delta"] for item in symbol_changes),
        default=0.0,
    )
    warnings = _comparison_warnings(previous, current)

    return {
        "from_as_of": previous["as_of"],
        "to_as_of": current["as_of"],
        "new_symbols_count": len(new_symbols),
        "removed_symbols_count": len(removed_symbols),
        "common_symbols_count": len(common_symbols),
        "proposal_change_count": proposal_change_count,
        "target_weight_jump_count": target_weight_jump_count,
        "total_abs_weight_delta": total_abs_weight_delta,
        "max_abs_weight_delta": max_abs_weight_delta,
        "warnings_count": len(warnings),
        "new_symbols": new_symbols,
        "removed_symbols": removed_symbols,
        "common_symbols": common_symbols,
        "symbol_changes": symbol_changes,
        "warnings": warnings,
    }


def build_manifest(
    *,
    start: str,
    end: str,
    warmup_start: str | None,
    strategy_profile: str,
    profile: str,
    frequency: str,
    tolerance: float,
    as_of_dates: list[str],
    positions_file: Path | None,
    target_weight_jump_threshold: float,
) -> dict[str, Any]:
    return {
        "generated_at": REPRODUCIBLE_GENERATED_AT,
        "runner_mode": "historical_paper_replay",
        **SAFETY_FIELDS,
        "strategy_profile": strategy_profile,
        "profile": profile,
        "replay_start": start,
        "replay_end": end,
        "warmup_start": warmup_start,
        "frequency": frequency,
        "tolerance": tolerance,
        "target_weight_jump_threshold": target_weight_jump_threshold,
        "as_of_dates": as_of_dates,
        "positions_file": str(positions_file) if positions_file else None,
        "safety_note": (
            "Historical paper replay is an analysis artifact only. It does not connect "
            "to a broker, does not trade, does not size positions, and does not "
            "generate investment recommendations."
        ),
    }


def write_outputs(
    report: dict[str, Any],
    manifest: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / JSON_REPORT_NAME
    markdown_path = output_dir / MARKDOWN_REPORT_NAME
    manifest_path = output_dir / MANIFEST_NAME
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(build_markdown(report, manifest), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return json_path, markdown_path, manifest_path


def build_markdown(report: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# Historical Paper Replay",
        "",
        "## Zusammenfassung",
        "",
        f"* Zeitraum: {report.get('replay_start')} bis {report.get('replay_end')}",
        f"* Strategieprofil: {report.get('strategy_profile')}",
        f"* Zeitprofil: {report.get('profile')}",
        f"* Stichtage: {len(report.get('as_of_dates', []))}",
        f"* Vergleiche: {len(report.get('comparisons', []))}",
        "",
        "## Sicherheitsstatus",
        "",
        "* Kein Broker.",
        "* Kein Live-Trading.",
        "* Keine Orders oder Ordervorschlaege.",
        "* Keine Stueckzahl- oder Euro-Berechnung.",
        "* Keine Investitionsfreigabe oder Anlageberatung.",
        "",
        "## Eingaben",
        "",
        f"* Frequenz: {manifest.get('frequency')}",
        f"* Toleranz: {manifest.get('tolerance')}",
        f"* Warmup-Start: {manifest.get('warmup_start') or ''}",
        f"* Positionsdatei: {manifest.get('positions_file') or ''}",
        "",
        "## Stichtage",
        "",
        "| as_of | Status | Positionen | Warnungen |",
        "| --- | --- | ---: | ---: |",
    ]
    for snapshot in report.get("snapshots", []):
        if not isinstance(snapshot, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(snapshot.get("as_of")),
                    _md_cell(snapshot.get("data_status")),
                    str(len(snapshot.get("positions", []))),
                    str(len(snapshot.get("warnings", []))),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Vergleichszusammenfassung",
            "",
            (
                "| Von | Bis | Neu | Entfernt | Gemeinsam | Proposal-Wechsel | "
                "Gewichtsspruenge | Total Abs Delta | Max Abs Delta | Warnungen |"
            ),
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    comparisons = report.get("comparisons", [])
    if isinstance(comparisons, list) and comparisons:
        for comparison in comparisons:
            if not isinstance(comparison, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(comparison.get("from_as_of")),
                        _md_cell(comparison.get("to_as_of")),
                        str(comparison.get("new_symbols_count", 0)),
                        str(comparison.get("removed_symbols_count", 0)),
                        str(comparison.get("common_symbols_count", 0)),
                        str(comparison.get("proposal_change_count", 0)),
                        str(comparison.get("target_weight_jump_count", 0)),
                        _format_number(comparison.get("total_abs_weight_delta")),
                        _format_number(comparison.get("max_abs_weight_delta")),
                        str(comparison.get("warnings_count", 0)),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| _Keine Vergleiche_ |  | 0 | 0 | 0 | 0 | 0 |  |  | 0 |")

    lines.extend(
        [
            "",
            "## Proposal-Hinweis",
            "",
            (
                "Buy, Sell und Hold sind reine Delta-/Gewichtungs-Pruefsignale. "
                "Sie sind keine Kauf-, Verkaufs- oder Halteempfehlung, keine "
                "Anlageberatung und loesen keine Orders aus."
            ),
            "",
            "## Auffaelligkeiten",
            "",
        ]
    )
    warnings = report.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        for warning in warnings:
            if isinstance(warning, dict):
                lines.append(
                    f"* {warning.get('scope')}: {warning.get('reason')} - {warning.get('message')}"
                )
    else:
        lines.append("* Keine Warnungen.")

    lines.extend(
        [
            "",
            "## Grenzen",
            "",
            "* Keine Benchmark-Berechnung.",
            "* Keine Performance- oder Drawdown-Bewertung.",
            "* Keine Marktphasenlogik.",
            "* Keine Strategieparameter-Optimierung.",
            "* Keine Investitionsfreigabe.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a minimal historical paper replay.")
    parser.add_argument("--strategy-profile", default=DEFAULT_STRATEGY_PROFILE)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--start", required=True, type=_date_arg)
    parser.add_argument("--end", required=True, type=_date_arg)
    parser.add_argument("--warmup-start", type=_date_arg)
    parser.add_argument("--frequency", default=DEFAULT_FREQUENCY, choices=(DEFAULT_FREQUENCY,))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    parser.add_argument(
        "--positions-file",
        type=Path,
        help=(
            "Optional local JSON object mapping as_of dates to target weights. "
            "Missing dates are reported as data gaps."
        ),
    )
    parser.add_argument(
        "--target-weight-jump-threshold",
        type=float,
        default=DEFAULT_TARGET_WEIGHT_JUMP_THRESHOLD,
    )
    args = parser.parse_args(argv)
    _validate_inputs(
        start=args.start,
        end=args.end,
        warmup_start=args.warmup_start,
        strategy_profile=args.strategy_profile,
        frequency=args.frequency,
        tolerance=args.tolerance,
        target_weight_jump_threshold=args.target_weight_jump_threshold,
    )
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        report = run_historical_paper_replay(
            start=args.start,
            end=args.end,
            warmup_start=args.warmup_start,
            strategy_profile=args.strategy_profile,
            profile=args.profile,
            frequency=args.frequency,
            output_dir=args.output_dir,
            tolerance=args.tolerance,
            positions_file=args.positions_file,
            target_weight_jump_threshold=args.target_weight_jump_threshold,
        )
    except ReplayInputError as exc:
        print(f"Fehler: {exc}")
        return 2

    print(f"JSON report: {(args.output_dir / JSON_REPORT_NAME).as_posix()}")
    print(f"Markdown report: {(args.output_dir / MARKDOWN_REPORT_NAME).as_posix()}")
    print(f"Manifest: {(args.output_dir / MANIFEST_NAME).as_posix()}")
    print(
        "Replay: "
        f"as_of_dates={len(report['as_of_dates'])} "
        f"comparisons={len(report['comparisons'])} "
        f"warnings={len(report['warnings'])}"
    )
    return 0


def _compare_symbol(
    *,
    symbol: str,
    previous_weight: float,
    current_weight: float,
    tolerance: float,
    target_weight_jump_threshold: float,
) -> dict[str, Any]:
    delta = current_weight - previous_weight
    return {
        "symbol": symbol,
        "previous_target_weight": previous_weight,
        "current_target_weight": current_weight,
        "weight_delta": delta,
        "abs_weight_delta": abs(delta),
        "previous_proposal": classify_proposal(previous_weight, 0.0, tolerance),
        "current_proposal": classify_proposal(current_weight, previous_weight, tolerance),
        "target_weight_jump": abs(delta) >= target_weight_jump_threshold,
    }


def classify_proposal(
    target_weight: float,
    comparison_weight: float,
    tolerance: float,
) -> str:
    delta = target_weight - comparison_weight
    if delta > tolerance:
        return "Buy"
    if delta < -tolerance:
        return "Sell"
    return "Hold"


def _comparison_warnings(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for label, snapshot in [("previous", previous), ("current", current)]:
        if snapshot.get("data_status") != "ok":
            warnings.append(
                {
                    "reason": f"{label}_{snapshot.get('data_status')}",
                    "message": (
                        f"{label} snapshot {snapshot.get('as_of')} has status "
                        f"{snapshot.get('data_status')}."
                    ),
                }
            )
    return warnings


def _report_warnings(
    snapshots: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    for snapshot in snapshots:
        for warning in snapshot.get("warnings", []):
            if isinstance(warning, dict):
                warnings.append({"scope": snapshot["as_of"], **warning})
    for comparison in comparisons:
        for warning in comparison.get("warnings", []):
            if isinstance(warning, dict):
                scope = f"{comparison['from_as_of']}..{comparison['to_as_of']}"
                warnings.append({"scope": scope, **warning})
    return warnings


def _target_weights(snapshot: dict[str, Any]) -> dict[str, float]:
    value = snapshot.get("target_weights")
    if not isinstance(value, dict):
        return {}
    return {
        str(symbol): weight
        for symbol, weight in value.items()
        if isinstance(weight, int | float) and not isinstance(weight, bool)
    }


def _coerce_positions(value: object, *, context: str) -> dict[str, float]:
    if not isinstance(value, dict):
        raise ReplayInputError(f"positions for {context} must be a JSON object")
    positions: dict[str, float] = {}
    for raw_symbol, raw_weight in value.items():
        symbol = str(raw_symbol).strip().upper()
        if not symbol:
            raise ReplayInputError(f"positions for {context} contain an empty symbol")
        if isinstance(raw_weight, bool) or not isinstance(raw_weight, int | float):
            raise ReplayInputError(f"weight for {symbol} at {context} must be numeric")
        weight = float(raw_weight)
        if weight < 0:
            raise ReplayInputError(f"weight for {symbol} at {context} must be non-negative")
        positions[symbol] = weight
    return positions


def _validate_inputs(
    *,
    start: str,
    end: str,
    warmup_start: str | None,
    strategy_profile: str,
    frequency: str,
    tolerance: float,
    target_weight_jump_threshold: float,
) -> None:
    start_date = _parse_iso_date(start, "start")
    end_date = _parse_iso_date(end, "end")
    if start_date > end_date:
        raise ReplayInputError(f"start must be <= end (got {start} > {end})")
    if warmup_start is not None and _parse_iso_date(warmup_start, "warmup_start") > start_date:
        raise ReplayInputError("warmup_start must be <= start")
    if strategy_profile != DEFAULT_STRATEGY_PROFILE:
        raise ReplayInputError("only strategy profile balanced_v1 is supported in this scope")
    if frequency != DEFAULT_FREQUENCY:
        raise ReplayInputError("only monthly frequency is supported in this scope")
    if tolerance < 0:
        raise ReplayInputError("tolerance must be non-negative")
    if target_weight_jump_threshold < 0:
        raise ReplayInputError("target_weight_jump_threshold must be non-negative")


def _add_month_preserving_day(value: date, preferred_day: int) -> date:
    month_index = value.year * 12 + value.month
    year = month_index // 12
    month = month_index % 12 + 1
    day = min(preferred_day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ReplayInputError(f"{field_name} must be an ISO date YYYY-MM-DD") from exc


def _date_arg(value: str) -> str:
    try:
        return _parse_iso_date(value, "date").isoformat()
    except ReplayInputError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _format_number(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return ""
    return f"{float(value):.6f}"


def _md_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())

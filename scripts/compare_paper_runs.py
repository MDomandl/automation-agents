from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.collect_paper_run_history import extract_run_summary

DEFAULT_OUT_DIR = Path("reports") / "paper_run_comparison"
JSON_REPORT_NAME = "paper_run_comparison.json"
MARKDOWN_REPORT_NAME = "paper_run_comparison.md"
DEFAULT_MAX_JUMP_THRESHOLD = 0.05

METADATA_FIELDS = [
    ("runner_mode", "runner_mode"),
    ("strategy_profile", "strategy_profile"),
    ("profile", "profile"),
    ("as_of", "as_of"),
    ("portfolio_file", "portfolio_file"),
    ("portfolio_name", "portfolio_name"),
    ("proposal_delta_tolerance", "proposal_delta_tolerance"),
]

PROPOSAL_SOURCES = [
    ("buy_proposals", "buy"),
    ("sell_proposals", "sell"),
    ("hold_proposals", "hold"),
]


class ReportLoadError(ValueError):
    """Raised when a report cannot be loaded as a usable JSON object."""


def compare_paper_runs(
    *,
    previous_report: Path,
    current_report: Path,
    out_dir: Path = DEFAULT_OUT_DIR,
    max_jump_threshold: float = DEFAULT_MAX_JUMP_THRESHOLD,
) -> dict[str, Any]:
    previous_payload = _load_report_json(previous_report)
    current_payload = _load_report_json(current_report)

    previous_summary = extract_run_summary(previous_report, previous_payload)
    current_summary = extract_run_summary(current_report, current_payload)
    previous_symbols = _extract_symbols(previous_payload)
    current_symbols = _extract_symbols(current_payload)
    warnings = _build_warnings(
        previous_payload=previous_payload,
        current_payload=current_payload,
        previous_summary=previous_summary,
        current_summary=current_summary,
        previous_symbols=previous_symbols,
        current_symbols=current_symbols,
    )

    previous_symbol_set = set(previous_symbols)
    current_symbol_set = set(current_symbols)
    added_symbols = sorted(current_symbol_set - previous_symbol_set)
    removed_symbols = sorted(previous_symbol_set - current_symbol_set)
    common_symbols = sorted(previous_symbol_set & current_symbol_set)
    symbol_comparisons = [
        _compare_symbol(
            symbol=symbol,
            previous=previous_symbols[symbol],
            current=current_symbols[symbol],
            max_jump_threshold=max_jump_threshold,
        )
        for symbol in common_symbols
    ]

    proposal_changes_count = sum(
        1 for item in symbol_comparisons if item["proposal_changed"] is True
    )
    target_weight_changes_count = sum(
        1
        for item in symbol_comparisons
        if item["target_weight_direction"] in {"increased", "decreased"}
    )
    large_target_weight_jumps_count = sum(
        1 for item in symbol_comparisons if item["large_target_weight_jump"] is True
    )
    delta_changes_count = sum(
        1
        for item in symbol_comparisons
        if item["delta_direction"] in {"increased", "decreased"}
    )
    unchanged_symbols_count = sum(
        1
        for item in symbol_comparisons
        if item["proposal_changed"] is False
        and item["target_weight_direction"] == "unchanged"
        and item["delta_direction"] == "unchanged"
    )

    comparison = {
        "generated_at": datetime.now(UTC).isoformat(),
        "previous_report": str(previous_report),
        "current_report": str(current_report),
        "previous_run_id": previous_summary.get("run_id"),
        "current_run_id": current_summary.get("run_id"),
        "metadata_comparison": _compare_metadata(previous_summary, current_summary),
        "warnings": warnings,
        "added_symbols": added_symbols,
        "removed_symbols": removed_symbols,
        "common_symbols_count": len(common_symbols),
        "proposal_changes_count": proposal_changes_count,
        "target_weight_changes_count": target_weight_changes_count,
        "large_target_weight_jumps_count": large_target_weight_jumps_count,
        "delta_changes_count": delta_changes_count,
        "unchanged_symbols_count": unchanged_symbols_count,
        "max_jump_threshold": max_jump_threshold,
        "symbol_comparisons": symbol_comparisons,
    }
    write_outputs(comparison, out_dir)
    return comparison


def write_outputs(comparison: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / JSON_REPORT_NAME
    markdown_path = out_dir / MARKDOWN_REPORT_NAME
    json_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(build_markdown(comparison), encoding="utf-8")
    return json_path, markdown_path


def build_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# Paper-Run-Vergleich",
        "",
        f"Generiert: {comparison.get('generated_at')}",
        f"Previous Report: `{comparison.get('previous_report')}`",
        f"Current Report: `{comparison.get('current_report')}`",
        "",
        (
            "Dieser Vergleich liest nur zwei vorhandene Paper-Reports. Er erzeugt "
            "keine Handlungsempfehlung, keine Investitionsfreigabe, keine Orders, "
            "keinen Broker-Zugriff und kein Live-Trading."
        ),
        "",
        "## Metadatenvergleich",
        "",
        "| Feld | Previous | Current | Gleich |",
        "| --- | --- | --- | --- |",
    ]
    for item in comparison.get("metadata_comparison", []):
        if isinstance(item, dict):
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(item.get("field")),
                        _md_cell(item.get("previous")),
                        _md_cell(item.get("current")),
                        _yes_no(item.get("matches")),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"* Neue Symbole: {len(comparison.get('added_symbols', []))}",
            f"* Entfernte Symbole: {len(comparison.get('removed_symbols', []))}",
            f"* Gemeinsame Symbole: {comparison.get('common_symbols_count')}",
            f"* Proposal-Wechsel: {comparison.get('proposal_changes_count')}",
            f"* Zielgewichtsaenderungen: {comparison.get('target_weight_changes_count')}",
            (
                "* Auffaellige Zielgewichtsspruenge: "
                f"{comparison.get('large_target_weight_jumps_count')}"
            ),
            f"* Delta-Aenderungen: {comparison.get('delta_changes_count')}",
            f"* Unveraenderte gemeinsame Symbole: {comparison.get('unchanged_symbols_count')}",
            "",
            "## Neue Symbole",
            "",
        ]
    )
    lines.extend(_symbol_table(comparison.get("added_symbols", [])))
    lines.extend(["", "## Entfernte Symbole", ""])
    lines.extend(_symbol_table(comparison.get("removed_symbols", [])))
    lines.extend(["", "## Gemeinsame Symbole mit Aenderungen", ""])
    lines.extend(_comparison_table(comparison.get("symbol_comparisons", []), only_changed=True))
    lines.extend(["", "## Proposal-Wechsel", ""])
    lines.extend(_comparison_table(comparison.get("symbol_comparisons", []), proposal_changes=True))
    lines.extend(["", "## Auffaellige Zielgewichtsspruenge", ""])
    lines.extend(_comparison_table(comparison.get("symbol_comparisons", []), large_jumps=True))
    lines.extend(["", "## Warnungen", ""])

    warnings = comparison.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        for warning in warnings:
            if isinstance(warning, dict):
                lines.append(
                    f"* {warning.get('reason')}: {warning.get('message')}"
                )
    else:
        lines.append("* Keine Warnungen.")

    lines.extend(
        [
            "",
            "## Sicherheitsabgrenzung",
            "",
            "* Keine Handlungsempfehlung.",
            "* Keine Investitionsfreigabe.",
            "* Keine Orders.",
            "* Kein Broker.",
            "* Kein Live-Trading.",
            "* Keine Stueckzahl- oder Euro-Berechnung.",
            "* Keine Gewichtungsnormalisierung.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two existing paper_run_report.json files."
    )
    parser.add_argument("--previous-report", type=Path, required=True)
    parser.add_argument("--current-report", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--max-jump-threshold",
        type=float,
        default=DEFAULT_MAX_JUMP_THRESHOLD,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        comparison = compare_paper_runs(
            previous_report=args.previous_report,
            current_report=args.current_report,
            out_dir=args.out_dir,
            max_jump_threshold=args.max_jump_threshold,
        )
    except ReportLoadError as exc:
        print(f"Fehler: {exc}")
        return 2

    print(f"JSON report: {(args.out_dir / JSON_REPORT_NAME).as_posix()}")
    print(f"Markdown report: {(args.out_dir / MARKDOWN_REPORT_NAME).as_posix()}")
    print(
        "Comparison: "
        f"added={len(comparison['added_symbols'])} "
        f"removed={len(comparison['removed_symbols'])} "
        f"common={comparison['common_symbols_count']} "
        f"proposal_changes={comparison['proposal_changes_count']} "
        f"large_target_weight_jumps={comparison['large_target_weight_jumps_count']} "
        f"warnings={len(comparison['warnings'])}"
    )
    return 0


def _load_report_json(report_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReportLoadError(
            f"Ungueltiges JSON in {report_path}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ReportLoadError(f"Report konnte nicht gelesen werden: {report_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReportLoadError(f"Report-JSON ist kein Objekt: {report_path}")
    return payload


def _build_warnings(
    *,
    previous_payload: dict[str, Any],
    current_payload: dict[str, Any],
    previous_summary: dict[str, Any],
    current_summary: dict[str, Any],
    previous_symbols: dict[str, dict[str, Any]],
    current_symbols: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    warnings = []
    if _looks_non_paper(previous_payload):
        warnings.append(_warning("previous_not_paper", "Previous Report wirkt nicht wie paper."))
    if _looks_non_paper(current_payload):
        warnings.append(_warning("current_not_paper", "Current Report wirkt nicht wie paper."))

    warning_reasons = {
        "runner_mode": "different_runner_mode",
        "strategy_profile": "different_strategy_profile",
        "profile": "different_profile",
        "as_of": "different_as_of",
        "portfolio_file": "different_portfolio_file",
        "portfolio_name": "different_portfolio_name",
        "proposal_delta_tolerance": "different_proposal_delta_tolerance",
    }
    for item in _compare_metadata(previous_summary, current_summary):
        if item["matches"] is False:
            field = item["field"]
            warnings.append(
                _warning(
                    warning_reasons[field],
                    f"Metadaten unterscheiden sich fuer {field}.",
                )
            )

    for label, payload, symbols in [
        ("previous", previous_payload, previous_symbols),
        ("current", current_payload, current_symbols),
    ]:
        if not symbols:
            warnings.append(
                _warning(
                    f"missing_positions_{label}",
                    f"Keine Positionsdaten fuer {label} gefunden.",
                )
            )
        if not any(isinstance(payload.get(source), list) for source, _ in PROPOSAL_SOURCES):
            warnings.append(
                _warning(
                    f"missing_proposal_classes_{label}",
                    f"Keine Proposal-Klassen fuer {label} gefunden.",
                )
            )
        if not _has_any_target_weight(payload, symbols):
            warnings.append(
                _warning(
                    f"missing_target_weights_{label}",
                    f"Keine Zielgewichte fuer {label} gefunden.",
                )
            )
        if not any(_number_or_none(item.get("delta")) is not None for item in symbols.values()):
            warnings.append(
                _warning(f"missing_deltas_{label}", f"Keine Deltas fuer {label} gefunden.")
            )
    return warnings


def _compare_metadata(
    previous_summary: dict[str, Any],
    current_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    result = []
    for output_field, summary_field in METADATA_FIELDS:
        previous = previous_summary.get(summary_field)
        current = current_summary.get(summary_field)
        result.append(
            {
                "field": output_field,
                "previous": previous,
                "current": current,
                "matches": previous == current,
            }
        )
    return result


def _extract_symbols(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    symbols: dict[str, dict[str, Any]] = {}
    target_positions = payload.get("target_positions")
    if isinstance(target_positions, dict):
        for raw_symbol, raw_weight in target_positions.items():
            symbol = _symbol_or_none(raw_symbol)
            if symbol is not None:
                symbols.setdefault(symbol, {})["target_weight"] = _number_or_none(raw_weight)

    for source, proposal in PROPOSAL_SOURCES:
        rows = payload.get(source)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            symbol = _symbol_or_none(row.get("ticker") or row.get("symbol"))
            if symbol is None:
                continue
            entry = symbols.setdefault(symbol, {})
            entry["proposal"] = proposal
            entry["comparison_weight"] = _first_number(
                row,
                ["previous_weight", "comparison_weight", "actual_weight", "reference_weight"],
            )
            if entry.get("target_weight") is None:
                entry["target_weight"] = _first_number(row, ["target_weight"])
            entry["delta"] = _first_number(row, ["delta_weight", "delta"])
    return symbols


def _compare_symbol(
    *,
    symbol: str,
    previous: dict[str, Any],
    current: dict[str, Any],
    max_jump_threshold: float,
) -> dict[str, Any]:
    previous_target = _number_or_none(previous.get("target_weight"))
    current_target = _number_or_none(current.get("target_weight"))
    previous_delta = _number_or_none(previous.get("delta"))
    current_delta = _number_or_none(current.get("delta"))
    target_change = _change(previous_target, current_target)
    delta_change = _change(previous_delta, current_delta)
    previous_proposal = previous.get("proposal")
    current_proposal = current.get("proposal")
    return {
        "symbol": symbol,
        "previous_target_weight": previous_target,
        "current_target_weight": current_target,
        "target_weight_change": target_change,
        "previous_comparison_weight": _number_or_none(previous.get("comparison_weight")),
        "current_comparison_weight": _number_or_none(current.get("comparison_weight")),
        "previous_delta": previous_delta,
        "current_delta": current_delta,
        "delta_change": delta_change,
        "previous_proposal": previous_proposal,
        "current_proposal": current_proposal,
        "proposal_changed": (
            None
            if previous_proposal is None or current_proposal is None
            else previous_proposal != current_proposal
        ),
        "target_weight_direction": _direction(target_change),
        "delta_direction": _direction(delta_change),
        "large_target_weight_jump": (
            abs(target_change) >= max_jump_threshold if target_change is not None else False
        ),
    }


def _looks_non_paper(payload: dict[str, Any]) -> bool:
    runner_mode = payload.get("runner_mode")
    return runner_mode is not None and runner_mode != "paper"


def _has_any_target_weight(
    payload: dict[str, Any],
    symbols: dict[str, dict[str, Any]],
) -> bool:
    target_positions = payload.get("target_positions")
    if isinstance(target_positions, dict) and target_positions:
        return True
    return any(_number_or_none(item.get("target_weight")) is not None for item in symbols.values())


def _comparison_table(
    rows: object,
    *,
    only_changed: bool = False,
    proposal_changes: bool = False,
    large_jumps: bool = False,
) -> list[str]:
    lines = [
        (
            "| Symbol | Prev Target | Curr Target | Target Change | Prev Delta | "
            "Curr Delta | Delta Change | Prev Proposal | Curr Proposal | Hinweis |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    added = 0
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            if proposal_changes and row.get("proposal_changed") is not True:
                continue
            if large_jumps and row.get("large_target_weight_jump") is not True:
                continue
            if only_changed and not _row_changed(row):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(row.get("symbol")),
                        _format_number(row.get("previous_target_weight")),
                        _format_number(row.get("current_target_weight")),
                        _format_number(row.get("target_weight_change")),
                        _format_number(row.get("previous_delta")),
                        _format_number(row.get("current_delta")),
                        _format_number(row.get("delta_change")),
                        _md_cell(row.get("previous_proposal")),
                        _md_cell(row.get("current_proposal")),
                        _md_cell("jump" if row.get("large_target_weight_jump") else ""),
                    ]
                )
                + " |"
            )
            added += 1
    if added == 0:
        lines.append("| _Keine_ |  |  |  |  |  |  |  |  |  |")
    return lines


def _symbol_table(symbols: object) -> list[str]:
    lines = ["| Symbol |", "| --- |"]
    if isinstance(symbols, list) and symbols:
        for symbol in symbols:
            lines.append(f"| {_md_cell(symbol)} |")
    else:
        lines.append("| _Keine_ |")
    return lines


def _row_changed(row: dict[str, Any]) -> bool:
    return (
        row.get("proposal_changed") is True
        or row.get("target_weight_direction") not in {"unchanged", "unknown"}
        or row.get("delta_direction") not in {"unchanged", "unknown"}
    )


def _first_number(row: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        value = _number_or_none(row.get(key))
        if value is not None:
            return value
    return None


def _change(previous: float | None, current: float | None) -> float | None:
    if previous is None or current is None:
        return None
    return current - previous


def _direction(change: float | None) -> str:
    if change is None:
        return "unknown"
    if change > 0:
        return "increased"
    if change < 0:
        return "decreased"
    return "unchanged"


def _number_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _symbol_or_none(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    symbol = value.strip().upper()
    return symbol or None


def _warning(reason: str, message: str) -> dict[str, str]:
    return {"reason": reason, "message": message}


def _format_number(value: object) -> str:
    number = _number_or_none(value)
    if number is None:
        return ""
    return f"{number:.6f}"


def _md_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


def _yes_no(value: object) -> str:
    return "ja" if value is True else "nein"


if __name__ == "__main__":
    raise SystemExit(main())

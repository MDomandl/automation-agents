from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_RUNS_DIR = Path("automation_runs")
DEFAULT_OUT_DIR = Path("reports") / "paper_run_history"
REPORT_NAME = "paper_run_report.json"


def collect_paper_run_history(
    *,
    runs_dir: Path = DEFAULT_RUNS_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
    strategy_profile: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    report_paths = sorted(runs_dir.rglob(REPORT_NAME)) if runs_dir.exists() else []
    warnings: list[dict[str, str]] = []
    runs: list[dict[str, Any]] = []
    skipped = 0

    if not runs_dir.exists():
        warnings.append(
            {
                "path": str(runs_dir),
                "reason": "runs_dir_not_found",
                "message": "Run-Basisverzeichnis nicht gefunden.",
            }
        )

    for report_path in report_paths:
        payload = _read_report_json(report_path, warnings)
        if payload is None:
            skipped += 1
            continue

        if not _is_paper_report(payload):
            skipped += 1
            warnings.append(
                {
                    "path": str(report_path),
                    "reason": "not_paper_report",
                    "message": "Report wurde nicht als Paper-Report erkannt.",
                }
            )
            continue

        summary = extract_run_summary(report_path, payload)

        if strategy_profile is not None and summary["strategy_profile"] is None:
            skipped += 1
            warnings.append(
                {
                    "path": str(report_path),
                    "reason": "missing_strategy_profile_for_filter",
                    "message": "Strategieprofil fehlt; Filter konnte nicht geprueft werden.",
                }
            )
            continue
        if strategy_profile is not None and summary["strategy_profile"] != strategy_profile:
            skipped += 1
            continue

        if profile is not None and summary["profile"] is None:
            skipped += 1
            warnings.append(
                {
                    "path": str(report_path),
                    "reason": "missing_profile_for_filter",
                    "message": "Profil fehlt; Filter konnte nicht geprueft werden.",
                }
            )
            continue
        if profile is not None and summary["profile"] != profile:
            skipped += 1
            continue

        runs.append(summary)

    history = {
        "generated_at": datetime.now(UTC).isoformat(),
        "runs_dir": str(runs_dir),
        "total_reports_found": len(report_paths),
        "total_reports_included": len(runs),
        "total_reports_skipped": skipped,
        "warnings": warnings,
        "runs": runs,
    }
    write_outputs(history, out_dir)
    return history


def extract_run_summary(report_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    run_dir = report_path.parent
    run_label = _string_or_none(payload.get("run_label")) or run_dir.name
    profile = _string_or_none(payload.get("profile")) or _derive_profile_from_run_label(run_label)
    target_positions = payload.get("target_positions")
    proposals_count = _len_if_list(payload.get("buy_proposals"))
    proposals_count += _len_if_list(payload.get("sell_proposals"))
    proposals_count += _len_if_list(payload.get("hold_proposals"))

    return {
        "report_path": str(report_path),
        "run_dir": str(run_dir),
        "run_id": _string_or_none(payload.get("run_id")) or run_label,
        "run_label": run_label,
        "profile": profile,
        "strategy_profile": _string_or_none(payload.get("strategy_profile_name")),
        "strategy_profile_label": _string_or_none(payload.get("strategy_profile_label")),
        "runner_mode": _string_or_none(payload.get("runner_mode")),
        "as_of": _string_or_none(payload.get("as_of")),
        "portfolio_source": _string_or_none(payload.get("portfolio_source")),
        "portfolio_file": _string_or_none(payload.get("portfolio_file")),
        "portfolio_file_name": _string_or_none(payload.get("portfolio_file_name")),
        "portfolio_file_display": _string_or_none(payload.get("portfolio_file_display")),
        "portfolio_name": _string_or_none(payload.get("portfolio_name")),
        "proposal_delta_tolerance": payload.get("proposal_delta_tolerance"),
        "buy_proposals_count": _len_if_list(payload.get("buy_proposals")),
        "sell_proposals_count": _len_if_list(payload.get("sell_proposals")),
        "hold_proposals_count": _len_if_list(payload.get("hold_proposals")),
        "positions_count": len(target_positions) if isinstance(target_positions, dict) else 0,
        "proposal_rows_count": proposals_count,
        "has_portfolio_checks": isinstance(payload.get("portfolio_checks"), dict),
        "has_safety_fields": _has_safety_fields(payload),
        "has_human_review": isinstance(payload.get("human_review_required"), dict),
    }


def write_outputs(history: dict[str, Any], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "paper_run_history.json"
    md_path = out_dir / "paper_run_history.md"
    json_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(build_markdown(history), encoding="utf-8")
    return json_path, md_path


def build_markdown(history: dict[str, Any]) -> str:
    runs = history.get("runs", [])
    warnings = history.get("warnings", [])
    lines = [
        "# Paper-Run-History",
        "",
        f"Generiert: {history.get('generated_at')}",
        f"Basisverzeichnis: `{history.get('runs_dir')}`",
        "",
        f"Gefundene Reports: {history.get('total_reports_found')}",
        f"Einbezogene Reports: {history.get('total_reports_included')}",
        f"Uebersprungene Reports: {history.get('total_reports_skipped')}",
        "",
        (
            "Diese Auswertung liest nur bestehende Paper-Reports. Sie startet keine "
            "Paper-Runs und erzeugt keine Ausfuehrungslogik."
        ),
        "",
        "## Runs",
        "",
        (
            "| Run | Profil | Strategieprofil | Modus | as_of | Portfolio | Buy | Sell | "
            "Hold | Checks | Safety | Review |"
        ),
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    if isinstance(runs, list) and runs:
        for run in runs:
            if not isinstance(run, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(run.get("run_label")),
                        _md_cell(run.get("profile")),
                        _md_cell(run.get("strategy_profile")),
                        _md_cell(run.get("runner_mode")),
                        _md_cell(run.get("as_of")),
                        _md_cell(
                            run.get("portfolio_name")
                            or run.get("portfolio_file_display")
                            or run.get("portfolio_source")
                        ),
                        str(run.get("buy_proposals_count", 0)),
                        str(run.get("sell_proposals_count", 0)),
                        str(run.get("hold_proposals_count", 0)),
                        _yes_no(run.get("has_portfolio_checks")),
                        _yes_no(run.get("has_safety_fields")),
                        _yes_no(run.get("has_human_review")),
                    ]
                )
                + " |"
            )
    else:
        lines.append(
            "| _Keine einbezogenen Paper-Reports_ |  |  |  |  |  | "
            "0 | 0 | 0 | nein | nein | nein |"
        )

    if isinstance(warnings, list) and warnings:
        lines.extend(["", "## Warnungen und uebersprungene Reports", ""])
        for warning in warnings:
            if isinstance(warning, dict):
                lines.append(
                    f"* `{warning.get('path')}`: {warning.get('reason')} - {warning.get('message')}"
                )

    lines.extend(
        [
            "",
            "## Sicherheitsabgrenzung",
            "",
            "* Keine Orders.",
            "* Kein Broker.",
            "* Kein Live-Trading.",
            "* Keine Investitionsfreigabe.",
            "* Keine Stueckzahl- oder Euro-Berechnung.",
            "* Keine Gewichtungsnormalisierung.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect an overview from existing paper_run_report.json files."
    )
    parser.add_argument("--runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--strategy-profile")
    parser.add_argument("--profile")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    history = collect_paper_run_history(
        runs_dir=args.runs_dir,
        out_dir=args.out_dir,
        strategy_profile=args.strategy_profile,
        profile=args.profile,
    )
    print(f"JSON report: {(args.out_dir / 'paper_run_history.json').as_posix()}")
    print(f"Markdown report: {(args.out_dir / 'paper_run_history.md').as_posix()}")
    print(
        "Reports: "
        f"found={history['total_reports_found']} "
        f"included={history['total_reports_included']} "
        f"skipped={history['total_reports_skipped']}"
    )
    return 0


def _read_report_json(report_path: Path, warnings: list[dict[str, str]]) -> dict[str, Any] | None:
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        warnings.append(
            {
                "path": str(report_path),
                "reason": "invalid_json",
                "message": f"Ungueltiges JSON: {exc.msg}",
            }
        )
        return None
    except OSError as exc:
        warnings.append(
            {
                "path": str(report_path),
                "reason": "read_error",
                "message": str(exc),
            }
        )
        return None
    if not isinstance(payload, dict):
        warnings.append(
            {
                "path": str(report_path),
                "reason": "invalid_report_shape",
                "message": "Report-JSON ist kein Objekt.",
            }
        )
        return None
    return payload


def _is_paper_report(payload: dict[str, Any]) -> bool:
    if payload.get("runner_mode") != "paper":
        return False
    return (
        payload.get("orders_executed") is False
        or payload.get("broker_connected") is False
        or payload.get("live_trading_enabled") is False
        or isinstance(payload.get("human_review_required"), dict)
    )


def _has_safety_fields(payload: dict[str, Any]) -> bool:
    execution = payload.get("execution")
    execution_safety = (
        isinstance(execution, dict)
        and execution.get("orders_executed") is False
        and execution.get("broker_connected") is False
        and execution.get("live_trading_enabled") is False
    )
    return (
        payload.get("orders_executed") is False
        and payload.get("broker_connected") is False
        and payload.get("live_trading_enabled") is False
        and execution_safety
    )


def _derive_profile_from_run_label(run_label: str | None) -> str | None:
    if not run_label:
        return None
    parts = run_label.split("_")
    if parts and parts[-1] == "paper" and len(parts) >= 2:
        return parts[-2]
    if parts:
        return parts[-1]
    return None


def _len_if_list(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _yes_no(value: object) -> str:
    return "ja" if value is True else "nein"


def _md_cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())

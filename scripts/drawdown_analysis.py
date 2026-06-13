from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

SNAPSHOT_NOTE = (
    "Positions are based on rebalance snapshots, not daily holdings. They indicate exposures "
    "present during the drawdown window but do not provide exact ticker-level drawdown attribution."
)
ATTRIBUTION_NOTE = (
    "Drawdown contribution by ticker is not computed because daily ticker-level returns and daily "
    "portfolio weights are not available in these artifacts."
)


def build_drawdown_report(
    *,
    matrix_summary_path: Path,
    strategy_profile: str = "balanced_v1",
    top_n: int = 3,
    generated_at: str | None = None,
) -> dict[str, Any]:
    matrix_summary = _load_json(matrix_summary_path)
    runs = _runs_for_profile(matrix_summary, strategy_profile)
    if not runs:
        raise ValueError(f"No runs found for strategy profile: {strategy_profile}")

    warnings: list[str] = []
    phases = []
    for run in runs:
        phase = analyze_phase_run(run, top_n=top_n, warnings=warnings)
        phases.append(phase)

    return {
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "strategy_profile": strategy_profile,
        "matrix_summary": str(matrix_summary_path),
        "top_n": top_n,
        "phases": phases,
        "warnings": warnings,
    }


def analyze_phase_run(
    run: dict[str, Any],
    *,
    top_n: int,
    warnings: list[str],
) -> dict[str, Any]:
    phase_name = _str_or_default(run.get("phase_name"), "unknown")
    phase_start = _str_or_default(run.get("phase_start"), "")
    phase_end = _str_or_default(run.get("phase_end"), "")
    run_id = _str_or_none(run.get("run_id"))
    run_dir = _str_or_none(run.get("run_dir"))
    manifest_path = _path_or_none(run.get("manifest_path"))
    manifest = _load_manifest(manifest_path, warnings, phase_name)
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}

    phase = {
        "phase": phase_name,
        "phase_start": phase_start,
        "phase_end": phase_end,
        "run_id": run_id,
        "run_dir": run_dir,
        "benchmark_column": None,
        "drawdowns": [],
        "warnings": [],
    }

    start = _parse_date(phase_start)
    end = _parse_date(phase_end)
    if start is None or end is None:
        _warn(warnings, phase, f"{phase_name}: invalid phase window.")
        return phase

    artifact_paths = _artifact_paths(artifacts, run_dir)
    equity_path = artifact_paths["equity"]
    if equity_path is None or not equity_path.exists():
        _warn(warnings, phase, f"{phase_name}: missing equity artifact.")
        return phase

    equity = load_series(equity_path, "date", "equity", start=start, end=end)
    if len(equity) < 2:
        _warn(warnings, phase, f"{phase_name}: equity segment too short.")
        return phase

    benchmark_path = artifact_paths["benchmark"]
    benchmark: list[tuple[datetime, float]] = []
    benchmark_column = None
    if benchmark_path is None or not benchmark_path.exists():
        _warn(warnings, phase, f"{phase_name}: missing benchmark artifact.")
    else:
        benchmark_column = benchmark_column_from_csv(benchmark_path)
        phase["benchmark_column"] = benchmark_column
        if benchmark_column is None:
            _warn(warnings, phase, f"{phase_name}: benchmark BM1_ column not found.")
        else:
            benchmark = load_series(benchmark_path, "date", benchmark_column, start=start, end=end)

    positions_rows = _artifact_rows(
        artifact_paths["positions"], warnings, phase, phase_name, "positions"
    )
    trades_rows = _artifact_rows(artifact_paths["trades"], warnings, phase, phase_name, "trades")

    benchmark_dd = compute_drawdown_series(benchmark)
    for rank, episode in enumerate(detect_drawdown_episodes(equity, top_n=top_n), start=1):
        drawdown_end = episode["drawdown_recovery"] or phase_end
        enriched = {
            "rank": rank,
            **episode,
            **benchmark_comparison(
                episode,
                benchmark_dd=benchmark_dd,
                window_end=_parse_date(drawdown_end),
            ),
            "positions": analyze_positions(
                positions_rows,
                drawdown_start=_parse_date(episode["drawdown_start"]),
                drawdown_end=_parse_date(drawdown_end),
                top_n=top_n,
            ),
            "trades": analyze_trades(
                trades_rows,
                drawdown_start=_parse_date(episode["drawdown_start"]),
                drawdown_end=_parse_date(drawdown_end),
            ),
        }
        phase["drawdowns"].append(enriched)
    return phase


def compute_drawdown_series(series: list[tuple[datetime, float]]) -> list[dict[str, Any]]:
    if not series:
        return []
    peak = series[0][1]
    rows = []
    for date_value, value in series:
        peak = max(peak, value)
        drawdown = value / peak - 1.0 if peak else 0.0
        rows.append({"date": date_value, "value": value, "drawdown": drawdown})
    return rows


def detect_drawdown_episodes(
    series: list[tuple[datetime, float]],
    *,
    top_n: int = 3,
) -> list[dict[str, Any]]:
    episodes = []
    peak_index = 0
    peak_value = series[0][1]
    active: dict[str, Any] | None = None

    for index, (date_value, value) in enumerate(series):
        if active is None:
            if value >= peak_value:
                peak_value = value
                peak_index = index
                continue
            active = {
                "start_index": peak_index,
                "start_date": series[peak_index][0],
                "peak_value": peak_value,
                "trough_index": index,
                "trough_date": date_value,
                "trough_value": value,
                "end_index": index,
                "recovery_date": None,
            }
            continue

        active["end_index"] = index
        if value < active["trough_value"]:
            active["trough_index"] = index
            active["trough_date"] = date_value
            active["trough_value"] = value
        if value >= active["peak_value"]:
            active["recovery_date"] = date_value
            episodes.append(_format_episode(active))
            active = None
            peak_index = index
            peak_value = value
        elif value > peak_value:
            peak_index = index
            peak_value = value

    if active is not None:
        episodes.append(_format_episode(active))

    return sorted(episodes, key=lambda item: item["drawdown_depth"])[:top_n]


def benchmark_column_from_csv(path: Path | None) -> str | None:
    rows = read_csv_rows(path)
    if not rows:
        return None
    for column in rows[0]:
        if column.startswith("BM1_"):
            return column
    return None


def benchmark_comparison(
    episode: dict[str, Any],
    *,
    benchmark_dd: list[dict[str, Any]],
    window_end: datetime | None,
) -> dict[str, Any]:
    if not benchmark_dd:
        return {
            "benchmark_drawdown_at_portfolio_trough": None,
            "benchmark_max_drawdown_same_window": None,
            "benchmark_trough_same_window": None,
            "drawdown_vs_benchmark_at_trough": None,
            "drawdown_vs_benchmark_window": None,
        }

    start = _parse_date(episode["drawdown_start"])
    trough = _parse_date(episode["drawdown_trough"])
    if start is None or trough is None or window_end is None:
        return benchmark_comparison({}, benchmark_dd=[], window_end=None)

    at_trough = next((row["drawdown"] for row in benchmark_dd if row["date"] == trough), None)
    window_rows = [row for row in benchmark_dd if start <= row["date"] <= window_end]
    if not window_rows:
        bm_max = None
        bm_trough = None
    else:
        trough_row = min(window_rows, key=lambda row: row["drawdown"])
        bm_max = trough_row["drawdown"]
        bm_trough = trough_row["date"].date().isoformat()

    return {
        "benchmark_drawdown_at_portfolio_trough": _pct_points(at_trough),
        "benchmark_max_drawdown_same_window": _pct_points(bm_max),
        "benchmark_trough_same_window": bm_trough,
        "drawdown_vs_benchmark_at_trough": _pct_points(
            None if at_trough is None else episode["drawdown_depth"] / 100.0 - at_trough
        ),
        "drawdown_vs_benchmark_window": _pct_points(
            None if bm_max is None else episode["drawdown_depth"] / 100.0 - bm_max
        ),
    }


def analyze_positions(
    rows: list[dict[str, str]],
    *,
    drawdown_start: datetime | None,
    drawdown_end: datetime | None,
    top_n: int,
) -> dict[str, Any]:
    empty = {
        "snapshot_count": 0,
        "used_pre_drawdown_snapshot": False,
        "top_tickers": [],
        "sector_exposure": [],
        "concentration": _empty_concentration(),
    }
    if drawdown_start is None or drawdown_end is None or not rows:
        return empty

    parsed = []
    for row in rows:
        as_of = _parse_date(row.get("as_of"))
        if as_of is not None:
            parsed.append((as_of, row))

    selected = [(as_of, row) for as_of, row in parsed if drawdown_start <= as_of <= drawdown_end]
    used_pre = False
    if not selected:
        previous = [(as_of, row) for as_of, row in parsed if as_of < drawdown_start]
        if previous:
            latest = max(as_of for as_of, _ in previous)
            selected = [(as_of, row) for as_of, row in previous if as_of == latest]
            used_pre = True
    if not selected:
        return empty

    snapshot_dates = sorted({as_of for as_of, _ in selected})
    return {
        "snapshot_count": len(snapshot_dates),
        "used_pre_drawdown_snapshot": used_pre,
        "top_tickers": _ticker_aggregation(selected, top_n=top_n),
        "sector_exposure": _sector_aggregation(selected),
        "concentration": _concentration(selected),
    }


def analyze_trades(
    rows: list[dict[str, str]],
    *,
    drawdown_start: datetime | None,
    drawdown_end: datetime | None,
) -> dict[str, Any]:
    empty = {
        "trade_count": 0,
        "turnover_sum": 0,
        "turnover_avg": None,
        "trade_cost_sum": 0,
        "enter": [],
        "exit": [],
    }
    if drawdown_start is None or drawdown_end is None or not rows:
        return empty
    selected = []
    for row in rows:
        date_value = _parse_date(row.get("date"))
        if date_value is not None and drawdown_start <= date_value <= drawdown_end:
            selected.append(row)
    if not selected:
        return empty

    turnovers = [_parse_float(row.get("turnover")) or 0.0 for row in selected]
    costs = [_parse_float(row.get("trade_cost")) or 0.0 for row in selected]
    return {
        "trade_count": len(selected),
        "turnover_sum": sum(turnovers),
        "turnover_avg": sum(turnovers) / len(turnovers) if turnovers else None,
        "trade_cost_sum": sum(costs),
        "enter": [value for row in selected if (value := _clean_text(row.get("enter")))],
        "exit": [value for row in selected if (value := _clean_text(row.get("exit")))],
    }


def load_series(
    path: Path,
    date_column: str,
    value_column: str,
    *,
    start: datetime,
    end: datetime,
) -> list[tuple[datetime, float]]:
    segment = []
    for row in read_csv_rows(path):
        date_value = _parse_date(row.get(date_column))
        value = _parse_float(row.get(value_column))
        if date_value is not None and value is not None and start <= date_value <= end:
            segment.append((date_value, value))
    return sorted(segment, key=lambda item: item[0])


def read_csv_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    lines = [
        line
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if not line.startswith("#")
    ]
    if not lines:
        return []
    return list(csv.DictReader(lines))


def build_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        f"# Drawdown Analysis - {report['strategy_profile']}",
        "",
        f"Generated at: {report['generated_at']}",
        "",
        SNAPSHOT_NOTE,
        "",
        ATTRIBUTION_NOTE,
        "",
        "## Summary",
        _md_table(
            (
                "Phase",
                "Worst DD",
                "Start",
                "Trough",
                "Recovery",
                "Benchmark DD same window",
                "DD vs Benchmark",
                "Recovered",
            ),
            tuple(_summary_row(phase) for phase in report["phases"]),
        ),
        "",
    ]
    for phase in report["phases"]:
        lines.extend(_phase_markdown(phase))
    if report.get("warnings"):
        lines.extend(["## Warnings", *[f"- {warning}" for warning in report["warnings"]], ""])
    return "\n".join(lines)


def write_reports(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = str(report["strategy_profile"])
    json_path = output_dir / f"{profile}_drawdown_analysis.json"
    md_path = output_dir / f"{profile}_drawdown_analysis.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(build_markdown_report(report), encoding="utf-8")
    return md_path, json_path


def _format_episode(active: dict[str, Any]) -> dict[str, Any]:
    depth = active["trough_value"] / active["peak_value"] - 1.0 if active["peak_value"] else 0.0
    return {
        "drawdown_start": active["start_date"].date().isoformat(),
        "drawdown_trough": active["trough_date"].date().isoformat(),
        "drawdown_recovery": (
            None if active["recovery_date"] is None else active["recovery_date"].date().isoformat()
        ),
        "drawdown_depth": _pct_points(depth),
        "drawdown_duration_days": (active["trough_date"] - active["start_date"]).days,
        "drawdown_duration_observations": active["end_index"] - active["start_index"] + 1,
        "recovered": active["recovery_date"] is not None,
    }


def _ticker_aggregation(
    selected: list[tuple[datetime, dict[str, str]]],
    *,
    top_n: int,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for _, row in selected:
        ticker = _str_or_default(row.get("ticker"), "UNKNOWN")
        grouped.setdefault(ticker, []).append(row)

    rows = []
    for ticker, group in grouped.items():
        weights = [_parse_float(row.get("weight")) for row in group]
        ranks = [_parse_float(row.get("rank")) for row in group]
        scores = [_parse_float(row.get("score")) for row in group]
        rows.append(
            {
                "ticker": ticker,
                "sector": _str_or_default(group[0].get("sector"), "Unknown"),
                "snapshot_count": len(group),
                "avg_weight": _pct_points(_avg(weights)),
                "max_weight": _pct_points(_max(weights)),
                "avg_rank": _avg(ranks),
                "min_rank": _min(ranks),
                "avg_score": _avg(scores),
                "max_score": _max(scores),
            }
        )
    return sorted(
        rows,
        key=lambda row: (row["avg_weight"] or 0.0, row["snapshot_count"]),
        reverse=True,
    )[:top_n]


def _sector_aggregation(selected: list[tuple[datetime, dict[str, str]]]) -> list[dict[str, Any]]:
    per_snapshot: dict[datetime, dict[str, float]] = {}
    for as_of, row in selected:
        sector = _str_or_default(row.get("sector"), "Unknown")
        weight = _parse_float(row.get("weight")) or 0.0
        per_snapshot.setdefault(as_of, {})
        per_snapshot[as_of][sector] = per_snapshot[as_of].get(sector, 0.0) + weight

    sectors = sorted({sector for snapshot in per_snapshot.values() for sector in snapshot})
    result = []
    for sector in sectors:
        values = [snapshot[sector] for snapshot in per_snapshot.values() if sector in snapshot]
        result.append(
            {
                "sector": sector,
                "snapshot_count": len(values),
                "avg_weight_sum": _pct_points(sum(values) / len(values) if values else None),
                "max_weight_sum": _pct_points(max(values) if values else None),
            }
        )
    return sorted(result, key=lambda row: row["avg_weight_sum"] or 0.0, reverse=True)


def _concentration(selected: list[tuple[datetime, dict[str, str]]]) -> dict[str, Any]:
    by_snapshot: dict[datetime, list[dict[str, str]]] = {}
    for as_of, row in selected:
        by_snapshot.setdefault(as_of, []).append(row)
    if not by_snapshot:
        return _empty_concentration()

    position_counts = []
    top1_weights = []
    top3_weights = []
    single_weights = []
    max_sector_weights = []
    for rows in by_snapshot.values():
        weights = sorted([_parse_float(row.get("weight")) or 0.0 for row in rows], reverse=True)
        position_counts.append(len(rows))
        top1_weights.append(weights[0] if weights else 0.0)
        top3_weights.append(sum(weights[:3]))
        single_weights.extend(weights)
        sector_weights: dict[str, float] = {}
        for row in rows:
            sector = _str_or_default(row.get("sector"), "Unknown")
            sector_weights[sector] = sector_weights.get(sector, 0.0) + (
                _parse_float(row.get("weight")) or 0.0
            )
        max_sector_weights.append(max(sector_weights.values()) if sector_weights else 0.0)

    return {
        "avg_position_count": _avg(position_counts),
        "min_position_count": _min(position_counts),
        "max_position_count": _max(position_counts),
        "avg_top1_weight": _pct_points(_avg(top1_weights)),
        "avg_top3_weight": _pct_points(_avg(top3_weights)),
        "max_single_weight": _pct_points(_max(single_weights)),
        "avg_max_sector_weight": _pct_points(_avg(max_sector_weights)),
        "max_sector_weight": _pct_points(_max(max_sector_weights)),
    }


def _empty_concentration() -> dict[str, Any]:
    return {
        "avg_position_count": None,
        "min_position_count": None,
        "max_position_count": None,
        "avg_top1_weight": None,
        "avg_top3_weight": None,
        "max_single_weight": None,
        "avg_max_sector_weight": None,
        "max_sector_weight": None,
    }


def _phase_markdown(phase: dict[str, Any]) -> list[str]:
    lines = [
        f"## Phase: {phase['phase']}",
        "",
        "### Top Drawdowns",
        _md_table(
            (
                "Rank",
                "Start",
                "Trough",
                "Recovery",
                "Depth",
                "Days",
                "Observations",
                "BM at Trough",
                "BM max same window",
                "DD vs BM",
            ),
            tuple(_drawdown_row(drawdown) for drawdown in phase["drawdowns"]),
        ),
        "",
    ]
    if phase["drawdowns"]:
        worst = phase["drawdowns"][0]
        positions = worst["positions"]
        trades = worst["trades"]
        lines.extend(
            [
                "### Positions during worst drawdown",
                "",
                "#### Top Tickers",
                _md_table(
                    ("Ticker", "Sector", "Snapshots", "Avg Weight", "Max Weight", "Avg Rank"),
                    tuple(_ticker_row(row) for row in positions["top_tickers"]),
                ),
                "",
                "#### Sector Exposure",
                _md_table(
                    ("Sector", "Snapshots", "Avg Weight Sum", "Max Weight Sum"),
                    tuple(_sector_row(row) for row in positions["sector_exposure"]),
                ),
                "",
                "#### Concentration",
                _md_table(
                    ("Metric", "Value"),
                    tuple(
                        (key, _fmt_value(value, pct="weight" in key))
                        for key, value in positions["concentration"].items()
                    ),
                ),
                "",
                "### Trades during worst drawdown",
                _md_table(
                    ("Metric", "Value"),
                    tuple((key, _display(value)) for key, value in trades.items()),
                ),
                "",
            ]
        )
    return lines


def _summary_row(phase: dict[str, Any]) -> tuple[object, ...]:
    if not phase["drawdowns"]:
        return (phase["phase"], "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a")
    worst = phase["drawdowns"][0]
    return (
        phase["phase"],
        _fmt_pct(worst["drawdown_depth"]),
        worst["drawdown_start"],
        worst["drawdown_trough"],
        worst["drawdown_recovery"] or "n/a",
        _fmt_pct(worst["benchmark_max_drawdown_same_window"]),
        _fmt_pct(worst["drawdown_vs_benchmark_window"]),
        str(worst["recovered"]).lower(),
    )


def _drawdown_row(drawdown: dict[str, Any]) -> tuple[object, ...]:
    return (
        drawdown["rank"],
        drawdown["drawdown_start"],
        drawdown["drawdown_trough"],
        drawdown["drawdown_recovery"] or "n/a",
        _fmt_pct(drawdown["drawdown_depth"]),
        drawdown["drawdown_duration_days"],
        drawdown["drawdown_duration_observations"],
        _fmt_pct(drawdown["benchmark_drawdown_at_portfolio_trough"]),
        _fmt_pct(drawdown["benchmark_max_drawdown_same_window"]),
        _fmt_pct(drawdown["drawdown_vs_benchmark_window"]),
    )


def _ticker_row(row: dict[str, Any]) -> tuple[object, ...]:
    return (
        row["ticker"],
        row["sector"],
        row["snapshot_count"],
        _fmt_pct(row["avg_weight"]),
        _fmt_pct(row["max_weight"]),
        _fmt_num(row["avg_rank"]),
    )


def _sector_row(row: dict[str, Any]) -> tuple[object, ...]:
    return (
        row["sector"],
        row["snapshot_count"],
        _fmt_pct(row["avg_weight_sum"]),
        _fmt_pct(row["max_weight_sum"]),
    )


def _artifact_rows(
    path: Path | None,
    warnings: list[str],
    phase: dict[str, Any],
    phase_name: str,
    artifact_name: str,
) -> list[dict[str, str]]:
    if path is None or not path.exists():
        _warn(warnings, phase, f"{phase_name}: missing {artifact_name} artifact.")
        return []
    return read_csv_rows(path)


def _artifact_paths(artifacts: dict[str, Any], run_dir: str | None) -> dict[str, Path | None]:
    root = Path(run_dir) / "aktien_oop" if run_dir else None
    return {
        "equity": _path_or_none(artifacts.get("equity"))
        or _fallback(root, "bt_monthly_15x3_equity_curve.csv"),
        "benchmark": _path_or_none(artifacts.get("bench"))
        or _path_or_none(artifacts.get("benchmark"))
        or _fallback(root, "bt_monthly_15x3_benchmark.csv"),
        "positions": _path_or_none(artifacts.get("positions"))
        or _fallback(root, "bt_monthly_15x3_positions.csv"),
        "trades": _path_or_none(artifacts.get("trades"))
        or _fallback(root, "bt_monthly_15x3_trades.csv"),
    }


def _fallback(root: Path | None, name: str) -> Path | None:
    return None if root is None else root / name


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Matrix summary not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Matrix summary must be a JSON object: {path}")
    return payload


def _load_manifest(path: Path | None, warnings: list[str], phase_name: str) -> dict[str, Any]:
    if path is None or not path.exists():
        warnings.append(f"{phase_name}: missing run_manifest.json.")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"{phase_name}: could not read run_manifest.json: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def _runs_for_profile(
    matrix_summary: dict[str, Any],
    strategy_profile: str,
) -> list[dict[str, Any]]:
    matrix = matrix_summary.get("matrix")
    if not isinstance(matrix, list):
        return []
    return [
        row
        for row in matrix
        if isinstance(row, dict) and row.get("strategy_profile") == strategy_profile
    ]


def _warn(warnings: list[str], phase: dict[str, Any], message: str) -> None:
    warnings.append(message)
    phase["warnings"].append(message)


def _md_table(headers: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_display(value) for value in row) + " |")
    return "\n".join(lines)


def _display(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "[]"
    return str(value)


def _fmt_pct(value: object) -> str:
    numeric = _parse_float(value)
    return "n/a" if numeric is None else f"{numeric:.2f}%"


def _fmt_num(value: object) -> str:
    numeric = _parse_float(value)
    return "n/a" if numeric is None else f"{numeric:.2f}"


def _fmt_value(value: object, *, pct: bool = False) -> str:
    return _fmt_pct(value) if pct else _fmt_num(value)


def _parse_date(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        return None


def _parse_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip().replace("%", ""))
    except ValueError:
        return None


def _pct_points(value: float | None) -> float | None:
    return None if value is None else value * 100.0


def _avg(values: list[float | int | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return sum(numeric) / len(numeric) if numeric else None


def _min(values: list[float | int | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return min(numeric) if numeric else None


def _max(values: list[float | int | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return max(numeric) if numeric else None


def _path_or_none(value: object) -> Path | None:
    return Path(value) if isinstance(value, str) and value else None


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _str_or_default(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None

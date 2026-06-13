from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from scripts.phase_metrics import DAYS_PER_YEAR, EPS, TRADING_DAYS

TURNOVER_NOTE = "monthly trade rows only; turnover timing is approximate"


def build_risk_metrics_report(
    *,
    matrix_summary_path: Path,
    strategy_profile: str = "balanced_v1",
    min_drawdown_depth_pct: float = -1.0,
    generated_at: str | None = None,
) -> dict[str, Any]:
    matrix_summary = _load_json(matrix_summary_path)
    runs = _runs_for_profile(matrix_summary, strategy_profile)
    if not runs:
        raise ValueError(f"No runs found for strategy profile: {strategy_profile}")

    warnings: list[str] = []
    phases = [
        analyze_phase_run(
            run,
            min_drawdown_depth_pct=min_drawdown_depth_pct,
            warnings=warnings,
        )
        for run in runs
    ]
    return {
        "strategy_profile": strategy_profile,
        "generated_at": generated_at or datetime.now().isoformat(timespec="seconds"),
        "source_matrix_summary": str(matrix_summary_path),
        "settings": {
            "trading_days": TRADING_DAYS,
            "days_per_year": DAYS_PER_YEAR,
            "eps": EPS,
            "drawdown_episode_min_depth_pct": min_drawdown_depth_pct,
        },
        "phases": phases,
        "warnings": warnings,
    }


def analyze_phase_run(
    run: dict[str, Any],
    *,
    min_drawdown_depth_pct: float,
    warnings: list[str],
) -> dict[str, Any]:
    phase_name = _str_or_default(run.get("phase_name"), "unknown")
    phase_start = _str_or_default(run.get("phase_start"), "")
    phase_end = _str_or_default(run.get("phase_end"), "")
    run_dir = _str_or_none(run.get("run_dir"))
    manifest_path = _path_or_none(run.get("manifest_path"))
    manifest = _load_manifest(manifest_path, warnings, phase_name)
    artifacts = manifest.get("artifacts") if isinstance(manifest.get("artifacts"), dict) else {}
    paths = _artifact_paths(artifacts, run_dir, manifest_path)

    phase = _empty_phase(
        phase_name=phase_name,
        phase_start=phase_start,
        phase_end=phase_end,
        run_id=_str_or_none(run.get("run_id")),
        run_dir=run_dir,
    )
    start = _parse_date(phase_start)
    end = _parse_date(phase_end)
    if start is None or end is None:
        _warn(warnings, phase, f"{phase_name}: invalid phase window.")
        return phase

    equity_path = paths["equity"]
    if equity_path is None or not equity_path.exists():
        _warn(warnings, phase, f"{phase_name}: missing equity artifact.")
        _apply_missing_trades_warning(paths["trades"], warnings, phase, phase_name)
        return phase

    portfolio = load_series(equity_path, "date", "equity", start=start, end=end)
    benchmark_path = paths["benchmark"]
    benchmark: list[tuple[datetime, float]] = []
    benchmark_column = None
    if benchmark_path is None or not benchmark_path.exists():
        _warn(warnings, phase, f"{phase_name}: missing benchmark artifact.")
        portfolio_aligned = portfolio
    else:
        benchmark_column = benchmark_column_from_csv(benchmark_path)
        phase["benchmark_column"] = benchmark_column
        if benchmark_column is None:
            _warn(warnings, phase, f"{phase_name}: benchmark BM1_ column not found.")
            portfolio_aligned = portfolio
        else:
            benchmark = load_series(benchmark_path, "date", benchmark_column, start=start, end=end)
            portfolio_aligned, benchmark = align_series(portfolio, benchmark)

    if portfolio_aligned:
        phase["phase_start_actual"] = portfolio_aligned[0][0].date().isoformat()
        phase["phase_end_actual"] = portfolio_aligned[-1][0].date().isoformat()

    phase["portfolio"] = series_risk_metrics(
        portfolio_aligned,
        min_drawdown_depth_pct=min_drawdown_depth_pct,
        phase_end=end,
    )
    if len(portfolio_aligned) < 2:
        _warn(warnings, phase, f"{phase_name}: portfolio segment missing or too short.")

    if benchmark_column is not None:
        phase["benchmark"] = series_risk_metrics(
            benchmark,
            min_drawdown_depth_pct=min_drawdown_depth_pct,
            phase_end=end,
        )
        if len(benchmark) < 2:
            _warn(warnings, phase, f"{phase_name}: benchmark segment missing or too short.")

    phase["relative"] = relative_metrics(phase["portfolio"], phase["benchmark"])
    capture, capture_warnings = capture_ratios(portfolio_aligned, benchmark)
    phase["relative"].update(capture)
    for warning in capture_warnings:
        _warn(warnings, phase, f"{phase_name}: {warning}")

    phase["turnover"] = turnover_stress_check(
        trades_path=paths["trades"],
        portfolio_series=portfolio_aligned,
        min_drawdown_depth_pct=min_drawdown_depth_pct,
        phase_start=start,
        phase_end=end,
    )
    if paths["trades"] is None or not paths["trades"].exists():
        _warn(warnings, phase, f"{phase_name}: missing trades artifact.")
    return phase


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


def benchmark_column_from_csv(path: Path | None) -> str | None:
    rows = read_csv_rows(path)
    if not rows:
        return None
    for column in rows[0]:
        if column.startswith("BM1_"):
            return column
    return None


def load_series(
    path: Path,
    date_column: str,
    value_column: str,
    *,
    start: datetime,
    end: datetime,
) -> list[tuple[datetime, float]]:
    series = []
    for row in read_csv_rows(path):
        date_value = _parse_date(row.get(date_column))
        value = _parse_float(row.get(value_column))
        if date_value is not None and value is not None and start <= date_value <= end:
            series.append((date_value, value))
    return sorted(series, key=lambda item: item[0])


def align_series(
    left: list[tuple[datetime, float]],
    right: list[tuple[datetime, float]],
) -> tuple[list[tuple[datetime, float]], list[tuple[datetime, float]]]:
    left_by_date = {date_value: value for date_value, value in left}
    right_by_date = {date_value: value for date_value, value in right}
    dates = sorted(set(left_by_date) & set(right_by_date))
    return (
        [(date_value, left_by_date[date_value]) for date_value in dates],
        [(date_value, right_by_date[date_value]) for date_value in dates],
    )


def series_risk_metrics(
    series: list[tuple[datetime, float]],
    *,
    min_drawdown_depth_pct: float,
    phase_end: datetime | None = None,
) -> dict[str, Any]:
    metrics = _empty_side()
    metrics["observation_count"] = len(series)
    if len(series) < 2 or abs(series[0][1]) <= EPS:
        return metrics

    normalized = normalize_series(series)
    returns = series_returns(normalized)
    total_return = normalized[-1][1] - 1.0
    days = (normalized[-1][0] - normalized[0][0]).days
    cagr = calc_cagr(total_return, days)
    drawdowns = drawdown_series(normalized)
    max_dd = min(drawdowns) if drawdowns else None
    downside_vol = downside_volatility(returns)

    metrics.update(
        {
            "total_return_pct": _pct_points(total_return),
            "cagr_pct": _pct_points(cagr),
            "max_drawdown_pct": _pct_points(max_dd),
            "calmar_ratio": calmar_ratio(cagr, max_dd),
            "ulcer_index_pct": _pct_points(ulcer_index(drawdowns)),
            "pain_index_pct": _pct_points(pain_index(drawdowns)),
            "time_under_water_observations": sum(1 for value in drawdowns if value < -EPS),
            "time_under_water_pct": (
                sum(1 for value in drawdowns if value < -EPS) / len(drawdowns) * 100.0
            ),
            "downside_volatility_pct": _pct_points(downside_vol),
            "sortino_ratio": sortino_ratio(cagr, downside_vol),
            "drawdown_distribution": drawdown_distribution(
                normalized,
                min_drawdown_depth_pct=min_drawdown_depth_pct,
                phase_end=phase_end or normalized[-1][0],
            ),
        }
    )
    return metrics


def normalize_series(series: list[tuple[datetime, float]]) -> list[tuple[datetime, float]]:
    first = series[0][1]
    return [(date_value, value / first) for date_value, value in series]


def series_returns(series: list[tuple[datetime, float]]) -> list[tuple[datetime, float]]:
    returns = []
    for index in range(1, len(series)):
        previous = series[index - 1][1]
        if abs(previous) <= EPS:
            continue
        returns.append((series[index][0], series[index][1] / previous - 1.0))
    return returns


def calc_cagr(total_return: float, days: int) -> float | None:
    if days <= 0 or total_return <= -1.0:
        return None
    return (1.0 + total_return) ** (DAYS_PER_YEAR / days) - 1.0


def drawdown_series(series: list[tuple[datetime, float]]) -> list[float]:
    peak = series[0][1]
    values = []
    for _, value in series:
        peak = max(peak, value)
        values.append(value / peak - 1.0 if abs(peak) > EPS else 0.0)
    return values


def calmar_ratio(cagr: float | None, max_drawdown: float | None) -> float | None:
    if cagr is None or max_drawdown is None or abs(max_drawdown) <= EPS:
        return None
    return cagr / abs(max_drawdown)


def ulcer_index(drawdowns: list[float]) -> float | None:
    if not drawdowns:
        return None
    return math.sqrt(sum(value * value for value in drawdowns) / len(drawdowns))


def pain_index(drawdowns: list[float]) -> float | None:
    if not drawdowns:
        return None
    return sum(abs(value) for value in drawdowns) / len(drawdowns)


def downside_volatility(returns: list[tuple[datetime, float]]) -> float | None:
    if not returns:
        return None
    negatives = [min(value, 0.0) for _, value in returns]
    return math.sqrt(sum(value * value for value in negatives) / len(negatives)) * math.sqrt(
        TRADING_DAYS
    )


def sortino_ratio(cagr: float | None, downside_vol: float | None) -> float | None:
    if cagr is None or downside_vol is None or downside_vol <= EPS:
        return None
    return cagr / downside_vol


def detect_drawdown_episodes(
    series: list[tuple[datetime, float]],
    *,
    phase_end: datetime,
) -> list[dict[str, Any]]:
    if not series:
        return []
    episodes = []
    peak_index = 0
    peak_value = series[0][1]
    active: dict[str, Any] | None = None
    for index, (date_value, value) in enumerate(series):
        if active is None:
            if value >= peak_value - EPS:
                peak_index = index
                peak_value = max(peak_value, value)
                continue
            active = {
                "start_date": series[peak_index][0],
                "peak_value": peak_value,
                "trough_date": date_value,
                "trough_value": value,
                "recovery_date": None,
            }
            continue

        if value < active["trough_value"]:
            active["trough_date"] = date_value
            active["trough_value"] = value
        if value >= active["peak_value"] - EPS:
            active["recovery_date"] = date_value
            episodes.append(_format_episode(active, end_date=date_value))
            active = None
            peak_index = index
            peak_value = value

    if active is not None:
        episodes.append(_format_episode(active, end_date=phase_end))
    return episodes


def drawdown_distribution(
    series: list[tuple[datetime, float]],
    *,
    min_drawdown_depth_pct: float,
    phase_end: datetime,
) -> dict[str, Any]:
    episodes = [
        episode
        for episode in detect_drawdown_episodes(series, phase_end=phase_end)
        if episode["drawdown_depth_pct"] <= min_drawdown_depth_pct
    ]
    recovered = [episode for episode in episodes if episode["recovered"]]
    unrecovered = [episode for episode in episodes if not episode["recovered"]]
    return {
        "drawdown_count": len(episodes),
        "avg_drawdown_depth_pct": _avg([episode["drawdown_depth_pct"] for episode in episodes]),
        "median_drawdown_depth_pct": _median(
            [episode["drawdown_depth_pct"] for episode in episodes]
        ),
        "max_drawdown_depth_pct": _min([episode["drawdown_depth_pct"] for episode in episodes]),
        "avg_drawdown_duration_days": _avg(
            [episode["drawdown_duration_days"] for episode in episodes]
        ),
        "median_drawdown_duration_days": _median(
            [episode["drawdown_duration_days"] for episode in episodes]
        ),
        "max_drawdown_duration_days": _max(
            [episode["drawdown_duration_days"] for episode in episodes]
        ),
        "recovered_drawdown_count": len(recovered),
        "unrecovered_drawdown_count": len(unrecovered),
        "avg_recovery_duration_days": _avg(
            [episode["recovery_duration_days"] for episode in recovered]
        ),
        "median_recovery_duration_days": _median(
            [episode["recovery_duration_days"] for episode in recovered]
        ),
        "max_recovery_duration_days": _max(
            [episode["recovery_duration_days"] for episode in recovered]
        ),
        "current_unrecovered_duration_days": (
            unrecovered[-1]["drawdown_duration_days"] if unrecovered else None
        ),
    }


def capture_ratios(
    portfolio: list[tuple[datetime, float]],
    benchmark: list[tuple[datetime, float]],
) -> tuple[dict[str, float | None], list[str]]:
    result = {"downside_capture": None, "upside_capture": None}
    warnings = []
    if len(portfolio) < 2 or len(benchmark) < 2:
        return result, warnings
    portfolio_returns = dict(series_returns(normalize_series(portfolio)))
    benchmark_returns = dict(series_returns(normalize_series(benchmark)))
    dates = sorted(set(portfolio_returns) & set(benchmark_returns))
    down_dates = [date_value for date_value in dates if benchmark_returns[date_value] < -EPS]
    up_dates = [date_value for date_value in dates if benchmark_returns[date_value] > EPS]

    if not down_dates:
        warnings.append("no benchmark down days for downside capture.")
    else:
        denominator = sum(benchmark_returns[date_value] for date_value in down_dates)
        if abs(denominator) <= EPS:
            warnings.append("downside capture denominator near zero.")
        else:
            result["downside_capture"] = (
                sum(portfolio_returns[date_value] for date_value in down_dates) / denominator
            )

    if not up_dates:
        warnings.append("no benchmark up days for upside capture.")
    else:
        denominator = sum(benchmark_returns[date_value] for date_value in up_dates)
        if abs(denominator) <= EPS:
            warnings.append("upside capture denominator near zero.")
        else:
            result["upside_capture"] = (
                sum(portfolio_returns[date_value] for date_value in up_dates) / denominator
            )
    return result, warnings


def relative_metrics(portfolio: dict[str, Any], benchmark: dict[str, Any]) -> dict[str, Any]:
    return {
        "total_return_delta_pct": _delta(
            portfolio["total_return_pct"], benchmark["total_return_pct"]
        ),
        "cagr_delta_pct": _delta(portfolio["cagr_pct"], benchmark["cagr_pct"]),
        "max_drawdown_delta_pct": _delta(
            portfolio["max_drawdown_pct"], benchmark["max_drawdown_pct"]
        ),
        "calmar_delta": _delta(portfolio["calmar_ratio"], benchmark["calmar_ratio"]),
        "ulcer_index_delta_pct": _delta(
            portfolio["ulcer_index_pct"], benchmark["ulcer_index_pct"]
        ),
        "pain_index_delta_pct": _delta(portfolio["pain_index_pct"], benchmark["pain_index_pct"]),
        "downside_capture": None,
        "upside_capture": None,
    }


def turnover_stress_check(
    *,
    trades_path: Path | None,
    portfolio_series: list[tuple[datetime, float]],
    min_drawdown_depth_pct: float,
    phase_start: datetime,
    phase_end: datetime,
) -> dict[str, Any]:
    result = {
        "avg_during_drawdowns": None,
        "avg_outside_drawdowns": None,
        "ratio_drawdown_vs_outside": None,
        "trade_count_during_drawdowns": None,
        "trade_count_outside_drawdowns": None,
        "note": TURNOVER_NOTE,
    }
    if trades_path is None or not trades_path.exists():
        return result

    rows = read_csv_rows(trades_path)
    windows = [
        (
            _parse_date(episode["drawdown_start"]),
            _parse_date(episode["drawdown_recovery"]) or phase_end,
        )
        for episode in detect_drawdown_episodes(
            normalize_series(portfolio_series),
            phase_end=phase_end,
        )
        if episode["drawdown_depth_pct"] <= min_drawdown_depth_pct
    ]
    during = []
    outside = []
    for row in rows:
        date_value = _parse_date(row.get("date"))
        turnover = _parse_float(row.get("turnover"))
        if date_value is None or turnover is None or not phase_start <= date_value <= phase_end:
            continue
        in_drawdown = any(start <= date_value <= end for start, end in windows if start)
        bucket = during if in_drawdown else outside
        bucket.append(turnover)

    result["trade_count_during_drawdowns"] = len(during)
    result["trade_count_outside_drawdowns"] = len(outside)
    result["avg_during_drawdowns"] = _avg(during)
    result["avg_outside_drawdowns"] = _avg(outside)
    if result["avg_during_drawdowns"] is not None and result["avg_outside_drawdowns"] not in (
        None,
        0.0,
    ):
        result["ratio_drawdown_vs_outside"] = (
            result["avg_during_drawdowns"] / result["avg_outside_drawdowns"]
        )
    return result


def build_markdown_report(report: dict[str, Any]) -> str:
    benchmark = next(
        (phase["benchmark_column"] for phase in report["phases"] if phase["benchmark_column"]),
        "n/a",
    )
    lines = [
        f"# Risk Metrics - {report['strategy_profile']}",
        "",
        f"Generated at: {report['generated_at']}",
        "",
        "## Summary",
        "",
        "- Metrics are computed phase-only from clipped portfolio and benchmark segments.",
        f"- Benchmark column: {benchmark}.",
        "- Capture ratios use daily return observations after date alignment.",
        f"- Turnover note: {TURNOVER_NOTE}.",
        "",
        "## Risk Summary",
        _md_table(
            (
                "Phase",
                "Portfolio CAGR",
                "Benchmark CAGR",
                "Portfolio MaxDD",
                "Benchmark MaxDD",
                "Calmar P",
                "Calmar B",
                "Ulcer P",
                "Ulcer B",
                "Pain P",
                "Pain B",
                "TUW P",
                "TUW B",
                "Sortino P",
                "Sortino B",
                "Down Capture",
                "Up Capture",
            ),
            tuple(_risk_summary_row(phase) for phase in report["phases"]),
        ),
        "",
        "## Drawdown Duration Distribution",
        _md_table(
            (
                "Phase",
                "Side",
                "Count",
                "Avg Depth",
                "Median Depth",
                "Max Depth",
                "Avg Duration",
                "Median Duration",
                "Max Duration",
                "Unrecovered",
            ),
            tuple(row for phase in report["phases"] for row in _distribution_rows(phase)),
        ),
        "",
        "## Turnover Stress Check",
        _md_table(
            (
                "Phase",
                "Avg During DD",
                "Avg Outside DD",
                "Ratio",
                "Trades During",
                "Trades Outside",
            ),
            tuple(_turnover_row(phase) for phase in report["phases"]),
        ),
        "",
        "## Interpretation Notes",
        "",
        "- Downside Capture < 1 is generally better when both sums are negative.",
        "- Upside Capture > 1 means stronger participation on benchmark up days.",
        "- Lower Ulcer and Pain Index values are better.",
        "- Higher Calmar and Sortino values are better.",
        "- Turnover is limited because only monthly rebalance trade rows are available.",
        "",
    ]
    if report.get("warnings"):
        lines.extend(["## Warnings", *[f"- {warning}" for warning in report["warnings"]], ""])
    return "\n".join(lines)


def write_reports(report: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    profile = str(report["strategy_profile"])
    md_path = output_dir / f"{profile}_risk_metrics.md"
    json_path = output_dir / f"{profile}_risk_metrics.json"
    md_path.write_text(build_markdown_report(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return md_path, json_path


def _empty_phase(
    *,
    phase_name: str,
    phase_start: str,
    phase_end: str,
    run_id: str | None,
    run_dir: str | None,
) -> dict[str, Any]:
    return {
        "phase": phase_name,
        "phase_start": phase_start,
        "phase_end": phase_end,
        "phase_start_actual": None,
        "phase_end_actual": None,
        "run_id": run_id,
        "run_dir": run_dir,
        "benchmark_column": None,
        "portfolio": _empty_side(),
        "benchmark": _empty_side(),
        "relative": {
            "total_return_delta_pct": None,
            "cagr_delta_pct": None,
            "max_drawdown_delta_pct": None,
            "calmar_delta": None,
            "ulcer_index_delta_pct": None,
            "pain_index_delta_pct": None,
            "downside_capture": None,
            "upside_capture": None,
        },
        "turnover": {
            "avg_during_drawdowns": None,
            "avg_outside_drawdowns": None,
            "ratio_drawdown_vs_outside": None,
            "trade_count_during_drawdowns": None,
            "trade_count_outside_drawdowns": None,
            "note": TURNOVER_NOTE,
        },
        "warnings": [],
    }


def _empty_side() -> dict[str, Any]:
    return {
        "total_return_pct": None,
        "cagr_pct": None,
        "max_drawdown_pct": None,
        "calmar_ratio": None,
        "ulcer_index_pct": None,
        "pain_index_pct": None,
        "time_under_water_observations": None,
        "observation_count": 0,
        "time_under_water_pct": None,
        "downside_volatility_pct": None,
        "sortino_ratio": None,
        "drawdown_distribution": _empty_distribution(),
    }


def _empty_distribution() -> dict[str, Any]:
    return {
        "drawdown_count": 0,
        "avg_drawdown_depth_pct": None,
        "median_drawdown_depth_pct": None,
        "max_drawdown_depth_pct": None,
        "avg_drawdown_duration_days": None,
        "median_drawdown_duration_days": None,
        "max_drawdown_duration_days": None,
        "recovered_drawdown_count": 0,
        "unrecovered_drawdown_count": 0,
        "avg_recovery_duration_days": None,
        "median_recovery_duration_days": None,
        "max_recovery_duration_days": None,
        "current_unrecovered_duration_days": None,
    }


def _format_episode(active: dict[str, Any], *, end_date: datetime) -> dict[str, Any]:
    recovery_date = active["recovery_date"]
    depth = active["trough_value"] / active["peak_value"] - 1.0
    return {
        "drawdown_start": active["start_date"].date().isoformat(),
        "drawdown_trough": active["trough_date"].date().isoformat(),
        "drawdown_recovery": None if recovery_date is None else recovery_date.date().isoformat(),
        "drawdown_depth_pct": _pct_points(depth),
        "drawdown_duration_days": (end_date - active["start_date"]).days,
        "recovery_duration_days": (
            None if recovery_date is None else (recovery_date - active["trough_date"]).days
        ),
        "recovered": recovery_date is not None,
    }


def _artifact_paths(
    artifacts: dict[str, Any],
    run_dir: str | None,
    manifest_path: Path | None,
) -> dict[str, Path | None]:
    root = Path(run_dir) / "aktien_oop" if run_dir else None
    return {
        "equity": _resolve_artifact(artifacts.get("equity"), manifest_path)
        or _fallback(root, "bt_monthly_15x3_equity_curve.csv"),
        "benchmark": _resolve_artifact(artifacts.get("bench"), manifest_path)
        or _resolve_artifact(artifacts.get("benchmark"), manifest_path)
        or _fallback(root, "bt_monthly_15x3_benchmark.csv"),
        "trades": _resolve_artifact(artifacts.get("trades"), manifest_path)
        or _fallback(root, "bt_monthly_15x3_trades.csv"),
    }


def _resolve_artifact(value: object, manifest_path: Path | None) -> Path | None:
    path = _path_or_none(value)
    if path is None or path.is_absolute() or manifest_path is None:
        return path
    candidate = manifest_path.parent / path
    return candidate if candidate.exists() else path


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


def _risk_summary_row(phase: dict[str, Any]) -> tuple[object, ...]:
    portfolio = phase["portfolio"]
    benchmark = phase["benchmark"]
    relative = phase["relative"]
    return (
        phase["phase"],
        _fmt_pct(portfolio["cagr_pct"]),
        _fmt_pct(benchmark["cagr_pct"]),
        _fmt_pct(portfolio["max_drawdown_pct"]),
        _fmt_pct(benchmark["max_drawdown_pct"]),
        _fmt_num(portfolio["calmar_ratio"]),
        _fmt_num(benchmark["calmar_ratio"]),
        _fmt_pct(portfolio["ulcer_index_pct"]),
        _fmt_pct(benchmark["ulcer_index_pct"]),
        _fmt_pct(portfolio["pain_index_pct"]),
        _fmt_pct(benchmark["pain_index_pct"]),
        _fmt_pct(portfolio["time_under_water_pct"]),
        _fmt_pct(benchmark["time_under_water_pct"]),
        _fmt_num(portfolio["sortino_ratio"]),
        _fmt_num(benchmark["sortino_ratio"]),
        _fmt_factor_pct(relative["downside_capture"]),
        _fmt_factor_pct(relative["upside_capture"]),
    )


def _distribution_rows(phase: dict[str, Any]) -> tuple[tuple[object, ...], ...]:
    rows = []
    for side in ("portfolio", "benchmark"):
        distribution = phase[side]["drawdown_distribution"]
        rows.append(
            (
                phase["phase"],
                side,
                distribution["drawdown_count"],
                _fmt_pct(distribution["avg_drawdown_depth_pct"]),
                _fmt_pct(distribution["median_drawdown_depth_pct"]),
                _fmt_pct(distribution["max_drawdown_depth_pct"]),
                _fmt_num(distribution["avg_drawdown_duration_days"]),
                _fmt_num(distribution["median_drawdown_duration_days"]),
                _fmt_num(distribution["max_drawdown_duration_days"]),
                distribution["unrecovered_drawdown_count"],
            )
        )
    return tuple(rows)


def _turnover_row(phase: dict[str, Any]) -> tuple[object, ...]:
    turnover = phase["turnover"]
    return (
        phase["phase"],
        _fmt_num(turnover["avg_during_drawdowns"]),
        _fmt_num(turnover["avg_outside_drawdowns"]),
        _fmt_num(turnover["ratio_drawdown_vs_outside"]),
        _display(turnover["trade_count_during_drawdowns"]),
        _display(turnover["trade_count_outside_drawdowns"]),
    )


def _md_table(headers: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_display(value) for value in row) + " |")
    return "\n".join(lines)


def _warn(warnings: list[str], phase: dict[str, Any], message: str) -> None:
    warnings.append(message)
    phase["warnings"].append(message)


def _apply_missing_trades_warning(
    trades_path: Path | None,
    warnings: list[str],
    phase: dict[str, Any],
    phase_name: str,
) -> None:
    if trades_path is None or not trades_path.exists():
        _warn(warnings, phase, f"{phase_name}: missing trades artifact.")


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


def _path_or_none(value: object) -> Path | None:
    return Path(value) if isinstance(value, str) and value else None


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _str_or_default(value: object, default: str) -> str:
    return value if isinstance(value, str) and value else default


def _pct_points(value: float | None) -> float | None:
    return None if value is None else value * 100.0


def _delta(left: float | None, right: float | None) -> float | None:
    return None if left is None or right is None else left - right


def _avg(values: list[float | int | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return sum(numeric) / len(numeric) if numeric else None


def _median(values: list[float | int | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return float(median(numeric)) if numeric else None


def _min(values: list[float | int | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return min(numeric) if numeric else None


def _max(values: list[float | int | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    return max(numeric) if numeric else None


def _display(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _fmt_pct(value: object) -> str:
    numeric = _parse_float(value)
    return "n/a" if numeric is None else f"{numeric:.2f}%"


def _fmt_num(value: object) -> str:
    numeric = _parse_float(value)
    return "n/a" if numeric is None else f"{numeric:.2f}"


def _fmt_factor_pct(value: object) -> str:
    numeric = _parse_float(value)
    return "n/a" if numeric is None else f"{numeric * 100.0:.2f}%"

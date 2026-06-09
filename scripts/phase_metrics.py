from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path
from typing import Any

TRADING_DAYS = 252.0
DAYS_PER_YEAR = 365.25
EPS = 1e-12
TURNOVER_NOTE = (
    "Computed from trade rows inside phase window; first in-phase trade may reflect "
    "pre-phase holdings."
)
NO_TURNOVER_NOTE = "No in-phase trade rows available."


def empty_phase_metrics() -> dict[str, float | bool | int | str | None]:
    return {
        "portfolio_total_return": None,
        "portfolio_cagr": None,
        "portfolio_max_drawdown": None,
        "portfolio_volatility": None,
        "portfolio_sharpe": None,
        "benchmark_total_return": None,
        "benchmark_cagr": None,
        "benchmark_max_drawdown": None,
        "benchmark_volatility": None,
        "benchmark_sharpe": None,
        "relative_total_return": None,
        "relative_cagr": None,
        "outperformed_benchmark": None,
        "cagr_outperformed_benchmark": None,
        "drawdown_better_than_benchmark": None,
        "turnover": None,
        "turnover_is_phase_only": False,
        "turnover_source": None,
        "turnover_note": NO_TURNOVER_NOTE,
        "phase_start_actual": None,
        "phase_end_actual": None,
        "observation_count": 0,
    }


def compute_phase_metrics(
    artifacts: dict[str, Any],
    phase_start: str,
    phase_end: str,
) -> dict[str, float | bool | int | str | None]:
    metrics = empty_phase_metrics()
    start = _parse_date(phase_start)
    end = _parse_date(phase_end)
    if start is None or end is None:
        return metrics

    equity_path = _artifact_path(artifacts, "equity")
    if equity_path is None or not equity_path.exists():
        return metrics

    portfolio_segment = _load_segment(equity_path, "date", "equity", start, end)
    portfolio_metrics = _series_metrics(portfolio_segment)
    _copy_series_metrics(metrics, "portfolio", portfolio_metrics)
    if portfolio_segment:
        metrics["phase_start_actual"] = portfolio_segment[0][0].date().isoformat()
        metrics["phase_end_actual"] = portfolio_segment[-1][0].date().isoformat()
        metrics["observation_count"] = len(portfolio_segment)

    benchmark_path = _artifact_path(artifacts, "bench") or _artifact_path(artifacts, "benchmark")
    benchmark_column = _benchmark_column(benchmark_path)
    benchmark_segment = _load_segment(benchmark_path, "date", benchmark_column, start, end)
    benchmark_metrics = _series_metrics(benchmark_segment)
    _copy_series_metrics(metrics, "benchmark", benchmark_metrics)

    portfolio_total = metrics["portfolio_total_return"]
    benchmark_total = metrics["benchmark_total_return"]
    if isinstance(portfolio_total, float) and isinstance(benchmark_total, float):
        metrics["relative_total_return"] = portfolio_total - benchmark_total
        metrics["outperformed_benchmark"] = portfolio_total > benchmark_total

    portfolio_cagr = metrics["portfolio_cagr"]
    benchmark_cagr = metrics["benchmark_cagr"]
    if isinstance(portfolio_cagr, float) and isinstance(benchmark_cagr, float):
        metrics["relative_cagr"] = portfolio_cagr - benchmark_cagr
        metrics["cagr_outperformed_benchmark"] = portfolio_cagr > benchmark_cagr

    portfolio_mdd = metrics["portfolio_max_drawdown"]
    benchmark_mdd = metrics["benchmark_max_drawdown"]
    if isinstance(portfolio_mdd, float) and isinstance(benchmark_mdd, float):
        metrics["drawdown_better_than_benchmark"] = portfolio_mdd > benchmark_mdd

    _apply_turnover(metrics, artifacts, start, end)
    return metrics


def phase_metrics_warnings(metrics: dict[str, Any], artifacts: dict[str, Any]) -> tuple[str, ...]:
    warnings = []
    if _artifact_path(artifacts, "equity") is None:
        warnings.append("[WARN] Phase-only metrics: missing equity artifact.")
    elif metrics.get("portfolio_total_return") is None:
        warnings.append("[WARN] Phase-only metrics: portfolio segment missing or too short.")

    if (_artifact_path(artifacts, "bench") or _artifact_path(artifacts, "benchmark")) is None:
        warnings.append("[WARN] Phase-only metrics: missing benchmark artifact.")
    elif metrics.get("benchmark_total_return") is None:
        warnings.append("[WARN] Phase-only metrics: benchmark segment missing or too short.")
    return tuple(warnings)


def _copy_series_metrics(
    target: dict[str, float | bool | int | str | None],
    prefix: str,
    values: dict[str, float | None],
) -> None:
    target[f"{prefix}_total_return"] = _pct_points(values["total_return"])
    target[f"{prefix}_cagr"] = _pct_points(values["cagr"])
    target[f"{prefix}_max_drawdown"] = _pct_points(values["max_drawdown"])
    target[f"{prefix}_volatility"] = _pct_points(values["volatility"])
    target[f"{prefix}_sharpe"] = values["sharpe"]


def _apply_turnover(
    metrics: dict[str, float | bool | int | str | None],
    artifacts: dict[str, Any],
    start: datetime,
    end: datetime,
) -> None:
    trades_path = _artifact_path(artifacts, "trades")
    rows = _read_csv_rows(trades_path)
    turnovers = []
    for row in rows:
        date_value = _parse_date(row.get("date"))
        if date_value is None or not start <= date_value <= end:
            continue
        turnover = _parse_float(row.get("turnover"))
        if turnover is not None:
            turnovers.append(turnover)
    if not turnovers:
        return

    metrics["turnover"] = sum(turnovers) / len(turnovers) * 100.0
    metrics["turnover_is_phase_only"] = True
    metrics["turnover_source"] = "trades_csv_in_phase_rows"
    metrics["turnover_note"] = TURNOVER_NOTE


def _series_metrics(segment: list[tuple[datetime, float]]) -> dict[str, float | None]:
    if len(segment) < 2:
        return {
            "total_return": None,
            "cagr": None,
            "max_drawdown": None,
            "volatility": None,
            "sharpe": None,
        }

    first = segment[0][1]
    if first == 0.0:
        return {
            "total_return": None,
            "cagr": None,
            "max_drawdown": None,
            "volatility": None,
            "sharpe": None,
        }

    normalized = [(date_value, value / first) for date_value, value in segment]
    total_return = normalized[-1][1] - 1.0
    days = max(1, (normalized[-1][0] - normalized[0][0]).days)
    cagr = _calc_cagr(total_return, days)
    returns = [0.0]
    returns.extend(
        normalized[index][1] / normalized[index - 1][1] - 1.0
        for index in range(1, len(normalized))
        if normalized[index - 1][1] != 0.0
    )
    volatility = _std_sample(returns) * math.sqrt(TRADING_DAYS)
    sharpe = (sum(returns) / len(returns) * TRADING_DAYS) / (volatility + EPS)
    return {
        "total_return": total_return,
        "cagr": cagr,
        "max_drawdown": _max_drawdown([value for _, value in normalized]),
        "volatility": volatility,
        "sharpe": sharpe,
    }


def _calc_cagr(total_return: float, days: int) -> float | None:
    if total_return <= -1.0:
        return None
    return (1.0 + total_return) ** (DAYS_PER_YEAR / days) - 1.0


def _max_drawdown(values: list[float]) -> float:
    peak = values[0]
    max_dd = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = value / peak - 1.0
        max_dd = min(max_dd, drawdown)
    return max_dd


def _std_sample(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance)


def _load_segment(
    path: Path | None,
    date_column: str,
    value_column: str | None,
    start: datetime,
    end: datetime,
) -> list[tuple[datetime, float]]:
    if path is None or value_column is None:
        return []
    rows = _read_csv_rows(path)
    segment = []
    for row in rows:
        date_value = _parse_date(row.get(date_column))
        value = _parse_float(row.get(value_column))
        if date_value is None or value is None or not start <= date_value <= end:
            continue
        segment.append((date_value, value))
    return sorted(segment, key=lambda item: item[0])


def _read_csv_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    try:
        lines = [
            line
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if not line.startswith("#")
        ]
    except OSError:
        return []
    if not lines:
        return []
    return list(csv.DictReader(lines))


def _benchmark_column(path: Path | None) -> str | None:
    rows = _read_csv_rows(path)
    if not rows:
        return None
    for column in rows[0]:
        if column.startswith("BM1_"):
            return column
    return None


def _artifact_path(artifacts: dict[str, Any], key: str) -> Path | None:
    value = artifacts.get(key)
    if not isinstance(value, str) or not value:
        return None
    return Path(value)


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
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct_points(value: float | None) -> float | None:
    return None if value is None else value * 100.0

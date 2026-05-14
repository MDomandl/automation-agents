from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUN_ID_RE = re.compile(r"^20\d{6}_\d{6}$")
UNIVERSE_RE = re.compile(
    r"universe_name=(?P<name>\S+)\s+universe_file=(?P<file>.*?)\s+"
    r"universe_len=(?P<len>\d+)\s+universe_hash=(?P<hash>[0-9a-fA-F]+)"
)
UNIVERSE_WARNING_RE = re.compile(
    r"Universe match:\s+count=(?P<len>\d+),\s+hash=(?P<hash>[0-9a-fA-F]+),\s+"
    r"name=(?P<name>[^,]+),\s+file=(?P<file>.+)$"
)
TOTAL_RETURN_RE = re.compile(r"(?:Portfolio Total Ret|Total Return):\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
CAGR_RE = re.compile(r"(?:Port CAGR|(?<!BM )CAGR):\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
VOL_RE = re.compile(r"^\s*Volatility:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%", re.MULTILINE)
SHARPE_RE = re.compile(r"Sharpe(?:\(0%\))?:\s*(?P<value>[-+]?\d+(?:\.\d+)?)")
SORTINO_RE = re.compile(r"Sortino(?:\(0%\))?:\s*(?P<value>[-+]?\d+(?:\.\d+)?)")
MAX_DD_RE = re.compile(r"^\s*Max DD:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%", re.MULTILINE)
TURNOVER_RE = re.compile(r"Avg Turnover:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
ALPHA_RE = re.compile(r"Alpha \(ann\.\):\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
BENCHMARK_NAME_RE = re.compile(r"^Benchmark:\s*(?P<value>\S+)", re.MULTILINE)
BENCHMARK_RETURN_RE = re.compile(r"BM Total Ret:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
BENCHMARK_CAGR_RE = re.compile(r"BM CAGR:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
BENCHMARK_MAX_DD_RE = re.compile(
    r"(?:BM|Benchmark) Max DD:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%"
)
BENCHMARK_VOL_RE = re.compile(r"BM Volatility:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
BENCHMARK_SHARPE_RE = re.compile(r"BM Sharpe(?:\(0%\))?:\s*(?P<value>[-+]?\d+(?:\.\d+)?)")
OUTPUT_PATH_RE = re.compile(r"^(?P<label>Equity|Positions|Trades|Bench|Summary):\s*(?P<path>.+?)\s*$", re.MULTILINE)

PERCENT_POINT_METRICS = {
    "total_return_pct",
    "max_drawdown_pct",
    "volatility_pct",
    "turnover_pct",
    "cagr_pct",
    "alpha_pct",
    "benchmark_return_pct",
    "benchmark_cagr_pct",
    "benchmark_max_drawdown_pct",
    "benchmark_volatility_pct",
}
NUMERIC_PERFORMANCE_METRICS = {
    "final_equity",
    "sharpe_ratio",
    "sortino_ratio",
}


@dataclass(frozen=True, slots=True)
class UniverseInfo:
    universe_name: str | None = None
    universe_file: str | None = None
    universe_len: int | None = None
    universe_hash: str | None = None


@dataclass(frozen=True, slots=True)
class PerformanceInfo:
    final_equity: float | None = None
    total_return_pct: float | None = None
    cagr_pct: float | None = None
    max_drawdown_pct: float | None = None
    volatility_pct: float | None = None
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    alpha_pct: float | None = None
    turnover_pct: float | None = None


@dataclass(frozen=True, slots=True)
class BenchmarkInfo:
    benchmark_name: str | None = None
    benchmark_return_pct: float | None = None
    benchmark_cagr_pct: float | None = None
    benchmark_max_drawdown_pct: float | None = None
    benchmark_volatility_pct: float | None = None
    benchmark_sharpe_ratio: float | None = None
    correlation_to_benchmark: float | None = None
    up_capture_ratio: float | None = None
    down_capture_ratio: float | None = None


@dataclass(frozen=True, slots=True)
class BehaviorInfo:
    trades_count: int | None = None
    trades_count_source: str | None = None
    avg_positions: float | None = None
    last_as_of: str | None = None
    last_portfolio: dict[str, float] | None = None


@dataclass(frozen=True, slots=True)
class RunSnapshot:
    run_id: str
    output_dir: Path | None
    decisions_dir: Path | None
    universe: UniverseInfo
    performance: PerformanceInfo
    benchmark: BenchmarkInfo
    behavior: BehaviorInfo
    sources: dict[str, str]


def default_ai_agents_root() -> Path:
    return Path.cwd().parent / "AiAgents"


def default_runs_root() -> Path:
    return default_ai_agents_root() / "automation_runs"


def default_decisions_root() -> Path:
    return default_ai_agents_root() / "aktien_oop" / "decisions"


def compare_runs(
    run_id_a: str,
    run_id_b: str,
    *,
    runs_root: str | Path | None = None,
    decisions_root: str | Path | None = None,
) -> dict[str, Any]:
    snapshot_a = load_run_snapshot(
        run_id_a,
        runs_root=Path(runs_root) if runs_root is not None else default_runs_root(),
        decisions_root=Path(decisions_root) if decisions_root is not None else default_decisions_root(),
    )
    snapshot_b = load_run_snapshot(
        run_id_b,
        runs_root=Path(runs_root) if runs_root is not None else default_runs_root(),
        decisions_root=Path(decisions_root) if decisions_root is not None else default_decisions_root(),
    )

    tickers_a = set((snapshot_a.behavior.last_portfolio or {}).keys())
    tickers_b = set((snapshot_b.behavior.last_portfolio or {}).keys())
    common_tickers = sorted(tickers_a & tickers_b)
    overlap_denominator = max(len(tickers_a), len(tickers_b))
    overlap_pct = (
        len(common_tickers) / overlap_denominator * 100.0
        if overlap_denominator > 0
        else None
    )

    return {
        "run_a": _snapshot_to_dict(snapshot_a),
        "run_b": _snapshot_to_dict(snapshot_b),
        "last_decision_tickers": {
            "common": common_tickers,
            "only_in_a": sorted(tickers_a - tickers_b),
            "only_in_b": sorted(tickers_b - tickers_a),
            "overlap_count": len(common_tickers) if overlap_denominator > 0 else None,
            "overlap_denominator": overlap_denominator if overlap_denominator > 0 else None,
            "overlap_pct": overlap_pct,
        },
    }


def load_run_snapshot(
    run_id: str,
    *,
    runs_root: Path,
    decisions_root: Path,
) -> RunSnapshot:
    if not RUN_ID_RE.match(run_id):
        raise ValueError(f"Expected run_id format YYYYMMDD_HHMMSS, got: {run_id}")

    output_dir = find_run_output_dir(run_id, runs_root)
    manifest = _load_manifest(output_dir)
    decisions_dir = find_decisions_dir(run_id, manifest, decisions_root)
    decision_payloads = load_decision_payloads(decisions_dir)
    text_blob = build_text_blob(output_dir, manifest)
    referenced_paths = resolve_referenced_output_paths(text_blob, output_dir, manifest)

    universe = extract_universe(manifest, decision_payloads, text_blob)
    performance = extract_performance(text_blob, referenced_paths)
    benchmark = extract_benchmark(text_blob, referenced_paths, run_id=run_id)
    behavior = extract_behavior(decision_payloads, referenced_paths)

    sources = {}
    if output_dir is not None:
        sources["output_dir"] = str(output_dir)
    if decisions_dir is not None:
        sources["decisions_dir"] = str(decisions_dir)
    for key, value in referenced_paths.items():
        sources[f"{key.lower()}_path"] = str(value)

    return RunSnapshot(
        run_id=run_id,
        output_dir=output_dir,
        decisions_dir=decisions_dir,
        universe=universe,
        performance=performance,
        benchmark=benchmark,
        behavior=behavior,
        sources=sources,
    )


def find_run_output_dir(run_id: str, runs_root: Path) -> Path | None:
    if not runs_root.exists():
        return None

    for manifest_path in sorted(runs_root.rglob("run_manifest.json")):
        payload = _read_json(manifest_path)
        if payload.get("run_id") == run_id:
            return manifest_path.parent

    label_prefix = f"{run_id[:4]}-{run_id[4:6]}-{run_id[6:8]}_{run_id[9:11]}-{run_id[11:13]}-{run_id[13:15]}"
    candidates = sorted(path for path in runs_root.iterdir() if path.is_dir() and path.name.startswith(label_prefix))
    return candidates[-1] if candidates else None


def find_decisions_dir(run_id: str, manifest: dict[str, Any], decisions_root: Path) -> Path | None:
    manifest_value = manifest.get("decisions_dir")
    if isinstance(manifest_value, str) and manifest_value.strip():
        path = Path(manifest_value)
        if path.exists() and path.is_dir():
            return path

    direct = decisions_root / run_id
    if direct.exists() and direct.is_dir():
        return direct

    if decisions_root.exists():
        matches = sorted(path for path in decisions_root.rglob(run_id) if path.is_dir())
        if matches:
            return matches[-1]

    return None


def load_decision_payloads(decisions_dir: Path | None) -> list[dict[str, Any]]:
    if decisions_dir is None or not decisions_dir.exists():
        return []

    payloads = []
    for path in sorted(decisions_dir.glob("*.json")):
        payload = _read_json(path)
        if payload:
            payload["_source_path"] = str(path)
            payloads.append(payload)
    return payloads


def build_text_blob(output_dir: Path | None, manifest: dict[str, Any]) -> str:
    parts = []
    for step in ("backtest", "runner"):
        step_payload = manifest.get(step)
        if isinstance(step_payload, dict):
            parts.append(str(step_payload.get("stdout") or ""))
            parts.append(str(step_payload.get("stderr") or ""))

    if output_dir is not None:
        for filename in ("summary.txt", "backtest_stdout.txt", "backtest_stderr.txt", "runner_stdout.txt", "runner_stderr.txt"):
            path = output_dir / filename
            if path.exists() and path.is_file():
                parts.append(path.read_text(encoding="utf-8", errors="replace"))

    return "\n".join(part for part in parts if part)


def resolve_referenced_output_paths(
    text_blob: str,
    output_dir: Path | None,
    manifest: dict[str, Any],
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    cwd = _manifest_cwd(manifest)

    for match in OUTPUT_PATH_RE.finditer(text_blob):
        label = match.group("label").lower()
        raw_path = match.group("path").strip()
        candidates = []
        path = Path(raw_path)
        candidates.append(path)
        if not path.is_absolute():
            if cwd is not None:
                candidates.append(cwd / path)
            if output_dir is not None:
                candidates.append(output_dir / path)

        existing = next(
            (
                candidate
                for candidate in candidates
                if candidate.exists()
                and candidate.is_file()
                and (
                    label == "bench"
                    or output_dir is None
                    or _is_relative_to(candidate, output_dir)
                )
            ),
            None,
        )
        if existing is not None:
            paths[label] = existing

    if output_dir is not None:
        for label, patterns in {
            "equity": ("*equity*.csv",),
            "positions": ("*positions*.csv",),
            "trades": ("*trades*.csv",),
            "bench": ("*benchmark*.csv",),
            "summary": ("*summary*.txt",),
        }.items():
            if label not in paths:
                matches = sorted(match for pattern in patterns for match in output_dir.rglob(pattern))
                if matches:
                    paths[label] = matches[-1]

    return paths


def extract_universe(
    manifest: dict[str, Any],
    decision_payloads: list[dict[str, Any]],
    text_blob: str,
) -> UniverseInfo:
    for payload in reversed(decision_payloads):
        info = _universe_from_mapping(payload)
        if info.universe_name or info.universe_hash:
            return info

    for warning in manifest.get("warnings") or ():
        if isinstance(warning, str):
            match = UNIVERSE_WARNING_RE.search(warning)
            if match:
                return UniverseInfo(
                    universe_name=match.group("name"),
                    universe_file=match.group("file"),
                    universe_len=int(match.group("len")),
                    universe_hash=match.group("hash"),
                )

    matches = list(UNIVERSE_RE.finditer(text_blob))
    if matches:
        match = matches[-1]
        return UniverseInfo(
            universe_name=match.group("name"),
            universe_file=match.group("file"),
            universe_len=int(match.group("len")),
            universe_hash=match.group("hash"),
        )

    return UniverseInfo()


def extract_performance(text_blob: str, referenced_paths: dict[str, Path]) -> PerformanceInfo:
    summary_path = referenced_paths.get("summary")
    if summary_path is not None and "automation_runs" in summary_path.parts:
        text_blob = text_blob + "\n" + summary_path.read_text(encoding="utf-8", errors="replace")

    equity_path = referenced_paths.get("equity")
    final_equity = read_last_numeric_csv_value(equity_path) if equity_path is not None else None

    return PerformanceInfo(
        final_equity=final_equity,
        total_return_pct=_last_percent(TOTAL_RETURN_RE, text_blob),
        cagr_pct=_last_percent(CAGR_RE, text_blob),
        max_drawdown_pct=_last_percent(MAX_DD_RE, text_blob),
        volatility_pct=_last_percent(VOL_RE, text_blob),
        sharpe_ratio=_last_portfolio_sharpe(text_blob),
        sortino_ratio=_last_float(SORTINO_RE, text_blob),
        alpha_pct=_last_percent(ALPHA_RE, text_blob),
        turnover_pct=_last_percent(TURNOVER_RE, text_blob),
    )


def extract_benchmark(
    text_blob: str,
    referenced_paths: dict[str, Path],
    *,
    run_id: str | None = None,
) -> BenchmarkInfo:
    summary_path = referenced_paths.get("summary")
    if summary_path is not None and "automation_runs" in summary_path.parts:
        text_blob = text_blob + "\n" + summary_path.read_text(encoding="utf-8", errors="replace")

    benchmark_name = _last_string(BENCHMARK_NAME_RE, text_blob)
    benchmark_max_drawdown_pct = read_benchmark_max_drawdown_pct(
        referenced_paths.get("bench"),
        benchmark_name=benchmark_name,
    )
    if benchmark_max_drawdown_pct is None:
        benchmark_max_drawdown_pct = _last_percent(BENCHMARK_MAX_DD_RE, text_blob)
    relation = read_benchmark_relation_metrics(
        referenced_paths.get("equity"),
        referenced_paths.get("bench"),
        benchmark_name=benchmark_name,
        run_id=run_id,
    )

    return BenchmarkInfo(
        benchmark_name=benchmark_name,
        benchmark_return_pct=_last_percent(BENCHMARK_RETURN_RE, text_blob),
        benchmark_cagr_pct=_last_percent(BENCHMARK_CAGR_RE, text_blob),
        benchmark_max_drawdown_pct=benchmark_max_drawdown_pct,
        benchmark_volatility_pct=_last_percent(BENCHMARK_VOL_RE, text_blob),
        benchmark_sharpe_ratio=_last_float(BENCHMARK_SHARPE_RE, text_blob),
        correlation_to_benchmark=relation["correlation_to_benchmark"],
        up_capture_ratio=relation["up_capture_ratio"],
        down_capture_ratio=relation["down_capture_ratio"],
    )


def extract_behavior(
    decision_payloads: list[dict[str, Any]],
    referenced_paths: dict[str, Path],
) -> BehaviorInfo:
    behavior_payloads = _select_behavior_payloads(decision_payloads)
    portfolios = [(payload.get("as_of"), _extract_weights(payload)) for payload in behavior_payloads]
    portfolios = [(str(as_of), weights) for as_of, weights in portfolios if as_of and weights]

    last_as_of = None
    last_portfolio = None
    if portfolios:
        last_as_of, last_portfolio = sorted(portfolios, key=lambda item: item[0])[-1]

    avg_positions = None
    if portfolios:
        avg_positions = sum(_position_count(weights) for _, weights in portfolios) / len(portfolios)

    trades_path = referenced_paths.get("trades")
    trades_count = count_csv_data_rows(trades_path) if trades_path is not None else None
    trades_count_source = str(trades_path) if trades_count is not None and trades_path is not None else None

    if trades_count is None:
        trades_count = estimate_trade_count_from_decisions(portfolios)
        trades_count_source = "decision_bundle_weight_changes" if portfolios else None

    return BehaviorInfo(
        trades_count=trades_count,
        trades_count_source=trades_count_source,
        avg_positions=avg_positions,
        last_as_of=last_as_of,
        last_portfolio=last_portfolio,
    )


def _select_behavior_payloads(decision_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    run_payloads = [payload for payload in decision_payloads if _payload_kind(payload) == "RUN"]
    if run_payloads:
        return run_payloads

    bt_payloads = [payload for payload in decision_payloads if _payload_kind(payload) == "BT"]
    if bt_payloads:
        return bt_payloads

    return decision_payloads


def _payload_kind(payload: dict[str, Any]) -> str:
    kind = payload.get("kind")
    if isinstance(kind, str) and kind.strip():
        return kind.strip().upper()

    source_path = payload.get("_source_path")
    if isinstance(source_path, str):
        name = Path(source_path).name.upper()
        if name.startswith("RUN_"):
            return "RUN"
        if name.startswith("BT_"):
            return "BT"

    return ""


def estimate_trade_count_from_decisions(portfolios: list[tuple[str, dict[str, float]]]) -> int | None:
    if len(portfolios) < 2:
        return None

    count = 0
    previous = portfolios[0][1]
    for _, current in portfolios[1:]:
        tickers = set(previous) | set(current)
        count += sum(1 for ticker in tickers if abs(previous.get(ticker, 0.0) - current.get(ticker, 0.0)) > 1e-12)
        previous = current
    return count


def count_csv_data_rows(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.reader(file_obj)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    return max(0, len(rows) - 1)


def read_last_numeric_csv_value(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None

    with path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        rows = list(reader)

    for row in reversed(rows):
        for key in ("equity", "portfolio_value", "value", "total_value"):
            value = _to_float(row.get(key))
            if value is not None:
                return value
        for value in reversed(list(row.values())):
            numeric = _to_float(value)
            if numeric is not None:
                return numeric
    return None


def read_benchmark_max_drawdown_pct(
    path: Path | None,
    *,
    benchmark_name: str | None = None,
) -> float | None:
    if path is None or not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8", newline="") as file_obj:
            reader = csv.DictReader(
                line for line in file_obj if line.strip() and not line.lstrip().startswith("#")
            )
            rows = list(reader)
            fieldnames = tuple(reader.fieldnames or ())
    except OSError:
        return None

    benchmark_column = _select_benchmark_column(fieldnames, benchmark_name=benchmark_name)
    if benchmark_column is None:
        return None

    values = [
        value
        for value in (_to_float(row.get(benchmark_column)) for row in rows)
        if value is not None and value > 0
    ]
    if len(values) < 2:
        return None

    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        drawdown = value / peak - 1.0
        max_drawdown = min(max_drawdown, drawdown)

    return max_drawdown * 100.0


def read_benchmark_relation_metrics(
    equity_path: Path | None,
    benchmark_path: Path | None,
    *,
    benchmark_name: str | None = None,
    run_id: str | None = None,
) -> dict[str, float | None]:
    empty = {
        "correlation_to_benchmark": None,
        "up_capture_ratio": None,
        "down_capture_ratio": None,
    }
    if not _csv_matches_run_id(benchmark_path, run_id):
        return empty
    if equity_path is not None and not _csv_matches_run_id(equity_path, run_id):
        return empty

    benchmark_rows, benchmark_fieldnames = _read_csv_dicts(benchmark_path)
    if not benchmark_rows:
        return empty

    benchmark_column = _select_benchmark_column(benchmark_fieldnames, benchmark_name=benchmark_name)
    if benchmark_column is None:
        return empty

    benchmark_levels = _read_level_series(benchmark_rows, benchmark_column)
    equity_rows, equity_fieldnames = _read_csv_dicts(equity_path)
    equity_column = _select_equity_column(equity_fieldnames) if equity_rows else None
    strategy_levels = (
        _read_level_series(equity_rows, equity_column)
        if equity_column is not None
        else _read_level_series(benchmark_rows, "equity")
    )

    strategy_returns = _pct_change_by_date(strategy_levels)
    benchmark_returns = _pct_change_by_date(benchmark_levels)
    common_dates = sorted(set(strategy_returns) & set(benchmark_returns))
    if len(common_dates) < 2:
        return empty

    aligned_strategy = [strategy_returns[date] for date in common_dates]
    aligned_benchmark = [benchmark_returns[date] for date in common_dates]
    # Capture ratios use arithmetic mean period returns on aligned daily return series.
    # This keeps the relation metric on the same frequency as the exported equity/benchmark CSV.
    return {
        "correlation_to_benchmark": _correlation(aligned_strategy, aligned_benchmark),
        "up_capture_ratio": _capture_ratio(aligned_strategy, aligned_benchmark, positive=True),
        "down_capture_ratio": _capture_ratio(aligned_strategy, aligned_benchmark, positive=False),
    }


def _read_csv_dicts(path: Path | None) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    if path is None or not path.exists():
        return [], ()

    try:
        with path.open("r", encoding="utf-8", newline="") as file_obj:
            reader = csv.DictReader(
                line for line in file_obj if line.strip() and not line.lstrip().startswith("#")
            )
            rows = list(reader)
            return rows, tuple(reader.fieldnames or ())
    except OSError:
        return [], ()


def _csv_matches_run_id(path: Path | None, run_id: str | None) -> bool:
    if path is None or run_id is None:
        return True
    try:
        with path.open("r", encoding="utf-8", newline="") as file_obj:
            for _ in range(5):
                line = file_obj.readline()
                if not line:
                    break
                match = re.search(r"run_id\s*=\s*(20\d{6}_\d{6})", line)
                if match:
                    return match.group(1) == run_id
    except OSError:
        return False
    return True


def _select_equity_column(fieldnames: tuple[str, ...]) -> str | None:
    for candidate in ("equity", "portfolio_value", "value", "total_value"):
        for fieldname in fieldnames:
            if fieldname.strip().lower() == candidate:
                return fieldname
    for fieldname in fieldnames:
        if fieldname.strip().lower() not in {"date", "as_of"}:
            return fieldname
    return None


def _read_level_series(rows: list[dict[str, str]], value_column: str | None) -> dict[str, float]:
    if value_column is None:
        return {}

    series: dict[str, float] = {}
    for row in rows:
        date = _string_or_none(row.get("date") or row.get("as_of"))
        value = _to_float(row.get(value_column))
        if date is not None and value is not None and value > 0:
            series[date] = value
    return series


def _pct_change_by_date(levels: dict[str, float]) -> dict[str, float]:
    returns: dict[str, float] = {}
    previous_value: float | None = None
    for date in sorted(levels):
        value = levels[date]
        if previous_value is not None and previous_value > 0:
            returns[date] = value / previous_value - 1.0
        previous_value = value
    return returns


def _correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    left_diffs = [value - left_mean for value in left]
    right_diffs = [value - right_mean for value in right]
    numerator = sum(a * b for a, b in zip(left_diffs, right_diffs))
    left_var = sum(value * value for value in left_diffs)
    right_var = sum(value * value for value in right_diffs)
    denominator = (left_var * right_var) ** 0.5
    if denominator <= 0:
        return None
    return numerator / denominator


def _capture_ratio(strategy_returns: list[float], benchmark_returns: list[float], *, positive: bool) -> float | None:
    pairs = [
        (strategy_return, benchmark_return)
        for strategy_return, benchmark_return in zip(strategy_returns, benchmark_returns)
        if (benchmark_return > 0 if positive else benchmark_return < 0)
    ]
    if not pairs:
        return None
    strategy_mean = sum(strategy_return for strategy_return, _ in pairs) / len(pairs)
    benchmark_mean = sum(benchmark_return for _, benchmark_return in pairs) / len(pairs)
    if abs(benchmark_mean) <= 1e-12:
        return None
    return strategy_mean / benchmark_mean


def _select_benchmark_column(
    fieldnames: tuple[str, ...],
    *,
    benchmark_name: str | None = None,
) -> str | None:
    candidates = [
        fieldname
        for fieldname in fieldnames
        if fieldname.strip().lower() not in {"date", "as_of", "equity"}
    ]
    if not candidates:
        return None

    if benchmark_name:
        normalized_name = _normalize_column_token(benchmark_name)
        for fieldname in candidates:
            if normalized_name and normalized_name in _normalize_column_token(fieldname):
                return fieldname

    for fieldname in candidates:
        normalized = fieldname.strip().lower()
        if normalized.startswith("bm") or "benchmark" in normalized:
            return fieldname

    return candidates[0]


def _normalize_column_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def calc_delta(a: object, b: object) -> float | None:
    left = _to_float(a)
    right = _to_float(b)
    if left is None or right is None:
        return None
    return right - left


def winner_higher_is_better(a: object, b: object) -> str:
    left = _to_float(a)
    right = _to_float(b)
    if left is None or right is None:
        return "n/a"
    if right > left:
        return "B"
    if left > right:
        return "A"
    return "tie"


def winner_lower_is_better(a: object, b: object) -> str:
    left = _to_float(a)
    right = _to_float(b)
    if left is None or right is None:
        return "n/a"
    if right < left:
        return "B"
    if left < right:
        return "A"
    return "tie"


def winner_drawdown(a: object, b: object) -> str:
    left = _to_float(a)
    right = _to_float(b)
    if left is None or right is None:
        return "n/a"
    left_abs = abs(left)
    right_abs = abs(right)
    if right_abs < left_abs:
        return "B"
    if left_abs < right_abs:
        return "A"
    return "tie"


def format_delta(
    a: object,
    b: object,
    *,
    metric: str | None = None,
    percent_points: bool | None = None,
) -> str:
    delta = calc_delta(a, b)
    if delta is None:
        return "n/a"
    if abs(delta) < 5e-13:
        delta = 0.0
    sign = "+" if delta > 0 else ""
    if percent_points is None:
        percent_points = metric in PERCENT_POINT_METRICS
    if percent_points:
        return f"{sign}{delta:.2f}pp"
    return f"{sign}{delta:.4f}"


def build_performance_verdict(comparison: dict[str, Any]) -> list[tuple[str, str]]:
    run_a = comparison["run_a"]
    run_b = comparison["run_b"]
    perf_a = run_a["performance"]
    perf_b = run_b["performance"]
    behavior_a = run_a["behavior"]
    behavior_b = run_b["behavior"]

    verdicts = [
        ("return", winner_higher_is_better(perf_a.get("total_return_pct"), perf_b.get("total_return_pct"))),
        ("max_drawdown", winner_drawdown(perf_a.get("max_drawdown_pct"), perf_b.get("max_drawdown_pct"))),
        ("volatility", winner_lower_is_better(perf_a.get("volatility_pct"), perf_b.get("volatility_pct"))),
        ("sharpe", winner_higher_is_better(perf_a.get("sharpe_ratio"), perf_b.get("sharpe_ratio"))),
        ("turnover", winner_lower_is_better(perf_a.get("turnover_pct"), perf_b.get("turnover_pct"))),
        ("trades_count", winner_lower_is_better(behavior_a.get("trades_count"), behavior_b.get("trades_count"))),
    ]

    if perf_a.get("sortino_ratio") is not None or perf_b.get("sortino_ratio") is not None:
        verdicts.append(
            ("sortino", winner_higher_is_better(perf_a.get("sortino_ratio"), perf_b.get("sortino_ratio")))
        )
    if perf_a.get("cagr_pct") is not None or perf_b.get("cagr_pct") is not None:
        verdicts.append(("cagr", winner_higher_is_better(perf_a.get("cagr_pct"), perf_b.get("cagr_pct"))))
    if perf_a.get("alpha_pct") is not None or perf_b.get("alpha_pct") is not None:
        verdicts.append(("alpha", winner_higher_is_better(perf_a.get("alpha_pct"), perf_b.get("alpha_pct"))))

    return verdicts


def build_interpretation(comparison: dict[str, Any]) -> list[str]:
    run_a = comparison["run_a"]
    run_b = comparison["run_b"]
    universe_a = run_a["universe"]
    universe_b = run_b["universe"]
    perf_a = run_a["performance"]
    perf_b = run_b["performance"]
    behavior_a = run_a["behavior"]
    behavior_b = run_b["behavior"]

    lines = []

    if (
        universe_a.get("universe_name") != universe_b.get("universe_name")
        or universe_a.get("universe_hash") != universe_b.get("universe_hash")
    ):
        lines.append("Different universe detected: portfolio differences are expected.")

    if universe_a.get("universe_len") != universe_b.get("universe_len"):
        lines.append(
            f"Universe size differs: A={_display(universe_a.get('universe_len'))}, "
            f"B={_display(universe_b.get('universe_len'))}."
        )

    return_winner = winner_higher_is_better(
        perf_a.get("total_return_pct"),
        perf_b.get("total_return_pct"),
    )
    if return_winner != "n/a":
        lines.append(f"Return winner: {return_winner}.")

    risk_winner = _risk_winner(
        perf_a.get("max_drawdown_pct"),
        perf_b.get("max_drawdown_pct"),
        perf_a.get("volatility_pct"),
        perf_b.get("volatility_pct"),
    )
    if risk_winner != "n/a":
        lines.append(f"Risk winner: {risk_winner}.")

    trading_winner = _trading_activity_lower(
        perf_a.get("turnover_pct"),
        perf_b.get("turnover_pct"),
        behavior_a.get("trades_count"),
        behavior_b.get("trades_count"),
    )
    if trading_winner in {"A", "B"}:
        lines.append(f"Trading activity is lower in {trading_winner}.")
    elif trading_winner == "mixed":
        lines.append("Trading activity is mixed.")

    return lines or ["No interpretation available from the current artifacts."]


def _risk_winner(
    drawdown_a: object,
    drawdown_b: object,
    volatility_a: object,
    volatility_b: object,
) -> str:
    drawdown_winner = winner_drawdown(drawdown_a, drawdown_b)
    volatility_winner = winner_lower_is_better(volatility_a, volatility_b)
    if drawdown_winner == "n/a" or volatility_winner == "n/a":
        return "n/a"
    if drawdown_winner == volatility_winner:
        return drawdown_winner
    return "mixed"


def _trading_activity_lower(
    turnover_a: object,
    turnover_b: object,
    trades_a: object,
    trades_b: object,
) -> str:
    lower: list[str] = []
    turnover_delta = calc_delta(turnover_a, turnover_b)
    if turnover_delta is not None and abs(turnover_delta) >= 5.0:
        lower.append("B" if turnover_delta < 0 else "A")

    trades_delta = calc_delta(trades_a, trades_b)
    if trades_delta is not None and abs(trades_delta) >= 3.0:
        lower.append("B" if trades_delta < 0 else "A")

    if not lower:
        return "n/a"
    unique = set(lower)
    if len(unique) == 1:
        return lower[0]
    return "mixed"


def build_console_report(comparison: dict[str, Any]) -> str:
    run_a = comparison["run_a"]
    run_b = comparison["run_b"]
    lines = [
        "=== Run Comparison ===",
        f"A: {run_a['run_id']}",
        f"B: {run_b['run_id']}",
        "",
        "Config / Universe",
        _row("universe_name", run_a["universe"]["universe_name"], run_b["universe"]["universe_name"]),
        _row("universe_file", run_a["universe"]["universe_file"], run_b["universe"]["universe_file"]),
        _row("universe_len", run_a["universe"]["universe_len"], run_b["universe"]["universe_len"]),
        _row("universe_hash", run_a["universe"]["universe_hash"], run_b["universe"]["universe_hash"]),
        "",
        "Performance",
        _performance_row("final_equity", run_a, run_b),
        _performance_row("total_return_pct", run_a, run_b),
        _performance_row("max_drawdown_pct", run_a, run_b),
        _performance_row("volatility_pct", run_a, run_b),
        _performance_row("sharpe_ratio", run_a, run_b),
        _performance_row("turnover_pct", run_a, run_b),
        *_optional_performance_rows(run_a, run_b),
        "",
        _benchmark_title(comparison),
        *_benchmark_rows(run_a, run_b),
        "",
        "Benchmark Relation",
        *_benchmark_relation_rows(run_a, run_b),
        "",
        "Performance / Trading Verdict",
        *(_verdict_row(label, winner) for label, winner in build_performance_verdict(comparison)),
        "",
        "Trading / Portfolio",
        _row("trades_count", run_a["behavior"]["trades_count"], run_b["behavior"]["trades_count"]),
        _row("avg_positions", _fmt_num(run_a["behavior"]["avg_positions"]), _fmt_num(run_b["behavior"]["avg_positions"])),
        _row("last_as_of", run_a["behavior"]["last_as_of"], run_b["behavior"]["last_as_of"]),
        _row("last_position_count", len(run_a["behavior"]["last_portfolio"] or {}), len(run_b["behavior"]["last_portfolio"] or {})),
        "",
        "Last Decision Tickers",
        _overlap_count_row(comparison),
        _overlap_pct_row(comparison),
        f"common ({len(comparison['last_decision_tickers']['common'])}): {_join(comparison['last_decision_tickers']['common'])}",
        f"only in A ({len(comparison['last_decision_tickers']['only_in_a'])}): {_join(comparison['last_decision_tickers']['only_in_a'])}",
        f"only in B ({len(comparison['last_decision_tickers']['only_in_b'])}): {_join(comparison['last_decision_tickers']['only_in_b'])}",
        "",
        "Interpretation",
        *(f"- {line}" for line in build_interpretation(comparison)),
    ]
    return "\n".join(lines)


def build_markdown_report(comparison: dict[str, Any]) -> str:
    run_a = comparison["run_a"]
    run_b = comparison["run_b"]
    lines = [
        "# Run Comparison Report",
        "",
        "## Runs",
        _md_table(
            ("Side", "Run ID"),
            (
                ("A", run_a["run_id"]),
                ("B", run_b["run_id"]),
            ),
        ),
        "",
        "## Config / Universe",
        _md_table(
            ("Metric", "A", "B"),
            (
                ("universe_name", run_a["universe"]["universe_name"], run_b["universe"]["universe_name"]),
                ("universe_file", run_a["universe"]["universe_file"], run_b["universe"]["universe_file"]),
                ("universe_len", run_a["universe"]["universe_len"], run_b["universe"]["universe_len"]),
                ("universe_hash", run_a["universe"]["universe_hash"], run_b["universe"]["universe_hash"]),
            ),
        ),
        "",
        "## Performance",
        _md_table(
            ("Metric", "A", "B", "Delta"),
            tuple(_performance_table_rows(run_a, run_b)),
            align_right=(1, 2, 3),
        ),
        "",
        f"## {_benchmark_title(comparison)}",
        _md_table(
            ("Metric", "A", "B", "Delta"),
            tuple(_benchmark_table_rows(run_a, run_b)),
            align_right=(1, 2, 3),
        ),
        "",
        "## Benchmark Relation",
        "_Daily return relations; capture ratios use arithmetic mean returns in positive/negative benchmark periods._",
        "",
        _md_table(
            ("Metric", "A", "B", "Delta"),
            tuple(_benchmark_relation_table_rows(run_a, run_b)),
            align_right=(1, 2, 3),
        ),
        "",
        "## Performance / Trading Verdict",
        _md_table(
            ("Metric", "Winner"),
            tuple(build_performance_verdict(comparison)),
        ),
        "",
        "## Trading / Portfolio",
        _md_table(
            ("Metric", "A", "B"),
            (
                ("trades_count", run_a["behavior"]["trades_count"], run_b["behavior"]["trades_count"]),
                ("avg_positions", _fmt_num(run_a["behavior"]["avg_positions"]), _fmt_num(run_b["behavior"]["avg_positions"])),
                ("last_as_of", run_a["behavior"]["last_as_of"], run_b["behavior"]["last_as_of"]),
                ("last_position_count", len(run_a["behavior"]["last_portfolio"] or {}), len(run_b["behavior"]["last_portfolio"] or {})),
            ),
        ),
        "",
        "## Last Decision Tickers",
        f"overlap_count: {_overlap_count_value(comparison)}  ",
        f"overlap_pct: {_overlap_pct_value(comparison)}",
        "",
        _md_table(
            ("Group", "Count", "Tickers"),
            (
                (
                    "Common",
                    len(comparison["last_decision_tickers"]["common"]),
                    _join_or_na(comparison["last_decision_tickers"]["common"]),
                ),
                (
                    "Only in A",
                    len(comparison["last_decision_tickers"]["only_in_a"]),
                    _join_or_na(comparison["last_decision_tickers"]["only_in_a"]),
                ),
                (
                    "Only in B",
                    len(comparison["last_decision_tickers"]["only_in_b"]),
                    _join_or_na(comparison["last_decision_tickers"]["only_in_b"]),
                ),
            ),
            align_right=(1,),
        ),
        "",
        "## Interpretation",
        *(f"- {line}" for line in build_interpretation(comparison)),
        "",
    ]
    return "\n".join(lines)


def _load_manifest(output_dir: Path | None) -> dict[str, Any]:
    if output_dir is None:
        return {}
    return _read_json(output_dir / "run_manifest.json")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file_obj:
            payload = json.load(file_obj)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _manifest_cwd(manifest: dict[str, Any]) -> Path | None:
    for step in ("backtest", "runner"):
        payload = manifest.get(step)
        if isinstance(payload, dict) and isinstance(payload.get("cwd"), str):
            return Path(payload["cwd"])
    return None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _universe_from_mapping(payload: dict[str, Any]) -> UniverseInfo:
    return UniverseInfo(
        universe_name=_string_or_none(payload.get("universe_name")),
        universe_file=_string_or_none(payload.get("universe_file")),
        universe_len=_int_or_none(payload.get("universe_len")),
        universe_hash=_string_or_none(payload.get("universe_hash")),
    )


def _extract_weights(payload: dict[str, Any]) -> dict[str, float]:
    for key in ("new_weights", "weights", "positions"):
        value = payload.get(key)
        if isinstance(value, dict):
            return {str(ticker): float(weight) for ticker, weight in value.items() if _to_float(weight) is not None}
        if isinstance(value, list):
            result = {}
            for item in value:
                if not isinstance(item, dict):
                    continue
                ticker = item.get("ticker")
                weight = _to_float(item.get("weight"))
                if ticker is not None and weight is not None:
                    result[str(ticker)] = weight
            if result:
                return result
    return {}


def _position_count(weights: dict[str, float]) -> int:
    return sum(1 for ticker, weight in weights.items() if ticker.upper() != "CASH" and abs(weight) > 1e-12)


def _last_percent(pattern: re.Pattern[str], text: str) -> float | None:
    return _last_float(pattern, text)


def _last_float(pattern: re.Pattern[str], text: str) -> float | None:
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return float(matches[-1].group("value"))


def _last_string(pattern: re.Pattern[str], text: str) -> str | None:
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    return matches[-1].group("value").strip()


def _last_portfolio_sharpe(text: str) -> float | None:
    values = []
    for line in text.splitlines():
        if not line.lstrip().startswith("Volatility:"):
            continue
        match = SHARPE_RE.search(line)
        if match:
            values.append(float(match.group("value")))
    return values[-1] if values else _last_float(SHARPE_RE, text)


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip().replace("%", ""))
    except ValueError:
        return None


def _int_or_none(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _snapshot_to_dict(snapshot: RunSnapshot) -> dict[str, Any]:
    return {
        "run_id": snapshot.run_id,
        "output_dir": str(snapshot.output_dir) if snapshot.output_dir is not None else None,
        "decisions_dir": str(snapshot.decisions_dir) if snapshot.decisions_dir is not None else None,
        "universe": {
            "universe_name": snapshot.universe.universe_name,
            "universe_file": snapshot.universe.universe_file,
            "universe_len": snapshot.universe.universe_len,
            "universe_hash": snapshot.universe.universe_hash,
        },
        "benchmark": {
            "benchmark_name": snapshot.benchmark.benchmark_name,
            "benchmark_return_pct": snapshot.benchmark.benchmark_return_pct,
            "benchmark_cagr_pct": snapshot.benchmark.benchmark_cagr_pct,
            "benchmark_max_drawdown_pct": snapshot.benchmark.benchmark_max_drawdown_pct,
            "benchmark_volatility_pct": snapshot.benchmark.benchmark_volatility_pct,
            "benchmark_sharpe_ratio": snapshot.benchmark.benchmark_sharpe_ratio,
            "correlation_to_benchmark": snapshot.benchmark.correlation_to_benchmark,
            "up_capture_ratio": snapshot.benchmark.up_capture_ratio,
            "down_capture_ratio": snapshot.benchmark.down_capture_ratio,
        },
        "performance": {
            "final_equity": snapshot.performance.final_equity,
            "total_return_pct": snapshot.performance.total_return_pct,
            "cagr_pct": snapshot.performance.cagr_pct,
            "max_drawdown_pct": snapshot.performance.max_drawdown_pct,
            "volatility_pct": snapshot.performance.volatility_pct,
            "sharpe_ratio": snapshot.performance.sharpe_ratio,
            "sortino_ratio": snapshot.performance.sortino_ratio,
            "alpha_pct": snapshot.performance.alpha_pct,
            "turnover_pct": snapshot.performance.turnover_pct,
        },
        "behavior": {
            "trades_count": snapshot.behavior.trades_count,
            "trades_count_source": snapshot.behavior.trades_count_source,
            "avg_positions": snapshot.behavior.avg_positions,
            "last_as_of": snapshot.behavior.last_as_of,
            "last_portfolio": snapshot.behavior.last_portfolio,
        },
        "sources": dict(snapshot.sources),
    }


def _row(label: str, left: object, right: object) -> str:
    return f"{label:<20} A={_display(left):<32} B={_display(right)}"


def _performance_row(metric: str, run_a: dict[str, Any], run_b: dict[str, Any]) -> str:
    left_raw = run_a["performance"].get(metric)
    right_raw = run_b["performance"].get(metric)
    left = _format_performance_value(metric, left_raw)
    right = _format_performance_value(metric, right_raw)
    delta = format_delta(metric=metric, a=left_raw, b=right_raw)
    return f"{metric:<20} A={_display(left):<12} B={_display(right):<12} Delta={delta}"


def _optional_performance_rows(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[str]:
    rows = []
    for metric in ("cagr_pct", "sortino_ratio", "alpha_pct"):
        if run_a["performance"].get(metric) is not None or run_b["performance"].get(metric) is not None:
            rows.append(_performance_row(metric, run_a, run_b))
    return rows


def _performance_table_rows(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[tuple[str, str | None, str | None, str]]:
    metrics = [
        "final_equity",
        "total_return_pct",
        "max_drawdown_pct",
        "volatility_pct",
        "sharpe_ratio",
        "turnover_pct",
    ]
    metrics.extend(
        metric
        for metric in ("cagr_pct", "sortino_ratio", "alpha_pct")
        if run_a["performance"].get(metric) is not None or run_b["performance"].get(metric) is not None
    )
    return [
        (
            metric,
            _format_performance_value(metric, run_a["performance"].get(metric)),
            _format_performance_value(metric, run_b["performance"].get(metric)),
            format_delta(metric=metric, a=run_a["performance"].get(metric), b=run_b["performance"].get(metric)),
        )
        for metric in metrics
    ]


def _benchmark_title(comparison: dict[str, Any]) -> str:
    run_a = comparison["run_a"]
    run_b = comparison["run_b"]
    names = {
        name
        for name in (
            run_a["benchmark"].get("benchmark_name"),
            run_b["benchmark"].get("benchmark_name"),
        )
        if name
    }
    if len(names) == 1:
        return f"Benchmark ({next(iter(names))})"
    return "Benchmark"


def _benchmark_rows(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[str]:
    return [_benchmark_row(metric, run_a, run_b) for metric in _benchmark_metrics()]


def _benchmark_relation_rows(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[str]:
    return [_benchmark_row(metric, run_a, run_b) for metric in _benchmark_relation_metrics()]


def _benchmark_row(metric: str, run_a: dict[str, Any], run_b: dict[str, Any]) -> str:
    left_raw = run_a["benchmark"].get(metric)
    right_raw = run_b["benchmark"].get(metric)
    left = _format_performance_value(metric, left_raw)
    right = _format_performance_value(metric, right_raw)
    delta = format_delta(metric=metric, a=left_raw, b=right_raw)
    return f"{metric:<30} A={_display(left):<12} B={_display(right):<12} Delta={delta}"


def _benchmark_table_rows(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[tuple[str, str | None, str | None, str]]:
    return [
        (
            metric,
            _format_performance_value(metric, run_a["benchmark"].get(metric)),
            _format_performance_value(metric, run_b["benchmark"].get(metric)),
            format_delta(metric=metric, a=run_a["benchmark"].get(metric), b=run_b["benchmark"].get(metric)),
        )
        for metric in _benchmark_metrics()
    ]


def _benchmark_relation_table_rows(run_a: dict[str, Any], run_b: dict[str, Any]) -> list[tuple[str, str | None, str | None, str]]:
    return [
        (
            metric,
            _format_performance_value(metric, run_a["benchmark"].get(metric)),
            _format_performance_value(metric, run_b["benchmark"].get(metric)),
            format_delta(metric=metric, a=run_a["benchmark"].get(metric), b=run_b["benchmark"].get(metric)),
        )
        for metric in _benchmark_relation_metrics()
    ]


def _benchmark_metrics() -> tuple[str, ...]:
    return (
        "benchmark_return_pct",
        "benchmark_cagr_pct",
        "benchmark_max_drawdown_pct",
        "benchmark_volatility_pct",
        "benchmark_sharpe_ratio",
    )


def _benchmark_relation_metrics() -> tuple[str, ...]:
    return (
        "correlation_to_benchmark",
        "up_capture_ratio",
        "down_capture_ratio",
    )


def _format_performance_value(metric: str, value: object) -> str | None:
    if metric in PERCENT_POINT_METRICS:
        return _fmt_pct(value)
    return _fmt_num(value)


def _verdict_row(label: str, winner: str) -> str:
    return f"{label:<20} {winner}"


def _overlap_count_row(comparison: dict[str, Any]) -> str:
    return f"{'overlap_count':<20} {_overlap_count_value(comparison)}"


def _overlap_pct_row(comparison: dict[str, Any]) -> str:
    return f"{'overlap_pct':<20} {_overlap_pct_value(comparison)}"


def _overlap_count_value(comparison: dict[str, Any]) -> str:
    tickers = comparison["last_decision_tickers"]
    count = tickers.get("overlap_count")
    denominator = tickers.get("overlap_denominator")
    if count is None or denominator is None:
        return "n/a"
    return f"{count} / {denominator}"


def _overlap_pct_value(comparison: dict[str, Any]) -> str:
    value = comparison["last_decision_tickers"].get("overlap_pct")
    return _fmt_pct(value) or "n/a"


def _display(value: object) -> str:
    return "n/a" if value is None else str(value)


def _fmt_num(value: object) -> str | None:
    numeric = _to_float(value)
    return None if numeric is None else f"{numeric:.4f}"


def _fmt_pct(value: object) -> str | None:
    numeric = _to_float(value)
    return None if numeric is None else f"{numeric:.2f}%"


def _join(values: list[str]) -> str:
    return ", ".join(values) if values else "-"


def _md_table(
    headers: tuple[str, ...],
    rows: tuple[tuple[object, ...], ...],
    *,
    align_right: tuple[int, ...] = (),
) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---:" if index in align_right else "---" for index, _ in enumerate(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_display(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def _join_or_na(values: list[str]) -> str:
    return ", ".join(values) if values else "n/a"


def default_markdown_output_dir() -> Path:
    return Path("reports") / "run_comparisons"


def markdown_report_path(output_dir: str | Path, run_a: str, run_b: str) -> Path:
    return Path(output_dir) / f"compare_{run_a}_vs_{run_b}.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two existing automation run outputs.")
    parser.add_argument("run_a", help="First run_id, e.g. 20260501_004942")
    parser.add_argument("run_b", help="Second run_id, e.g. 20260501_120332")
    parser.add_argument("--runs-root", default=str(default_runs_root()), help="Root directory with automation run folders")
    parser.add_argument("--decisions-root", default=str(default_decisions_root()), help="Root directory with decision run_id folders")
    parser.add_argument("--json-out", help="Optional path to write JSON comparison")
    parser.add_argument("--md-out", help="Optional path to write Markdown comparison")
    parser.add_argument(
        "--export-md",
        action="store_true",
        help="Write a Markdown report to reports/run_comparisons by default",
    )
    parser.add_argument(
        "--output-dir",
        default=str(default_markdown_output_dir()),
        help="Directory for --export-md Markdown reports",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    comparison = compare_runs(
        args.run_a,
        args.run_b,
        runs_root=args.runs_root,
        decisions_root=args.decisions_root,
    )
    print(build_console_report(comparison))

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.md_out:
        output_path = Path(args.md_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(build_markdown_report(comparison), encoding="utf-8")

    if args.export_md:
        output_path = markdown_report_path(args.output_dir, args.run_a, args.run_b)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(build_markdown_report(comparison), encoding="utf-8")
        print()
        print("Markdown report written:")
        print(output_path.as_posix())


if __name__ == "__main__":
    main()

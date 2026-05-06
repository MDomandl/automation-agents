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
VOL_RE = re.compile(r"^\s*Volatility:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%", re.MULTILINE)
SHARPE_RE = re.compile(r"Sharpe(?:\(0%\))?:\s*(?P<value>[-+]?\d+(?:\.\d+)?)")
MAX_DD_RE = re.compile(r"Max DD:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
TURNOVER_RE = re.compile(r"Avg Turnover:\s*(?P<value>[-+]?\d+(?:\.\d+)?)%")
OUTPUT_PATH_RE = re.compile(r"^(?P<label>Equity|Positions|Trades|Summary):\s*(?P<path>.+?)\s*$", re.MULTILINE)


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
    max_drawdown_pct: float | None = None
    volatility_pct: float | None = None
    sharpe_ratio: float | None = None
    turnover_pct: float | None = None


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

    return {
        "run_a": _snapshot_to_dict(snapshot_a),
        "run_b": _snapshot_to_dict(snapshot_b),
        "last_decision_tickers": {
            "common": sorted(tickers_a & tickers_b),
            "only_in_a": sorted(tickers_a - tickers_b),
            "only_in_b": sorted(tickers_b - tickers_a),
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
                and (output_dir is None or _is_relative_to(candidate, output_dir))
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
        max_drawdown_pct=_last_percent(MAX_DD_RE, text_blob),
        volatility_pct=_last_percent(VOL_RE, text_blob),
        sharpe_ratio=_last_portfolio_sharpe(text_blob),
        turnover_pct=_last_percent(TURNOVER_RE, text_blob),
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
        _row("final_equity", _fmt_num(run_a["performance"]["final_equity"]), _fmt_num(run_b["performance"]["final_equity"])),
        _row("total_return_pct", _fmt_pct(run_a["performance"]["total_return_pct"]), _fmt_pct(run_b["performance"]["total_return_pct"])),
        _row("max_drawdown_pct", _fmt_pct(run_a["performance"]["max_drawdown_pct"]), _fmt_pct(run_b["performance"]["max_drawdown_pct"])),
        _row("volatility_pct", _fmt_pct(run_a["performance"]["volatility_pct"]), _fmt_pct(run_b["performance"]["volatility_pct"])),
        _row("sharpe_ratio", _fmt_num(run_a["performance"]["sharpe_ratio"]), _fmt_num(run_b["performance"]["sharpe_ratio"])),
        _row("turnover_pct", _fmt_pct(run_a["performance"]["turnover_pct"]), _fmt_pct(run_b["performance"]["turnover_pct"])),
        "",
        "Trading / Portfolio",
        _row("trades_count", run_a["behavior"]["trades_count"], run_b["behavior"]["trades_count"]),
        _row("avg_positions", _fmt_num(run_a["behavior"]["avg_positions"]), _fmt_num(run_b["behavior"]["avg_positions"])),
        _row("last_as_of", run_a["behavior"]["last_as_of"], run_b["behavior"]["last_as_of"]),
        _row("last_position_count", len(run_a["behavior"]["last_portfolio"] or {}), len(run_b["behavior"]["last_portfolio"] or {})),
        "",
        "Last Decision Tickers",
        f"common ({len(comparison['last_decision_tickers']['common'])}): {_join(comparison['last_decision_tickers']['common'])}",
        f"only in A ({len(comparison['last_decision_tickers']['only_in_a'])}): {_join(comparison['last_decision_tickers']['only_in_a'])}",
        f"only in B ({len(comparison['last_decision_tickers']['only_in_b'])}): {_join(comparison['last_decision_tickers']['only_in_b'])}",
    ]
    return "\n".join(lines)


def build_markdown_report(comparison: dict[str, Any]) -> str:
    run_a = comparison["run_a"]
    run_b = comparison["run_b"]
    lines = [
        "# Run Comparison",
        "",
        f"- A: `{run_a['run_id']}`",
        f"- B: `{run_b['run_id']}`",
        "",
        "## Config / Universe",
        _md_table(
            ("Field", "A", "B"),
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
            ("Metric", "A", "B"),
            (
                ("final_equity", _fmt_num(run_a["performance"]["final_equity"]), _fmt_num(run_b["performance"]["final_equity"])),
                ("total_return_pct", _fmt_pct(run_a["performance"]["total_return_pct"]), _fmt_pct(run_b["performance"]["total_return_pct"])),
                ("max_drawdown_pct", _fmt_pct(run_a["performance"]["max_drawdown_pct"]), _fmt_pct(run_b["performance"]["max_drawdown_pct"])),
                ("volatility_pct", _fmt_pct(run_a["performance"]["volatility_pct"]), _fmt_pct(run_b["performance"]["volatility_pct"])),
                ("sharpe_ratio", _fmt_num(run_a["performance"]["sharpe_ratio"]), _fmt_num(run_b["performance"]["sharpe_ratio"])),
                ("turnover_pct", _fmt_pct(run_a["performance"]["turnover_pct"]), _fmt_pct(run_b["performance"]["turnover_pct"])),
            ),
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
        f"- common ({len(comparison['last_decision_tickers']['common'])}): {_join(comparison['last_decision_tickers']['common'])}",
        f"- only in A ({len(comparison['last_decision_tickers']['only_in_a'])}): {_join(comparison['last_decision_tickers']['only_in_a'])}",
        f"- only in B ({len(comparison['last_decision_tickers']['only_in_b'])}): {_join(comparison['last_decision_tickers']['only_in_b'])}",
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
        "performance": {
            "final_equity": snapshot.performance.final_equity,
            "total_return_pct": snapshot.performance.total_return_pct,
            "max_drawdown_pct": snapshot.performance.max_drawdown_pct,
            "volatility_pct": snapshot.performance.volatility_pct,
            "sharpe_ratio": snapshot.performance.sharpe_ratio,
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


def _md_table(headers: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_display(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two existing automation run outputs.")
    parser.add_argument("run_a", help="First run_id, e.g. 20260501_004942")
    parser.add_argument("run_b", help="Second run_id, e.g. 20260501_120332")
    parser.add_argument("--runs-root", default=str(default_runs_root()), help="Root directory with automation run folders")
    parser.add_argument("--decisions-root", default=str(default_decisions_root()), help="Root directory with decision run_id folders")
    parser.add_argument("--json-out", help="Optional path to write JSON comparison")
    parser.add_argument("--md-out", help="Optional path to write Markdown comparison")
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


if __name__ == "__main__":
    main()

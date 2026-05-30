from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.compare_runs import (
    default_decisions_root,
    default_runs_root,
    load_decision_payloads,
    load_run_snapshot,
)
from scripts.run_max_per_sector_testmatrix import (
    SectorMetrics,
    _format_sector_distribution,
    build_sector_metrics,
    replace_sector_limits,
)
from scripts.run_max_turnover_cap_testmatrix import replace_benchmark, replace_max_turnover_cap
from scripts.run_sp500_testmatrix import (
    PROFILE_NAMES,
    UNIVERSES,
    _replace_universe_section,
    default_ai_agents_root,
)
from scripts.run_top_k_testmatrix import (
    _fmt_num,
    _fmt_pct,
    _md_table,
    _snapshot_success,
    replace_top_k,
)


BALANCED_TOP_K = 15
BALANCED_MAX_PER_SECTOR = 2
BALANCED_MAX_TURNOVER_CAP = 0.20
BALANCED_BENCHMARK = "SXR8.DE"
BALANCED_CASH_YIELD_ANNUAL = 0.0
BALANCED_REGIME_SMA_DAYS = 200
REPORT_DIR = Path("reports") / "strategy_analysis" / "regime_cash"


@dataclass(frozen=True, slots=True)
class RegimeVariant:
    name: str
    file_stem: str
    require_above_sma: bool
    regime_below_action: str
    include_cash: bool
    character: str
    skip_reason: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.skip_reason is None


@dataclass(frozen=True, slots=True)
class CashMetrics:
    average_cash_pct: float | None = None
    max_cash_pct: float | None = None
    time_in_market_pct: float | None = None
    time_in_cash_pct: float | None = None
    regime_off_count: int | None = None
    regime_switch_count: int | None = None
    warning: str | None = None


@dataclass(frozen=True, slots=True)
class RegimeRunResult:
    test_id: str
    regime_variant: str
    require_above_sma: bool
    regime_below_action: str
    include_cash: bool
    profile: str
    run_id: str
    report_path: Path
    total_return_pct: float | None
    cagr_pct: float | None
    alpha_pct: float | None
    max_drawdown_pct: float | None
    volatility_pct: float | None
    sharpe_ratio: float | None
    turnover_pct: float | None
    trades_count: int | None
    benchmark_cagr_pct: float | None
    benchmark_max_drawdown_pct: float | None
    benchmark_sharpe_ratio: float | None
    up_capture_ratio: float | None
    down_capture_ratio: float | None
    success: bool
    sector_metrics: SectorMetrics = field(default_factory=SectorMetrics)
    cash_metrics: CashMetrics = field(default_factory=CashMetrics)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run sp500 Balanced v2 regime/cash sensitivity matrix."
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=PROFILE_NAMES,
        default=list(PROFILE_NAMES),
        help="Profiles to run. Defaults to short medium long.",
    )
    parser.add_argument(
        "--include-cash-variant",
        action="store_true",
        help="Also run cash_variante if explicitly requested.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(REPORT_DIR),
        help="Directory for regime/cash reports.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ai_agents_dir = default_ai_agents_root()
    aktien_oop_dir = ai_agents_dir / "aktien_oop"
    backtest_config_path = aktien_oop_dir / "backtest_config.toml"
    runner_config_path = aktien_oop_dir / "configs" / "runner_config.toml"
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    original_backtest_config = backtest_config_path.read_text(encoding="utf-8")
    original_runner_config = runner_config_path.read_text(encoding="utf-8")

    variants = _variants(include_cash_variant=bool(args.include_cash_variant))
    results: list[RegimeRunResult] = []
    skipped = [variant for variant in variants if not variant.is_valid]
    try:
        test_index = 1
        for variant in (variant for variant in variants if variant.is_valid):
            for profile in args.profiles:
                test_id = f"R{test_index}"
                test_index += 1
                print(f"=== {test_id} {variant.name} {profile.upper()} ===")
                run_id = _run_for_regime_variant(
                    profile=profile,
                    variant=variant,
                    backtest_config_path=backtest_config_path,
                    runner_config_path=runner_config_path,
                )
                snapshot = load_run_snapshot(
                    run_id,
                    runs_root=default_runs_root(),
                    decisions_root=default_decisions_root(),
                )
                report_path = report_dir / f"{variant.file_stem}_{profile.upper()}.md"
                report_path.write_text(
                    build_run_report(
                        test_id=test_id,
                        variant=variant,
                        profile=profile,
                        snapshot=snapshot,
                    ),
                    encoding="utf-8",
                )
                result = _build_result(
                    test_id=test_id,
                    variant=variant,
                    profile=profile,
                    run_id=run_id,
                    report_path=report_path,
                    snapshot=snapshot,
                )
                results.append(result)
                print(f"run_id: {run_id}")
                print(f"report: {report_path.as_posix()}")
                print()
    finally:
        backtest_config_path.write_text(original_backtest_config, encoding="utf-8")
        runner_config_path.write_text(original_runner_config, encoding="utf-8")

    summary_path = report_dir / "regime_cash_summary.md"
    summary_path.write_text(build_summary(results, skipped), encoding="utf-8")
    print("Summary written:")
    print(summary_path.as_posix())


def _variants(*, include_cash_variant: bool) -> tuple[RegimeVariant, ...]:
    variants = [
        RegimeVariant(
            name="defensiv_cash",
            file_stem="regime_defensive_cash",
            require_above_sma=True,
            regime_below_action="SELL",
            include_cash=True,
            character="bei negativem Regime in Cash",
        ),
        RegimeVariant(
            name="defensiv_hold",
            file_stem="regime_defensive_hold",
            require_above_sma=True,
            regime_below_action="HOLD",
            include_cash=False,
            character="Regime beachten, aber nicht in Cash wechseln",
        ),
        RegimeVariant(
            name="immer_investiert",
            file_stem="regime_always_invested",
            require_above_sma=False,
            regime_below_action="HOLD",
            include_cash=False,
            character="keine Regime-/Cash-Bremse",
        ),
    ]
    variants.append(
        RegimeVariant(
            name="cash_variante",
            file_stem="regime_cash_variant",
            require_above_sma=False,
            regime_below_action="HOLD",
            include_cash=True,
            character="Cash ohne Regime",
            skip_reason=(
                "include_cash has no clean effect without an active SELL regime-off transition "
                "in current sizing."
            ),
        )
    )
    return tuple(variants)


def _run_for_regime_variant(
    *,
    profile: str,
    variant: RegimeVariant,
    backtest_config_path: Path,
    runner_config_path: Path,
) -> str:
    _write_matrix_config(backtest_config_path, variant)
    _write_matrix_config(runner_config_path, variant)

    command = [sys.executable, "-B", "-m", "scripts.run_bt_run_agent", "--profile", profile]
    print(f"Running {profile.upper()} {variant.name}: {' '.join(command)}")
    completed = subprocess.run(
        command,
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Run failed for profile={profile} variant={variant.name}\n"
            f"returncode={completed.returncode}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    run_id = _extract_run_id(completed.stdout)
    if run_id is None:
        raise RuntimeError(
            f"Could not extract run_id for profile={profile} variant={variant.name}\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    return run_id


def _write_matrix_config(path: Path, variant: RegimeVariant) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_universe_section(text, UNIVERSES["sp500"])
    text = replace_top_k(text, BALANCED_TOP_K)
    text = replace_sector_limits(
        text,
        use_sector_limits=True,
        max_per_sector=BALANCED_MAX_PER_SECTOR,
    )
    text = replace_max_turnover_cap(text, BALANCED_MAX_TURNOVER_CAP)
    text = replace_benchmark(text, BALANCED_BENCHMARK)
    text = replace_regime_cash(text, variant)
    path.write_text(text, encoding="utf-8")


def replace_regime_cash(text: str, variant: RegimeVariant) -> str:
    text = _replace_or_insert_top_level_scalar(
        text,
        "include_cash",
        _bool_text(variant.include_cash),
    )
    text = _replace_or_insert_top_level_scalar(
        text,
        "cash_yield_annual",
        f"{BALANCED_CASH_YIELD_ANNUAL:.2f}",
    )
    text = _replace_or_insert_section_scalar(
        text,
        "regime",
        "require_above_sma",
        _bool_text(variant.require_above_sma),
    )
    text = _replace_or_insert_section_scalar(
        text,
        "regime",
        "regime_sma_days",
        str(BALANCED_REGIME_SMA_DAYS),
    )
    text = _replace_or_insert_section_scalar(
        text,
        "regime",
        "regime_below_action",
        f'"{variant.regime_below_action}"',
    )
    return text


def _replace_or_insert_top_level_scalar(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    section = ""
    replaced = False
    inserted = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if not replaced and not inserted:
                result.append(f"{key} = {value}")
                inserted = True
            section = stripped.strip("[]").strip().lower()
            result.append(line)
            continue
        if section == "" and stripped.startswith(f"{key}"):
            prefix, _, rest = line.partition("=")
            result.append(f"{prefix}= {value}{_comment(rest)}")
            replaced = True
            continue
        result.append(line)
    if not replaced and not inserted:
        result.extend(["", f"{key} = {value}"])
    return "\n".join(result) + "\n"


def _replace_or_insert_section_scalar(text: str, section_name: str, key: str, value: str) -> str:
    lines = text.splitlines()
    result: list[str] = []
    section = ""
    seen_section = False
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if section == section_name and not replaced:
                result.append(f"{key} = {value}")
                replaced = True
            section = stripped.strip("[]").strip().lower()
            seen_section = seen_section or section == section_name
            result.append(line)
            continue
        if section == section_name and stripped.startswith(key):
            prefix, _, rest = line.partition("=")
            result.append(f"{prefix}= {value}{_comment(rest)}")
            replaced = True
            continue
        result.append(line)
    if section == section_name and not replaced:
        result.append(f"{key} = {value}")
    elif not seen_section:
        result.extend(["", f"[{section_name}]", f"{key} = {value}"])
    return "\n".join(result) + "\n"


def _comment(rest: str) -> str:
    if "#" not in rest:
        return ""
    _, _, comment_tail = rest.partition("#")
    return "  #" + comment_tail


def _extract_run_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        if line.startswith("run_id:"):
            return line.split(":", 1)[1].strip()
    return None


def _build_result(
    *,
    test_id: str,
    variant: RegimeVariant,
    profile: str,
    run_id: str,
    report_path: Path,
    snapshot: Any,
) -> RegimeRunResult:
    perf = snapshot.performance
    bench = snapshot.benchmark
    behavior = snapshot.behavior
    return RegimeRunResult(
        test_id=test_id,
        regime_variant=variant.name,
        require_above_sma=variant.require_above_sma,
        regime_below_action=variant.regime_below_action,
        include_cash=variant.include_cash,
        profile=profile.upper(),
        run_id=run_id,
        report_path=report_path,
        total_return_pct=perf.total_return_pct,
        cagr_pct=perf.cagr_pct,
        alpha_pct=perf.alpha_pct,
        max_drawdown_pct=perf.max_drawdown_pct,
        volatility_pct=perf.volatility_pct,
        sharpe_ratio=perf.sharpe_ratio,
        turnover_pct=perf.turnover_pct,
        trades_count=behavior.trades_count,
        benchmark_cagr_pct=bench.benchmark_cagr_pct,
        benchmark_max_drawdown_pct=bench.benchmark_max_drawdown_pct,
        benchmark_sharpe_ratio=bench.benchmark_sharpe_ratio,
        up_capture_ratio=bench.up_capture_ratio,
        down_capture_ratio=bench.down_capture_ratio,
        success=_snapshot_success(snapshot),
        sector_metrics=build_sector_metrics(snapshot),
        cash_metrics=build_cash_metrics(snapshot),
    )


def build_cash_metrics(snapshot: Any) -> CashMetrics:
    decisions_dir = getattr(snapshot, "decisions_dir", None)
    payloads = load_decision_payloads(decisions_dir)
    selected = _select_cash_payloads(payloads)
    cash_values = [_cash_weight(payload) for payload in selected]
    cash_values = [value for value in cash_values if value is not None]

    warning = None if cash_values else "cash metrics unavailable: no decision weights"
    average_cash_pct = sum(cash_values) / len(cash_values) * 100.0 if cash_values else None
    max_cash_pct = max(cash_values) * 100.0 if cash_values else None
    time_in_cash_pct = (
        sum(1 for value in cash_values if value >= 0.999) / len(cash_values) * 100.0
        if cash_values
        else None
    )
    time_in_market_pct = (
        sum(1 for value in cash_values if value < 0.999) / len(cash_values) * 100.0
        if cash_values
        else None
    )

    regime_off_count, regime_switch_count = _regime_counts(snapshot)
    return CashMetrics(
        average_cash_pct=average_cash_pct,
        max_cash_pct=max_cash_pct,
        time_in_market_pct=time_in_market_pct,
        time_in_cash_pct=time_in_cash_pct,
        regime_off_count=regime_off_count,
        regime_switch_count=regime_switch_count,
        warning=warning,
    )


def _select_cash_payloads(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bt_payloads = [payload for payload in payloads if _payload_kind(payload) == "BT"]
    if bt_payloads:
        return bt_payloads
    run_payloads = [payload for payload in payloads if _payload_kind(payload) == "RUN"]
    return run_payloads or payloads


def _payload_kind(payload: dict[str, Any]) -> str:
    kind = payload.get("kind")
    if isinstance(kind, str) and kind.strip():
        return kind.strip().upper()
    source_path = payload.get("_source_path")
    if isinstance(source_path, str):
        name = Path(source_path).name.upper()
        if name.startswith("BT_"):
            return "BT"
        if name.startswith("RUN_"):
            return "RUN"
    return ""


def _cash_weight(payload: dict[str, Any]) -> float | None:
    weights = payload.get("new_weights")
    if not isinstance(weights, dict):
        weights = payload.get("weights")
    if not isinstance(weights, dict):
        return None
    try:
        return float(weights.get("CASH", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None


def _regime_counts(snapshot: Any) -> tuple[int | None, int | None]:
    output_dir = getattr(snapshot, "output_dir", None)
    if output_dir is None:
        return None, None
    text = "\n".join(
        _read_text(path)
        for path in (
            output_dir / "backtest_stdout.txt",
            output_dir / "runner_stdout.txt",
            output_dir / "runner_stderr.txt",
        )
    )
    actions = []
    for match in re.finditer(r"\[DBG\]\[REGIME\].*?decision=(\{.*?\})", text):
        raw = match.group(1)
        ok_false = "'ok': False" in raw or '"ok": false' in raw
        action_match = re.search(r"['\"]action['\"]:\s*['\"](?P<action>\w+)['\"]", raw)
        action = action_match.group("action").upper() if action_match else ("OFF" if ok_false else "PROCEED")
        actions.append(action if ok_false else "PROCEED")
    if not actions:
        return None, None
    off_count = sum(1 for action in actions if action != "PROCEED")
    switch_count = sum(1 for left, right in zip(actions, actions[1:]) if left != right)
    return off_count, switch_count


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def build_run_report(
    *,
    test_id: str,
    variant: RegimeVariant,
    profile: str,
    snapshot: Any,
) -> str:
    result = _build_result(
        test_id=test_id,
        variant=variant,
        profile=profile,
        run_id=snapshot.run_id,
        report_path=Path(),
        snapshot=snapshot,
    )
    sector_metrics = result.sector_metrics
    cash_metrics = result.cash_metrics
    perf = snapshot.performance
    bench = snapshot.benchmark
    behavior = snapshot.behavior
    lines = [
        "# Regime/Cash Run Report",
        "",
        "## Run",
        _md_table(
            ("Metric", "Value"),
            (
                ("test_id", test_id),
                ("universe", "sp500"),
                ("top_k", BALANCED_TOP_K),
                ("use_sector_limits", "true"),
                ("max_per_sector", BALANCED_MAX_PER_SECTOR),
                ("max_turnover_cap", f"{BALANCED_MAX_TURNOVER_CAP:.2f}"),
                ("benchmark", BALANCED_BENCHMARK),
                ("regime_variant", variant.name),
                ("require_above_sma", _bool_text(variant.require_above_sma)),
                ("regime_below_action", variant.regime_below_action),
                ("include_cash", _bool_text(variant.include_cash)),
                ("cash_yield_annual", f"{BALANCED_CASH_YIELD_ANNUAL:.2f}"),
                ("regime_sma_days", BALANCED_REGIME_SMA_DAYS),
                ("profile", profile.upper()),
                ("run_id", snapshot.run_id),
            ),
        ),
        "",
        "## Performance",
        _md_table(
            ("Metric", "Value"),
            (
                ("total_return_pct", _fmt_pct(perf.total_return_pct)),
                ("cagr_pct", _fmt_pct(perf.cagr_pct)),
                ("alpha_pct", _fmt_pct(perf.alpha_pct)),
                ("max_drawdown_pct", _fmt_pct(perf.max_drawdown_pct)),
                ("volatility_pct", _fmt_pct(perf.volatility_pct)),
                ("sharpe_ratio", _fmt_num(perf.sharpe_ratio)),
                ("turnover_pct", _fmt_pct(perf.turnover_pct)),
                ("trades_count", behavior.trades_count),
            ),
        ),
        "",
        f"## Benchmark ({bench.benchmark_name or 'n/a'})",
        _md_table(
            ("Metric", "Value"),
            (
                ("benchmark_cagr_pct", _fmt_pct(bench.benchmark_cagr_pct)),
                ("benchmark_max_drawdown_pct", _fmt_pct(bench.benchmark_max_drawdown_pct)),
                ("benchmark_sharpe_ratio", _fmt_num(bench.benchmark_sharpe_ratio)),
                ("up_capture_ratio", _fmt_num(bench.up_capture_ratio)),
                ("down_capture_ratio", _fmt_num(bench.down_capture_ratio)),
            ),
        ),
        "",
        "## Cash / Regime Metrics",
        _md_table(
            ("Metric", "Value"),
            (
                ("average_cash_pct", _fmt_pct(cash_metrics.average_cash_pct)),
                ("max_cash_pct", _fmt_pct(cash_metrics.max_cash_pct)),
                ("time_in_market_pct", _fmt_pct(cash_metrics.time_in_market_pct)),
                ("time_in_cash_pct", _fmt_pct(cash_metrics.time_in_cash_pct)),
                ("regime_off_count", _display(cash_metrics.regime_off_count)),
                ("regime_switch_count", _display(cash_metrics.regime_switch_count)),
                ("warning", cash_metrics.warning or "n/a"),
            ),
        ),
        "",
        "## Sector Metrics",
        _md_table(
            ("Metric", "Value"),
            (
                ("max_sector_weight", _fmt_pct(sector_metrics.max_sector_weight_pct)),
                ("dominant_sector", sector_metrics.dominant_sector or "n/a"),
                ("sector_count", sector_metrics.sector_count),
                ("sector_distribution", _format_sector_distribution(sector_metrics)),
            ),
        ),
        "",
    ]
    return "\n".join(lines)


def build_summary(results: list[RegimeRunResult], skipped: list[RegimeVariant] | None = None) -> str:
    skipped = skipped or []
    lines = [
        "# Regime/Cash Sensitivity Matrix",
        "",
        "Universe: sp500",
        f"top_k: {BALANCED_TOP_K}",
        "use_sector_limits: true",
        f"max_per_sector: {BALANCED_MAX_PER_SECTOR}",
        f"max_turnover_cap: {BALANCED_MAX_TURNOVER_CAP:.2f}",
        f"Benchmark: {BALANCED_BENCHMARK}",
        "",
        "## Runs",
        _md_table(
            (
                "regime_variant",
                "require_above_sma",
                "regime_below_action",
                "include_cash",
                "Profile",
                "Run ID",
                "Total Return",
                "CAGR",
                "Alpha",
                "Max Drawdown",
                "Volatility",
                "Sharpe",
                "Turnover",
                "Trades Count",
                "Benchmark CAGR",
                "Benchmark Drawdown",
                "Benchmark Sharpe",
                "Up Capture",
                "Down Capture",
                "Max Sector Weight",
                "Dominant Sector",
                "Sector Count",
                "Average Cash",
                "Max Cash",
                "Time in Market",
                "Time in Cash",
                "Regime Off Count",
                "Regime Switch Count",
            ),
            tuple(_summary_row(result) for result in results),
        ),
        "",
        "## Profile Winners",
        _md_table(
            (
                "Profile",
                "Best Return",
                "Best Drawdown",
                "Best Sharpe",
                "Lowest Down Capture",
                "First Assessment",
            ),
            tuple(_winner_row(profile, results) for profile in ("SHORT", "MEDIUM", "LONG")),
        ),
        "",
        "## Skipped Variants",
        _md_table(
            ("Variant", "Reason"),
            tuple((variant.name, variant.skip_reason or "n/a") for variant in skipped),
        ),
        "",
        "## Reports",
        _md_table(
            ("Test", "Variant", "Profile", "Run ID", "Report"),
            tuple(
                (
                    result.test_id,
                    result.regime_variant,
                    result.profile,
                    result.run_id,
                    result.report_path.as_posix(),
                )
                for result in results
            ),
        ),
        "",
        "## TODO",
        "- Regime counts are parsed from stdout and may be n/a if logs are missing.",
        "",
        "Raw matrix JSON:",
        "```json",
        json.dumps(_json_results(results), indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def _summary_row(result: RegimeRunResult) -> tuple[object, ...]:
    sector_metrics = result.sector_metrics
    cash_metrics = result.cash_metrics
    return (
        result.regime_variant,
        _bool_text(result.require_above_sma),
        result.regime_below_action,
        _bool_text(result.include_cash),
        result.profile,
        result.run_id,
        _fmt_pct(result.total_return_pct),
        _fmt_pct(result.cagr_pct),
        _fmt_pct(result.alpha_pct),
        _fmt_pct(result.max_drawdown_pct),
        _fmt_pct(result.volatility_pct),
        _fmt_num(result.sharpe_ratio),
        _fmt_pct(result.turnover_pct),
        result.trades_count if result.trades_count is not None else "n/a",
        _fmt_pct(result.benchmark_cagr_pct),
        _fmt_pct(result.benchmark_max_drawdown_pct),
        _fmt_num(result.benchmark_sharpe_ratio),
        _fmt_num(result.up_capture_ratio),
        _fmt_num(result.down_capture_ratio),
        _fmt_pct(sector_metrics.max_sector_weight_pct),
        sector_metrics.dominant_sector or "n/a",
        sector_metrics.sector_count if sector_metrics.sector_count is not None else "n/a",
        _fmt_pct(cash_metrics.average_cash_pct),
        _fmt_pct(cash_metrics.max_cash_pct),
        _fmt_pct(cash_metrics.time_in_market_pct),
        _fmt_pct(cash_metrics.time_in_cash_pct),
        _display(cash_metrics.regime_off_count),
        _display(cash_metrics.regime_switch_count),
    )


def _winner_row(profile: str, results: list[RegimeRunResult]) -> tuple[object, ...]:
    profile_results = [result for result in results if result.profile == profile]
    best_return = _best_variant(profile_results, "total_return_pct", higher=True)
    best_drawdown = _best_variant(profile_results, "max_drawdown_pct", drawdown=True)
    best_sharpe = _best_variant(profile_results, "sharpe_ratio", higher=True)
    lowest_down_capture = _best_variant(profile_results, "down_capture_ratio", higher=False)
    assessment = _assessment(best_return, best_drawdown, best_sharpe, lowest_down_capture)
    return (profile, best_return, best_drawdown, best_sharpe, lowest_down_capture, assessment)


def _best_variant(
    results: list[RegimeRunResult],
    field_name: str,
    *,
    higher: bool = True,
    drawdown: bool = False,
) -> str:
    candidates = []
    for result in results:
        value = getattr(result, field_name)
        if value is None:
            continue
        score = abs(value) if drawdown else value
        candidates.append((score, result.regime_variant))
    if not candidates:
        return "n/a"
    _, label = min(candidates) if (drawdown or not higher) else max(candidates)
    return label


def _assessment(best_return: str, best_drawdown: str, best_sharpe: str, lowest_down_capture: str) -> str:
    if best_drawdown == best_sharpe == lowest_down_capture and best_drawdown != "n/a":
        return f"{best_drawdown} leads on risk/efficiency."
    if best_return != "n/a" and best_return != best_drawdown:
        return f"Return favors {best_return}; risk favors {best_drawdown}."
    return "Mixed; inspect report details."


def _json_results(results: list[RegimeRunResult]) -> list[dict[str, Any]]:
    payload = []
    for result in results:
        item = asdict(result)
        item["report_path"] = result.report_path.as_posix()
        payload.append(item)
    return payload


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _display(value: object) -> str:
    return "n/a" if value is None else str(value)


if __name__ == "__main__":
    main()

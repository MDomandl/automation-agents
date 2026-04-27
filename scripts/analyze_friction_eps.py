from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO


DEFAULT_AUTOMATION_RUNS_DIR = Path(
    r"D:\Users\doman\Documents\OneDrive\Dokumente\Programmierung\Projekte\AiAgents\automation_runs"
)


@dataclass(frozen=True, slots=True)
class RunPaths:
    manifest_path: Path
    run_dir: Path
    decisions_dir: Path
    aktien_oop_dir: Path
    compare_point_count: int


@dataclass(frozen=True, slots=True)
class SideArtifacts:
    label: str
    old_weights: dict[str, float]
    final_weights: dict[str, float]
    friction_eps: float | None
    target_weights: dict[str, float] | None = None
    raw_weights: dict[str, float] | None = None
    after_round_weights: dict[str, float] | None = None
    after_friction_weights: dict[str, float] | None = None
    friction_actions: dict[str, str] | None = None
    exact_target_available: bool = False


@dataclass(frozen=True, slots=True)
class AnalysisRow:
    as_of: str
    ticker: str
    prev_weight: float | None
    target_weight_bt: float | None
    target_weight_run: float | None
    abs_delta_bt: float | None
    abs_delta_run: float | None
    friction_eps_bt: float | None
    friction_eps_run: float | None
    bt_action: str
    run_action: str
    final_weight_bt: float | None
    final_weight_run: float | None
    note: str

    def to_csv_row(self) -> dict[str, str]:
        return {
            "as_of": self.as_of,
            "ticker": self.ticker,
            "prev_weight": _fmt_csv(self.prev_weight),
            "target_weight_bt": _fmt_csv(self.target_weight_bt),
            "target_weight_run": _fmt_csv(self.target_weight_run),
            "abs_delta_bt": _fmt_csv(self.abs_delta_bt),
            "abs_delta_run": _fmt_csv(self.abs_delta_run),
            "friction_eps_bt": _fmt_csv(self.friction_eps_bt),
            "friction_eps_run": _fmt_csv(self.friction_eps_run),
            "bt_action": self.bt_action,
            "run_action": self.run_action,
            "final_weight_bt": _fmt_csv(self.final_weight_bt),
            "final_weight_run": _fmt_csv(self.final_weight_run),
            "note": self.note,
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze friction_eps effects for recent BT/RUN compare points."
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Automation run directory containing run_manifest.json. Defaults to latest run.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Explicit path to run_manifest.json.",
    )
    parser.add_argument(
        "--as-of",
        dest="as_ofs",
        nargs="+",
        help="Explicit as_of points to analyze. Defaults to recent compare points from the run.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        type=Path,
        help="Optional CSV output path. Defaults to <run_dir>/friction_eps_analysis.csv when omitted.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, stdout: TextIO | None = None) -> int:
    args = parse_args(argv)
    stream = stdout or sys.stdout

    run_paths = resolve_run_paths(
        manifest_path=args.manifest,
        run_dir=args.run_dir,
    )
    selected_as_ofs = resolve_selected_as_ofs(run_paths, args.as_ofs)
    rows = build_analysis(run_paths, selected_as_ofs)
    csv_path = write_analysis_csv(rows, args.csv_path or (run_paths.run_dir / "friction_eps_analysis.csv"))

    render_console_summary(rows, run_paths, selected_as_ofs, csv_path, stream)
    return 0


def resolve_run_paths(
    *,
    manifest_path: Path | None = None,
    run_dir: Path | None = None,
) -> RunPaths:
    if manifest_path is None:
        if run_dir is not None:
            manifest_path = run_dir / "run_manifest.json"
        else:
            manifest_path = find_latest_manifest(DEFAULT_AUTOMATION_RUNS_DIR)

    payload = load_json(manifest_path)
    resolved_run_dir = manifest_path.parent
    decisions_dir = Path(str(payload["decisions_dir"]))
    backtest_config_path = Path(str(payload["backtest_config_path"]))
    compare_point_count = int(payload.get("compare_point_count", 1) or 1)

    return RunPaths(
        manifest_path=manifest_path,
        run_dir=resolved_run_dir,
        decisions_dir=decisions_dir,
        aktien_oop_dir=backtest_config_path.parent,
        compare_point_count=compare_point_count,
    )


def find_latest_manifest(automation_runs_dir: Path) -> Path:
    manifests = sorted(
        automation_runs_dir.glob("*/run_manifest.json"),
        key=lambda path: path.stat().st_mtime,
    )
    if not manifests:
        raise FileNotFoundError(f"No run_manifest.json found under {automation_runs_dir}")
    return manifests[-1]


def resolve_selected_as_ofs(run_paths: RunPaths, explicit_as_ofs: list[str] | None) -> list[str]:
    if explicit_as_ofs:
        return [str(value).strip() for value in explicit_as_ofs if str(value).strip()]

    common_as_ofs = sorted(
        set(list_available_as_ofs(run_paths.decisions_dir, "BT"))
        & set(list_available_as_ofs(run_paths.decisions_dir, "RUN"))
    )
    if not common_as_ofs:
        raise FileNotFoundError(f"No BT/RUN pairs found in {run_paths.decisions_dir}")
    return common_as_ofs[-run_paths.compare_point_count :]


def list_available_as_ofs(decisions_dir: Path, prefix: str) -> list[str]:
    as_ofs: set[str] = set()
    for path in decisions_dir.glob(f"{prefix}_*.json"):
        payload = load_json(path)
        raw_as_of = payload.get("as_of")
        if isinstance(raw_as_of, str) and raw_as_of.strip():
            as_ofs.add(raw_as_of.strip())
    return sorted(as_ofs)


def build_analysis(run_paths: RunPaths, as_ofs: list[str]) -> list[AnalysisRow]:
    rows: list[AnalysisRow] = []
    for as_of in as_ofs:
        bt = load_bt_side(run_paths, as_of)
        run = load_run_side(run_paths, as_of)
        bt_actions = replay_friction_actions(
            target_weights=bt.target_weights,
            prev_weights=bt.old_weights,
            friction_eps=bt.friction_eps,
        )

        tickers = sorted(
            set(bt.old_weights)
            | set(run.old_weights)
            | set(bt.final_weights)
            | set(run.final_weights)
            | set(bt.target_weights or {})
            | set(run.target_weights or {})
        )
        for ticker in tickers:
            prev_bt = weight_value(bt.old_weights, ticker)
            prev_run = weight_value(run.old_weights, ticker)
            unified_prev = choose_prev_weight(prev_bt, prev_run)

            target_bt = weight_value(bt.target_weights, ticker, unavailable_if_none=True)
            target_run = weight_value(run.target_weights, ticker, unavailable_if_none=True)
            final_bt = weight_value(bt.final_weights, ticker)
            final_run = weight_value(run.final_weights, ticker)

            note_parts: list[str] = []
            if prev_bt is not None and prev_run is not None and not approx_equal(prev_bt, prev_run):
                note_parts.append("prev mismatch BT/RUN")

            bt_action = classify_exact_bt_action(
                ticker=ticker,
                bt=bt,
                action_map=bt_actions,
                note_parts=note_parts,
            )
            run_action = classify_runner_action(
                ticker=ticker,
                run=run,
                note_parts=note_parts,
            )

            add_finalization_notes(
                ticker=ticker,
                bt=bt,
                run=run,
                final_bt=final_bt,
                final_run=final_run,
                note_parts=note_parts,
            )

            rows.append(
                AnalysisRow(
                    as_of=as_of,
                    ticker=ticker,
                    prev_weight=unified_prev,
                    target_weight_bt=target_bt,
                    target_weight_run=target_run,
                    abs_delta_bt=calc_abs_delta(unified_prev, target_bt),
                    abs_delta_run=calc_abs_delta(unified_prev, target_run),
                    friction_eps_bt=bt.friction_eps,
                    friction_eps_run=run.friction_eps,
                    bt_action=bt_action,
                    run_action=run_action,
                    final_weight_bt=final_bt,
                    final_weight_run=final_run,
                    note="; ".join(note_parts),
                )
            )
    return rows


def load_bt_side(run_paths: RunPaths, as_of: str) -> SideArtifacts:
    bundle = load_json(find_latest_bundle(run_paths.decisions_dir, "BT", as_of))
    bt_dump_path = run_paths.aktien_oop_dir / "dumps" / f"weights_BT_{as_of}.csv"
    bt_dump = load_weight_dump(bt_dump_path) if bt_dump_path.exists() else None
    params = bundle.get("params", {})
    friction_eps = safe_float(params.get("friction_eps"))

    target_weights = bt_dump["weight_after_round"] if bt_dump is not None else None
    raw_weights = bt_dump["weight_raw"] if bt_dump is not None else None
    final_weights = (
        bt_dump["weight_final"]
        if bt_dump is not None
        else normalize_weight_map(bundle.get("new_weights") or bundle.get("weights"))
    )

    return SideArtifacts(
        label="BT",
        old_weights=normalize_weight_map(bundle.get("old_weights")),
        final_weights=final_weights,
        friction_eps=friction_eps,
        target_weights=target_weights,
        raw_weights=raw_weights,
        after_round_weights=target_weights,
        exact_target_available=bt_dump is not None,
    )


def load_run_side(run_paths: RunPaths, as_of: str) -> SideArtifacts:
    bundle = load_json(find_latest_bundle(run_paths.decisions_dir, "RUN", as_of))
    debug_dir = run_paths.aktien_oop_dir / "debug"
    friction_dump_path = debug_dir / f"RUN_friction_{as_of}.csv"
    calcparams_path = debug_dir / f"RUN_CalcParams_{as_of}.json"
    friction_eps = None
    if calcparams_path.exists():
        calcparams = load_json(calcparams_path)
        friction_eps = safe_float(calcparams.get("friction_eps"))
    else:
        runner_config_path = run_paths.aktien_oop_dir / "configs" / "runner_config.toml"
        if runner_config_path.exists():
            friction_eps = load_runner_friction_eps(runner_config_path)

    runner_dump_path = debug_dir / f"RUN_weights_{as_of}.csv"
    runner_dump = load_simple_weight_dump(runner_dump_path) if runner_dump_path.exists() else None
    friction_dump = load_runner_friction_dump(friction_dump_path) if friction_dump_path.exists() else None
    final_weights = (
        friction_dump["final_weight"]
        if friction_dump is not None
        else runner_dump or normalize_weight_map(bundle.get("new_weights"))
    )

    return SideArtifacts(
        label="RUN",
        old_weights=(
            friction_dump["prev_weight"]
            if friction_dump is not None
            else normalize_weight_map(bundle.get("old_weights"))
        ),
        final_weights=final_weights,
        friction_eps=friction_eps,
        target_weights=(
            friction_dump["target_weight_before_friction"]
            if friction_dump is not None
            else None
        ),
        raw_weights=None,
        after_round_weights=None,
        after_friction_weights=(
            friction_dump["weight_after_friction"]
            if friction_dump is not None
            else None
        ),
        friction_actions=(
            friction_dump["friction_action"]
            if friction_dump is not None
            else None
        ),
        exact_target_available=friction_dump is not None,
    )


def load_runner_friction_eps(runner_config_path: Path) -> float | None:
    with runner_config_path.open("rb") as file_obj:
        payload = tomllib.load(file_obj)

    limits_cfg = payload.get("limits")
    if isinstance(limits_cfg, dict) and "friction_eps" in limits_cfg:
        return safe_float(limits_cfg.get("friction_eps"))
    return safe_float(payload.get("friction_eps"))


def find_latest_bundle(decisions_dir: Path, prefix: str, as_of: str) -> Path:
    matches = sorted(decisions_dir.glob(f"{prefix}_*_{as_of}.json"))
    if not matches:
        raise FileNotFoundError(f"No {prefix} bundle found for as_of={as_of} in {decisions_dir}")
    return matches[-1]


def load_weight_dump(path: Path) -> dict[str, dict[str, float]]:
    raw: dict[str, float] = {}
    after_round: dict[str, float] = {}
    final: dict[str, float] = {}
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            ticker = str(row["ticker"]).strip()
            raw[ticker] = float(row["weight_raw"])
            after_round[ticker] = float(row["weight_after_round"])
            final[ticker] = float(row["weight_final"])
    return {
        "weight_raw": raw,
        "weight_after_round": after_round,
        "weight_final": final,
    }


def load_simple_weight_dump(path: Path) -> dict[str, float]:
    weights: dict[str, float] = {}
    with path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            ticker = str(row["ticker"]).strip()
            weights[ticker] = float(row["weight"])
    return weights


def load_runner_friction_dump(path: Path) -> dict[str, dict[str, float] | dict[str, str]]:
    prev_weight: dict[str, float] = {}
    target_weight_before_friction: dict[str, float] = {}
    weight_after_friction: dict[str, float] = {}
    final_weight: dict[str, float] = {}
    friction_action: dict[str, str] = {}

    with path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            ticker = str(row["ticker"]).strip()
            prev_weight[ticker] = float(row["prev_weight"])
            target_weight_before_friction[ticker] = float(row["target_weight_before_friction"])
            weight_after_friction[ticker] = float(row["weight_after_friction"])
            final_weight[ticker] = float(row["final_weight"])
            friction_action[ticker] = str(row["friction_action"]).strip()

    return {
        "prev_weight": prev_weight,
        "target_weight_before_friction": target_weight_before_friction,
        "weight_after_friction": weight_after_friction,
        "final_weight": final_weight,
        "friction_action": friction_action,
    }


def replay_friction_actions(
    *,
    target_weights: dict[str, float] | None,
    prev_weights: dict[str, float],
    friction_eps: float | None,
) -> dict[str, str]:
    if target_weights is None:
        return {}

    eps = float(friction_eps or 0.0)
    actions: dict[str, str] = {}

    if eps <= 0.0 or not prev_weights:
        for ticker in sorted(set(target_weights) | set(prev_weights)):
            old_weight = float(prev_weights.get(ticker, 0.0))
            target_weight = float(target_weights.get(ticker, 0.0))
            actions[ticker] = classify_applied_action(old_weight, target_weight)
        return actions

    for ticker in sorted(set(target_weights) | set(prev_weights)):
        old_weight = float(prev_weights.get(ticker, 0.0))
        target_weight = float(target_weights.get(ticker, 0.0))
        if abs(target_weight - old_weight) < eps:
            actions[ticker] = "suppressed_exact"
        else:
            actions[ticker] = classify_applied_action(old_weight, target_weight)
    return actions


def classify_applied_action(old_weight: float, target_weight: float) -> str:
    if old_weight <= 0.0 and target_weight > 0.0:
        return "enter_applied_exact"
    if old_weight > 0.0 and target_weight <= 0.0:
        return "exit_applied_exact"
    if approx_equal(old_weight, target_weight):
        return "unchanged_exact"
    return "reweighted_exact"


def classify_exact_bt_action(
    *,
    ticker: str,
    bt: SideArtifacts,
    action_map: dict[str, str],
    note_parts: list[str],
) -> str:
    if not bt.exact_target_available:
        note_parts.append("BT target unavailable")
        return "unknown_bt_target"

    target = weight_value(bt.target_weights, ticker, unavailable_if_none=True)
    final = weight_value(bt.final_weights, ticker)
    if target is None and final == 0.0 and ticker not in bt.old_weights:
        return "absent"

    action = action_map.get(ticker, "unknown_exact")
    if action == "suppressed_exact":
        note_parts.append("BT action exact from dump replay")
    if target is not None and final is not None and not approx_equal(target, final):
        note_parts.append("BT target->final changed after later finalization")
    return action


def classify_runner_action(
    *,
    ticker: str,
    run: SideArtifacts,
    note_parts: list[str],
) -> str:
    final = weight_value(run.final_weights, ticker)
    old_weight = weight_value(run.old_weights, ticker)
    if run.friction_actions is not None:
        action = run.friction_actions.get(ticker, "unknown_exact")
        if run.after_friction_weights is not None:
            after_friction = weight_value(run.after_friction_weights, ticker)
            if after_friction is not None and final is not None and not approx_equal(after_friction, final):
                note_parts.append("RUN later finalization changed post-friction weight")
        return action
    if run.target_weights is not None:
        target = weight_value(run.target_weights, ticker)
        return classify_applied_action(float(old_weight or 0.0), float(target or 0.0))

    if old_weight == 0.0 and final == 0.0:
        return "absent"
    note_parts.append("RUN target unavailable (final-only debug)")
    if old_weight is not None and final is not None and approx_equal(old_weight, final):
        return "unchanged_inferred"
    if (old_weight or 0.0) <= 0.0 and (final or 0.0) > 0.0:
        return "enter_inferred"
    if (old_weight or 0.0) > 0.0 and (final or 0.0) <= 0.0:
        return "exit_inferred"
    return "reweighted_inferred"


def add_finalization_notes(
    *,
    ticker: str,
    bt: SideArtifacts,
    run: SideArtifacts,
    final_bt: float | None,
    final_run: float | None,
    note_parts: list[str],
) -> None:
    if bt.raw_weights is not None:
        raw_bt = weight_value(bt.raw_weights, ticker, unavailable_if_none=True)
        after_round_bt = weight_value(bt.after_round_weights, ticker, unavailable_if_none=True)
        if raw_bt is not None and after_round_bt is not None and not approx_equal(raw_bt, after_round_bt):
            note_parts.append("BT rounding changed target")
        if after_round_bt is not None and final_bt is not None and not approx_equal(after_round_bt, final_bt):
            note_parts.append("BT renorm/finalization changed target")

    if final_bt is not None and final_run is not None and approx_equal(final_bt, final_run):
        note_parts.append("final BT/RUN equal")


def choose_prev_weight(prev_bt: float | None, prev_run: float | None) -> float | None:
    if prev_bt is not None and prev_run is not None:
        if approx_equal(prev_bt, prev_run):
            return prev_bt
        return prev_bt
    return prev_bt if prev_bt is not None else prev_run


def calc_abs_delta(prev_weight: float | None, target_weight: float | None) -> float | None:
    if prev_weight is None or target_weight is None:
        return None
    return abs(target_weight - prev_weight)


def normalize_weight_map(payload: Any) -> dict[str, float]:
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): float(value)
        for key, value in payload.items()
        if value is not None
    }


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def weight_value(
    values: dict[str, float] | None,
    ticker: str,
    *,
    unavailable_if_none: bool = False,
) -> float | None:
    if values is None:
        return None if unavailable_if_none else 0.0
    return float(values.get(ticker, 0.0))


def approx_equal(left: float, right: float, *, tolerance: float = 1e-12) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=tolerance)


def write_analysis_csv(rows: list[AnalysisRow], csv_path: Path) -> Path:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(
            file_obj,
            fieldnames=[
                "as_of",
                "ticker",
                "prev_weight",
                "target_weight_bt",
                "target_weight_run",
                "abs_delta_bt",
                "abs_delta_run",
                "friction_eps_bt",
                "friction_eps_run",
                "bt_action",
                "run_action",
                "final_weight_bt",
                "final_weight_run",
                "note",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row.to_csv_row())
    return csv_path


def render_console_summary(
    rows: list[AnalysisRow],
    run_paths: RunPaths,
    as_ofs: list[str],
    csv_path: Path,
    stream: TextIO,
) -> None:
    print("=== friction_eps analyzer ===", file=stream)
    print(f"run_manifest: {run_paths.manifest_path}", file=stream)
    print(f"decisions_dir: {run_paths.decisions_dir}", file=stream)
    print(f"as_of_points: {', '.join(as_ofs)}", file=stream)
    print(f"rows: {len(rows)}", file=stream)
    print(f"csv: {csv_path}", file=stream)
    print("", file=stream)

    for as_of in as_ofs:
        as_of_rows = [row for row in rows if row.as_of == as_of]
        suppressed_bt = sum(1 for row in as_of_rows if row.bt_action == "suppressed_exact")
        exact_bt = sum(1 for row in as_of_rows if row.bt_action.endswith("_exact"))
        final_equal = sum(
            1
            for row in as_of_rows
            if row.final_weight_bt is not None
            and row.final_weight_run is not None
            and approx_equal(row.final_weight_bt, row.final_weight_run)
        )
        print(
            f"{as_of}: tickers={len(as_of_rows)} bt_exact={exact_bt} bt_suppressed={suppressed_bt} final_equal={final_equal}",
            file=stream,
        )

    print("", file=stream)
    print(
        "as_of       ticker  prev_weight  target_weight_bt  target_weight_run  abs_delta_bt  abs_delta_run  "
        "friction_eps_bt  friction_eps_run  bt_action             run_action            final_weight_bt  "
        "final_weight_run  note",
        file=stream,
    )
    for row in rows:
        print(format_row_for_console(row), file=stream)


def format_row_for_console(row: AnalysisRow) -> str:
    return (
        f"{row.as_of:<10}  "
        f"{row.ticker:<6}  "
        f"{_fmt_console(row.prev_weight):>11}  "
        f"{_fmt_console(row.target_weight_bt):>16}  "
        f"{_fmt_console(row.target_weight_run):>17}  "
        f"{_fmt_console(row.abs_delta_bt):>12}  "
        f"{_fmt_console(row.abs_delta_run):>13}  "
        f"{_fmt_console(row.friction_eps_bt):>15}  "
        f"{_fmt_console(row.friction_eps_run):>16}  "
        f"{row.bt_action:<20}  "
        f"{row.run_action:<20}  "
        f"{_fmt_console(row.final_weight_bt):>15}  "
        f"{_fmt_console(row.final_weight_run):>16}  "
        f"{row.note}"
    )


def _fmt_console(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:.6f}"


def _fmt_csv(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.16f}"


if __name__ == "__main__":
    raise SystemExit(main())

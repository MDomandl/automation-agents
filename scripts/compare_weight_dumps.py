from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path


DEFAULT_COMPARE_COLUMNS = (
    "weight_raw",
    "weight_after_round",
    "weight_final",
)


@dataclass(frozen=True, slots=True)
class WeightDiffSummary:
    only_in_bt_count: int
    only_in_run_count: int
    differing_row_count: int
    compared_columns: tuple[str, ...]
    max_abs_delta_by_column: dict[str, float]


@dataclass(frozen=True, slots=True)
class WeightDiffResult:
    rows: tuple[dict[str, object], ...]
    summary: WeightDiffSummary


def _read_csv_rows(path: str | Path) -> tuple[list[dict[str, str]], tuple[str, ...]]:
    csv_path = Path(path)
    with csv_path.open("r", encoding="utf-8", newline="") as file_obj:
        reader = csv.DictReader(file_obj)
        rows = [dict(row) for row in reader]
        fieldnames = tuple(reader.fieldnames or ())
    return rows, fieldnames


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_row(row: dict[str, str], fieldnames: tuple[str, ...]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for fieldname in fieldnames:
        value = row.get(fieldname, "")
        numeric = _to_float(value)
        normalized[fieldname] = numeric if numeric is not None else value
    return normalized


def _load_rows_by_ticker(path: str | Path) -> tuple[dict[str, dict[str, object]], tuple[str, ...]]:
    rows, fieldnames = _read_csv_rows(path)
    if "ticker" not in fieldnames:
        raise ValueError(f"CSV is missing required 'ticker' column: {path}")

    by_ticker: dict[str, dict[str, object]] = {}
    for row in rows:
        ticker = str(row.get("ticker", "")).strip()
        if not ticker:
            continue
        by_ticker[ticker] = _normalize_row(row, fieldnames)

    return by_ticker, fieldnames


def _resolve_compare_columns(
    bt_fieldnames: tuple[str, ...],
    run_fieldnames: tuple[str, ...],
) -> tuple[str, ...]:
    shared = set(bt_fieldnames) & set(run_fieldnames)
    return tuple(column for column in DEFAULT_COMPARE_COLUMNS if column in shared)


def compare_weight_dumps(
    bt_path: str | Path,
    run_path: str | Path,
    *,
    tolerance: float = 1e-9,
) -> WeightDiffResult:
    bt_rows, bt_fieldnames = _load_rows_by_ticker(bt_path)
    run_rows, run_fieldnames = _load_rows_by_ticker(run_path)
    compare_columns = _resolve_compare_columns(bt_fieldnames, run_fieldnames)

    all_tickers = sorted(set(bt_rows) | set(run_rows))
    diff_rows: list[dict[str, object]] = []
    only_in_bt_count = 0
    only_in_run_count = 0
    differing_row_count = 0
    max_abs_delta_by_column = {column: 0.0 for column in compare_columns}

    for ticker in all_tickers:
        bt_row = bt_rows.get(ticker)
        run_row = run_rows.get(ticker)

        row: dict[str, object] = {
            "ticker": ticker,
            "status": "match",
            "only_in_bt": bt_row is not None and run_row is None,
            "only_in_run": run_row is not None and bt_row is None,
        }

        if bt_row is None:
            row["status"] = "only_in_run"
            only_in_run_count += 1
        elif run_row is None:
            row["status"] = "only_in_bt"
            only_in_bt_count += 1

        row_has_diff = row["status"] != "match"

        for column in compare_columns:
            bt_value = bt_row.get(column) if bt_row is not None else None
            run_value = run_row.get(column) if run_row is not None else None
            row[f"bt_{column}"] = bt_value
            row[f"run_{column}"] = run_value

            bt_float = _to_float(bt_value)
            run_float = _to_float(run_value)
            delta = None

            if bt_float is not None and run_float is not None:
                delta = bt_float - run_float
                max_abs_delta_by_column[column] = max(max_abs_delta_by_column[column], abs(delta))
                if abs(delta) > tolerance:
                    row_has_diff = True
            elif bt_value != run_value:
                row_has_diff = True

            row[f"delta_{column}"] = delta

        if row_has_diff and row["status"] == "match":
            row["status"] = "diff"
            differing_row_count += 1

        diff_rows.append(row)

    summary = WeightDiffSummary(
        only_in_bt_count=only_in_bt_count,
        only_in_run_count=only_in_run_count,
        differing_row_count=differing_row_count,
        compared_columns=compare_columns,
        max_abs_delta_by_column=max_abs_delta_by_column,
    )
    return WeightDiffResult(rows=tuple(diff_rows), summary=summary)


def write_diff_csv(path: str | Path, rows: tuple[dict[str, object], ...]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if rows:
        fieldnames = list(rows[0].keys())
    else:
        fieldnames = ["ticker", "status", "only_in_bt", "only_in_run"]

    with output_path.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_console_summary(result: WeightDiffResult) -> str:
    lines = [
        f"only-in-BT: {result.summary.only_in_bt_count}",
        f"only-in-RUN: {result.summary.only_in_run_count}",
        f"differing rows: {result.summary.differing_row_count}",
    ]
    for column in result.summary.compared_columns:
        lines.append(
            f"max |delta_{column}|: {result.summary.max_abs_delta_by_column[column]:.12g}"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bt", required=True, help="Path to weights_BT_<as_of>.csv")
    parser.add_argument("--run", required=True, help="Path to weights_RUN_<as_of>.csv")
    parser.add_argument("--out", required=True, help="Path to write the diff CSV")
    parser.add_argument("--tol", type=float, default=1e-9, help="Numeric diff tolerance")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = compare_weight_dumps(args.bt, args.run, tolerance=args.tol)
    write_diff_csv(args.out, result.rows)
    print(build_console_summary(result))


if __name__ == "__main__":
    main()

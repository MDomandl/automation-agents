from pathlib import Path
import math

from scripts.compare_weight_dumps import compare_weight_dumps, write_diff_csv


def write_csv(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def test_compare_weight_dumps_joins_by_ticker_and_computes_deltas(tmp_path: Path) -> None:
    bt_path = tmp_path / "weights_BT_2025-04-30.csv"
    run_path = tmp_path / "weights_RUN_2025-04-30.csv"

    write_csv(
        bt_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.4,0.4,0.4
MSFT,0.6,0.6,0.6
""",
    )
    write_csv(
        run_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.4,0.39,0.38
MSFT,0.6,0.61,0.62
""",
    )

    result = compare_weight_dumps(bt_path, run_path)

    assert result.summary.only_in_bt_count == 0
    assert result.summary.only_in_run_count == 0
    assert result.summary.differing_row_count == 2
    assert result.summary.max_abs_delta_by_column["weight_final"] == 0.020000000000000018

    first_row = result.rows[0]
    assert first_row["ticker"] == "AAPL"
    assert first_row["delta_weight_raw"] == 0.0
    assert first_row["delta_weight_after_round"] == 0.010000000000000009
    assert first_row["delta_weight_final"] == 0.020000000000000018


def test_compare_weight_dumps_detects_only_in_bt_and_only_in_run(tmp_path: Path) -> None:
    bt_path = tmp_path / "weights_BT_2025-04-30.csv"
    run_path = tmp_path / "weights_RUN_2025-04-30.csv"

    write_csv(
        bt_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.5,0.5,0.5
MSFT,0.5,0.5,0.5
""",
    )
    write_csv(
        run_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.5,0.5,0.5
NVDA,0.5,0.5,0.5
""",
    )

    result = compare_weight_dumps(bt_path, run_path)
    rows = {row["ticker"]: row for row in result.rows}

    assert result.summary.only_in_bt_count == 1
    assert result.summary.only_in_run_count == 1
    assert rows["MSFT"]["status"] == "only_in_bt"
    assert rows["NVDA"]["status"] == "only_in_run"


def test_compare_weight_dumps_tolerance_suppresses_small_numeric_diffs(tmp_path: Path) -> None:
    bt_path = tmp_path / "weights_BT_2025-04-30.csv"
    run_path = tmp_path / "weights_RUN_2025-04-30.csv"

    write_csv(
        bt_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.4000000001,0.4,0.4
""",
    )
    write_csv(
        run_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.4,0.4,0.4
""",
    )

    result = compare_weight_dumps(bt_path, run_path, tolerance=1e-6)

    assert result.summary.differing_row_count == 0
    assert result.rows[0]["status"] == "match"
    assert math.isclose(result.rows[0]["delta_weight_raw"], 1e-10, rel_tol=0.0, abs_tol=1e-15)


def test_write_diff_csv_writes_side_by_side_columns(tmp_path: Path) -> None:
    bt_path = tmp_path / "weights_BT_2025-04-30.csv"
    run_path = tmp_path / "weights_RUN_2025-04-30.csv"
    out_path = tmp_path / "diff.csv"

    write_csv(
        bt_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.5,0.5,0.5
""",
    )
    write_csv(
        run_path,
        """
ticker,weight_raw,weight_after_round,weight_final
AAPL,0.4,0.4,0.4
""",
    )

    result = compare_weight_dumps(bt_path, run_path)
    write_diff_csv(out_path, result.rows)
    content = out_path.read_text(encoding="utf-8")

    assert "bt_weight_raw" in content
    assert "run_weight_raw" in content
    assert "delta_weight_final" in content

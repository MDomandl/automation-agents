import json

from app.infrastructure.storage.decision_bundle_store import FileDecisionBundleStore


def test_get_all_pairs_returns_all_common_as_of_pairs(tmp_path) -> None:
    store = FileDecisionBundleStore(tmp_path)

    (tmp_path / "BT_001_2025-03-31.json").write_text(
        json.dumps({"as_of": "2025-03-31", "new_weights": {"AAPL": 1.0}}),
        encoding="utf-8",
    )
    (tmp_path / "RUN_001_2025-03-31.json").write_text(
        json.dumps({"as_of": "2025-03-31", "new_weights": {"AAPL": 1.0}}),
        encoding="utf-8",
    )
    (tmp_path / "BT_001_2025-04-30.json").write_text(
        json.dumps({"as_of": "2025-04-30", "new_weights": {"MSFT": 1.0}}),
        encoding="utf-8",
    )
    (tmp_path / "RUN_001_2025-04-30.json").write_text(
        json.dumps({"as_of": "2025-04-30", "new_weights": {"MSFT": 1.0}}),
        encoding="utf-8",
    )
    (tmp_path / "BT_only_2025-05-31.json").write_text(
        json.dumps({"as_of": "2025-05-31", "new_weights": {"NVDA": 1.0}}),
        encoding="utf-8",
    )

    pairs = store.get_all_pairs()

    assert len(pairs) == 2
    assert pairs[0][0].endswith("BT_001_2025-03-31.json")
    assert pairs[0][1].endswith("RUN_001_2025-03-31.json")
    assert pairs[1][0].endswith("BT_001_2025-04-30.json")
    assert pairs[1][1].endswith("RUN_001_2025-04-30.json")

def test_get_latest_pair_returns_latest_common_as_of(tmp_path) -> None:
    store = FileDecisionBundleStore(tmp_path)

    (tmp_path / "BT_001_2025-10-10.json").write_text(
        json.dumps({"as_of": "2025-10-10", "weights": {"AAPL": 1.0}}),
        encoding="utf-8",
    )
    (tmp_path / "RUN_001_2025-10-10.json").write_text(
        json.dumps({"as_of": "2025-10-10", "weights": {"AAPL": 1.0}}),
        encoding="utf-8",
    )
    (tmp_path / "BT_001_2025-10-11.json").write_text(
        json.dumps({"as_of": "2025-10-11", "weights": {"MSFT": 1.0}}),
        encoding="utf-8",
    )
    (tmp_path / "RUN_001_2025-10-11.json").write_text(
        json.dumps({"as_of": "2025-10-11", "weights": {"MSFT": 1.0}}),
        encoding="utf-8",
    )

    pair = store.get_latest_pair()

    assert pair is not None
    bt_path, run_path = pair
    assert bt_path.endswith("BT_001_2025-10-11.json")
    assert run_path.endswith("RUN_001_2025-10-11.json")


def test_load_artifact_reads_weights_dict(tmp_path) -> None:
    path = tmp_path / "BT_test.json"
    path.write_text(
        json.dumps(
            {
                "as_of": "2025-10-10",
                "weights": {
                    "AAPL": 0.6,
                    "MSFT": 0.4,
                },
            }
        ),
        encoding="utf-8",
    )

    store = FileDecisionBundleStore(tmp_path)
    artifact = store.load_artifact(str(path))

    assert artifact.source == "BT"
    assert artifact.as_of == "2025-10-10"
    assert artifact.weights == {"AAPL": 0.6, "MSFT": 0.4}


def test_load_artifact_reads_positions_list(tmp_path) -> None:
    path = tmp_path / "RUN_test.json"
    path.write_text(
        json.dumps(
            {
                "as_of": "2025-10-10",
                "positions": [
                    {"ticker": "AAPL", "weight": 0.7},
                    {"ticker": "CASH", "weight": 0.3},
                ],
            }
        ),
        encoding="utf-8",
    )

    store = FileDecisionBundleStore(tmp_path)
    artifact = store.load_artifact(str(path))

    assert artifact.source == "RUN"
    assert artifact.as_of == "2025-10-10"
    assert artifact.weights == {"AAPL": 0.7, "CASH": 0.3}
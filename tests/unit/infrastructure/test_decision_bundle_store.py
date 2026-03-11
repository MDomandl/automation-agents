import json

from app.infrastructure.storage.decision_bundle_store import FileDecisionBundleStore


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
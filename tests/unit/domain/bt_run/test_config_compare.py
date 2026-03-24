from app.domain.bt_run.config_compare import (
    ConfigDiffSeverity,
    compare_configs,
)


def test_compare_configs_detects_differences_with_severity() -> None:
    bt_config = {
        "period": "800d",
        "top_k": 12,
        "dump_decision_bundles": True,
    }
    run_config = {
        "period": "400d",
        "top_k": 12,
        "dump_decision_bundles": False,
    }

    result = compare_configs(
        bt_config,
        run_config,
        relevant_keys=("period", "top_k", "dump_decision_bundles"),
        key_severities={
            "period": ConfigDiffSeverity.CRITICAL,
            "top_k": ConfigDiffSeverity.CRITICAL,
            "dump_decision_bundles": ConfigDiffSeverity.INFO,
        },
    )

    assert result.matched is False
    assert len(result.differences) == 2
    assert result.critical_count == 1
    assert result.info_count == 1

    assert result.differences[0].key == "dump_decision_bundles"
    assert result.differences[0].severity == ConfigDiffSeverity.INFO

    assert result.differences[1].key == "period"
    assert result.differences[1].severity == ConfigDiffSeverity.CRITICAL

def test_compare_configs_respects_relevant_keys_whitelist() -> None:
    bt_config = {
        "period": "800d",
        "top_k": 12,
        "rebalance": "monthly",
    }
    run_config = {
        "period": "400d",
        "top_k": 12,
        "rebalance": "weekly",
    }

    result = compare_configs(
        bt_config,
        run_config,
        relevant_keys=("top_k",),
    )

    assert result.matched is True
    assert result.differences == ()
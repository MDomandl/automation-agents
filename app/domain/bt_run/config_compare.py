from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True, slots=True)
class ConfigDifference:
    key: str
    bt_value: Any
    run_value: Any


@dataclass(frozen=True, slots=True)
class ConfigCompareResult:
    matched: bool
    differences: tuple[ConfigDifference, ...]


def compare_configs(
    bt_config: Dict[str, Any],
    run_config: Dict[str, Any],
) -> ConfigCompareResult:

    differences = []

    all_keys = set(bt_config.keys()) | set(run_config.keys())

    for key in sorted(all_keys):
        bt_val = bt_config.get(key)
        run_val = run_config.get(key)

        if bt_val != run_val:
            differences.append(
                ConfigDifference(
                    key=key,
                    bt_value=bt_val,
                    run_value=run_val,
                )
            )

    return ConfigCompareResult(
        matched=len(differences) == 0,
        differences=tuple(differences),
    )
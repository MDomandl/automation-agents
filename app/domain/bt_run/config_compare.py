from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Iterable, Mapping


class ConfigDiffSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass(frozen=True, slots=True)
class ConfigDifference:
    key: str
    bt_value: Any
    run_value: Any
    severity: ConfigDiffSeverity

@dataclass(frozen=True, slots=True)
class ConfigCompareResult:
    matched: bool
    differences: tuple[ConfigDifference, ...]

    @property
    def has_critical_differences(self) -> bool:
        return any(d.severity == ConfigDiffSeverity.CRITICAL for d in self.differences)

    @property
    def has_warning_differences(self) -> bool:
        return any(d.severity == ConfigDiffSeverity.WARNING for d in self.differences)

    @property
    def critical_count(self) -> int:
        return sum(1 for d in self.differences if d.severity == ConfigDiffSeverity.CRITICAL)

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.differences if d.severity == ConfigDiffSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for d in self.differences if d.severity == ConfigDiffSeverity.INFO)

def compare_configs(
    bt_config: Dict[str, Any],
    run_config: Dict[str, Any],
    relevant_keys: Iterable[str] | None = None,
    key_severities: Mapping[str, ConfigDiffSeverity] | None = None,
) -> ConfigCompareResult:

    differences = []

    if relevant_keys is None:
        keys_to_compare = set(bt_config.keys()) | set(run_config.keys())
    else:
        keys_to_compare = set(relevant_keys)

    severity_map = dict(key_severities or {})

    for key in sorted(keys_to_compare):
        bt_val = bt_config.get(key)
        run_val = run_config.get(key)

        if bt_val != run_val:
            severity = severity_map.get(key, ConfigDiffSeverity.WARNING)

            differences.append(
                ConfigDifference(
                    key=key,
                    bt_value=bt_val,
                    run_value=run_val,
                    severity=severity,
                )
            )

    return ConfigCompareResult(
        matched=len(differences) == 0,
        differences=tuple(differences),
    )
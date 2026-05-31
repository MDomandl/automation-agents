from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from scripts.run_max_per_sector_testmatrix import replace_sector_limits
from scripts.run_max_turnover_cap_testmatrix import replace_benchmark, replace_max_turnover_cap
from scripts.run_sp500_testmatrix import UNIVERSES, _replace_universe_section
from scripts.run_top_k_testmatrix import replace_top_k


PROFILE_CONFIG_DIR = Path("configs") / "profiles"
PROFILE_CONFIG_PATHS = (
    PROFILE_CONFIG_DIR / "conservative_v1.toml",
    PROFILE_CONFIG_DIR / "balanced_v1.toml",
    PROFILE_CONFIG_DIR / "offensive_v1.toml",
)
REQUIRED_PROFILE_KEYS = frozenset(
    {
        "profile_name",
        "profile_label",
        "universe",
        "top_k",
        "use_sector_limits",
        "max_per_sector",
        "max_turnover_cap",
        "require_above_sma",
        "regime_below_action",
        "include_cash",
        "cash_yield_annual",
        "regime_sma_days",
        "benchmark_ticker",
    }
)
ALLOWED_REGIME_BELOW_ACTIONS = frozenset({"SELL", "HOLD"})


class StrategyProfileError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StrategyProfile:
    name: str
    label: str
    file_stem: str
    universe: str
    top_k: int
    use_sector_limits: bool
    max_per_sector: int
    max_turnover_cap: float
    require_above_sma: bool
    regime_below_action: str
    include_cash: bool
    cash_yield_annual: float
    regime_sma_days: int
    benchmark_ticker: str
    source_path: Path = Path()


def available_strategy_profile_names(
    profile_dir: Path = PROFILE_CONFIG_DIR,
) -> tuple[str, ...]:
    if not profile_dir.exists():
        return ()
    return tuple(sorted(path.stem for path in profile_dir.glob("*.toml")))


def resolve_strategy_profile_path(
    value: str,
    *,
    profile_dir: Path = PROFILE_CONFIG_DIR,
) -> Path:
    raw = Path(value)
    looks_like_path = raw.suffix == ".toml" or len(raw.parts) > 1
    if looks_like_path:
        return raw

    path = profile_dir / f"{value}.toml"
    if path.exists():
        return path

    known = ", ".join(available_strategy_profile_names(profile_dir)) or "none"
    raise StrategyProfileError(
        f"Unknown strategy profile {value!r}. Expected one of: {known}, "
        "or pass a .toml profile path."
    )


def load_strategy_profile(path: Path) -> StrategyProfile:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise StrategyProfileError(f"Invalid profile TOML in {path}: {exc}") from exc
    except OSError as exc:
        raise StrategyProfileError(f"Could not read profile file {path}: {exc}") from exc

    missing = sorted(REQUIRED_PROFILE_KEYS - raw.keys())
    if missing:
        raise StrategyProfileError(
            f"Invalid profile {path}: missing required keys: {', '.join(missing)}"
        )

    action = raw["regime_below_action"]
    if action not in ALLOWED_REGIME_BELOW_ACTIONS:
        allowed = ", ".join(sorted(ALLOWED_REGIME_BELOW_ACTIONS))
        raise StrategyProfileError(
            f"Invalid profile {path}: regime_below_action must be one of {allowed}; "
            f"got {action!r}"
        )

    universe = raw["universe"]
    if universe not in UNIVERSES:
        known = ", ".join(sorted(UNIVERSES))
        raise StrategyProfileError(
            f"Invalid profile {path}: universe must be one of {known}; got {universe!r}"
        )

    name = raw["profile_name"]
    return StrategyProfile(
        name=name,
        label=raw["profile_label"],
        file_stem=_profile_file_stem(name),
        source_path=path,
        universe=universe,
        top_k=raw["top_k"],
        use_sector_limits=raw["use_sector_limits"],
        max_per_sector=raw["max_per_sector"],
        max_turnover_cap=raw["max_turnover_cap"],
        require_above_sma=raw["require_above_sma"],
        regime_below_action=action,
        include_cash=raw["include_cash"],
        cash_yield_annual=raw["cash_yield_annual"],
        regime_sma_days=raw["regime_sma_days"],
        benchmark_ticker=raw["benchmark_ticker"],
    )


def load_strategy_profile_arg(value: str) -> StrategyProfile:
    return load_strategy_profile(resolve_strategy_profile_path(value))


def apply_strategy_profile_overlay(text: str, strategy_profile: StrategyProfile) -> str:
    text = _replace_universe_section(text, UNIVERSES[strategy_profile.universe])
    text = replace_top_k(text, strategy_profile.top_k)
    text = replace_sector_limits(
        text,
        use_sector_limits=strategy_profile.use_sector_limits,
        max_per_sector=strategy_profile.max_per_sector,
    )
    text = replace_max_turnover_cap(text, strategy_profile.max_turnover_cap)
    text = replace_benchmark(text, strategy_profile.benchmark_ticker)
    text = _replace_or_insert_top_level_scalar(
        text,
        "include_cash",
        _bool_text(strategy_profile.include_cash),
    )
    text = _replace_or_insert_top_level_scalar(
        text,
        "cash_yield_annual",
        f"{strategy_profile.cash_yield_annual:.2f}",
    )
    text = _replace_or_insert_section_scalar(
        text,
        "regime",
        "require_above_sma",
        _bool_text(strategy_profile.require_above_sma),
    )
    text = _replace_or_insert_section_scalar(
        text,
        "regime",
        "regime_sma_days",
        str(strategy_profile.regime_sma_days),
    )
    return _replace_or_insert_section_scalar(
        text,
        "regime",
        "regime_below_action",
        f'"{strategy_profile.regime_below_action}"',
    )


def write_strategy_profile_overlay(
    source_path: Path,
    target_path: Path,
    strategy_profile: StrategyProfile,
) -> None:
    text = source_path.read_text(encoding="utf-8")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        apply_strategy_profile_overlay(text, strategy_profile),
        encoding="utf-8",
    )


def strategy_profile_manifest_fields(strategy_profile: StrategyProfile) -> dict[str, object]:
    return {
        "strategy_profile_name": strategy_profile.name,
        "strategy_profile_label": strategy_profile.label,
        "strategy_profile_file": strategy_profile.source_path.as_posix(),
        "universe": strategy_profile.universe,
        "top_k": strategy_profile.top_k,
        "use_sector_limits": strategy_profile.use_sector_limits,
        "max_per_sector": strategy_profile.max_per_sector,
        "max_turnover_cap": strategy_profile.max_turnover_cap,
        "require_above_sma": strategy_profile.require_above_sma,
        "regime_below_action": strategy_profile.regime_below_action,
        "include_cash": strategy_profile.include_cash,
        "cash_yield_annual": strategy_profile.cash_yield_annual,
        "regime_sma_days": strategy_profile.regime_sma_days,
        "benchmark_ticker": strategy_profile.benchmark_ticker,
    }


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
        if section == "" and stripped.startswith(key):
            prefix, _, rest = line.partition("=")
            result.append(f"{prefix}= {value}{_comment(rest)}")
            replaced = True
            continue
        result.append(line)
    if not replaced and not inserted:
        result.extend(["", f"{key} = {value}"])
    return "\n".join(result) + "\n"


def _replace_or_insert_section_scalar(
    text: str,
    section_name: str,
    key: str,
    value: str,
) -> str:
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


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _profile_file_stem(profile_name: str) -> str:
    return f"profile_{_base_profile_name(profile_name)}"


def _base_profile_name(profile_name: str) -> str:
    return profile_name.removesuffix("_v1")

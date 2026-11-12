from __future__ import annotations

import importlib
import os
import sys
import tomllib
from pathlib import Path

import pytest

from scripts.strategy_profiles import load_strategy_profile, write_strategy_profile_overlay


@pytest.fixture
def cash_loaders(monkeypatch, tmp_path):
    root_value = os.environ.get("AI_AGENTS_ROOT")
    if not root_value:
        pytest.skip("requires AI_AGENTS_ROOT for the real aktien_oop loaders")
    ai_root = Path(root_value).resolve()
    monkeypatch.syspath_prepend(str(ai_root))
    monkeypatch.chdir(tmp_path)
    backtest = importlib.import_module("aktien_oop.backtest")
    config = importlib.import_module("aktien_oop.config")
    assert Path(backtest.__file__).resolve() == ai_root / "aktien_oop" / "backtest.py"
    assert Path(config.__file__).resolve() == ai_root / "aktien_oop" / "config.py"

    def load(bt_path, runner_path):
        monkeypatch.setattr(sys, "argv", ["backtest", "--config", str(bt_path)])
        bt_cfg = backtest._build_cfg_from_config_and_cli(backtest.parse_args())
        monkeypatch.setattr(
            sys,
            "argv",
            ["runner", "--config", str(runner_path), "--save-dir", str(tmp_path / "output")],
        )
        runner_cfg = config.Config.from_cli()
        return bt_cfg.include_cash, runner_cfg.include_cash

    return ai_root, load


@pytest.mark.parametrize("profile_name", ["balanced_v1", "conservative_v1", "offensive_v1"])
def test_profile_cash_contract_with_real_base_configs(profile_name, cash_loaders, tmp_path):
    ai_root, load = cash_loaders
    repo_root = Path(__file__).resolve().parents[3]
    profile = load_strategy_profile(repo_root / "configs" / "profiles" / f"{profile_name}.toml")
    sources = (
        ai_root / "aktien_oop" / "backtest_config.toml",
        ai_root / "aktien_oop" / "configs" / "runner_config.toml",
    )
    original_bytes = tuple(path.read_bytes() for path in sources)
    baseline_copies = (tmp_path / "base-bt.toml", tmp_path / "base-runner.toml")
    for source_bytes, target in zip(original_bytes, baseline_copies):
        target.write_bytes(source_bytes)

    # Without a profile, both real loaders retain the existing cash-enabled baseline.
    assert load(*baseline_copies) == (True, True)
    overlays = (tmp_path / "profile-bt.toml", tmp_path / "profile-runner.toml")
    for source, target in zip(sources, overlays):
        write_strategy_profile_overlay(source, target, profile)

    # Check effective values first: the old overlay fails here for balanced_v1.
    effective_cash = load(*overlays)
    assert effective_cash == (profile.include_cash, profile.include_cash), effective_cash
    for target in overlays:
        payload = tomllib.loads(target.read_text(encoding="utf-8"))
        assert payload["include_cash"] is profile.include_cash
        assert payload["limits"]["include_cash"] is profile.include_cash
        assert payload["regime"]["include_cash"] is profile.include_cash

    assert load(*baseline_copies) == (True, True)
    assert tuple(path.read_bytes() for path in sources) == original_bytes
    assert tuple(path.read_bytes() for path in baseline_copies) == original_bytes


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "include_cash = true\n[limits]\ninclude_cash = false\n[regime]\ninclude_cash = true\n",
            (False, True),
        ),
        (
            "include_cash = false\n[limits]\ninclude_cash = true\n[regime]\ninclude_cash = false\n",
            (True, False),
        ),
        ("include_cash = true\n", (True, True)),
        ("include_cash = false\n", (False, False)),
    ],
    ids=[
        "limits-before-root-regime-before-root",
        "opposite-section-values",
        "root-true",
        "root-false",
    ],
)
def test_cash_loader_priorities_remain_unchanged(text, expected, cash_loaders, tmp_path):
    _, load = cash_loaders
    path = tmp_path / "priority.toml"
    path.write_text(text, encoding="utf-8")
    assert load(path, path) == expected

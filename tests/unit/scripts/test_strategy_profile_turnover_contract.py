from __future__ import annotations

import importlib
import json
import os
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from scripts.run_bt_run_agent import _build_weight_change_proposals
from scripts.strategy_profiles import load_strategy_profile, write_strategy_profile_overlay


@pytest.fixture
def turnover_contract(monkeypatch, tmp_path):
    root_value = os.environ.get("AI_AGENTS_ROOT")
    if not root_value:
        pytest.skip("requires AI_AGENTS_ROOT for the real aktien_oop loaders")
    ai_root = Path(root_value).resolve()
    monkeypatch.syspath_prepend(str(ai_root))
    monkeypatch.chdir(tmp_path)

    backtest = importlib.import_module("aktien_oop.backtest")
    config = importlib.import_module("aktien_oop.config")
    core_calc = importlib.import_module("aktien_oop.core_calc")
    runner_module = importlib.import_module("aktien_oop.runner")
    assert Path(backtest.__file__).resolve() == ai_root / "aktien_oop" / "backtest.py"
    assert Path(config.__file__).resolve() == ai_root / "aktien_oop" / "config.py"

    def load(backtest_path: Path, runner_path: Path):
        monkeypatch.setattr(sys, "argv", ["backtest", "--config", str(backtest_path)])
        backtest_config = backtest._build_cfg_from_config_and_cli(backtest.parse_args())
        monkeypatch.setattr(
            sys,
            "argv",
            ["runner", "--config", str(runner_path), "--save-dir", str(tmp_path / "output")],
        )
        runner_config = config.Config.from_cli()
        runner = runner_module.Runner.__new__(runner_module.Runner)
        runner.cfg = runner_config
        runner_params = runner._build_params(runner._normalize_cfg())
        return backtest_config, runner_config, runner_params, core_calc.calculate_portfolio

    return ai_root, load


def test_balanced_profile_turnover_cap_reaches_both_calculations(
    turnover_contract, tmp_path
):
    ai_root, load = turnover_contract
    repo_root = Path(__file__).resolve().parents[3]
    profile = load_strategy_profile(repo_root / "configs" / "profiles" / "balanced_v1.toml")
    sources = (
        ai_root / "aktien_oop" / "backtest_config.toml",
        ai_root / "aktien_oop" / "configs" / "runner_config.toml",
    )
    original_bytes = tuple(path.read_bytes() for path in sources)
    overlays = (tmp_path / "profile-bt.toml", tmp_path / "profile-runner.toml")
    for source, target in zip(sources, overlays):
        write_strategy_profile_overlay(source, target, profile)

    backtest_config, runner_config, runner_params, calculate_portfolio = load(*overlays)

    assert profile.max_turnover_cap == pytest.approx(0.20)
    assert backtest_config.max_turnover_cap == pytest.approx(0.20)
    assert runner_config.max_turnover_cap == pytest.approx(0.20)
    assert runner_params.max_turnover_cap == pytest.approx(0.20)
    for target in overlays:
        payload = tomllib.loads(target.read_text(encoding="utf-8"))
        assert payload["max_turnover_cap"] == pytest.approx(0.20)
        assert payload["limits"]["max_turnover_cap"] == pytest.approx(0.20)

    dates = pd.date_range("2024-01-01", periods=260, freq="B")
    prices = pd.DataFrame(
        {
            "AAA": [100.0 + index * 0.30 for index in range(len(dates))],
            "BBB": [100.0 + index * 0.20 for index in range(len(dates))],
            "CCC": [100.0 + index * 0.10 for index in range(len(dates))],
        },
        index=dates,
    )

    def get_prices(_universe, _as_of, _period, _adjusted):
        return prices

    def get_sectors(universe):
        return {ticker: f"sector-{ticker}" for ticker in universe}

    common_params = replace(
        runner_params,
        as_of=dates[-1].strftime("%Y-%m-%d"),
        dump_scores=False,
        dump_selection=False,
        dump_weights=False,
    )
    previous_weights = {"AAA": 0.60, "BBB": 0.40}
    uncapped_weights, uncapped_scores = calculate_portfolio(
        tuple(prices.columns),
        replace(common_params, max_turnover_cap=1.0),
        get_prices,
        get_sectors,
        prev_holdings=previous_weights,
        prev_weights=previous_weights,
    )
    capped_weights, capped_scores = calculate_portfolio(
        tuple(prices.columns),
        replace(common_params, max_turnover_cap=0.20),
        get_prices,
        get_sectors,
        prev_holdings=previous_weights,
        prev_weights=previous_weights,
    )

    assert capped_weights == uncapped_weights
    pd.testing.assert_series_equal(capped_scores, uncapped_scores)
    assert _build_weight_change_proposals(previous_weights, capped_weights) == (
        _build_weight_change_proposals(previous_weights, uncapped_weights)
    )
    assert tuple(path.read_bytes() for path in sources) == original_bytes


def test_real_base_config_behavior_without_strategy_profile_remains_unchanged(
    turnover_contract, tmp_path
):
    ai_root, load = turnover_contract
    sources = (
        ai_root / "aktien_oop" / "backtest_config.toml",
        ai_root / "aktien_oop" / "configs" / "runner_config.toml",
    )
    original_bytes = tuple(path.read_bytes() for path in sources)
    baseline_copies = (tmp_path / "base-bt.toml", tmp_path / "base-runner.toml")
    for source_bytes, target in zip(original_bytes, baseline_copies):
        target.write_bytes(source_bytes)

    backtest_config, runner_config, runner_params, _ = load(*baseline_copies)

    assert backtest_config.max_turnover_cap == pytest.approx(0.0)
    assert runner_config.max_turnover_cap == pytest.approx(1.0)
    assert runner_params.max_turnover_cap == pytest.approx(1.0)
    assert tuple(path.read_bytes() for path in sources) == original_bytes
    assert tuple(path.read_bytes() for path in baseline_copies) == original_bytes


@pytest.fixture
def production_turnover_inputs(turnover_contract, tmp_path, monkeypatch):
    ai_root, load = turnover_contract
    monkeypatch.setenv("AKTIEN_OOP_MARKET_CACHE_DIR", str(tmp_path / "market-cache"))
    repo_root = Path(__file__).resolve().parents[3]
    profile = load_strategy_profile(repo_root / "configs/profiles/balanced_v1.toml")
    overlays = (tmp_path / "bt.toml", tmp_path / "runner.toml")
    for source, target in zip(
        ("backtest_config.toml", "configs/runner_config.toml"), overlays
    ):
        write_strategy_profile_overlay(ai_root / "aktien_oop" / source, target, profile)
    bt_cfg, runner_cfg, _, _ = load(*overlays)
    tickers = tmp_path / "tickers.txt"
    meta = tmp_path / "meta.csv"
    tickers.write_text("AAA\nBBB\n", encoding="utf-8")
    meta.write_text("ticker,sector\nAAA,Tech\nBBB,Health\n", encoding="utf-8")
    dates = pd.bdate_range("2024-01-01", periods=320)

    def prices(requested, *args, **kwargs):
        names = [requested] if isinstance(requested, str) else list(requested)
        return pd.DataFrame(100.0, index=dates, columns=names)

    # Network access is forbidden in these isolated production-path tests.
    data_client = importlib.import_module("aktien_oop.data_client")

    def unexpected_download(*args, **kwargs):
        pytest.fail("unexpected market-data download")

    monkeypatch.setattr(data_client.yf, "download", unexpected_download)
    return bt_cfg, runner_cfg, tickers, meta, dates, prices


def test_runner_run_computes_turnover_in_decision_bundle(
    production_turnover_inputs, tmp_path, monkeypatch
):
    _, base_cfg, tickers, meta, dates, prices = production_turnover_inputs
    runner_module = importlib.import_module("aktien_oop.runner")
    previous = {"AAA": 1.0}
    target = {"AAA": 0.4, "BBB": 0.6}
    results = []
    for cap in (base_cfg.max_turnover_cap, 1.0):
        out = tmp_path / f"runner-{cap}"
        cfg = replace(
            base_cfg,
            max_turnover_cap=cap,
            tickers_file=tickers,
            sector_meta_file=meta,
            universe=replace(base_cfg.universe, tickers_file=tickers, meta_file=meta),
            as_of=dates[-1].strftime("%Y-%m-%d"),
            save_dir=out,
            decisions_dir=out / "decisions",
            force_rebalance=True,
            dump_decision_bundles=True,
        )
        runner = runner_module.Runner(cfg)
        runner.store.save_positions(pd.DataFrame([
            {"as_of": dates[-2], "ticker": "AAA", "allocation_pct": 100.0}
        ]))
        monkeypatch.setattr(runner.data, "load_prices", prices)
        monkeypatch.setattr(
            runner.data, "regime_decision", lambda *args: {"ok": True, "action": "PROCEED"}
        )

        def fixed_portfolio(universe, params, *args, **kwargs):
            # Only the sizing input is controlled; run() computes turnover itself.
            assert params.max_turnover_cap == pytest.approx(cap)
            assert kwargs["prev_weights"] == previous
            return target.copy(), pd.Series({"AAA": 2.0, "BBB": 1.0})

        monkeypatch.setattr(runner_module, "calculate_portfolio", fixed_portfolio)
        runner.run()
        bundle_path, = (out / "decisions").glob("RUN_*.json")
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        assert bundle["first_run_no_prev_state"] is False
        assert bundle["turnover_raw"] == pytest.approx(0.6)
        assert bundle["turnover_eff"] == pytest.approx(min(0.6, cap))
        assert bundle["old_weights"] == previous
        assert bundle["new_weights"] == target
        positions = runner.store.load_positions_snapshot_before("2026-01-01").positions
        results.append((bundle, positions))

    pd.testing.assert_frame_equal(results[0][1], results[1][1])
    assert _build_weight_change_proposals(previous, results[0][0]["new_weights"]) == (
        _build_weight_change_proposals(previous, results[1][0]["new_weights"])
    )


def test_backtester_run_computes_turnover_costs_and_equity(
    production_turnover_inputs, tmp_path, monkeypatch
):
    base_cfg, _, tickers, meta, dates, prices = production_turnover_inputs
    backtest = importlib.import_module("aktien_oop.backtest")
    monkeypatch.setattr(backtest, "download_close", prices)
    # Two rebalances exercise a genuine old/new transition after initial entry.
    monkeypatch.setattr(backtest, "rebal_dates", lambda *args: list(dates[-3:-1]))
    results = []
    for cap in (base_cfg.max_turnover_cap, 1.0):
        out = tmp_path / f"bt-{cap}"
        cfg = replace(
            base_cfg,
            max_turnover_cap=cap,
            tickers_file=str(tickers),
            sector_meta=str(meta),
            save_dir=str(out),
            start=dates[0].strftime("%Y-%m-%d"),
            end=dates[-1].strftime("%Y-%m-%d"),
            min_history_days=1,
            cost_bps=20.0,
            slippage_bps=10.0,
            rebalance_every_n=1,
            dump_decision_bundles=False,
        )
        calls = []

        def fixed_portfolio(universe, params, *args, **kwargs):
            assert params.max_turnover_cap == pytest.approx(cap)
            calls.append(kwargs["prev_weights"].copy())
            weights = {"AAA": 1.0} if len(calls) == 1 else {"AAA": 0.4, "BBB": 0.6}
            return weights, pd.Series({"AAA": 2.0, "BBB": 1.0})

        monkeypatch.setattr(backtest, "calculate_portfolio", fixed_portfolio)
        tester = backtest.Backtester(cfg)
        monkeypatch.setattr(
            tester.data, "regime_decision", lambda *args: {"ok": True, "action": "PROCEED"}
        )
        tester.run()
        assert calls == [{}, {"AAA": 1.0}]
        prefix = out / f"bt_{cfg.frequency}_{cfg.top_k}x{cfg.buffer_k}"
        trades = pd.read_csv(f"{prefix}_trades.csv", comment="#")
        positions = pd.read_csv(f"{prefix}_positions.csv", comment="#")
        equity = pd.read_csv(f"{prefix}_equity_curve.csv", comment="#")
        expected_turnover = [min(0.5, cap), min(0.6, cap)]
        assert trades["turnover"].tolist() == pytest.approx(expected_turnover)
        expected_cost = [value * 30.0 / 10000.0 for value in expected_turnover]
        assert trades["trade_cost"].tolist() == pytest.approx(expected_cost)
        assert equity["equity"].iloc[-1] == pytest.approx(
            (1.0 - expected_cost[0]) * (1.0 - expected_cost[1])
        )
        results.append((trades, positions))

    pd.testing.assert_frame_equal(results[0][1], results[1][1])
    pd.testing.assert_frame_equal(
        results[0][0][["enter", "exit"]], results[1][0][["enter", "exit"]]
    )

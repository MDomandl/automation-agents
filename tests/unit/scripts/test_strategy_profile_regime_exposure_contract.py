"""Characterize current behavior; do not prescribe a corrected exposure strategy.

Run with AI_AGENTS_ROOT pointing to the real companion checkout. All portfolios,
overlays, caches and reports belong to tmp_path. No historical market data is used.
"""

from __future__ import annotations

import importlib
import json
import socket
import tomllib
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from scripts.strategy_profiles import (
    load_strategy_profile,
    write_strategy_profile_overlay,
)
from tests.unit.scripts.test_strategy_profile_turnover_contract import (
    turnover_contract as turnover_contract,
)

PROFILES = ("conservative_v1", "balanced_v1", "offensive_v1")
POLICIES = {
    "conservative_v1": (True, "SELL", True),
    "balanced_v1": (True, "HOLD", False),
    "offensive_v1": (False, "HOLD", False),
}


@pytest.fixture
def regime_contract(turnover_contract, monkeypatch, tmp_path):
    # Reuse the cash/turnover tests' real-loader pattern without changing them.
    ai_root, load = turnover_contract
    bt = importlib.import_module("aktien_oop.backtest")
    runner = importlib.import_module("aktien_oop.runner")
    data = importlib.import_module("aktien_oop.data_client")
    repo = Path(__file__).resolve().parents[3]
    sources = (
        ai_root / "aktien_oop/backtest_config.toml",
        ai_root / "aktien_oop/configs/runner_config.toml",
    )
    protected = (
        *sources,
        *(repo / f"configs/profiles/{name}.toml" for name in PROFILES),
    )
    before = {path: path.read_bytes() for path in protected}
    monkeypatch.setenv("AKTIEN_OOP_MARKET_CACHE_DIR", str(tmp_path / "market-cache"))

    def forbidden(*args, **kwargs):
        pytest.fail("unexpected external market-data/network access")

    monkeypatch.setattr(data.yf, "download", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)

    def profile_configs(name):
        profile = load_strategy_profile(repo / f"configs/profiles/{name}.toml")
        paths = (tmp_path / name / "bt.toml", tmp_path / name / "runner.toml")
        for source, target in zip(sources, paths):
            write_strategy_profile_overlay(source, target, profile)
        bt_cfg, run_cfg, _, _ = load(*paths)
        payloads = [tomllib.loads(path.read_text(encoding="utf-8")) for path in paths]
        return profile, bt_cfg, run_cfg, payloads

    yield SimpleNamespace(bt=bt, runner=runner, data=data, configs=profile_configs)
    assert {path: path.read_bytes() for path in protected} == before


@pytest.mark.parametrize("name", PROFILES)
def test_declared_generated_and_loaded_profile_contract(name, regime_contract):
    profile, bt_cfg, run_cfg, payloads = regime_contract.configs(name)
    require, policy, cash = POLICIES[name]
    assert (
        profile.require_above_sma,
        profile.regime_below_action,
        profile.include_cash,
    ) == (
        require,
        policy,
        cash,
    )
    assert profile.regime_sma_days == 200
    assert profile.benchmark_ticker == "SXR8.DE"
    assert not hasattr(profile, "regime_exposure_low")
    for payload in payloads:
        assert payload["regime"]["require_above_sma"] is require
        assert payload["regime"]["regime_below_action"] == policy
        assert payload["regime"]["regime_sma_days"] == 200
        assert payload["include_cash"] is cash
        assert payload["limits"]["include_cash"] is cash
        assert payload["regime"]["include_cash"] is cash
    assert payloads[0]["limits"]["benchmark_ticker"] == "SXR8.DE"
    assert payloads[0]["limits"]["regime_exposure_low"] == pytest.approx(0.65)
    assert "benchmark_ticker" not in payloads[0]  # effective BT default, not root overlay
    assert "regime_exposure_low" not in payloads[0]
    assert "benchmark_ticker" not in payloads[1]
    for cfg in (bt_cfg, run_cfg):
        assert cfg.require_above_sma is require
        assert cfg.regime_below_action == policy
        assert cfg.regime_sma_days == 200
        assert cfg.include_cash is cash
    assert bt_cfg.benchmark_ticker == "SXR8.DE"
    assert bt_cfg.regime_exposure_low == pytest.approx(0.50)
    assert bt_cfg.vol_target_ann is None
    assert not hasattr(run_cfg, "benchmark_ticker")
    assert not hasattr(run_cfg, "regime_exposure_low")


@pytest.fixture
def synthetic_run(regime_contract, monkeypatch, tmp_path):
    c = regime_contract
    dates = pd.bdate_range("2024-01-01", periods=320)
    rebalances = dates[[-6, -3]]
    prices = pd.DataFrame(
        {
            "AAA": [100.0 + i * 0.10 for i in range(len(dates))],
            "BBB": [80.0 + i * 0.07 for i in range(len(dates))],
        },
        index=dates,
    )
    # Both positive and negative returns: a 50% factor also reduces losses.
    base_returns = pd.Series([0.0075, -0.0075, 0.015, -0.015, 0.0075], index=dates[-5:])
    for offset, rate in enumerate((0.01, -0.01, 0.02, -0.02, 0.01), start=len(dates) - 5):
        prices.iloc[offset] = prices.iloc[offset - 1] * pd.Series(
            {"AAA": 1 + rate, "BBB": 1 + rate / 2}
        )
    tickers, meta = tmp_path / "tickers.txt", tmp_path / "meta.csv"
    tickers.write_text("AAA\nBBB\n", encoding="utf-8")
    meta.write_text("ticker,sector\nAAA,Tech\nBBB,Health\n", encoding="utf-8")

    def run(
        name,
        gate_positive=True,
        exposure_positive=True,
        exposure_case=None,
        cadence=1,
        output_root=None,
    ):
        work = Path(output_root) if output_root is not None else tmp_path
        work.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(work)
        monkeypatch.setenv("AKTIEN_OOP_MARKET_CACHE_DIR", str(work / "market-cache"))
        profile, bt_base, run_base, _ = c.configs(name)
        gspc = pd.Series([100.0 + i * 0.01 for i in range(len(dates))], index=dates)
        if not gate_positive:
            gspc.loc[rebalances[1] :] = [80.0 - i * 0.01 for i in range(3)]
        benchmark = pd.Series([100.0 + i * 0.02 for i in range(len(dates))], index=dates)
        if not exposure_positive:
            benchmark.loc[dates[-5] :] = [80.0 - i * 0.02 for i in range(5)]
        if exposure_case == "equal":
            benchmark[:] = 100.0
        elif exposure_case == "short":
            benchmark = benchmark.iloc[-199:]
        elif exposure_case == "missing-day":
            benchmark = benchmark.drop(dates[-1])
        elif exposure_case == "empty":
            benchmark = benchmark.iloc[:0]
        elif exposure_case == "all-nan":
            benchmark[:] = float("nan")
        requests, decisions, core_calls, exposure_calls = [], [], [], []

        def gspc_download(symbol, *, start, end, **kwargs):
            assert symbol == "^GSPC"
            assert kwargs["auto_adjust"] is False
            requests.append(symbol)
            close = gspc.loc[(gspc.index >= pd.Timestamp(start)) & (gspc.index < pd.Timestamp(end))]
            return pd.concat({"Close": close.to_frame("^GSPC")}, axis=1)

        def close_prices(requested, *args, **kwargs):
            names = [requested] if isinstance(requested, str) else list(requested)
            if names == ["SXR8.DE"]:
                return benchmark.to_frame("SXR8.DE")
            if names == ["GEV", "PLTR", "STX"]:
                # Runner's hard-coded diagnostic probe; these are never portfolio candidates.
                return pd.DataFrame(100.0, index=dates, columns=names)
            assert set(names) <= {"AAA", "BBB"}
            return prices[names].copy()

        monkeypatch.setattr(c.data.yf, "download", gspc_download)
        monkeypatch.setattr(c.bt, "download_close", close_prices)
        monkeypatch.setattr(c.bt, "rebal_dates", lambda *args: list(rebalances))
        # Spies call the real functions; no decisions, weights or returns are fabricated.
        real_decision = c.data.DataClient.regime_decision
        real_core = importlib.import_module("aktien_oop.core_calc").calculate_portfolio
        real_exposure = c.bt.apply_exposures_and_cash

        def decision_spy(client, cfg, as_of):
            decision = real_decision(client, cfg, as_of)
            decisions.append((client, as_of, decision))
            return decision

        def core_spy(*args, **kwargs):
            result = real_core(*args, **kwargs)
            core_calls.append((args[1].dump_tag, args[1].as_of, result[0].copy()))
            return result

        def exposure_spy(base, regime_on, bm, sma, low, vt_on, vt_exp, cash, cash_yield):
            result = real_exposure(base, regime_on, bm, sma, low, vt_on, vt_exp, cash, cash_yield)
            exposure_calls.append((base.copy(), result.copy(), regime_on, cash))
            return result

        monkeypatch.setattr(c.data.DataClient, "regime_decision", decision_spy)
        monkeypatch.setattr(c.bt, "calculate_portfolio", core_spy)
        monkeypatch.setattr(c.runner, "calculate_portfolio", core_spy)
        monkeypatch.setattr(c.bt, "apply_exposures_and_cash", exposure_spy)
        bt_out = work / "backtest"
        cfg = replace(
            bt_base,
            tickers_file=str(tickers),
            sector_meta=str(meta),
            save_dir=str(bt_out),
            start=str(dates[0].date()),
            end=str(dates[-1].date()),
            min_history_days=1,
            rebalance_every_n=cadence,
            decisions_dir=str(bt_out / "decisions"),
            dump_decision_bundles=True,
        )
        tester = c.bt.Backtester(cfg)
        reporting_error = None
        if exposure_case in {"empty", "all-nan"}:
            # Current reporting bug: equity/positions/trades are written first, then
            # corrcoef receives a nonempty portfolio and an empty benchmark array.
            # Characterize that failure without patching NumPy or production logic.
            with pytest.raises(ValueError, match="input array dimensions") as error:
                tester.run()
            reporting_error = str(error.value)
        else:
            tester.run()
        prefix = bt_out / f"bt_{cfg.frequency}_{cfg.top_k}x{cfg.buffer_k}"
        positions = pd.read_csv(f"{prefix}_positions.csv", comment="#")
        trades = pd.read_csv(f"{prefix}_trades.csv", comment="#").fillna("")
        equity = pd.read_csv(f"{prefix}_equity_curve.csv", comment="#", parse_dates=["date"])
        initial = positions[positions["as_of"] == str(rebalances[0].date())]
        initial_weights = dict(zip(initial["ticker"], initial["weight"]))
        # The runner starts from the portfolio genuinely selected by the first BT core call.
        out = work / "runner"
        run_cfg = replace(
            run_base,
            tickers_file=tickers,
            sector_meta_file=meta,
            universe=replace(run_base.universe, tickers_file=tickers, meta_file=meta),
            as_of=str(rebalances[1].date()),
            save_dir=out,
            decisions_dir=out / "decisions",
            force_rebalance=True,
            dump_decision_bundles=True,
        )
        runner = c.runner.Runner(run_cfg)
        runner.store.save_positions(
            pd.DataFrame(
                [
                    {
                        "as_of": rebalances[0],
                        "ticker": ticker,
                        "allocation_pct": weight * 100,
                    }
                    for ticker, weight in initial_weights.items()
                ]
            )
        )
        monkeypatch.setattr(runner.data, "load_prices", close_prices)
        runner.run()
        (bundle_path,) = (out / "decisions").glob("RUN_*.json")
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        snapshot = runner.store.load_positions_snapshot_before(str(dates[-1].date())).positions
        return SimpleNamespace(
            profile=profile,
            cfg=cfg,
            dates=dates,
            rebalances=rebalances,
            base_returns=base_returns,
            positions=positions,
            trades=trades,
            equity=equity,
            initial=initial_weights,
            bundle=bundle,
            runner_weights=runner._weights_from_positions(snapshot),
            decisions=[decision for client, _, decision in decisions if client is tester.data],
            core_calls=core_calls,
            exposure_calls=exposure_calls,
            gspc_requests=requests,
            reporting_error=reporting_error,
        )

    return run


@pytest.mark.parametrize("name", PROFILES)
@pytest.mark.parametrize(
    "gate_positive, exposure_positive",
    [(True, False), (False, True), (False, False), (True, True)],
    ids=[
        "A-proceed-low-exposure",
        "B-negative-gate-positive-exposure",
        "C-both-negative",
        "D-both-positive",
    ],
)
def test_profile_signal_matrix_reaches_real_runner_and_backtester(
    name,
    gate_positive,
    exposure_positive,
    synthetic_run,
):
    result = synthetic_run(name, gate_positive, exposure_positive)
    enabled, policy, _ = POLICIES[name]
    action = policy if enabled and not gate_positive else "PROCEED"
    sold = action == "SELL"
    factor = 0.5 if enabled and not exposure_positive else 1.0
    assert result.initial == {"AAA": 0.5, "BBB": 0.5}
    assert [d["action"] for d in result.decisions] == ["PROCEED", action]
    assert result.bundle["regime"]["action"] == action
    assert result.bundle["regime"]["ok"] is (action == "PROCEED")
    expected_weights = {"CASH": 1.0} if sold else result.initial
    final = result.positions[result.positions["as_of"] == str(result.rebalances[1].date())]
    assert dict(zip(final["ticker"], final["weight"])) == expected_weights
    assert result.bundle["old_weights"] == result.initial
    assert result.bundle["new_weights"] == expected_weights
    assert result.runner_weights == expected_weights
    assert [tag for tag, _, _ in result.core_calls].count("BT") == (1 if action != "PROCEED" else 2)
    assert [tag for tag, _, _ in result.core_calls].count("RUN") == (
        1 if action == "PROCEED" else 0
    )
    assert (
        bool(result.gspc_requests) is enabled
    )  # disabled profile never calls the gate data source

    assert len(result.exposure_calls) == 2
    all_returns = []
    for i, (base, actual, regime_on, cash) in enumerate(result.exposure_calls):
        expected_base = result.base_returns.iloc[:3] if i == 0 else result.base_returns.iloc[3:]
        if i == 1 and sold:
            expected_base = expected_base * 0
        pd.testing.assert_series_equal(base, expected_base, check_names=False)
        pd.testing.assert_series_equal(actual, expected_base * factor, check_names=False)
        assert regime_on is enabled
        assert cash == (1.0 if i == 1 and sold else 0.0)
        all_returns.extend(actual.tolist())
    # Only the actual rebalance trades create turnover/costs. Exposure creates none.
    assert len(result.trades) == 2
    assert result.trades["turnover"].tolist() == pytest.approx([0.2, 0.2 if sold else 0.0])
    assert result.trades["trade_cost"].tolist() == pytest.approx([0.0003, 0.0003 if sold else 0.0])
    assert result.trades["enter"].tolist() == ["AAA,BBB", ""]
    assert result.trades["exit"].tolist() == ["", "AAA,BBB" if sold else ""]
    assert result.bundle["turnover_raw"] == pytest.approx(1.0 if sold else 0.0)
    expected_equity = 1.0 - 0.0003
    expected_curve = [expected_equity]
    for i, daily_return in enumerate(all_returns):
        if i == 3 and sold:
            expected_equity *= 1.0 - 0.0003
        expected_equity *= 1.0 + daily_return
        expected_curve.append(expected_equity)
    # Current CSV de-duplicates the shared boundary date, retaining its first row.
    # SELL cost on that boundary therefore first appears in the next day's equity.
    assert result.equity["date"].tolist() == result.dates[-6:].tolist()
    assert result.equity["equity"].tolist() == pytest.approx(expected_curve)
    # Two return periods plus the initial allocation date, no hidden exposure trades.
    assert len(result.equity) == 6


@pytest.mark.parametrize("case", ["equal", "short", "missing-day", "empty", "all-nan"])
def test_backtester_exposure_data_edges_reach_equity(case, synthetic_run):
    result = synthetic_run("balanced_v1", exposure_case=case)
    assert bool(result.reporting_error) is (case in {"empty", "all-nan"})
    assert [d["action"] for d in result.decisions] == ["PROCEED", "PROCEED"]
    factor = pd.Series(1.0, index=result.base_returns.index)
    if case in {"short", "all-nan"}:
        factor[:] = 0.5
    elif case == "missing-day":
        factor.iloc[-1] = 0.5
    expected = result.base_returns * factor
    actual = pd.concat([call[1] for call in result.exposure_calls])
    pd.testing.assert_series_equal(actual, expected, check_names=False)
    assert [call[2] for call in result.exposure_calls] == [case != "empty"] * 2
    assert result.bundle["new_weights"] == {"AAA": 0.5, "BBB": 0.5}
    assert "CASH" not in set(result.positions["ticker"])
    assert result.trades["trade_cost"].tolist() == pytest.approx([0.0003, 0.0])
    assert result.equity["equity"].iloc[-1] == pytest.approx((1 - 0.0003) * (1 + expected).prod())


def test_daily_exposure_also_runs_when_rebalance_is_skipped(synthetic_run):
    result = synthetic_run("balanced_v1", exposure_positive=False, cadence=2)
    assert len(result.decisions) == 1  # second date skips the trading gate/core
    assert len(result.trades) == 1
    assert len(result.exposure_calls) == 2
    actual = pd.concat([call[1] for call in result.exposure_calls])
    pd.testing.assert_series_equal(actual, result.base_returns * 0.5, check_names=False)
    assert result.equity["equity"].iloc[-1] == pytest.approx(
        (1 - 0.0003) * (1 + result.base_returns * 0.5).prod()
    )


@pytest.mark.parametrize(
    "case, gate_ok, exposure_factor",
    [
        ("above", True, 1.0),
        ("equal", False, 1.0),
        ("below", False, 0.5),
        ("empty", True, None),
        ("short", True, 0.5),
        ("all-nan", True, 0.5),
        ("missing-day", True, 0.5),
        ("missing-close", True, None),
    ],
)
def test_sma_boundary_contract(case, gate_ok, exposure_factor, regime_contract, monkeypatch):
    c = regime_contract
    _, cfg, _, _ = c.configs("balanced_v1")
    dates = pd.bdate_range("2024-01-01", periods=201)
    as_of = dates[-1]
    close = pd.Series(100.0, index=dates[-200:])
    if case in {"above", "missing-day"}:
        close.iloc[-1] = 101.0
    elif case == "below":
        close.iloc[-1] = 99.0
    elif case == "short":
        close = close.iloc[-199:]
    elif case == "empty":
        close = close.iloc[:0]
    elif case == "all-nan":
        close[:] = float("nan")
    if case == "missing-day":
        close.index = dates[-201:-1]  # latest quote is stale; latest known SMA is still positive
    frame = close.to_frame("Open" if case == "missing-close" else "Close")

    def provider(symbol, **kwargs):
        assert symbol == "^GSPC"
        return frame.copy()

    monkeypatch.setattr(c.data.yf, "download", provider)
    client = c.data.DataClient(cfg)
    assert client.sp500_above_200dma(str(as_of.date()), 200, "800d") is gate_ok
    assert client.regime_decision(cfg, str(as_of.date()))["action"] == (
        "PROCEED" if gate_ok else "HOLD"
    )
    if exposure_factor is not None:
        series = close.dropna()  # same preparation as Backtester.run
        base = pd.Series([0.02, -0.02], index=[as_of, as_of + pd.offsets.BDay()])
        actual = c.bt.apply_exposures_and_cash(
            base,
            True,
            series,
            series.rolling(200).mean(),
            cfg.regime_exposure_low,
            False,
            None,
            0.0,
            0.0,
        )
        # The next date is absent: unlike the trading gate, exposure does not carry forward.
        assert actual.tolist() == pytest.approx([0.02 * exposure_factor, -0.01])


@pytest.mark.parametrize("cash_weight", [0.4, 1.0])
def test_exposure_scales_only_existing_stock_return_not_cash_yield(cash_weight, regime_contract):
    c = regime_contract
    _, cfg, _, _ = c.configs("conservative_v1")
    dates = pd.bdate_range("2024-01-01", periods=2)
    base = pd.Series([0.01, -0.02], index=dates) * (1.0 - cash_weight)
    bm, sma = pd.Series(90.0, index=dates), pd.Series(100.0, index=dates)
    # Deliberately nonzero synthetic yield to observe cash behavior; profile yield remains zero.
    annual_yield = 0.10
    actual = c.bt.apply_exposures_and_cash(
        base,
        True,
        bm,
        sma,
        cfg.regime_exposure_low,
        False,
        None,
        cash_weight,
        annual_yield,
    )
    daily_cash = (1.0 + annual_yield) ** (1.0 / 252) - 1.0
    pd.testing.assert_series_equal(actual, base * 0.5 + cash_weight * daily_cash)

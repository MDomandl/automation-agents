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
    dates = pd.bdate_range("2024-01-01", periods=320).as_unit("ns")
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
        legacy_diagnostics=False,
        bt_overrides=None,
        block_diagnostic_output=False,
        gate_unknown=False,
    ):
        work = Path(output_root) if output_root is not None else tmp_path
        work.mkdir(parents=True, exist_ok=True)
        monkeypatch.chdir(work)
        monkeypatch.setenv("AKTIEN_OOP_MARKET_CACHE_DIR", str(work / "market-cache"))
        profile, bt_base, run_base, _ = c.configs(name)
        gspc = pd.Series([100.0 + i * 0.01 for i in range(len(dates))], index=dates)
        if gate_unknown:
            gspc = gspc.iloc[:0]
        elif not gate_positive:
            gspc.loc[rebalances[1] :] = [80.0 - i * 0.01 for i in range(3)]
        benchmark = pd.Series([100.0 + i * 0.02 for i in range(len(dates))], index=dates)
        if not exposure_positive:
            benchmark.loc[dates[-5] :] = [80.0 - i * 0.02 for i in range(5)]
        if exposure_case == "equal":
            benchmark[:] = 100.0
        elif exposure_case == "short":
            benchmark = benchmark.iloc[-199:]
        elif exposure_case == "missing-day":
            benchmark = benchmark.drop(dates[-6])
        elif exposure_case == "empty":
            benchmark = benchmark.iloc[:0]
        elif exposure_case == "all-nan":
            benchmark[:] = float("nan")
        elif exposure_case == "alternating":
            benchmark[:] = [100.0 if i % 2 == 0 else 110.0 for i in range(len(dates))]
        requests, decisions, core_calls, exposure_calls, benchmark_requests = [], [], [], [], []

        def gspc_download(symbol, *, start, end, **kwargs):
            assert symbol == "^GSPC"
            assert kwargs["auto_adjust"] is False
            requests.append(symbol)
            close = gspc.loc[(gspc.index >= pd.Timestamp(start)) & (gspc.index < pd.Timestamp(end))]
            return pd.concat({"Close": close.to_frame("^GSPC")}, axis=1)

        def close_prices(requested, *args, **kwargs):
            names = [requested] if isinstance(requested, str) else list(requested)
            if names == ["SXR8.DE"]:
                benchmark_requests.append(kwargs["data_kind"])
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
            legacy_exposure_diagnostics=legacy_diagnostics,
            **(bt_overrides or {}),
        )
        tester = c.bt.Backtester(cfg)
        if block_diagnostic_output:
            (bt_out / f"bt_{cfg.frequency}_{cfg.top_k}x{cfg.buffer_k}_legacy_exposure_diagnostic.json").mkdir()
        tester.run()
        prefix = bt_out / f"bt_{cfg.frequency}_{cfg.top_k}x{cfg.buffer_k}"
        diagnostic_path = Path(f"{prefix}_legacy_exposure_diagnostic.json")
        diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8")) if diagnostic_path.is_file() else None
        summary = Path(f"{prefix}_summary.txt").read_text(encoding="utf-8")
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
            execution_as_of=str(dates[-1].date()),
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
                        "as_of": dates[-5],
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
            diagnostic=diagnostic,
            summary=summary,
            benchmark_requests=benchmark_requests,
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
    result = synthetic_run(name, gate_positive, exposure_positive, legacy_diagnostics=True)
    enabled, policy, _ = POLICIES[name]
    action = policy if enabled and not gate_positive else "PROCEED"
    sold = action == "SELL"
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

    assert result.bundle["configuration_evidence"]["runtime"]["legacy_diagnostics_status"] == "not_supported_in_runner"
    assert result.diagnostic["binding_eligible"] is False
    expected_base = result.base_returns.copy()
    expected_base.iloc[0] = 0.0
    if sold:
        expected_base.iloc[-1] = 0.0
    factors = pd.Series(1.0, index=expected_base.index)
    if enabled and not exposure_positive:
        factors.iloc[2:] = 0.5
    if enabled:
        assert result.diagnostic["status"] == "available"
        actual_base = pd.concat([call[0] for call in result.exposure_calls])
        pd.testing.assert_series_equal(actual_base, expected_base, check_names=False, check_freq=False)
        assert [call[2] for call in result.exposure_calls] == [False, True, not sold]
        assert [call[3] for call in result.exposure_calls] == [0.0, 0.0, 1.0 if sold else 0.0]
        actual_returns = result.diagnostic["daily_returns"]
        assert [row["date"] for row in actual_returns] == [str(day.date()) for day in expected_base.index]
        assert [row["hypothetical_return_before_costs"] for row in actual_returns] == pytest.approx(
            (expected_base * factors).tolist()
        )
    else:
        assert result.diagnostic["status"] == "inactive"
        assert not result.exposure_calls
    # Only the actual rebalance trades create turnover/costs. Exposure creates none.
    assert len(result.trades) == 2
    assert result.trades["turnover"].tolist() == pytest.approx([0.2, 0.2 if sold else 0.0])
    assert result.trades["trade_cost"].tolist() == pytest.approx([0.0003, 0.0003 if sold else 0.0])
    assert result.trades["enter"].tolist() == ["AAA,BBB", ""]
    assert result.trades["exit"].tolist() == ["", "AAA,BBB" if sold else ""]
    assert result.bundle["turnover_raw"] == pytest.approx(1.0 if sold else 0.0)
    expected_equity = 1.0
    expected_curve = [expected_equity]
    for i, daily_return in enumerate(expected_base.tolist()):
        expected_equity *= 1.0 + daily_return
        if i == 0 or (i == 3 and sold):
            expected_equity *= 1.0 - 0.0003
        expected_curve.append(expected_equity)
    assert result.trades["date"].tolist() == [str(day.date()) for day in result.dates[[-5, -2]]]
    assert result.equity["date"].tolist() == result.dates[-6:].tolist()
    assert result.equity["equity"].tolist() == pytest.approx(expected_curve)
    # Two return periods plus the initial allocation date, no hidden exposure trades.
    assert len(result.equity) == 6


@pytest.mark.parametrize("case", ["equal", "short", "missing-day", "empty", "all-nan"])
def test_backtester_exposure_data_edges_reach_equity(case, synthetic_run):
    result = synthetic_run("balanced_v1", exposure_case=case, legacy_diagnostics=True)
    if case == "equal":
        assert result.diagnostic["status"] == "available"
        assert [call[2] for call in result.exposure_calls] == [False, True, True]
    else:
        codes = {"short": "INSUFFICIENT_HISTORY", "missing-day": "MISSING_AS_OF",
                 "empty": "MISSING_LEGACY_EXPOSURE", "all-nan": "NONFINITE_PRICE"}
        assert result.diagnostic["status"] == "unavailable"
        assert codes[case] in {issue["code"] for issue in result.diagnostic["diagnostics"]}
        assert "daily_returns" not in result.diagnostic
    if case in {"empty", "all-nan"}:
        assert "Comparison unavailable" in result.summary
    assert [d["action"] for d in result.decisions] == ["PROCEED", "PROCEED"]
    expected = result.base_returns.copy()
    expected.iloc[0] = 0.0
    if case == "equal":
        actual = pd.concat([call[1] for call in result.exposure_calls])
        pd.testing.assert_series_equal(actual, expected, check_names=False, check_freq=False)
    assert result.bundle["new_weights"] == {"AAA": 0.5, "BBB": 0.5}
    assert "CASH" not in set(result.positions["ticker"])
    assert result.trades["trade_cost"].tolist() == pytest.approx([0.0003, 0.0])
    assert result.equity["equity"].iloc[-1] == pytest.approx((1 - 0.0003) * (1 + expected).prod())


def test_legacy_switch_off_keeps_gate_and_ignores_legacy_parameters(synthetic_run, tmp_path):
    expected = synthetic_run("balanced_v1", gate_positive=False, exposure_positive=False,
                             output_root=tmp_path / "diagnostic", legacy_diagnostics=True)
    actual = synthetic_run("balanced_v1", gate_positive=False, exposure_positive=False,
                           output_root=tmp_path / "default", bt_overrides={
                               "regime_exposure_low": -1.0, "vol_target_ann": 0.25, "vol_lookback_days": 1,
                           })
    assert expected.diagnostic["status"] == "available"
    assert actual.diagnostic is None and not actual.exposure_calls
    assert [d["action"] for d in actual.decisions] == ["PROCEED", "HOLD"]
    assert len(actual.benchmark_requests) == 1
    for field in ("positions", "trades", "equity"):
        pd.testing.assert_frame_equal(getattr(expected, field), getattr(actual, field))
    assert expected.runner_weights == actual.runner_weights


@pytest.mark.parametrize("settings, field", [
    ({"regime_exposure_low": -0.01}, "regime_exposure_low"),
    ({"regime_exposure_low": 1.01}, "regime_exposure_low"),
    ({"vol_target_ann": -0.2}, "vol_target_ann"),
    ({"vol_target_ann": "0.2"}, "vol_target_ann"),
    ({"vol_target_ann": float("nan")}, "vol_target_ann"),
    ({"vol_target_ann": 10 ** 1000}, "vol_target_ann"),
    ({"benchmark_ticker": ["SPY"], "benchmark": ["SPY"]}, "benchmark_ticker"),
    ({"vol_target_ann": 0.2, "vol_lookback_days": 1}, "vol_lookback_days"),
    ({"vol_target_ann": 0.2, "vol_lookback_days": None}, "vol_lookback_days"),
])
def test_bad_opt_in_parameters_only_invalidate_diagnostic(synthetic_run, settings, field):
    actual = synthetic_run("balanced_v1", legacy_diagnostics=True, bt_overrides=settings)
    assert actual.diagnostic["status"] == "unavailable"
    assert actual.diagnostic["diagnostics"][0]["field"] == field
    assert "daily_returns" not in actual.diagnostic
    assert len(actual.trades) == 2
    assert actual.equity["equity"].iloc[-1] > 0
    if field == "benchmark_ticker":
        assert "Comparison unavailable" in actual.summary


@pytest.mark.parametrize("factor", [0.0, 1.0])
def test_regime_diagnostic_bounds(synthetic_run, factor):
    actual = synthetic_run("balanced_v1", exposure_positive=False, legacy_diagnostics=True,
                           bt_overrides={"regime_exposure_low": factor, "vol_target_ann": 0.0})
    if factor == 1.0:
        assert actual.diagnostic["status"] == "inactive"
        assert not actual.exposure_calls
    else:
        assert actual.diagnostic["status"] == "available"
        assert actual.diagnostic["daily_returns"][-1]["hypothetical_return_before_costs"] == 0.0
    assert actual.equity["equity"].pct_change().iloc[-1] == pytest.approx(actual.base_returns.iloc[-1])


@pytest.mark.parametrize("target", [0.20, 3.00])
def test_voltarget_diagnostic_without_regime_gate(synthetic_run, target):
    actual = synthetic_run("offensive_v1", exposure_case="alternating", legacy_diagnostics=True,
                           bt_overrides={"vol_target_ann": target, "vol_lookback_days": 2})
    assert actual.diagnostic["status"] == "available"
    assert actual.diagnostic["regime_scaling"] is False
    assert actual.diagnostic["voltarget_scaling"] is True
    assert actual.gspc_requests == []
    sigma = pd.Series([110 / 100 - 1, 100 / 110 - 1]).std()
    factor = min(1.0, target / (252 ** 0.5 * sigma))
    assert actual.diagnostic["daily_returns"][-1]["hypothetical_return_before_costs"] == pytest.approx(
        actual.base_returns.iloc[-1] * factor
    )
    assert actual.equity["equity"].pct_change().iloc[-1] == pytest.approx(actual.base_returns.iloc[-1])


def test_unsupported_diagnostic_benchmark_does_not_block_comparison(synthetic_run):
    actual = synthetic_run("balanced_v1", legacy_diagnostics=True,
                           bt_overrides={"benchmark_ticker": "UNMAPPED"})
    assert actual.diagnostic["status"] == "unavailable"
    assert actual.diagnostic["diagnostics"][0]["code"] == "UNSUPPORTED_EXPOSURE_CALENDAR"
    assert actual.bundle["new_weights"] == actual.initial
    from scripts.compare_runs import extract_benchmark, extract_performance
    comparison = extract_benchmark(actual.summary, {})
    portfolio = extract_performance(actual.summary, {})
    assert comparison.benchmark_name == "SXR8.DE"
    assert comparison.benchmark_return_pct is not None
    assert comparison.benchmark_cagr_pct is not None
    assert comparison.benchmark_volatility_pct != portfolio.volatility_pct
    assert comparison.benchmark_sharpe_ratio != portfolio.sharpe_ratio
    assert portfolio.volatility_pct == pytest.approx(
        (actual.equity["equity"].pct_change().fillna(0.0).std() * 252 ** 0.5) * 100, abs=0.0051
    )


def test_unrepresentable_legacy_history_does_not_stop_backtest(synthetic_run):
    actual = synthetic_run("offensive_v1", legacy_diagnostics=True, bt_overrides={
        "vol_target_ann": 0.2, "vol_lookback_days": 1_000_000_000,
    })
    assert actual.diagnostic["status"] == "unavailable"
    assert actual.diagnostic["diagnostics"][0]["code"] == "UNREPRESENTABLE_LEGACY_HISTORY"
    assert len(actual.trades) == 2


def test_nonfinite_diagnostic_setting_keeps_d5_failure_artifact(synthetic_run, tmp_path):
    error = importlib.import_module("aktien_oop.core_calc").DataQualityError
    with pytest.raises(error):
        synthetic_run("balanced_v1", legacy_diagnostics=True, gate_unknown=True,
                      bt_overrides={"vol_target_ann": float("nan")})
    failure = json.loads((tmp_path / "backtest/BT_data_quality_invalid.json").read_text(encoding="utf-8"))
    assert failure["action"] == "UNCONFIRMED"
    assert failure["decision_confirmed"] is False
    assert failure["configuration_evidence"]["runtime"]["vol_target_ann"] == "nonfinite: nan"
    assert failure["diagnostics"]
    assert not list((tmp_path / "backtest").glob("*_trades.csv"))


def test_diagnostic_write_error_does_not_stop_backtest(synthetic_run):
    actual = synthetic_run("balanced_v1", legacy_diagnostics=True, block_diagnostic_output=True)
    assert actual.diagnostic is None
    runtime = actual.cfg.configuration_evidence["runtime"]
    assert runtime["legacy_diagnostics_status"] == "write_failed"
    assert runtime["legacy_diagnostics_file"] is None
    assert runtime["legacy_diagnostics_issues"][0]["code"] == "LEGACY_DIAGNOSTIC_OUTPUT_IO"
    assert len(actual.trades) == 2


def test_legacy_run_index_stride_is_rejected_before_exposure_or_trades(synthetic_run, tmp_path):
    error = importlib.import_module("aktien_oop.core_calc").DataQualityError
    with pytest.raises(error, match="UNSUPPORTED_REBALANCE_STRIDE"):
        synthetic_run("balanced_v1", exposure_positive=False, cadence=2)
    assert not list((tmp_path / "backtest").glob("*_trades.csv"))


@pytest.mark.parametrize(
    "case, gate_ok, exposure_factor",
    [
        ("above", True, 1.0),
        ("equal", False, 1.0),
        ("below", False, 0.5),
        ("empty", None, None),
        ("short", None, None),
        ("all-nan", None, None),
        ("missing-day", None, None),
        ("missing-close", None, None),
    ],
)
def test_sma_boundary_contract(case, gate_ok, exposure_factor, regime_contract, monkeypatch):
    c = regime_contract
    _, cfg, _, _ = c.configs("balanced_v1")
    import exchange_calendars as xcals
    dates = xcals.get_calendar("XNYS", start="2023-12-20", end="2025-01-01").sessions_in_range("2024-01-01", "2024-12-31")[:201]
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
        "UNCONFIRMED" if gate_ok is None else "PROCEED" if gate_ok else "HOLD"
    )
    if exposure_factor is not None:
        series = close.dropna()  # same preparation as Backtester.run
        calendar = xcals.get_calendar("XNYS")
        first_after = calendar.next_session(as_of)
        second_after = calendar.next_session(first_after)
        base = pd.Series([0.02, -0.02], index=[first_after, second_after])
        error = importlib.import_module("aktien_oop.core_calc").DataQualityError
        with pytest.raises(error, match="UNKNOWN_LEGACY_EXPOSURE"):
            c.bt.apply_exposures_and_cash(base.iloc[:1], True, series, series.rolling(200).mean(),
                cfg.regime_exposure_low, False, None, 0.0, 0.0)
        # A genuinely available observation still has identical arithmetic.
        actual = c.bt.apply_exposures_and_cash(base.iloc[1:], True, series,
            series.rolling(200).mean(), cfg.regime_exposure_low, False, None, 0.0, 0.0)
        assert actual.tolist() == pytest.approx([-0.02 * exposure_factor])


@pytest.mark.parametrize("cash_weight", [0.4, 1.0])
def test_exposure_scales_only_existing_stock_return_not_cash_yield(cash_weight, regime_contract):
    c = regime_contract
    _, cfg, _, _ = c.configs("conservative_v1")
    dates = pd.to_datetime(["2024-01-08", "2024-01-09"])
    previous = pd.to_datetime(["2024-01-04", "2024-01-05"])
    base = pd.Series([0.01, -0.02], index=dates) * (1.0 - cash_weight)
    bm, sma = pd.Series(90.0, index=previous), pd.Series(100.0, index=previous)
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

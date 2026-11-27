"""D6 tests with the production calendar, Core, Runner, Backtester and Store."""
import importlib
import json
import pickle
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from tests.unit.scripts.test_strategy_profile_turnover_contract import turnover_contract as turnover_contract

pytestmark = pytest.mark.usefixtures("m1_isolation")


@pytest.fixture
def modules(turnover_contract):
    return SimpleNamespace(**{
        module: importlib.import_module(f"aktien_oop.{module}")
        for module in ("backtest", "runner", "rebalance", "core_calc", "config", "market_data_cache")
    })


@pytest.mark.parametrize("signal,execution,frequency", [
    ("2025-06-27", "2025-06-30", "weekly"),
    ("2025-07-03", "2025-07-07", "weekly"),  # Independence Day
    ("2025-08-29", "2025-09-02", "monthly"),  # Weekend month-end and Labor Day
    ("2020-12-31", "2021-01-04", "weekly"),  # ISO week 2020-W53
    ("2024-02-29", "2024-03-01", "monthly"),
    ("2025-02-28", "2025-03-03", "monthly"),
    ("2025-04-30", "2025-05-01", "monthly"),
    ("2025-01-31", "2025-02-03", "monthly"),
    ("2025-11-28", "2025-12-01", "weekly"),  # Early close after Thanksgiving
])
def test_calendar_uses_the_official_last_and_next_sessions(modules, signal, execution, frequency):
    timing = modules.rebalance
    signal = pd.Timestamp(signal)
    execution = pd.Timestamp(execution)
    calendar = modules.core_calc.trading_calendar("XNYS", signal, execution, "synthetic")
    dates = timing.scheduled_signal_days(calendar, signal - pd.Timedelta(days=5), signal, frequency)
    assert dates[-1] == signal
    event = timing.rebalance_time(calendar, signal)
    assert calendar.session_close(signal) < event.decision_time < event.execution_time
    assert event.execution_date == execution
    assert timing.latest_complete_session(calendar, event.decision_time - pd.Timedelta(seconds=1)) < signal
    assert timing.latest_complete_session(calendar, event.decision_time) == signal
    if signal == pd.Timestamp("2020-12-31"):
        assert timing.cadence_period(signal, frequency) == timing.cadence_period("2021-01-03", frequency)
        assert timing.cadence_period(signal, frequency) != timing.cadence_period(execution, frequency)


def test_horizon_mid_interval_does_not_append_a_signal_and_dst_uses_local_close(modules):
    timing = modules.rebalance
    calendar = modules.core_calc.trading_calendar("XNYS", "2025-03-03", "2025-03-14", "synthetic")
    dates = timing.scheduled_signal_days(calendar, "2025-03-03", pd.Timestamp("2025-03-12"), "weekly")
    assert dates == [pd.Timestamp("2025-03-07")]
    event = timing.rebalance_time(calendar, dates[0])
    assert event.decision_time == pd.Timestamp("2025-03-08T05:00:00Z")
    assert event.execution_time == pd.Timestamp("2025-03-10T20:00:00Z")
    now = pd.Timestamp("2025-03-10T16:00:00Z")
    assert timing.observation_time("2025-03-10", now) == now
    assert timing.latest_complete_session(calendar, now) == dates[0]


@pytest.fixture
def runtime(modules, tmp_path, monkeypatch):
    bt, run = modules.backtest, modules.runner
    calendar = modules.core_calc.trading_calendar("XNYS", "2024-01-01", "2025-08-01", "synthetic")
    dates = calendar.sessions_in_range("2024-01-01", "2025-07-31").tz_localize(None)
    prices = pd.DataFrame({"AAA": 100 * 1.002 ** np.arange(len(dates)),
                           "BBB": 100 * 1.001 ** np.arange(len(dates))}, index=dates)
    tickers = tmp_path / "tickers.txt"
    tickers.write_text("AAA\nBBB\n", encoding="utf-8")
    meta = tmp_path / "sectors.csv"
    meta.write_text("ticker,sector\nAAA,Technology\nBBB,Health\n", encoding="utf-8")
    calls = []
    signal = "2025-07-03"
    execution = "2025-07-07"

    def install(frame):
        def bt_prices(names, start, end, **kwargs):
            if kwargs.get("data_kind") == "benchmark":
                return prices[["AAA"]].rename(columns={"AAA": names[0]})
            # Deliberately return the entire preload including future bars.
            return frame.reindex(columns=names).copy()

        def run_prices(names, as_of, period, adjusted):
            calls.append((tuple(names), as_of))
            return frame.reindex(columns=names).copy()

        monkeypatch.setattr(bt, "download_close", bt_prices)
        monkeypatch.setattr(modules.runner.DataClient, "load_prices",
                            lambda self, *args, **kwargs: run_prices(*args))

    def tester(folder, end):
        config = bt.BTConfig(
            tickers_file=str(tickers), sector_meta=str(meta), save_dir=str(folder),
            as_of=None, start="2025-06-30", end=end, frequency="weekly",
            top_k=1, buffer_k=1, use_sector_limits=True, max_per_sector=1, cost_bps=0,
            slippage_bps=0, min_history_days=1, score_days=63, vol_days=10, benchmark="SPY",
            dump_decision_bundles=True, decisions_dir=str(folder / "decisions"),
        )
        return bt.Backtester(config)

    def runner(folder, as_of, *, force=False, available=None, frequency="weekly"):
        config = modules.config.Config(
            tickers_file=tickers, sector_meta_file=meta, save_dir=folder,
            universe=modules.config.UniverseConfig("synthetic", tickers, meta),
            as_of=as_of, execution_as_of=available, rebalance_frequency=frequency,
            force_rebalance=force, require_above_sma=False, top_k=1, buffer_k=1,
            max_per_sector=1, max_active_names=1, dump_decision_bundles=True,
            decisions_dir=folder / "decisions",
        )
        object.__setattr__(config, "windows", {"score_days": 63, "vol_days": 10})
        return run.Runner(config)

    def bundles(folder, kind):
        return [json.loads(file.read_text(encoding="utf-8")) for file in
                sorted((folder / "decisions").glob(f"{kind}_*.json"))]

    install(prices)
    return SimpleNamespace(prices=prices, calls=calls, signal=signal, execution=execution, install=install,
                           tester=tester, runner=runner, bundles=bundles)


def test_real_runner_pending_execution_and_next_invocation_are_distinct(runtime, tmp_path):
    r = runtime
    folder = tmp_path / "runner"
    before_signal = r.runner(folder, "2025-07-03T14:00:00-04:00")
    # The early holiday-week close is still an incomplete daily bar for this clock.
    # The latest available normal signal belongs to the preceding week.
    before_signal.store.save_positions(pd.DataFrame({
        "as_of": ["2025-06-30"], "ticker": ["AAA"], "allocation_pct": [100.0],
    }), signal_as_of="2025-06-27")
    before_signal.run()
    assert not r.calls
    assert not r.bundles(folder, "RUN")

    before_execution = r.runner(folder, "2025-07-07T15:00:00-04:00")
    before_execution.run()
    proposal = json.loads((folder / f"RUN_timing_pending_{r.signal}.json").read_text())
    assert proposal["target_weights"] == {"AAA": 1.0}
    assert proposal["decision_confirmed"] is False
    assert proposal["execution_date"] == r.execution
    assert all(date == r.signal for _, date in r.calls)
    assert before_execution.store.load_latest_positions_snapshot().as_of == pd.Timestamp("2025-06-30")

    at_execution = r.runner(folder, "2025-07-07")
    at_execution.run()
    bundle, = r.bundles(folder, "RUN")
    assert bundle["execution_status"] == "validated_model_close"
    assert bundle["new_weights"] == proposal["target_weights"]
    assert at_execution.store.load_latest_positions_snapshot().as_of == pd.Timestamp(r.execution)
    assert at_execution.store.load_latest_positions_snapshot().signal_as_of == pd.Timestamp(r.signal)
    assert r.calls[-1] == (("AAA",), r.execution)
    call_count = len(r.calls)
    r.runner(folder, "2025-07-08").run()
    assert len(r.calls) == call_count
    assert len(r.bundles(folder, "RUN")) == 1


@pytest.mark.parametrize("kind", ["RUN", "BT"])
@pytest.mark.parametrize("missing", ["row", "value"])
def test_missing_execution_price_never_moves_or_confirms_the_event(runtime, modules, tmp_path, kind, missing):
    r = runtime
    frame = r.prices.copy()
    if missing == "row":
        frame = frame.drop(pd.Timestamp(r.execution))
    else:
        frame.loc[r.execution, "AAA"] = float("nan")
    r.install(frame)
    folder = tmp_path / kind
    instance = r.runner(folder, "2025-07-09") if kind == "RUN" else r.tester(folder, "2025-07-09")
    if kind == "RUN":
        # The prior holding must leave and the higher-priced candidate must enter.
        object.__setattr__(instance.cfg, "min_price", 150.0)
        instance.store.save_positions(pd.DataFrame({
            "as_of": ["2025-06-30"], "ticker": ["BBB"], "allocation_pct": [100.0],
        }), signal_as_of="2025-06-27")
        snapshot = instance.store.positions_path.read_bytes()
    with pytest.raises(modules.core_calc.DataQualityError, match="MISSING_OR_INVALID_EXECUTION_PRICE"):
        instance.run()
    invalid = json.loads((folder / f"{kind}_data_quality_invalid.json").read_text())
    assert invalid["diagnostics"][0]["as_of"] == r.execution
    assert invalid["diagnostics"][0]["signal_as_of"] == r.signal
    assert invalid["decision_confirmed"] is False
    assert not r.bundles(folder, kind)
    if kind == "RUN":
        assert instance.store.positions_path.read_bytes() == snapshot
        assert r.calls[-1][1] == r.execution
    else:
        assert not list(folder.glob("*_trades.csv"))


def test_real_bt_and_runner_have_equal_times_and_choices_after_future_shocks(runtime, tmp_path):
    r = runtime
    baseline, bt_out, run_out = (tmp_path / name for name in ("baseline", "bt", "run"))
    r.tester(baseline, "2025-07-08").run()
    original, = r.bundles(baseline, "BT")
    assert original["new_weights"] == {"AAA": 1.0}

    future = r.prices.copy()
    future.loc[r.execution:, "BBB"] *= 30
    future.loc[r.execution:, "AAA"] /= 2
    r.install(future)
    r.tester(bt_out, "2025-07-08").run()
    r.runner(run_out, r.signal, available="2025-07-08").run()
    bt_result, = r.bundles(bt_out, "BT")
    run_result, = r.bundles(run_out, "RUN")
    for name in ("signal_as_of", "decision_time", "execution_date", "execution_time", "new_weights"):
        assert bt_result[name] == run_result[name] == original[name]
    assert bt_result["scores"] == original["scores"]
    equity = pd.read_csv(next(bt_out.glob("*_equity_curve.csv")), comment="#", index_col="date")
    assert equity.loc[r.execution, "equity"] == 1
    assert equity.loc["2025-07-08", "equity"] == pytest.approx(1.002)


def test_bt_old_weights_earn_through_execution_and_new_weights_earn_after(runtime, tmp_path):
    r = runtime
    prices = r.prices.copy()
    prices.loc["2025-07-10":, "BBB"] *= 2
    prices.loc["2025-07-11":, "AAA"] /= 2
    prices.loc["2025-07-14":, "AAA"] *= 1.25
    prices.loc["2025-07-14":, "BBB"] *= 2
    r.install(prices)
    output = tmp_path / "bt"
    tester = r.tester(output, "2025-07-15")
    tester.cfg.min_price = 150.0
    tester.run()
    first, second = r.bundles(output, "BT")
    assert first["new_weights"] == {"AAA": 1.0}
    assert second["new_weights"] == {"BBB": 1.0}
    equity = pd.read_csv(next(output.glob("*_equity_curve.csv")), comment="#", index_col="date")["equity"]
    assert equity["2025-07-14"] / equity["2025-07-11"] == pytest.approx(1.25 * 1.002)
    assert equity["2025-07-15"] / equity["2025-07-14"] == pytest.approx(1.001)


def test_forced_signal_uses_only_its_explicit_clock_and_no_duplicate(runtime, tmp_path):
    r = runtime
    folder = tmp_path / "run"
    when = "2025-07-02T21:00:00Z"
    first = r.runner(folder, when, force=True)
    first.store.save_positions(pd.DataFrame({
        "as_of": ["2025-06-30"], "ticker": ["AAA"], "allocation_pct": [100.0],
    }))
    first.run()
    proposal = json.loads((folder / "RUN_timing_pending_2025-07-01.json").read_text())
    assert proposal["forced"] is True
    assert proposal["execution_date"] == "2025-07-02"
    r.runner(folder, "2025-07-02").run()
    bundle, = r.bundles(folder, "RUN")
    assert bundle["signal_as_of"] == "2025-07-01"
    assert bundle["signal_forced"] is True
    calls = len(r.calls)
    r.runner(folder, when, force=True, available="2025-07-03").run()
    assert len(r.calls) == calls
    assert len(r.bundles(folder, "RUN")) == 1


def test_cache_does_not_reuse_a_bar_retrieved_before_daily_finality(modules, tmp_path):
    cache_module = modules.market_data_cache
    cache = cache_module.MarketDataCache(tmp_path / "cache")
    request = cache_module.MarketDataRequest.build(
        data_kind="close", tickers=["AAA"], as_of="2025-03-07", final_timezone="America/New_York",
    )
    older = pd.DataFrame({"AAA": [12.0]}, index=pd.to_datetime(["2025-03-07"]))
    current = older * 2
    path = cache.cache_path(request)
    path.parent.mkdir(exist_ok=True)
    with path.open("wb") as file:
        pickle.dump({"metadata": dict(request.key_payload(), created_at="2025-03-07T21:00:00Z"),
                     "frame": older}, file)
    pd.testing.assert_frame_equal(cache.get_or_load_frame(request, lambda: current), current)


def test_legacy_gate_and_volatility_for_today_use_only_previous_information(modules):
    bt = modules.backtest
    calendar = modules.core_calc.trading_calendar("XNYS", "2025-06-20", "2025-07-10", "synthetic")
    dates = calendar.sessions_in_range("2025-06-20", "2025-07-10").tz_localize(None)
    base = pd.Series(0.10, index=pd.to_datetime(["2025-07-07"]))
    price = pd.Series(100.0, index=dates)
    sma = pd.Series(90.0, index=dates)
    vol = pd.Series(0.4, index=dates)
    expected = bt.apply_exposures_and_cash(base, True, price, sma, 0.5, True, vol, 0.0, 0.0)
    price.loc["2025-07-03":] = 2.0
    vol.loc["2025-07-03":] = 0.01
    actual = bt.apply_exposures_and_cash(base, True, price, sma, 0.5, True, vol, 0.0, 0.0)
    pd.testing.assert_series_equal(actual, expected)
    assert actual.iloc[0] == pytest.approx(0.04)


def test_pending_event_is_processed_before_next_signal(runtime, tmp_path):
    r = runtime
    folder = tmp_path / "runner"
    r.runner(folder, r.signal).run()
    r.runner(folder, "2025-07-11").run()
    event, = r.bundles(folder, "RUN")
    assert event["execution_date"] == r.execution
    assert event["signal_as_of"] == r.signal
    assert not (folder / f"RUN_timing_pending_{r.signal}.json").exists()
    r.runner(folder, "2025-07-11").run()
    assert (folder / "RUN_timing_pending_2025-07-11.json").exists()
    assert len(r.bundles(folder, "RUN")) == 1


def test_legacy_snapshot_on_the_execution_date_is_never_overwritten(runtime, modules, tmp_path):
    folder = tmp_path / "runner"
    r = runtime.runner(folder, runtime.signal, available=runtime.execution)
    r.store.save_positions(pd.DataFrame({
        "as_of": [runtime.execution], "ticker": ["BBB"], "allocation_pct": [100.0],
    }))
    before = r.store.positions_path.read_bytes()
    with pytest.raises(modules.core_calc.DataQualityError, match="EXECUTION_SNAPSHOT_CONFLICT"):
        r.run()
    assert r.store.positions_path.read_bytes() == before
    assert not runtime.calls


@pytest.mark.parametrize("kind", ["BT", "RUN"])
def test_foreign_venue_is_diagnosed_before_scoring(runtime, modules, tmp_path, kind):
    (tmp_path / "tickers.txt").write_text("SXR8.DE\n", encoding="utf-8")
    folder = tmp_path / kind
    instance = runtime.tester(folder, runtime.execution) if kind == "BT" else runtime.runner(folder, runtime.execution)
    with pytest.raises(modules.core_calc.DataQualityError, match="UNSUPPORTED_TRADING_CALENDAR"):
        instance.run()
    assert not runtime.calls


@pytest.mark.parametrize("kind,columns", [("close", ["AAA"]), ("ohlc", ["Close", "High", "Low"])])
def test_incomplete_execution_close_is_not_cached(modules, tmp_path, kind, columns):
    spec = modules.market_data_cache
    cache = spec.MarketDataCache(tmp_path / "cache")
    request = spec.MarketDataRequest.build(data_kind=kind, tickers=["AAA"], as_of="2025-07-07",
                                          final_timezone="America/New_York", exact_close=True)
    earlier = pd.DataFrame(12, index=pd.to_datetime(["2025-07-03"]), columns=columns)
    current = pd.DataFrame(np.int64(13), index=pd.to_datetime(["2025-07-07"]), columns=columns)
    cache.get_or_load_frame(request, lambda: earlier)
    assert not cache.cache_path(request).exists()
    pd.testing.assert_frame_equal(cache.get_or_load_frame(request, lambda: current), current)
    assert cache.cache_path(request).exists()


def test_seeder_only_exposes_dated_model_executions(runtime, modules, tmp_path):
    from app.infrastructure.storage.portfolio_store_previous_state_seeder import PortfolioStorePreviousStateSeeder

    output = tmp_path / "bt"
    runtime.tester(output, "2025-07-08").run()
    seeder = PortfolioStorePreviousStateSeeder
    snapshots = seeder._load_bt_snapshots(output / "decisions")
    assert snapshots == {runtime.execution: {"AAA": 1.0}}
    positions = next(output.glob("*_positions.csv"))
    args = dict(bt_positions_path=positions, runner_positions_path=tmp_path / "seed" / "portfolio_positions.csv",
                bt_snapshots=snapshots, portfolio_store_type=modules.runner.PortfolioStore, pandas_module=pd)
    early = seeder._seed(runner_as_of=runtime.execution, **args)
    assert early.seeded is False
    later = seeder._seed(runner_as_of="2025-07-08", **args)
    assert later.seeded is True
    assert later.previous_as_of == runtime.execution

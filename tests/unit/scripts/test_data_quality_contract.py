"""M1.40: controlled data only, real gate/Core/Runner/Backtester and Store."""
import importlib
import json
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from tests.unit.scripts.test_strategy_profile_turnover_contract import turnover_contract as turnover_contract
from tests.unit.scripts.test_strategy_profile_regime_exposure_contract import regime_contract as regime_contract

pytestmark = pytest.mark.usefixtures("m1_isolation")


@pytest.fixture
def quality(regime_contract, tmp_path, monkeypatch):
    c = regime_contract
    core = importlib.import_module("aktien_oop.core_calc")
    import exchange_calendars as xcals
    dates = xcals.get_calendar("XNYS",start="2023-12-20",end="2026-12-31").sessions_in_range("2024-01-01","2026-12-30")[:320]
    prices = pd.DataFrame({"AAA": 100 + np.arange(320) * .10,
                           "BBB": 80 + np.arange(320) * .07}, index=dates)
    gate = pd.DataFrame({"Close": 100 + np.arange(320) * .10}, index=dates)
    benchmark_dates=xcals.get_calendar("XETR",start="2023-12-20",end="2026-12-31").sessions_in_range("2024-01-01",dates[-1])
    benchmark=pd.DataFrame({"Close":100+np.arange(len(benchmark_dates))*.1},index=benchmark_dates)
    cfg = SimpleNamespace(require_above_sma=True, regime_below_action="HOLD",
                          regime_sma_days=200, period="800d")
    client = c.data.DataClient(cfg)
    monkeypatch.setattr(client._market_cache, "get_or_load_frame", lambda req, loader: gate.copy())
    params = core.CalcParams(str(dates[-1].date()), "800d", True, 200, 63,
                             use_sector_limits=True, max_per_sector=1, top_k=2)

    def calculate(frame=prices, sectors=None, previous=None):
        return core.calculate_portfolio(["AAA", "BBB"], params,
            lambda *a: frame.copy(), lambda *a: sectors if sectors is not None else {"AAA":"Tech", "BBB":"Health"},
            prev_weights=previous)

    def run(kind, *, profile="balanced_v1", frame=None, gate_case=None, sectors=True, prior=True, exposure_frame=None):
        work = tmp_path / kind
        work.mkdir(exist_ok=True)
        monkeypatch.chdir(work)
        monkeypatch.setenv("AKTIEN_OOP_MARKET_CACHE_DIR", str(work / "cache"))
        _, bt_base, run_base, _ = c.configs(profile)
        tickers, meta = work / "tickers.txt", work / "meta.csv"
        tickers.write_text("AAA\nBBB\n", encoding="utf-8")
        meta.write_text("ticker,sector\nAAA,Tech\n" + ("BBB,Health\n" if sectors else ""), encoding="utf-8")
        source = prices.copy() if frame is None else frame.copy()
        def download(names, *a, **kw):
            names = [names] if isinstance(names, str) else names
            if names == ["SXR8.DE"]:
                return (benchmark if exposure_frame is None else exposure_frame).rename(columns={"Close":"SXR8.DE"}).copy()
            return source.reindex(columns=names).copy()
        def gspc(symbol, *, start, end, **kw):
            result = gate.loc[(gate.index >= start) & (gate.index < end)].copy()
            # The first BT decision remains valid. Failure on its second decision.
            if gate_case and pd.Timestamp(end) > dates[-3]:
                if gate_case == "empty": result = result.iloc[:0]
                elif gate_case == "short": result = result.tail(10)
                elif gate_case == "missing-day": result = result.iloc[:-1]
                elif gate_case == "nan": result.iloc[-1,0] = np.nan
                elif gate_case == "negative": result.iloc[-1,0] = 10
            return result
        monkeypatch.setattr(c.data.yf, "download", gspc)
        if kind == "BT":
            monkeypatch.setattr(c.bt, "download_close", download)
            monkeypatch.setattr(c.bt, "rebal_dates", lambda *a: list(dates[[-6,-3]]))
            cfg = replace(bt_base, tickers_file=str(tickers), sector_meta=str(meta),
                start=str(dates[0].date()), end=str(dates[-1].date()), min_history_days=1,
                save_dir=str(work), decisions_dir=str(work / "decisions"), dump_decision_bundles=True)
            instance = c.bt.Backtester(cfg)
        else:
            cfg = replace(run_base, tickers_file=tickers, sector_meta_file=meta,
                universe=replace(run_base.universe,tickers_file=tickers,meta_file=meta),
                as_of=str(dates[-3].date()), execution_as_of=str(dates[-1].date()), save_dir=work, decisions_dir=work / "decisions",
                force_rebalance=True, dump_decision_bundles=True)
            instance = c.runner.Runner(cfg)
            monkeypatch.setattr(instance.data, "load_prices", download)
            if prior:
                instance.store.save_positions(pd.DataFrame({"as_of":[dates[-6]], "ticker":["AAA"], "allocation_pct":[100.]}))
        return instance, work

    return SimpleNamespace(c=c, core=core, dates=dates, prices=prices, gate=gate, benchmark=benchmark,
                           client=client, cfg=cfg, params=params, calculate=calculate, run=run)


@pytest.mark.parametrize("case,code", [
    ("empty","EMPTY_REGIME"), ("short","INSUFFICIENT_HISTORY"),
    ("nan","NONFINITE_PRICE"), ("inf","NONFINITE_PRICE"),
    ("zero","NONPOSITIVE_PRICE"), ("missing-day","MISSING_AS_OF"),
    ("gap","UNRESOLVED_SESSION_GAP"), ("duplicate","DUPLICATE_TIMESTAMP"),
    ("unsorted","UNSORTED_TIMESTAMPS"), ("missing-close","MISSING_REGIME_CLOSE"),
    ("wrong-symbol","MISSING_REGIME_CLOSE"),
])
def test_gate_unknown_is_neither_positive_nor_negative(quality, monkeypatch, case, code):
    q=quality
    frame=q.gate.copy()
    if case == "empty": frame=frame.iloc[:0]
    elif case == "short": frame=frame.tail(10)
    elif case in ("nan","inf","zero"): frame.iloc[-1,0]={"nan":np.nan,"inf":np.inf,"zero":0}[case]
    elif case == "missing-day": frame=frame.iloc[:-1]
    elif case == "gap": frame=frame.drop(frame.index[-4])
    elif case == "duplicate": frame=pd.concat([frame,frame.tail(1)])
    elif case == "unsorted": frame=frame.iloc[::-1]
    elif case == "missing-close": frame=frame.rename(columns={"Close":"Open"})
    elif case == "wrong-symbol": frame.columns=pd.MultiIndex.from_tuples([("Close","OTHER")])
    monkeypatch.setattr(q.client._market_cache,"get_or_load_frame",lambda *a:frame)
    result=q.client.regime_decision(q.cfg,str(q.dates[-1].date()))
    assert result["action"] == "UNCONFIRMED" and result["ok"] is None
    assert result["status"] == "invalid"
    assert result["diagnostics"][0]["code"] == code
    assert result["diagnostics"][0]["source"] == "yfinance:^GSPC"


@pytest.mark.parametrize("policy",["HOLD","SELL"])
def test_known_negative_has_policy_and_gate_free_does_not_request_signal(quality, monkeypatch, policy):
    q=quality
    q.gate.iloc[-1,0]=10
    q.cfg.regime_below_action=policy
    d=q.client.regime_decision(q.cfg,str(q.dates[-1].date()))
    assert d["ok"] is False and d["action"]==policy
    q.cfg.require_above_sma=False
    def forbidden(*a,**kw): pytest.fail("disabled gate fetched data")
    monkeypatch.setattr(q.client,"sp500_above_200dma",forbidden)
    assert q.client.regime_decision(q.cfg,str(q.dates[-1].date()))["action"]=="PROCEED"


def test_valid_core_result_and_deterministic_partial_exclusion(quality):
    q=quality
    weights,scores=q.calculate()
    assert weights == {"AAA":.5,"BBB":.5}
    assert scores.attrs["data_quality"] == []
    for value in (np.nan,np.inf,0,-2):
        frame=q.prices.copy(); frame.iloc[-1,1]=value
        weights,scores=q.calculate(frame)
        assert weights=={"AAA":1.0}
        issue=scores.attrs["data_quality"][0]
        assert issue["ticker"]=="BBB" and issue["severity"]=="exclusion"
        assert issue["as_of"]==str(q.dates[-1].date()) and issue["field"]=="Close"
        with pytest.raises(q.core.DataQualityError): q.calculate(frame,previous={"BBB":1.})


@pytest.mark.parametrize("case,code",[("empty","EMPTY_PRICES"),("short","INSUFFICIENT_HISTORY"),
    ("missing-day","MISSING_AS_OF"),("gap","UNRESOLVED_SESSION_GAP"),
    ("duplicate","DUPLICATE_TIMESTAMP"),("unsorted","UNSORTED_TIMESTAMPS")])
def test_core_rejects_invalid_matrix_before_repairs(quality,case,code):
    q=quality; frame=q.prices.copy()
    if case=="empty":frame=frame.iloc[:0]
    elif case=="short":frame=frame.tail(40)
    elif case=="missing-day":frame=frame.iloc[:-1]
    elif case=="gap":frame=frame.drop(frame.index[-3])
    elif case=="duplicate":frame=pd.concat([frame,frame.tail(1)])
    elif case=="unsorted":frame=frame.iloc[::-1]
    with pytest.raises(q.core.DataQualityError,match=code):q.calculate(frame)


def test_unknown_sector_excluded_with_limits_warned_without_limits(quality):
    q=quality
    weights,scores=q.calculate(sectors={"AAA":"Tech","BBB":np.nan})
    assert weights=={"AAA":1.}
    assert any(d["code"]=="UNKNOWN_SECTOR" for d in scores.attrs["data_quality"])
    with pytest.raises(q.core.DataQualityError,match="UNKNOWN_SECTOR"):
        q.calculate(sectors={},previous={"AAA":1.})
    p=replace(q.params,use_sector_limits=False)
    weights,scores=q.core.calculate_portfolio(["AAA","BBB"],p,lambda *a:q.prices,lambda *a:{})
    assert weights=={"AAA":.5,"BBB":.5}
    assert all(d["severity"]=="warning" for d in scores.attrs["data_quality"])


@pytest.mark.parametrize("kind",["BT","RUN"])
@pytest.mark.parametrize("gate_case",["empty","short","missing-day","nan"])
def test_real_runtime_blocks_unknown_and_preserves_confirmed_state(quality,kind,gate_case):
    q=quality; instance,work=q.run(kind,gate_case=gate_case)
    if kind=="RUN": before=instance.store.load_positions_snapshot_before(str(q.dates[-1].date())).positions.copy()
    with pytest.raises(q.core.DataQualityError):instance.run()
    invalid=json.loads((work/f"{kind}_data_quality_invalid.json").read_text())
    assert invalid["status"]=="invalid" and invalid["decision_confirmed"] is False
    assert invalid["action"]=="UNCONFIRMED" and invalid["diagnostics"]
    assert invalid["configuration_evidence"]["binding_eligible"] is False
    if kind=="RUN":
        after=instance.store.load_positions_snapshot_before(str(q.dates[-1].date())).positions
        pd.testing.assert_frame_equal(before,after)
        assert not list((work/"decisions").glob("RUN_*.json"))
    else:
        assert not list(work.glob("*_summary.txt"))
        assert len(list((work/"decisions").glob("BT_*.json")))==1


@pytest.mark.parametrize("kind",["BT","RUN"])
@pytest.mark.parametrize("profile",["balanced_v1","offensive_v1"])
def test_real_valid_runs_and_sector_diagnostics(quality,kind,profile):
    q=quality; instance,work=q.run(kind,profile=profile,sectors=False)
    instance.run()
    bundles=[json.loads(p.read_text()) for p in (work/"decisions").glob(f"{kind}_*.json")]
    assert bundles
    for bundle in bundles:
        e=bundle["configuration_evidence"]["runtime"]
        assert e["data_quality_status"]=="valid"
        assert any(d["code"]=="UNKNOWN_SECTOR" and d["ticker"]=="BBB" for d in e["data_quality"])
        assert "BBB" not in bundle["new_weights"]


@pytest.mark.parametrize("kind",["BT","RUN"])
def test_held_price_failure_is_not_an_automatic_sell(quality,kind):
    q=quality;frame=q.prices.copy();frame.loc[q.dates[-3],"AAA"]=np.nan
    instance,work=q.run(kind,frame=frame)
    with pytest.raises(q.core.DataQualityError):instance.run()
    invalid=json.loads((work/f"{kind}_data_quality_invalid.json").read_text())
    assert any(d["code"]=="NONFINITE_PRICE" for d in invalid["diagnostics"])


def test_exchange_holidays_are_valid_but_missing_open_session_is_not(quality):
    import exchange_calendars as xcals
    q=quality
    sessions=xcals.get_calendar("XNYS",start="2023-12-20",end="2025-12-31").sessions_in_range("2024-01-01","2025-12-30")
    frame=pd.DataFrame({"AAA":100+np.arange(len(sessions))*.1},index=sessions)
    valid,diagnostics=q.core.validate_prices(frame,["AAA"],"2025-12-30",221,"synthetic")
    assert len(valid)==len(frame) and diagnostics==[]
    # Christmas is a closed session, not an unknown market signal.
    valid,diagnostics=q.core.validate_prices(frame,["AAA"],"2025-12-25",221,"synthetic")
    assert valid.index[-1]==pd.Timestamp("2025-12-24")
    assert diagnostics[0]["effective_as_of"]=="2025-12-24"
    with pytest.raises(q.core.DataQualityError,match="UNRESOLVED_SESSION_GAP"):
        q.core.validate_prices(frame.drop(pd.Timestamp("2025-12-23")),["AAA"],"2025-12-30",221,"synthetic")


@pytest.mark.parametrize("value",["123.0",True])
def test_non_numeric_price_types_fail_at_quality_boundary(quality,value):
    q=quality;frame=q.prices.astype(object);frame.loc[:,"AAA"]=value
    with pytest.raises(q.core.DataQualityError,match="NONNUMERIC_PRICE"):
        q.calculate(frame,previous={"AAA":1.})


def test_future_gate_data_are_ignored_and_nonfinite_computed_sma_is_unknown(quality,monkeypatch):
    q=quality
    cutoff = str(q.dates[-2].date())
    q.gate.iloc[-1, 0] = 1.0
    result=q.client.regime_decision(q.cfg,cutoff)
    assert result["action"]=="PROCEED"
    with monkeypatch.context() as scoped:
        scoped.setattr(q.client._market_cache, "get_or_load_frame", lambda *a: q.gate.iloc[:-1].copy())
        assert q.client.regime_decision(q.cfg,cutoff) == result
    # Isolate the calculated-indicator boundary even with finite input prices.
    rolling=pd.core.window.rolling.Rolling
    monkeypatch.setattr(rolling,"mean",lambda self,*a,**kw:pd.Series(np.inf,index=self.obj.index))
    result=q.client.regime_decision(q.cfg,str(q.dates[-1].date()))
    assert result["action"]=="UNCONFIRMED"
    assert result["diagnostics"][0]["code"]=="UNDEFINED_REGIME_SMA"


@pytest.mark.parametrize("kind",["BT","RUN"])
def test_sector_conflicts_cannot_silently_pick_first_row(quality,kind):
    q=quality;instance,work=q.run(kind)
    (work/"meta.csv").write_text("ticker,sector\nAAA,Tech\nBBB,Health\n bbb ,Tech\n",encoding="utf-8")
    instance.run()
    for path in (work/"decisions").glob(f"{kind}_*.json"):
        bundle=json.loads(path.read_text())
        assert "BBB" not in bundle["new_weights"]
        assert any(d["code"]=="UNKNOWN_SECTOR" and d["ticker"]=="BBB"
                   for d in bundle["configuration_evidence"]["runtime"]["data_quality"])


def test_runtime_invocation_evidence_is_fresh_and_preserved(quality,monkeypatch):
    q=quality;instance,work=q.run("RUN")
    object.__setattr__(instance.cfg, "execution_as_of", None)
    instance.run()
    monkeypatch.setattr(instance.data,"regime_decision",lambda *a:{"ok":None,"action":"UNCONFIRMED"})
    with pytest.raises(q.core.DataQualityError):instance.run()
    invalid=json.loads((work/"RUN_data_quality_invalid.json").read_text())
    assert invalid["configuration_evidence"]["runtime"]["core_invoked"] is False
    monkeypatch.setattr(instance.data,"regime_decision",lambda *a:{"ok":True,"action":"PROCEED"})
    frame=q.prices.copy();frame.loc[q.dates[-3],:]=0
    monkeypatch.setattr(instance.data,"load_prices",lambda *a:frame)
    with pytest.raises(q.core.DataQualityError):instance.run()
    invalid=json.loads((work/"RUN_data_quality_invalid.json").read_text())
    assert invalid["configuration_evidence"]["runtime"]["core_invoked"] is True


def test_unsupported_specific_sector_limits_are_explicit(quality):
    q=quality;instance,work=q.run("RUN")
    object.__setattr__(instance.cfg,"sector_limits",{"Tech":1})
    object.__setattr__(instance.cfg,"max_per_sector",0)
    with pytest.raises(q.core.DataQualityError,match="UNSUPPORTED_SPECIFIC_SECTOR_LIMITS"):
        instance.run()


def test_nonfinite_valuation_return_never_becomes_zero(quality):
    q=quality;frame=q.prices.copy()
    frame.loc[q.dates[-5],"AAA"]=1e-308
    frame.loc[q.dates[-4],"AAA"]=1e308
    instance,work=q.run("BT",frame=frame)
    with pytest.raises(q.core.DataQualityError,match="NONFINITE_VALUATION_RETURN"):
        instance.run()
    assert not list(work.glob("*_summary.txt"))


def test_non_sessions_never_count_toward_sma_history(quality,monkeypatch):
    q=quality
    daily=pd.date_range(end=q.dates[-1],periods=200)
    frame=pd.DataFrame({"Close":np.arange(200,dtype=float)+100},index=daily)
    monkeypatch.setattr(q.client._market_cache,"get_or_load_frame",lambda *a:frame)
    result=q.client.regime_decision(q.cfg,str(q.dates[-1].date()))
    assert result["action"]=="UNCONFIRMED"
    assert any(d["code"]=="INSUFFICIENT_HISTORY" for d in result["diagnostics"])


def test_holiday_quote_cannot_replace_effective_session_signal(quality,monkeypatch):
    import exchange_calendars as xcals
    q=quality
    sessions=xcals.get_calendar("XNYS",start="2023-12-20",end="2025-12-31").sessions_in_range("2024-01-01","2025-12-24")
    frame=pd.DataFrame({"Close":100.},index=sessions)
    frame.loc[pd.Timestamp("2025-12-25")]=10000.
    monkeypatch.setattr(q.client._market_cache,"get_or_load_frame",lambda *a:frame)
    result=q.client.regime_decision(q.cfg,"2025-12-25")
    assert result["action"]=="HOLD" and result["ok"] is False
    assert any(d["code"]=="NON_SESSION_OBSERVATION" for d in result["diagnostics"])


@pytest.mark.parametrize("kind",["BT","RUN"])
@pytest.mark.parametrize("value",["123.0",True])
def test_real_runtime_excludes_non_numeric_unheld_candidate(quality,kind,value):
    q=quality;frame=q.prices.copy();frame["BBB"]=value
    instance,work=q.run(kind,frame=frame)
    instance.run()
    for path in (work/"decisions").glob(f"{kind}_*.json"):
        bundle=json.loads(path.read_text())
        assert bundle["new_weights"]=={"AAA":1.}
        assert any(d["code"]=="NONNUMERIC_PRICE" for d in bundle["configuration_evidence"]["runtime"]["data_quality"])


@pytest.mark.parametrize("value",[np.nan,0,-1])
def test_legacy_exposure_cannot_drop_invalid_historical_observation(quality,value):
    q=quality;exposure=q.benchmark.copy();exposure.iloc[-50,0]=value
    baseline,work=q.run("BT")
    baseline.run()
    equity_path=next(work.glob("*_equity_curve.csv"))
    expected=pd.read_csv(equity_path,comment="#")

    instance,work=q.run("BT",exposure_frame=exposure)
    instance.cfg.legacy_exposure_diagnostics=True
    instance.run()
    invalid_path=next(work.glob("*_legacy_exposure_diagnostic.json"))
    invalid=json.loads(invalid_path.read_text(encoding="utf-8"))
    assert invalid["status"]=="unavailable" and "daily_returns" not in invalid
    assert any(d["source"]=="exposure_benchmark" for d in invalid["diagnostics"])
    assert not (work/"BT_data_quality_invalid.json").exists()
    pd.testing.assert_frame_equal(expected,pd.read_csv(equity_path,comment="#"))


def test_non_session_quote_never_changes_bt_equity(quality):
    q=quality
    instance,work=q.run("BT")
    instance.run()
    path=next(work.glob("*_equity_curve.csv"))
    before=pd.read_csv(path,comment="#")
    weekend=next(d for d in pd.date_range(q.dates[-6],q.dates[-1]) if d.weekday()>=5)
    frame=q.prices.copy();frame.loc[weekend]=99999.;frame=frame.sort_index()
    instance,work=q.run("BT",frame=frame)
    instance.run()
    pd.testing.assert_frame_equal(before,pd.read_csv(path,comment="#"))
    payloads=[json.loads(p.read_text()) for p in (work/"decisions").glob("BT_*.json")]
    # Earlier confirmed bundles deliberately remain present after a later run.
    assert any(d["code"]=="NON_SESSION_OBSERVATION" for payload in payloads
               for d in payload["configuration_evidence"]["runtime"]["price_data_quality"])


def test_runner_does_not_invent_an_empty_universe(quality):
    q=quality;instance,work=q.run("RUN")
    (work/"tickers.txt").write_text("",encoding="utf-8")
    with pytest.raises(q.core.DataQualityError,match="INVALID_UNIVERSE"):instance.run()


@pytest.mark.parametrize("kind",["BT","RUN"])
def test_gate_free_runtime_succeeds_without_gate_data(quality,kind):
    q=quality;instance,work=q.run(kind,profile="offensive_v1",gate_case="empty")
    instance.run()
    assert list((work/"decisions").glob(f"{kind}_*.json"))

"""Actual loaders and synthetic production runs; no historical run or network."""

import hashlib
import importlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.strategy_profiles import load_strategy_profile, write_strategy_profile_overlay
from tests.unit.scripts.test_strategy_profile_regime_exposure_contract import (
    regime_contract as regime_contract,
)
from tests.unit.scripts.test_strategy_profile_regime_exposure_contract import (
    synthetic_run as synthetic_run,
)
from tests.unit.scripts.test_strategy_profile_turnover_contract import (
    turnover_contract as turnover_contract,
)

pytestmark = pytest.mark.usefixtures("m1_isolation")
PROFILES = ("conservative_v1", "balanced_v1", "offensive_v1")


@pytest.fixture
def real_loaders(turnover_contract, monkeypatch, tmp_path):
    root, _ = turnover_contract
    bt = importlib.import_module("aktien_oop.backtest")
    config = importlib.import_module("aktien_oop.config")
    runner = importlib.import_module("aktien_oop.runner")

    def load(bt_text="", run_text="", *, bt_cli=(), run_cli=(), second=None):
        paths = [tmp_path / "bt.toml", tmp_path / "run.toml"]
        paths[0].write_text(bt_text, encoding="utf-8")
        paths[1].write_text(run_text, encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["bt", "--config", str(paths[0]), *bt_cli])
        b = bt._build_cfg_from_config_and_cli(bt.parse_args())
        argv = ["run", "--config", str(paths[1]), "--save-dir", str(tmp_path / "out")]
        if second is not None:
            overlay = tmp_path / "second.toml"
            overlay.write_text(second, encoding="utf-8")
            argv += ["--config", str(overlay)]
        monkeypatch.setattr(sys, "argv", [*argv, *run_cli])
        r = config.Config.from_cli()
        instance = runner.Runner.__new__(runner.Runner)
        instance.cfg = r
        norm = instance._normalize_cfg(as_of_str=r.as_of)
        instance._apply_norm_to_cfg(norm, as_of_str=r.as_of)
        params = instance._build_params(norm)
        return b, r, params

    return root, load


@pytest.mark.parametrize("name", PROFILES)
def test_real_profile_provenance_and_effective_values(name, real_loaders, tmp_path):
    root, load = real_loaders
    repo = Path(__file__).resolve().parents[3]
    profile = load_strategy_profile(repo / f"configs/profiles/{name}.toml")
    outputs = [tmp_path / "profile-bt.toml", tmp_path / "profile-run.toml"]
    for source, output in zip(("backtest_config.toml", "configs/runner_config.toml"), outputs):
        write_strategy_profile_overlay(root / "aktien_oop" / source, output, profile)
    b, r, p = load(*(path.read_text(encoding="utf-8") for path in outputs))
    for cfg in (b, r):
        e = cfg.configuration_evidence
        assert e["declared_profile"]["strategy_profile_name"] == name
        assert (
            e["declared_profile"]["profile_sha256"]
            == hashlib.sha256(profile.source_path.read_bytes()).hexdigest()
        )
        assert e["generated"]["include_cash"] is profile.include_cash
        assert e["parameters"]["top_k"]["declared_profile"] == 15
        assert e["parameters"]["top_k"]["loaded"] == 15
        assert e["parameters"]["max_turnover_cap"]["loaded"] == 0.2
        assert e["binding_eligible"] is False
        assert e["parameters"]["require_above_sma"]["source"] == "regime.require_above_sma"
    assert p.include_cash is profile.include_cash
    assert p.top_k == 15 and p.max_turnover_cap == 0.2
    assert r.configuration_evidence["runtime"]["include_cash"] is profile.include_cash
    low = b.configuration_evidence["parameters"]["regime_exposure_low"]
    assert low["generated_candidates"] == {"limits.regime_exposure_low": 0.65}
    assert low["source"] == "loader_default_or_fixed_runtime_default"
    assert low["loaded"] == 0.5
    benchmark = b.configuration_evidence["parameters"]["benchmark_ticker"]
    assert benchmark["generated_candidates"] == {"limits.benchmark_ticker": "SXR8.DE"}
    assert benchmark["loaded"] == "SXR8.DE" and benchmark["source"].startswith("loader_default")
    assert r.configuration_evidence["parameters"]["benchmark_ticker"]["source"] == "not_loaded"


def test_real_root_section_cli_and_runtime_conflicts(real_loaders):
    _, load = real_loaders
    text = (
        "top_k=5\nmax_turnover_cap=0.2\ninclude_cash=true\n"
        "[limits]\nmax_per_sector=2\ninclude_cash=false\n"
        "[regime]\ninclude_cash=true\n"
    )
    b, r, p = load(
        text,
        text,
        bt_cli=("--max-per-sector", "0", "--cost-bps", "0"),
        run_cli=("--max-per-sector", "0", "--no-sector-limits"),
    )
    assert b.include_cash is False and r.include_cash is True
    assert b.max_per_sector == 0 and b.cost_bps == 0
    assert p.max_per_sector == 2  # existing Runner re-normalisation, NOT fixed
    assert p.use_sector_limits is False
    e = r.configuration_evidence
    assert e["parameters"]["max_per_sector"]["loaded"] == 0
    assert e["parameters"]["max_per_sector"]["runtime"] == 2
    assert any(
        f["type"] == "runtime_overrides_loader" and f["parameter"] == "max_per_sector"
        for f in e["findings"]
    )
    assert any(
        f["type"] == "shadowed_or_ignored_value" and f["parameter"] == "include_cash"
        for f in b.configuration_evidence["findings"]
    )


@pytest.mark.parametrize("value", (False, True))
def test_false_is_not_absence_and_zero_is_preserved(value, real_loaders):
    _, load = real_loaders
    text = f"include_cash={str(value).lower()}\nmax_turnover_cap=0\nfriction_eps=0\n"
    b, r, p = load(text, text)
    for cfg in (b, r):
        assert cfg.include_cash is value
        assert cfg.configuration_evidence["parameters"]["include_cash"]["loaded"] is value
        assert cfg.max_turnover_cap == 0
        assert (
            cfg.configuration_evidence["parameters"]["max_turnover_cap"]["source"]
            == "max_turnover_cap"
        )
    assert p.max_turnover_cap == 0


def test_defaults_and_no_profile_are_not_claimed_as_profile_values(real_loaders):
    _, load = real_loaders
    b, r, p = load()
    assert b.max_turnover_cap == 0 and r.max_turnover_cap == 1
    assert b.top_k == 8 and r.top_k == 10
    assert b.frequency == "monthly" and r.rebalance_frequency == "weekly"
    for cfg in (b, r):
        assert cfg.configuration_evidence["declared_profile"] is None
        assert cfg.configuration_evidence["parameters"]["top_k"]["source"].startswith(
            "loader_default"
        )
    assert p.adjusted is True


def test_passed_but_unused_core_window_flags_are_not_claimed_active(real_loaders):
    import pandas as pd

    _, load = real_loaders
    _, cfg, params = load()
    core = importlib.import_module("aktien_oop.core_calc")
    dates = pd.bdate_range("2024-01-01", periods=320)
    prices = pd.DataFrame(
        {"AAA": [100 + i * 0.1 for i in range(320)], "BBB": [80 + i * 0.05 for i in range(320)]},
        index=dates,
    )
    params = replace(
        params,
        as_of=str(dates[-1].date()),
        dump_scores=False,
        dump_weights=False,
        dump_selection=False,
    )
    first = core.calculate_portfolio(
        ["AAA", "BBB"], params, lambda *args: prices, lambda names: {t: t for t in names}
    )
    second = core.calculate_portfolio(
        ["AAA", "BBB"],
        replace(params, vol_days=1, sma_days=1, use_under_sma=True),
        lambda *args: prices,
        lambda names: {t: t for t in names},
    )
    assert first[0] == second[0]
    pd.testing.assert_series_equal(first[1], second[1])
    usage = cfg.configuration_evidence["core_parameter_usage"]
    assert "not read" in usage["vol_days"]
    assert "not read" in usage["use_under_sma/sma_days"]


def test_runner_chain_records_each_file_and_winning_origin(real_loaders, tmp_path):
    _, load = real_loaders
    _, r, p = load(
        run_text="top_k=6\n[limits]\nmax_active_names=4\n",
        second="top_k=7\n[limits]\nmax_active_names=3\n",
    )
    e = r.configuration_evidence
    assert p.top_k == 7 and p.max_active_names == 3
    assert len(e["sources"]) == 2
    assert e["sources"][0]["values"]["top_k"] == 6
    assert e["parameters"]["top_k"]["source_file"] == str((tmp_path / "second.toml").resolve())
    assert (
        e["sources"][1]["sha256"]
        == hashlib.sha256((tmp_path / "second.toml").read_bytes()).hexdigest()
    )


def test_ignored_unknown_and_invalid_policy_are_visible(real_loaders):
    _, load = real_loaders
    text = (
        'extends="missing.toml"\nadjusted=false\n'
        "[limits]\nmax_turnover_capp=0.9\ncost_bps=0\n"
        '[regime]\nregime_below_action="INVALID"\nregime_sma_days=0\n'
    )
    b, r, p = load(text, text)
    assert b.regime_below_action == r.regime_below_action == "HOLD"
    assert p.adjusted is True  # root adjusted=false is currently ignored
    assert r.regime_sma_days == 200  # truthiness fallback remains unchanged
    for cfg in (b, r):
        findings = cfg.configuration_evidence["findings"]
        assert any(
            f["type"] == "unknown_key" and f["parameter"] == "limits.max_turnover_capp"
            for f in findings
        )
        assert any(f["type"] == "unsupported_inheritance" for f in findings)
        assert any(
            f["parameter"] == "regime_below_action" and f["type"] == "loader_conversion_or_fallback"
            for f in findings
        )


def test_explicit_benchmark_exposure_cli_is_observed_without_changing_defaults(real_loaders):
    _, load = real_loaders
    text = (
        'regime_exposure_low=0.3\nbenchmark="SPY"\n'
        '[limits]\nregime_exposure_low=0.65\nbenchmark_ticker="SXR8.DE"\n'
    )
    b, _, _ = load(text, bt_cli=("--regime-exposure-low", "0", "--benchmark", "^GSPC"))
    assert b.regime_exposure_low == 0 and b.benchmark_ticker == "^GSPC"
    assert (
        b.configuration_evidence["parameters"]["regime_exposure_low"]["source"]
        == "cli.regime_exposure_low"
    )
    assert b.configuration_evidence["parameters"]["benchmark_ticker"]["source"] == "cli.benchmark"


@pytest.mark.parametrize("name", PROFILES)
@pytest.mark.parametrize("gate_positive", (True, False))
def test_real_runtime_and_written_artifacts(name, gate_positive, synthetic_run, tmp_path):
    result = synthetic_run(name, gate_positive=gate_positive, exposure_positive=False)
    e = result.bundle["configuration_evidence"]
    assert e["kind"] == "RUN" and e["runtime"]["gate_ticker"] == "^GSPC"
    assert e["runtime"]["legacy_exposure_active"] is False
    assert e["runtime"]["include_cash"] is result.profile.include_cash
    assert e["runtime"]["max_turnover_cap"] == 0.2
    assert e["runtime"]["universe_tickers"] == ["AAA", "BBB"]
    assert e["runtime"]["sector_mapping"] == {"AAA": "Tech", "BBB": "Health"}
    assert e["runtime"]["decision"]["action"] == (
        "PROCEED" if gate_positive or name == "offensive_v1" else result.profile.regime_below_action
    )
    bt_files = sorted((tmp_path / "backtest/decisions").glob("BT_*.json"))
    assert len(bt_files) == 2
    for path in bt_files:
        bundle = json.loads(path.read_text(encoding="utf-8"))
        evidence = bundle["configuration_evidence"]
        assert evidence["runtime"]["as_of"] == bundle["as_of"]
        assert evidence["runtime"]["legacy_exposure_active"] is (name != "offensive_v1")
        assert evidence["runtime"]["legacy_exposure_factor"] == 0.5
        assert evidence["runtime"]["cost_bps"] == 10  # limits.cost_bps=0 ignored
        assert evidence["runtime"]["slippage_bps"] == 5  # limits.slippage_bps=7 ignored
        assert evidence["runtime"]["sizing"] == "equal_initial_weights"
        assert evidence["runtime"]["universe_tickers"] == ["AAA", "BBB"]
        assert evidence["runtime"]["sector_mapping"] == {"AAA": "Tech", "BBB": "Health"}
        assert evidence["binding_eligible"] is False
    snapshot = json.loads(
        next((tmp_path / "backtest").glob("*_params.json")).read_text(encoding="utf-8")
    )
    assert snapshot["configuration_evidence"]["runtime"]["max_turnover_cap"] == 0.2


def test_diagnostic_snapshots_deterministic_and_no_shared_mutation(real_loaders):
    _, load = real_loaders
    diagnostics = importlib.import_module("aktien_oop.configuration_evidence")
    assert diagnostics._equivalent(None, None, "sector_meta")
    text = "top_k=6\nmax_turnover_cap=0\n"
    first = load(text, text)
    snapshot = diagnostics.evidence_snapshot(first[1])
    second = load(text, text)
    assert snapshot == diagnostics.evidence_snapshot(second[1])
    clone = replace(first[1], top_k=9)
    diagnostics.observe_runtime(clone, "RUN", top_k=9)
    assert diagnostics.evidence_snapshot(first[1]) == snapshot
    with pytest.raises(ValueError, match="diagnostic"):
        diagnostics.require_binding_evidence(snapshot)
    with pytest.raises(ValueError, match="diagnostic"):
        diagnostics.require_binding_evidence(None)


def test_cadence_skip_preserves_existing_portfolio_without_evaluation(
    real_loaders, tmp_path, monkeypatch, capsys
):
    import pandas as pd

    _, load = real_loaders
    _, cfg, _ = load(run_text='as_of="2025-04-30"\n')
    tickers = tmp_path / "tickers.txt"
    meta = tmp_path / "meta.csv"
    tickers.write_text("AAA\n", encoding="utf-8")
    meta.write_text("ticker,sector\nAAA,Tech\n", encoding="utf-8")
    cfg = replace(
        cfg,
        universe=replace(cfg.universe, tickers_file=tickers, meta_file=meta),
        tickers_file=tickers,
        sector_meta_file=meta,
        force_rebalance=False,
        decisions_dir=tmp_path / "decisions",
    )
    module = importlib.import_module("aktien_oop.runner")

    class FrozenTimestamp:
        def __new__(cls, *args, **kwargs):
            return pd.Timestamp(*args, **kwargs)

        @staticmethod
        def now():
            return pd.Timestamp("2025-04-30")

    class FrozenPandas:
        Timestamp = FrozenTimestamp

        def __getattr__(self, name):
            return getattr(pd, name)

    monkeypatch.setattr(module, "pd", FrozenPandas())
    runner = module.Runner(cfg)
    runner.store.save_positions(
        pd.DataFrame([{"as_of": "2025-04-29", "ticker": "AAA", "allocation_pct": 100.0}])
    )
    protected = (runner.store.positions_path, runner.store.snapshots_path)
    before = [p.read_bytes() for p in protected]
    runner.run()
    assert [p.read_bytes() for p in protected] == before
    assert "AAA" in capsys.readouterr().out
    assert not cfg.decisions_dir.exists()


@pytest.mark.parametrize("name", PROFILES)
def test_evidence_has_no_effect_on_decisions_or_accounting(
    name, synthetic_run, monkeypatch, tmp_path
):
    import pandas as pd

    observed = synthetic_run(
        name, gate_positive=False, exposure_positive=False, output_root=tmp_path / "observed"
    )
    for module_name in ("aktien_oop.runner", "aktien_oop.backtest"):
        module = importlib.import_module(module_name)
        monkeypatch.setattr(module, "observe_runtime", lambda *args, **kwargs: None)
    baseline = synthetic_run(
        name, gate_positive=False, exposure_positive=False, output_root=tmp_path / "baseline"
    )
    pd.testing.assert_frame_equal(observed.positions, baseline.positions)
    pd.testing.assert_frame_equal(observed.trades, baseline.trades)
    pd.testing.assert_frame_equal(observed.equity, baseline.equity)
    assert observed.runner_weights == baseline.runner_weights
    assert observed.decisions == baseline.decisions


def test_skip_bundle_diagnostic_is_truthful(synthetic_run, tmp_path):
    synthetic_run("balanced_v1", cadence=2)
    bundles = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in (tmp_path / "backtest/decisions").glob("BT_*.json")
    ]
    skipped = [b for b in bundles if b["configuration_evidence"]["runtime"].get("cadence_skipped")]
    assert len(skipped) == 1
    assert skipped[0]["configuration_evidence"]["runtime"]["as_of"] == skipped[0]["as_of"]
    assert skipped[0]["configuration_evidence"]["runtime"]["core_invoked"] is False


def test_ignored_gate_cli_is_not_claimed_effective(real_loaders):
    _, load = real_loaders
    b, _, _ = load(bt_cli=("--regime-use-filter",))
    assert b.require_above_sma is False
    assert any(
        f["parameter"] == "cli.regime_use_filter" and f["type"] == "unused_cli_argument"
        for f in b.configuration_evidence["findings"]
    )
    b, _, _ = load(bt_cli=("--regime-sma-days", "17"))
    assert b.regime_sma_days == 200
    assert any(
        f["parameter"] == "cli.regime_sma_days" and f["type"] == "unused_cli_argument"
        for f in b.configuration_evidence["findings"]
    )


def test_runner_period_cli_is_overridden_by_runtime_section(real_loaders):
    _, load = real_loaders
    _, r, p = load(run_text='[core]\nperiod="800d"\n', run_cli=("--period", "400d"))
    assert p.period == "800d"
    entry = r.configuration_evidence["parameters"]["period"]
    assert entry["loaded"] == "400d" and entry["runtime"] == "800d"


def test_runner_stale_requested_asof_is_unconfirmed(
    synthetic_run, regime_contract, monkeypatch
):
    import pandas as pd

    original_run = regime_contract.runner.Runner.run

    def requested_after_data(runner):
        object.__setattr__(runner.cfg, "as_of", "2025-04-01")
        return original_run(runner)

    monkeypatch.setattr(regime_contract.runner.Runner, "run", requested_after_data)
    # M1.40 supersedes the former permissive fallback characterization.
    core = importlib.import_module("aktien_oop.core_calc")
    with pytest.raises(core.DataQualityError, match="MISSING_AS_OF"):
        synthetic_run("balanced_v1")


def test_toml_dates_survive_real_runner_bundle(real_loaders, monkeypatch, tmp_path):
    _, load = real_loaders
    _, cfg, p = load(
        run_text="as_of=2025-04-30\n[notes]\ncreated=2025-04-30T14:00:00Z\ncutoff=14:00:00\n"
    )
    runner_module = importlib.import_module("aktien_oop.runner")
    runner = runner_module.Runner.__new__(runner_module.Runner)
    runner.cfg = replace(cfg, decisions_dir=tmp_path / "decisions")
    runner.universe_name = "synthetic"
    runner.universe_file = tmp_path / "tickers.txt"
    monkeypatch.setattr(runner, "load_tickers", lambda: ["AAA"])
    runner._write_decision_bundle(p.as_of, {}, {"AAA": 1.0})
    bundle = json.loads(
        next((tmp_path / "decisions").glob("RUN_*.json")).read_text(encoding="utf-8")
    )
    e = bundle["configuration_evidence"]
    assert e["generated"]["as_of"] == "2025-04-30"
    assert e["sources"][0]["values"]["notes"]["created"] == "2025-04-30T14:00:00+00:00"
    assert e["generated"]["notes"]["cutoff"] == "14:00:00"


def test_core_provenance_and_rebalance_alias(real_loaders, tmp_path):
    _, load = real_loaders
    text = (
        'universe_name="root"\nsector_meta="root.csv"\n'
        '[core]\nuniverse_name="core"\nsector_meta="core.csv"\n'
        '[rebalance]\nfrequency="monthly"\n'
    )
    _, r, p = load(run_text=text, run_cli=("--rebalance", "weekly"))
    e = r.configuration_evidence
    assert r.universe.name == "core"
    assert e["parameters"]["universe_name"]["source"] == "core.universe_name"
    assert r.sector_meta_file == (tmp_path / "core.csv").resolve()
    assert e["parameters"]["sector_meta_file"]["source"] == "core.sector_meta"
    assert e["parameters"]["rebalance_frequency"]["loaded"] == "weekly"
    assert e["parameters"]["rebalance_frequency"]["runtime"] == p.rebalance == "monthly"


def test_effective_gate_fallback_with_real_synthetic_data(real_loaders, monkeypatch):
    import pandas as pd

    _, load = real_loaders
    b, _, _ = load(bt_text="[regime]\nrequire_above_sma=true\nregime_sma_days=0\n")
    data = importlib.import_module("aktien_oop.data_client")
    dates = pd.bdate_range("2024-01-01", periods=220)
    close = pd.Series([100 + i for i in range(len(dates))], index=dates)

    def synthetic_download(*args, **kwargs):
        return pd.concat({"Close": close.to_frame("^GSPC")}, axis=1)

    monkeypatch.setattr(data.yf, "download", synthetic_download)
    client = data.DataClient(b)
    assert client.regime_decision(b, str(dates[-1].date()))["action"] == "PROCEED"
    e = b.configuration_evidence
    assert e["parameters"]["regime_sma_days"]["loaded"] == 0
    assert e["parameters"]["regime_sma_days"]["runtime"] == 200
    assert e["runtime"]["gate_sma_days"] == 200 and e["runtime"]["gate_period"] == "800d"


def test_empty_exposure_ticker_fallback_and_skip_reset(
    synthetic_run, regime_contract, monkeypatch, tmp_path
):
    original_configs = regime_contract.configs

    def configs(name):
        profile, b, r, payload = original_configs(name)
        return profile, replace(b, benchmark_ticker=""), r, payload

    monkeypatch.setattr(regime_contract, "configs", configs)
    # synthetic_run installs its own two-date schedule. Wrap the real call to
    # extend it to 3 events; n=2 must produce trade, skip, trade.
    original_run = regime_contract.bt.Backtester.run

    def run_three(tester):
        dates = __import__("pandas").bdate_range("2024-01-01", periods=320)
        monkeypatch.setattr(
            regime_contract.bt, "rebal_dates", lambda *args: list(dates[[-6, -3, -2]])
        )
        return original_run(tester)

    monkeypatch.setattr(regime_contract.bt.Backtester, "run", run_three)
    synthetic_run("balanced_v1", cadence=2)
    bundles = sorted(
        (
            json.loads(p.read_text(encoding="utf-8"))
            for p in (tmp_path / "backtest/decisions").glob("BT_*.json")
        ),
        key=lambda b: b["as_of"],
    )
    assert len(bundles) == 3
    assert [b["configuration_evidence"]["runtime"]["cadence_skipped"] for b in bundles] == [
        False,
        True,
        False,
    ]
    assert bundles[-1]["configuration_evidence"]["runtime"]["exposure_ticker"] == "SXR8.DE"


def test_real_bt_normalization_and_zero_cap_manifest(
    synthetic_run, regime_contract, monkeypatch, tmp_path
):
    original = regime_contract.configs

    def zero_config(name):
        profile, b, r, payload = original(name)
        return (
            profile,
            replace(
                b,
                top_k=0,
                buffer_k=0,
                score_days=0,
                vol_days=0,
                max_turnover_cap=0,
                max_per_sector=0,
            ),
            r,
            payload,
        )

    monkeypatch.setattr(regime_contract, "configs", zero_config)
    synthetic_run("balanced_v1")
    for path in (tmp_path / "backtest/decisions").glob("BT_*.json"):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        runtime = bundle["configuration_evidence"]["runtime"]
        assert runtime["top_k"] == 12 and runtime["buffer_k"] == 3
        assert runtime["score_days"] == 252 and runtime["vol_days"] == 63
        assert runtime["max_turnover_cap"] == 0
        assert bundle["params"]["max_turnover_cap"] == 0
        assert bundle["max_per_sector"] == runtime["max_per_sector"] == 0

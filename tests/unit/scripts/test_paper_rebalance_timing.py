"""Synthetic checks of the BT/RUN timing hand-off and its Paper report."""
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path

import pandas as pd
import pytest

from app.agents.bt_run_agent import BtRunAgentInput, BtRunCompareInput
from app.bootstrap.bt_run_container import build_bt_run_agent
from app.domain.bt_run.run_context import CompareMode, RunContext, RunnerMode, RunProfile
from app.infrastructure.process.subprocess_runner import ProcessResult, SubprocessRunner
from app.tools.process.run_backtest_tool import RunBacktestToolInput
from app.tools.process.run_runner_tool import RunRunnerTool, RunRunnerToolInput, runner_option
from scripts.run_bt_run_agent import build_paper_run_artifact, write_paper_run_report
from tests.unit.scripts.test_rebalance_timing_contract import (
    modules as modules,
    runtime as runtime,
    turnover_contract as turnover_contract,
)

pytestmark = pytest.mark.usefixtures("m1_isolation")


@pytest.fixture
def paper_workflow(runtime, modules, tmp_path, monkeypatch):
    folder = tmp_path / "synthetic-model"
    decisions = folder / "decisions"
    config = tmp_path / "synthetic.toml"
    config.write_text("", encoding="utf-8")
    context = RunContext(
        run_id="synthetic-paper", run_timestamp=datetime(2025, 7, 8),
        run_label="synthetic-paper", profile=RunProfile.SHORT, compare_mode=CompareMode.LATEST,
        ai_agents_dir=tmp_path, aktien_oop_dir=folder, decisions_dir=decisions,
        output_dir=tmp_path / "report", backtest_config_path=config, runner_config_path=config,
        runner_mode=RunnerMode.PAPER,
    )
    context.output_dir.mkdir()
    instance = runtime.runner(folder, runtime.signal)
    instance.store.save_positions(
        pd.DataFrame({"as_of": ["2025-06-30"], "ticker": ["AAA"], "allocation_pct": [100.0]}),
        signal_as_of="2025-06-27",
    )
    previous_bytes = instance.store.positions_path.read_bytes()
    agent_input = BtRunAgentInput(
        backtest_input=RunBacktestToolInput(("bt",), config),
        runner_input=RunRunnerToolInput(("run",), config),
        compare_input=BtRunCompareInput(),
        require_bt_bundles_for_compare=True,
    )

    def run(
        *, horizon=None, missing_price=False, liquidate=False, attempts=1,
        configured_horizon=None, skip_backtest=False, explicit_signal=None, invalid_bundle=None,
    ):
        errors = []
        if configured_horizon is not None:
            config.write_text(
                f"[core]\nexecution_as_of = {json.dumps(configured_horizon)}\n", encoding="utf-8",
            )

        def in_process(_self, command, *, cwd=None, timeout_seconds=None):
            if command[0] == "bt":
                if not skip_backtest:
                    runtime.tester(folder, runtime.execution).run()
            else:
                runner = runtime.runner(
                    folder, runner_option(command, "--as-of"),
                    available=runner_option(command, "--execution-as-of") or configured_horizon,
                )
                if missing_price:
                    runtime.install(runtime.prices.drop(pd.Timestamp(runtime.execution)))
                if liquidate:
                    monkeypatch.setattr(runner.data, "regime_decision", lambda *_: {
                        "action": "SELL", "ok": False, "status": "valid",
                    })
                try:
                    if invalid_bundle is None:
                        runner.run()
                    else:
                        (decisions / f"RUN_invalid_{runtime.signal}.json").write_text(
                            json.dumps(invalid_bundle), encoding="utf-8",
                        )
                except modules.core_calc.DataQualityError as exc:
                    errors.append(str(exc))
                    return ProcessResult(command, 1, "", str(exc), None, 0.0)
            return ProcessResult(command, 0, "", "", None, 0.0)

        monkeypatch.setattr(SubprocessRunner, "run", in_process)
        command = ("run", f"--as-of={explicit_signal}") if explicit_signal else ("run",)
        options = replace(
            agent_input, compare_point_count=6,
            runner_input=replace(
                agent_input.runner_input, command=command, execution_as_of_override=horizon,
            ),
        )
        agent = build_bt_run_agent(decisions)
        results = [agent.execute(options) for _ in range(attempts)]
        return results, errors

    return context, run, instance, previous_bytes


def test_after_execution_close_but_before_final_daily_bar_is_pending(runtime, paper_workflow):
    context, run, instance, previous_bytes = paper_workflow
    (result,), errors = run(horizon="2025-07-07T21:00:00Z")
    assert not errors and result.runner.success
    assert result.runner.command[-4:] == (
        "--as-of", runtime.signal, "--execution-as-of", "2025-07-07T21:00:00Z",
    )
    assert not runtime.bundles(context.aktien_oop_dir, "RUN")
    assert instance.store.positions_path.read_bytes() == previous_bytes
    assert {as_of for _, as_of in runtime.calls} == {runtime.signal}
    artifact = build_paper_run_artifact(context, result)
    report = json.loads(write_paper_run_report(context, artifact).read_text(encoding="utf-8"))
    assert report["decision_status"] == report["execution_status"] == "pending"
    assert report["decision_confirmed"] is False
    assert report["decision_bundle"] is None
    assert report["signal_as_of"] == runtime.signal
    assert report["execution_date"] == runtime.execution
    assert report["previous_positions"] == {"AAA": 1.0}
    assert report["target_positions"] is report["cash_weight"] is None
    assert report["buy_proposals"] == report["sell_proposals"] == report["hold_proposals"] == []


@pytest.mark.parametrize("liquidate", [False, True])
def test_wrapper_hands_off_bt_observation_and_reports_confirmed_target(
    runtime, tmp_path, paper_workflow, liquidate,
):
    context, run, instance, _ = paper_workflow
    (result,), errors = run(liquidate=liquidate)
    bt, = runtime.bundles(context.aktien_oop_dir, "BT")
    runner, = runtime.bundles(context.aktien_oop_dir, "RUN")
    horizon = bt["configuration_evidence"]["runtime"]["execution_observed_through"]
    assert result.runner.command[-4:] == ("--as-of", runtime.signal, "--execution-as-of", horizon)
    assert not errors
    for field in ("signal_as_of", "decision_time", "execution_date", "execution_time"):
        assert bt[field] == runner[field]
    assert all(day == runtime.signal for _, day in runtime.calls[:-1])
    assert runtime.calls[-1][1] == runtime.execution
    assert instance.store.load_latest_positions_snapshot().as_of == pd.Timestamp(runtime.execution)
    positions = tmp_path / "synthetic-paper.csv"
    positions.write_text("symbol,weight\nAAA,0.75\nBBB,0.25\n", encoding="utf-8")
    artifact = build_paper_run_artifact(context, result, portfolio_file=positions)
    assert artifact["decision_confirmed"] is True
    assert artifact["decision_status"] == "confirmed"
    assert artifact["previous_positions"] == {"AAA": 0.75, "BBB": 0.25}
    expected = {} if liquidate else {"AAA": 1.0}
    assert artifact["target_positions"] == runner["new_weights"] == expected
    assert [item["ticker"] for item in artifact["buy_proposals"]] == ([] if liquidate else ["AAA"])
    assert [item["ticker"] for item in artifact["sell_proposals"]] == (
        ["AAA", "BBB"] if liquidate else ["BBB"]
    )


def test_missing_execution_quote_does_not_confirm_or_replace_positions(runtime, paper_workflow):
    context, run, instance, previous_bytes = paper_workflow
    (result,), errors = run(missing_price=True)
    assert "MISSING_OR_INVALID_EXECUTION_PRICE" in errors[0]
    assert not runtime.bundles(context.aktien_oop_dir, "RUN")
    assert instance.store.positions_path.read_bytes() == previous_bytes
    assert runtime.calls[-1][1] == runtime.execution
    artifact = build_paper_run_artifact(context, result)
    assert artifact["decision_confirmed"] is False
    assert artifact["execution_date"] == runtime.execution
    assert artifact["target_positions"] is None
    assert artifact["buy_proposals"] == artifact["sell_proposals"] == []


def test_repeat_does_not_confirm_or_report_stale_same_signal_bundle(runtime, paper_workflow):
    context, run, instance, _ = paper_workflow
    (first, retry), errors = run(attempts=2)
    assert not errors
    assert len(runtime.bundles(context.aktien_oop_dir, "RUN")) == 1
    assert not retry.compare.success
    assert instance.store.load_latest_positions_snapshot().as_of == pd.Timestamp(runtime.execution)
    assert build_paper_run_artifact(context, first)["decision_confirmed"] is True
    repeated = build_paper_run_artifact(context, retry)
    assert repeated["decision_confirmed"] is False
    assert repeated["decision_bundle"] is None
    assert repeated["target_positions"] is None
    assert repeated["buy_proposals"] == repeated["sell_proposals"] == []


@pytest.mark.parametrize(("malformed", "status"), [
    (None, "missing_bundle"),
    ({"new_weights": {"AAA": "NaN"}}, "invalid_bundle"),
    ({"positions": [{"ticker": "AAA"}]}, "invalid_bundle"),
    ({}, "invalid_bundle"),
    ({"new_weights": {}, "decision_confirmed": False}, "unconfirmed_bundle"),
    ({"new_weights": {}, "as_of": "2025-07-10"}, "invalid_bundle"),
])
def test_missing_or_invalid_bundle_is_not_an_empty_target(
    tmp_path, paper_workflow, malformed, status,
):
    context, run, _, _ = paper_workflow
    (result,), _ = run()
    # Isolate the report boundary from the valid bundle already verified in the other tests.
    bundle = context.decisions_dir / "RUN_synthetic_2025-07-03.json"
    if malformed is not None:
        bundle.write_text(json.dumps({"as_of": "2025-07-03", **malformed}), encoding="utf-8")
    result = replace(
        result, runner_execution_date=None, runner_decision_paths=(bundle,) if malformed is not None else (),
    )
    positions = tmp_path / "synthetic-paper.csv"
    positions.write_text("symbol,weight\nAAA,1.0\n", encoding="utf-8")
    artifact = build_paper_run_artifact(context, result, portfolio_file=positions)
    assert artifact["decision_status"] == status
    assert artifact["decision_confirmed"] is False
    assert artifact["previous_positions"] == {"AAA": 1.0}
    assert artifact["target_positions"] is None
    assert artifact["buy_proposals"] == artifact["sell_proposals"] == []


def test_runner_explicit_signal_and_horizon_take_precedence(tmp_path: Path):
    inputs = RunRunnerToolInput(
        ("run", "--as-of=2025-06-27", "--execution-as-of", "2025-06-30"),
        tmp_path / "runner.toml", as_of_override="2025-07-03",
        execution_as_of_override="2025-07-07",
    )
    assert RunRunnerTool._build_command(inputs) == inputs.command
    different_signal = replace(inputs, command=("run", "--as-of=2025-06-27"))
    assert RunRunnerTool._build_command(different_signal) == different_signal.command



def test_configured_execution_cutoff_is_not_extended_by_backtest(runtime, paper_workflow):
    context, run, _, _ = paper_workflow
    (result,), errors = run(configured_horizon="2025-07-07T21:00:00Z")
    assert not errors
    assert result.runner.command[-2:] == ("--as-of", runtime.signal)
    assert build_paper_run_artifact(context, result)["decision_status"] == "pending"


def test_stale_backtest_bundle_cannot_supply_execution_horizon(runtime, paper_workflow):
    context, run, _, _ = paper_workflow
    runtime.tester(context.aktien_oop_dir, runtime.execution).run()
    (result,), errors = run(skip_backtest=True)
    assert not errors
    assert result.runner.command[-2:] == ("--as-of", runtime.signal)
    assert build_paper_run_artifact(context, result)["decision_status"] == "pending"

def test_explicit_signal_runs_once_in_multi_point_profile(runtime, paper_workflow):
    context, run, _, _ = paper_workflow
    context.decisions_dir.mkdir(parents=True)
    (context.decisions_dir / "BT_other_2025-06-27.json").write_text(
        json.dumps({"as_of": "2025-06-27", "new_weights": {}}), encoding="utf-8",
    )
    (result,), errors = run(explicit_signal=runtime.signal)
    assert not errors
    assert result.runner.message == "Runner executed 1 compare point(s)"
    assert len(runtime.bundles(context.aktien_oop_dir, "RUN")) == 1
    assert build_paper_run_artifact(context, result)["decision_confirmed"] is True



def test_paper_cli_does_not_seed_over_confirmed_previous_positions(
    runtime, tmp_path, paper_workflow, monkeypatch,
):
    import scripts.run_bt_run_agent as cli

    context, _, instance, previous_bytes = paper_workflow
    earlier = instance.store.snapshots_path.read_bytes()
    horizon = "2025-07-07T21:00:00Z"
    config = context.runner_config_path
    config.write_text(
        f"save_dir = {json.dumps(str(context.aktien_oop_dir))}\n"
        f"[core]\nexecution_as_of = {json.dumps(horizon)}\n",
        encoding="utf-8",
    )

    def in_process(_self, command, *, cwd=None, timeout_seconds=None):
        if "aktien_oop.main" not in command:
            runtime.tester(context.aktien_oop_dir, runtime.execution).run()
            earlier_bt = {
                "as_of": "2025-06-27",
                "execution_date": "2025-06-30",
                "execution_status": "validated_model_close",
                "new_weights": {"BBB": 1.0},
            }
            (context.decisions_dir / "BT_earlier_2025-06-27.json").write_text(
                json.dumps(earlier_bt), encoding="utf-8",
            )
        else:
            runtime.runner(
                context.aktien_oop_dir, runner_option(command, "--as-of"),
                available=runner_option(command, "--execution-as-of") or horizon,
            ).run()
        return ProcessResult(command, 0, "", "", str(cwd), 0.0)

    monkeypatch.setattr(SubprocessRunner, "run", in_process)
    monkeypatch.setattr(cli, "build_run_context", lambda *_: context)
    monkeypatch.setattr(cli.sys, "argv", [
        "run_bt_run_agent.py", "--profile", "short", "--runner-mode", "paper",
        "--start", "2025-06-30", "--end", runtime.execution,
    ])
    cli.main()

    assert instance.store.positions_path.read_bytes() == previous_bytes
    assert instance.store.snapshots_path.read_bytes() == earlier
    report = json.loads((context.output_dir / "paper_run_report.json").read_text(encoding="utf-8"))
    assert report["decision_status"] == "pending"
    assert report["previous_positions"] == {"AAA": 1.0}
    assert report["decision_confirmed"] is False
    assert report["target_positions"] is None
    assert report["buy_proposals"] == report["sell_proposals"] == []



def test_first_confirmed_target_without_previous_positions_has_no_weight_deltas(
    paper_workflow,
):
    context, run, instance, _ = paper_workflow
    instance.store.positions_path.unlink()
    instance.store.snapshots_path.unlink()
    (result,), errors = run()
    assert not errors
    artifact = build_paper_run_artifact(context, result)
    assert artifact["decision_confirmed"] is True
    assert artifact["target_positions"] == {"AAA": 1.0}
    assert artifact["previous_positions"] is None
    assert artifact["buy_proposals"] == artifact["sell_proposals"] == artifact["hold_proposals"] == []


def test_invalid_confirmed_timing_evidence_cannot_produce_a_proposal(paper_workflow):
    context, run, _, _ = paper_workflow
    (result,), _ = run()
    path, = result.runner_decision_paths
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["decision_time"] = payload["execution_time"]
    payload["configuration_evidence"]["runtime"]["decision_time"] = payload["decision_time"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    artifact = build_paper_run_artifact(context, result)
    assert artifact["decision_status"] == "invalid_bundle"
    assert artifact["target_positions"] is None
    assert artifact["sell_proposals"] == artifact["buy_proposals"] == []



@pytest.mark.parametrize("invalid_bundle", [
    ["not a JSON object"],
    {"as_of": "2025-07-03", "new_weights": {"AAA": "invalid"}},
])
def test_corrupt_runner_bundle_does_not_prevent_paper_diagnostics(paper_workflow, invalid_bundle):
    context, run, instance, previous_bytes = paper_workflow
    (result,), errors = run(invalid_bundle=invalid_bundle)
    assert not errors
    assert result.runner.success and not result.compare.success
    assert "decision bundles" in result.compare.message
    artifact = build_paper_run_artifact(context, result)
    report = json.loads(write_paper_run_report(context, artifact).read_text(encoding="utf-8"))
    assert report["decision_confirmed"] is False
    assert report["decision_status"] == "invalid_bundle"
    assert report["target_positions"] is None
    assert report["buy_proposals"] == report["sell_proposals"] == []
    assert instance.store.positions_path.read_bytes() == previous_bytes

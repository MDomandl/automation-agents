"""M1.20: real I/O paths with frozen synthetic inputs, never market downloads."""

from __future__ import annotations

import importlib
import logging
import os
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from app.application.bt_run.previous_state import RunnerPreviousSeedRequest
from app.infrastructure.storage.portfolio_store_previous_state_seeder import (
    PortfolioStorePreviousStateSeeder,
)
from tests.unit.scripts.test_strategy_profile_regime_exposure_contract import (
    regime_contract as regime_contract,
)
from tests.unit.scripts.test_strategy_profile_regime_exposure_contract import (
    synthetic_run as synthetic_run,
)
from tests.unit.scripts.test_strategy_profile_regime_exposure_contract import (
    turnover_contract as turnover_contract,
)


@pytest.mark.parametrize("path_name", ["bt-close", "runner-ohlc", "runner-close", "gate"])
def test_real_cache_hit_is_offline(m1_isolation, monkeypatch, path_name):
    data = importlib.import_module("aktien_oop.data_client")
    bt = importlib.import_module("aktien_oop.backtest")
    dates = pd.bdate_range("2024-01-01", periods=260)
    close = pd.Series([100.0 + i * 0.1 for i in range(len(dates))], index=dates)
    calls = []

    def synthetic_download(symbol, **kwargs):
        calls.append(symbol)
        frame = pd.DataFrame({"Close": close, "High": close + 1, "Low": close - 1})
        if symbol == "^GSPC":
            return pd.concat({"Close": close.to_frame("^GSPC")}, axis=1)
        return frame

    blocked_download = data.yf.download
    monkeypatch.setattr(data.yf, "download", synthetic_download)
    client = data.DataClient(SimpleNamespace(period="800d"))
    as_of = str(dates[-1].date())
    functions = {
        "bt-close": lambda: bt.download_close(["AAA"], str(dates[0].date()), "2024-12-31"),
        "runner-ohlc": lambda: client.download_ohlc("AAA", as_of=as_of, period="360d"),
        "runner-close": lambda: client.get_prices(["AAA"], as_of, "360d", True),
        "gate": lambda: client.sp500_above_200dma(as_of, period="360d"),
    }
    first = functions[path_name]()  # Real cache STORE, using only an in-memory supplier.
    assert calls
    assert list((m1_isolation.root / "market-cache").glob("*.pkl"))
    calls.clear()
    monkeypatch.setattr(data.yf, "download", blocked_download)
    second = functions[path_name]()  # Actual HIT must never reach the supplier.
    if isinstance(first, pd.DataFrame):
        pd.testing.assert_frame_equal(first, second)
    else:
        assert first is second is True
    assert calls == []


def test_offline_cache_miss_blocks_download(m1_isolation):
    data = importlib.import_module("aktien_oop.data_client")
    client = data.DataClient(SimpleNamespace(period="800d"))
    with m1_isolation.expect_blocked("unexpected download"):
        client.download_ohlc("AAA", as_of="2024-12-27", period="360d")
    assert not list((m1_isolation.root / "market-cache").glob("*.pkl"))


@pytest.mark.parametrize("uri", [False, True], ids=["native-path", "sqlite-uri"])
def test_external_sqlite_is_rejected(m1_isolation, uri):
    path = m1_isolation.root.parent / "must-not-create.db"
    database = path.as_uri().replace("file:///", "file:") if uri else str(path)
    with m1_isolation.expect_blocked("external write|SQLite URI"):
        sqlite3.connect(database, uri=uri)
    assert not path.exists()


def test_local_and_memory_sqlite_are_permitted(m1_isolation):
    for database in (str(m1_isolation.root / "local.db"), ":memory:"):
        connection = sqlite3.connect(database)
        try:
            connection.execute("CREATE TABLE example (value INTEGER)")
            connection.execute("INSERT INTO example VALUES (7)")
            assert connection.execute("SELECT value FROM example").fetchone() == (7,)
        finally:
            connection.close()


def test_inherited_yfinance_caches_are_relocated_and_restored(tmp_path, request):
    # Deliberately initialize before requesting the guard, like an earlier test.
    cache = importlib.import_module("yfinance.cache")
    managers = [cache._TzDBManager, cache._CookieDBManager, cache._ISINDBManager]
    original = [(manager._cache_dir, manager._db) for manager in managers]

    def restored():
        assert [(manager._cache_dir, manager._db) for manager in managers] == original

    # Register before monkeypatch/m1 so this assertion runs after their teardown.
    request.addfinalizer(restored)
    monkeypatch = request.getfixturevalue("monkeypatch")
    inherited = tmp_path.parent / "inherited-yfinance"
    inherited.mkdir()
    sentinel = inherited / "do-not-touch.db"
    sentinel.write_bytes(b"untouched inherited cache")
    for manager in managers:
        monkeypatch.setattr(manager, "_cache_dir", str(inherited))
    guard = request.getfixturevalue("m1_isolation")
    values = (
        (cache.get_tz_cache(), "AAA", "Europe/Berlin"),
        (cache.get_cookie_cache(), "test", {"synthetic": "cookie"}),
        (cache.get_isin_cache(), "TEST-ISIN", "AAA"),
    )
    for instance, key, value in values:
        instance.store(key, value)
        found = instance.lookup(key)
        assert (found["cookie"] if isinstance(found, dict) else found) == value
    local = guard.root / "yfinance-cache"
    assert len(list(local.glob("*.db"))) == 3
    assert all(Path(manager._cache_dir) == local for manager in managers)
    assert sentinel.read_bytes() == b"untouched inherited cache"
    assert sorted(path.name for path in inherited.iterdir()) == ["do-not-touch.db"]


@pytest.mark.parametrize(
    "transport", ["dns", "reverse-dns", "tcp", "udp", "requests", "curl", "yfinance"]
)
def test_network_transports_fail_before_io(m1_isolation, transport):
    with m1_isolation.expect_blocked("network event|unexpected download"):
        if transport == "dns":
            socket.getaddrinfo("example.invalid", 443)
        elif transport == "reverse-dns":
            socket.getnameinfo(("192.0.2.1", 443), 0)
        elif transport == "tcp":
            with socket.socket() as connection:
                connection.connect(("127.0.0.1", 9))
        elif transport == "udp":
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
                connection.sendto(b"blocked", ("127.0.0.1", 9))
        elif transport == "requests":
            importlib.import_module("requests").get("https://example.invalid")
        elif transport == "curl":
            importlib.import_module("curl_cffi.requests").get("https://example.invalid")
        else:
            importlib.import_module("yfinance").download("AAA")


@pytest.mark.parametrize("operation", ["write", "append", "remove", "replace", "cache", "read"])
def test_protected_paths_reject_io(m1_isolation, operation):
    ai = Path(os.environ["AI_AGENTS_ROOT"])
    original = ai / "aktien_oop/backtest_config.toml"
    before = original.read_bytes()
    with m1_isolation.expect_blocked("external write|external cache|protected data read"):
        if operation == "write":
            original.write_text("must not write", encoding="utf-8")
        elif operation == "append":
            with original.open("a", encoding="utf-8") as stream:
                stream.write("must not append")
        elif operation == "remove":
            original.unlink()
        elif operation == "replace":
            source = m1_isolation.root / "replacement.toml"
            source.write_text("must not replace", encoding="utf-8")
            source.replace(original)
        elif operation == "cache":
            cache = importlib.import_module("aktien_oop.market_data_cache")
            cache.MarketDataCache(ai / "aktien_oop/data_cache/market_data")
        else:
            (ai / "aktien_oop/portfolio_positions.csv").read_bytes()
    assert original.read_bytes() == before


def test_real_writer_and_seeder_paths_are_contained(m1_isolation):
    root = m1_isolation.root
    bt = importlib.import_module("aktien_oop.backtest")
    runner = importlib.import_module("aktien_oop.runner")
    store = importlib.import_module("aktien_oop.store")
    debug = root / "aktien_oop/debug"
    debug.mkdir(parents=True)
    runner._write_runner_friction_debug(
        debug_dir=debug,
        as_of_str="2024-12-27",
        prev_weights={},
        final_weights={"AAA": 1.0},
        friction_eps=0.0,
    )
    bt._to_csv_with_runid(root / "reports/report.csv", pd.DataFrame({"value": [1]}), run_id="M1")
    handler = logging.FileHandler(root / "m1.log", encoding="utf-8")
    try:
        handler.emit(logging.LogRecord("M1", logging.INFO, __file__, 1, "isolated", (), None))
    finally:
        handler.close()
    decisions = root / "decisions"
    bt._bt_write_decision_bundle("BT", decisions, "2024-12-26", {"AAA": 1.0}, run_id="M1")
    bt_config, run_config = root / "bt.toml", root / "runner.toml"
    bt_config.write_text(
        'save_dir="backtest"\nfrequency="monthly"\ntop_k=1\nbuffer_k=0\n',
        encoding="utf-8",
    )
    run_config.write_text('save_dir="runner"\n', encoding="utf-8")
    # Real store and real seeder; the seeder's TemporaryDirectory must also stay here.
    result = PortfolioStorePreviousStateSeeder().seed(
        RunnerPreviousSeedRequest(
            backtest_config_path=bt_config,
            backtest_cwd=root,
            runner_config_path=run_config,
            runner_cwd=root,
            runner_as_of="2024-12-27",
            decisions_dir=decisions,
        )
    )
    assert result.seeded, result.message
    snapshot = store.PortfolioStore(root / "runner").load_positions_snapshot_before("2024-12-27")
    assert snapshot.positions["ticker"].tolist() == ["AAA"]
    assert (root / "runner/portfolio_snapshots.csv").is_file()
    assert (debug / "RUN_friction_2024-12-27.csv").is_file()
    assert (root / "reports/report.csv").is_file()
    assert "isolated" in (root / "m1.log").read_text(encoding="utf-8")
    assert any(path.is_relative_to(root / "tmp") for path in m1_isolation.writes)
    assert all(path.is_relative_to(root) for path in m1_isolation.writes)


def test_two_fresh_production_runs_are_deterministic(m1_isolation, synthetic_run):
    first = synthetic_run("balanced_v1", output_root=m1_isolation.root / "first")
    second = synthetic_run("balanced_v1", output_root=m1_isolation.root / "second")
    for field in ("positions", "trades", "equity"):
        pd.testing.assert_frame_equal(getattr(first, field), getattr(second, field))
    for key in ("as_of", "old_weights", "new_weights", "turnover_raw", "turnover_eff"):
        assert first.bundle[key] == second.bundle[key]
    assert first.runner_weights == second.runner_weights
    assert all(path.is_relative_to(m1_isolation.root) for path in m1_isolation.writes)
    for folder in ("first", "second"):
        # The characterization's 800d request exceeds its 320-row synthetic supply;
        # existing validation may decline to STORE it. HIT behavior is tested above.
        assert m1_isolation.root / folder / "market-cache" in m1_isolation.caches
        assert list((m1_isolation.root / folder / "runner/decisions").glob("RUN_*.json"))
        assert list((m1_isolation.root / folder / "backtest/decisions").glob("BT_*.json"))


@pytest.mark.parametrize("fail", [False, True], ids=["success", "caught-failure"])
def test_guarded_child_preserves_files_on_success_and_failure(tmp_path, fail):
    """An outer test checks actual pytest failure/teardown, including swallowed errors."""
    repo = Path(__file__).resolve().parents[3]
    sentinel = tmp_path / "protected.toml"
    sentinel.write_bytes(b"original config\n")
    child = tmp_path / "test_child.py"
    child.write_text(
        'pytest_plugins = ["tests.unit.scripts.m1_isolation"]\n'
        "def test_guard(m1_isolation):\n"
        "    from pathlib import Path\n"
        "    (m1_isolation.root / 'inside.txt').write_text('ok')\n"
        + (
            "    try:\n"
            f"        Path({str(sentinel)!r}).write_text('forbidden')\n"
            "    except BaseException:\n"
            "        pass  # Deliberately swallowed: teardown must still fail.\n"
            if fail
            else ""
        ),
        encoding="utf-8",
    )
    env = dict(
        os.environ,
        PYTHONPATH=str(repo),
        PYTHONDONTWRITEBYTECODE="1",
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
    )
    # No M1 guard is active in this parent; the only child is this explicit offline pytest.
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            str(child),
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(tmp_path / "child-temp"),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == (1 if fail else 0), result.stdout + result.stderr
    if fail:
        assert "unacknowledged M1 isolation violation" in result.stdout
    assert sentinel.read_bytes() == b"original config\n"
    assert not list(tmp_path.glob("**/*.pkl"))

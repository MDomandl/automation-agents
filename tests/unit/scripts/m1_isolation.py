"""Opt-in, in-process guard for synthetic M1 tests; not an OS security sandbox.

No calculation is replaced here. CPython audit events guard tested filesystem,
SQLite, socket and process paths; native HTTP transports are blocked separately.

Supported: scoped cash/turnover/regime contracts, matrix helper unit tests and
test_m1_isolation, including real Runner/Backtester/Store/Seeder with synthetic
inputs. Run Python 3.11.9 with -B, -p no:cacheprovider and a fresh --basetemp.
Set AI_AGENTS_ROOT to the companion checkout; no dependency installation needed.

Not approved: production CLIs, run_bt_run_agent orchestration, matrix/batch main
functions, live/paper runs, tests without this fixture, parallel tests/threads or
arbitrary native I/O/pre-opened external handles. The guard starts in fixture
setup, not during pytest collection; it is not an OS or hostile-code sandbox.
"""

from __future__ import annotations

import importlib
import os
import platform
import re
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import pytest

_active = None
_installed = False


class IsolationViolation(BaseException):
    """Unexpected I/O; also recorded so a production catch cannot hide it."""


@dataclass
class M1Sandbox:
    root: Path
    protected_data: tuple[Path, ...]
    violations: list[str] = field(default_factory=list)
    writes: set[Path] = field(default_factory=set)
    caches: set[Path] = field(default_factory=set)

    def inside(self, value):
        return Path(value).resolve().is_relative_to(self.root)

    def block(self, message):
        self.violations.append(message)
        raise IsolationViolation(message)

    def require_inside(self, value, purpose):
        if not self.inside(value):
            self.block(f"M1 isolation: external {purpose}: {value}")
        return Path(value).resolve()

    @contextmanager
    def expect_blocked(self, pattern):
        """Acknowledge exactly one deliberately tested guard rejection."""
        start = len(self.violations)
        with pytest.raises(IsolationViolation, match=pattern):
            yield
        recorded = self.violations[start:]
        assert len(recorded) == 1 and re.search(pattern, recorded[0])
        del self.violations[start:]

    def check_path(self, value, *, write=False):
        # fdopen uses an existing descriptor; mkstemp/open were already checked.
        if isinstance(value, int) or value is None:
            return
        path = Path(os.fsdecode(value)).resolve()
        if write:
            self.require_inside(path, "write")
            self.writes.add(path)
        elif not self.inside(path) and any(
            path == parent or path.is_relative_to(parent) for parent in self.protected_data
        ):
            self.block(f"M1 isolation: protected data read: {path}")


def _audit(event, args):
    guard = _active
    if guard is None:
        return
    # Local hostname lookup and urllib3's loopback bind capability probe send no data.
    if event in {
        "socket.connect",
        "socket.getaddrinfo",
        "socket.gethostbyname",
        "socket.gethostbyaddr",
        "socket.getnameinfo",
        "socket.sendto",
        "socket.sendmsg",
    }:
        guard.block(f"M1 isolation: network event {event}")
    if event in {
        "subprocess.Popen",
        "os.system",
        "os.exec",
        "os.posix_spawn",
        "os.spawn",
    }:
        guard.block(f"M1 isolation: process event {event}")
    if event == "sqlite3.connect":
        database = os.fsdecode(args[0])
        if database.startswith("file:"):
            guard.block("M1 isolation: SQLite URI not permitted")
        if database != ":memory:":
            guard.check_path(database, write=True)
    elif event == "open":
        path, mode, flags = args
        write = bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        guard.check_path(path, write=write)
    elif event in {"os.rename", "os.link", "os.symlink"}:
        for path in args[:2]:
            guard.check_path(path, write=True)
        if any(fd not in (-1, None) for fd in args[2:]):
            guard.block("M1 isolation: relative directory descriptor")
    elif event in {
        "os.remove",
        "os.rmdir",
        "os.mkdir",
        "os.chmod",
        "os.truncate",
        "os.utime",
    }:
        # Relevant calls use ordinary paths, not dir_fd-relative paths.
        if event in {"os.remove", "os.rmdir"} and args[-1] not in (-1, None):
            guard.block("M1 isolation: relative directory descriptor")
        guard.check_path(args[0], write=True)
    elif event == "os.chdir":
        guard.require_inside(args[0], "working directory")


@pytest.fixture
def m1_isolation(monkeypatch, tmp_path):
    """Activate before importing the real companion calculation modules."""
    global _active, _installed
    ai_value = os.environ.get("AI_AGENTS_ROOT")
    if not ai_value:
        pytest.skip("M1 integration isolation requires AI_AGENTS_ROOT")
    ai = Path(ai_value).resolve()
    repo = Path(__file__).resolve().parents[3]
    root = tmp_path.resolve()
    data_roots = [
        ai / "aktien_oop" / name for name in ("data_cache", "debug", "decisions", "dumps")
    ] + [repo / name for name in ("data", "portfolios", "reports", "aktien_oop")]
    data_roots += list((ai / "aktien_oop").glob("*.csv"))
    protected = [
        ai / "aktien_oop/backtest_config.toml",
        ai / "aktien_oop/configs/runner_config.toml",
        *sorted((repo / "configs/profiles").glob("*.toml")),
    ]
    before = {path: path.read_bytes() for path in protected}
    guard = M1Sandbox(root, tuple(path.resolve() for path in data_roots))
    for name in ("tmp", "market-cache", "home", "cache", "appdata", "localappdata"):
        (root / name).mkdir()
    monkeypatch.chdir(root)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setattr(tempfile, "tempdir", str(root / "tmp"))
    for key, value in {
        "AKTIEN_OOP_MARKET_CACHE_DIR": root / "market-cache",
        "TMP": root / "tmp",
        "TEMP": root / "tmp",
        "TMPDIR": root / "tmp",
        "HOME": root / "home",
        "USERPROFILE": root / "home",
        "XDG_CACHE_HOME": root / "cache",
        "APPDATA": root / "appdata",
        "LOCALAPPDATA": root / "localappdata",
    }.items():
        monkeypatch.setenv(key, str(value))
    monkeypatch.syspath_prepend(str(ai))
    # Cache stdlib OS metadata before the guard: on Windows a cold platform()
    # query invokes the read-only `ver` command. Production subprocesses stay blocked.
    platform.platform()
    if not _installed:
        sys.addaudithook(_audit)
        _installed = True
    assert _active is None, "M1 guards cannot be nested"
    _active = guard
    local_databases = []
    try:
        # Existing matrix helpers resolve profiles relative to cwd. Supply byte-
        # identical copies there rather than restoring a repository cwd.
        profile_dir = root / "configs/profiles"
        profile_dir.mkdir(parents=True)
        for source in sorted((repo / "configs/profiles").glob("*.toml")):
            (profile_dir / source.name).write_bytes(source.read_bytes())

        def forbidden_download(*args, **kwargs):
            guard.block("M1 isolation: unexpected download/HTTP request")

        # yfinance uses curl_cffi, which can bypass Python's socket audit events.
        yf = importlib.import_module("yfinance")
        monkeypatch.setattr(yf, "download", forbidden_download)
        # These managers retain import-time paths and handles across tests. Keep
        # any old objects untouched and restore them through monkeypatch teardown.
        yf_cache = importlib.import_module("yfinance.cache")
        cache_specs = (
            ("_TzDBManager", "_TzCacheManager", "_tz_cache", "tz_db_proxy"),
            ("_CookieDBManager", "_CookieCacheManager", "_Cookie_cache", "Cookie_db_proxy"),
            ("_ISINDBManager", "_ISINCacheManager", "_isin_cache", "isin_db_proxy"),
        )
        for db_name, manager_name, cache_attr, proxy_name in cache_specs:
            db_manager = getattr(yf_cache, db_name)
            monkeypatch.setattr(db_manager, "_db", None)
            monkeypatch.setattr(db_manager, "_cache_dir", str(root / "yfinance-cache"))
            monkeypatch.setattr(getattr(yf_cache, manager_name), cache_attr, None)
            monkeypatch.setattr(getattr(yf_cache, proxy_name), "obj", None)
            local_databases.append(db_manager)
        for module_name in ("requests.sessions", "curl_cffi.requests"):
            module = importlib.import_module(module_name)
            monkeypatch.setattr(module.Session, "request", forbidden_download)
            if hasattr(module, "AsyncSession"):
                monkeypatch.setattr(module.AsyncSession, "request", forbidden_download)

        cache = importlib.import_module("aktien_oop.market_data_cache")
        assert Path(cache.__file__).resolve() == ai / "aktien_oop/market_data_cache.py"
        original_init = cache.MarketDataCache.__init__
        original_path = cache.MarketDataCache.cache_path

        def cache_init(instance, cache_dir=None):
            resolved = cache_dir if cache_dir is not None else cache.default_cache_dir()
            guard.require_inside(resolved, "cache")
            guard.caches.add(Path(resolved).resolve())
            original_init(instance, resolved)

        def cache_path(instance, request):
            path = original_path(instance, request)
            guard.require_inside(path, "cache")
            return path

        monkeypatch.setattr(cache.MarketDataCache, "__init__", cache_init)
        monkeypatch.setattr(cache.MarketDataCache, "cache_path", cache_path)
        yield guard
    finally:
        try:
            for manager in local_databases:
                manager.close_db()
        finally:
            _active = None
        assert {path: path.read_bytes() for path in protected} == before
        if guard.violations:
            pytest.fail("unacknowledged M1 isolation violation(s): " + "; ".join(guard.violations))

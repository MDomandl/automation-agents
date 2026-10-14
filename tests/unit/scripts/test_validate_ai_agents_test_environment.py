import sys
from pathlib import Path
from subprocess import CompletedProcess
from types import ModuleType

import pytest

from scripts.validate_ai_agents_test_environment import (
    EXPECTED_AI_AGENTS_REVISION,
    EnvironmentValidationError,
    import_ai_agents_module,
    import_portfolio_store_module,
    validate_ai_agents_revision,
    validate_ai_agents_root,
    validate_portfolio_store_contract,
    validate_python_version,
)


def make_ai_agents_root(root: Path) -> Path:
    package = root / "aktien_oop"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "core_calc.py").write_text("MARKER = 'core'\n", encoding="utf-8")
    (package / "store.py").write_text(
        "class PositionSnapshot: pass\n"
        "class PortfolioStore:\n"
        "    def save_positions(self, frame, *, snapshot_as_of=None): pass\n"
        "    def load_positions_snapshot_before(self, as_of): pass\n",
        encoding="utf-8",
    )
    return root


def git_runner(*, revision: str = EXPECTED_AI_AGENTS_REVISION, status: str = ""):
    def run(command, **kwargs):
        stdout = revision if command[-2:] == ["rev-parse", "HEAD"] else status
        return CompletedProcess(command, 0, stdout=stdout, stderr="")

    return run


def test_python_version_requires_exactly_3_11() -> None:
    validate_python_version((3, 11, 9))

    with pytest.raises(EnvironmentValidationError, match="Python 3.11 is required"):
        validate_python_version((3, 12, 0))


def test_ai_agents_root_must_be_absolute(tmp_path: Path) -> None:
    with pytest.raises(EnvironmentValidationError, match="must be an absolute path"):
        validate_ai_agents_root(Path("relative"))


def test_ai_agents_root_requires_expected_structure(tmp_path: Path) -> None:
    with pytest.raises(EnvironmentValidationError, match=r"aktien_oop[/\\]store.py"):
        validate_ai_agents_root(tmp_path)


def test_ai_agents_root_must_exist(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(EnvironmentValidationError, match="is not a directory"):
        validate_ai_agents_root(missing)


def test_revision_accepts_expected_clean_worktree(tmp_path: Path) -> None:
    root = make_ai_agents_root(tmp_path / "source")
    (root / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")

    assert validate_ai_agents_revision(root, runner=git_runner()) == EXPECTED_AI_AGENTS_REVISION


def test_revision_uses_only_scoped_non_writing_git_queries(tmp_path: Path) -> None:
    root = make_ai_agents_root(tmp_path / "source")
    (root / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    calls = []

    def recording_runner(command, **kwargs):
        calls.append((command, kwargs))
        stdout = EXPECTED_AI_AGENTS_REVISION if command[-2:] == ["rev-parse", "HEAD"] else ""
        return CompletedProcess(command, 0, stdout=stdout, stderr="")

    validate_ai_agents_revision(root, runner=recording_runner)

    common = ["git", "-c", f"safe.directory={root.resolve()}", "-C", str(root.resolve())]
    assert [command for command, _ in calls] == [
        [*common, "rev-parse", "HEAD"],
        [*common, "status", "--porcelain=v1", "--untracked-files=all"],
    ]
    assert all(kwargs["check"] is False for _, kwargs in calls)
    assert all(kwargs["capture_output"] is True for _, kwargs in calls)
    assert all(kwargs["text"] is True for _, kwargs in calls)
    assert all(kwargs["env"]["GIT_OPTIONAL_LOCKS"] == "0" for _, kwargs in calls)
    assert all("safe.directory" not in kwargs["env"] for _, kwargs in calls)


def test_revision_rejects_wrong_commit(tmp_path: Path) -> None:
    root = make_ai_agents_root(tmp_path / "source")
    (root / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")

    with pytest.raises(EnvironmentValidationError, match="revision mismatch"):
        validate_ai_agents_revision(root, runner=git_runner(revision="0" * 40))


def test_revision_rejects_dirty_worktree(tmp_path: Path) -> None:
    root = make_ai_agents_root(tmp_path / "source")
    (root / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")

    with pytest.raises(EnvironmentValidationError, match="clean worktree"):
        validate_ai_agents_revision(root, runner=git_runner(status=" M aktien_oop/store.py"))


def test_import_rejects_module_loaded_from_another_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_root = make_ai_agents_root(tmp_path / "expected")
    wrong_store = tmp_path / "wrong" / "aktien_oop" / "store.py"
    wrong_store.parent.mkdir(parents=True)
    wrong_store.write_text("class PortfolioStore: pass\n", encoding="utf-8")
    wrong_module = ModuleType("aktien_oop.store")
    wrong_module.__file__ = str(wrong_store)
    wrong_module.PortfolioStore = object
    monkeypatch.setitem(sys.modules, "aktien_oop.store", wrong_module)

    with pytest.raises(EnvironmentValidationError, match="unexpected origin"):
        import_portfolio_store_module(expected_root)


def test_import_accepts_module_from_validated_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_ai_agents_root(tmp_path / "source")
    monkeypatch.delitem(sys.modules, "aktien_oop.store", raising=False)
    monkeypatch.delitem(sys.modules, "aktien_oop", raising=False)

    try:
        module = import_portfolio_store_module(root)

        assert Path(module.__file__).resolve() == (root / "aktien_oop" / "store.py").resolve()
        assert module.PortfolioStore.__name__ == "PortfolioStore"
        assert not (root / "aktien_oop" / "__pycache__").exists()
    finally:
        sys.modules.pop("aktien_oop.store", None)
        sys.modules.pop("aktien_oop", None)


def test_portfolio_store_contract_accepts_snapshot_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_ai_agents_root(tmp_path / "source")
    monkeypatch.delitem(sys.modules, "aktien_oop.store", raising=False)
    monkeypatch.delitem(sys.modules, "aktien_oop", raising=False)

    validate_portfolio_store_contract(import_portfolio_store_module(root))


def test_portfolio_store_contract_rejects_missing_snapshot_parameter() -> None:
    module = ModuleType("aktien_oop.store")

    class PositionSnapshot:
        pass

    class PortfolioStore:
        def save_positions(self, frame):
            pass

        def load_positions_snapshot_before(self, as_of):
            pass

    module.PositionSnapshot = PositionSnapshot
    module.PortfolioStore = PortfolioStore

    with pytest.raises(EnvironmentValidationError, match="must accept snapshot_as_of"):
        validate_portfolio_store_contract(module)


def test_portfolio_store_contract_rejects_missing_snapshot_loader() -> None:
    module = ModuleType("aktien_oop.store")

    class PositionSnapshot:
        pass

    class PortfolioStore:
        def save_positions(self, frame, *, snapshot_as_of=None):
            pass

    module.PositionSnapshot = PositionSnapshot
    module.PortfolioStore = PortfolioStore

    with pytest.raises(EnvironmentValidationError, match="load_positions_snapshot_before"):
        validate_portfolio_store_contract(module)


def test_repeated_imports_do_not_leak_modules_or_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_root = make_ai_agents_root(tmp_path / "first")
    second_root = make_ai_agents_root(tmp_path / "second")
    monkeypatch.delitem(sys.modules, "aktien_oop.store", raising=False)
    monkeypatch.delitem(sys.modules, "aktien_oop", raising=False)
    original_path = sys.path.copy()

    first = import_ai_agents_module(first_root, "aktien_oop.store")
    second = import_ai_agents_module(second_root, "aktien_oop.store")

    assert Path(first.__file__).resolve() == first_root / "aktien_oop" / "store.py"
    assert Path(second.__file__).resolve() == second_root / "aktien_oop" / "store.py"
    assert "aktien_oop" not in sys.modules
    assert "aktien_oop.store" not in sys.modules
    assert sys.path == original_path


def test_generic_import_loads_core_calc_from_expected_origin_without_state_leaks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = make_ai_agents_root(tmp_path / "source")
    monkeypatch.delitem(sys.modules, "aktien_oop.core_calc", raising=False)
    monkeypatch.delitem(sys.modules, "aktien_oop", raising=False)
    original_path = sys.path.copy()

    module = import_ai_agents_module(root, "aktien_oop.core_calc")

    assert Path(module.__file__).resolve() == root / "aktien_oop" / "core_calc.py"
    assert module.MARKER == "core"
    assert "aktien_oop" not in sys.modules
    assert "aktien_oop.core_calc" not in sys.modules
    assert sys.path == original_path
    assert not (root / "aktien_oop" / "__pycache__").exists()

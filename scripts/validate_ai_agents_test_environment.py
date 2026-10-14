"""Validate the explicit AiAgents source checkout used by integration tests."""

from __future__ import annotations

import argparse
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import inspect
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence

EXPECTED_PYTHON = (3, 11)
EXPECTED_AI_AGENTS_REVISION = "f5626a3b3ddb51651577ae7735af5133ed4ee712"
REQUIRED_PATHS = (
    Path("aktien_oop") / "__init__.py",
    Path("aktien_oop") / "store.py",
)


class EnvironmentValidationError(RuntimeError):
    """Raised when the integration-test environment is not trustworthy."""


class _SourceOnlyLoader(importlib.machinery.SourceFileLoader):
    """Compile the declared source file without consulting bytecode caches."""

    def get_code(self, fullname: str) -> object:
        source_path = self.get_filename(fullname)
        source = self.get_data(source_path)
        return self.source_to_code(source, source_path)


class _AiAgentsSourceFinder(importlib.abc.MetaPathFinder):
    """Resolve only aktien_oop sources below one validated root."""

    def __init__(self, root: Path):
        self._package_root = root / "aktien_oop"

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "aktien_oop":
            relative_parts: tuple[str, ...] = ()
        elif fullname.startswith("aktien_oop."):
            relative_parts = tuple(fullname.split(".")[1:])
        else:
            return None

        candidate = self._package_root.joinpath(*relative_parts)
        package_source = candidate / "__init__.py"
        module_source = candidate.with_suffix(".py")
        if package_source.is_file():
            loader = _SourceOnlyLoader(fullname, str(package_source))
            return importlib.util.spec_from_file_location(
                fullname,
                package_source,
                loader=loader,
                submodule_search_locations=[str(candidate)],
            )
        if module_source.is_file():
            loader = _SourceOnlyLoader(fullname, str(module_source))
            return importlib.util.spec_from_file_location(
                fullname,
                module_source,
                loader=loader,
            )
        raise ModuleNotFoundError(
            f"{fullname} has no source file below {self._package_root}"
        )


def validate_python_version(version_info: Sequence[int] = sys.version_info) -> None:
    actual = tuple(version_info[:2])
    if actual != EXPECTED_PYTHON:
        raise EnvironmentValidationError(
            f"Python {EXPECTED_PYTHON[0]}.{EXPECTED_PYTHON[1]} is required; "
            f"found {actual[0]}.{actual[1]}"
        )


def validate_ai_agents_root(value: str | Path) -> Path:
    root = Path(value)
    if not root.is_absolute():
        raise EnvironmentValidationError("AI_AGENTS_ROOT must be an absolute path")
    if not root.is_dir():
        raise EnvironmentValidationError(f"AI_AGENTS_ROOT is not a directory: {root}")

    resolved_root = root.resolve()
    missing = [str(path) for path in REQUIRED_PATHS if not (resolved_root / path).is_file()]
    if missing:
        raise EnvironmentValidationError(
            "AI_AGENTS_ROOT is missing required files: " + ", ".join(missing)
        )
    return resolved_root


def validate_ai_agents_revision(
    ai_agents_root: str | Path,
    *,
    runner: object = subprocess.run,
) -> str:
    root = validate_ai_agents_root(ai_agents_root)
    if not (root / ".git").exists():
        raise EnvironmentValidationError("AI_AGENTS_ROOT is not a Git worktree")

    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    common = ["git", "-c", f"safe.directory={root}", "-C", str(root)]

    def run_git(*arguments: str) -> str:
        result = runner(
            [*common, *arguments],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
            raise EnvironmentValidationError(f"could not inspect AI_AGENTS_ROOT: {detail}")
        return result.stdout.strip()

    revision = run_git("rev-parse", "HEAD")
    if revision != EXPECTED_AI_AGENTS_REVISION:
        raise EnvironmentValidationError(
            "AI_AGENTS_ROOT revision mismatch: "
            f"expected {EXPECTED_AI_AGENTS_REVISION}, found {revision}"
        )

    dirty = run_git("status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise EnvironmentValidationError(
            "AI_AGENTS_ROOT must be a clean worktree; Git reported local changes"
        )
    return revision


def import_portfolio_store_module(ai_agents_root: str | Path) -> ModuleType:
    module = import_ai_agents_module(ai_agents_root, "aktien_oop.store")
    if not hasattr(module, "PortfolioStore"):
        raise EnvironmentValidationError("aktien_oop.store does not define PortfolioStore")
    return module


def validate_portfolio_store_contract(module: ModuleType) -> None:
    portfolio_store = getattr(module, "PortfolioStore", None)
    if not inspect.isclass(portfolio_store):
        raise EnvironmentValidationError("aktien_oop.store does not define PortfolioStore")

    save_positions = getattr(portfolio_store, "save_positions", None)
    if not callable(save_positions):
        raise EnvironmentValidationError("PortfolioStore.save_positions is required")
    snapshot_parameter = inspect.signature(save_positions).parameters.get("snapshot_as_of")
    if snapshot_parameter is None or snapshot_parameter.kind not in (
        inspect.Parameter.KEYWORD_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    ):
        raise EnvironmentValidationError("PortfolioStore.save_positions must accept snapshot_as_of")

    if not callable(getattr(portfolio_store, "load_positions_snapshot_before", None)):
        raise EnvironmentValidationError(
            "PortfolioStore.load_positions_snapshot_before is required"
        )
    if not inspect.isclass(getattr(module, "PositionSnapshot", None)):
        raise EnvironmentValidationError("aktien_oop.store.PositionSnapshot is required")


def import_ai_agents_module(ai_agents_root: str | Path, module_name: str) -> ModuleType:
    root = validate_ai_agents_root(ai_agents_root)
    if not module_name.startswith("aktien_oop."):
        raise EnvironmentValidationError(f"unsupported AiAgents module: {module_name}")

    expected_module_origin = root.joinpath(*module_name.split(".")).with_suffix(".py").resolve()
    if not expected_module_origin.is_file():
        raise EnvironmentValidationError(
            f"AI_AGENTS_ROOT does not contain required module: {expected_module_origin}"
        )

    original_sys_path = sys.path.copy()
    original_meta_path = sys.meta_path.copy()
    original_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "aktien_oop" or name.startswith("aktien_oop.")
    }
    for name, module in original_modules.items():
        _validate_import_origin(module, _expected_source_path(root, name), name)
    for name in original_modules:
        sys.modules.pop(name, None)

    sys.meta_path.insert(0, _AiAgentsSourceFinder(root))
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        importlib.invalidate_caches()
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            raise EnvironmentValidationError(f"could not import {module_name}: {exc}") from exc
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
        sys.path[:] = original_sys_path
        sys.meta_path[:] = original_meta_path
        for name in tuple(sys.modules):
            if name == "aktien_oop" or name.startswith("aktien_oop."):
                sys.modules.pop(name, None)
        sys.modules.update(original_modules)

    _validate_import_origin(module, expected_module_origin, module_name)
    return module


def _expected_source_path(root: Path, module_name: str) -> Path:
    if module_name == "aktien_oop":
        return (root / "aktien_oop" / "__init__.py").resolve()
    relative = module_name.split(".")[1:]
    candidate = root.joinpath("aktien_oop", *relative)
    package_source = candidate / "__init__.py"
    if package_source.is_file():
        return package_source.resolve()
    module_source = candidate.with_suffix(".py")
    if module_source.is_file():
        return module_source.resolve()
    raise EnvironmentValidationError(
        f"cached {module_name} has no matching source below {root / 'aktien_oop'}"
    )


def _validate_import_origin(module: ModuleType, expected: Path, name: str) -> None:
    origin = getattr(module, "__file__", None)
    if origin is None or Path(origin).resolve() != expected:
        raise EnvironmentValidationError(
            f"{name} was imported from an unexpected origin: expected {expected}, found {origin}"
        )


def audit_test_environment(ai_agents_root: str | Path) -> Path:
    validate_python_version()
    root = validate_ai_agents_root(ai_agents_root)
    validate_ai_agents_revision(root)
    store_module = import_portfolio_store_module(root)
    validate_portfolio_store_contract(store_module)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ai-agents-root",
        required=True,
        help="Explicit absolute path to the read-only AiAgents checkout",
    )
    args = parser.parse_args(argv)
    try:
        root = audit_test_environment(args.ai_agents_root)
    except EnvironmentValidationError as exc:
        parser.error(str(exc))
    print(f"validated AI_AGENTS_ROOT={root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

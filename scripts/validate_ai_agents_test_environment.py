"""Validate the explicit AiAgents source checkout used by integration tests."""

from __future__ import annotations

import argparse
import importlib
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

    root_text = str(root)
    expected_package_origin = (root / "aktien_oop" / "__init__.py").resolve()
    expected_module_origin = root.joinpath(*module_name.split(".")).with_suffix(".py").resolve()
    if not expected_module_origin.is_file():
        raise EnvironmentValidationError(
            f"AI_AGENTS_ROOT does not contain required module: {expected_module_origin}"
        )

    cached_package = sys.modules.get("aktien_oop")
    if cached_package is not None:
        _validate_import_origin(cached_package, expected_package_origin, "aktien_oop")
    cached_module = sys.modules.get(module_name)
    if cached_module is not None:
        _validate_import_origin(cached_module, expected_module_origin, module_name)

    original_sys_path = sys.path.copy()
    original_modules = {
        name: module
        for name, module in sys.modules.items()
        if name == "aktien_oop" or name.startswith("aktien_oop.")
    }
    sys.path.insert(0, root_text)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        importlib.invalidate_caches()
        spec = importlib.util.find_spec(module_name)
        origin = None if spec is None else spec.origin
        if origin is None or Path(origin).resolve() != expected_module_origin:
            raise EnvironmentValidationError(
                f"{module_name} resolved to an unexpected origin before import: "
                f"expected {expected_module_origin}, found {origin}"
            )
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            raise EnvironmentValidationError(f"could not import {module_name}: {exc}") from exc
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
        sys.path[:] = original_sys_path
        for name in tuple(sys.modules):
            if name == "aktien_oop" or name.startswith("aktien_oop."):
                sys.modules.pop(name, None)
        sys.modules.update(original_modules)

    _validate_import_origin(module, expected_module_origin, module_name)
    return module


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

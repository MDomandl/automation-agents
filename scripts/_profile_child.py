from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any, Callable


class RuntimeProbe:
    def __init__(self) -> None:
        self.phase_seconds: dict[str, float] = defaultdict(float)
        self.call_counts: dict[str, int] = defaultdict(int)
        self.price_shapes: list[dict[str, Any]] = []

    def wrap(self, owner: object, attr: str, phase: str, label: str | None = None) -> None:
        descriptor = inspect.getattr_static(owner, attr, None)
        original = getattr(owner, attr, None)
        if descriptor is None or original is None or getattr(original, "_runtime_probe_wrapped", False):
            return
        is_staticmethod = isinstance(descriptor, staticmethod)
        is_classmethod = isinstance(descriptor, classmethod)
        if is_staticmethod or is_classmethod:
            original = descriptor.__func__
        if not callable(original):
            return

        metric_name = label or attr

        def measured(*args: Any, **kwargs: Any) -> Any:
            started_at = perf_counter()
            try:
                result = original(*args, **kwargs)
                if phase == "data_loading":
                    self._record_price_shape(metric_name, result)
                return result
            finally:
                elapsed = perf_counter() - started_at
                self.phase_seconds[phase] += elapsed
                self.call_counts[metric_name] += 1

        setattr(measured, "_runtime_probe_wrapped", True)
        if is_staticmethod:
            setattr(owner, attr, staticmethod(measured))
        elif is_classmethod:
            setattr(owner, attr, classmethod(measured))
        else:
            setattr(owner, attr, measured)

    def _record_price_shape(self, source: str, result: Any) -> None:
        shape = getattr(result, "shape", None)
        if not shape or len(shape) < 2:
            return
        rows = int(shape[0])
        cols = int(shape[1])
        self.price_shapes.append({"source": source, "rows": rows, "columns": cols})

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "phase_seconds": dict(sorted(self.phase_seconds.items())),
                    "call_counts": dict(sorted(self.call_counts.items())),
                    "price_shapes": self.price_shapes,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    parser.add_argument("--metrics-out", required=True)
    parser.add_argument("module_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if args.module_args and args.module_args[0] == "--":
        args.module_args = args.module_args[1:]
    return args


def _patch_if_available(probe: RuntimeProbe, module_name: str, patches: tuple[tuple[str, str, str], ...]) -> None:
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return
    for attr, phase, label in patches:
        probe.wrap(module, attr, phase, label)


def install_probe(module_name: str, probe: RuntimeProbe) -> None:
    _patch_if_available(
        probe,
        "aktien_oop.core_calc",
        (
            ("slice_to_window", "scoring", "core_calc.slice_to_window"),
            ("compute_scores", "scoring", "core_calc.compute_scores"),
            ("apply_filters", "scoring", "core_calc.apply_filters"),
            ("select_topk", "scoring", "core_calc.select_topk"),
            ("select_topk_buffer", "scoring", "core_calc.select_topk_buffer"),
            ("_dump_selection", "report_decision_bundles", "core_calc._dump_selection"),
            ("_dump_weights", "report_decision_bundles", "core_calc._dump_weights"),
        ),
    )
    _patch_if_available(
        probe,
        "aktien_oop.backtest",
        (
            ("download_close", "data_loading", "backtest.download_close"),
            ("_bt_write_decision_bundle", "report_decision_bundles", "backtest._bt_write_decision_bundle"),
            ("_to_csv_with_runid", "finalization", "backtest._to_csv_with_runid"),
        ),
    )
    _patch_if_available(
        probe,
        "aktien_oop.runner",
        (
            ("_write_runner_friction_debug", "report_decision_bundles", "runner._write_runner_friction_debug"),
        ),
    )

    try:
        data_client = importlib.import_module("aktien_oop.data_client")
        cls = getattr(data_client, "DataClient", None)
        if cls is not None:
            for attr in ("get_prices", "regime_decision", "sp500_above_200dma"):
                phase = "benchmark" if attr in {"regime_decision", "sp500_above_200dma"} else "data_loading"
                probe.wrap(cls, attr, phase, f"DataClient.{attr}")
    except Exception:
        pass

    try:
        store = importlib.import_module("aktien_oop.store")
        cls = getattr(store, "PortfolioStore", None)
        if cls is not None:
            for attr in (
                "load_positions_before",
                "load_positions",
                "save_positions",
                "last_rebalance_time",
                "append_run",
                "append_csv",
                "write_positions",
                "append_jsonl",
            ):
                probe.wrap(cls, attr, "report_decision_bundles", f"PortfolioStore.{attr}")
    except Exception:
        pass

    if module_name == "aktien_oop.main":
        # Importing aktien_oop.main pulls Runner into the module; patch its class-level methods too.
        try:
            runner = importlib.import_module("aktien_oop.runner")
            cls = getattr(runner, "Runner", None)
            if cls is not None:
                probe.wrap(cls, "_write_decision_bundle", "report_decision_bundles", "Runner._write_decision_bundle")
                probe.wrap(cls, "_should_rebalance", "rebalance_loop", "Runner._should_rebalance")
        except Exception:
            pass


def main() -> None:
    args = parse_args(sys.argv[1:])
    metrics_out = Path(args.metrics_out)
    probe = RuntimeProbe()
    old_argv = sys.argv[:]
    try:
        module = importlib.import_module(args.module)
        install_probe(args.module, probe)
        sys.argv = [args.module, *args.module_args]
        main_func = getattr(module, "main", None)
        if not callable(main_func):
            raise RuntimeError(f"Module {args.module!r} has no callable main()")
        main_func()
    finally:
        sys.argv = old_argv
        probe.write(metrics_out)


if __name__ == "__main__":
    main()

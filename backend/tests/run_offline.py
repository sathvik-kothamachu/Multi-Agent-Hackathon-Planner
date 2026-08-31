"""Offline test runner (stdlib only) — verifies the pure-logic pytest suites
without needing pytest installed. On the user's machine, prefer `pytest`.

Usage: python -m tests.run_offline   (from the backend/ directory)
"""
from __future__ import annotations

import importlib
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_MODULES = [
    "tests.test_similarity",
    "tests.test_routing",
    "tests.test_persona_logic",
    "tests.test_merge",
    "tests.test_compare",
    "tests.test_flow_simulation",
]


def run() -> int:
    passed = failed = 0
    failures: list[str] = []
    for mod_name in TEST_MODULES:
        mod = importlib.import_module(mod_name)
        fns = sorted(
            n for n in dir(mod) if n.startswith("test_") and callable(getattr(mod, n))
        )
        for fn_name in fns:
            try:
                getattr(mod, fn_name)()
                passed += 1
            except Exception:  # noqa: BLE001 - report any failure
                failed += 1
                failures.append(f"{mod_name}.{fn_name}\n{traceback.format_exc()}")
    print(f"\n{passed} passed, {failed} failed")
    for f in failures:
        print("\nFAILED " + f)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())

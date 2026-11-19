#!/usr/bin/env python3
# ============================================================
# tests/run_all_tests.py
# Wild Shield Karnataka — Test Runner
#
# Run all tests and display a formatted summary report.
# Usage:
#   python tests/run_all_tests.py
#
# Returns exit code 0 if all tests pass, 1 if any fail.
# ============================================================

import sys
import os
import unittest
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run_suite(name: str, module_path: str) -> tuple[int, int, list[str]]:
    """
    Load and run a test module.
    Returns (passed, failed, failure_messages).
    """
    loader = unittest.TestLoader()
    suite = loader.discover(
        os.path.dirname(__file__),
        pattern=os.path.basename(module_path),
    )
    runner = unittest.TextTestRunner(
        verbosity=0,
        stream=open(os.devnull, "w"),  # Suppress output — we format it ourselves
    )
    result = runner.run(suite)

    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    messages = []
    for test, traceback in result.failures + result.errors:
        messages.append(f"  FAIL: {test}\n{_extract_error(traceback)}")
    return passed, failed, messages


def _extract_error(traceback: str) -> str:
    """Extract the most relevant error line from a traceback."""
    lines = traceback.strip().split("\n")
    # Get the AssertionError line
    for line in reversed(lines):
        line = line.strip()
        if line.startswith("AssertionError") or line.startswith("Error"):
            return f"       {line}"
    return f"       {lines[-1]}"


def main():
    print("\n" + "=" * 65)
    print("  🐘 WILD SHIELD KARNATAKA — Test Suite")
    print("=" * 65)

    test_suites = [
        ("Agent 1 — Risk Assessment", "test_agent1.py"),
        ("Agent 2 — Safety Advisor", "test_agent2.py"),
        ("Orchestrator — Full Pipeline", "test_orchestrator.py"),
        ("Utils — Helper Functions", "test_utils.py"),
    ]

    total_passed = 0
    total_failed = 0
    all_failures = []
    suite_results = []

    for suite_name, pattern in test_suites:
        print(f"\n  Running: {suite_name}...")
        start = time.time()

        loader = unittest.TestLoader()
        suite = loader.discover(
            os.path.dirname(os.path.abspath(__file__)),
            pattern=pattern,
        )

        # Count tests first
        test_count = suite.countTestCases()

        # Run with capturing
        import io
        stream = io.StringIO()
        runner = unittest.TextTestRunner(verbosity=2, stream=stream)
        result = runner.run(suite)
        elapsed = time.time() - start

        passed = result.testsRun - len(result.failures) - len(result.errors)
        failed = len(result.failures) + len(result.errors)
        total_passed += passed
        total_failed += failed

        status = "✅ PASS" if failed == 0 else "❌ FAIL"
        print(f"  {status}  {passed}/{result.testsRun} tests passed  ({elapsed:.2f}s)")

        # Collect failure details
        for test, traceback in result.failures + result.errors:
            msg = f"  → FAIL in {suite_name}: {test}\n"
            lines = traceback.strip().split("\n")
            for line in reversed(lines):
                line = line.strip()
                if line and (line.startswith("AssertionError") or "Error:" in line):
                    msg += f"    {line}\n"
                    break
            all_failures.append(msg)

        suite_results.append((suite_name, passed, result.testsRun, failed, elapsed))

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  📊 RESULTS SUMMARY")
    print("=" * 65)

    for suite_name, passed, total, failed, elapsed in suite_results:
        icon = "✅" if failed == 0 else "❌"
        bar_filled = int((passed / total) * 20) if total > 0 else 0
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        print(f"  {icon}  {suite_name:<35} {passed:>3}/{total:<3} [{bar}]")

    print("-" * 65)
    grand_total = total_passed + total_failed
    pct = (total_passed / grand_total * 100) if grand_total > 0 else 0
    print(f"  TOTAL:  {total_passed}/{grand_total} tests passed ({pct:.0f}%)")

    if all_failures:
        print(f"\n  ❌ {len(all_failures)} FAILURE(S):")
        for msg in all_failures:
            print(msg)

    print("=" * 65)

    if total_failed == 0:
        print("  ✅ ALL TESTS PASSED — Wild Shield Karnataka is ready.")
    else:
        print(f"  ❌ {total_failed} TEST(S) FAILED — See failures above.")

    print("=" * 65 + "\n")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

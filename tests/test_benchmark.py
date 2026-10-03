#!/usr/bin/env python3
"""Smoke tests for tools/benchmark.py — stdlib only.

Guards two things that matter for docs/EFFICIENCY.md:
  * the benchmark runs and emits both markdown and JSON
  * the generator's measured candidate count matches the closed-form formula
    (the same assertion the benchmark makes internally), so the published
    scaling numbers can't silently drift from the code.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BENCH = REPO / "tools" / "benchmark.py"


def run(*args):
    proc = subprocess.run([sys.executable, str(BENCH), *args], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


class Benchmark(unittest.TestCase):
    def test_markdown_runs(self):
        code, out, err = run("--repeats", "1")
        self.assertEqual(code, 0, err)
        self.assertIn("Generator scaling (measured)", out)
        self.assertIn("Budget", out)

    def test_json_runs_and_matches_formula(self):
        code, out, err = run("--json", "--repeats", "1")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertIn("scaling", data)
        self.assertIn("coverage", data)
        # Re-derive the closed form here and check each measured row agrees.
        for row in data["scaling"]:
            v, a, p = row["vectors_per_path"], row["attackers_per_path"], row["paths"]
            expected = p * (5 * v * a + v * (v - 1))
            self.assertEqual(row["candidates"], expected,
                             f"candidate count drifted from formula for {row}")

    def test_coverage_prioritizes_base_first(self):
        _, out, _ = run("--json", "--repeats", "1")
        rows = json.loads(out)["coverage"]["rows"]
        smallest = min(rows, key=lambda r: r["budget_N"])
        # The smallest budget must be spent entirely on base (highest-severity) timelines.
        self.assertEqual(smallest["mutation"], 0)
        self.assertEqual(smallest["chain"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

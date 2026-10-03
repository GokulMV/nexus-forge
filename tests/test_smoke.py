#!/usr/bin/env python3
"""Smoke tests for the Nexus Forge scripts.

Stdlib only (unittest + subprocess), so this runs anywhere Python 3.8+ is present
with no install step. It exercises the two scripts the way the skill does:

    surface.json --generate_timelines--> ranked timelines (JSON)
    verdicts.json ----------forge------> report (Markdown)

Run from the repo root:

    python3 -m unittest discover -s tests -v
    # or
    python3 tests/test_smoke.py
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "nexus-forge" / "scripts"
EXAMPLES = REPO / "examples"
GEN = SCRIPTS / "generate_timelines.py"
FORGE = SCRIPTS / "forge.py"
SURFACE = EXAMPLES / "surface.example.json"
VERDICTS = EXAMPLES / "verdicts.example.json"


def run(*args):
    """Run a script and return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        [sys.executable, *map(str, args)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


class FixturesExist(unittest.TestCase):
    def test_paths_present(self):
        for p in (GEN, FORGE, SURFACE, VERDICTS):
            self.assertTrue(p.exists(), f"missing fixture: {p}")


class GenerateTimelines(unittest.TestCase):
    def test_schema_flag(self):
        code, out, err = run(GEN, "--schema")
        self.assertEqual(code, 0, err)
        self.assertIn("surface map", out)

    def test_selects_requested_count(self):
        code, out, err = run(GEN, SURFACE, "--count", "6")
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["selected_count"], 6)
        self.assertEqual(len(data["selected"]), 6)
        # overflow + selected accounts for every enumerated candidate
        self.assertEqual(
            data["total_candidates"], len(data["selected"]) + len(data["overflow"])
        )

    def test_ranking_is_deterministic(self):
        _, a, _ = run(GEN, SURFACE, "--count", "12")
        _, b, _ = run(GEN, SURFACE, "--count", "12")
        self.assertEqual(a, b, "generation must be deterministic for the same input")

    def test_highest_severity_first(self):
        code, out, _ = run(GEN, SURFACE, "--count", "exhaustive")
        self.assertEqual(code, 0)
        scores = [s["score"] for s in json.loads(out)["selected"]]
        self.assertEqual(scores, sorted(scores, reverse=True),
                         "selected timelines must be ranked by score descending")

    def test_bad_count_errors_cleanly(self):
        code, _, err = run(GEN, SURFACE, "--count", "not-a-number")
        self.assertNotEqual(code, 0)
        self.assertIn("integer", err.lower())


class Forge(unittest.TestCase):
    def test_schema_flag(self):
        code, out, err = run(FORGE, "--schema")
        self.assertEqual(code, 0, err)
        self.assertIn("input JSON shape", out)

    def test_renders_all_sections(self):
        code, out, err = run(FORGE, VERDICTS)
        self.assertEqual(code, 0, err)
        for heading in (
            "# Nexus Forge report",
            "## 1. Engagement scope",
            "## 2. Surface map",
            "## 3. Timeline matrix",
            "## 4. Nexus findings",
            "## 5. Antibodies",
            "## 6. Hardening timeline",
            "## 7. Residual & assumptions",
        ):
            self.assertIn(heading, out, f"report missing section: {heading}")

    def test_findings_sorted_critical_first(self):
        _, out, _ = run(FORGE, VERDICTS)
        # F2 is Critical, F1/F3 are High -> F2's finding block must come first.
        self.assertLess(
            out.index("### F2:"), out.index("### F1:"),
            "findings must be ordered most-severe first",
        )

    def test_missing_file_errors_cleanly(self):
        code, _, err = run(FORGE, EXAMPLES / "does-not-exist.json")
        self.assertNotEqual(code, 0)
        self.assertIn("not found", err.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)

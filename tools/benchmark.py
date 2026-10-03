#!/usr/bin/env python3
"""benchmark.py — measure the efficiency characteristics of the Nexus Forge generator.

This produces the numbers used in docs/EFFICIENCY.md. It is reproducible and stdlib-only:
it imports `enumerate_timelines` from the skill's generator and measures, on synthetic
surfaces of increasing size:

  * candidate count  (how many timelines the generator enumerates)
  * wall-clock        (median over repeated runs)
  * throughput        (candidates / second)

...and, on the shipped example surface, how the selected set's composition
(base / mutation / chain) shifts as the budget N grows.

Run from the repo root:

    python3 tools/benchmark.py            # human-readable markdown
    python3 tools/benchmark.py --json     # machine-readable

No randomness is involved, so counts are identical run to run; only timings vary.
"""

import argparse
import importlib.util
import json
import statistics
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GEN_PATH = REPO / "nexus-forge" / "scripts" / "generate_timelines.py"
EXAMPLE_SURFACE = REPO / "examples" / "surface.example.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_timelines", GEN_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GEN = load_generator()

# Per the generator's logic, a path with V vectors and A attackers yields
#   5*V*A   base+mutation timelines  (1 base + 4 mutations per vector-attacker pair)
# + V*(V-1) two-step chains
# This closed form lets EFFICIENCY.md state scaling exactly, not approximately.
def predicted(n_paths, vectors, attackers):
    per_path = 5 * vectors * attackers + vectors * (vectors - 1)
    return n_paths * per_path


def make_surface(n_paths, vectors_per_path, attackers_per_path):
    attackers = [f"attacker-{i}" for i in range(attackers_per_path)]
    assets = [{"name": f"asset-{i}", "value": "high"} for i in range(n_paths)]
    paths = []
    for p in range(n_paths):
        paths.append({
            "entry": f"/api/endpoint-{p}",
            "asset": f"asset-{p}",
            "boundary": "auth required",
            "vectors": [f"vector-{v}" for v in range(vectors_per_path)],
            "attackers": attackers,
            "reachability": "high",
        })
    return {"attackers": attackers, "assets": assets, "paths": paths}


def time_enumerate(surface, repeats):
    samples = []
    count = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        scenarios = GEN.enumerate_timelines(surface)
        samples.append(time.perf_counter() - t0)
        count = len(scenarios)
    return count, statistics.median(samples)


def scaling_rows(repeats):
    # (paths, vectors/path, attackers/path) — from a tiny service to a large surface.
    shapes = [
        (3, 2, 3),
        (5, 3, 4),
        (10, 4, 5),
        (25, 5, 5),
        (50, 6, 5),
        (100, 6, 6),
    ]
    rows = []
    for n_paths, vectors, attackers in shapes:
        surface = make_surface(n_paths, vectors, attackers)
        count, median_s = time_enumerate(surface, repeats)
        assert count == predicted(n_paths, vectors, attackers), "formula/behavior drift"
        ms = median_s * 1000.0
        rows.append({
            "paths": n_paths,
            "vectors_per_path": vectors,
            "attackers_per_path": attackers,
            "candidates": count,
            "median_ms": round(ms, 3),
            "throughput_per_s": int(count / median_s) if median_s else None,
        })
    return rows


def composition(scenarios):
    out = {"base": 0, "mutation": 0, "chain": 0}
    for s in scenarios:
        out[s["kind"]] = out.get(s["kind"], 0) + 1
    return out


def coverage_rows():
    surface = json.loads(EXAMPLE_SURFACE.read_text(encoding="utf-8"))
    scenarios = GEN.enumerate_timelines(surface)
    total = len(scenarios)
    rows = []
    for n in (6, 12, 25, 50, total):
        selected = scenarios[:n]
        comp = composition(selected)
        rows.append({
            "budget_N": n,
            "selected": len(selected),
            "pct_of_space": round(100.0 * len(selected) / total, 1),
            "base": comp["base"],
            "mutation": comp["mutation"],
            "chain": comp["chain"],
        })
    return {"total_candidates": total, "full_composition": composition(scenarios), "rows": rows}


def md_table(headers, rows):
    line = "| " + " | ".join(headers) + " |"
    sep = "|" + "---|" * len(headers)
    body = "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)
    return "\n".join([line, sep, body])


def main():
    ap = argparse.ArgumentParser(description="Benchmark the Nexus Forge generator.")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of markdown.")
    ap.add_argument("--repeats", type=int, default=15, help="Timing samples per shape (median reported).")
    args = ap.parse_args()

    scaling = scaling_rows(args.repeats)
    coverage = coverage_rows()

    if args.json:
        print(json.dumps({"scaling": scaling, "coverage": coverage}, indent=2))
        return

    print("## Generator scaling (measured)\n")
    print(md_table(
        ["Paths", "Vectors/path", "Attackers/path", "Candidates", "Median time", "Throughput"],
        [[r["paths"], r["vectors_per_path"], r["attackers_per_path"], f"{r['candidates']:,}",
          f"{r['median_ms']} ms", f"{r['throughput_per_s']:,}/s"] for r in scaling],
    ))
    print("\n## Budget -> coverage on the example surface (3 paths)\n")
    c = coverage
    print(f"Full space: **{c['total_candidates']} candidates** "
          f"({c['full_composition']['base']} base, {c['full_composition']['mutation']} mutation, "
          f"{c['full_composition']['chain']} chain).\n")
    print(md_table(
        ["Budget N", "Selected", "% of space", "base", "mutation", "chain"],
        [[r["budget_N"], r["selected"], f"{r['pct_of_space']}%", r["base"], r["mutation"], r["chain"]]
         for r in c["rows"]],
    ))


if __name__ == "__main__":
    main()

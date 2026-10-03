#!/usr/bin/env python3
"""
generate_timelines.py — expand a target's surface map into a ranked list of attack timelines.

Standard library only. This is the generator behind the "user picks N timelines" dial: it takes the
Phase-1 surface map and a budget N, enumerates the combinatorial space (attacker × vector × path,
plus mutations and two-step chains), ranks candidates, and returns the top N as JSON — plus the
overflow, so a later run with a bigger N resumes instead of restarting.

It does NOT decide verdicts. It lays out *which* timelines to reason through; you run each against
the real code in Phase 3 and record outcomes with forge.py.

Usage:
    python3 generate_timelines.py surface.json --count 6
    python3 generate_timelines.py surface.json --count exhaustive -o timelines.json
    python3 generate_timelines.py --schema

Input (surface.json) — every field optional; sensible defaults fill gaps:
{
  "attackers": ["Script-based opportunist","Known-vuln exploiter","Insider",
                "Adaptive AI adversary","Supply-chain attacker"],
  "assets": [{"name":"user table (PII)","value":"high"}, {"name":"payments","value":"critical"}],
  "paths": [
    {
      "entry": "GET /api/users",
      "asset": "user table (PII)",
      "boundary": "auth required",
      "vectors": ["rate-limit / quota evasion","IDOR"],          // vectors the code here is exposed to
      "attackers": ["Adaptive AI adversary","Insider"],          // who can reach it (optional; else all)
      "reachability": "high"                                      // optional: high/medium/low
    }
  ]
}

Output: ranked scenarios with id, path, attacker, vector, kind (base|mutation|chain), a score, and
a one-line rationale; plus `selected` (top N) and `overflow` (the rest).
"""

import argparse
import json
import sys

DEFAULT_ATTACKERS = [
    "Script-based opportunist",
    "Known-vuln exploiter",
    "Insider",
    "Adaptive AI adversary",
    "Supply-chain attacker",
]
ASSET_VALUE = {"critical": 4, "high": 3, "medium": 2, "low": 1}
REACH_VALUE = {"high": 3, "medium": 2, "low": 1}
# Ranking is by severity (asset value × reachability). Kind orders ties only: a path's headline
# "base" attack leads, then its mutations, then its chains. So a small budget (N=6) spends itself on
# the obvious high-severity attacks, and as N grows the extra slots fill with the mutations and
# two-step chains — the combinations a checklist would miss. Novelty isn't a score boost; it's what
# naturally enters once the obvious scenarios are exhausted.
KIND_RANK = {"base": 0, "mutation": 1, "chain": 2}

# Default mutation families applied to any vector — the "adaptive attacker doesn't give up" set.
MUTATIONS = [
    ("re-encoded payload", "alternate encoding to slip a validator that checks the literal form"),
    ("boundary / fuzzed values", "edge values probing the one input the validator missed"),
    ("split under the limit", "request sliced to stay under a rate/quota threshold (the 'fetch N at a time' trick)"),
    ("rotated identity", "fresh device id / fingerprint / account to defeat client-side binding (VM/emulator)"),
]


def asset_value(name, asset_index):
    v = asset_index.get(name, "medium")
    return ASSET_VALUE.get(str(v).lower(), 2)


def reach_value(path):
    return REACH_VALUE.get(str(path.get("reachability", "medium")).lower(), 2)


def score(av, rv):
    return av * rv


def enumerate_timelines(surface):
    attackers_all = surface.get("attackers") or DEFAULT_ATTACKERS
    asset_index = {a["name"]: a.get("value", "medium")
                   for a in surface.get("assets", []) if isinstance(a, dict) and "name" in a}
    paths = surface.get("paths", [])

    scenarios = []
    seq = 0

    def add(path, attacker, vector, kind, note):
        nonlocal seq
        seq += 1
        av = asset_value(path.get("asset", ""), asset_index)
        rv = reach_value(path)
        scenarios.append({
            "id": f"T{seq:03d}",
            "entry": path.get("entry", "?"),
            "asset": path.get("asset", "?"),
            "boundary": path.get("boundary", ""),
            "attacker": attacker,
            "vector": vector,
            "kind": kind,
            "score": score(av, rv),
            "rationale": note,
        })

    for path in paths:
        vectors = path.get("vectors") or ["(unspecified — infer from code at this entry)"]
        attackers = path.get("attackers") or attackers_all
        for vector in vectors:
            for attacker in attackers:
                # base timeline
                add(path, attacker, vector, "base",
                    f"{attacker} drives {vector} at {path.get('entry','?')} toward {path.get('asset','?')}.")
                # mutations of this base
                for mname, mwhy in MUTATIONS:
                    add(path, attacker, f"{vector} + {mname}", "mutation",
                        f"If blocked, {attacker} tries {mname}: {mwhy}.")
            # two-step chains: this vector as step 1, every other vector on the same path as step 2
            for v2 in vectors:
                if v2 == vector:
                    continue
                add(path, "Adaptive AI adversary", f"{vector} → {v2}", "chain",
                    f"Chain: {vector} yields a foothold, then {v2} reaches {path.get('asset','?')}.")

    # stable, deterministic ranking: severity (score) desc, then base before mutation before chain
    # for ties, then id for full determinism.
    scenarios.sort(key=lambda s: (-s["score"], KIND_RANK.get(s["kind"], 9), s["id"]))
    return scenarios


def main():
    p = argparse.ArgumentParser(description="Generate a ranked timeline list from a surface map.")
    p.add_argument("surface", nargs="?", help="Path to surface.json")
    p.add_argument("--count", default="6",
                   help="How many timelines to select: an integer, or 'exhaustive' for all. Base/default 6.")
    p.add_argument("-o", "--out", help="Write JSON here instead of stdout.")
    p.add_argument("--schema", action="store_true", help="Print input schema + exit.")
    args = p.parse_args()

    if args.schema:
        print(__doc__)
        return
    if not args.surface:
        p.error("provide surface.json, or --schema")

    try:
        with open(args.surface, encoding="utf-8") as fh:
            surface = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"error: file not found: {args.surface}")
    except json.JSONDecodeError as e:
        sys.exit(f"error: invalid JSON: {e}")

    scenarios = enumerate_timelines(surface)
    total = len(scenarios)

    if str(args.count).lower() in ("exhaustive", "all", "max"):
        n = total
    else:
        try:
            n = max(1, int(args.count))
        except ValueError:
            sys.exit("error: --count must be an integer or 'exhaustive'")

    result = {
        "budget_requested": args.count,
        "total_candidates": total,
        "selected_count": min(n, total),
        "selected": scenarios[:n],
        "overflow": scenarios[n:],   # resume here when the user expands N later
    }

    payload = json.dumps(result, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload)
        print(f"wrote {args.out}: {result['selected_count']} selected / {total} candidates "
              f"({len(result['overflow'])} held in overflow)")
    else:
        print(payload)


if __name__ == "__main__":
    main()

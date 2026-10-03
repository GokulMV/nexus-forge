#!/usr/bin/env python3
"""
forge.py — assemble Nexus Forge verdicts into a heatmap + report.

Standard library only. You (Claude) supply the judgments as a JSON file; this script
formats them into the report structure in references/report-template.md so you don't
hand-align tables each run.

Usage:
    python3 forge.py verdicts.json                 # print report to stdout
    python3 forge.py verdicts.json -o report.md    # write to a file
    python3 forge.py --schema                       # print the input schema + a worked example

The input JSON shape (see --schema for a full example):

{
  "target": "my-service",
  "owner_confirmation": "user owns the repo",
  "mode": "analyze",
  "isolation": "N/A (analyze)",
  "covered": "...", "not_covered": "...",
  "surface": {"entry_points": [...], "trust_boundaries": [...], "assets": [...]},
  "nexus": [
    {
      "id": "F1",
      "title": "User table harvestable under client-side rate limit",
      "attacker": "Adaptive AI adversary",
      "vector": "rate-limit / quota evasion",
      "asset": "user table (PII)",
      "postures": {"block":"unknown","allow":"affected","tarpit":"unknown",
                   "detect_approve":"strong","deceive":"na","immune":"strong"},
      "strength": "affected",
      "severity": "High",
      "severity_note": "mass PII exposure x trivial for an agent",
      "ttc": "hours",
      "ttc_assumptions": "valid free-tier account; only barrier is a client-side '6 at a time' limit",
      "broke": "GET /api/users enforces the 6-item page size client-side only; server has no total quota.",
      "evidence": "Agent paginated 0..N offset under the limit; full table retrieved in ~40 min of wall-clock.",
      "recommended_posture": "detect_approve + server-side total quota",
      "antibody": {
        "fix": "Enforce per-identity total-row quota server-side; add anomaly alert on breadth of offsets.",
        "applied_to": "sandbox copy",
        "result": "neutralized",
        "mutations_tested": "fingerprint rotation, slower pagination, parallel identities",
        "new_nexus": "none",
        "status": "proposal for owner review"
      }
    }
  ]
}

Any field may be omitted; the renderer degrades gracefully.
"""

import argparse
import json
import sys

CELL = {
    "strong": "\U0001F7E2",     # green
    "affected": "\U0001F534",   # red
    "unknown": "\U0001F7E1",    # amber
    "na": "—",             # em dash
}
POSTURE_COLS = [
    ("block", "Block"),
    ("allow", "Allow"),
    ("tarpit", "Tarpit"),
    ("detect_approve", "Detect+Approve"),
    ("deceive", "Deceive"),
    ("immune", "Immune"),
]
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def cell(value):
    return CELL.get(str(value).strip().lower(), CELL["na"])


def bullets(items):
    if not items:
        return "- _(none recorded)_"
    return "\n".join(f"- {it}" for it in items)


def severity_rank(n):
    return SEVERITY_ORDER.get(str(n.get("severity", "")).strip().lower(), 9)


def render(data):
    out = []
    w = out.append

    target = data.get("target", "<unnamed target>")
    w(f"# Nexus Forge report — {target}\n")

    # 1. Scope
    w("## 1. Engagement scope")
    w(f"- **Target**: {target}")
    w(f"- **Owner confirmation**: {data.get('owner_confirmation', '_(confirm before relying on this report)_')}")
    w(f"- **Mode**: {data.get('mode', '<analyze|harness|live>')}")
    w(f"- **Isolation**: {data.get('isolation', '_(state for live/harness)_')}")
    w(f"- **Covered**: {data.get('covered', '_(describe)_')}")
    w(f"- **Not covered**: {data.get('not_covered', '_(describe)_')}\n")

    # 2. Surface
    surface = data.get("surface", {})
    w("## 2. Surface map")
    w("**Entry points**")
    w(bullets(surface.get("entry_points")))
    w("\n**Trust boundaries**")
    w(bullets(surface.get("trust_boundaries")))
    w("\n**Assets at risk**")
    w(bullets(surface.get("assets")))
    w("")

    nexus = data.get("nexus", [])

    # 3. Heatmap
    w("## 3. Timeline matrix (heatmap)")
    header = "| Attacker × Vector → Asset | " + " | ".join(c[1] for c in POSTURE_COLS) + " |"
    sep = "|" + "---|" * (len(POSTURE_COLS) + 1)
    w(header)
    w(sep)
    for n in nexus:
        label = f"{n.get('attacker','?')} × {n.get('vector','?')} → {n.get('asset','?')}"
        postures = n.get("postures", {})
        cells = " | ".join(cell(postures.get(key, "na")) for key, _ in POSTURE_COLS)
        w(f"| {label} | {cells} |")
    w("\nLegend: \U0001F7E2 held · \U0001F534 broke · \U0001F7E1 unknown · — not applicable.\n")

    # 4. Findings (severity order, affected/unknown first)
    w("## 4. Nexus findings")
    findings = [n for n in nexus if str(n.get("strength", "")).lower() in ("affected", "unknown")]
    findings.sort(key=severity_rank)
    if not findings:
        w("_No affected or unknown nexus points — every modeled timeline held. Re-check coverage in §7._\n")
    for n in findings:
        w(f"### {n.get('id','F?')}: {n.get('title','(untitled)')}")
        w(f"- **Path**: {n.get('attacker','?')} via {n.get('vector','?')} → {n.get('asset','?')}")
        w(f"- **Strength**: {n.get('strength','?')}")
        sev = n.get("severity", "?")
        sev_note = n.get("severity_note", "")
        w(f"- **Severity**: {sev}" + (f" — {sev_note}" if sev_note else ""))
        ttc = n.get("ttc", "?")
        w(f"- **Time-to-compromise**: {ttc} — *estimate*; assumptions: {n.get('ttc_assumptions','_(state them)_')}")
        w(f"- **What broke**: {n.get('broke','_(describe)_')}")
        w(f"- **Evidence**: {n.get('evidence','_(repro / request-response / logs)_')}")
        w(f"- **Recommended posture**: {n.get('recommended_posture','_(pick per references/response-branches.md)_')}\n")

    # 5. Antibodies
    w("## 5. Antibodies")
    any_ab = False
    for n in nexus:
        ab = n.get("antibody")
        if not ab:
            continue
        any_ab = True
        w(f"### {n.get('id','F?')} antibody")
        w(f"- **Fix**: {ab.get('fix','_(describe)_')}")
        w(f"- **Applied to**: {ab.get('applied_to','sandbox copy (never live)')}")
        w(f"- **Re-challenge result**: {ab.get('result','?')}")
        w(f"- **Mutations tested**: {ab.get('mutations_tested','_(list)_')}")
        w(f"- **New nexus opened**: {ab.get('new_nexus','none')}")
        w(f"- **Status**: {ab.get('status','proposal for owner review — not applied to any live system')}\n")
    if not any_ab:
        w("_No antibodies recorded yet. Run Phase 5 for each affected point._\n")

    # 6. Hardening timeline
    w("## 6. Hardening timeline (manageable assets)")
    custom = data.get("hardening")
    if custom:
        for band in ("now", "next", "later"):
            w(f"- **{band.capitalize()}**: {custom.get(band, '_(none)_')}")
    else:
        w("_Order the findings above by severity-per-effort into Now / Next / Later. "
          "Each item: the finding it closes, rough effort, and the approval it needs._")
    w("")

    # 7. Residual
    w("## 7. Residual & assumptions")
    residual = data.get("residual", {})
    w("**Still unknown**")
    w(bullets(residual.get("unknown")))
    w("\n**Assumptions behind TTC**")
    w(bullets(residual.get("assumptions")))
    w("\n**Caveat**: TTC figures are order-of-magnitude planning estimates, not guarantees; a "
      "determined or well-resourced attacker may move faster.")

    return "\n".join(out) + "\n"


SCHEMA_EXAMPLE = __doc__


def main():
    p = argparse.ArgumentParser(description="Render a Nexus Forge report from verdict JSON.")
    p.add_argument("verdicts", nargs="?", help="Path to the verdict JSON file.")
    p.add_argument("-o", "--out", help="Write report here instead of stdout.")
    p.add_argument("--schema", action="store_true", help="Print the input schema + example and exit.")
    args = p.parse_args()

    if args.schema:
        print(SCHEMA_EXAMPLE)
        return
    if not args.verdicts:
        p.error("provide a verdict JSON path, or --schema")

    try:
        with open(args.verdicts, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"error: file not found: {args.verdicts}")
    except json.JSONDecodeError as e:
        sys.exit(f"error: invalid JSON in {args.verdicts}: {e}")

    report = render(data)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        print(f"wrote {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()

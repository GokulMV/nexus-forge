# Architecture

Nexus Forge is a **Claude Code skill** plus two small, stdlib-only Python helpers. The skill is the
brain (it reads code, reasons through attacks, decides verdicts); the scripts are deterministic
scaffolding (they enumerate the scenario space and format the report) so the reasoning isn't spent
on bookkeeping.

## Mental model

A single request can branch into many **timelines** — one per `(attacker × vector × response)`
combination. Each timeline is run in a sandbox; the ones where the attack succeeds are **nexus
events**. The report shows where the code holds, where it breaks, and roughly how long each break
would take a real attacker. For every break, an **antibody** (a targeted fix) is proposed and
re-challenged with mutations to confirm it actually neutralizes the threat instead of displacing it.

Everything points **inward** — at a system the user owns or is authorized to test. See
[`../SECURITY.md`](../SECURITY.md) and the "Safety & scope" section of the skill.

## The three axes

| Axis | What it varies | Catalog |
|------|----------------|---------|
| **A — Attacker** | who is attacking and how they adapt | `nexus-forge/references/threat-actors.md` |
| **B — Vector** | the technique (injection, IDOR, rate-limit evasion, deserialization, SSRF, race, prompt injection, …) | derived from the target's code |
| **C — Response** | how the system reacts: Block / Allow / Tarpit / Detect+Approve / Deceive / Immune | `nexus-forge/references/response-branches.md` |

The axes are **generators, not a fixed checklist** — timelines are derived from the target's own
surface, so the combinations a developer never wrote down (mutations, two-step chains) surface on
their own as the budget grows.

## The five phases

```
1. Map        inventory entry points, trust boundaries, assets          -> surface.json
2. Branch     cross the axes into a ranked timeline matrix (budget N)    -> generate_timelines.py
3. Run        execute each timeline at the chosen depth (analyze/harness/live)
4. Surveil    score each nexus: strength / severity / time-to-compromise -> scoring.md
5. Immunize   propose an antibody per break, re-challenge with mutations -> verdicts.json
                                                                         -> forge.py -> report.md
```

## Run modes (depth)

- **`analyze`** — pure threat modeling; nothing is executed. Safe anywhere.
- **`harness`** — generate parameterized test artifacts for the owner to run against their own
  non-prod. See `nexus-forge/references/harness-guide.md`.
- **`live`** — run checks directly against an authorized non-prod target; start non-destructive,
  stop at proof.

## Data flow

```
          Phase 1 (Claude reads the code)
                      │
                      ▼
               surface.json ──────────────┐
                      │                    │
                      ▼                    │
   generate_timelines.py  --count N        │  deterministic enumeration + ranking
                      │                    │  (no verdicts decided here)
                      ▼                    │
              timelines.json               │
                      │                    │
     Phases 3–5 (Claude reasons through    │
     each timeline against the real code,  │
     records strength/severity/TTC and     │
     proposes + re-challenges antibodies)  │
                      │                    │
                      ▼                    │
               verdicts.json ◀─────────────┘
                      │
                      ▼
                 forge.py
                      │
                      ▼
       report.md  (scope, surface, heatmap,
       findings, antibodies, hardening plan,
       residual & assumptions)
```

## The two scripts

### `generate_timelines.py`
Expands a surface map + a budget `N` into a **ranked** scenario list. For each code path it crosses
attackers × vectors, adds **mutation** variants (re-encoding, boundary values, split-under-limit,
rotated identity) and **two-step chains**, then sorts by severity (`asset value × reachability`),
with kind (`base` → `mutation` → `chain`) breaking ties. It selects the top `N` and keeps the rest
in `overflow`, so raising `N` later **resumes** instead of restarting. It never decides a verdict.

### `forge.py`
Takes the verdicts Claude records and renders the final Markdown report — the heatmap grid, the
severity-ordered findings, the antibody results, the hardening timeline, and the residual/assumptions
section. Every field is optional; the renderer degrades gracefully. Run `--schema` for the full input
shape and a worked example.

Both scripts are **Python 3.8+ standard library only** — no dependencies, no network, no install.

## Why split brain (skill) from scaffolding (scripts)?

The judgments — *is this path reachable? did the control hold under mutation? how long would this
take?* — require reading the actual code and reasoning about it; that's the skill's job. The
bookkeeping — enumerating the combinatorial space deterministically, ranking it, and formatting
tables — is mechanical and belongs in code so it's repeatable and auditable. Keeping them separate
means a run is reproducible (same surface + same `N` → same timeline list) while the security
reasoning stays where it belongs.

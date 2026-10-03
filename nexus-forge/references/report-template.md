# Report template

`scripts/forge.py` renders this from the verdict data you assemble. The structure below is what the
final report must contain; keep section order. Fill judgments yourself — the script formats, it does
not decide.

```markdown
# Nexus Forge report — <target name>

## 1. Engagement scope
- **Target**: <repo / service / description>
- **Owner confirmation**: <owned / authorized — how confirmed>
- **Mode**: <analyze | harness | live>
- **Isolation**: <N/A for analyze | non-prod target confirmed for live/harness>
- **Covered**: <what was tested>
- **Not covered**: <what was out of scope and why>

## 2. Surface map
- **Entry points**: <list>
- **Trust boundaries**: <list>
- **Assets at risk**: <list>

## 3. Timeline matrix (heatmap)
A grid of nexus points. Rows = (attacker × vector) reaching an asset; columns = response posture.
Each cell: 🟢 strong / 🔴 affected / 🟡 unknown.

| Attacker × Vector → Asset | Block | Allow | Tarpit | Detect+Approve | Deceive | Immune |
|---|---|---|---|---|---|---|
| <e.g. Adaptive-AI × rate-limit evasion → user table> | 🟡 | 🔴 | 🟡 | 🟢 | — | 🟢 |

Legend: 🟢 held · 🔴 broke · 🟡 unknown · — not applicable.

## 4. Nexus findings
For each 🔴 (and notable 🟡), in severity order:

### F<n>: <short title>
- **Path**: <attacker> via <vector> → <asset>
- **Strength**: affected / unknown
- **Severity**: <Critical/High/Medium/Low> — <impact × exploitability, one line>
- **Time-to-compromise**: <minutes/hours/days/weeks> — *estimate*; assumptions: <profile, starting
  access, tooling, preconditions>
- **What broke**: <the specific function/endpoint/config and the condition>
- **Evidence**: <repro steps / request-response / log excerpt — enough for the owner to confirm>
- **Recommended posture**: <block / tarpit / detect+approve / deceive / immune> — <why this one here>

## 5. Antibodies
For each finding with an attempted fix:

### F<n> antibody
- **Fix**: <the targeted mitigation — diff / rule / config / dependency bump>
- **Applied to**: <sandbox copy — never live>
- **Re-challenge result**: <neutralized / partial / displaced>
- **Mutations tested**: <what variants were re-run>
- **New nexus opened**: <any / none>
- **Status**: proposal for owner review — not applied to any live system.

## 6. Hardening timeline (manageable assets)
Fixes ordered by severity-per-effort, grouped:
- **Now** (critical/high, low effort): <...>
- **Next** (high/medium): <...>
- **Later** (medium/low, or higher effort): <...>
Each item: the finding it closes, rough effort, and the owner approval it needs.

## 7. Residual & assumptions
- **Still unknown**: <points that need deeper testing — and the mode/access that would resolve each>
- **Assumptions behind TTC**: <every assumption the estimates rest on>
- **Caveat**: TTC figures are order-of-magnitude planning estimates, not guarantees; a determined or
  well-resourced attacker may move faster.
```

Keep the tone of the rendered report defensive and owner-facing throughout: it is a map for fixing,
delivered to the person who owns the system.

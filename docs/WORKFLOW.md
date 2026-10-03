# Visualized Workflow

All diagrams below are [Mermaid](https://mermaid.js.org/) and render automatically on the GitHub
file view — no tooling needed. They show how a single request to Nexus Forge fans out into many
timelines and collapses back into one actionable report.

## 1. The engagement, end to end

```mermaid
flowchart TD
    U(["User: red-team my repo"]) --> SAFE{"Safety and scope:<br/>ownership? isolation?"}
    SAFE -- "not confirmed" --> STOP(["Stop and ask the owner"])
    SAFE -- "confirmed" --> ASK[/"Ask once: run mode + budget N"/]

    ASK --> M1

    subgraph P1 ["Phase 1 · MAP"]
        M1["Enumerate entry points,<br/>trust boundaries, assets"] --> SURF[("surface.json")]
    end

    subgraph P2 ["Phase 2 · BRANCH"]
        GEN["generate_timelines.py --count N"] --> TL[("ranked timelines:<br/>selected + overflow")]
    end

    subgraph P3 ["Phase 3 · RUN"]
        RUN{{"Run each timeline<br/>at chosen depth"}} --> MODE[["analyze · harness · live"]]
    end

    subgraph P4 ["Phase 4 · SURVEIL"]
        SCORE["Score each nexus:<br/>strength · severity · TTC"]
    end

    subgraph P5 ["Phase 5 · IMMUNIZE"]
        AB["Synthesize antibody,<br/>re-challenge with mutations"]
    end

    SURF --> GEN
    TL --> RUN
    MODE --> SCORE
    SCORE --> AB
    AB --> VER[("verdicts.json")]
    VER --> FORGE["forge.py"]
    FORGE --> REPORT(["report.md:<br/>heatmap · findings · hardening plan"])
```

## 2. Why it's called a *nexus*: one request, many timelines

Each timeline is one cell of a three-axis matrix. The generator crosses the axes, so the
combinations a checklist never lists — mutations and two-step chains — appear on their own.

```mermaid
flowchart LR
    REQ(["One attack surface"]) --> A

    subgraph A ["Axis A · Attacker"]
        A1["Script opportunist"]
        A2["Known-CVE exploiter"]
        A3["Malicious insider"]
        A4["Adaptive AI adversary"]
        A5["Supply-chain attacker"]
    end

    subgraph B ["Axis B · Vector"]
        B1["Injection"]
        B2["Broken auth"]
        B3["IDOR / privilege"]
        B4["Rate-limit evasion"]
        B5["Deserialization / SSRF"]
        B6["Race / TOCTOU"]
        B7["Prompt injection / tool abuse"]
    end

    subgraph C ["Axis C · Response"]
        C1["Block"]
        C2["Allow (baseline)"]
        C3["Tarpit"]
        C4["Detect and await approval"]
        C5["Deceive (honeypot)"]
        C6["Immune / antibody"]
    end

    A --> B --> C --> NX{{"Nexus point:<br/>did the attack reach the asset?"}}
    NX -- "held" --> GREEN(["🟢 strong"])
    NX -- "broke" --> RED(["🔴 affected"])
    NX -- "undetermined" --> AMBER(["🟡 unknown"])
```

## 3. The adaptive loop — a blocked timeline is not the end

This is what separates Nexus Forge from a static checklist: when a control blocks the literal
payload, the attacker (and so the skill) *mutates*, and each mutation is a new timeline.

```mermaid
flowchart TD
    START(["Run timeline"]) --> HIT{"Control reached?"}
    HIT -- "allowed through" --> AFFECTED(["🔴 affected — trace to asset"])
    HIT -- "blocked" --> MUT{"Try a mutation"}
    MUT --> M1["Re-encode payload"]
    MUT --> M2["Boundary / fuzz values"]
    MUT --> M3["Split under the limit"]
    MUT --> M4["Rotate identity / fingerprint"]
    MUT --> M5["Chain a 2nd vector"]
    M1 & M2 & M3 & M4 & M5 --> RETRY{"Any mutation through?"}
    RETRY -- "yes" --> AFFECTED
    RETRY -- "no, after budget" --> STRONG(["🟢 strong — held under mutation"])
```

## 4. The antibody loop (Phase 5) — fix, then prove the fix holds

```mermaid
sequenceDiagram
    participant F as Affected nexus
    participant A as Antibody (fix)
    participant S as Sandbox copy
    participant R as Re-challenge
    F->>A: synthesize narrowest root-cause fix
    A->>S: apply to disposable copy (never live)
    S->>R: replay original attack + all mutations
    alt original + every mutation blocked
        R-->>F: neutralized
    else original blocked, a mutation still wins
        R-->>F: displaced — not a real fix, record it
    else fix opens a new weakness
        R-->>F: new nexus — re-run the matrix here
    end
    Note over F,R: Antibody ships as a PROPOSAL for the owner, never auto-committed.
```

## 5. Data flow between the two scripts

The scripts are deterministic scaffolding; the security judgment happens in the reasoning between
them (that's the skill's job — see [ARCHITECTURE.md](ARCHITECTURE.md)).

```mermaid
flowchart LR
    S[("surface.json")] --> G["generate_timelines.py<br/>(enumerate + rank, no verdicts)"]
    G --> T[("timelines.json<br/>selected + overflow")]
    T --> R2["Claude reasons over the real code,<br/>decides each verdict"]
    R2 --> V[("verdicts.json")]
    V --> F["forge.py<br/>(format only)"]
    F --> O(["report.md"])
```

See [EFFICIENCY.md](EFFICIENCY.md) for how the generator scales and how the budget `N` trades
coverage against effort — with reproducible, measured numbers.

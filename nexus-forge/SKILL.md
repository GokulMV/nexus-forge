---
name: nexus-forge
description: >-
  Adversarial security testing of a codebase or service the user OWNS: branch every (attack-vector
  × defensive-response) pair into an isolated "timeline" and re-run until the weak paths surface.
  Use when the user wants to threat-model, pentest, red-team, fuzz, or harden their own app; map
  which code is strong vs. fragile; estimate time-to-compromise for an attack path; simulate an
  adaptive AI attacker that reads API errors and adapts (paginating under rate limits, spinning a
  VM to dodge device binding, solving captchas); or run an "immune response" loop that proposes a
  fix (antibody), re-runs the attack plus mutations, and checks whether it holds or just displaces
  the attacker. Trigger on "test my app's security", "find the exploits in my code", "how long to
  hack this", "red team my API", "which part of my code is weak", "harden against attacks", or the
  user's own "timelines / nexus / variants" framing. Strictly defensive; operates only on systems
  the user owns or is authorized to test.
---

# Nexus Forge

A disciplined way to adversarially test **your own** application. The mental model is the
TVA from Loki: a single request can branch into many **timelines**, one per
(attack × response) combination. You run every branch in a sandbox, watch which ones let the
attack succeed ("nexus events"), and report where the code is strong, where it breaks, and how
long each break would take a real attacker. Then — like a body meeting a pathogen — you can let a
timeline synthesize an **antibody** (a targeted fix), re-run the attack plus mutations against it,
and see whether the antibody actually neutralizes the threat or just pushes it sideways.

Nothing here ever points outward. Every attack, every mutation, every "counter" happens inside the
simulation, against the user's own target. See `Safety & scope` below — read it before anything else.

## Safety & scope — the Sacred Timeline

This skill exists to **defend**, never to attack others. Before doing any work, confirm these hold.
If any is uncertain, stop and ask the user; do not proceed on assumption.

1. **Ownership.** The target is a system the user owns or has explicit, current authorization to
   test. A repo they're working in, their own deployed service, a staging box they control. If the
   target looks like someone else's production system or a third party's property, stop.
2. **Isolation for live runs.** Active testing (mode `live`) runs against non-production — a local
   instance, a staging/throwaway environment, or a disposable copy. Never fuzz or flood a system
   real users depend on.
3. **Findings, not weapons.** Output is oriented to *fixing*: proof-of-concept severity evidence,
   reproduction steps for the owner, and mitigations. Do not produce drop-in, weaponized,
   point-and-shoot exploit kits whose main use is attacking an unwilling third party, and do not
   build hack-back / retaliation against an attacker's own machine — that is illegal (e.g. CFAA,
   India's IT Act) and endangers the user. The "immune / counter" timeline is always an *internal*
   mitigation on the user's own target, never an outbound action.
4. **The adaptive-AI adversary is modeled to defend against it.** Describing how an AI attacker
   paginates under a rate limit or spins a VM to dodge device binding is in-scope *as a threat to
   harden against*. Translating that into a ready-to-run bypass for an arbitrary service is not.

When declining a part of a request on these grounds, keep helping with the rest — the defensive
version almost always gets the user what they actually need.

## The five phases

Run these in order. Use a task list so the user can watch progress; this work has real stages.

1. **Map** — inventory the target's attack surface and trust boundaries.
2. **Branch** — build the timeline matrix: every relevant (attacker × vector × response) triple.
3. **Run** — execute each timeline at the chosen depth (analyze / harness / live).
4. **Surveil** — score each nexus point: strong vs. affected, severity, and time-to-compromise.
5. **Immunize** — for the affected points, propose antibodies and re-run to confirm they hold.

### Choosing the run mode (ask once, up front)

The skill operates at three depths. If the user hasn't said which, ask with tappable options:

- **`analyze`** — pure threat modeling. Read the code/architecture, reason through each timeline on
  paper, produce the reports. Nothing is executed. Safe anywhere, including against a description of
  a production system.
- **`harness`** — generate the test artifacts (fuzzers, SAST/DAST config, attack-sim scripts, a
  mutation harness) for the user to run themselves against their own non-prod. You write the tools;
  they pull the trigger.
- **`live`** — you run the checks directly against a non-prod target the user points you at, then
  report. Requires the isolation guarantee above.

Modes compose — a typical engagement is `analyze` to find candidates, then `harness` or `live` to
confirm the interesting ones.

## Phase 1 — Map the surface

Before branching, you need to know what can be attacked and where trust changes hands.

- Enumerate **entry points**: HTTP/RPC endpoints, auth flows, file/upload handlers, message
  consumers (queues/topics), scheduled jobs, webhooks, admin/debug surfaces, third-party callbacks.
- Mark **trust boundaries**: where unauthenticated becomes authenticated, user becomes admin,
  one service calls another, external input reaches a parser/DB/shell/deserializer.
- Note **assets**: what an attacker would want — credentials, PII, money movement, data
  exfiltration, compute, or simply availability.
- Pull in **what already exists**: dependency manifests (for known-CVE paths), auth config, rate
  limits, input validation, logging/alerting. Weakness often lives in what's *missing*.

If you're pointed at a repo, read it. If pointed at a running service in `live` mode, enumerate
endpoints non-destructively first. If given only a description (`analyze`), map from the description
and flag assumptions.

Produce a short surface inventory before branching — it's the coordinate system everything else
plots onto.

## Phase 2 — Branch the timelines

A timeline is one cell of a three-axis matrix. Read `references/threat-actors.md` for the attacker
catalog and `references/response-branches.md` for the response catalog; both have the full detail.
In brief:

**Axis A — the attacker (variant):**
- Script-based opportunist — handwritten/off-the-shelf scripts, no finesse.
- Known-vulnerability exploiter — CVEs in your dependencies, misconfigurations, default creds.
- Authorized-but-malicious insider — valid credentials used beyond their intent (IDOR, privilege
  creep, data scraping within quota).
- **Adaptive AI adversary** — reads your responses and adapts. Sees a 429 → paginates 6 at a time
  under the limit. Sees device binding → asks to run a VM/emulator. Sees a captcha → routes to a
  solver. This is the modern one; give it weight.
- Supply-chain / dependency attacker — malicious package, poisoned build step, compromised CI.

**Axis B — the vector:** injection (SQL/NoSQL/command/template), broken auth & session, access
control (IDOR, privilege escalation), rate-limit & quota evasion, deserialization, SSRF, secrets
exposure, race conditions / TOCTOU, and for AI features: prompt injection, tool/agent abuse, RAG
poisoning, model-output trust.

**Axis C — the response the system takes in that timeline:**
- **Block** — reject outright.
- **Allow** — let it through (the baseline: what happens with no defense).
- **Tarpit / throttle** — slow it to uselessness.
- **Detect & await approval** — flag the event, hold, surface to the owner for a decision.
- **Deceive** — serve a safe decoy (honeypot/canary) *on your own infra* to surface attacker
  behavior without exposing real assets.
- **Immune / antibody** — synthesize a targeted mitigation, apply it to a sandbox copy, and
  re-run the attack + mutations to test it (Phase 5).

These three axes are **generators, not a closed menu**. The real space of timelines is enormous —
every attacker, crossed with every vector, crossed with every response, crossed with every *mutation*
of a payload and every *chain* of two vectors. That vastness is the point, not a problem to prune
away: the timeline a developer never anticipated usually lives in a combination nobody wrote down.
So Nexus Forge doesn't work from a fixed list — it **auto-generates scenarios from the target's own
code and surface**, up to a budget the user sets.

### The timeline budget (N) — user-selected, base 6, expandable

The user chooses **N**, how many timelines to spin up this run. This is the main dial of the skill.

- **Default base: `N = 6`** — a constant floor, enough for a fast first read. Use it when the user
  doesn't specify.
- **Expandable without limit** — the user can ask for 12, 50, 200, or `exhaustive`. Higher N means
  the generator goes deeper: more attacker×vector pairs, more mutations per vector, longer vector
  chains, more response postures evaluated per nexus point. Nothing caps this but the user's choice
  and the time/compute they'll spend.
- Ask once, up front, with tappable options (e.g. `6 (quick)`, `12`, `25`, `exhaustive`, or a custom
  number), alongside the run-mode question. If the user is absent, default to 6 and say so.

`scripts/generate_timelines.py` turns the surface map + N into a concrete, ranked scenario list so
generation is systematic rather than ad-hoc — see Phase 2b.

### Phase 2b — Auto-generate the scenarios from the code

Don't pick timelines from imagination. **Derive them from what the target actually is**, so the
scenarios fit this codebase and surface novel combinations:

1. **Seed** from the Phase 1 surface map — each (entry point → asset through a trust boundary) is a
   candidate path.
2. **Cross** each path with the attackers that can plausibly reach it and the vectors the code at
   that point is exposed to (an endpoint that concatenates SQL → injection; one that trusts a client
   limit → quota evasion; one that deserializes input → deser attacks). The code decides which
   vectors are even in play.
3. **Mutate and chain** — for each base scenario, generate variants (re-encoding, boundary values,
   split-under-limit, alternate transport) and two-step chains (leak → reuse, low-priv → escalate).
   This is where the unanticipated timelines come from.
4. **Rank** candidates by severity (asset value × reachability) and **take the top N**. A path's
   headline attack leads; its mutations and chains sit just behind it. So a small budget (the base 6)
   spends itself on the obvious high-severity attacks, and as the user raises N the extra slots fill
   with the mutations and two-step chains — the combinations a checklist would miss. The novelty of a
   bigger run is emergent: it's simply what enters once the obvious scenarios are exhausted.
5. **Record what was generated but not run** (the candidates beyond N), so expanding the budget later
   resumes from there instead of starting over.

Run `python3 scripts/generate_timelines.py surface.json --count N` to produce this ranked list as
JSON; feed the ones you run into `forge.py` as verdicts. The script is a scaffold — it enumerates and
ranks the combinatorial space deterministically so you can then reason through each scenario against
the real code. It never decides a verdict; you do that in Phase 3.

## Phase 3 — Run the timelines

Per the chosen mode:

- **`analyze`**: reason each timeline through. For each, state what the attacker does, how the code
  as written responds, and whether the attack reaches its goal. Be concrete — cite the function,
  endpoint, or config that decides the outcome. No hand-waving "this could be vulnerable"; name the
  line and the condition.
- **`harness`**: generate runnable artifacts and tell the user exactly how to run them against
  their non-prod. See `references/harness-guide.md` for what to generate per vector (fuzzer configs,
  SAST/DAST invocation, an attack-sim script, and the mutation loop). Keep artifacts parameterized
  so nothing is hardcoded to one environment.
- **`live`**: execute against the authorized non-prod target. Start non-destructive, escalate only
  as needed to establish severity, stop at proof — you need enough to prove the break, not to cause
  damage. Capture evidence (request/response, logs) for the report.

The **adaptive loop** is what makes this more than a checklist: when a timeline is blocked, don't
stop — mutate. Change encoding, chain a second vector, split a request under a limit, swap the
transport. That mutation is itself a new timeline. This is how you find the path the developer
didn't anticipate, and it mirrors how a real adaptive attacker (AI or human) actually behaves.

## Phase 4 — Tactical surveillance (scoring)

For every nexus point, produce a verdict. Read `references/scoring.md` for the rubric; the shape:

- **Strength**: `strong` (held across the attack and its mutations), `affected` (broke, or broke
  under mutation), or `unknown` (couldn't determine at this depth — say what's needed to resolve).
- **Severity**: impact × exploitability, using the mapped asset to set impact.
- **Time-to-compromise (TTC)**: an *order-of-magnitude estimate* of attacker effort along this
  path — minutes / hours / days / weeks — with the assumptions stated (attacker skill, whether a
  public exploit exists, access already held). This is a planning aid, not a guarantee; always
  label it as an estimate and show the reasoning, never a bare number.

The `scripts/forge.py` helper assembles these verdicts into the heatmap and report so you don't
hand-format tables. Use it rather than writing bespoke output each time.

## Phase 5 — Immunize (the antibody loop)

For each `affected` point, run the immune response — entirely inside the simulation, on the user's
own target:

1. **Synthesize an antibody**: propose the most targeted fix — an input validator, an authz check,
   a parameterized query, a rate-limit/quota rule, a dependency bump, a deserialization allowlist.
   Prefer the narrowest fix that addresses the root cause over a broad blanket.
2. **Apply to a sandbox copy only** — never the live target. In `analyze`, this is a described diff;
   in `harness`/`live`, a patch against a disposable copy.
3. **Re-challenge**: re-run the original attack *and mutated variants* against the antibody. An
   antibody that stops the exact payload but not a re-encoded one hasn't neutralized the threat — it
   displaced it. Note displacement explicitly; it's a common false win.
4. **Report the outcome**: neutralized / partial / displaced, plus any new nexus the fix opened.

Antibodies are always delivered as **proposals** for the owner to review and apply, never
auto-committed to a real system. This is the "detect & await approval" posture applied to fixes
themselves.

## Output

Use `scripts/forge.py` to render the final report; its template lives in
`references/report-template.md`. The report has these sections, in order:

1. **Engagement scope** — target, mode, isolation confirmation, what was and wasn't tested.
2. **Surface map** — entry points, trust boundaries, assets (from Phase 1).
3. **Timeline matrix / heatmap** — the grid of nexus points, each colored strong / affected /
   unknown, so the user sees at a glance where the code holds and where it bleeds.
4. **Nexus findings** — per affected point: attacker, vector, what broke, severity, TTC estimate
   with assumptions, and reproduction evidence.
5. **Antibodies** — proposed fix per finding, re-challenge result (neutralized / partial /
   displaced), and any new nexus opened.
6. **Hardening timeline** — the "manageable assets": fixes ordered by severity-per-effort, grouped
   into what to do now / next / later, so the user has a plan, not just a pile.
7. **Residual & assumptions** — what remains `unknown`, what depth would resolve it, and every
   assumption the TTC estimates rest on.

Keep the prose honest: an `unknown` labeled as such is worth more than a confident guess. If a
timeline couldn't be run to conclusion, say so and say what it would take.

## A note on the adaptive-AI angle

The user specifically cares about attackers using AI to *adapt around* defenses — pagination under
rate limits, VM/emulator to dodge device IDs, solver services for captchas. Treat this as a
first-class attacker in every engagement, because a static control that a human would respect, an
adaptive agent will probe and route around. The defensive lesson is almost always the same: controls
that rely on the client behaving (client-side limits, device fingerprints, "please only fetch 6")
are weak against an adaptive adversary; move the invariant server-side, tie it to something the
attacker can't cheaply mint (authenticated identity + server-enforced quota + anomaly detection),
and assume the fingerprint will be spoofed. Surface that lesson wherever this attacker reaches an
asset.

## Reference files

- `references/threat-actors.md` — the attacker catalog, including the adaptive-AI adversary, with
  the signals each one reads and how each adapts. Read during Phase 2.
- `references/response-branches.md` — the six response postures in detail, when each fits, and the
  legal/safe boundary on "deceive" and "immune". Read during Phase 2.
- `references/scoring.md` — strength / severity / TTC rubric. Read during Phase 4.
- `references/harness-guide.md` — what to generate per vector in `harness` mode. Read when the mode
  includes `harness`.
- `references/report-template.md` — the exact output structure `forge.py` fills.

## Scripts

- `scripts/generate_timelines.py` — expands the surface map + budget N into a ranked scenario list
  (base + mutations + chains), selects the top N, and holds the overflow so expanding N later
  resumes rather than restarts. Run in Phase 2b.
- `scripts/forge.py` — renders the heatmap + report from the verdicts you record in Phases 3–5.
  Both are stdlib-only; run `--schema` on either to see its input shape.

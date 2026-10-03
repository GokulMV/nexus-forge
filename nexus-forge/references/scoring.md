# Scoring rubric — tactical surveillance

Every nexus point gets three scores: **strength**, **severity**, and **time-to-compromise**. Keep
them honest — a labeled `unknown` is more useful than a confident guess, and every TTC is an
estimate with stated assumptions, never a promise.

## Strength

How well the code held across the attack *and its mutations*:

- **`strong`** — the control rejected the attack and survived reasonable mutation (re-encoding,
  chaining, splitting under limits, alternate transport). The invariant is enforced where it can't
  be bypassed (server-side, tied to identity).
- **`affected`** — the attack reached its goal, either directly or after mutation. Includes controls
  that stop the literal payload but fall to a variant (that's still affected — the attacker gets
  through).
- **`unknown`** — couldn't be determined at the current depth. State exactly what would resolve it:
  "needs `live` run against staging", "needs the auth middleware source", "needs to know if the
  quota is enforced server-side". Never round `unknown` up to `strong`.

Color the heatmap by this field: strong = green, affected = red, unknown = amber.

## Severity

Impact × exploitability. Use the asset mapped in Phase 1 to set impact — don't score in the
abstract.

**Impact** (what the attacker gains if the path works):
- *Critical*: full account/system takeover, money movement, mass PII/secret exfiltration, RCE.
- *High*: single-account compromise, significant data exposure, privilege escalation.
- *Medium*: limited data exposure, denial of service, information disclosure aiding a later step.
- *Low*: minor info leak, nuisance, requires improbable preconditions.

**Exploitability** (how hard the path is):
- *Trivial*: public exploit exists, no auth needed, or one obvious request.
- *Moderate*: needs some skill, chaining, or low-privilege access already held.
- *Hard*: needs significant effort, insider access, or rare conditions.

Combine conservatively: a critical-impact path that's trivially exploitable is your top finding;
a low-impact path that's hard to exploit is backlog. When in doubt, let impact dominate — a hard but
catastrophic path still matters.

## Time-to-compromise (TTC)

An **order-of-magnitude estimate** of attacker effort along this path, as a planning aid. Report as
a band — **minutes / hours / days / weeks** — never a false-precision number, and always with the
assumptions it rests on.

State these assumptions explicitly every time:
- **Attacker profile**: which of the five archetypes, and skill level.
- **Starting access**: unauthenticated? valid low-priv account? insider?
- **Tooling available**: does a public exploit exist? an automated scanner? an adaptive agent?
- **Preconditions**: anything that must already be true (a leaked credential, a specific config).

Rough anchors (adjust to the case, show your reasoning):
- **Minutes**: public exploit for an unpatched dependency; default creds; no-auth IDOR on
  sequential IDs; a secret in a client bundle.
- **Hours**: credential stuffing against weak lockout; enumeration under a weak/ client-side rate
  limit; a known misconfig needing minor adaptation.
- **Days**: chaining two medium vectors; brute force against a moderate control; building a working
  exploit from a disclosed-but-not-weaponized bug.
- **Weeks**: hard path needing custom research, insider positioning, or defeating multiple
  server-side controls.

Crucial adjustment for the **adaptive-AI adversary**: a control that would cost a human *days* of
manual tedium (paginating a huge dataset 6 at a time, rotating fingerprints across a VM fleet,
solving captchas at scale) can collapse to *hours* when an agent automates the tedium. If the path is
reachable by the adaptive attacker and the only thing standing in the way is attacker patience or
manual effort, shorten the band and say why. That's precisely the user's concern.

Always present TTC as, e.g.: *"~hours — assumes an adaptive agent with a valid free-tier account;
the only barrier is the client-side '6 at a time' limit, which the agent ignores, so harvesting the
full table is just wall-clock time, not difficulty."*

## Putting it together per finding

A finding reads: **[vector] via [attacker] → [strength], [severity], TTC [band] (assumptions)**, then
what broke, the evidence, and the recommended response posture. `forge.py` formats this; you supply
the judgments.

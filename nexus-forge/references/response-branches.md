# Response-branch catalog (the timelines a defense can split into)

When an attack reaches a control point, the system can respond in one of six ways. Each is a
separate timeline. The point of modeling all six — rather than assuming one global policy — is that
the *right* response differs per nexus point: a cheap read endpoint might warrant tarpitting, a
money-movement endpoint warrants detect-and-await-approval, a honeypot admin path warrants
deception. The report recommends a posture per point.

For each branch: what it is, when it fits, how to simulate it, and its cost/risk.

## 1. Block

- **What**: reject the request outright — 403, drop the connection, fail the operation.
- **Fits**: clearly malicious input, known-bad signatures, violations of a hard invariant.
- **Simulate**: confirm the control actually rejects *and* that the rejection can't be bypassed by
  mutation (re-encoding, alternate endpoint, chained vector). A block that only stops the literal
  payload is weak.
- **Cost/risk**: false positives lock out real users; a blocked adaptive attacker immediately
  mutates, so blocking without detection just starts a cat-and-mouse you can't see.

## 2. Allow (baseline)

- **What**: the request goes through. This is the "no defense" timeline — what happens today if the
  control is missing or ineffective.
- **Fits**: always run this as the control case, to measure what the attack achieves unopposed. It's
  how you establish severity and TTC.
- **Simulate**: trace the attack to its goal and record the full impact (what data, what action,
  what blast radius).
- **Cost/risk**: this *is* the risk — it's the measurement of it.

## 3. Tarpit / throttle

- **What**: don't reject — slow down. Add latency, reduce throughput, degrade the response until the
  attack is uneconomical.
- **Fits**: scraping, brute force, enumeration — anything whose value depends on volume or speed.
  Buys time and raises attacker cost without a hard wall that signals "you found something."
- **Simulate**: model whether the slowdown actually makes the attack's goal infeasible in the
  attacker's time budget. Against the adaptive agent, check it can't simply parallelize across many
  minted identities to recover throughput.
- **Cost/risk**: can degrade service for real users if mis-targeted; a distributed attacker may
  absorb it.

## 4. Detect & await approval  ← the user's chosen default posture

- **What**: recognize the suspicious event, hold or quarantine the action, and surface it to the
  owner for a decision. No automated counter-action.
- **Fits**: high-impact, irreversible, or ambiguous actions where a wrong automated response is worse
  than a brief delay — money movement, privilege grants, bulk deletes, data export. Also the right
  default when the owner wants a human in the loop.
- **Simulate**: verify the event is actually *detected* (you can't hold what you don't see), that the
  hold is enforced server-side, and that the approval path exists and is timely. Measure detection
  coverage: which timelines does the detector catch, which slip past?
- **Cost/risk**: adds latency to legitimate flagged actions; depends entirely on detection quality;
  needs someone available to approve. But it never does the wrong thing automatically, which is why
  it's a safe default.

## 5. Deceive (honeypot / canary / decoy)

- **What**: serve a convincing but safe decoy — a fake admin panel, canary credentials/tokens, a
  poisoned-but-harmless dataset — **on your own infrastructure**, to surface and study attacker
  behavior without exposing real assets.
- **Fits**: catching insiders and adaptive agents in the act; canary tokens that fire an alert the
  moment stolen data is used; wasting an attacker's time on a dead end.
- **Simulate**: confirm the decoy is isolated from real data, that tripping it reliably alerts, and
  that it can't be used as a pivot back into real systems.
- **Boundary**: deception is **inward** — it lives on your infra and misleads an attacker who came to
  you. It is never an outbound action against the attacker's machine. "Poisoned response" means a
  decoy you serve, not a payload that attacks whoever fetches it. Hack-back is out: illegal (CFAA,
  IT Act) and it endangers the owner.
- **Cost/risk**: maintenance overhead; a badly isolated honeypot becomes a real foothold; legal care
  needed that the decoy only ever affects the attacker's view of *your* system.

## 6. Immune / antibody  ← the co-evolution loop

- **What**: the biological-immune-response timeline. The attack lands in the sandbox; the system
  synthesizes a targeted **antibody** (a specific mitigation), applies it to a disposable copy, and
  re-runs the original attack plus mutated variants to test whether the antibody holds. Generation
  after generation: attacker mutates, antibody adapts.
- **Fits**: any `affected` nexus point where you want to not just note the break but prove a fix
  actually closes it — and confirm the fix doesn't just displace the attacker to a neighboring path.
- **Simulate**: see Phase 5 in SKILL.md. The critical test is **displacement**: an antibody that
  stops `' OR 1=1 --` but not its URL-encoded form has displaced, not neutralized. Always re-run
  mutations, not just the exact payload.
- **Boundary**: the antibody is a *fix to the user's own code/config*, delivered as a proposal for
  the owner to review and apply. It is never an outbound counter-attack. The "returns the attack"
  idea = the system fighting the infection within itself, exactly like antibodies — all internal.
- **Cost/risk**: a fix can open new nexus (e.g., an authz check that introduces a timing oracle);
  re-run the matrix around the patched area. Never auto-apply to a live system.

## Recommending a posture per nexus point

Don't pick one global policy. For each point, weigh: reversibility and blast radius of the action
(irreversible/high → detect-and-await or block), the attacker most likely to reach it (adaptive →
assume client controls fail, enforce server-side), the value of observing vs. stopping (insider risk
→ consider deception), and the cost of false positives (customer-facing → avoid hard blocks that lock
out real users). State the recommended posture and the reasoning in the finding.

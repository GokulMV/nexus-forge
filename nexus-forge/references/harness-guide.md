# Harness guide — what to generate in `harness` mode

In `harness` mode you produce runnable test artifacts the user executes themselves against their own
non-production environment. Everything here is for the owner to run against the owner's system. Keep
artifacts parameterized (target URL, credentials, limits via config/env) so nothing is hardcoded to
one environment and nothing is a drop-in weapon against an arbitrary third party.

General rules:
- Write to a `harness/` output directory with a `README` that states the isolation requirement up
  front: run against non-prod only, on a system you own.
- Make targets configurable; never bake in a real hostname or real credentials.
- Default to non-destructive. Any destructive check (writes, deletes) is opt-in behind an explicit
  flag and documented.
- Prefer established, auditable tooling over bespoke exploit code. Configure the scanner; don't
  reinvent the payload.

## Per-vector artifacts

**Injection (SQL/NoSQL/command/template)**
- A parameterized fuzzer that sends boundary and encoding-variant inputs to the identified
  parameters and flags responses indicating injection (errors, timing, reflected output).
- Point the user at a SAST pass over the handling code and a DAST scanner config for the live
  endpoint. The harness confirms the finding; the fix is parameterized queries / safe APIs.

**Broken auth & session**
- A script that exercises login throttling, session fixation, token expiry/rotation, and password
  reset flows, reporting which protections are present.
- Credential-stuffing *simulation* uses synthetic accounts you created — never a real breach list.

**Access control (IDOR / privilege escalation)**
- A script authenticating as a low-privilege test account that enumerates object references and
  cross-tenant IDs, reporting any it can read/modify that it shouldn't. Needs two test accounts to
  prove cross-user access.

**Rate-limit & quota evasion** (the adaptive-AI centerpiece)
- A harness that probes the limit, then *mimics the adaptive agent*: paginates just under the
  threshold, rotates client identifiers (simulating VM/fingerprint rotation using synthetic IDs),
  and measures how much data a cooperative-looking client can harvest over time. The finding is
  whether the server enforces a *total* quota per identity or only a rate — if only a rate, the
  adaptive attacker wins on wall-clock.

**Deserialization / SSRF / secrets exposure**
- Deserialization: a check that feeds crafted objects to endpoints and reports whether type
  allowlisting is enforced.
- SSRF: a check that submits internal/metadata URLs and reports whether egress is restricted.
- Secrets: a scan of client bundles, responses, error messages, and the repo history for exposed
  keys/tokens.

**Race conditions / TOCTOU**
- A concurrency harness that fires parallel requests at check-then-act flows (balance deduction,
  coupon redemption, quota consumption) and reports whether the invariant holds under contention.

**AI/LLM features (if present)**
- Prompt-injection corpus against any user-input-to-LLM path; checks whether system instructions
  can be overridden or tools abused.
- RAG-poisoning check: whether attacker-controlled content entering the knowledge base influences
  later outputs.
- Tool/agent-abuse check: whether the model can be steered to call tools beyond intended scope.

## The mutation harness (shared across vectors)

The thing that makes this adversarial rather than a checklist: a loop that takes a blocked payload
and automatically generates variants — alternate encodings, case changes, chained vectors, requests
split under limits, swapped transports — and re-sends them, recording which mutation (if any) gets
through. This is the simulated adaptive attacker. Wire each vector's fuzzer into it so a "blocked"
result triggers mutation before concluding `strong`.

## The antibody re-challenge harness

For Phase 5: a runner that applies a proposed patch to a disposable copy of the target, then replays
the original attack *and* the mutation set against the patched copy, reporting neutralized / partial
/ displaced. This is what proves a fix holds rather than just stopping the one payload you tested.
Never point it at the live target — only a throwaway copy.

# Threat-actor catalog (the variants)

Each timeline is driven by one attacker archetype. Model the ones plausible for the target; don't
force all five if some can't reach any asset. For each, the key question is: **what signal does this
attacker read, and how does it adapt when blocked?** A defense that assumes the attacker gives up on
the first rejection is the defense that fails.

## 1. Script-based opportunist

- **Capability**: handwritten or off-the-shelf scripts, automated scanners, credential-stuffing
  lists. No deep understanding of your system; sprays and prays.
- **Reads**: HTTP status codes, obvious error strings, whether a page loads.
- **Adapts**: swaps wordlists, rotates IPs/proxies, retries with backoff. Low creativity.
- **Harden against**: this is what generic rate limiting, WAF rules, and input validation stop.
  If an opportunist gets through, the problem is basic hygiene.

## 2. Known-vulnerability exploiter

- **Capability**: maps your stack to public CVEs and known misconfigurations; uses existing exploit
  code (Metasploit modules, PoCs from advisories), default/leaked credentials.
- **Reads**: version banners, dependency fingerprints, exposed admin panels, error pages that leak
  framework/version.
- **Adapts**: tries each known CVE for the identified version in turn; pivots to config weaknesses
  (open S3 bucket, debug endpoint, verbose errors) when no code CVE lands.
- **Harden against**: dependency scanning (SCA), patch cadence, removing version disclosure,
  disabling debug/admin surfaces in prod. TTC here is often *minutes* if a public exploit exists for
  an unpatched dependency — weight it heavily.

## 3. Authorized-but-malicious insider

- **Capability**: holds valid credentials (a real user, a partner, a low-privilege employee) and
  uses them beyond intent.
- **Reads**: what their legitimate access returns, then probes the edges — object IDs they can
  increment (IDOR), endpoints their role shouldn't reach, data they can scrape within quota.
- **Adapts**: stays under per-account limits, uses legitimate-looking request patterns, escalates
  privilege through overlooked paths (mass-assignment, a forgotten admin flag).
- **Harden against**: authorization checks on *every* object access (not just authentication),
  least privilege, per-identity quotas and anomaly detection, server-side enforcement of what each
  role may do. This attacker defeats perimeter defenses by definition — they're already inside.

## 4. Adaptive AI adversary  ← the modern one, give it weight

- **Capability**: an LLM-driven agent (or a human using one) that treats your API as an environment
  to solve. It doesn't follow a fixed script; it reasons about your responses and routes around
  controls.
- **Reads**: *everything you tell it* — error messages, rate-limit headers, device-binding
  challenges, captcha types, response timing, field names, validation messages.
- **Adapts** — the signature behaviors the user called out:
  - Sees `429 Too Many Requests` / a rate-limit header → **paginates under the limit** (fetches 6 at
    a time, sleeps, resumes) to harvest the whole dataset without tripping the threshold.
  - Sees **device-ID / fingerprint binding** → spins up a **VM or emulator**, rotates fingerprints,
    mints fresh device identities to bypass the binding.
  - Sees a **captcha** → routes it to a solver service or a vision model.
  - Sees **field-level validation** → re-encodes, fuzzes boundary values, probes for the one input
    the validator missed.
  - Sees a **client-side limit** ("please only request 6") → ignores it, because client-side
    requests are advisory to an adversary.
- **Harden against**: the invariant that defeats all of the above is **don't trust the client, and
  don't rely on the attacker's cooperation**. Move every limit server-side and tie it to
  authenticated identity, not to something cheap to mint (IP, device fingerprint, a client honor
  system). Enforce quotas on the *total* an identity can pull, not just the rate. Add anomaly
  detection on access *patterns* (breadth of objects touched, time-of-day, sequential IDs), because
  an adaptive agent's pattern differs from a human's even when each request looks legal. Assume
  fingerprints are spoofed and captchas are solved; design so that's survivable.
- **Why it matters**: a control a polite human respects, this attacker probes and bypasses. Every
  timeline should ask "what does the adaptive agent do when it hits this control?" — the answer is
  rarely "give up."

## 5. Supply-chain / dependency attacker

- **Capability**: compromises something upstream — a malicious npm/PyPI/Maven package, a typosquat,
  a poisoned transitive dependency, a compromised build step or CI secret.
- **Reads**: your dependency manifests, build pipeline, what runs with what privileges.
- **Adapts**: hides in postinstall scripts, transitive deps, or a legitimate package that was taken
  over; triggers only in CI or prod to evade local testing.
- **Harden against**: lockfiles with integrity hashes, dependency pinning, SCA in CI, least-privilege
  build tokens, provenance/signing, review of new and updated dependencies. This attacker reaches
  assets without ever touching your running endpoints.

## Using the catalog

For each mapped asset, ask which of these five can plausibly reach it and through which vector. That
(attacker × vector) pair, crossed with the response branches, is your timeline set for that asset.
Prune pairs that can't connect; keep the ones that can, especially any the adaptive-AI adversary can
reach, since those tend to be the paths the developer didn't anticipate.

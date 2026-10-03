# Security & Responsible Use

Nexus Forge is **defensive** tooling. It exists to help you find and fix weaknesses in a system you
own, before someone else finds them. It is not a tool for attacking others, and it is designed so
that its output is a map for fixing — not a weapon.

## The Sacred Timeline — rules every run must honor

Before doing any work, these must hold. If any is uncertain, the skill stops and asks; it does not
proceed on assumption.

1. **Ownership.** The target is a system you own or have explicit, current authorization to test —
   a repo you work in, your own deployed service, a staging box you control. If the target looks
   like someone else's production system or a third party's property, stop.

2. **Isolation for live runs.** Active testing (`live` mode) runs against **non-production only** —
   a local instance, a staging/throwaway environment, or a disposable copy. Never fuzz or flood a
   system real users depend on.

3. **Findings, not weapons.** Output is oriented to *fixing*: severity evidence, reproduction steps
   for the owner, and mitigations. Nexus Forge does **not** produce drop-in, point-and-shoot exploit
   kits whose main use is attacking an unwilling third party, and does **not** build
   hack-back / retaliation against an attacker's machine. Hack-back is illegal (e.g. the US Computer
   Fraud and Abuse Act, India's Information Technology Act) and endangers the owner. The
   "immune / counter" timeline is always an *internal* mitigation on your own target.

4. **The adaptive-AI adversary is modeled to defend against it.** Describing how an AI attacker
   paginates under a rate limit, spins up a VM to dodge device binding, or routes a captcha to a
   solver is in scope *as a threat to harden against*. Translating that into a ready-to-run bypass
   for an arbitrary service is not.

When a part of a request crosses this line, the skill declines that part and keeps helping with the
rest — the defensive version almost always gets you what you actually need.

## Antibodies are proposals, never auto-applied

Fixes ("antibodies") the skill synthesizes are applied only to a **sandbox copy** for
re-challenging, and are delivered to you as **proposals to review and apply yourself**. Nexus Forge
never commits a change to a live system.

## Reporting a vulnerability in this project

If you find a security issue in the Nexus Forge scripts or skill themselves, please open a private
report via GitHub Security Advisories on this repository, or contact the maintainer directly, rather
than filing a public issue. There is no bug-bounty program; this is a best-effort open-source
project.

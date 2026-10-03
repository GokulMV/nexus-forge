# Contributing to Nexus Forge

Thanks for your interest. A few ground rules keep this project coherent and on the right side of the
line.

## Principles

- **Stay defensive.** Every contribution must sit on the defensive side of [SECURITY.md](SECURITY.md).
  New attacker models, vectors, response postures, and scoring guidance are welcome *as material for
  hardening your own systems*. Ready-to-run exploits against arbitrary third parties, or anything
  resembling hack-back, are out of scope and will be declined.
- **Keep the scripts dependency-free.** `generate_timelines.py` and `forge.py` are Python 3.8+
  **standard library only** — no third-party packages, no network calls. This is deliberate: the
  tooling must run anywhere, offline, with nothing to install, and be trivially auditable.
- **Scripts scaffold; the skill reasons.** The scripts enumerate, rank, and format. They must never
  decide a security verdict — that judgment belongs to the person (or model) reading the real code.

## Making a change

1. Fork and branch from `main`.
2. Make your change. If you touch a script, update or add a case in `tests/test_smoke.py`.
3. Run the tests:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
4. If you change a script's input shape, update its `--schema` docstring, the matching file in
   `examples/`, and the relevant `nexus-forge/references/*.md`.
5. Open a pull request describing *what* changed and *why*, and confirm it respects the principles
   above.

## Style

- Match the existing code: small, readable, stdlib, graceful degradation on missing fields.
- Keep documentation honest and owner-facing — a labeled `unknown` is worth more than a confident
  guess.

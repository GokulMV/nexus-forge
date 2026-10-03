# Efficiency

Nexus Forge is built to be cheap to run and to apply to *any* repository. This page states exactly
what that means, with **reproducible, measured numbers** — not marketing.

> **What is and isn't claimed here.** The figures below measure the *generator* — how fast it
> enumerates and ranks the timeline space, how it scales, and how the budget `N` trades coverage for
> effort. They are deterministic and reproducible (`python3 tools/benchmark.py`). They do **not**
> claim a vulnerability-detection rate: whether a given weakness is found depends on the reasoning in
> Phase 3 against your real code, which is a human/model judgment, not a number this tool fabricates.
> Honest `unknown`s over invented percentages — the same rule the reports follow.

## Why it works on *any* repo

The skill operates on a **surface map** — an abstraction of entry points, trust boundaries, and
assets — not on language-specific source parsing. That single design choice is what makes it
repo-agnostic and cheap:

| Property | Consequence |
|---|---|
| **Language-agnostic** | The surface map describes HTTP/RPC endpoints, queues, jobs, and webhooks — not syntax. The same tool serves a Kotlin service, a Python API, a Go binary, a Node app, a Rust server. |
| **Zero dependencies** | `generate_timelines.py` and `forge.py` are Python 3.8+ **standard library only**. No `pip install`, no lockfile, nothing to audit. |
| **Offline / air-gapped** | No network calls. Runs in a locked-down CI runner or a disconnected environment. |
| **Deterministic** | Same surface + same `N` → byte-identical timeline list. Reproducible runs, reviewable diffs, no flakiness. |
| **Incremental** | Scenarios beyond `N` are kept in `overflow`, so raising the budget later **resumes** instead of re-running from zero. |

## Scaling is exact, not approximate

The generator's output size has a closed form. For a path exposing `V` vectors to `A` attackers:

```
timelines(path) = 5·V·A        (1 base + 4 mutations per vector×attacker pair)
                + V·(V−1)       (two-step chains among the path's vectors)
```

Summed over all paths, that is the full candidate space. The benchmark **asserts** the running code
matches this formula on every shape it measures, so the scaling claim can't silently drift.

## Generator scaling (measured)

Measured by `tools/benchmark.py` (median of 15 runs each), from a tiny service to a large surface.
Absolute times depend on the machine; the point is the **shape** — it stays linear in the number of
candidates, and the whole enumeration is milliseconds even for a very large surface.

| Paths | Vectors/path | Attackers/path | Candidates | Median time | Throughput |
|---|---|---|---|---|---|
| 3 | 2 | 3 | 96 | 0.123 ms | 782,906/s |
| 5 | 3 | 4 | 330 | 0.433 ms | 762,735/s |
| 10 | 4 | 5 | 1,120 | 1.569 ms | 713,908/s |
| 25 | 5 | 5 | 3,625 | 5.292 ms | 684,961/s |
| 50 | 6 | 5 | 9,000 | 13.776 ms | 653,308/s |
| 100 | 6 | 6 | 21,000 | 34.168 ms | 614,603/s |

A 100-endpoint surface — larger than most services — enumerates and ranks **21,000 attack
timelines in ~34 ms**. The enumeration is never the bottleneck; your (or the model's) reasoning
through the *selected* timelines is where the time goes, which is exactly what the budget `N`
controls.

## The budget dial: coverage vs. effort

`N` decides how many of the ranked timelines you actually reason through. Because ranking is by
severity (`asset value × reachability`), a small budget spends itself entirely on the
highest-severity **base** attacks; **mutations** and **chains** only enter as `N` grows. So you
pay reasoning effort in strict priority order.

Measured on the shipped example surface (`examples/surface.example.json`, 3 paths →
**96 candidates**: 18 base, 72 mutation, 6 chain):

| Budget N | Selected | % of space | base | mutation | chain |
|---|---|---|---|---|---|
| 6 (default) | 6 | 6.2% | 6 | 0 | 0 |
| 12 | 12 | 12.5% | 12 | 0 | 0 |
| 25 | 25 | 26.0% | 14 | 11 | 0 |
| 50 | 50 | 52.1% | 14 | 36 | 0 |
| 96 (exhaustive) | 96 | 100.0% | 18 | 72 | 6 |

**How to read this:** the default `N = 6` costs you six timelines of reasoning and covers the six
most severe direct attacks — a fast, high-signal first pass. Raising `N` buys depth (payload
mutations, then two-step chains) with linearly more effort and no wasted motion, because nothing
lower-severity is ever reasoned through before something higher-severity. That is the efficiency:
**effort scales with how much assurance you want, and always buys the most dangerous timeline next.**

## Reproduce it yourself

```bash
python3 tools/benchmark.py            # the tables above, as markdown
python3 tools/benchmark.py --json     # same data, machine-readable
python3 tools/benchmark.py --repeats 50   # tighter timing medians
```

No arguments, no setup, no network. The numbers on this page came straight from that command.

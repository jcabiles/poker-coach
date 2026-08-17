# N-LOGIT — a frozen continue reference, so cutting a bot's calling dial makes it FOLD more, not RAISE more

Base `origin/main` `3bac7d2` · commits `f365082` (build) + `891683a` (review folds) ·
spec `docs/ai-dlc/specs/n-logit.md` rev 3 · ledger `docs/ai-dlc/ledger/n-logit.md`

## The defect

At a facing-chips node FOLD / CALL / RAISE share one normalization, and `call_looseness` multiplies the CALL
merit only. Mass taken off CALL is therefore redistributed to FOLD **and** RAISE in proportion to their
merits — which on an aggressive persona lands mostly on RAISE. Measured before this change, halving each
pack's effective looseness moved raise-share the *wrong* way for all six personas (roadmap R10-4). Tightening
a bot made it wilder.

## The fix — two lines

Each pack authors `continue_ref`: the effective `call_looseness` its facing-node raise behaviour was
calibrated against, **frozen**. The engine scales the RAISE merit by `looseness / continue_ref` immediately
before the existing single normalization:

```
P(raise | continue) = (R₀·L/ref) / (C₀·L + R₀·L/ref) = (R₀/ref) / (C₀ + R₀/ref)
```

`L` cancels. `call_looseness` now controls **whether** the bot continues; the raise-side calibration controls
**how**. Mass freed from CALL routes to FOLD.

The divisor is the frozen anchor, never the live lever — re-synchronising the two collapses the scale to 1.0
forever and silently deletes the feature. That is exactly how rev 1 of this spec died (ledger R-1).

## Why play is bit-identical

At the authored anchor `looseness == ref`, so the scale is *exactly* `1.0` and the opted-in path is
bit-identical to the un-opted one. Nothing moved:

- 30,000 randomly generated facing cells, opted-in vs base path: **0 bitwise mismatches**
- `tests/test_price_tail.py`'s 23 frozen exact-equality vectors: untouched, green
- every seeded fixture, golden and `BANDS` entry: untouched. Graded-coverage delta: **zero**

## The evidence that it isn't a no-op

Rev 1 of this spec shipped a mechanism that cancelled algebraically and passed 8 of its own 10 gates while
doing nothing, because those gates were *identity* measurements. Only a *sensitivity* measurement separates a
behaviour-preserving fix from one that does nothing.

**G1, red-first, with the packs authored and the engine untouched** — worst |Δ P(raise | continue)| over
×0.25/×0.5/×2/×4, against a ≤1e-12 gate:

| nit | tag | lag | maniac | calling_station | passive_fish |
|---|---|---|---|---|---|
| 0.332927 | 0.333327 | 0.333318 | 0.333332 | 0.293076 | 0.333303 |

G2 showed 15,624 routing-sign violations. Representative: nit, two-pair flop, ×0.25 — `ΔP(fold) = +0.0217`
while `ΔP(raise) = +0.2974`. The calling lever went down and the raise rate went **up** by 14× the fold rate's
move.

Counterfactuals, re-run after review: forcing `rscale = 1.0` — a literal no-op that keeps every other line —
fails **5** gates. A mutant that deletes continue mass instead of preserving raise:call odds fails **2**.

## Two disclosed reach changes

**Gained** — on the river polar-bluff cell the call merit is hard-zeroed, so RAISE is the only continue and
the lever now moves the bluff-raise rate, which it could not before. Largest on ACE_HIGH at a small faced
price: lag `P(raise)` 0.104 → 0.651 across the sweep, maniac 0.773 at ×4. **Owner-ruled ship-as-is**; the
question is handed to the already-filed `N-riverair`, since the real anomaly is that node's hard-coded zero.

**Lost** — `_commit_transform` zeroes the FOLD merit on SPR-committed nodes while FOLD stays legal, so `L`
cancels out of the *whole* distribution and `call_looseness` is **inert** there, where it was dominant before
(tag, AA at SPR 1.0: 0.945 / 0.811 / 0.517 → flat 0.811). Consequence for the next slice: **`R9-LOOSEFIT` has
no reach over committed nodes, and must re-measure AF rather than assume the raise side is inert.**

Both are pinned by gates, in both directions, so neither can move silently.

## Review

Three reviewers, all git-read-only: `refuter` (Opus), Codex Sol (`gpt-5.6-sol`, effort high), and
`persona-realism-theory-reviewer`. **None found a HIGH defect in the mechanism.** Nine findings, every one
reproduced before adjudication: six accepted and fixed, two accepted-and-pinned rather than changed, one
downgraded from HIGH to a disclosure, one escalated to the owner. The interesting ones:

- **Codex** broke the decisive gate: G1 could be satisfied by a continuation *collapse* rather than by
  orthogonality. A skip is now only legitimate when the anchor was non-degenerate too.
- **The refuter** found that G4 pinned the weakest member of the very class it exists to disclose, and found
  the committed-node inertness above, which nothing in the suite could observe.
- **The theory reviewer** answered the spec's two open questions and confirmed the value-side improvement:
  a nit's set-raise frequency was swinging 0.881 → 0.317 with its *calling* dial and is now exactly flat.

Full adjudication with reasoning for every accept and reject: `docs/ai-dlc/ledger/n-logit.md`.

## Verification

`1386 passed, 1 skipped`, pytest exit 0 (read unpiped) · `BACKEND VERIFY OK` · `ruff check .` clean · base
verified green the same way before branching (`1356 passed, 1 skipped`).

Files: `personas_postflop.py` (the scale + a runtime guard), `content/models.py` (the field, its bounds, an
explicit-null rejection, and a corrected authorship comment), six `content/personas/*.json` (one number and a
version bump each), two test files (additions only — zero deletions).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01M7cLmiYSZBz3nHBZnYBCx2

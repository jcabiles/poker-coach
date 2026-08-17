# Finding ledger — RR-LINT (range-representation lint belt)

Slice: frozen defect inventory tripwire (tests-only; RR decision set, owner-adjudicated
2026-07-30). Branch `feat/persona-realism-rr-lint` (worktree), commits `c7cc77e` (build) +
`f02b025` (review folds), based on `05525cd` (#137). Reviewers (git-READ-ONLY): `refuter`,
Codex `gpt-5.6-sol` (theory reviewer skipped — the slice asserts no theory claims; it freezes
measured file state; theory input came via the adjudicated design pass).

## Done-condition

Three lints (row gaps / inert tokens / weight interleaving) over every preflop node of all six
packs, each asserted EQUAL to a committed inventory of HEAD's defects; fails on NEW defects and
on FIXED-but-still-listed ones (anti-laundering, both directions negative-proven). Refuter
reproduced all three sets exactly from a from-scratch reimplementation; full suite 1135 pass /
1 skip in-worktree; `BACKEND VERIFY OK`; zero pack/fixture edits.

## Findings

| # | Source | Sev | Finding | Adjudication |
|---|--------|-----|---------|--------------|
| C-1/R-1 | Codex+refuter (convergent) | MED | Dominant-action pick used dict-order `max()`; 22 exact-tie mixes → under-reporting 5 real escalations at HEAD (incl. station limped-aces limp 0.5→1.0 ×2) AND spurious tripwire fires on semantically-null key reorders | **ACCEPTED — FIXED** `f02b025`: co-dominant set (every non-fold action within 1e-9 of the non-fold max) tracked deterministically; key-reorder no-op proven inventory-stable; inventory regenerated 10→15 interleavings |
| R-2 | refuter | LOW | `fold` eligible as dominant action → future rising-fold false positives | **ACCEPTED — FIXED**: fold excluded from dominance |
| C-2 | Codex | LOW | Entry identity unstable: positions joined in authored order, mixes keyed by list index — harmless edits could reshuffle entries | **ACCEPTED — FIXED**: sorted position keys; mixes identified by first combos token |
| R-3 | refuter | LOW | Intra-mix shadowed/duplicate tokens not covered | **ACCEPTED — FIXED**: covered-set now accumulates per token; zero instances at HEAD (inventory unchanged) |
| R-4 | refuter | LOW | Commit message said "17 response-layer entries"; correct count 16 | **NOTED**: corrected in the fold commit message; constants were always exact |

Verdicts: refuter **PASS** (lattice exact 169-partition; carve-out idiom correctly unflagged;
node-key collisions impossible per `PersonaPack._node_ordering`; both tripwire directions
negative-proven via TMPDIR mutations) · Codex **FAIL→resolved** (its independent recomputation
matched all three constants; both issues folded).

## Interaction note (verified live by the refuter)

Against `feat/persona-realism-r10-pre2`'s maniac.json the lint fails LOUDLY on exactly the 7
maniac entries PRE2 fixes, all in the "FIXED but still listed" direction — whichever branch
merges second updates the constants (documented in both ledgers + the module docstring).

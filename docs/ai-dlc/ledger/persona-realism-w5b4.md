# Finding ledger — W5-b4 (maniac vs_limpers iso + vs_rfi 3bet/call/fold repair)

Slice: W3R-1 target reopen (roadmap ~line 1333). Branch `feat/persona-realism-w5b4` (isolated
worktree), commits `deb614a` (build) + review-fold commit, based on `6aabf41` (#140). Built in
a parallel wave with R9-SIGNAL (#141, merged). Reviewers (git-READ-ONLY): `refuter`,
`persona-realism-theory-reviewer`, Codex `gpt-5.6-sol`.

## Done-condition

🔴 committable gate `test_maniac_vpip_pfr_gap_back_under_ten` — RED at parent (gap 15.89 at the
gate's n, refuter-verified by pack swap), deterministic 7.33 at HEAD (40-seed sweep 6.83–9.56,
mean 8.11). Content: vs_limpers positional split (late iso authored 54.3%, sampled ~58%; EP
35%); vs_rfi tiers {3bet 1.0} / {.5/.5} / {.2/.3/.5} / any-two {3bet .05, fold .95}; fringe
over-limp {raise .5, limp .2, fold .3} (realized limp mass 0.2% of hands — no F11 limp-trap).
Measured n=1200: gap 15.44→7.58 · cold-call 33.9→16.7 · vs_rfi 3-bet 12.4→22.6 · PFR
25.1→31.7 · VPIP 40.6→39.3 (WRONG direction — disclosed, see T-1/R-3).

## Findings (14 total; the three reviews converged on the same three themes)

| # | Source | Sev | Finding | Adjudication |
|---|--------|-----|---------|--------------|
| T-1 | theory | HIGH | Gap fixed by DELETING continue mass — fold-to-open 61%, "least maniacal on the roster"; remedy: restore tier-3 calls | **DIAGNOSIS ACCEPTED, REMEDY MEASURED INFEASIBLE**: 4-point grid (in this ledger, below) — every call-restoration breaks the committed gap<10 gate (sweep max 9.6→11.4) AND raises 3-bet-pot via squeezes behind the maniac's calls. Adjudicated per T-2's own framing: the reachable VPIP/continue lever is `unopened` (out of scope, N9); W4-b inherits "continue-vs-open is an unwatched missing §5 row". Disclosed in the gate docstring |
| T-2 | theory | MED | "Texture guards cap VPIP" adjudication wrongly let a non-§5 directional guard outrank a §5 keystone row | **ACCEPTED — REFRAMED** in the gate docstring exactly as prescribed (unopened out of scope; guards bounded the substitute lever; §5 VPIP row NOT reopened; W4-b inherits the specific question) |
| C-1/R-1 | Codex+refuter | HIGH/MED | Texture guards machine-dependent: throughput-derived n made 0.15/0.45 guards fail at 22/26 reachable n post-slice, green only at the 1500 cap | **ACCEPTED — FIXED STRUCTURALLY**: `texture_n` FIXED at 1500 (the `_WTSD_ORDER_N` precedent); guards re-derived from a 10-seed sweep at fixed n (3-bet-pot 0.162±0.0085 → ceiling 0.20; limper 0.469±0.014 → floor 0.42; p2f 2.374±0.034 → floor 2.2) — the +3pp 3-bet-pot vs parent IS the repaired maniac attacking opens; the old 0.15 encoded passive-table prose main already violated in expectation. A trim experiment (3bet .2→.15) was run and REVERTED: stream displacement re-rolled readings randomly and it degraded identity for nothing |
| C-2/R-2/T-3 | all three | HIGH/MED | Arrival-band recentres claimed a causal "genuine texture shift" — 21-seed PAIRED sweeps show the slice moves NEITHER cell (BTN t=-0.83, roster-wide t=+0.07); the old BTN floor was mis-drafted (11/21 parent seeds already below it) | **ACCEPTED — REFRAMED + RE-DERIVED**: both blocks rewritten as mis-calibration repairs with the paired evidence quoted; BTN band [0.02, 0.075] (pooled 21-seed dispersion, ceiling tightened per theory so a revert/collapse still trips); roster-wide [0.275, 0.335] kept, justification corrected (the causal shift was R10-PRE2's, concealed by pinned-seed luck) |
| R-3 | refuter | MED | VPIP regressed (40.6→39.3; 40-seed ~38.8 vs ~39.7) — half the REPORTED pass/fail unmet and undisclosed | **ACCEPTED — DISCLOSED** prominently in the gate docstring + here; adjudication per T-1/T-2 |
| R-4 | refuter | LOW | Gate docstring margin optimistic (6-seed 8.8 max vs 40-seed 9.56) + cited wrong n | **FIXED**: 40-seed numbers + CI-deterministic note + n=600 clarified |
| C-3 | Codex | LOW | Never-cold-calls test was a stochastic 5-hand probe; stale tier comments | **FIXED**: deterministic authored-mix resolution asserting call weight literally 0.0, on top of the probe; tier comments updated |
| T-4 | theory | LOW | Provenance triples missing on gap/3-bet citations | **FIXED**: §5a registry rows quoted verbatim |
| T-5 | theory | LOW | nit AF golden cell 0.894→None silently stopped watching a HARD-today stat | **FIXED**: named in the re-record block, accepted for this wave (population-n band still gates it) |

Clean per the refuter: fixture attribution bit-exact (pack-swap reproduces every parent
number) · F11 holds STRUCTURALLY (169-class enumeration: no reachable mix lets trash call) ·
BANDS re-anchor exact, other five personas byte-identical (pool anchor untouched) · node
ordering valid · scope = 1 pack + 7 test files.

## The infeasibility grid (T-1 evidence; n=600 sweeps ×6, texture n=2000)

| tier-3 | gap max (<10 gate) | fold-to-open | 3-bet-pot |
|---|---|---|---|
| `.2/.3/.5` (shipped) | 8.8 ✓ | 61.4% | .145 ✓ |
| `.2/.4/.4` | 9.6 thin | 57.9% | .152 ✗ |
| `.2/.45/.35` | 10.8 ✗ | 55.6% | .153 ✗ |
| `.2/.5/.3` | 11.4 ✗ | 57.6% | .159 ✗ |

## W4-b hand-offs accumulated by this slice

1. maniac stable-n AF 3.62→3.16 (from R10-PRE2, still open).
2. maniac VPIP 39.3 vs §5 45-58 — lever is `unopened`/arrival, not response nodes.
3. MISSING §5 ROW: maniac continue-vs-open (fold-to-RFI) — the identity-bearing stat the
   aggregates were balanced on, currently unwatched.

# Finding ledger — R10 preflop lane slice 3 (R10-PRE2)

Slice: maniac ladder separation / first-in identity (R10-1a). Branch
`feat/persona-realism-r10-pre2` (isolated worktree), commits `a46de37` (build, pre-rebase
`61b0e5a`) + `127f1a9` (review folds, pre-rebase `414210a`), rebased onto `05525cd` (#137).
Reviewers (git-READ-ONLY): `refuter`, `persona-realism-theory-reviewer`, Codex `gpt-5.6-sol`.

## Done-condition

Gate ① maniac authored per-seat RFI > LAG at every seat — FAILED at parent (all 9 seats,
refuter-recomputed independently), passes post-fix: 34.18/37.38/40.42/49.02/57.32/63.47/73.27,
SB 60.27, BB 50.71 (LAG 25.10…66.09/51.98/45.40). Gate ② (review-added) monotone-to-button —
FAILED at parent (CO 49.67 > BTN 48.34), passes post-fix. Levels DIRECTIONAL (9-max rubric,
format-unstated → seeds only). Sampled rates REPORTED via R10-COUNT: aggregate 0.410, EP 0.367
vs authored EP avg 0.373 (Codex independently reproduced 0.4095/0.3734). `BACKEND VERIFY OK`
1133 pass / 1 skip; ruff clean.

## Findings

| # | Source | Sev | Finding | Adjudication |
|---|--------|-----|---------|--------------|
| T-1 | theory | MED | BB `unopened` node structurally unreachable in organic play (0/898 occupancies; fold-around ends the hand, SB limp routes to vs_limpers) — equal-seat-weight framing overstates what shipped | **ACCEPTED — FOLDED**: occupancy table + BB-unreachable note in the ladder-gate docstring; node kept (authored-shape pin + pack symmetry). Arrival gap is a known contract silence, not a slice defect |
| T-2 | theory | MED | Stable-n AF side-effect undisclosed: maniac AF 3.62→3.16 (n=1200), further below §5's 4–6 keystone | **ACCEPTED — FOLDED**: stable-n before/after triple recorded in the golden-stats block with explicit ⚠️ W4-b hand-off; REPORTED only, no band moved |
| T-3 | theory | MED | N200 WTSD "directionally coherent" narrative was a causal story on rng-tripwire noise (stable-n WTSD flat: 0.506→0.499) | **ACCEPTED — FOLDED**: narrative replaced with stream-displacement-noise wording + stable-n numbers |
| T-4 | theory | LOW | Rubric seeds cited without format triple | **FOLDED**: labeled 9-max dossier rubric, format-unstated → directional only |
| T-5 | theory | LOW | Monotone gate relies on §5a's [UNVERIFIED] ordering licence undeclared | **FOLDED**: declaration added (claim is STRUCTURAL — fewer players behind) |
| T-6 | theory | LOW | Coverage-dip mechanism sentence inferential pending T-REJECT | **FOLDED**: marked inferential |
| R-1 | refuter | LOW | W3R-1 module docstring still states ace trims as live; test names asserted the opposite of their bodies | **FOLDED**: supersession note added; tests renamed `*_offsuit_aces_open` |
| R-2 | refuter | LOW | `_stats` "rows 3-4 structurally independent" claim false (deal-stream coupling; 12.81→12.67 / 46.51→46.94 this slice; 45.99 figure stale) | **FOLDED**: residual-coupling note added with measured numbers |
| R-3 | refuter | LOW | Documented 20-reseed sweep span understates dispersion (independent 13-seed sweep exceeded both floors) | **FOLDED**: union span (agg 0.373-0.444, EP 0.318-0.404) documented as the resizing basis; bands unchanged (≥2σ margin under both) |
| R-4 | refuter | LOW | SB no-open-limp probe was a 3-hand spot-check | **FOLDED**: pack-level `test_maniac_unopened_has_no_limp_weight_anywhere` added |
| R-5 | refuter | LOW | Roadmap R10-PRE2 spec not committed on the branch | **NOTED, NO ACTION**: owner convention — persona roadmap/profile edits stay local, out of branches; this ledger is the acceptance record |

Verdicts: Codex **PASS, zero issues** · refuter **PASS** (independently recomputed both gates at
parent+HEAD; reverted-maniac.json-only repro of ALL fixture states byte-identically; 13-seed
sweep zero band trips; zero holes/dead tokens in the new ranges) · theory **GO** (ladder
realistically the flattest of the position-aware roster — 2.14× UTG→BTN vs LAG 2.63×, TAG
3.40×; A2o+ supersession factually verified against LAG's own HJ A2o raise 0.4; N5/N9 clean —
zero response-node lines changed).

## Fixture re-records (slice-authorized)

R10-COUNT cross-val bands re-derived (sole-authorized re-recorder): agg [0.32,0.51], EP
[0.27,0.47] · maniac BANDS rows 1-2 re-anchored to exact authored 51.78 ±2.0pp ·
coverage_baseline 1176→1251 total, graded HELD exactly at 329 (ratio 28.0→26.3% DIP flagged,
T-cover mapper track; numerator-invariant so no realism regression can hide in it) ·
`_PRE_M3_FIRES` re-pinned · `_GOLDEN_STATS_N200` all six rows (stream displacement; stable-n
truth recorded alongside) · W3R-1 maniac pins re-pinned to the PRE2 ranges. Population bands
frozen to W4-b.

## Interaction note

RR-LINT (`feat/persona-realism-rr-lint`, built same day) freezes a defect inventory that
includes 7 maniac `unopened` entries this slice fixes (QJo/43s gaps, K2o inert token, 4 weight
interleavings). Whichever branch merges second updates: PRE2-second → drop those entries during
rebase; RR-LINT-second → recompute inventory on post-PRE2 main.

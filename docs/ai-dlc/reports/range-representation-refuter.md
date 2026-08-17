# Range-representation debate — refuter report (2026-07-30)

Adversarial review of the position "hand-authored range charts + algorithmic verification is the
right pattern". Verdict: **the position survives only in its narrowest form (claim 3 — authored
data + measured certification — and "data lives in content/"). Claims 1, 2, 4 refuted or
materially weakened by the repo's own record.** The framing "authored charts vs generator" is a
false axis; the real axis is *representation*, and the content/ invariant is neutral between them.

## Deterministic checks run

- `pytest tests/test_personas.py tests/test_content.py tests/test_w3r1_preflop_cleanup.py -q` →
  68 passed at HEAD *while every defect below is present*. The existing gate suite catches none.
- Independently re-derived the authored combo-weighted RFI ladder from content/personas/*.json
  (first-match-wins, 1326-combo weighting) — reproduces the roadmap R10-1 table ±1pp, plus one
  NEW violation the roadmap does not name.

## Findings

### HIGH — reviewability-in-practice is falsified by the defect record
- W5-b1 (PR #119 + #124) widened nit/tag/lag ladders; #124's own message: "maniac is untouched."
  That single omission is the whole of R10-1a (maniac < lag at 9 of 9 seats).
- P1 (PR #83, commit 5cb7a35) fixed "a station never folds premiums first-to-act" in
  calling_station.json — and left maniac.json's premium unopened mixes at raise 0.85/fold 0.15
  (BTN 0.70/0.30). Six days later the 756-hand external review had to rediscover it as R10-1b.
- PR #119 was squash-merged not-green (nine tests red) per #124's message.
- These packs went through refuter + Codex dual review per PR. Eyeball review did not catch a
  cross-persona ordering break, a premium-fold class it had just fixed elsewhere, or a wildcard
  node inverting nit vs tag. Reviewability is the position's load-bearing argument and the one
  the history falsifies.

### HIGH — the "texture" premise is empirically ~zero in the membership layer
- Tested every unopened node for per-row contiguity (pairs row + 13 suited rows + 13 offsuit
  rows; a range is exactly a floor vector iff every row is a top-anchored contiguous segment):
  **784 of 787 rows contiguous (99.6%)**. The authored ranges ARE a ~27-dimensional floor vector
  per (persona, seat) plus fringe tier weight.
- The only three non-contiguities are authoring BUGS, not texture:
  - tag.json:80 (BTN): `T5s+ … T3s` → **T4s hole**
  - tag.json:96 (BB): `K5s+, Q7s+ … K3s, Q5s` → **K4s and Q6s holes**
  Every other fringe token is exactly floor−1. Hand-authoring produced zero intentional texture
  beyond the floor vector and three off-by-one gaps that survived review.
- The position's strawman: it attacks percentile-over-a-ONE-dimensional-score, which nobody has
  to propose. A 27-row floor table reproduces the corpus exactly and cannot emit a hole.

### HIGH — the constraint web is already a constraint system being solved wrong by hand
- Standing/pending inequalities over the 36 unopened width scalars: maniac>lag ×9 (R10-PRE2),
  nit<tag ×9 (W5-b3), four-way chain later, within-persona seat monotonicity, 4-bet-share
  ordering (R10-3BET), vs_3bet tiers. Those scalars are nonlinear first-match-wins aggregates of
  **1031 authored tokens across 129 mixes**; editing one token perturbs several inequalities.
- **NEW violation not in the roadmap's R10-1 list: maniac's own ladder is non-monotonic at HEAD —
  CO 49.1% > BTN 47.2% authored RFI.** The button is authored TIGHTER than the cutoff for the
  loosest persona. PRE2's maniac>lag gate would not catch it; no test at HEAD catches it.

### MED — "a generator's output can't be reviewed" is false as stated
- Nothing in the pipeline reads anything but emitted JSON (schema types combos as plain string;
  personas.py:57 `_combos = frozenset(parse_range(spec))`). A generator that commits its emitted
  content/personas/*.json yields a byte-identical artifact — same eyeball review, same git diff,
  same schema gate, same measurement gates — PLUS a reviewable ~27-number parameter table making
  ordering constraints checkable dimension-wise. Lost: only the ability to hand-place an
  arbitrary single combo outside the floor structure — zero intentional instances in the corpus
  (3 instances, all bugs).

### MED — authoring tedium is silently corrupting the packs (dead tokens)
- 14 nodes across 5 of 6 packs carry fully SHADOWED (dead) combos first-match-wins can never
  reach, e.g.:
  - maniac unopened BTN mix1: ['K2o'] (already in mix0's K2o+)
  - maniac vs_3bet mix2: 12 dead combos incl. AKs/AQs/AJs/KQo/JTs
  - maniac vs_rfi mix1: ['AJs','AKo','AKs','AQo','AQs']
  - tag vs_rfi mix2: ['ATs','KJs']; mix3: ['KQo']
  - lag vs_3bet mix2: ['AKo','AKs']
- `test_no_fully_shadowed_mix_within_node` (P1) only rejects a WHOLLY dead mix, not dead tokens.
  The files carry text that reads as intent (maniac vs_3bet APPEARS to call AQs 50%) but is
  inert — weakening the reviewability claim a second, independent way.

### LOW — spot_signature and fixture blast radius are non-discriminators
- spot_signature() (srs.py:48-68) hashes no range content; pack edits are signature-safe either
  way. Fixture re-records trigger on behavior change, identical for human or generator edits.
  The one generator-specific cost is emitted-diff churn (mitigable by deterministic ordering).

## Strongest surviving alternative (steelman)

Keep the invariant literally — strategy still lives in versioned content/ — but move the
*authored surface* from freeform combo strings to a per-(persona, seat, facing) **row-floor
table** (pair floor, one floor per suited row, one per offsuit row, fringe-band depth, tier
weights), with the existing combos strings **emitted** from it and committed. Same files, same
schema, same loader, same review-by-diff, zero downstream blast radius. Buys, measured against
the actual record: the 3 range holes and 14 dead-token sets become UNREPRESENTABLE; cross-persona
ordering becomes a comparison of ~27 numbers instead of a nonlinear aggregate of 1031 tokens (a
W5-b1-style "widen 3 of 4 packs" edit fails at authoring time, not 4 days later in a 756-hand
review); the maniac CO>BTN inversion becomes a one-line monotonicity assert. Claim 3 (measured
certification) survives intact but is ORTHOGONAL to representation — R10-COUNT measures behavior
after the fact; none of the defects above were authoring-time-detectable under the current
representation.

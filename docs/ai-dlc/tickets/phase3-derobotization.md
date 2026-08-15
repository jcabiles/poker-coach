# Tickets — persona de-robotization (phase-3 ruling A, slice 1)

**Bottom line: six tickets in four pull requests. T0 and T1 build the
measurement and the guardrails and must land first, because every later ticket
is judged by them and because the two reused gates are blind to exactly the
things this slice changes. T2 through T5 are the actual de-robotization, each
gate-verified, each shipped as its own reviewable pull request.**

Spec: `docs/ai-dlc/specs/phase3-derobotization.md`.
Contract map: `docs/ai-dlc/contracts/phase3-derobotization.md`.
Review findings: `docs/ai-dlc/ledger/phase3-derobotization.md`.

## Dependency order

```
T0 (gate runner) ──┐
                   ├──> T2 (preflop sizing jitter)      [PR-1]
T1 (guardrails) ───┤
                   ├──> T3 (range-edge softening) ──> T4 (positional gradients)   [PR-2]
                   └──> T5 (postflop size ecology)  [PR-3]
```

T0 and T1 ship together as **PR-0** and block everything. T2, the T3+T4 pair,
and T5 are independent of one another and touch disjoint top-level keys of the
same six persona files, so each branches from `main`. Each is test-merged
against the others before its PR opens; any real conflict is reported rather
than silently resolved.

---

## T0 — Gate runner, verified against two known answers

**Do:** Build the runner that produces a candidate batch and evaluates it with
the two existing constraint rules against the pinned baseline.

- `backend/tools/derobo_gate.py` — export a batch at seed 601, 50,000 hands,
  the baseline's pinned nine-seat lineup; then invoke the analytics check as a
  subprocess under poker-analytics' own interpreter and parse its JSON.
- `poker-analytics:analysis/derobo_gate_check.py` — open the batch with
  `scorer.stats.open_batch`, build the lineup and the ten-statistic per-persona
  vectors, call `rule1_label_and_separation` and `rule4_determinism`, emit
  PASS/FAIL JSON with every threshold and measured value named.
- `--seeds 5` runs the five-seed set for slice acceptance.

**Do not:** call `run_checks()`; rebuild `a5_baseline_z.json`; add duckdb or
numpy to the poker-coach environment; touch any grader.

**Acceptance:**
1. Against **unchanged** packs the runner reproduces the baseline's recorded
   `min_pairwise_distance` of `1.792042`.
2. The recomputed per-persona statistic vectors match the baseline artifact's
   stored `raw_vectors` for all six personas.
3. Both rules report PASS on the unchanged roster.
4. Runner unit tests cover: a deliberately degraded synthetic candidate FAILS
   the separation floor, and a synthetic all-one-action candidate FAILS the
   determinism guard. A gate that has never been seen to fail is not a gate.

**Done-condition:** `python -m tools.derobo_gate --check --self-test`

**Owns:** `backend/tools/derobo_gate.py`, `backend/tests/test_derobo_gate.py`,
`poker-analytics:analysis/derobo_gate_check.py` and its tests.

---

## T1 — Guardrails the gates cannot provide

**Do:** Add the pack-validation invariants and the positive tests from spec
§7.2 that the two statistical gates are structurally blind to. These are
guardrails, not behaviour changes, and they pass against the current packs on
day one — verified: today there are zero shadowed mixes and zero off-grid
sizing keys.

- Grid membership: every authored `postflop.sizing` and `sizing_by_node` key is
  a member of `RECOGNIZED_BET_FRACS`. Enforced in `models.py` validation.
- No shadowed mixes: within a preflop node, no mix is unreachable because an
  earlier mix already covers its combos.
- Positional completeness: for any facing whose nodes are position-explicit,
  the union of positions covers every seat — no seat may silently fall to the
  implicit-fold path.

**Do not:** change any pack value; change any decision logic.

**Acceptance:** all three invariants pass unchanged against the six shipped
packs; each has a negative test proving it fails on a deliberately malformed
pack; `./scripts/verify.sh` green.

**Done-condition:** `./scripts/verify.sh`

**Owns:** `backend/app/domain/content/models.py` (validators only),
`backend/tests/test_persona_pack_invariants.py`.

---

## ✅ Blocker CLEARED by T-control — the deck's control no longer fingerprints the packs

**T-control replaced the deck's control with the rule-breaking scripted policy
that amendment (g.5) §A already ratified, so editing a persona pack no longer
breaks the detection machinery.** Proven end to end: with all six packs
genuinely edited, all 89 detection-corpus tests pass, where 24 previously
failed.

**No new amendment was needed.** (g.5) §A already states that the finale deck's
single control is the rule-breaking bot and that the T1 dial config is demoted
to an off-deck diagnostic. This was code catching up to a ruling, not a fresh
protocol decision.

**Why this is a structural fix rather than a re-pin.** The old control was a
counterfactual *on* the shipped packs, so its identity depended on them and any
routine bot change became a protocol event. The new control is defined by its
own policy code and runs against whatever packs ship. That mirrors how benchmark
suites separate concerns — the workload stays frozen while the system under test
varies freely, and the system's identity is recorded beside the result rather
than embedded in the benchmark.

**Disclosure, carried in the code as well as here:** the T1 diagnostic that
(g.5) §A retains becomes unavailable once the packs change, because its config
describes packs that no longer exist. Re-deriving it against a changed roster
would change what the diagnostic *is*, so it is deliberately left alone. Nothing
in the finale depends on it.

**T2b, T3, T4 and T5 are unblocked.** T2b still needs the value rework the theory
review asked for (recorded below); T3, T4 and T5 are ready to start.

### Original blocker write-up, kept for the record

**Any change to a persona pack's content breaks the S6 detection machinery, and
un-breaking it is an owner decision rather than a code fix.** This was found by
running T2's pack values through the suite: 24 tests in
`tests/test_detection_corpus.py` fail, all from one root cause.

`docs/ai-dlc/specs/flywheel-s6-control-config.json` is a preregistered protocol
artifact. It carries a `base_pack_hash` declaring which persona packs it was
authored against, and `tools/counterfactual.load_config` refuses the config
when that hash no longer matches the loaded packs — correctly, since the config
describes a counterfactual on packs the engine is no longer running. A second
pin, `PROTOCOL_CONTROL_CONFIG_HASH` in `tools/detection_corpus.py`, fixes the
config's own hash.

The mechanism is behaving exactly as designed. The question is what should be
re-pinned and by whom, and it is genuinely governance-shaped:

- The ratified amendment (g.5) §A **removes this T1 dial control from the
  finale deck entirely** and keeps it only as an off-deck diagnostic, so the
  finale does not need it re-derived against the improved roster.
- The shakedown tree it belongs to is closed history that the amendment says is
  never reused.
- But the corpus builder refuses to build *anything* while the shipped config
  is stale, so the code must acknowledge the roster moved.

**Not resolved autonomously.** Re-pinning a preregistered protocol artifact, or
narrowing the check that guards one, is a protocol act. The options — mark the
shipped config explicitly historical, re-derive it against the final roster, or
scope the protocol check to runs that actually use it — differ in what they
claim about the finale, which is exactly the kind of decision the amendment
reserves.

**Consequence for the plan: T2 splits.** T2a ships the mechanism with no pack
values, which is byte-identical and green. T2b authors the values and is
blocked. T3, T4 and T5 are all pack-content changes and are blocked behind the
same decision.

## T2a — Preflop raise-size variation, mechanism only ✅

**Do:** Add optional weighted size mixes to `PersonaSizing` and draw from them
in `preflop_raise_to`, with no pack authoring any mix yet.

A weighted mix of enumerated sizes, not a jittered scalar. Sampling and then
clamping into a legal range piles probability mass on the clamp boundary —
recreating a determinism at exactly the value neither gate can see — and for a
lever already outside the range it collapses every draw onto the boundary,
shifting the centre rather than adding variance. Enumerating the permitted
sizes makes both impossible, keeps every value inside hero's grading bands by
construction, and keeps sizes at numbers a person would actually pick.

**Acceptance (met):** shipped packs author no mix, so behaviour is
byte-identical; `rng=None` and mix-absent both fall back to the scalar; a
duck-typed sizing object without the new fields still works; malformed mixes
are rejected; the action draw remains the first RNG call; a seeded draw is
reproducible; grading-band constants are pinned against the grader so a drift
there fails here. 22 tests.

**Done-condition:** `./scripts/verify.sh`

**Owns:** `backend/app/domain/table/sizing.py`,
`backend/app/domain/content/models.py` (`PersonaSizing`),
`content/schema/persona.schema.json`,
`backend/tests/test_preflop_size_mix.py`.

## T2b — Preflop size values (BLOCKED, and the drafted values need rework)

Blocked by the protocol pin above. Separately, the theory review passed the
T2a mechanism but returned NEEDS-WORK on the drafted numbers — fortunate
timing, since they had not shipped. The rework below is required first.

**1. Draw conditioned on seat, not i.i.d. per decision (HIGH).** The central
finding. A per-decision coin flip from a persona-global menu trades one machine
signature — a constant — for another: noise correlated with nothing a human
conditions on. Measured over a 4,000-hand export, 77–90% of every persona's
opens come from seats whose canonical open is 3.0bb, and this repo's own model
of a realistic ladder is already position-conditional (`scenarios.py:63-72` —
3.0 early, 2.5 late). The drafted mixes would emit 2.5bb UTG opens at 20–35%,
which no competent full-ring TAG does.

The fix is the idiom T4 already applies to the `vs_rfi` nodes: thread
`position` into `preflop_raise_to` and key the mix by seat. Regulars (tag, lag,
nit) get a low-entropy seat table — roughly 0.85 on the seat's canonical size
plus a small off-size rung — which yields the ~80/20 aggregate the flat mix was
reaching for, but earned rather than asserted. Recreationals (station, fish,
maniac) stay seat-blind with genuinely wider menus, because a player who does
not adjust to position **is** the archetype, and that is the cheapest realistic
source of size variety on the table. This inverts the draft's intuition:
recreationals vary more; regulars vary by seat.

**2. Narrow the maniac's open to {4.0: 0.30, 4.5: 0.70} (HIGH).** The draft
drops its mean from 4.5 to 4.15 on the persona defined by maximal aggression
and on the highest-volume lever measured (1,080 opens per 4,000 hands). Worse,
20% of its opens would land at 3.5 — the station's own modal open — making one
maniac open in five size-indistinguishable from the table's most passive seat.
This also corrects a claim of mine: at a lever already on the cap, one-sided
variance and mean preservation are arithmetically incompatible, so the mix
design does not make a centre shift *impossible*, only *authored*. The honest
statement is that a real maniac's open variance runs upward — 5x, 6x, jam — and
the grading cap forbids expressing it, so this persona gets the least realism
per unit of risk.

**3. Drop the 3.5 rung from tag, lag and nit; consider a 2.8 3-bet rung
(MED).** The "≤4.5bb" band is `_OVERSIZE_OPEN_CAP`, which governs only the
hero-facing-an-open gate — the outer envelope cited as though it were the whole
rule. At the vs-4-bet node the villain opener's open must additionally be at
most `_STD_OPEN_CAP` = 3.0, so moving 20–25% of those personas' opens to 3.5
makes those hands ungradeable and **reduces hero coverage**, which spec §7.1
forbids. The seat-conditional design removes the rung anyway.

The mirror image is a win worth banking: at the vs-3-bet node the cap is 3.5 ×
the *canonical* open, so when hero opens 3.0 from a 2.5-canonical seat the cap
is 8.75 and every shipped multiplier (all ≥3.0) is ungradeable. A 2.8 rung for
tag and nit would create hero coverage that does not exist today (2.8 × 3.0 =
8.4 maps; 3.0 × 3.0 = 9.0 does not).

**4. Record the size-blind defence gap (MED).** Preflop response keys on the
raise *count*, never the size (`_preflop_facing`), so once sizes mix,
fold-to-open becomes flat across sizes by construction — a new machine tell
created by the fix. Engine work is out of scope by the ruling, so do not build
size-aware defence: keep the spread narrow (a second argument for the
low-entropy regular design) and record the gap beside the maniac 4-bet
exclusion. Escalate only if a measurement shows it is detectable.

**5. Give every weight provenance, and add a histogram report (MED).** All 48
weights are bare numbers. Nothing downstream can falsify one — the weight *is*
the frequency, so the mix is self-fitting, and both gates are blind to sizing
by construction. Attach a one-line source per lever, or say `[UNVERIFIED]` out
loud as the contract's provenance duty requires, and add a non-gating report to
acceptance printing each persona's realised open-size histogram, its mean, and
the delta against the shipped scalar, so centre shifts are visible rather than
inferred.

**Confirmed sound by the same review:** the discrete-mix-over-jitter choice;
identity preserved for five of six personas (only the maniac moves); the nit
reading tighter-but-bigger is correct poker; and cross-persona size overlap
does **not** damage separation, because the floor scores ten frequency
statistics and sizing is not among them. Its guidance is to stop treating
sizing as an identity axis at all — a TAG and a LAG are separated by how often
they open, not by how much.

## T2 — Preflop raise-size variation (superseded by T2a/T2b above)

**Do:** Give each persona's open, iso, 3-bet and 4-bet a distribution instead
of a single number.

- Optional jitter fields on `PersonaSizing`; mirrored in
  `content/schema/persona.schema.json`. Omitting them is byte-identical to
  today.
- `preflop_raise_to()` takes an optional `rng` and **draws from a pre-truncated
  valid interval** — never a symmetric draw followed by a clamp (spec §6.2).
- At-cap levers draw one-sided downward: maniac `open_bb` 4.5; tag, lag and nit
  `threebet_mult` 3.5; tag and lag `fourbet_mult` 2.4.
- The maniac's `fourbet_mult` (3.0, already above the 2.4 cap) is **excluded**
  and left exactly as shipped.
- A second bound against the grading caps, distinct from the existing
  `_clamp` on the engine's legal bracket.

**Do not:** insert any draw before the action draw; touch
`RECOGNIZED_BET_FRACS` or any grader; retune the merit constants.

**Acceptance:** spec §7.1 in full, plus positive test 1 — each opted-in lever
produces at least two distinct non-forced sizes over a seeded sample, with
bounded mass at any interval boundary and forced jams excluded. Packs omitting
the fields stay byte-identical.

**Done-condition:** `./scripts/verify.sh && python -m tools.derobo_gate --check`

**Owns:** `backend/app/domain/table/sizing.py`,
`backend/app/domain/content/models.py` (`PersonaSizing` only),
`content/schema/persona.schema.json`, the `sizing` block of the six packs.

---

## T3 — Range-edge softening

**Do:** Replace hard 100%/0% weights at the *edge* of each persona's preflop
ranges with mixed weights, so marginal hands are sometimes played and sometimes
not. Core holdings keep their current probabilities.

**Critical mechanic (spec §6.4):** mixes are scanned first-match-wins and combo
overlap is not validated, so a softer mix appended *after* an existing hard mix
covering the same hands is dead code that fails silently. Edge mixes must be
ordered ahead of the hard mix, or the hard mix's combo set narrowed. T1's
shadowing test is the guard.

**Do not:** widen or narrow what a persona fundamentally plays — this is about
the boundary's sharpness, not the range's size. Do not touch core combos.

**Acceptance:** spec §7.1, plus positive tests 2, 3 and 6 — every declared edge
combo is strictly between 0 and 1, no mix is shadowed, and non-edge combos keep
their current probabilities. Separation floor must hold; if it fires, the
softening widths come down.

**Done-condition:** `./scripts/verify.sh && python -m tools.derobo_gate --check`

**Owns:** the `preflop` block of the six packs (edge mixes).

---

## T4 — Positional response gradients

**Do:** Split the wildcard `vs_rfi`, `vs_limpers`, `vs_3bet` and `vs_4bet`
nodes (`positions: None`) into position-aware nodes, so a persona stops
answering identically from every seat. This is the mechanism behind the
measured flat constants — tag folding to a raise at ~83% from every seat, nit
at ~94%, the station's seat-blind defence.

**Do not:** omit a seat. Node validation does not require complete coverage and
an omitted seat silently folds 100% (spec §6.5); T1's completeness test is the
guard.

**Acceptance:** spec §7.1, plus positive test 4 — coverage is complete and
named position pairs produce genuinely *different* action vectors, which is the
whole point of the split. Separation floor must hold.

**Done-condition:** `./scripts/verify.sh && python -m tools.derobo_gate --check`

**Owns:** the `preflop` block of the six packs (node structure). Sequenced
after T3 because both edit that block.

---

## T5 — Postflop sizing ecology

**Do:** Re-weight each pack's existing on-grid pot-fraction distributions so the
0.5 fraction has real presence table-wide and the maniac has a small size at
all — today its menu is 0.75/1.0/1.5 only, which is the measured "82.5% large
or overbet" tell.

**Do not:** add any fraction outside {0.33, 0.5, 0.75, 1.0, 1.5}; introduce
continuous jitter; touch `RECOGNIZED_BET_FRACS`, `_CANON_BET_TOL`, or any
grader. Continuous postflop jitter would silently un-map hero's turn and river
lines — the `T-cover` defect.

**Acceptance:** spec §7.1, plus positive test 5 (grid membership) and the
coverage ratio explicitly checked, since this ticket is the one that could
plausibly move it. Separation floor must hold — sizing is a strong persona
fingerprint and flattening it too far is the realistic way to fail this gate.

**Done-condition:** `./scripts/verify.sh && python -m tools.derobo_gate --check`

**Owns:** the `postflop` block of the six packs.

---

## Pull-request packaging

| PR | Tickets | Theme |
|---|---|---|
| PR-0 | T0, T1 | Measurement and guardrails — must merge first |
| PR-1 | T2 | Preflop raise-size variation |
| PR-2 | T3, T4 | Preflop range de-determinization |
| PR-3 | T5 | Postflop sizing ecology |

Each PR carries its own gate output and coverage ratio in the description. Per
the tiered review policy: PR-0 and PR-1 (behaviour-touching code) get the
`refuter`, Codex Sol, and the `persona-realism-theory-reviewer`; PR-2 and PR-3
(pack data) get the `refuter` and the theory reviewer, with Codex on PR-3
because the sizing ecology is where the separation floor is most at risk.

## Slice close-out

After all four PRs: run the five-seed gate set, record the combined result and
the final coverage ratio in the ledger, and tick the slice in the roadmap. Do
**not** run any paid detection judging — the finale is owner-only and
single-shot by the ratified amendment.

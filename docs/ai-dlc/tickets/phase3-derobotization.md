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

## T2 — Preflop raise-size variation

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

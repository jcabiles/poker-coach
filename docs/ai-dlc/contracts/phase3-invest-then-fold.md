# Contract map — invest-then-fold (improvement slice 2)

**Bottom line: two of the three planned changes are safe by construction, and one
of them knowingly breaks a safety argument the code states in prose and no test
enforces. Ticket T1 extends a damp that is currently scoped to "facing a raise"
precisely so it never touches the curve an existing contract measures — and the
test that guards that curve hardcodes one opponent, so it cannot see the new
multiway case at all. Ticket T2 must move two halves of one mathematical law
together or a frozen-vector test will fail in a way that looks like a routine
re-record. Nothing in the slice can orphan SRS history or reach the grader.**

Scope: `backend/app/domain/personas_postflop.py`, the three touch points named in
`../tickets/phase3-invest-then-fold.md`. Produced by a read-only scout with no
sight of the spec's conclusions; persisted by the session because the scout had
no write access.

## Who calls this code

`sample_postflop_decision` has exactly two production callers plus one harness,
and **none of them defaults `opponents` or omits `street`** — every one derives
both from live state. That is what makes T1 and T3 safe at the caller boundary.

| Caller | Location | Notes |
|---|---|---|
| Live table loop | `table/play.py:182` (`_postflop_decision`, via `bot_decision`) | Passes every keyword explicitly. No defaults taken. |
| Villain-range estimator | `table/range_estimate.py:387` (`_postflop_action_dist`) | Omits `is_aggressor` and `context` only, both documented as harmless. Passes the real `opponents`, `street`, `facing_raise`. |
| Statistical harness | `test_personas_postflop.py:2077` (`_play_hand`) | Mirrors `play.py`'s derivation exactly, by that module's own instruction. Derives `opponents` live. |

The analytics export, the detection corpus builder, and the probe policies all
route through `play.bot_decision`, never calling the sampler directly. That
matches the caller map in `phase3-derobotization.md`, which is still accurate.

Only bare unit-test helpers default `opponents` to 1 — and those are exactly the
tests that pin the behaviour T1 changes. See the risk below.

## Risk 1 (HIGH) — T1 breaks a prose-only safety argument, untested

`personas_postflop.py:253-258` argues, in a comment and nowhere else, that the
naked-ace float damp is safe **because** it is gated on `facing_raise`: the
α-ceiling contract is measured over a facing-a-**bet** curve, so a
facing-a-**raise** gate is off the measurement node by construction and every
facing-a-bet decision stays byte-identical.

**T1 deliberately removes that property.** Extending the predicate with
`or opponents > 1` puts the damp onto facing-a-bet nodes for the first time —
the exact case the comment says is structurally excluded.

The guard is `test_personas_postflop.py:6700`
(`test_ace_high_facing_a_bet_is_byte_identical`), and its `_w3r6_dist` helper at
`:6557` **hardcodes `opponents=1`**. It will keep passing after T1 while the
property it was written to protect no longer holds.

This does not mean T1 is wrong. It means T1's safety has to be re-established by
measurement rather than inherited from the old argument, and the comment at
`:253-258` must be rewritten rather than left standing as a false claim.

## Risk 2 (HIGH) — T2 must move both halves of the bluff-size law together

The bluff-size law is deliberately two-stage:

- **Stage 1**, `personas_postflop.py:899-914`, scales `bluff_mass` — which feeds
  the action-level RAISE merit — by the expected `_bluff_size_factor` over the
  **authored** `sizing_dist` keys.
- **Stage 2**, `:1370-1383`, tilts the size draw by the same factor, again on the
  authored key, and only afterwards clamps the result to the stack.

T2 moves stage 2 onto the stack-capped effective size. **If stage 1 is not moved
with it, the module's own comment says the two stop being a joint law**, and the
action-level bluff frequency silently diverges from the sizes actually drawn —
including in the villain range the player is shown.

The tripwire is `test_price_tail.py:301`
(`test_alpha_ceiling_sub_anchor_vectors_are_byte_identical`), which asserts exact
equality against `HEAD_VECTORS`, a table of full-precision floats encoding stage
one's present authored-key computation for the calling station and passive fish
across AIR and ACE_HIGH.

**The trap is in that test's own docstring**, which explains that bet-size tickets
are expected to move these vectors. A genuine stage-1/stage-2 mismatch will
therefore present as a routine re-record. Any vector change in this slice must be
justified against the joint law, not waved through.

**Supporting evidence that T2 is directionally right:** `size_bucket`'s docstring
at `:65-67` already states the RES-E bucket must be computed on the live
pot-fraction and **never** on the discrete authored sizing keys. Stage 2 is
currently on the wrong side of that rule, and T2 fixes it — which is also why
leaving stage 1 on authored keys would put *it* on the wrong side.

## Risk 3 (MEDIUM) — CORRECTED: a T2 fault CAN corrupt the displayed villain range

**Corrected 2026-08-19 after PR #199 measured the opposite of what this section
claimed. The original text is kept below because a ticket criterion inherited its
error.**

The half that is true: `_CaptureRng.choices()` at `range_estimate.py:357-361`
returns `population[0]` on its first call and is never invoked again, so **the
sizing draw never executes under estimation**.

The half that was false: concluding from that "T2 therefore cannot corrupt the
displayed villain range". **That reasoning covers stage two of the bluff-size law
only.** Stage one runs *before* the action draw and scales `bluff_mass`, and the
action merit vector is precisely what `_CaptureRng` records — so a stage-one
change reaches the estimator directly. Risk 2 above says as much in its own
words, "including in the villain range the player is shown", so this map
contradicted itself and the slice followed the wrong half.

Measured during T2's build, on the repricing that was later withdrawn: the
estimator builds BET and RAISE with `max_bb=None` while stage one read that
field, so the range shown to the player kept the old pricing while the live bot
used the new one — overstating a short-stacked bot's air by 1.25× to 1.45×, at
nodes that are 13.0 percent of all bluff-cell aggressive nodes.

**The error propagated.** Ticket acceptance criterion 6 read "No estimator test
can catch a fault here, so do not rely on one", which pointed the build away from
the one test that would have caught it. The estimator's own parity tests were
structurally blind for the same reason: both sides of every comparison built the
same capless bracket. PR #199 fixes that with
`test_no_aggressive_bracket_field_is_read_before_the_action_draw`, which drives
its live side from `engine.legal_actions` at a real short-stack node.

**The original text, for the record:** "T2 therefore cannot corrupt the displayed
villain range — and equally, no estimator-side test can detect a T2 fault. Its
only protection is `test_price_tail.py`'s frozen vectors and the live-bot suite."

## What is safe, and why — checked, not assumed

- **Estimator parity for T1 and T3 is structural, not merely tested.**
  `range_estimate._postflop_action_dist` calls the same sampler with the real
  `ctx.opponents`, `ctx.street` and `ctx.facing_raise`, and `_CaptureRng`
  short-circuits only the action draw — which is downstream of both predicates.
  Exact-equality parity tests already exist at `test_range_estimate.py:515`
  (river, air, no draw) and `:574` (facing a raise, naked ace-high). **Neither
  drives more than one opponent**, so they catch general divergence but not a
  multiway-specific T1 fault.
- **SRS history cannot be orphaned.** `srs.py:48-68` hashes villain type,
  position, street, facing and stack bucket. No strength bucket, no merit, no
  bluff-cell state. None of the three changes reaches it.
- **The grader is uncoupled.** `grade_map_postflop.py` does not import
  `personas_postflop`; its only mention is a comment about an unrelated rounding
  tolerance.
- **The bet-size grid is untouched.** T2 reweights probability among sizing keys
  that are already authored and already on `RECOGNIZED_BET_FRACS`. It introduces
  no new size, so the grid conflict escalated to the owner is not engaged.
- **The pre-existing multiway fold mechanism does not collide with T1.**
  `_MW_CATCH_TIGHTEN ** max(opponents - 1, 0)` at `:969-970` already applies to
  ACE_HIGH among other buckets, but `test_mw_catch_toppair.py`'s fixtures never
  probe ACE_HIGH — so it neither conflicts with T1 nor protects it.

## What this map adds to the tickets

Two acceptance criteria that were not in the ticket file before this scan, both
folded in: T1 must re-establish the α-ceiling property at more than one opponent
facing a bet and rewrite the stale comment; T2 must move stage 1 and stage 2
together and justify any `HEAD_VECTORS` movement rather than re-recording it.

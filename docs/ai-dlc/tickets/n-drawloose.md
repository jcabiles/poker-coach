# N-DRAWLOOSE — tickets (rev 2, option B)

**Status:** approved · Gate 2 cleared by the owner 2026-08-04, with both rulings taken as
recommended (R1 escalate-don't-attribute · R2 re-record + disclose the ratio).
**Base:** `b0a6a4e` · **Spec:** `docs/ai-dlc/specs/n-drawloose.md`
**Order:** strictly serial, T1 → T7. Nothing parallelises: each ticket reads a suite state
the previous one changes, and this slice is the sole fixture recorder while open.
**Owned files:** T1 owns `backend/app/domain/personas_postflop.py` alone. T2/T3/T4/T7 own
disjoint regions of the test tree and land serially anyway.

Rev 1's tickets were failed by both reviewers. The mutants each ticket must now kill are
listed because reviewers demonstrated them, not because they were imagined.

---

### T1 — the engine change (three coupled sites)

Implement the branch form from spec §2 at `:979`, `:1098` and `:1247`.

**Acceptance**
- **Branch, never re-associate.** Non-STRONG paths keep the literal
  `(call_base + _DRAW_CALL_BONUS[draw]) * looseness`. Re-associating shifts 17 WEAK cells by
  1 ulp, and this repo has lost 6 of 23 frozen price vectors to a 1-ulp residue before
  (`:1204-1207`, ledger R2-1).
- The `:1098` damp must subtract exactly what `:979` added, **on both** `call_merit` and
  `_call_merit_at_ref`. If they diverge the damp mis-removes, and there is no clamp there.
- `rscale` keeps the literal `looseness / ref` expression on the non-STRONG branch — this is
  what leaves `test_price_tail.py`'s 23 bit-exact vectors untouched.
- Guard `_call_merit_at_ref > 0.0` before dividing.
- No `content/` file is touched.

**Done-condition:** `ruff check .` clean; full suite shows exactly the four failures in spec
§5 and no fifth.

### T2 — prove the raise-leg coupling is real

The N-LOGIT invariance gate (`test_personas_postflop.py:7135-7188`) stays **unmodified and
unscoped** — under option B it passes, and it is now the thing that catches a
half-implementation. Add a gate proving the new `rscale` branch is *exercised and
non-trivial*.

**Acceptance**
- Assert that on a strong-draw node `rscale != looseness / continue_ref` (i.e. the branch
  was taken and changes the value), and that on a draw-NONE node it is exactly equal.
- Assert the invariance gate still measures ≥1000 comparisons per persona after the change —
  its existing thin-measurement guard. Do not assume it survived.
- **Named mutants this must kill:** (a) ship T1's call-side change with `rscale` left frozen
  → the invariance gate fails on draw cells; (b) apply the coupling on *all* draws rather
  than STRONG only → the draw-NONE equality assertion fails.
**Done-condition:** both mutants demonstrated red, the shipped form green.

### T3 — G-DRAW: the dial stops deciding strong draws

Five correctly-priced strong-draw facing nodes; nit at 0.45 against the same pack rebuilt at
0.60; self-difference ≤ **0.030**.

**Acceptance**
- Nodes: D1 combo draw flop ⅔-pot · D2 flush draw flop pot · D3 combo draw turn ½-pot ·
  D4 flush draw flop ½-pot 4-way (`opponents=3` — **label it four-way**; rev 1 called it
  three-way) · **P1 middle pair + flush draw**.
- **P1 is not optional.** Bucket and draw are independent axes
  (`personas_postflop.py:752-756`) and rev 1's panel sat entirely on the AIR/ACE_HIGH side.
  Record P2 (top pair + flush draw) as a **record, not a pin**: at HEAD it is +0.0134,
  already inside the cap, so it cannot carry redness.
- Price with `pot_bb = pre_bet_pot + to_call` and `latest_aggressor_contribution_bb =
  to_call`, and assert the fraction the **engine** computed equals the declared one — reuse
  the `_r9lf_priced_dist` pattern. Do **not** use `_dist_for_pack` (no contribution
  parameter; trips a legacy denominator branch). Include a companion test proving the price
  assertion itself fires on a mislabelled node — it caught two of the director's own nodes
  this slice.
- **Declare prices as exact ratios** (`4.0/6.0`), never rounded decimals.
- State `0.030`'s provenance: it is a **chosen budget**, not derived. The 0.071797 log-odds
  ceiling that justifies G-NODE's 0.040 does **not** transfer, because the draw-node continue
  merit is no longer proportional to the dial. Attach the floor sweep from T4's evidence.
- ⚠️ **D3 is a turn node and knowingly pins in current turn behaviour.** Comment that
  `N-DRAWTURN` is expected to invalidate it, so a future slice does not read it as settled.

**HEAD (red):** +0.0682 · +0.0678 · +0.0693 · +0.0628 · +0.0380.
**Shipping variant:** +0.0040 · +0.0164 · +0.0041 · +0.0146 · +0.0097.
**Done-condition:** red at HEAD on all five; green after T1; and a comment confirming
G-DRAW, G-NODE and T4's level band are mutually independent.

### T4 — C2: the absolute level band (a cap alone is level-blind)

Two-sided band at the trace node: nit P(fold) ∈ **[0.20, 0.34]**, measured 0.2768.

**Acceptance:** a sensitivity cap does not bound how loose the bots become. Measured floor
values of 0.6, **2.0 and 5.0** all satisfy G-DRAW; 5.0 more than doubles every persona's
strong-draw bonus and loosens even the calling station, and nothing else catches it because
T5 re-records the moved fixtures. Add a `calling_station` **byte-identity pin** on a
strong-draw node in the same ticket — under the branch form the station is structurally
unchanged, and rev 1 had no gate saying so.
**Done-condition:** red at HEAD (0.4217 is outside the band); green after T1; red against a
`floor = 5.0` mutant.

### T5 — fixture re-records

Re-record `_GOLDEN_STATS_N200` (observed: `calling_station` AF 0.32778 → 0.36676) and
`_PRE_M3_FIRES` (observed: UTG2¹ **74 → 70**).

**Acceptance:** attribution proven by revert in **both** directions; a dated chain entry at
each constant. Compute the OLD side from the **fixture**, never from the prose chain — five
records have been lost that way. Expect movement in personas this slice never touches: all
six share one seeded rng stream.
**Done-condition:** both green; **no third fixture moved** — if one did, stop and
investigate; it is a defect, not a re-record.

### T6 — the two rulings

Apply whatever the owner rules at Gate 2.

**R2 / coverage.** `total` 1288 → 1233 (the *first* assertion, "hand stream drifted"), graded
335 → 323, graded **share up 26.01 % → 26.20 %**. Re-record `coverage_baseline.json` and
disclose the ratio as the honest metric. ⚠️ Rev 1's T5 asked the builder to "measure which
three graded decisions were lost" — **that task does not exist**; 246 of 400 hands change
shape, and there is no set of three.

**R1 / fish band.** Do **not** write provenance attributing the breach to this slice: the
unchanged engine breaches its own floor on 2 of 8 reseeds, and the paired effect is mean
−0.0020 with the sign flipping twice. Recommended remedy is the R10-TAIL-a1 precedent —
escalate to a stable sample before failing. Whatever ships, the OVERBET row must still pass
and no other band row may move.

### T7 — the stale-statement sweep

Correct every comment the change falsifies:
- `personas_postflop.py:763-776` — quotes the old `call_merit` line verbatim and reasons from it.
- `:1186-1231` — the N-LOGIT cancellation derivation. Under option B the guarantee still
  holds; the *mechanism* text is now wrong and must describe the coupled `rscale`.
- `:1204-1207` — the "re-syncing `continue_ref` collapses `rscale` to 1.0" note, now
  interacting with a second `rscale` branch.
- **`test_personas_postflop.py:9839-9840`** — G-NODE's own docstring, which states the
  same-factor property as the justification for its 0.040 constant. It now holds only for
  draw-NONE, and the 0.071797 ceiling is derived from it. **Rev 1's list missed this**, which
  is exactly the class its own warning named.
- `_R9LF_PANEL`'s docstring ("both continue merits scale by the same factor s").
- **NEW, raised by T1's implementer — the `_c_now` read has zero explanation in code.**
  `rscale` divides the **live post-damp** CALL entry by `_call_merit_at_ref`. That choice is
  what keeps the dial inert on SPR-committed nodes, and it silently requires the N-LOGIT
  block to sit **below** the commit block. Comment both facts at the site. Also note that
  R9-DEFENCE-a's line damp cannot contaminate `_c_now` only because that damp is gated on
  `draw is NONE` (`:1181`) — if that gate is ever widened to draws, `line_mult` would be
  applied to RAISE twice.

**Acceptance:** `grep -rn "call_base + _DRAW_CALL_BONUS"` and `grep -rni "same factor"` across
`backend/` — every hit corrected or explicitly justified.
**Done-condition:** no comment in the tree asserts an invariant the engine no longer holds.

---

## Fan-in

`refuter` + Codex Sol (`gpt-5.6-sol`) on the diff, plus `persona-realism-theory-reviewer`,
all **git-READ-ONLY**. Brief the theory reviewer explicitly on: the pair-plus-draw quadrant,
the WEAK draws left deliberately on the dial, and whether entrenching a constant raise:call
ratio (TH-5) is acceptable — that is the known cost of option B and the theory reviewer is
the right check on it.

**Suite target:** 1419 + the new gates, green; ruff clean; BACKEND VERIFY OK.

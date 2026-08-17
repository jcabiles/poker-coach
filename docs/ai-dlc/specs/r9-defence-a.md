# R9-DEFENCE-a — delta spec (rev 2)

**Slice of:** `docs/ai-dlc/roadmap/persona-realism.md` (item `R9-DEFENCE-a`, design-pass adjudication
`:1626-1642`). **Design pass (accepted, owner 2026-07-31):** `docs/ai-dlc/reports/r9-defence-design.md`.
**Base:** `origin/main` `8cc6c38` — verified green `1386 passed, 1 skipped`, pytest exit 0, read unpiped.
**Prerequisites:** `R9-SIGNAL` (#141) · `N-logit` (#163 + #164). Both verified present at base.

> **rev 2 supersedes rev 1.** Rev 1 was reviewed by `refuter` (Opus) and Codex Sol concurrently; **both
> returned FAIL**. Neither found a defect in the mechanism — both broke the *gates*, by different routes,
> and both routes worked. A no-op implementation passed **11 of rev 1's 12 criteria**. Fourteen findings
> accepted; full adjudication in `docs/ai-dlc/ledger/r9-defence-a.md`. Every change below traces to one.

---

## 1. Goal

A bot facing a wager from the same seat that also bet or raised on the **previous postflop street**
continues less often. Freed mass goes to FOLD; the raise:call ratio at that node is left invariant.

## 2. The defect

Postflop decisions carry no memory of the opponent's line: a bot facing a turn bet behaves identically
whether that same opponent bet the flop (a second barrel) or checked it. Measured at base, the deviation
between those two worlds is exactly `0.000000` — the signal exists and nothing reads it. This is an
**arrival** defect: the policy at the node is defensible; the node's *history* never reaches it.

## 3. Mechanism

### 3.1 The formula

At a facing-chips node, with assembled merits `F` (fold), `C` (call), `R` (raise):

```
line_mult = exp(−λ_p · g(line))            λ_p ≥ 0,  g(0) = 0,  g(1) = 1
C' = C · line_mult
R' = R · line_mult
                        ⇒ logit P'(continue) = logit P(continue) − λ_p · g(line)
```

**`λ_p = _LINE_DELTA · pf.line_sensitivity`, with `_LINE_DELTA = 1.0`** *(R-1)*.

The value is **pinned, not inherited.** Two independent checks fix it: at `1.0` the reference-node effect
reproduces the design pass's own predicted table (nit / `MIDDLE_PAIR`: `ΔP(fold) = +0.131` measured vs
`+0.1312` predicted); at `0.25` it gives `+0.030`, which does not. It is also the only value at which §5's
`le = 2.0 ⇒ continue-odds cut ≥ 7×` is true. Rev 1 left it unstated and a no-op passed almost the whole
harness — do not "mirror" it from another constant.

`line = 0` reproduces today's vector exactly. `line_sensitivity` unset ⇒ `λ_p = 0` ⇒ `line_mult == 1.0`
exactly ⇒ **bit-identical** (`m * 1.0 == m` bitwise).

### 3.2 Raise-neutrality, and what it does and does not exclude

Scaling **both** defend merits by one factor inside the single existing normalization leaves the
conditional raise share untouched:

```
P'(raise | continue) = R·line_mult / (C·line_mult + R·line_mult) = R / (C + R)
```

**A `call_merit`-only multiplier CANNOT pass this** — that is precisely the N-LOGIT misroute, which sends
freed mass to RAISE.

**A `fold_merit`-only implementation CAN pass it, and every other behavioural gate** *(R-2)*. It is
*projectively identical*: `normalize(F, C·s, R·t·s) = normalize(F/s, C, R·t)`. Both reviewers measured this
to bit equality. Rev 1 claimed otherwise and was wrong. **No output-space test can distinguish the two
forms.** The C/R-only form is therefore prescribed for auditability — the fold merit stays an untouched
input, which keeps the A1 no-fold-floor guardrail inspectable — and it is enforced **structurally on the
raw merits before normalization** (§7 P-1), never behaviourally.

### 3.3 Attach point and composition with N-LOGIT

**Inside the facing-chips branch** — the mechanism applies **only** when `ActionType.FOLD in by_kind`
*(R-7)*. This gate is part of the mechanism, not commentary: the region between the SPR block and the
normalization sits at **function-body indentation**, i.e. the common path shared with unopened
(`CHECK+BET`) and matched-with-option (`CHECK+RAISE`) nodes — which is exactly why N-LOGIT re-guards with
its own `if ActionType.FOLD in by_kind:` at `:1066`. An implementation that omits the gate would scale the
RAISE entry on check-raise shapes.

**Position:** after the SPR-commit / B5b block (ends `:1007`) and before the N-LOGIT raise scale
(`:1059-1068`), which precedes the single normalization (`:1070-1076`) and the action draw (`:1076`; the
sizing draw is `:1088` *(R-13)*).

The justification is simply **"inside the facing branch, before the single normalization."** Rev 1 also
argued "after the commit block, because B5b subtracts absolute quantities" — that argument is **moot**
under §4's scope predicate and has been withdrawn *(R-6)*; see §4.

**Composition with N-LOGIT — commutes.** Final entries: `(F, C·line_mult, R·rscale·line_mult)`. Both are
scalar multiplies on entries before one normalization, so coded order cannot change the result:

```
P(raise|cont) = R·rscale·line_mult / (C·line_mult + R·rscale·line_mult) = R·rscale / (C + R·rscale)
```

`line_mult` cancels — N-LOGIT's orthogonality survives this slice and this slice's raise-neutrality
survives N-LOGIT. Both reviewers searched for a counterexample (river polar-bluff cell, committed path,
`max(m, 0.0)` clamp, zero-total fallback) and **neither found one**. Still gated (§7 S-4), because a future
edit could move one multiply across the normalization — and gated **against the production transform**, not
against algebra recomputed inside the test *(R-12)*.

### 3.4 The signal (shipped — do not rebuild)

`aggressor_barrel_run(...)` at `table/postflop_context.py:152-200`, shipped by R9-SIGNAL **with** all three
amendments the design pass demanded (postflop-only; consecutive-not-cumulative; flat sampler kwarg).
`sample_postflop_decision` already accepts `aggressor_bet_prev_street: bool = False` (`:732`) and records
that nothing reads it (`:753`). Production derives and threads it (`table/play.py`).

**Design-pass §8 risk 1 is therefore CLOSED** — mark that section stale. `g(line)` in v1 is the identity on
that boolean. **Re-deriving the run rule anywhere is forbidden** — the docstring at `:185-186` explicitly
warns against a second taxonomy.

## 4. Scope

**Predicate — explicit, and gated** *(R-6)*:

```
bucket ∈ {MIDDLE_PAIR, TOP_PAIR, ACE_HIGH, AIR}  AND  draw is DrawCategory.NONE
```

Rev 1 listed buckets and draw categories in one column and never defined the product. They are
**independent axes** (`personas_postflop.py:33-51`), so `MIDDLE_PAIR` *with* a flush draw — a common cell —
was undefined.

| Excluded | Reason |
|---|---|
| `MONSTER` | `_FOLD_BASE[MONSTER] = 0.0` ⇒ `P(fold) = 0` everywhere. Inclusion would be a documented no-op. |
| `TWO_PAIR_PLUS` | `P(fold)` 0.007–0.036 roster-wide. No room, and two pair does not fold to a barrel. |
| `OVERPAIR_TPTK` | The bucket **bundles** true overpairs (AA on K-high — must never fold to a barrel) with TPTK. Damping it damps real overpairs. **Pre-registered** behind W3R-7's bucket split. |
| any `draw ≠ NONE` | **Reason corrected — see below.** Out because `_DRAW_CALL_BONUS[WEAK]` is the un-equity-gated F7 defect and stacking an un-calibrated line factor on an already-inflated call merit compounds it (the W3R-5 #2 mistake). STRONG draws out pending joint calibration. **Pre-registered as v2, now dependent on F7's equity gate landing first.** |

> **CORRECTED (theory review, 2026-08-03 — ledger R-26).** Rev 2 excluded draws because "a draw's continue
> is already priced by equity + the T1 threshold, and that machinery already moves with street." **Both
> limbs are false for the CALL leg.** `call_merit = (call_base + _DRAW_CALL_BONUS[draw]) * looseness`
> consults no equity and no street — `_DRAW_CALL_BONUS` is a flat lookup `{NONE: 0.0, WEAK: 0.20,
> STRONG: 0.55}` — and the street-decay machinery cited (`_STREET_WEAK_DRAW_MULT`, `_DRAW_RAISE_BONUS`) is
> **aggression-side only**. Measured: a naked gutshot's `P(call)` facing a half-pot bet goes **UP** flop →
> turn (nit `0.3556 → 0.3696`), not down. Verified independently against the code.
>
> **The exclusion stands; only its reason was wrong.** **Known consequence, disclosed rather than
> discovered:** a nit facing a second barrel now continues **more** with a naked 4-out gutshot (`0.4224`)
> than with ace-high (`0.3932`) — the ordering was the other way round before (`0.4224` vs `0.5415`).
> Directionally a gutshot does gain against a narrowed range; what is unrealistic is that its response to
> the line is **exactly zero** while every no-draw class moves.

**Consequence of the predicate, stated because rev 1 got it wrong** *(R-6)*: for every in-scope bucket,
`made = _RUNG[bucket] >= _RUNG[OVERPAIR_TPTK]` is False (in-scope rungs are 0–3; the threshold is 4) and
`drawing` is False. So `value_commit` is **always False** and the B5b branch never runs on an in-scope cell
(`:983-1007`). Therefore **`_commit_transform` and B5b can never co-occur with this mechanism.**

Rev 1 described SPR-committed nodes as a "declared no-reach zone" and pinned it. That framing was wrong:
the mechanism is scoped **away** from those nodes, not inert on them — and a gate on a combination that
cannot occur always passes. Replaced by the out-of-scope byte-identity pin (§7 P-2), which is a real gate.

**Node kind:** any facing-chips node (bet or raise). No within-street leg — that axis already carries two
landed `facing_raise`-gated damps, and a third un-calibrated factor there is the W3R-5 collision.
**Required:** where both fire (facing a turn *raise* from a seat that bet the flop), document the joint
product and show the α-relevant nodes untouched.

**Street:** the mechanic reads no street variable. `line = 0` on the flop is a property of the **signal**
(the run loop over preceding postflop streets is empty on the flop), which keeps this slice outside the
roadmap's `street → scalar` prohibition. Note the honest limit *(R-11)*: the sampler takes an unconstrained
boolean, so a **direct caller** can pass `True` with `street=FLOP`. The guarantee lives with the derivation,
not the sampler — and the sampler is deliberately left honest rather than given a street check, which would
reintroduce the forbidden term.

**Jams:** OUT. A jam is byte-identical to a min-raise at the same price; discriminating needs a new signal
off `legal` (`min_bb == max_bb`) with its own parity obligation. v1 treats a jam as the raise it legally is.

## 5. The lever

```python
line_sensitivity: float | None = Field(default=None, ge=0.0, le=2.0)   # PersonaPostflop
```

- **Authored in pack JSON, never a code constant** — the S4 mechanics/identity split.
- **Bounded explicitly at `le=2.0`.** Precedent is `position_sensitivity`, whose reviewers forced an
  explicit bound — that bound is `1.0` *(R-14)*; the precedent is for *bounding*, not for the number. At
  `_LINE_DELTA = 1.0`, `λ_max = 2.0` cuts continue-odds ≥ 7×, a safe ceiling with the fitted region well
  inside.
- **Absence is the opt-out; explicit JSON `null` is rejected** — follow `_continue_ref_authorship` /
  `_stickiness_authorship`, which key on `model_fields_set` (key presence, not value).
- **A runtime guard is required** where λ is computed: `model_copy(update=...)` bypasses validation and the
  suite uses that idiom routinely.

**Seed ladder — DIRECTIONAL, with one declared tie tier** *(R-10)*:

```
nit 0.60  >  tag 0.50  >  { lag 0.35 ≡ passive_fish 0.35 }  >  maniac 0.20  >  calling_station 0.10
```

Ordering is **strict between tiers, equal within the braced tier.** Rev 1 demanded strict monotonicity over
a ladder containing an authored tie — unsatisfiable.

The station's near-zero is **the archetype, not a leak**: a line-blind call-down is its defining trait.

> **CORRECTED (theory review, 2026-08-03 — ledger R-27). The maniac's seed was justified by a channel v1
> does not have.** Rev 2 said "the maniac contests a barrel rather than folding to it, and its reaction
> lives in the raise share, which this slice deliberately does not touch." That is true of
> `P(raise | continue)` and **false of `P(raise)` absolute.** Because both defend merits are scaled
> together, absolute raise frequency FALLS at every in-scope cell. Measured at the reference node, and
> reproduced independently:
>
> | | line=0 | line=1 | Δ |
> |---|---|---|---|
> | maniac, AIR | 0.2853 | 0.2513 | **−0.0341** |
> | lag, AIR | 0.1793 | 0.1385 | **−0.0408** |
> | tag, AIR | 0.1140 | 0.0767 | −0.0373 |
>
> On the **river polar-bluff cell** (`call_merit` floored to 0) there is no call leg at all, so the
> mechanism acts as a **pure bluff-raise suppressor**: maniac 0.2041 → 0.1735, lag 0.1230 → 0.0900.
>
> So the shipped behaviour is "the maniac and the LAG contest a sustained barrel **less** often than a first
> stab" — the wrong sign for the two archetypes whose character is to contest. **This is a documentation
> defect, not a behaviour defect:** raise-neutrality of the *ratio* is the deliberate safety property
> (§3.2), and boosting the raise leg is stage-2, i.e. `R9-DEFENCE-b`, pre-registered do-not-build.
>
> **Honest v1 statement, replacing the struck justification:** the maniac's line response in v1 is a small
> uniform continue shrink. Its contest-the-barrel reaction is **deferred to `R9-DEFENCE-b`**, and until then
> `0.20` is a floor chosen to minimise the wrong-signed raise-side side effect — **not a fitted contest
> rate**. The measured deltas above are recorded here so `R9-DEFENCE-b` inherits the numbers rather than
> re-deriving them.

Seeds are **DIRECTIONAL FIT SEEDS** — settable from the closed-form inversion against a stated
continue-rate change at a named reference node, never dropped in, never fit to a per-street aggregate. **No
HARD per-persona target** may be asserted: no provenance row exists for fold-to-second-barrel, and gating on
a level without one is the DIRECTIONAL-gating the project forbids.

## 6. Owner decisions (Gate 1, 2026-08-02)

1. **The realism harness gets the signal; the pinned measurements do not change.** The harness's local
   `_postflop_decision` wrapper (`tests/test_personas_postflop.py:1914`) threads no line signal in either
   `context_aware` state, so the population run cannot observe this mechanism at all — leaving §7 S-5
   unfalsifiable. Thread it, keep every existing band and golden statistic **byte-identical** (signal off by
   default), and add a **paired line-aware vs line-blind run**.
   **Buildability correction** *(R-4)*: `_persona_stats` uses a single `random.Random(20260710)` **both** to
   draw each hand seed and as the action RNG inside `_play_hand` (`:2524-2538`), so the moment play changes,
   the deal sequences diverge. The paired run therefore **requires pre-generated immutable hand seeds from a
   dedicated deal RNG**, with every non-line input held identical across arms. Without that it measures deal
   noise.
2. **The villain-range estimator is IN scope.** `range_estimate.py` does not thread the flag, and `_Ctx`
   (`:92-129`) tracks aggression only *within* the current street, resetting at each transition. **Sizing,
   after reconciling both reviewers** *(R-16)*: `PublicAction` (`:66-76`) already carries `street`,
   `position`, `action` — the three fields `aggressor_barrel_run` reads — so the shipped derivation is
   **reusable as-is**. The genuinely missing piece is one tracked value: the current street's aggressor
   **seat**. Budget it as *reuse + one tracked value*, and **do not re-derive the run rule**.

## 7. Acceptance criteria

Two classes, and the distinction is load-bearing *(R-5)*. Rev 1 demanded RED-FIRST of every criterion,
including pins that are green at base by construction — which is incoherent and invites weakening a pin
until it fails.

- **S-gates (SENSITIVITY)** — must be demonstrated **RED at the red reference**, with the failure recorded
  in the PR. These are the proof the change does something.

  > **Build-stage correction (2026-08-02, T4).** "Every S-gate must be RED" is **unsatisfiable for S-2 and
  > S-3**, and demanding it would corrupt them. Both compare the anchor against the *tuned* point; with the
  > engine untouched those are the same vector, so "continue mass did not collapse" and "the raise share did
  > not move" are trivially TRUE there. Their teeth are on **mutants**, which is the job §10.4 gives them —
  > and measured: S-3 catches the `call_merit`-only misroute, S-2 catches the `C'=R'=0` collapse.
  > **Amended rule: an S-gate must be falsifiable by EITHER a red reading at the red reference OR a named
  > mutant it demonstrably kills.** Falsifiability is the requirement; red-at-base was only ever a proxy
  > for it. A gate that can do neither is vacuous and must be rebuilt.
- **P-pins (REGRESSION)** — must be **GREEN at base and stay green**. Never re-record, never widen.

**Grid definition (required, was undefined in rev 1):** the cell grid is the product of
`{MIDDLE_PAIR, TOP_PAIR, ACE_HIGH, AIR} × {NONE} × {flop, turn, river} × {HU, 3-way} × {faced fractions
0.25, 0.5, 0.75, 1.5} × {SPR 1, 4, 20} × legal shape ∈ {FOLD+CALL, FOLD+CALL+RAISE}`, over all six packs.
Axes are published in the test module.

### S-gates

**S-1 — the identity breaks, with a floor.** At `MIDDLE_PAIR` and `TOP_PAIR`, HU, SPR ≥ 10, facing a BET at
a fixed fraction, the `line = 1` vector differs from `line = 0` with `P(fold)` strictly greater, for every
persona with `line_sensitivity > 0`. **Plus a minimum effect size at a named reference node, written as a
literal**: nit / `MIDDLE_PAIR` / turn / HU / SPR 20 / faced 0.5-pot ⇒ `ΔP(fold) ≥ 0.05` *(R-1)*. The floor
must **not** be derived from `_LINE_DELTA` — a self-referential assertion passes at any magnitude, which is
how a `1e-12` no-op passed rev 1. Measured with `latest_aggressor_contribution_bb` supplied.

**S-2 — anti-collapse, on both ends** *(R-3)*. Continue mass must be strictly positive and finite at the
anchor **and** at the tuned point. Rev 1 constrained only the anchor, and a mutant setting `C' = R' = 0`
from a non-degenerate anchor passed both S-1 and rev 1's anti-collapse gate. No cell may be skipped
silently: skip counts are reported and floored per persona.

**S-3 — raise-neutrality.** `P(raise)/(P(call)+P(raise))` invariant between `line = 0` and `line = 1` to
`1e-9`, over every grid cell **with strictly positive continue mass at both ends**. Cells where `C + R = 0`
— reachable in scope, since the river `bluff_cell` hard-zeroes `call_merit` (`:884-885`) and RAISE is
appended only when legal — are **excluded here and pinned separately as inert** by P-5 *(R-3)*.

**S-4 — the lever is the shift, and composition commutes.** `logit P(continue|line=0) − logit
P(continue|line=1)` equals `λ_p` to `1e-9` at every finite-interior cell. Assert in **odds space, not
probability space** — the probability-space ordering differs from the λ ordering because base continue rates
differ. Ordering is **strict between tiers, equal within `{lag, passive_fish}`** *(R-10)*. Include a
**sweep over multiple `line_sensitivity` values, including `model_copy`-injected ones**, so a hard-coded
per-persona response table cannot pass. Composition: with `continue_ref` authored, the two scales commute to
a **relative tolerance of `1e-12`, not bit-equality** *(R-8)* — measured, `(R·k)·s` vs `(R·s)·k` differs
bitwise 34.9% of the time, so exact equality would fail a correct implementation. Exercise the **production
transform**, not algebra recomputed in the test *(R-12)*.

**S-5 — paired population sensitivity** *(R-4)*. Over pre-generated immutable hand seeds from a **dedicated
deal RNG**, with all non-line inputs identical across arms and an asserted **occurrence floor** (minimum
barrel nodes encountered) below which the comparison is not reported.

> **Build-stage correction (2026-08-02, T5 — OWNER-RULED). The original "showdown frequency falls by
> ≥ 0.01" literal was measured FALSE and is retired.** It was set a priori by the spec author before
> anything was measured. T5 measured the true effect at four sample sizes; at `N = 24000` the asymptote is
> nit `−0.0121` · lag `−0.0072` · tag `−0.0061` · passive_fish `−0.0043` · maniac `−0.0031` ·
> calling_station `−0.0023`. Five of six never reach 0.01, and nit only marginally.
>
> **This is not a mechanism defect.** Measured at the barrel node in the same run, fold rate rises in clean
> ladder order: nit `+0.054` · tag `+0.048` · passive_fish `+0.036` · maniac `+0.030` · lag `+0.023` ·
> station `+0.003`. Showdown frequency is simply a heavily diluted read of it — 2,074 in-scope barrel nodes
> across 4,000 hands × 9 seats, only 37 of them nit's.
>
> **Ruling: gate on the DIRECT measure, not the diluted shadow of it.**
> - **S-5a (decisive)** — population **fold rate at barrel nodes**, mechanism on vs off: strictly positive
>   for every persona with `line_sensitivity > 0`; **literal floor `nit ≥ 0.03`**.
>
>   **Ordering — amended (Codex fan-in, ledger R-28).** Rev 2 required "strict between tiers, equal within
>   `{lag, passive_fish}`". Organic play does not support that and the build correctly declined to assert
>   it: the `{lag, fish} > maniac` edge is unstable (at `N=4000` maniac beats lag outright; only at
>   `N=16000` does the λ order return), and the braced tie's members carry equal λ, not equal spot mixes.
>   **Amended requirement: assert the coarse order that IS stable at every N measured —
>   `nit > tag > {lag, passive_fish, maniac} > calling_station` — and document the unasserted edge.** The
>   λ-exact ordering claim lives where it is true: at a fixed node, in odds space (S-4). Buying the missing
>   edge with a bigger N is forbidden — it trades honesty about the population for a number.
>
>   **NOT node-matched — label corrected (Codex fan-in, ledger R-29).** The arms share a pre-generated seed
>   schedule, and flop arrivals are asserted equal (the mechanism cannot fire before the turn), but after
>   the first differing action the trajectories diverge: measured in-scope node counts differ slightly
>   between arms (e.g. tag 86/85, passive_fish 270/268). An earlier ledger entry called this "node-matched";
>   it is **seed-paired, end-to-end**. The measurement remains valid — the effect (nit `+0.1463`) dwarfs the
>   ≤1% node-count difference — but the stronger claim was not earned and has been withdrawn.
>   The `0.03` is a **floor with headroom, NOT a fitted value**, and the module must say so: the closed form
>   gives nit a reference-node effect of `+0.131` (design-predicted, reproduced at `+0.131190`), organic
>   play necessarily averages that over a spot mix, and `0.03` sits ~1.8× below the measured `+0.054` while
>   far above any no-op. **The unfitted decisive effect-size gate remains S-1's literal `0.05`** at the
>   reference node — a number that matched a prediction made before any of this was measured.
> - **S-5b (directional companion)** — showdown frequency falls strictly, floored at `0.002`;
>   `|Δ| ≤ 0.005` for `calling_station`. Labelled a population-**consequence** check, not an effect-size
>   gate. The retired `0.01` literal stays recorded beside it with the evidence that killed it.

**S-6 — estimator parity, with discriminators** *(R-9)*. The parity fixture must contain at least one node
with `aggressor_barrel_run(...) >= 1`; the estimator's distribution there must **differ** from the
line-blind one; and the derived flag must equal the shipped derivation node-for-node under four
discriminators: **same-seat true · different-seat false in multiway · broken consecutive line false · flop
false**. Without these, an estimator that always passes `False`, or one reading "any aggression last
street", passes while being wrong.

### P-pins

**P-1 — structural: only CALL and RAISE raw merits change.** Assert on the **raw merits before
normalization** that the FOLD entry is bitwise unchanged and CALL/RAISE are scaled by one common factor. No
output test can do this *(R-2)* — the fold-side form is projectively identical.

**P-2 — out-of-scope cells are byte-identical** between `line = 0` and `line = 1`: every excluded bucket,
every `draw ≠ NONE`, and every non-facing node (unopened `CHECK+BET`, matched-with-option `CHECK+RAISE`)
*(R-6, R-7)*.

**P-3 — flop byte-identity via the production derivation** *(R-11)*: every flop facing node as production
derives the flag, the balanced-villain α fixture, and the fold-to-first-c-bet computation, unchanged
bit-for-bit. Pin the derivation's flop-zero property directly rather than asserting a sampler property the
flat kwarg does not have.

**P-4 — default-off byte-identity + rng order.** `line_sensitivity` unset ⇒ identity across the full grid;
the flat kwarg defaults `False`; the **action draw stays the first `rng.choices`** (`:1076`; sizing `:1088`)
— the mechanism adds no rng call.

**P-5 — zero-continue cells are inert.** Where `C + R = 0`, the vector is unchanged between `line = 0` and
`line = 1` *(R-3)*.

**P-6 — `tests/test_price_tail.py` untouched.** Its 23 frozen exact-equality vectors stay green **without
edit** (doubly protected: default-off and flop-scoped). **If you find yourself editing that file, STOP —
the implementation has diverged from this spec.**

**P-7 — no band exits, no re-anchoring.** Existing `BANDS` and golden statistics **byte-identical** — if any
moves, the harness threading leaked into the default path, which is a defect, not a re-record opportunity.
Fold-to-first-c-bet untouched by construction; AF node-neutral by construction. **If any pinned band exits,
STOP and escalate to W4-b** — do not widen a band, do not re-scope a test.

**P-8 — coverage delta** reported against the immutable snapshot (anti-laundering rule).

**P-9 — version bump** on every edited pack, gated by a per-pack version floor.

## 8. Out of scope

No jam discriminator · no `OVERPAIR_TPTK` or draw-class response (pre-registered v2 / behind W3R-7) · no
within-street action-kind leg · no OVERBET price tail (`R10-TAIL`(a)) · no multiway continue-threshold
change (`R10-TAIL`(b) owns the headcount exponent — **`λ_p` must not be fit to compensate for either**) ·
no river air-call absolute (`N-riverair`) · no stage-2 raise-share line term (`R9-DEFENCE-b`, pre-registered,
**do not build**) · no frontend change.

**Fixture classes — rev 2 correction, owner-ruled 2026-08-02.** Rev 2 originally said "no fixture
re-records" flat. That was too broad and conflated two different things:

- **NEVER move.** `tests/test_price_tail.py`'s 23 frozen exact-equality vectors · the population `BANDS`
  (AF / fold-to-c-bet / WTSD) · the golden persona statistics. A move here is a defect; escalate, never
  re-record. (P-6, P-7 stand unchanged.)
- **Documented per-slice re-pin protocol.** `tests/test_coverage_baseline.py` and
  `tests/test_limper_coverage_belt.py` record how bots play a fixed deal sequence. Any authorized
  bot-behaviour change displaces the shared seeded rng stream and moves them by construction; both files
  carry an explicit re-record convention with 11+ precedents. **Owner ruling: re-pinning these two is
  authorized for this slice** (ticket T2b), under the protocol those files themselves define — attribution
  proven by revert, every coverage shape verified still firing, dip reported not laundered.

**Graded-coverage dip — owner-ruled 2026-08-02: flag, do not block.** More realistic villains steer hero
into a different mix of spots, and the (unchanged) mapper grades that mix slightly less: 27.70% → 26.01%.
This is mapper-track movement, owned by `T-cover`, not a persona-realism regression — the same adjudication
the last several slices made, and the same magnitude as `R10-PRE2` (28.0% → 26.3%). Record it in the ledger
and the PR; do not couple this slice to grader work.

## 9. Constraints

`backend/app/domain/` takes no web/DB imports (test-enforced) · results are frequency + EV, never boolean ·
strategy lives in versioned `content/` data · `spot_signature()` frozen · grading stays behind the one async
`StrategyProvider` · no auth/hosting.

**Git:** worktree off fresh `origin/main`; never commit in the shared tree; push by immutable OID, bare, no
pipes; never push `main`; never merge (owner only). **Reviewers are GIT-READ-ONLY.** **Pin every review
sub-agent to base explicitly** — a `contract-mapper` in this slice mapped a stale tree and reported the
prerequisite as missing *(S-0.1)*.

**Never read a suite result from a piped exit code** — redirect to a file and read the file.

## 10. Verify-by

1. `./scripts/verify.sh` → `BACKEND VERIFY OK`. Suite run **unpiped** (`pytest -q > out.txt 2>&1; echo $?`),
   result read from the file. Base: `1386 passed, 1 skipped`.
2. `cd backend && ruff check .` clean.
3. **RED-FIRST evidence for every S-gate**, captured at base and pasted into the PR. P-pins are shown
   **green** at base instead.
4. **Counterfactual mutants, each shown to FAIL:** (a) `line_mult = 1.0` forced — the literal no-op;
   (b) `_LINE_DELTA = 1e-12` — the no-op that passed 11 of rev 1's 12 criteria; (c) a `call_merit`-only
   multiplier — the N-LOGIT misroute; (d) `C' = R' = 0` — the continuation collapse that passed rev 1's
   anti-collapse gate; (e) a fold-side implementation — must pass every behavioural gate and be caught by
   **P-1 alone**; (f) scaling every bucket regardless of scope — caught by P-2. A harness that passes any of
   (a)–(d) or (f), or that catches (e) anywhere but P-1, is broken.
5. Fan-in review before merge: fresh `refuter` + `persona-realism-theory-reviewer` + Codex Sol, all
   GIT-READ-ONLY, all pinned to base. Every finding reproduced before accept/reject; every accept **and**
   reject recorded with reasoning in `docs/ai-dlc/ledger/r9-defence-a.md`.

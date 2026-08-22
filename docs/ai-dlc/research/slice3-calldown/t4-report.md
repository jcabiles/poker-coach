# S3-T4 — the α fold ceiling extended over ace-high on the river

**Bottom line. The guard extension ships, and it ships RED BY DESIGN: naked
ace-high breaks the α fold ceiling at every one of the 24 heads-up river cells,
for all six personas, by between 27 and 64 percentage points. That is a finding
about the engine, not a tuning problem, so the new test is marked as a strict
expected failure — a one-way compliance tripwire that pins no number, stays quiet
while the breach persists, and turns the suite red the day the river becomes
compliant. **The theory review of this ticket then found that the obligation
itself is mis-specified**: α bounds how often the defender's WHOLE RANGE folds
and says nothing per hand class, and a whole-range probe shows the per-bucket
reading is wrong in both directions on ace-high at once (§6). That is filed, not
resolved, and if the owner re-rules the new test should be DELETED rather than
fixed. The conditional
half of the ticket, re-deriving `_ACE_HIGH_RIVER_CALL_DAMP`, DOES NOT FIRE: the
headroom condition needs the calling station and the LAG each 5 percentage points
down on the band harness and they are 0.95 down and 0.41 UP, shortfalls of 4.05
and 5.41 points. The re-derivation is filed as a follow-up with those numbers, and
no engine constant moved.**

Plain-language glossary for this document, given once. **S3-T4** is ticket 4 of
improvement slice 3 ("calldown") of the bot-realism flywheel — the initiative
that is trying to make the practice bots play like people. **α (alpha)** is
`f/(1+f)`, the share of the time a hand whose only job is to catch bluffs may
fold facing a bet of `f` times the pot before the bettor's bluffs become free
money; it is a CEILING on folding and never a floor. **Naked ace-high** is an
ace with no pair and no draw. **Went-to-showdown** is the share of hands a
persona takes to showdown out of the hands where it saw the flop. The **band
harness** is the pinned six-persona population inside
`backend/tests/test_personas_postflop.py`, and it is the gating instrument for
this slice. **`_ACE_HIGH_RIVER_CALL_DAMP`** is the single engine constant that
governs how much naked ace-high calls on the river; it ships at 0.06 and this
ticket does not change it.

Branch `feat/slice3-t4-alpha-acehigh`, now rebased onto `abcfd97` (the merge of
S3-T3, pull request #216). It was BUILT on `4f653ef` (the merge of S3-T2, pull
request #215) rather than waiting on the serial chain, and that is safe rather
than a shortcut: #216 changed no engine file and no shared test file — it added
`backend/tools/capped_composition_probe.py` and its own test, and withdrew its
lever — so every number in this report is measured against an engine that #216
left untouched. The rebase produced one conflict, in the shared slice ledger,
and none in code.

## 1. What pull request #204 left undone, and what this ticket closes

#204 shipped the 2026-08-19 owner ruling's **instrument**. The owner ruled that
α binds the ACE_HIGH strength bucket, closing a question the engine had been
reporting rather than settling. #204 built the measurement helper
(`_measure_ace_high_fold_by_size`), published the full violation map
(`../slice2-invest-then-fold/alpha-acehigh-ruling.md`), and pinned exactly one
assertion: `test_ace_high_alpha_holds_for_the_station_pre_river`, covering the
calling station on every street BEFORE the river.

Three things were deliberately left open there, and S3-T4 closes all three.

| left open by #204 | closed here |
|---|---|
| The **river** call leg carried no assertion at all — §6 of the ruling document declined to pin the violated cells. | `test_ace_high_river_alpha_ceiling`, six personas heads-up, marked `xfail(strict=True)`. §3 below answers §6's two objections rather than overruling them. |
| No **non-vacuity** proof existed for any α assertion on this bucket — the station test passes, but nothing showed it was capable of failing, and nothing showed a failing assertion would be capable of passing. | `test_ace_high_river_alpha_guard_is_not_vacuous`, proving both directions on the same assertion body (§4). |
| The **stale engine prose** was disclosed and not fixed. `personas_postflop.py` still said "WHETHER α SHOULD BE ASSERTED OVER ACE-HIGH AT ALL IS AN OPEN QUESTION referred to the owner", which the ruling had already made false. #204 shipped no engine diff, so correcting it fell to the next ticket to touch the file. | Two comment blocks corrected, at the `_CALL_BASE` block and at the river call branch. **Comment-only: not one non-comment line of the engine changed**, verified by diff filter. |

## 2. The measurement — every heads-up river cell breaches α

Measured at this file's own α node: n = 1,250 naked-ace-high spots
(`StrengthBucket.ACE_HIGH` with `DrawCategory.NONE`), pot-before-bet 6bb, 100bb
stacks, deal seed 20260721, per-cell decision seed
`20260721 + 100·persona_index + frac_index`, heads-up, `street=RIVER`.

| persona | ⅓-pot (α .2481) | ½-pot (α .3333) | pot (α .5000) | 1.5×-pot (α .6000) | worst margin |
|---|---:|---:|---:|---:|---:|
| maniac | 0.5176 | 0.7264 | 0.8336 | 0.9024 | **+0.2695** (⅓-pot) |
| calling_station | 0.5584 | 0.6520 | 0.7520 | 0.7936 | +0.3187 (½-pot) |
| lag | 0.6392 | 0.8048 | 0.8848 | 0.9336 | +0.4715 (½-pot) |
| tag | 0.7600 | 0.8928 | 0.9328 | 0.9664 | +0.5595 (½-pot) |
| passive_fish | 0.7640 | 0.9072 | 0.9368 | 0.9648 | +0.5739 (½-pot) |
| nit | 0.8872 | 0.9624 | 0.9736 | 0.9864 | +0.6391 (⅓-pot) |

**24 of 24 cells breach, and none of them is close to the wall.** The smallest
breach in the whole table is the maniac facing a third of the pot, +26.95
percentage points, about 19 binomial standard errors at the measured rate and
n = 1,250. No reseed and no sample-size change can flip this verdict, which is
why the expected-failure mark is safe to make strict.

**Where the α law actually lives**, stated because an earlier draft of this
report cited the wrong home. α as a fold ceiling is the **RES-D A1 guardrail** —
implemented on the grader side as `_calibrate_catcher_fold` and asserted on the
bot side by `test_fold_to_bet_respects_alpha_ceiling` (RES-D §1c/§2 invariant 3).
It is NOT theory contract §9 item 1: that item is the separate 60% → 42.9%
correction about the 3×-pot semi-bluff threshold. The only thing §9 item 1
usefully offers here is an arithmetic coincidence worth noting and not citing as
authority — it happens to record that 60% is the α ceiling for a 1.5×-pot bet,
which is the last column's `1.5/2.5 = 0.6000` exactly.

**Two rows moved since #204 measured them, and both moved the WRONG WAY.** This
is a real cost of the calldown slice and it is stated here rather than left for
a reader to diff:

| persona | #204's ⅓-pot river fold | this tip | move |
|---|---:|---:|---:|
| nit | 0.8432 | 0.8872 | **+0.0440** |
| tag | 0.6800 | 0.7600 | **+0.0800** |

S3-T2 cut the nit's `call_looseness` from 0.45 to 0.32 and the TAG's from 0.6 to
0.38 to bring their went-to-showdown rates down. A tighter calling dial also
folds naked ace-high more often, so the same retune that bought the slice its
showdown reduction spent α headroom on this bucket. The other four rows
reproduce `alpha-acehigh-ruling.md` cell for cell.

## 3. Why a strict expected failure, when the ruling document declined one

`alpha-acehigh-ruling.md` §6 refused an expected-failure pin on two grounds, and
the shape shipped here answers both rather than arguing with them.

The result is a **one-way compliance tripwire**. Say the one-way-ness plainly:
**this test cannot detect the breach WIDENING.** Every one of the 24 cells could
climb another twenty points and it would still report a quiet XFAIL, exactly as
it does today — the widening S3-T2 already caused (§2's nit +0.0440 and TAG
+0.0800) was caught by the measurement below, not by the test. Gating the
widening would need a second, level-pinning instrument, and this slice
deliberately did not build one, because §6 puts the whole per-bucket obligation
in question.

**Objection 1: it would entrench the violation as the engine's specification.**
Answered by `strict=True`. A strict expected failure goes RED when it starts
passing. The day a persona's whole river row falls under α, that leg reports
XPASS and the suite fails, so the engine cannot quietly become correct and
nobody can mistake the mark for a specification. This was verified rather than
assumed: setting `_ACE_HIGH_RIVER_CALL_DAMP` to 5.0 in the engine file and
running the guard produced **six FAILED legs**, one per persona, and the constant
was reverted immediately afterwards.

**Objection 2: a one-sided ratchet over sixty-odd cells is a re-record burden on
every future slice.** Answered by granularity and by pinning no number. The mark
sits on the TEST, one leg per persona — six legs, not sixty cells — and the
assertion contains no recorded value. Every cell may move as far as it likes in
either direction with no re-record here. Only crossing a persona's whole river
row into compliance changes the verdict, which is precisely the event a fix
wants announced.

**Scoped heads-up, on purpose.** α = `f/(1+f)` is a heads-up identity. In a
multiway pot the minimum-defence obligation is SHARED between defenders, so a
single defender's admissible fold rate is strictly ABOVE `f/(1+f)` and this
ceiling is not the right bound there — the same multiway caveat already recorded
with `_ACE_HIGH_RIVER_CALL_DAMP` in the engine. The station test asserts α at two
and three opponents as well; that is conservative and it happens to pass, and
this leg does not take the same conservatism.

**AIR's zero is untouched.** The engine's river branch still sets AIR's call merit
to exactly 0.0. This ticket does not read it, assert on it, or move it; the range
filter is `StrengthBucket.ACE_HIGH` alone. Acceptance criterion 2 is met on both
halves.

## 4. The non-vacuity proof, and a direction correction

**The ticket asks for the wrong direction, and the substance it wants is proved
in both.** S3-T4's text asks for a non-vacuity proof by "deliberate damp
INFLATION beyond what α allows". Inflating this damp cannot breach α: the damp
multiplies the CALL merit, so raising it LOWERS the fold rate and moves the roster
toward the ceiling's compliant side. α bounds folding and therefore places no
upper bound on calling at all. What the ticket actually wants — the guard is not
passing, or failing, by construction — is asserted here in the two directions
that exist, on the same `_ace_high_river_alpha_breaches` body the guard uses.

| leg | scratch damp | result | binding cell |
|---|---:|---|---|
| **The guard trips** on a damp move α forbids | 2.5 | 6 of 24 cells still over α; the nit's leg trips | nit at 1.5×-pot, 0.6704 vs 0.6000, **+0.0704** (≈5.3 binomial standard errors) |
| **The guard can pass** — so its failure at 0.06 is evidence about the engine, not about the fixture | 5.0 | 0 of 24 cells over α; every persona's leg is clean | nit at ½-pot, 0.2632 vs 0.3333, **−0.0701** of headroom |

Both scratch values are set with `monkeypatch` and undone inside the test, which
then asserts the shipped constant is still 0.06.

**Where full compliance actually sits, measured rather than inherited.** The
roster crosses into 0-of-24 between a damp of 3.5 (1 cell over — the nit at
½-pot by +0.0003) and 3.6 (0 over, −0.0069 of headroom).

| damp | cells over α (of 24) | worst margin |
|---:|---:|---|
| 0.06 (shipped) | 24 | nit ⅓-pot +0.6391 |
| 1.0 | 19 | nit ½-pot +0.2875 |
| 2.0 | 9 | nit 1.5× +0.1208 |
| 2.5 | 6 | nit 1.5× +0.0704 |
| 3.0 | 2 | nit ½-pot +0.0307 |
| 3.5 | 1 | nit ½-pot +0.0003 |
| **3.6** | **0** | nit ½-pot −0.0069 |
| 5.0 | 0 | nit ½-pot −0.0701 |

`alpha-acehigh-ruling.md` put that crossing near 3.0 before S3-T2. The nit's and
the TAG's tighter calling dials pushed it up to 3.6 — the same +0.044 and +0.080
movement §2 records, priced in the currency of the constant. **The compliance
point is now roughly 60 times the shipped 0.06**, and the frozen went-to-showdown
bands already refused 0.45, which is 7.5 times it. That is the arithmetic the
ruling-versus-bands reconciliation needs, it got worse this slice, and it remains
the owner's to settle.

## 5. The conditional re-derivation does NOT fire

**Owner ruling 7 of 2026-08-22 requires the calling station AND the LAG each at
least 5 percentage points DOWN on the band harness against the `d351150`
baseline. Neither clears it, and the LAG moved the wrong way.**

The ruling lives in the machine-local owner rulings file
`local/session-2026-08-22/rulings.md`, which is gitignored, so it is quoted here
in full rather than only cited: *"7. S3-T4 headroom condition: station AND lag
each >=5pp down on band harness vs d351150 baseline (71.1 / 57.3)."*

Measured on the band harness at its pinned seed (`random.Random(20260710)`) and
its stable sample (`_WTSD_ORDER_N` = 4,000 hands) at this branch's tip, which
reproduces main's post-S3-T2 numbers exactly:

| persona | `d351150` baseline | this tip | change | condition | shortfall |
|---|---:|---:|---:|---|---:|
| calling_station | 0.7105 | 0.7010 | **−0.95pp** | ≥ 5.00pp down | **4.05pp short** |
| lag | 0.5728 | 0.5769 | **+0.41pp** (UP) | ≥ 5.00pp down | **5.41pp short** |

For completeness, the other four at the same tip: nit 0.6173, tag 0.5528, maniac
0.5945, passive_fish 0.5204.

**So the re-derivation is not attempted, and is not forced.** The amendment
draft's §III.2 sets the same bar from the other side — it licenses raising the
damp only once Stage 2 has brought the station and the LAG down toward their
grounded bands (38–48 and 26–31), where the roughly 2.7 points of LAG headroom
and 1.9 points of station headroom the damp needs exist with a wide margin.
Neither persona is anywhere near those bands: the station is 22.1 points above
the top of its band and the LAG is 26.7 points above the top of its own.

**Three further reasons the re-derivation should not be forced today**, taken
from §III.2 and confirmed by §4's sweep:

1. The damp pushes showdown frequency the WRONG way for this slice. Ace-high
   calling more rivers means more hands reaching showdown, which is the exact
   statistic slice 3 exists to reduce.
2. The compliance point moved AWAY this slice, from about 3.0 to 3.6. A
   re-derivation now would be re-derived against a distribution that S3-T2 just
   made worse, not against a settled one.
3. §III.2's ratchet forbids upward movement past a ceiling, so the amendment as
   ratified does not license raising the damp regardless of the measurement.

**One citation correction carried forward from §III.2, because a merged engine
comment gets it wrong.** That comment says "the theory contract attributes the
roster's showdown excess to flop and turn calldown". The contract's C6 note names
no street — its words are that the population is inflated because "price-blind
defense keeps too many pots to showdown". The flop-and-turn attribution belongs
to the flywheel slice-2 material, which is where the invest-then-fold defect was
measured. The conclusion is unchanged; the authority for it is the slice-2
measurement, and this document cites it that way.

## 6. Reviewer finding — α is a per-RANGE bound, not a per-BUCKET bound

**The persona-realism theory review of this ticket found that the obligation
S3-T4 was asked to enforce is itself mis-specified, and the measurement backs
it.** α = `f/(1+f)` bounds how often the DEFENDER'S WHOLE RANGE may fold. It says
nothing about how often any individual hand class inside that range may fold. The
2026-08-19 ruling, and therefore §2's test, apply a range-level identity to one
bucket — and on THIS bucket that is wrong in both directions at once, not merely
conservative.

**A whole-range probe at the same node**, uniform deal, five-card river board,
n = 2,000, seed 20260721. "Beats ace-high" is every strength bucket strictly
above `ACE_HIGH`.

| slice of the range | share |
|---|---:|
| beats ace-high (monster · two-pair-plus · overpair/top-pair-top-kicker · top pair · middle pair) | **0.5675** |
| naked ace-high | 0.1280 |
| air | 0.3045 |

Minimum defence frequency — the share of its range a defender must continue with
to stop bluffing being automatically profitable — is `1 − α`. So:

| bet | α | range must continue | supplied by hands beating ace-high alone | what α actually requires OF ACE-HIGH | what §2's test demands |
|---|---:|---:|---:|---|---|
| pot | 0.5000 | 0.5000 | 0.5675 | **nothing — ace-high may fold 100%** | fold ≤ 50.00% |
| 1.5×-pot | 0.6000 | 0.4000 | 0.5675 | nothing — same | fold ≤ 60.00% |
| ½-pot | 0.3333 | 0.6667 | 0.5675 | about 77% of ace-high must continue | fold ≤ 33.33% |
| ⅓-pot | 0.2481 | 0.7519 | 0.5675 | **about 100%, and even that is 5.6 points short — air must call too** | fold ≤ 24.81% |

**Wrong in both directions.** At the two large prices the test demands ace-high
fold under 50% and 60% while the identity permits folding it outright — too
STRICT. At the smallest price the test is satisfied by a 24.81% fold rate while
the identity demands ace-high continue essentially always — too LOOSE. A single
per-bucket number cannot be both.

**Why the one-pair catcher fixture escapes this and ace-high does not.** A
one-pair bluff-catcher sits AT the minimum-defence margin — it is the marginal
hand the range's last continuing units are drawn from — so its per-bucket rate
happens to coincide with the range's, and asserting α on it per-bucket is
defensible. Ace-high does not sit at that margin. The coincidence does not
transfer, which means `_CATCHER_BUCKETS`' original exclusion of ace-high was
right, though for a better reason than the one written beside it.

**This re-opens the ruling's provenance, under a rule this repository already
has.** The W3R-1 rule (theory contract §5a obligation 2) says that when a fit
cannot reach a target using a legitimate range or lever, the slice STOPS and
re-opens that TARGET's provenance — it does not widen the lever, widen the band,
or re-scope the test. S3-T4 is that case exactly: compliance needs a river call
damp near 3.6, sixty times the shipped 0.06, against the 7.5 times the
went-to-showdown bands already refused (§4). Under W3R-1 the infeasibility is
evidence about the target, and the target is the 2026-08-19 ruling.

**If the owner re-rules, `test_ace_high_river_alpha_ceiling` should be DELETED,
not fixed.** It would not be a guard measuring the wrong number; it would be a
guard measuring a quantity the contract does not bound, and softening or
re-scoping it is the precise dodge W3R-1 exists to stop.

**Nothing is resolved here.** This is filed as ledger item 10 and left open, and
so is the α-per-archetype defect at ledger item 2 that it reshapes — that item
asks whether a tight archetype may sit closer to the α wall, which presumes α is
a per-bucket bound; the prior question is whether it is one at all. Per owner
ruling 10 of 2026-08-22 the α assertion stays RAW, and S3-T4 did not touch it.

## 7. Follow-up filed

Recorded in `../../ledger/flywheel-slice3-calldown.md`, at the numbering this
branch carries after the rebase onto #216:

- **Filed 8** — re-derive `_ACE_HIGH_RIVER_CALL_DAMP` once the ruling-7 headroom
  bar is cleared, with the shortfalls above as the measured reason it was not.
- **Filed 9** — the 24-of-24 α river breach, at HIGH, for owner ruling.
- **Filed 10** — the per-range-versus-per-bucket contract defect of §6 above, at
  MEDIUM, filed beside filed 2 and reshaping it.

None of the three is resolved by this ticket.

## 8. Checks

| check | result |
|---|---|
| `./scripts/verify.sh` | **BACKEND VERIFY OK** — 2186 passed, 2 skipped, 6 xfailed (at the rebased tip; 2183 before the rebase, the three added tests being #216's own) |
| `cd backend && ruff check .` | All checks passed |
| `PYTHONPATH=. .venv/bin/python -m tools.derobo_gate --check --all-seeds` | GATE PASS, 5 of 5 seeds; binding separation 1.765554 against a floor of 1.254429 at seed 603 — identical to the S3-T2 reading, as it must be with no behavioural change |
| `pytest -k "alpha or persona_postflop_bands or wtsd_ordering"` | 55 passed, 6 xfailed (the six new river legs) |

**No fixture was re-recorded, and none was needed.** Nothing behavioural moved:
the engine diff is comment-only, no pack file was touched, and the de-robotization
gate reproduces main's separation figure to six decimal places.

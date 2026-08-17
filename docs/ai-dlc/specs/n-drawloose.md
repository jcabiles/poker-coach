# N-DRAWLOOSE — the archetype dial stops folding strong draws

**Status:** **rev 3 — BUILT AND SHIPPED** on `feat/n-drawloose`, 2026-08-05. Suite 1430
passed / 1 skipped / 0 failed, ruff clean, `BACKEND VERIFY OK`. Rev 2 was approved at
Gate 2, built, then **failed by all three fan-in reviewers**; rev 3 is what shipped.
· **Base:** `origin/main` = `b0a6a4e`
**Roadmap item:** `N-DRAWLOOSE`, owner-prioritised 2026-08-04 — build before any further
persona tuning, because every future archetype tightening makes it worse.
**Origin:** R9-LOOSEFIT theory fan-in, finding TH-1.
**Evidence:** `docs/ai-dlc/reports/n-drawloose-premeasurement.md`
**Adjudication:** `docs/ai-dlc/ledger/n-drawloose.md` — rev 1 was **failed by both reviewers**;
every number below is re-harvested from the variant that actually ships.

> **⚠️ Rev 1 is withdrawn.** It claimed the N-LOGIT raise-share invariant was
> unrecoverable, narrowed that gate on the strength of the claim, and quoted three
> load-bearing numbers from a variant it had itself rejected. Both reviewers refuted the
> impossibility claim independently; one built the counter-formulation and ran it. The
> owner re-opened the decision and chose the counter-formulation (option B, 2026-08-04).

---

## 1. Goal

**A persona's calling dial must not decide whether it continues with a strong draw.**

`personas_postflop.py:979` multiplies the draw bonus by `call_looseness` along with the
made-hand base, so tightening an archetype tightens it against hands nobody folds. The
shipped nit folds a 15-out combo draw 0.4217 of the time — the roster's highest, on a hand
needing 28.6 % that is a favourite by the river, against that spot's own committed
prescription ("semi-bluff raise / call, few folds").

## 2. The change — three coupled sites

**Branch, do not re-associate.** Rewriting `(a+b)·L` as `a·L + b·L` changes IEEE rounding
wherever `b ≠ 0` and shifts 17 WEAK cells by 1 ulp; this repo has already lost 6 of 23
frozen price vectors to a 1-ulp residue (`personas_postflop.py:1204-1207`, ledger R2-1).
Branching keeps every non-STRONG path **bitwise** on today's expression.

```python
# the call merit, plus the reference merit the raise leg needs.
# The reference is UNFLOORED — that is what carries the floor's growth to RAISE.
_ref_lever = pf.continue_ref if pf.continue_ref is not None else looseness
_call_merit_at_ref = (call_base + _DRAW_CALL_BONUS[draw]) * _ref_lever
if draw is DrawCategory.STRONG and looseness < 1.0:
    call_merit = call_base * looseness + _DRAW_CALL_BONUS[draw] * max(looseness, 1.0)
else:
    call_merit = (call_base + _DRAW_CALL_BONUS[draw]) * looseness   # literal, untouched

# the B5b commit damp removes exactly what was added, from BOTH merits;
# the reference's subtraction is unfloored too, or the L = 1 boundary steps.

# the N-LOGIT raise scale, same predicate
if draw is DrawCategory.STRONG and looseness < 1.0 and _call_merit_at_ref > 0.0:
    rscale = call_merit_now / _call_merit_at_ref
else:
    rscale = looseness / ref            # literal shipped expression, untouched
```

**`looseness < 1.0`, not just `draw is STRONG`.** Where the dial is already ≥ 1 the floor is
a mathematical no-op, so falling through to the original expression makes the calling
station's bit-identity **structural** — true at any dial value. Rev 2 used the bare `STRONG`
predicate, and `max(L, 1.0)` returns `L` there, so it computed `call_base·L + bonus·L`: the
re-associated form this design exists to avoid. The station survived only because 4.0 is a
power of two. Demonstrated at fan-in by refitting it to 3.7 — one ulp on all three legs.
(The old comment's "a refit to 3.5 would have broken it" was itself wrong; 3.5 is
arithmetically lucky too.) Gated now at both 4.0 and **3.7**.

⚠️ **`call_merit_now` means the LIVE post-damp CALL entry, not the pre-damp `call_merit`
local.** Read it out of `entries` at the point of use. This is load-bearing, and the
ambiguity is real enough that T1's implementer flagged it: taking the pre-damp local would
break `G-COMMIT` (the dial must stay inert on SPR-committed nodes) precisely when
`_commit_transform` has already rewritten CALL. It also means the N-LOGIT block **must stay
below** the commit block — reordering them breaks the guarantee silently, with no test
naming the dependency. T7 comments this; `N-DRAWORDER` is filed for a pin.

**Why the raise leg moves too.** N-LOGIT guarantees, to `1e-12`, that the calling dial never
changes `P(raise | continue)`. That held only because CALL and RAISE were both
*proportional* to the dial. Flooring the draw bonus makes CALL affine, so a frozen
`rscale = looseness/continue_ref` would break the guarantee on draw cells.

Rev 1 called that unrecoverable. **It is not.** Setting `rscale := C(L)/C(ref)` makes
`R/(C+R) = R₀/(C₀·ref+R₀)` — independent of the dial for *any* call shape — and on the
fall-through branch it reduces to the literal `looseness/ref`. The guarantee is preserved
everywhere instead of being narrowed, and is **continuous across the `L = 1` boundary**:
both branches evaluate to the same value, measured spread `5.55e-17` over a sweep spanning
it, including through the B5b damp and the SPR commit transform.

⚠️ **The reference must be UNFLOORED — rev 2 got this wrong and it cost a realism
regression.** Computing `C(ref)` with the floored expression cancels the floor's growth out
of the ratio, so the extra continue mass all lands on CALL and none on RAISE. Measured
consequence: every aggressive persona stopped semi-bluff raising big draws — lag's raise
probability at the trace node fell 0.4718 → 0.3884, maniac 0.6099 → 0.5264, tag
0.3891 → 0.3216, and the aggression factor drifted away from the theory contract's targets.
A LAG holding a monster draw flat-called where it used to check-raise. Found by the theory
reviewer at fan-in; the refuter, reasoning only from gates, called the slice clean.
Unfloored, RAISE grows by exactly the factor CALL grows by, so the raise:call split is
preserved **against the base engine** — max deviation `1.11e-16` across six personas and
seven nodes, now pinned as a gate.

**Why a floor and not an exemption.** `calling_station` is the only persona whose dial
exceeds 1 (4.0); a plain exemption *takes* continue mass from the loosest bot — measured
0.0915 → 0.2156. The floor is identical to an exemption for every persona below 1.
⚠️ Under rev 1's re-associated form the station was unchanged only because 4.0 is a power
of two (`(a+b)·4 == a·4 + b·4` bitwise); a refit to 3.5 would have broken it silently.
Under the branch form the property is **structural**, not arithmetical.

**Why STRONG only.** Flooring the WEAK bonus would enlarge the un-equity-gated gutshot
defect (F7) that the engine already discloses. This argument stands on its own; the
comment at `:768-776` is **not** authority for the asymmetry — it excludes STRONG draws
too, for a different reason (the line damp's scope).

**Out of scope:** every pack value (no `content/` edit) · `continue_ref` itself (frozen —
re-syncing it deletes the N-LOGIT feature) · `_DRAW_RAISE_BONUS` and `_DRAW_AGG_BONUS` ·
WEAK draws · the turn/equity question (§6) · `BANDS` in `test_personas*.py` (frozen to W4-b).

## 3. What it must achieve — pre-registered, measured first

Every gate below was demonstrated **red against a concrete mutant** before shipping, and
each carries an independence witness naming what it can fail on that no sibling covers.
Two gates in the first pass could not do that and were replaced.

| # | claim | gate | base `b0a6a4e` | **as shipped** |
|---|---|---|---|---|
| C1 | a strong draw's fold rate barely responds to the dial | **G-DRAW** self-difference (nit 0.45 vs the same pack at 0.60) ≤ **0.030**, at six priced strong-draw nodes | D1 +0.0682 · D2 +0.0678 · D3 +0.0693 · D4 +0.0628 · P1 +0.0380 · R2 +0.0387 — **all red** | +0.0039 · +0.0161 · +0.0040 · +0.0143 · +0.0094 · +0.0096 |
| C2 | the nit's strong-draw folding falls materially | **absolute ceiling** at the trace node: P(fold) ≤ 0.34 | 0.4217 — red | **0.2608** |
| C2b | the roster is not loosened wholesale | **cross-persona**: nit − station fold gap ≥ 0.10 at D1 | +0.3301 | **+0.1692** (floor=2.0 → +0.0624, floor=5.0 → −0.0073, both red) |
| C3 | the dial still works on made hands | existing G-NODE floor ≥ 0.040, unmodified | +0.0697 / +0.0717 | **byte-identical** |
| C4 | the dial cannot change the raise share | existing N-LOGIT G1 at `1e-12`, unmodified and unscoped | green | **green** |
| C4b | the raise share matches the BASE engine | **new**: P(raise∣continue) pinned per persona, 6 × 7 nodes | — | max deviation **1.11e-16** |
| C5 | non-STRONG behaviour is bitwise unchanged | **new**: exact `==` on the full distribution at a WEAK and a draw-NONE node | — | bitwise identical |
| C6 | the station's invariance is structural | **new**: exact `==` at a non-power-of-two dial (**3.7**), and at 4.0 | — | bitwise identical at both |

**C2b replaced an absolute floor, on the owner's ruling.** The original lower bound said the
nit must fold a strong draw at least 20 % of the time. That is indefensible as poker — no
nit folds a 15-out combo draw getting 28.6 % — and it would have blocked `N-DRAWEQUITY` and
`N-DRAWTURN`, whose whole purpose is making equity-aware draws continue *more*. The
cross-persona form makes the same kill by the persona-flattening an over-loose floor causes.

**A sensitivity cap alone is level-blind**, which is why C2/C2b exist at all: floor values of
0.6, 2.0 and 5.0 all satisfy C1, and 5.0 loosens even the calling station. Under both
floor=2.0 and floor=5.0 the cap *and* the ceiling stay green while C2b goes red — the
argument is now demonstrated rather than asserted.

**C4b exists because C4 cannot see a level shift.** G1 pins that the raise share does not
move *with the dial*; it says nothing about where that share sits. Rev 2 satisfied G1 while
collapsing the share by up to 0.13 against the base engine. C4b is the gate that catches it.

⚠️ **Node selection is load-bearing.** P2 (top pair + flush draw) sits at +0.0134 at base —
already inside the cap — so a panel of only high-fold naked draws would make G-DRAW's
redness a property of the nodes, not the gate. P1 and R2 exist because hand strength and
draw strength are **independent axes** and rev 1's panels sat entirely on one side of that
grid. **R2 is P1 facing a raise**: every earlier node had `facing_raise=False`, and the
refuter demonstrated a mutant flooring only when *not* facing a raise that passed all seven
gates while leaving the defect fully alive in production.

**The honest red-at-base window is (0.0161, 0.0380)** — between the loosest shipped reading
and the tightest base one. The 0.030 cap is a **chosen budget**, not derived: G-NODE's
0.071797 log-odds ceiling does not transfer, because a draw node's continue merit is no
longer proportional to the dial.

## 4. Disclosed behaviour changes

⚠️ **FIVE personas change, not one.** All three fan-in reviewers independently refuted the
earlier framing that only the nit moved and everything else was shared-shuffle displacement.
The floor binds for **every persona whose dial is below 1.0** — nit, tag, lag, maniac and
passive_fish. Only `calling_station` (dial 4.0) is inert, and after the `looseness < 1.0`
predicate that inertness is structural. Do not repeat the one-persona story.

- **Strong draws are folded much less, across the roster.** At the trace node: nit
  0.4217 → **0.2608**, passive_fish 0.4173 → 0.2451, lag 0.2277 → 0.1467.
- **Pair-plus-draw hands continue more.** A nit with middle pair + a flush draw folds
  0.1765 → 0.1206; top pair + flush draw 0.0558 → 0.0390. Undisclosed in rev 1; gated by P1.
- **The raise:call split is unchanged.** The freed fold mass is split between CALL and RAISE
  in the base engine's own proportion — `P(raise∣continue)` matches base to `1.11e-16` for
  all six personas. Rev 2 instead routed all of it to CALL, which is the regression the
  theory reviewer caught.
- **Coverage improves.** Graded share 26.01 % → **27.53 %** — within 0.77 pp of the
  immutable start snapshot, the strongest recovery of the mapper-track dip recorded.
- Everything outside strong draws is bitwise unchanged, at every dial value, for all six
  personas — now pinned by C5 and C6 rather than merely asserted.

## 5. What broke, and how each was resolved — final suite **1430 passed, 1 skipped, 0 failed**, ruff clean, `BACKEND VERIFY OK`

| # | test | disposition — as shipped |
|---|---|---|
| 1 | `test_persona_stats_byte_identical_after_log_refactor` | `_GOLDEN_STATS_N200` re-recorded under protocol. ⚠️ `calling_station` and `nit` end **byte-identical to base**; both were investigated to raw counts rather than waved through (see §5a) |
| 2 | `test_limper_coverage_fires_on_organic_play` — UTG2¹ 74 → **95** | `_PRE_M3_FIRES` re-recorded under protocol; all nine rows moved |
| 3 | `test_coverage_never_regresses` — `hand stream drifted`, 1288 → **1195**, graded 335 → **329** | `coverage_baseline.json` re-recorded; **ruling R2**. Graded *share* **rises** 26.01 % → 27.53 % |
| 4 | `test_t4_flop_absolute_band[passive_fish-0.33]` — 0.193 vs floor 0.20 | **ruling R1**, revised at fan-in: the row is now **report-only**, not asserted |
| 5 | `test_nlogit_g3_identity_at_authored_values_is_bit_exact` | appeared only after the raise-leg fix; **scoped and replaced** (see §5b) |

### 5a — the two byte-identical golden rows

`calling_station` matches base on all three cells *and* on the raw counts underneath
(360 / 61 / 308), so it is genuine byte-identity, not a ratio collision over different data.
Its decision function provably never changes (C6); on this harness's seed and lineup, no
other persona's changed decision happened to alter game state at any of the station's own
action nodes across 200 hands. **That is a property of this sample, not a second structural
guarantee** — a different seed could show displacement. The `nit` row matches for the
mundane reason that its n=200 sample reaches no aggression cell on either engine.

### 5b — G3 scoped, and replaced

`test_nlogit_g3_identity_at_authored_values_is_bit_exact` asserts the N-LOGIT feature is
inert at authored values. Routing the floor's growth through that feature makes it not inert
on strong draws. **This is unavoidable in any design that fixes the raise leg through
`rscale`**: the un-opted path (`continue_ref is None`) short-circuits the block entirely, so
growth carried through it cannot reach both paths. The owner ruled to scope G3 and replace
it — scoping without replacing was explicitly not acceptable, since rev 1 of this spec was
failed for narrowing a gate.

Reach, re-measured rather than assumed: of 10,368 (cell, persona) comparisons **exactly 320
differ** — 64 per persona for the five sub-1.0 personas, all in the raise-legal half of
their 128 STRONG cells. `calling_station` and all 1,600 non-STRONG cells stay bit-identical.
The excluded-cell count is itself pinned, so the scope cannot widen silently. C4b is the
replacement and is strictly stronger on those cells.

Passing, and previously flagged at risk: the N-LOGIT raise-share gate (the rev-1 blocker,
now green), last slice's 970-cell population sweep, G-NODE, the B5b commit tests, the whole
R9-DEFENCE-a line suite, and all 23 frozen vectors in `test_price_tail.py`.

⚠️ The calling-station golden moves even though the station's *policy* is bitwise
unchanged — all six personas share one seeded rng stream, so changing the nit re-deals
everyone. That is expected, and is not evidence of a wider defect.

### R1 — the `passive_fish` small-price band

**Reframed after review; rev 1 got this backwards.** The band (fold 20-38 % to a ⅓-pot flop
bet) is **already a coin flip at HEAD**: reseeded eight ways, the unchanged engine breaches
its own floor on **2 of 8** (0.1799, 0.1801). The paired base→candidate effect over those
seeds is **mean −0.0020, sign flipping twice**; the pinned seed's −0.0144 is the most
negative of the eight. The curve is a Monte-Carlo count over ~1045 arrival spots
(SE ≈ 0.012) against a margin of 0.0077.

So this is **not** a band this slice broke, and rev 1's story ("the floor was being met by
the over-folding this slice removes") is withdrawn — it was also contradicted by rev 1's own
table, where the nit reads 0.1400 → 0.1400.

⚠️ **NARROWED AT BUILD (T6), and the distinction matters.** Everything above is a
*small-sample* reading, and it reproduced: at `n≈1045` the base engine breaches its own
floor on 2 of 8 re-deals and the paired effect is noise (mean −0.0003, sign flipping, 3
down / 3 up / 2 tied on the builder's reseed scheme). But at a **stable** sample the effect
stops being noise: base 0.2122 vs shipped 0.2065 at n=33636, and 0.2118 vs 0.2039 at
n≈8400 — **a consistent −0.006**. The defensible claim is therefore the narrow one:

> the **breach** is not attributable to this slice — but "this slice does not move the fish
> here" would be false, and must not be written anywhere.

The shipped test says exactly this and no more. **Residual risk, disclosed:** after
escalation the row passes at 0.2065 against a 0.20 floor — a margin of ~0.006, about 2.6
standard errors. Escalation has no headroom left, so the next change that touches fish
arrival turns this into the fit question `N-FISHFLOOR` was filed for.

**Ruled, then revised at fan-in.** The owner first ruled to apply the R10-TAIL-a1 precedent —
escalate to a stable sample before failing. That shipped and worked (0.2065 against a 0.20
floor at n=33636). The theory reviewer then pointed out the deeper problem: the committed
theory contract marks that row **DIRECTIONAL-only**, its underlying metric not yet built, so
it may bound a regression but **may not define a pass**. An 80,000-deal re-measure was a
sampling remedy for what is really a provenance problem.

**As shipped:** the row is **report-only** — measured and printed, not asserted — and the
escalation machinery is deleted. The other three rows assert unchanged and were verified
unaffected. `N-FISHFLOOR` remains filed for the re-derivation. Provenance still attributes
the *breach* to sampling, not to this slice, while stating plainly that the slice does move
the fish down ~0.005 at a stable sample. **Also disclosed, and previously missed:** the fish
OVERBET row moves ~3.1× as far (−0.0165) and went unrecorded only because it never breached
at the throughput sample, so breach-only escalation never fired on it.

### R2 — the coverage assertion

Not a ratchet dip. The test fails on its *first* assertion, whose comment ("a drift means
the harness stopped being engine-only") was written to catch harness contamination, not a
deliberate bot-policy change. Most of the 400 hands change shape, so there is **no set of
"three lost graded decisions" to attribute** — rev 1 asked a builder to find them and that
task does not exist.

**As shipped:** `total` **1288 → 1195**, graded **335 → 329**, graded **share 26.01 % →
27.53 %**. Fewer decisions are graded only because bots reach fewer decision points at all;
the share of play the mapper *can* grade rises, and lands within 0.77 pp of the immutable
start snapshot — the strongest recovery of the mapper-track dip this fixture has recorded.
`coverage_baseline.json` re-recorded, ratio disclosed as the honest metric. Asserting the
share is deliberately **not** done here: it belongs to `T-cover`, not to a persona slice.

## 6. Constraints

Domain core keeps no web/DB imports (test-enforced) · no `content/` edit · `continue_ref`
frozen · `BANDS` frozen to W4-b · results stay frequency + EV · grading stays behind the
async `StrategyProvider` · `spot_signature()` frozen · only `_GOLDEN_STATS_N200`,
`_PRE_M3_FIRES` and `coverage_baseline.json` may be re-recorded, each under its own protocol
with attribution proven by revert **both** ways; any other fixture that moves is a defect ·
never read a suite result from a piped exit code · absolute paths, bare git · reviewers are
git-READ-ONLY.

## 7. Verify-by

`./scripts/verify.sh` green · `ruff check .` clean · suite 1419 + the new gates, with the
four failures resolved by their stated dispositions and no fifth appearing.

## 8. Filings — found here, not built here

| id | finding |
|---|---|
| `N-DRAWEQUITY` | `_draw_equity` (`:658-672`) assigns **every** STRONG draw a flat nine-out proxy. A 15-out combo draw therefore reads 0.18 on the turn when the hand actually has ≈15/46 = 32.6 %. Every equity-gated decision inherits this. Found by Codex while refuting rev 1's turn claim. |
| `N-DRAWTURN` | Draws may continue too much on later streets — but **the specific rev-1 claim is withdrawn**: the trace combo draw at 32.6 % beats its 28.6 % price on the turn. The concern survives for genuine nine-out draws. The remedy is the price/equity gate the theory contract's §4 P6/F7 row wants; the engine has no implied-odds model, so a pure immediate-odds gate would itself be wrong. Depends on `N-DRAWEQUITY`. |
| `N-DRAWWEAK` | `_DRAW_CALL_BONUS[WEAK]` stays un-equity-gated and on the dial. Resolve with `N-DRAWTURN`, not separately. |
| `N-FISHFLOOR` | The fish ⅓-pot flop band breaches at HEAD on 2 of 8 seeds. A band that thin is a tripwire, not a target — re-derive at W4-b. |
| `N-DRAWORDER` | `rscale` divides the **live post-damp** CALL entry, which silently requires the N-LOGIT block to sit **below** the commit block. Reordering them breaks the guarantee with no test naming the dependency. The refuter showed the reorder *is* caught indirectly (G1 + G3 on low-SPR cells), so this is a naming gap, not an exposure. Pin it. |
| `TH-5` (carried, **and the concern is withdrawn**) | The premise that option B entrenches the constant raise:call ratio was put to the theory reviewer, who **disagreed and gave reasons**: before this slice the invariance was implicit in the algebra with nothing to edit; it is now an explicit named expression at one site with an obvious parameter slot, so correcting TH-5 later is *easier*, not harder. The recommended hedge — record `P(raise∣continue)` per persona rather than add a placeholder constant — shipped as gate C4b. |

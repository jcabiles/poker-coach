# N-DRAWLOOSE — finding ledger

Base `b0a6a4e`. Spec `docs/ai-dlc/specs/n-drawloose.md`. Every finding gets an adjudicated
status; reviewer output is a report, never gospel, and is verified against the code before
it is accepted.

---

## SPEC STAGE — director's own findings (measurement, before review)

| id | severity | finding | disposition |
|---|---|---|---|
| D-1 | HIGH | **A plain exemption of the dial from the draw bonus is a regression for `calling_station`.** It is the only persona whose dial exceeds 1 (4.0), so removing the dial *takes* continue mass from the loosest bot: trace-node fold 0.0915 → 0.2156. | ACCEPTED — killed the exemption shape; the spec floors at 1 instead, which is identical for every persona below 1 and a measured no-op for the station. |
| D-2 | HIGH | **The N-LOGIT raise-share invariance cannot survive on draw nodes under any shape of this fix.** CALL becomes affine in the dial (`call_base·L + BONUS`) while RAISE stays proportional via `rscale`, so the dial no longer cancels from `R/(C+R)`. Exempting the raise bonus as well gives `aL+b` vs `cL+d` — still not proportional. | ACCEPTED as structural. Owner ruled: narrow the gate to draw-NONE cells and add a companion gate on strong-draw cells (T2). Recorded as arithmetic, not as a property of the test data. |
| D-3 | MED | **Scoping to STRONG does not avoid the fish band breach**, it only halves it: 0.1761 (STRONG+WEAK) → 0.1933 (STRONG-only), against a 0.20 floor. Measured, not assumed — the STRONG-only variant was built and the full suite re-run. | ACCEPTED — the band question is unavoidable and is filed as open ruling R1 rather than engineered around. |
| D-4 | MED | **The fish band had 0.0077 of headroom at HEAD** (0.2077 against a 0.20 floor). Its floor was partly being met by the over-folding this slice removes. | ACCEPTED — reframes R1 from "this slice broke a band" to "this slice exposed a band resting on the defect". Filed separately as `N-FISHFLOOR`. |
| D-5 | MED | **The static contract map missed the arrival band entirely.** It names no lever, no engine symbol and no draw; it is reached only through organic play. | ACCEPTED and recorded in the contract map's BLIND SPOTS. Standing lesson: the contract map explains *why* something breaks; only the full suite establishes *whether*. |
| D-6 | LOW | **The turn case moves the wrong way.** On the turn the same combo draw holds 0.18 equity against 0.2857 needed, so continuing is unjustified on immediate odds — and every shape of this fix makes the bot continue there more. | ACCEPTED, NOT FIXED — filed as `N-DRAWTURN`. The remedy is the price/equity gate the theory contract's §4 P6/F7 row wants, and the engine has no implied-odds model, so a pure immediate-odds gate would itself be wrong. One mechanism per slice. |

## SPEC STAGE — director errors caught by instruments

Recorded because the initiative's own law is to record what was measured, including the
measurer's mistakes.

| id | what happened | caught by |
|---|---|---|
| E-1 | Declared a node's price as a rounded `0.6667` when the engine computes `0.6666666666666666`. | The price-asserting instrument refused the reading rather than returning a number. Fixed by declaring `4.0/6.0`, not by loosening the tolerance. |
| E-2 | Declared a node as ½-pot that the engine priced at pot (`pre_pot 18, to_call 18`). | Same instrument. The node was dropped from the panel. This is the second slice running in which that assertion caught a mispriced node — it is doing real work and T3 requires it. |
| E-3 | Wrote a single before/after list mixing readings from **two different variants** (tag/lag/maniac from the STRONG+WEAK run, nit/fish from the STRONG-only run). | Self-caught on re-read before review. Corrected to an explicit per-variant table with "not measured" stated rather than implied. |

## REVIEW STAGE — Codex Sol (`gpt-5.6-sol`), verdict **FAIL**

Every finding was re-verified against the code or by independent measurement before being
accepted. Five accepted, one narrowed, one accepted-as-documentation.

| id | sev | finding | adjudication |
|---|---|---|---|
| C-1 | BLOCKER | **"Unrecoverable under any shape" is too strong.** Coupling the raise scale to the call merit — `R(L) = R₀·C(L)/C(ref)` — makes `R/(C+R) = R₀/(C(ref)+R₀)`, exactly independent of the dial, with `R(ref) = R₀`. | **ACCEPTED, claim NARROWED.** Verified algebraically: the construction is correct. The true statement is "unrecoverable **while the raise leg keeps its shipped `rscale = looseness/continue_ref` form**". The coupled form is still **rejected on design grounds, not impossibility**: it makes the raise merit inherit the CALL bonus (a strong draw's raise weight would move with a call-side constant), and TH-5 already records that holding raise:call *exactly* constant is the wrong shape — a real player tightening a defence drops the weakest calls and keeps every value raise. Spec §4.1, report §5.1, contract map and the **roadmap entry** all carried the overstated version and are corrected. |
| C-2 | HIGH | **The coverage evidence is wrong for the shipped scope.** Real readings: base 1288/335, candidate 1233/323 — a 55-decision stream drift and 12 fewer graded, not "same stream, three lost". | **ACCEPTED — my error, independently re-measured and confirmed** (`_measure()` run directly in both worktrees; the unchanged tree reproduces 1288/335 exactly). The STRONG-only suite fails on the **`total`** assertion ("hand stream drifted"), not the graded ratchet. R2 and T5 rewritten. New framing the numbers support: graded **ratio** RISES 26.01 % → 26.20 % (335/1288 → 323/1233); the absolute count falls only because fewer hero decisions are reached at all. |
| C-3 | HIGH | **`_PRE_M3_FIRES` movement is wrong**: candidate produces UTG2¹ **70**, not 84. | **ACCEPTED — my error.** 84 is the STRONG+WEAK reading; 70 is STRONG-only. T4 corrected. |
| C-4 | HIGH | **The proposed gates admit wrong implementations.** Named escapes: scope the fix to `bucket in {AIR, ACE_HIGH}` (every published node is AIR/ACE_HIGH, and N-LOGIT's only STRONG template is ACE_HIGH at `test_personas_postflop.py:7001-7005`), so TOP_PAIR/MIDDLE_PAIR + STRONG stays defective · make the `:1098` mirror right for AIR/ACE_HIGH and wrong for made+STRONG at low SPR · implement only where a RAISE leg is legal · floor the whole strong-draw call merit (the ≤0.030 cap rewards insensitivity and sets no continuation ceiling) · ship the plain exemption and eat the station regression (no gate pins station byte-identity). | **ACCEPTED in full.** T2/T3 were underspecified — the exact defect class this initiative keeps paying for. Tickets rewritten with: a made-hand-bucket STRONG node, a FOLD/CALL-only strong-draw node, a low-SPR made+STRONG node, an explicit station byte-identity pin, and an absolute continuation floor alongside the sensitivity cap. |
| C-5 | MED | **C3's roster claim is false** — the nit remains the heaviest strong-draw folder after the fix (nit 0.2838 vs fish 0.2769). | **ACCEPTED.** I measured this early and failed to carry it into the spec's claim text. The honest claim is the **magnitude** of the nit's own fall (0.4217 → 0.2838), not a roster ordering — the same "pairwise, not superlative" discipline R9-LOOSEFIT had to be forced into. Corrected. |
| C-6 | MED | **More organic consumers unlisted**: `test_mw_funnel_belt.py:36`, `test_grade_map_limped_flop.py:350`, `test_grade_map.py:703`, `test_grade_map_turn_river.py:604`, `test_range_estimate.py:1035`, and R9-DEFENCE's organic S5 population run. All pass, but all are the hidden-dependency shape. | **ACCEPTED as documentation.** Added to the contract map with their measured (passing) status, so the next slice inherits the list rather than rediscovering it. |
| C-7 | MED | **D4 is mislabelled** — `opponents=3` is four-way, not three-way; a true three-way node reads HEAD 0.0596 / fix 0.0174. **And the turn-equity filing conflates the engine's proxy with the hand**: `_draw_equity` (`:658-672`) assigns every STRONG draw a flat nine-out proxy, so 0.18 is the proxy's number; the actual 15-out combo draw has ≈15/46 = 32.6 % on the turn, which is **above** the 28.6 % price. | **ACCEPTED, both limbs.** The label is fixed. The second limb is the more valuable finding: it does not kill `N-DRAWTURN` but it re-points it — the over-continuation concern survives for genuine nine-out draws, while the specific "this combo draw is unjustified on the turn" claim is withdrawn, and a **new** finding emerges: the engine's flat nine-out proxy materially understates combo draws. Filed as `N-DRAWEQUITY`. |

**Confirmed by Codex, could not be broken:** the full-suite result (5 failed / 1414 passed / 1 skipped) · the fish band 0.1933 · the trace node 0.4217 → 0.2838 with the station byte-identical at 0.0915432 · D-1/D-2/D-3 self-differences to four decimals · **that the C1 cap and the existing made-hand floor are genuinely algebraically independent** (the vacuity check this initiative now requires — it passed) · that STRONG-only is coherent as incremental containment.

## REVIEW STAGE — `refuter` (Opus), verdict **FAIL**

Independent of Codex; converged on the same three top findings and added nine. Adjudicated
against the code, and its counter-formulation was **re-run by the director on the full
suite** rather than taken on report.

| id | sev | finding | adjudication |
|---|---|---|---|
| R-1 | HIGH | **Built and ran the counter-formulation.** `rscale := C_shape(L)/C_shape(ref)` preserves the raise-share invariant for *any* call shape, and reduces to the literal `looseness/ref` on `draw is NONE`, so it is backward-compatible where `test_price_tail`'s 23 bit-exact vectors live. Measured: G1 **green**, nit trace 0.2768 (better than 0.2838), D1 self +0.0040, D3 +0.0041. | **ACCEPTED and independently re-measured by the director on the FULL suite** (the refuter ran only two files): **4 failed / 1415 passed / 1 skipped, ruff clean** — one fewer failure than the specced fix, and the one removed is the hard blocker. Self-differences reproduced: +0.0040 / +0.0164 / +0.0041 / +0.0146, made hands byte-identical. **Escalated to the owner as a re-opened Gate-2 decision**, because the choice they already made (re-scope the gate) rested on my impossibility claim, which was false. |
| R-2 | HIGH | Coverage evidence is the rejected variant's; real drift is 1288→1233 with 246/400 hands changing shape, Σ&#124;Δtotal&#124; = 599. There is no set of "three lost decisions" to attribute, so T5's acceptance criterion is unachievable as written. | **ACCEPTED** — duplicate of C-2, with stronger evidence. T5 rewritten around arrival displacement, not a ratchet dip. |
| R-3 | HIGH | `_PRE_M3_FIRES` is 74 → **70**. **And §5.1's explanation is fabricated**: I wrote that the grid's `weak_draw` cells "are classified by the engine as STRONG"; the templates classify exactly as labelled, asserted by an existing passing test (`:7104-7132`) and confirmed by a direct dump. The STRONG-only run's failures are all `strong_draw` cells. | **ACCEPTED — the worst finding of the review.** The number was a variant mix-up; the *explanation* was invented to rationalise it. Filtering on `DrawCategory` is still right, for the real reason (a template rename desyncs a name filter). Deleted, not softened. |
| R-4 | MED | **WEAK draws are NOT bit-identical.** Re-associating `(a+b)·L` into `a·L + b·L` changes IEEE rounding wherever `b ≠ 0`: 17 WEAK cells shift by 1 ulp. The repo has been bitten by this exact thing before (`personas_postflop.py:1204-1207`, ledger R2-1 — a 1-ulp residue broke 6 of 23 frozen vectors). | **ACCEPTED.** T1's "WEAK and NONE are provably unchanged" was false as written. Fix is structural: **branch rather than re-associate** — keep the literal shipped expression for non-STRONG. Then the claim is true and T3's WEAK pin can assert exact equality. |
| R-5 | MED | **R1 is not honestly framed.** HEAD itself breaches the 0.20 floor on **2 of 8 reseeds** (0.1799, 0.1801); the paired base→candidate effect over 8 seeds is **mean −0.0020 with the sign flipping twice**. The pinned seed's −0.0144 is the most negative of the eight. The cited "asserts stably at this N" sentence describes the July-2026 authoring criterion, not a standing property. Also my causal story ("fish moves furthest because its dial is lowest") is contradicted by my own table — the nit at 0.45 reads 0.1400 → 0.1400. | **ACCEPTED in full.** This inverts R1: the band is a **coin-flip tripwire at HEAD, independent of this slice**, not a band this slice broke. T6 must not write provenance attributing the breach to this change. Remedy re-pointed to the R10-TAIL-a1 precedent (escalate to stable n before failing) — same disease, same cure. |
| R-6 | MED | **The gates pin the derivative and never the level.** Floor values of 0.6, 2.0 and **5.0** all pass T3; `floor=5.0` more than doubles every persona's strong-draw bonus, loosens even the calling station, and nothing catches it because T4 re-records the moved fixtures. C3 (the only level claim) is ticketed nowhere. | **ACCEPTED.** A sensitivity cap with no level bound is the same defect class as last slice's "gates impose NO lower bound". C3 becomes a real two-sided gate. |
| R-7 | MED | **The pair+draw quadrant is measured by nothing.** The engine's own comment (`:752-756`) says bucket and draw are INDEPENDENT axes; G-NODE is five draw-NONE nodes and G-DRAW is four AIR/ACE_HIGH nodes — both on one side of the grid. Measured, undisclosed: a nit with MIDDLE_PAIR + flush draw folds **30 % less** after the fix (0.1765 → 0.1229). And TOP_PAIR+FD is **already under the 0.030 cap at HEAD**, so G-DRAW's red-at-HEAD property belongs to the chosen nodes, not to the gate. | **ACCEPTED.** Add a `MIDDLE_PAIR + STRONG` node (red at HEAD +0.0380, green with the fix +0.0120) and disclose the pair+draw movement in the spec's §3. |
| R-8 | MED | T7's stale-comment list misses `test_personas_postflop.py:9839-9840` — G-NODE's own docstring, which states the now-falsified same-factor property as the justification for its 0.040 constant. | **ACCEPTED.** Matters beyond hygiene: the 0.071797 analytic ceiling that makes 0.040 defensible is *derived from* that property, which after this change holds only for draw-NONE. |
| R-9 | MED | G-DRAW's D3 is a **turn** node, so a ≤0.030 cap there **pins in** the turn over-continuation the report itself calls unjustified; a future `N-DRAWTURN` equity gate would have to break G-DRAW to land. | **ACCEPTED, and compounded by C-7** — the report's turn premise was itself wrong (0.18 is the engine's flat nine-out proxy; the actual 15-out draw has ≈32.6 %, which beats the price). The whole turn narrative is rewritten, and D3 carries an explicit note that `N-DRAWTURN` is expected to invalidate it. |
| R-10 | LOW | `0.030` is asserted, not derived; the log-odds-shift ceiling that justified its sibling 0.040 does not transfer, because the draw-node continue merit is no longer proportional to the dial. | **ACCEPTED** — state it as a chosen budget with the floor sweep attached, or derive it. |
| R-11 | LOW | **"calling_station unchanged" is true by accident of a power of two.** Its dial is 4.0, so `(a+b)·4 == a·4 + b·4` bitwise. A refit to 3.5 would silently break the property. | **ACCEPTED** — and R-4's branch fix makes the property structural instead of arithmetical. Excellent catch. |
| R-12 | LOW | The `:768-776` citation is selective — it excludes STRONG draws too ("STRONG draws are out pending joint calibration") and supplies no WEAK/STRONG asymmetry. | **ACCEPTED.** The scope decision stands on its own argument (exempting WEAK enlarges a disclosed defect); the citation stops being offered as authority for the asymmetry. |

**Confirmed by the refuter, could not be broken:** the defect and its characterisation · floor-over-exemption (station 0.0915 → 0.2156 under a plain exemption, reproduced) · C2 exactly (draw-NONE bitwise identical, by hex comparison — `_DRAW_CALL_BONUS[NONE] == 0.0`) · the four G-DRAW readings to 4dp · **C1/C2 non-vacuity** (the previous slice's failure mode does not recur) · single seam · no fourth seeded golden · the failure set and `ruff` clean.

### Director error, root-caused

C-2, C-3 and the earlier E-3 are **one error repeated three times**: I ran the STRONG+WEAK
variant first, harvested its failure detail, switched the worktree to STRONG-only, re-ran,
and read only the summary line — then wrote the spec from the first run's numbers. E-3 was
caught by re-reading; C-2 and C-3 were not, and reached a spec that was presented for
review. **Standing lesson: when a variant changes, every number in the document is stale
until re-harvested from that variant's own output — a summary line matching (both runs
showed "5 failed") is not evidence that the failures are the same failures.**

## BUILD STAGE

Not started. Gate 2 not yet passed.

---

# FAN-IN REVIEW OF THE BUILT SLICE — 2026-08-05

Three independent reviewers on `b0a6a4e..09c2364`, all git-read-only: `refuter` (Opus),
Codex Sol (`gpt-5.6-sol`), and `persona-realism-theory-reviewer`. **All three returned
FAIL / NEEDS-WORK.** None found the mechanism wrong; all found the claims around it wrong.
Every finding below was verified before being accepted or rejected.

## Accepted, and fixed in rev 3

| id | reviewer | finding | adjudication |
|---|---|---|---|
| **F-1** | all three, independently | "Only the nit's policy changed; everything else is shared-shuffle displacement" is FALSE — the floor binds for all five personas with a dial < 1.0 | **ACCEPTED.** The conclusion (re-records legitimate) survived; the stated mechanism did not. Corrected in the spec, both chain comments, and the build-state report. Written in three places by me before anyone caught it — the cost of a causal story that sounded right |
| **F-2** | theory (HIGH) | The floored reference cancels the floor's growth out of `rscale`, so all freed mass lands on CALL and none on RAISE. Aggressive personas stopped semi-bluff raising: lag 0.4718→0.3884, maniac 0.6099→0.5264, tag 0.3891→0.3216; AF drifts away from contract targets | **ACCEPTED, owner-ruled.** Reference computed UNFLOORED. `P(raise∣continue)` now matches base to 1.11e-16. Gated as C4b. ⚠️ The refuter, reasoning only from gates, called the slice clean — the gap was that no gate measured the quantity the change moved most |
| **F-3** | refuter (HIGH) | "Structural, not arithmetical" is false: `max(L,1.0)` returns `L` for L≥1, so the STRONG branch IS the re-associated form. Station survives only because 4.0 is a power of two. Demonstrated at 3.7 | **ACCEPTED.** Predicate is now `looseness < 1.0`, so any dial ≥1 falls through to the literal. Gated at 3.7 and 4.0. Also corrected the spec's own example: 3.5 would *not* have broken it either |
| **F-4** | Codex | Claim C5 (non-STRONG bitwise unchanged) had **no gate** — re-associating that expression passed 77 tests including all 23 frozen vectors, while WEAK weights moved 1 ulp | **ACCEPTED.** Exact-equality vectors added. Disclosed: the draw-NONE leg cannot kill that mutant (bonus is 0.0 there); the WEAK leg carries the kill |
| **F-5** | Codex | The new G1 census gate cannot fail independently of G1 — same count, same threshold | **ACCEPTED.** This is the exact defect the previous slice was failed for, recurring — **and my own brief asked for it.** Replaced with an exact per-category census |
| **F-6** | refuter | Every new node had `facing_raise=False`; mutant M13 (floor only when not facing a raise) passed all seven gates while the defect stayed alive in production | **ACCEPTED.** `_NDNode.facing_raise` added, node R2 added, plus a liveness test so a forgotten kwarg cannot silently re-open it |
| **F-7** | refuter | The `_c_now` comment cites G-COMMIT, whose only cell is an overpair with no draw — it cannot exercise the branch. A vacuous gate in comment form | **ACCEPTED.** Re-cited to G1, and the replacement was *verified* by enumerating the grid: 32 strong-draw cells at the committing 12 bb stack |
| **F-8** | Codex | `content/models.py` still describes the old invariants — a file the first sweep never opened | **ACCEPTED.** Corrected |
| **F-9** | refuter | ~10 wrong line anchors introduced by the commit whose job was fixing stale references, in a file whose house rule is to name constructs | **ACCEPTED.** ~35 anchors replaced with construct names |
| **F-10** | refuter | The fish OVERBET row moves ~3× as far as the row that failed and is disclosed nowhere, because it never breached at the throughput sample | **ACCEPTED.** Disclosed. A live instance of the blind spot the escalation's own comment named |
| **F-11** | theory (MED) | T4's absolute lower bound is a mutant guard dressed as a poker claim, and would block `N-DRAWEQUITY`/`N-DRAWTURN` | **ACCEPTED, owner-ruled.** Replaced with the cross-persona claim (C2b) |
| **F-12** | theory (MED) | The fish row is DIRECTIONAL-only per the theory contract, so it may bound a regression but may not define a pass; escalation was a sampling remedy for a provenance problem | **ACCEPTED, owner-ruled** — and it *revised* an earlier owner ruling. Row demoted to report-only; the 80k escalation deleted |

## Accepted as correction, no code change

| id | reviewer | finding | adjudication |
|---|---|---|---|
| **F-13** | wave-A worker | The spec's "a refit to 3.5 would have broken it silently" is wrong — 3.5 is bit-clean too; only values like 3.7 expose it | **ACCEPTED.** Spec corrected |
| **F-14** | wave-B worker | My "1152/1152 cells stay identical" figure was a subset, not the whole; the true count is 1600 non-STRONG per persona, with exactly 320 of 10,368 comparisons differing | **ACCEPTED.** Corrected. A number I quoted from a review without re-deriving it |
| **F-15** | wave-C worker | `calling_station` and `nit` golden rows end byte-identical to base | **ACCEPTED as investigated, not as coincidence.** Raw counts underneath are identical too. Documented as a property of this seed and lineup, **not** a second structural guarantee |

## Rejected or withdrawn

| id | finding | adjudication |
|---|---|---|
| **F-16** | `TH-5`: option B entrenches the constant raise:call ratio, making the eventual correction harder — **my premise, put to the theory reviewer** | **REJECTED by the reviewer, with reasons I accept.** The invariance used to be implicit in the algebra with nothing to edit; it is now one named expression with an obvious parameter slot, so the correction is *easier*. The recommended hedge (record the share, don't add a placeholder constant) shipped as C4b |
| **F-17** | Does `_draw_equity`'s flat nine-out proxy undercut this slice's justification? | **NO**, measured: the floor is unconditional on equity and this path never consults `_draw_equity`. The adjacent risk does not materialise — bots still fold to a 3×-pot overbet (nit 0.8358 → 0.7568). The price factor still bites |
| **F-18** | Codex: "246 of 400 hands change shape" (spec) vs "286" (test comment) — one is stale | **MOOT.** Both predate the rev-3 engine; the whole passage was rewritten and the count claim removed |
| **F-19** | Codex #3: no gate names the N-LOGIT/commit ordering dependency | **ACCEPTED AS A NAMING GAP, NOT AN EXPOSURE.** The refuter demonstrated the reorder IS caught, by G1 + G3 on low-SPR cells. Filed as `N-DRAWORDER` rather than fixed here |

## Process findings worth carrying

1. **A gate-only reviewer and a domain reviewer disagree in a predictable direction.** The
   refuter verified everything measurable and passed the slice; the theory reviewer failed it
   on the one behaviour nothing measured. Neither was wrong. Running only one would have
   shipped the regression — this is the case *for* keeping both, stated as evidence rather
   than as policy.
2. **My own brief asked for the vacuous gate (F-5).** Asking a worker to "assert X still
   holds" where X is already asserted elsewhere manufactures exactly the defect this
   initiative keeps being failed for. Ask what a gate can fail on that no sibling covers.
3. **Codex edited the engine despite a review-only brief**, to run mutants. It restored
   correctly and the tree was verified clean, but the instruction did not hold. Assume a
   reviewer with write access will write.
4. **A stale `.pyc` silently produced wrong numbers** when two mutants wrote files of equal
   length in the same second. Any mutation measurement needs `PYTHONDONTWRITEBYTECODE=1` and
   a `__pycache__` purge.
5. **Scripts run outside the worktree measure the wrong engine.** `sys.path[0]` is the
   script's directory, so `app` resolves through the venv's editable install to the main
   checkout, and both trees print identical numbers with no warning. `pytest` is immune
   (`pythonpath = ["."]`). Print `__file__` and check it.

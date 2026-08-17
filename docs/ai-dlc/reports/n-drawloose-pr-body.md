## The defect

Each bot personality has a dial, `call_looseness`, controlling how willing it is to call. The engine multiplied a hand's **entire** call merit by it — including the bonus a hand gets for holding a strong draw. So tightening a personality didn't just make it fold weak hands, it made it fold draws.

The nit folded a 15-out combo draw **42% of the time** — the highest fold rate on the roster, above the passive fish — on a hand needing 28.6% equity and holding roughly 50%, against that spot's own committed "semi-bluff raise / call, few folds" prescription.

## The fix

For `DrawCategory.STRONG` **and `looseness < 1.0`**, the dial is floored at 1.0 where it multiplies `_DRAW_CALL_BONUS`. The reference merit used by the N-LOGIT raise scale is computed **unfloored**, so the floor's extra continue mass is split between CALL and RAISE in the base engine's own proportion.

Result: bots stop folding hands nobody folds, **without becoming passive**.

| | base | shipped |
|---|---|---|
| nit fold, 15-out combo draw, 2/3-pot | 0.4217 | **0.2608** |
| passive_fish, same node | 0.4173 | 0.2451 |
| nit fold, middle pair + flush draw | 0.1765 | 0.1206 |
| `P(raise \| continue)`, all six personas × 7 nodes | — | **matches base to 1.11e-16** |
| graded coverage share | 26.01 % | **27.53 %** |

Five personas' policy changes — every one whose dial is below 1.0. `calling_station` (dial 4.0) is bitwise unchanged, and that is now **structural**: any dial ≥ 1 falls through to the untouched original expression, so it no longer depends on 4.0 happening to be a power of two.

## What review changed

Three independent reviewers — `refuter`, Codex Sol, and the persona-realism theory reviewer — all failed the first build. **The reviewed version is not what shipped.**

- **The theory reviewer found a realism regression no gate could see.** The first build floored the reference merit, which cancelled the floor's growth out of the raise scale, so every bit of freed fold mass landed on CALL. Aggressive personas stopped semi-bluff raising big draws — lag 0.4718 → 0.3884, maniac 0.6099 → 0.5264. The refuter, reasoning only from gates, had passed the slice as clean.
- **The refuter disproved a claim in the approved spec.** "Structural, not arithmetical" was false: `max(L, 1.0)` returns `L`, so the strong-draw branch *was* the re-associated form the design exists to avoid. Demonstrated by refitting the station to 3.7 — one ulp on all three legs.
- **Codex found that claim C5 had no test at all.** It re-associated the non-strong expression and 77 tests passed, including all 23 frozen price vectors, while weights moved by one bit.
- **All three independently refuted the causal story** that only the nit changed.

Two gates from the first build were replaced: one that could not fail independently of the gate it duplicated, and one whose panel had no facing-a-raise node, letting a partial fix pass everything.

## Gates

Nine claims, each demonstrated **red against a named mutant** before shipping, each carrying an independence witness:

- **G-DRAW** — the dial no longer decides a strong draw, ≤ 0.030 self-difference at six priced nodes including pair+draw and facing-a-raise
- **Absolute ceiling** on the trace node, plus a **cross-persona** floor (nit must still fold strong draws far more than the station) — this replaced an absolute lower bound that was indefensible as poker and would have blocked the filed equity follow-ups
- **Raise-share pinned against the base engine**, 6 personas × 7 nodes — this is the gate that catches a lever-*invariant* level shift, which G1 by construction cannot see
- **Exact-equality vectors** for non-strong behaviour, and for the station at a **non-power-of-two dial (3.7)**
- Existing G-NODE and N-LOGIT G1 unmodified and green

`test_nlogit_g3_identity_at_authored_values_is_bit_exact` is **scoped** to exclude strong draws — unavoidable, since routing the floor's growth through the N-LOGIT feature means it is no longer inert at rest there — and **replaced** by the strictly stronger raise-share gate on those cells. Reach was re-measured, not assumed: exactly 320 of 10,368 comparisons differ, all in the raise-legal half of strong-draw cells for the five sub-1.0 personas, and the excluded-cell count is itself pinned so the scope cannot widen silently.

## Fixtures and rulings

All three re-recordable fixtures moved and were re-recorded under protocol, with attribution proven by reverting in both directions against the base commit and the old side read from the fixture, never from prose.

Two owner rulings, both revised after review:
- the `passive_fish` ⅓-pot band is now **report-only** — the theory contract marks that target directional-only, so it may bound a regression but may not define a pass — and the 80,000-deal escalation that first rescued it is deleted;
- `coverage_baseline.json` re-recorded with the graded **share** disclosed as the honest metric.

## Verification

`1430 passed, 1 skipped, 0 failed` · `ruff check` clean · `BACKEND VERIFY OK`.

Filed, not fixed here: `N-DRAWEQUITY`, `N-DRAWTURN`, `N-DRAWWEAK`, `N-FISHFLOOR`, `N-DRAWORDER`. `TH-5` is withdrawn — the theory reviewer disagreed with the premise and gave reasons.

Trail: `docs/ai-dlc/specs/n-drawloose.md` (rev 3), `ledger/n-drawloose.md` (all findings adjudicated), `reports/n-drawloose-build-state.md` (build record and traps).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

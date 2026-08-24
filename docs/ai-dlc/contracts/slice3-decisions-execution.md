# Contract map — slice-3 decisions execution (Lane A) + Lane B scope discovery

**Bottom line.** Lane A (executing the owner's six 2026-08-24 rulings) is doc/test work only —
no engine code changes anywhere. Its one code action is deleting a test, and the scan found
**two more tests built on the same withdrawn premise** that the rulings never name, plus two
prescriptive docs that would contradict the new ruling if left as-is. Lane B (population-
statistics ingestion) was found to be **already built and shipped 2026-08-06** — the roadmap's
NEXT entry is stale, which trips the misalignment tripwire; its scope is an owner decision,
recorded in the spec, not assumed here.

Scanned 2026-08-24 by two read-only contract-mapper agents (poker-coach; poker-analytics +
cross-repo). Rulings record: `../research/slice3-calldown/owner-decisions.md` (do not edit —
historical memo).

## Lane A surfaces

### Theory contract — `persona-realism-theory-contract.md`
- No semantic version; amendments are named/dated blocks (A1–A8) or numbered correction-ledger
  entries in §9 (:467-519). Follow that convention; never a version bump.
- §4 row P8 (elasticity split) at :104 — ruling 3 parks the bucket-aware fold lever here.
- §7 invariants at :432-454; the factor-order text Filed 14 disputes is at :446 (contract says
  position mult before multiway; engine applies position LAST). Text-only fix.
- **§11 (:544-563) is titled "Reviewer checklist" (items 1–15), not "pre-registration
  obligations".** Ruling 4's landing spot is ambiguous: new item 16 beside W3R-1 (:563), or
  §5a's "two obligations" (:401-409), or a new labeled block. Needs a decision.
- §3 amendment A8 item 5 (:82) already records the value-side commit slope — ruling 2 needs
  only a cross-reference to the 2026-08-24 ruling date.
- Provenance-gate test `backend/tests/test_contract_provenance.py` inspects only the
  §5a→§6 span; edits to §3/§4/§7/§9/§11 cannot trip it.

### Tests — `backend/tests/test_personas_postflop.py`
- `test_ace_high_river_alpha_ceiling` :1057-1102, `xfail(strict=True)` — named for deletion.
- **Scope gap 1:** `test_ace_high_river_alpha_guard_is_not_vacuous` :1105-1170 exists solely to
  prove the deleted guard's xfail mark is real; orphaned if left. Shares helper
  `_ace_high_river_alpha_breaches` (:1035-1054); `_measure_ace_high_fold_by_size` (:858-905)
  also becomes single-referenced.
- **Scope gap 2:** `test_ace_high_alpha_holds_for_the_station_pre_river` :908-978 asserts the
  per-bucket α ceiling pre-river for the station, citing the withdrawn 2026-08-19 ruling in its
  docstring. Not named in any ruling; leaving it green contradicts "α is per-range".
- Engine constant `_ACE_HIGH_RIVER_CALL_DAMP = 0.06` (`personas_postflop.py:715`) is untouched —
  independently pinned by `test_t3_river_damp_moves_only_the_ace_high_call_leg` (:9607-9629)
  and documented in-code (:660-714). Ruling 1 deletes a test, not the damp.

### Ledger — `ledger/flywheel-slice3-calldown.md`
- Filed line ranges: 1 :71-113 · 2 :115-153 · 4 :197-220 · 5 :223-256 · 8 :326-372 · 9 :374-416
  · 10 :418-493 · 11 :496-543 · 13 :578-650 · 14 :653-668 · 15 :671-691.
- Append-only/chronological; **no existing closed-marker convention** — closure mechanism:
  append a dated adjudication note under each Filed-N heading (chosen to match the file's
  chronological style; do not retrofit a status field).
- Filed 9 ↔ Filed 10 cross-reference each other; close them together, not independently.

### Consistency surfaces the rulings don't name (must be edited or Lane A ships contradictions)
- `contracts/flywheel-slice3-calldown.md:76-84` asserts the withdrawn per-bucket ruling as a
  "LIVE DISCLOSED TENSION"; :108 carries stale test line numbers.
- `roadmap/bot-realism-flywheel.md:356-357` describes the S3-T4 tripwire as "filed for ruling".
- Any other doc citing S3-T4/Filed 9 as live (grep at build time).

### Invariants check
No domain-purity, freq+EV, content-pack, or spot_signature surface. Verification =
`./scripts/verify.sh` + `ruff check .` after the test deletion; both green is the done bar.

## Lane B discovery (scope is an owner decision)

- The registry exists: `poker-analytics/data/targets/registry-v2.json`, hash-pinned in
  `scorer/registry.py:25-29` (v2.0.0, statdef-2026-08-06); governed by estimand-contract §g.1
  (2026-08-06-A). All four owner-ruling conditions verified satisfied: filter+date provenance
  (720-obs `raw_snapshot`), LOW confidence throughout, justified strata→persona mapping +
  sensitivity analysis (`mapping_sensitivity`, `frozen_rules`), limitations list embedded in
  every score payload.
- Consumers: `scorer/score_realism.py`, `scorer/constraints.py`, `scorer/build_covariance.py`,
  test suites (`make scorer-test`, stdlib unittest — NOT pytest).
- The poker-coach band harness / grounded WTSD bands are a DIFFERENT poker-coach-owned system
  (Stage-0 regime in the theory contract); no poker-coach tool reads registry-v2.
- Genuinely open residuals, all disclosed in-contract, none of them "ingestion":
  fold-to-3-bet pool budget vacuous (73pp > range, estimand-contract :830-843, deliberate);
  persona-tier degeneracy (2 target vectors for 6 personas — source publishes no finer
  segments); era-drift + single-site bias (unresolvable without new sources).
- Any re-fetch of `bluffaces.com/calculators/mda/` would need sandbox allowlist widening;
  the existing snapshot needs no fetch.
- Working-agreement bindings: registry/scorer owned by poker-analytics; registry edits are
  code-session work done in a worktree per that repo's working agreement *(corrected
  2026-08-24 — an earlier draft used the label "Session-F", which appears nowhere in the
  agreement; refuter finding)*; targets come from external human evidence only, never the
  theory contract; no cross-source synthesis into targets (frozen rule).

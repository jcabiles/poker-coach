# Delta spec — slice-3 decisions execution + publication readiness (2026-08-24)

**Goal (one line).** Execute the owner's six slice-3 rulings (2026-08-24) as doc/test changes,
reconcile the stale Lane-B roadmap entry, and bring poker-analytics' public-facing methodology
narrative to publication-readiness with a red-team report — no engine code, nothing published.

**Situating.** These are tails of the bot-realism-flywheel roadmap: the slice-3 close
(improvement phase, ruling A) and the "Portfolio publication path" NEXT item. Inherits that
roadmap's no-gos. Rulings record: `../research/slice3-calldown/owner-decisions.md` (this
session, 2026-08-24: D1 α per-range/delete guard · D2 commit slope IN re-anchor scope ·
D3 fold lever parked at §4 P8 · D4 adopt Filed-15 rule · D5 watch-band acknowledged ·
D6 parked items stay parked). Contract map: `../contracts/slice3-decisions-execution.md`.

## Package 1 — Lane A: rulings execution (poker-coach)

Files to touch:
- `docs/ai-dlc/contracts/persona-realism-theory-contract.md` —
  (a) dated amendment block recording: α is a per-RANGE bound; the 2026-08-19 per-bucket
  ruling is withdrawn (owner, 2026-08-24); Filed 2's residual (may a tight archetype sit near /
  cross the range-level α wall?) stays open and needs a sourced margin before any test admits
  it. Follow the file's named/dated amendment convention — no version bump.
  (b) §11: new item 16 (Filed 15) — written as a PROSPECTIVE binding obligation with a
  pass/fail reviewer check (the W3R-1 dual pattern): "a reduction floor is registered against
  the configuration proposed to ship; if the ship list changes, floors are re-derived before
  values land. Reviewer verifies: was every floor in this slice registered against the shipped
  configuration?" The amendment block states the rule binds before a slice ships, not only at
  review (both reviewers, 2026-08-24).
  (c) §7 :446: fix factor-order text to match the engine (position multiplier applied last,
  after multiway); text-only per Filed 14.
  (d) §3 A8 item 5: cross-reference the 2026-08-24 ruling (commit slope IN scope for the
  re-anchor slice).
  (e) §4 row P8: note the bucket-aware fold lever is parked here (Filed 1, owner 2026-08-24),
  built only if a slice targets the fold-to-cbet gap.
  (f) Record Filed 13 as deferred to the re-anchor slice (no row governs unopened late-street
  betting; row authored when the river leg is recalibrated).
- `backend/tests/test_personas_postflop.py` — DELETE `test_ace_high_river_alpha_ceiling`
  (:1057-1102), `test_ace_high_river_alpha_guard_is_not_vacuous` (:1105-1170),
  `test_ace_high_alpha_holds_for_the_station_pre_river` (:908-978), the 55-line narrator
  comment block :980-1034 (describes the deleted tripwire as "filed for owner ruling" —
  refuter finding 3), and helpers that become unreferenced (`_ace_high_river_alpha_breaches`
  :1035-1054; `_measure_ace_high_fold_by_size` :858-905 ONLY if no surviving test references
  it — verify before deleting). CORRECT (docstring-only) the surviving
  `test_fold_to_bet_respects_alpha_ceiling` docstring (:8421-8428), which asserts the
  withdrawn ruling as current. `_ACE_HIGH_RIVER_CALL_DAMP` and
  `test_t3_river_damp_moves_only_the_ace_high_call_leg` are UNTOUCHED. Baseline before
  deletion: 395 passed / 6 xfailed (the 6 xfails are the parametrized ceiling test —
  refuter-verified); after deletion the suite must show 0 xfails from this family.
- `backend/app/domain/personas_postflop.py` — **COMMENT-ONLY corrections, zero behavior
  change** (adjudicated exception to the engine-edit exclusion; both reviewers' top finding):
  the comment blocks at :323-370 and :1742-1748 assert the 2026-08-19 per-bucket ruling as
  settled law and name the deleted tests as its live enforcement. Rewrite those prose blocks
  to record the 2026-08-24 per-range re-ruling and withdrawal. No code token outside comments
  may change; the full suite green is the proof.
- `docs/ai-dlc/ledger/flywheel-slice3-calldown.md` — dated adjudication notes appended under
  Filed 1/2/4/5/8/9/10/11/13/14/15 headings (append-only style; 9 and 10 closed together as
  cross-referenced; 8 dissolved by D1; 4 stays parked per D6; 5 acknowledged; 11
  recording-only).
- `docs/ai-dlc/contracts/flywheel-slice3-calldown.md` — :76-84 "LIVE DISCLOSED TENSION"
  paragraph rewritten as resolved-by-withdrawal; :108 stale test refs corrected/removed.
- `docs/ai-dlc/roadmap/bot-realism-flywheel.md` — slice-3 entry's S3-T4 line updated
  ("filed for ruling" → ruled 2026-08-24, guard deleted); record the six-decisions ruling
  batch in the slice-3 entry.
- Consistency sweep: grep `docs/ai-dlc` + `backend` for live citations of the 2026-08-19
  per-bucket ruling / S3-T4 tripwire / "Filed 9" as open; fix or annotate each hit.

## Package 2 — Lane B: roadmap reconciliation (poker-coach, docs only)

- `docs/ai-dlc/roadmap/bot-realism-flywheel.md` NEXT entry "Population-statistics ingestion +
  target-registry upgrade": mark satisfied 2026-08-06 by registry v2
  (`poker-analytics:data/targets/registry-v2.json`, estimand-contract §g.1), with the four
  owner conditions verified met; note the genuinely open residuals (vacuous fold-to-3-bet pool
  budget; persona-tier degeneracy; era-drift/single-site) as disclosed limitations, NOT new
  work items. No registry content changes.

## Package 3 — Lane C: publication readiness (poker-analytics, report-shaped)

Per the roadmap's owner-ratified strategy (curated narrative public, raw exhaust private):
- `README.md` front door: what the repo is, the three write-ups, decision records,
  limitations — written for a skeptical senior-analytics-hiring reader.
- Publication-grade pass over `docs/methods/reachability-verdict-s5.md`,
  `docs/methods/detection-pilot-s6.md`, `docs/methods/estimand-contract.md` (+ score
  design/validation-failure narrative): clarity/lede/limitations per the writing rules —
  content corrections only where a claim is wrong against its own sources; no result may be
  softened, every stated limitation travels.
- Dataset/model cards with reproducibility pins (PRD §5).
- Hiring-manager red-team: fresh adversarial reviewer over the would-be-public surface;
  findings adjudicated, not auto-folded.
- Final deliverable: publication-readiness report + proposed strip list, filed for the owner.
  **The repo stays private; no visibility change, nothing is published.**

## Out of scope (explicit)

Engine or pack values (`backend/app/domain/`, `content/`) — with the ONE adjudicated
exception above: comment-only prose corrections in `personas_postflop.py`, no behavioral
diff · registry content
(`registry-v2.json`) or its pinned hashes · the finale detection run, keys, deck · the blind
play session · repo visibility flips or any external publishing · new data fetches / network
sources · the re-anchor slice itself (only its scope is recorded) · PR merges (owner-only).

## Constraints

Roadmap no-gos inherited. Domain purity, freq+EV, content-in-data invariants untouched by
construction (no engine edits). Worktree-only branch work (shared tree is concurrent).
poker-analytics edits follow its working agreement (docs/README work; no scorer code).
PRs opened autonomously on `chore/*` branches; never merged by the agent.

## Verify-by

1. poker-coach: `./scripts/verify.sh` green and `cd backend && ruff check .` clean after the
   test deletions; deleted test names absent from the suite; damp pin test still green.
2. Consistency: grep for `2026-08-19` per-bucket citations + `test_ace_high_river_alpha`
  across both repos returns only historical/adjudicated mentions.
3. poker-analytics: `make scorer-test` still green (docs-only — proves nothing broke);
   readiness report + strip list exist and name every file they judged.
4. Each package lands as its own PR; roadmap/ledger/contract edits ship in the same PR as the
   change they describe.

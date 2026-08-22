# Delta spec — improvement slice 3: calldown

**status: approved (owner, 2026-08-21)**

**Bottom line.** Slice 3 lowers the roster's continuation frequency at decisions
that already mix — the calling dials, not new mechanisms — moving each
persona's went-to-showdown rate (WTSD: showdowns divided by hands that saw the
flop) down toward its research-grounded target band, measured against the
interim band regime ratified 2026-08-21 (grounded floors, one-way downward
ceiling ratchet). It also ships the one approved new lever from the slice-2
reviews: a minimal stack-to-pot multiplier on made-value aggression, closing
the bluff-share identity's missing value side. Four build tickets, one serial
chain.

**Situating.** This is the third slice of the bot-realism flywheel's
improvement phase (roadmap: `docs/ai-dlc/roadmap/bot-realism-flywheel.md`),
ruled CORE scope on 2026-08-21 (no longer the scope valve — the reserve item
cut first if appetite runs out). Boundary inherited from slice 2's spec §6.2:
slice 2 owned degenerate or mis-invested decisions; slice 3 owns continuation
frequency at nodes that already mix. The commit brake (Stage 1 of the
went-to-showdown re-anchor work, internally tracked as W4-a — the mechanism
that raises fold merit as a seat's committed fraction of its stack grows) is
explicitly NOT in this slice — deferred past the finale with a reopening
trigger. Engine/stack work stays excluded except the two levers named here,
both merit-layer (they change how a hand's strength and price are weighted,
not the game's stakes or structure).

## Evidence base (measured 2026-08-21 at tip d351150, ratified lineup, seed 20260817)

`d351150` is the commit the roster was measured at; "ratified lineup" is the
fixed nine-seat table (`tag,tag,calling_station,tag,passive_fish,lag,
passive_fish,nit,maniac`) every flywheel measurement uses so results are
comparable across slices; seed 20260817 makes the deal sequence reproducible.

| Persona | Grounded target | 50k export WTSD | Band harness WTSD | Gap (harness) |
|---|---|---|---|---|
| nit | 20–28 | 59.5 | 63.6 | +35.6pp |
| tag | 25–29 | 54.2 | 61.3 | +32.3pp |
| lag | 26–31 | 51.9 | 57.3 | +26.3pp |
| maniac | 30–40 | 53.1 | 59.6 | +19.6pp |
| calling_station | 38–48 | 66.4 | 71.1 | +23.1pp |
| passive_fish | 33–42 | 49.1 | 54.0 | +12.0pp |

Pooled: 54.9 (export) / 61.8 (harness). Every persona sits ABOVE its grounded
band on both instruments. Full report:
`docs/ai-dlc/research/slice3-calldown/baseline-2026-08-21.md`. Invest-then-fold
events (folds after committing at least 25 big blinds at long odds — the
statistic slice 2 targeted) 987, down from 1,015; attributable to PR #205's LAG
preflop pack change altering postflop arrival — record, don't chase. Residual
air-only river folds: 144, unchanged. All-in-hand share 19.8%.

**Instrument note (binding):** the band harness (the pinned population inside
`backend/tests/test_personas_postflop.py` that the WTSD bands actually assert
against) and the 50k export (a fresh 50,000-hand simulation) are different
instruments and disagree by ~7pp pooled. Slice gates run on the BAND HARNESS —
it is what the test file asserts; the export is diagnostic. Any acceptance
criterion that could be single-seed-fragile must be pooled (averaged across
several random seeds) or paired (measured before/after on the same seeds) —
slice-2 lesson: capped-node composition read 0.960 ± 0.022 pooled, but single
seeds swung 0.92–0.99.

## Defect definition (sharper than "WTSD is high")

Price-blind continuation: the calling dials (`call_looseness` — a per-persona
multiplier on how readily a bot calls a bet, applied once per facing decision
at `personas_postflop.py:1121, 1245-1250`) are tuned so that every persona
continues too often against bets at every price, and part of the calling
weight is structurally untunable because the strong-draw floor (a lower bound
that keeps tight personas from folding big draws, at `:1228-1250`) pins the
strong-draw call bonus at dial=1.0 whenever the dial is set tighter than that.
Five of six personas sit below that floor's threshold, so tightening their
dial leaves their strong-draw calling unchanged — the dial's headroom is spent
only on the non-draw share.

## Constraints carried in (violating any is a defect)

- Interim band regime governs WTSD legs: floors = grounded floors; ceilings
  ratchet down (measurement + 3 standard deviations, rounded outward, never
  above the incumbent ceiling) after each ticket, recorded with the
  arithmetic. Upward movement past a ceiling: refused by default, escapable
  only via an attribution note the owner ratifies pre-merge.
- Ordering legs (statements that one persona's statistic must exceed
  another's): station>tag, station>lag, maniac<station are HARD. fish<tag and
  station−fish>0.10 are transition-scoped; a ticket may move either ONCE, with
  measurement + direction + the grounded pair it moves toward recorded.
- Five-seed de-robotization gate (`--all-seeds` — the tool that checks the
  roster's statistics stay separated from each other and from a frozen human
  baseline across five random seeds) at every ticket tip; binding pair (the
  two personas measured closest together, the ones most at risk of collapsing
  into each other) reported by name; LAG–TAG is the tight axis (post-#205
  tightest: seed 604 at 1.23× the required separation floor). Never rebuild
  `a5_baseline_z.json` (the frozen human-baseline artifact the gate compares
  against). WTSD is a large share of pooled distance — this slice is the
  likeliest on the roadmap to press the separation floor; watch it per
  ticket, and if it binds, that is a stop-and-report, not a tuning target.
- No new RNG draw anywhere: the action draw stays the FIRST `rng.choices`
  call, sizing second (guarded by `test_nlogit_g6...`, 8 capture RNGs — test
  doubles that record which random draws happen and in what order — plus the
  range estimator's key on that order).
- α fold-ceilings (per-hand-class upper bounds on how often a bucket may
  fold, keyed to a poker-theoretic α threshold) are ceilings only — no ticket
  may add a lower-bound fold assertion.
- `_calibrate_catcher_fold` and everything in `backend/app/domain/postflop.py`
  is hero-grading code — out of scope, category error to touch (it grades the
  human player's decisions, not the villain bots this slice tunes).
- Expected re-records per behavior ticket (slice-authorized, with provenance +
  revert-to-prove-attribution — the discipline of reverting a change to show
  a re-recorded pinned value really does trace back to it): `_GOLDEN_STATS_N200`
  (a pinned 200-hand statistical fingerprint), `_PRE_M3_FIRES` (a sibling pin),
  coverage baseline, export digests. Tolerances never widened; exact pins stay
  exact.
- Goodhart guard: every tuning choice must be defensible as sound poker
  independent of the realism metric. "Lands inside the band" is not an
  argument.
- Repo invariants: domain purity (the backend's poker logic has no web/DB
  imports), strategy in `content/` packs, freq+EV results, `spot_signature()`
  (the hash keying spaced-repetition history) frozen.

## Tickets (serial chain — every ticket touches `personas_postflop.py` and/or its test file)

**S3-T1 — Make the strong-draw calling weight tunable without deleting its
intent.** The floor at `personas_postflop.py:1228-1250` (`max(looseness, 1.0)`
on `_DRAW_CALL_BONUS[STRONG]`) was added deliberately so tight personas stop
folding big draws; it may not simply be deleted. Replace it with a form that
responds to the dial while preserving a floor on the *equity-justified* share
(design freedom to the builder, but: `calling_station` (dial 4.0) must remain
byte-identical — the guard test exists; the `rscale` CALL:RAISE coupling
(`:1643-1646`, the rebalancing that keeps the CALL:RAISE ratio steady when the
floor fires) must be re-derived, not assumed; `_call_merit_at_ref` stays the
base engine's unfloored merit). Acceptance: a dial sweep demonstrating
strong-draw call frequency now moves monotonically with the dial for the five
affected personas; station byte-identity holds; five-seed gate; bands
(interim) green; no new RNG draw.
*Prerequisite for S3-T2 by owner assignment (2026-08-18).*

**S3-T2 — Tune the calling dials toward grounded WTSD, per persona.** The bulk
of the movement. Adjust `call_looseness` pack values (and only pack values —
no new constants) per persona, largest gaps first (nit, tag, lag). Joint
constraints: each persona moves DOWN toward its grounded band without
breaching a HARD ordering leg; the two transition-scoped legs may each be
moved once with the required record; ceiling ratchet re-applied and recorded
after the ticket. Acceptance: band-harness WTSD for nit/tag/lag reduced by an
amount the ticket pre-registers after S3-T1's sweep data exists
(pre-registration at spec time would be fake precision); no persona's
aggression-factor or fold-to-continuation-bet leg leaves its band; five-seed
gate green; pooled export WTSD reported before/after as diagnostic. Expect the
largest golden re-record of the slice.

**S3-T3 — Value-side lever (approved 2026-08-21): minimal stack-to-pot
multiplier on made-value aggression.** Spec seed:
`local/session-2026-08-19/dossier-valueside.md` Option 1 (a machine-local
dossier, not in this repo's committed docs). Parity-free by construction
(reads stack/pot only — no bracket fields, so PR #199's parity guard — the
test that keeps the villain-range estimator's math matching the live bot's —
cannot trip). Same change amends theory contract §3 to document the identity's
limits (the sibling amendment named in the ratified draft's Part V). The
"identity" is the theory contract's semi-bluff EV formula tying bluff
frequency to bet size; this lever adds the missing value-hand side of that
formula. Acceptance: POOLED capped-node composition (the mix of actions at
decisions where the stack size caps the bet, "capped" meaning the bet had to
shrink because the seat did not have enough chips) moves toward the uncapped
norm (pre-registered direction, pooled-or-paired measurement only); LAG WTSD
ceiling watched (0.59 incumbent, ratcheted value may be lower by then);
five-seed gate; byte-identity where stack does not bind.

**S3-T4 — α-guard extension over ACE_HIGH + damp re-derivation gate.** Owner
ruled 2026-08-19 that α (a poker-theoretic bound on how often a hand class
should fold, described above) bounds the ACE_HIGH bucket (naked ace-high with
no pair or draw); the guard is still scoped by test-only `_CATCHER_BUCKETS`
which excludes it. Extend the guard to the ACE_HIGH river call leg. Then, ONLY
IF S3-T2 has bought the headroom (station and lag down toward grounded
bands), re-derive `_ACE_HIGH_RIVER_CALL_DAMP` (the constant that dampens
ace-high's river call frequency) against the then-current price distribution
per the ratified draft's III.2 conditions (re-measured minimum-defence
obligation — the game-theoretic floor on how often a bluff-catcher must call
to keep an opponent from profitably bluffing — resulting river continue rate,
ratchet re-applied). If headroom does not exist, the ticket ships the guard
extension alone and files the re-derivation with the measured shortfall.
Acceptance: guard is non-vacuous (fails under a deliberate damp inflation);
everything else per ticket standard.

## Out of scope

The commit brake and ANY made-hand fold change (Stage 1, deferred, trigger
recorded) · bottom-bucket price saturation · the maniac preflop 4-bet
catch-all (pack question, filed) · all-in cascade (ruled out of phase) · the
air-only river call zero (correct by design, 144 events stay) · bet-sizing
changes (anti-sizing-tell no-go) · any re-anchor of bands to final grounded
values (that is the designated re-anchor slice, internally tracked as A6) ·
hero-grading code.

## Verify-by

Per ticket: `./scripts/verify.sh` green · `cd backend && ruff check .` clean ·
five-seed derobo gate with binding pair named · band harness (interim regime)
green · ratchet arithmetic recorded. Slice close: pooled + per-persona WTSD
from both instruments, before/after table across the chain; owner blind play
impressions asked for again (they outrank the numbers).

## Interim regime as installed (PR #208, tip d351150 — ceilings ratchet further as tickets land)

nit (0.20, 0.69) · tag (0.25, 0.65) · lag (0.26, 0.59) · maniac (0.30, 0.62,
live again) · station (0.38, 0.72) · fish (0.33, 0.57). Lag and station
ceilings are incumbent-capped (raw ratchets would be 0.61/0.73), so both sit
closer to their ceilings than the formula implies — first calldown ticket
should expect them to bind earliest on any upward wobble.

## Owner rulings folded in at approval (2026-08-21)

Two contract edits ride with this spec's approval, both recorded in
`docs/ai-dlc/contracts/persona-realism-theory-contract.md`:

- Reviewer rubric §11 item 3's wording ("P3 commit brake scoped to facing-fold
  merit only?") is replaced to align with amendment A2's two-boundary scope
  (fold side and boost side, one wave, joint calibration) — the exact wording
  A2 already ratified in §4 but §11 item 3 never picked up.
- Contract §5's note (labeled C6) predicting went-to-showdown "should FALL
  once P3 and P8 land" is corrected: P8 (a preflop calling-dial split) is
  built and live and the gap did not close, so the mechanisms are recast as
  ENABLING — they remove structural obstacles, they do not themselves move
  the frequency — and the expected source of movement is this slice's
  continuation-frequency tuning.

## Review tiers

S3-T1, S3-T2, S3-T3: behavior-touching engine/pack work → persona-realism
theory reviewer + refuter + Codex Sol (an OpenAI model tier used for
cross-family second opinions, run at high reasoning effort), all briefed to
derive rather than react. S3-T4: test-guard + conditional constant → theory
reviewer + refuter minimum, add Codex Sol if the damp re-derivation fires.

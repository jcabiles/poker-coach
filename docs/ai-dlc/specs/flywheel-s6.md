# Delta spec — S6: detection-protocol feasibility pilot (rev 2, post dual review)

Slice S6 of `../roadmap/bot-realism-flywheel.md` (NOW lane). Requirements confirmed at
Gate 1, 2026-08-07; rev 2 folds all 28 accepted dual-review findings (ledger:
`../ledger/flywheel-s6.md`). Contract map: `../contracts/flywheel-s6.md`.
Governing preregistration: `poker-analytics:docs/methods/estimand-contract.md` §d
(lines 439–539) — **this spec implements §d. Every deviation from a §d-pinned parameter is
a formal amendment (bold, per §g), recorded BEFORE any judging. This spec declares three
such amendments up front (§A below) rather than smuggling them.**

> **Post-merge amendment (2026-08-07, owner-ruled, pre-judging):** the judge panel is now
> **4 judges from 2 vendors** — Claude Sonnet + Claude Opus (Anthropic) and gpt-5.6-terra +
> gpt-5.6-sol (OpenAI) — recorded as **§g.3 amendment 2026-08-07-B** in the estimand
> contract. Every "5-vendor"/"5 judges" reading below is historical; the harness and
> analysis generalize to any k (control rule `ceil(4k/5)` = 4 of 4 at k=4; deck builds with
> `--judges 4` ⇒ 328 judged calls). See the execution checklist for the as-amended run.

## Goal (one line)

Execute the §d-preregistered blind detection protocol once — 40 human + 40 bot anonymized
30-hand seat-bundles, 5-vendor LLM judge panel — and report the first (conditional,
single-player) bot-detection number plus a protocol shakedown write-up.

## §A — Pre-declared §d amendments (recorded in the contract, in bold, before judging)

1. **Buy-in spread.** §d.2 pins the bot class as "seeded self-play seats (production
   policy)". Production export resets every seat to exactly 100bb per hand while live human
   hands re-buy to a randomized [95,105]bb — a near-certain class tell. Amendment: the bot
   run uses `--buyin-spread`, replicating the live re-buy mechanism exactly (see F1). The
   policy (decision logic) is unchanged; only starting stacks match the live environment.
2. **Base-rate preamble.** §d.2 pins "judges told the true base rate is 50/50" but the
   §d.3 verbatim prompt contains no base-rate statement (internal §d inconsistency, found
   in review). Amendment: a pinned one-sentence system preamble stating the 50/50 base
   rate is added; the §d.3 prompt body stays verbatim.
3. **Duplicate-bundle class.** §d.2's per-judge duplicate is class-unpinned. With the
   40+40 deck + 1 bad-bot control, a bot duplicate makes the judge-visible mix 42 bot / 40
   human, contradicting the "50/50 … it is" statement. Amendment/clarification: each
   judge's duplicate is drawn from the HUMAN class (seeded per judge), making the visible
   mix 41/41. Control + duplicate remain excluded from the analysis deck and all deck
   statistics.

**All three amendments OWNER-APPROVED at Gate 2, 2026-08-07** — recorded in the estimand
contract (bold, per §g) by ticket T7, before the first judged bundle.

## Owner decisions (Gate 1, 2026-08-07)

1. Tooling home = poker-coach (`backend/tools/`); write-up → poker-analytics; one-line
   working-agreement addendum records this.
2. Stack-leak fix = randomize bot buy-ins (now amendment §A.1).
3. Judge panel: pinned five vendors (Anthropic, OpenAI, Google, Meta-hosted, DeepSeek);
   key acquisition = execution-blocking checklist; **owner runs judging in a real
   terminal**, keys from environment only.
4. Human corpus re-pinned at build time (frozen in manifest before any judging).
5. Bot sampling: fresh seeded self-play run, ratified 9-seat lineup.
6. Cross-persona similarity statistic DEFERRED to NEXT (named follow-up).

## Design rules (from adjudicated review findings)

**Corpus (detection_corpus.py):**
- **Exactly 40 + 40.** Human: within one SQLite read snapshot, re-pin `hand_no ≤ N`;
  enumerate candidate non-overlapping consecutive 30-hand windows; select exactly 40 by a
  seeded deterministic rule; record candidate AND selected window IDs in the manifest.
- **Human bundle integrity (fail closed):** a window is valid only if every hand number in
  it exists exactly once, is complete (`hand_over`, valid `state_json`, focus seat dealt);
  gaps/duplicates/malformed/in-progress rows REJECT the window — never skip-and-close-ranks.
- **Bot windows globally disjoint:** 40 disjoint 30-hand windows from a ≥1,200-hand spread
  run; exactly one focus seat per window, assigned across the 9 ratified seats by a
  recorded deterministic scheme. (No two bundles share any hand.)
- **Control bundle (T1 outcome + owner ruling 2026-08-07):** the §c axes cap decision
  degeneracy at ~0.54 (preflop mix tables sit outside the axis registry), so the 0.90
  "near-deterministic" build proxy is RETIRED. Control = the T1 best-effort config
  (hash `3a64601c…`, max-aggression profile; appendix below), generated with the same
  buy-in spread, rendering, and metadata treatment as the bot corpus. Its validity test
  is §d's own invalidation threshold PLUS a **one-judge pre-screen**: before the full
  paid judging run, one vendor judges the control bundle; if it is not labeled "bot",
  STOP and revisit — do not spend the remaining calls. (Rejected: bespoke non-dial
  generator — extra amendment; axis-registry extension — frozen registry, out of
  appetite.)
- **Blinding split (least privilege):** two artifacts — (i) blinded presentation manifest:
  opaque presentation IDs, rendered text, payload hashes ONLY (hashes salted with the
  presentation_id so duplicate entries don't hash-collide with their sources; **accepted
  residual, disclosed:** a holder of this file can still find text twins by direct
  rendered_text comparison — inherent to §d.2's identical-stimulus duplicate; judges
  never see the manifest); (ii) secret unblinding
  manifest: class labels, seat/persona/window map, corpus pins. **The judge harness takes
  only (i) as input and has no code path to read (ii);** only analysis joins them, after
  judging. Both local/gitignored (owner hand data; never-push umbrella).

**Renderer (one code path, canonical schema):**
- Normalize BOTH sources into one canonical hand-record schema; render only that schema.
  Board = revealed streets only (never predealt `Hand.board`); showdown seats =
  settlement-defined; identical stack/result formatting.
- Per-bundle hands re-keyed to LOCAL indices 1–30 — source `hand_no`/IDs never rendered.
- STRIPS: persona names, seat indices (→ opaque IDs from seeded shuffle), session/stake
  metadata, run_id/config_hash/analytics-only fields, absolute hand numbers. No timing.
- Golden cross-source fixtures: fold-outs, all-ins, side pots, no-showdown rivers,
  malformed inputs; tests assert on the exact outbound judge payload.
- Fold-heavy (low-action) bundles are accepted as inherent variance and disclosed as a
  limitation in the write-up — no content filter (avoids a selection bias of its own).

**Buy-in spread flag (export_analytics.py) — F1:**
- Replicates live semantics EXACTLY: nine independent integer-cent targets uniform on
  [9500, 10500] (95.00–105.00bb), drawn per hand in seat order from a distinct per-hand
  stream derived from the hand's rng seed (mirroring `sim_session.py:220-255` incl. its
  `rng_seed`-derived stream); conformance test against the live `_rebuy_seats`
  implementation — not merely a "distributions differ" test.
- **Identity:** when the flag is set, `run_id` carries a mode token
  (`run-s{seed}-n{n}-bspread-c{hash[:12]}`) and the manifest records the mode + bounds;
  spread-only manifest fields are added conditionally so the DEFAULT path's manifest shape
  and semantics are unchanged. Default path byte-identical (canonical comparison excludes
  the declared-volatile `exported_at`/`_TIMING.json`, per the S4 convention; golden tests
  freeze or exclude wall-clock fields).

**Judging harness (detection_judge.py; owner-run):**
- Preflight before the FIRST call: all five credentials verified, requested snapshot IDs
  resolved and recorded (requested vs provider-resolved both stored) in an immutable
  launch manifest.
- Vendor calls via stdlib HTTPS (python urllib) — no five-SDK dependency spike; JSON
  bodies per vendor API.
- Strict response validation: exact JSON schema, no coercion (label ∈ {human,bot},
  confidence integer 0–100); raw response always preserved. One retry with the IDENTICAL
  prompt on malformed output, then recorded-missing. Transport failures recorded
  distinctly from malformed responses and retried per an operational (non-inferential)
  backoff.
- Atomic per-(bundle,judge) checkpoint writes; resume is idempotent and cannot change
  bundle order or duplicate selection.
- Per-judge presentation order: independent seeded permutation; duplicate gets a fresh
  opaque presentation ID, inserted with no adjacency guarantee; schedule tested.
- Deterministic decoding (temp 0 or provider equivalent, recorded).

**Analysis (detection_analysis.py; structured outputs only, never parsed from rendered text):**
- Control invalidation FIRST, fail closed: panel mean over USABLE control confidences
  < 50 AND ≥4 of 5 judges individually label "bot"; any missing label counts against the
  4-of-5 conjunct; if either conjunct cannot be established → batch INVALID → only
  diagnostics/completeness are emitted, never deck statistics.
- Pinned formulas: positive class = human (confidence_human). Balanced accuracy = mean of
  human recall and bot recall over aggregate labels (panel mean confidence ≥ 50 ⇒ human).
  AUC on panel mean confidence with half-credit ties. d′ = z(P(label human|human)) −
  z(P(label human|bot)) with extreme-rate correction using class-specific usable N.
  Human-misclassification rate reported (the D3/D10 requirement).
- Missing-response rule: a bundle's panel score = mean over its usable judge confidences;
  bundles with < 3 usable judges are excluded from inferential statistics and counted in
  the completeness report.
- Bootstrap pinned: stratified by class, resample 40+40 bundles with replacement within
  class, judges fixed (each bundle keeps its judge vector), controls/duplicates excluded;
  B = 10,000; percentile intervals at 95%; dedicated seed. Understates total uncertainty
  (one human cluster) — stated in output and write-up.
- Kish n_eff: all FOUR registered uses carried into acceptance criteria (shown beside k in
  every table; evidential-weight statements use n_eff never k; agreement never reported as
  correctness; n_eff/k < 0.5 flag). Pairwise-complete error correlations; zero-variance or
  degenerate pairs → n_eff reported "unavailable", never imputed.
- **Determinism:** one master seed with domain-separated derivations (corpus selection,
  focus-seat scheme, opaque IDs, per-judge order, per-judge duplicate, bootstrap); all
  derived seeds + ordered presentation IDs stored; canonical sorts everywhere (no
  filesystem/dict-order dependence); rendered payloads hashed into the manifest.

## Files / interfaces to touch

poker-coach: `backend/tools/export_analytics.py` (spread flag + run_id mode token),
`backend/tools/detection_corpus.py` (NEW), `backend/tools/detection_judge.py` (NEW),
`backend/tools/detection_analysis.py` (NEW), tests under `backend/tests/`.
poker-analytics: `docs/methods/estimand-contract.md` (§A amendments, bold, before
judging), `docs/methods/detection-pilot-s6.md` (NEW write-up),
`docs/FLYWHEEL-STATUS.md`, `docs/WORKING-AGREEMENT.md` + poker-coach mirror (ownership
addendum). No new backend dependencies (urllib + stdlib statistics; if SciPy-grade
functions are needed, `scipy` is a declared build-time decision, not assumed).

## Out of scope (explicit)

Cross-persona similarity statistic (deferred, named) · human-judge execution · any
bot-policy, pack, or domain-core change · target-setting from the pilot number · S5 work ·
registry/scorer changes · importing commercial detection figures · frontend changes.

## Constraints

Domain core untouched; read-only DB access (no migration); strategy stays in `content/`;
`spot_signature()` frozen. Statistics never parsed from rendered text. Every artifact
traceable to (engine sha, seed, config). Owner hand data + unblinding manifest never
pushed. §d prompt verbatim (plus the §A.2 pinned preamble); vendor substitution or
wording change = amendment. Sweep scores remain exploratory-surrogate — no realism claims
from scores. All push/PR/fetch + the judging run = owner, real terminal.

## Appetite & scope valves (re-cost — Gate 2 decision)

Roadmap pins 2–3 days; BOTH reviewers independently judged full scope not credible in it.
Re-cost: **4–5 days — OWNER-APPROVED at Gate 2, 2026-08-07** (precedent: S4's Gate-2
re-cost 2–3 → 4–6). Roadmap S6 box gets the re-cost note at close, S4-style.
Pre-agreed cut order if the build overruns (roadmap valve: "shrink judge count, never
blinding"): (1) drop to 3 judge vendors (recorded amendment), (2) defer live judging +
write-up to a follow-on execution step (build accepted on stub-judge dry run), (3) B =
2,000 bootstrap. Blinding and pinned protocol parameters are never cut.

## Verify-by (what /verify-change checks)

1. `./scripts/verify.sh` green (incl. new tests) + `ruff check .` clean.
2. End-to-end DRY RUN with a deterministic stub judge on a small deck (6+6 + control +
   duplicates): valid manifests + full statistics block; byte-identical re-run given the
   same master seed (canonical comparison excluding declared-volatile fields).
3. Leak audit on the real deck: automated renderer checks (no persona strings, seat
   indices, absolute hand numbers, analytics fields; buy-in spread statistically matched
   between classes; payload hashes recorded) + golden cross-source fixtures green + manual
   spot-check of one rendered bundle per class.
4. Default-path regression: export without the flag canonically identical to pre-change
   for a pinned (seed, n, config); spread run's run_id carries the mode token.
5. Blinding split verified: judge harness has no code path to the unblinding manifest
   (test: harness package imports + input schema reject label-bearing files).
6. Live judging + write-up execute AFTER build acceptance (owner runs; §A amendments
   recorded in the estimand contract before the first judged bundle).

## Appendix: control config (T1)

**Finding: the registered §a.2 axes CANNOT produce ≥0.90 decision-level degeneracy.**
Best-effort config (`docs/ai-dlc/specs/flywheel-s6-control-config.json`,
`config_hash 3a64601cbe060373d06a93fd7cd285bd6b0d47b58b23c53ad2e1031ef088b3f8`) measured,
in **spread mode** (F1 `--buyin-spread`, the treatment the control bundle actually ships
with — buy-in mode is run-identity, not config content, so the hash is unchanged),
**degeneracy 0.5407** (fold, 3880/7176 non-post decisions) at `seed 901, n_hands 500` —
this is the OPERATIVE number. The flat-100bb number (no `--buyin-spread`) measured
**0.5393** (3876/7187) at the same seed/n — kept below only for provenance; stack depth
did not materially move the statistic here.

```
cd backend && python -m tools.probe_control_config \
  ../docs/ai-dlc/specs/flywheel-s6-control-config.json --seed 901 --n-hands 500 \
  --buyin-spread
```

(Repo convention: `tools/*.py` import as a package and must run via `python -m
tools.<module>`, not as a bare script path — same as `export_analytics.py`.)

**Why the axes cap out here (structural, not a search failure).** Preflop action
selection is drawn entirely from each pack's frozen `preflop` mix tables (`personas.py:
sample_preflop_action`) — none of the §a.2 axes touch it, only `sizing.open_bb` /
`threebet_mult` / `fourbet_mult` (bet *size*, not action frequency). At baseline, preflop
decisions are ~62% of all non-post decisions and their own modal class (fold) is only
~64% of preflop. Postflop levers (`aggression`, `call_looseness`, `bluff_freq`,
`spr_commit`, `size_elasticity`, `position_sensitivity`, `line_sensitivity`,
`multiway_bluff_damp`) can skew postflop play, but postflop volume is inherently smaller
than preflop volume per hand (baseline ≈ 0.4× preflop's decision count) and shrinks
further as folding increases (a folded seat stops acting). Given fixed preflop
composition, the theoretical ceiling for ANY single global action class — even at 100%
postflop skew — works out to roughly 0.75–0.78, well short of 0.90; several extreme
configs were tried and none exceeded ~0.54 in practice (see below).

**Configs tried** (all validated by the §c validator; personas = all 6; `postflop.*`
paths; `call_looseness` at floor 0.2 throughout):
| aggression | bluff_freq | spr_commit | extra | degeneracy (fold, n=300, seed=7/42) |
|---|---|---|---|---|
| baseline (no overrides) | — | — | — | 0.437 (fold, n=300 seed 42) |
| 5.6 | 1.0 | default | — | 0.525 |
| 0.2 | 0.0 | default | — | 0.421 |
| 5.6 | 0.0 | default | — | 0.511 |
| 0.2 | 0.0 | default | high `call_looseness`=5.0 instead of floor | 0.396 |
| 5.6 | 1.0 | default | `call_looseness`=5.0 | 0.422 |
| 5.6 | 1.0 | 0.5 | `multiway_bluff_damp`=1.0, `line_sensitivity`=2.0, `size_elasticity`=3.0 (elastic personas), `position_sensitivity`=1.0 (positional personas) — **the shipped config** | 0.538 |

Root cause of the sub-100% postflop fold share even at the floor: `postflop.aggression`
(`agg_scale`) scales BET, CALL and RAISE merit together (`personas_postflop.py:897` and
its downstream use), so cranking aggression to make *someone* bet (creating fold
opportunities) simultaneously inflates the SAME persona's own call/raise merit when it is
the one facing a bet — there is no axis that raises "opponent aggression" independent of
"own continue merit."

**Disposition:** per ticket T1's exit clause, this is reported to the director as an
axis-registration limitation, not patched with an ad hoc generator. A degenerate CONTROL
in the ~0.50–0.55 range is still directionally distinct from baseline (~0.43) and from
realistic bot play, but does not meet the spec's "near-deterministic" (>90%) bar as
written. **Owner ruling (2026-08-07): this best-effort config is ACCEPTED as the control
bundle, gated by a one-judge pre-screen before the full paid judging run — the 0.90
degeneracy proxy is retired.**

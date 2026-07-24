# Spec — Persona-Realism W0 Foundation (wave of 3 slices)

> **Roadmap slice:** `docs/ai-dlc/roadmap/persona-realism.md` → NOW / Wave W0 (W0-a, W0-b, W0-c).
> **Theory contract (worker brief + reviewer rubric):** `docs/ai-dlc/contracts/persona-realism-theory-contract.md`.
> **Contracts map (this wave):** see `docs/ai-dlc/contracts/persona-realism-w0-foundation.md`.
> **Outcome link:** the north-star = "the six villain bots make decisions that match their real-world archetype."
> W0 changes **NO bot behavior** — it builds the measuring tape (metrics), the shared inputs (denominator), and the
> anti-degeneracy infra (node-trace) that every later behavior wave gates on.

## One-line goal
Land the foundation wave: a domain-pure pot-before-aggression helper, six new harness metrics behind a
Definition-of-Done rule, and a seeded node-trace realism pack + fit-loop doc — all **pure additions**, existing
suites byte-identical, no persona behavior change.

## Packaging (owner-decided)
- **Three per-slice PRs** on three branches off a fresh `main` (files are disjoint). Execution: single implementer
  (me), sequentially, each branch off clean `main`; the wave is *structured* as parallel-independent slices
  (parallel-waves' disjoint-ownership principle) but built back-to-back for theory-contract fidelity.
- **Stop after all three PRs are open** (do not merge — gated to owner). Behavior waves W1+ resume on merged base.
- Each PR gets: Claude `refuter` + `persona-realism-theory-reviewer` + Codex Sol (`gpt-5.6-sol`) at fan-in.
- **No roadmap edits inside the slice PRs** (Sol #10): editing the one `persona-realism.md` in all three PRs would
  3-way-conflict on merge, and a slice isn't "done" until merged/verified — so the roadmap `[x]` checkboxes are marked
  **post-merge**, not now. The fit-loop doc (W0-c) is self-standing and referenced from this spec, not linked from the
  roadmap (keeps W0-c file-disjoint). Doc ownership: W0-c owns `persona-realism-fit-loop.md`; the spec/contracts/tickets
  are this planning artifact (already written), not part of any slice PR.
- **Coverage-delta per PR (Sol #10 / theory contract §7):** every W0 slice is infra/test-only and changes **no graded
  behavior**, so each PR states `cumulative graded-coverage delta: 0 (no behavior change)` explicitly rather than
  omitting it. (If the immutable initiative-start snapshot `coverage_baseline.persona-realism-start.json` is absent,
  flag it for the owner — do not expand W0's scope to create it.)

## Shared invariants (from the theory contract §7 + CLAUDE.md — apply to all three)
- **Domain purity:** `backend/app/domain/` (incl. `sizing.py`) imports nothing web/DB (`tests/test_domain_purity.py`).
- **Action draw stays the FIRST `rng.choices`** (`personas_postflop.py` action draw; `range_estimate._CaptureRng`
  depends on it) — W0 inserts no new randomness before it.
- **`spot_signature()` / `TAXONOMY_VERSION` FROZEN; graders untouched** (`grade_map*.py`, `postflop.py`). Bot/test side only.
- **Default-off byte-identity:** no new required args on any live sampler; the denominator helper is an unconsumed pure add.
- **No band re-anchor this wave** (the single authoritative re-anchor is W4; W0 adds no gate on population bands).
- **Softmax law:** W0 sets no behavioral magnitudes, so no fit-seed tuning here — but the metrics it builds are what
  every later fit loop measures against.

---

## Slice W0-a — Shared pot-before-aggression denominator

**Goal.** One domain-pure helper that reconstructs, from `state.action_history`, (1) the pot **before the current
street's most recent bet/raise increment** and (2) that **latest aggressor's raise increment** — the single
"pot before current aggression" definition the theory contract §7 requires P3 (W4-a), the F9 faced_frac fix (W1-b),
and P7 to share.

**Files to touch.**
- `backend/app/domain/table/sizing.py` — add the helper next to the existing `last_aggressor_position` (the only
  other `action_history`-walking helper). New: a small `NamedTuple` result + one function.
- `backend/tests/test_sizing.py` (or a new `backend/tests/test_pot_before_aggression.py` if `test_sizing.py` absent) —
  unit tests only.

**Design (most-grounded choice, documented).**
- Signature: `pot_before_current_aggression(action_history: Sequence[HistoryAction], street: Street) -> PreAggressionPot`
  returning `PreAggressionPot(pot_before_bb: float, latest_aggressor_increment_bb: float)`.
- **KEY CORRECTION (verified `engine.py:288, 304`):** `HistoryAction.amount_bb` is ALREADY the per-action
  **INCREMENT** — BET/RAISE store `min(size − invested_street, stack)`, CALL stores the call increment, POST the blind,
  CHECK/FOLD `0.0`. The contract-map's "amount_bb = bet-TO for BET/RAISE" was **wrong**. So **no full chip-replay is
  needed** (this is simpler than the contract map assumed):
  - `total_pot = sum(h.amount_bb for h in action_history)` (equals the live `sum(s.invested_total_bb)` — every
    increment is added to `invested_total`).
  - `latest_aggressor_increment_bb` = the `amount_bb` of the **last BET/RAISE whose `h.street == street`** (scan in
    reverse; `0.0` if the current street is unraised / checked-through).
  - `pot_before_bb = total_pot − latest_aggressor_increment_bb`.
- **Why this is the correct denominator (matches the faced_frac intent, fixes the self-re-raise bug):** the buggy
  inline formula subtracts `current_bet_to` (the bet-**TO**), which on a self-re-raise over-subtracts the actor's own
  earlier same-street chips; subtracting the stored **increment** subtracts exactly the chips the last aggression
  added. E.g. BTN bets 3, SB raises-to 9, BTN re-raises-to 21: BTN's re-raise `amount_bb = 18` (= 21 − its prior 3),
  so `pot_before = total − 18` (correct), vs the buggy `total − 21`.
- **Domain-pure:** touches only `HistoryAction` / `Street` / `ActionType` from `app.domain.spot` — no new imports.
- **Why a single helper returning both scalars:** §7 "denominator unification" — three consumers share ONE definition;
  building only pot-before would force a second helper for the increment later.
- **Call site is `play.py` (has `state.action_history`), NOT inside `sample_postflop_decision`** (the sampler receives
  only scalars — `pot_bb`, `current_bet_to` — never `action_history`). So W1-b will compute the increment at the
  `play.py` site and thread it into the sampler as a new default-off kwarg. The estimator (`range_estimate`, also
  scalar-only, `_Ctx` has no increment field) will need the same increment threaded then — **estimator-parity work is
  W1-b's, out of scope here** (W0-a has no consumer, so no divergence and byte-identity holds trivially).

**Out of scope.** Wiring the helper into `personas_postflop.py:492` (that is W1-b) · any `range_estimate` change ·
any behavior change · any new sampler kwarg.

**Verify-by (pass/fail).**
- New unit tests, all green:
  - self-re-raise (aggressor re-raises own earlier same-street bet) → `pot_before_bb` excludes only the re-raise
    increment and `latest_aggressor_increment_bb` equals the re-raise delta (the case the inline formula gets wrong);
  - fresh single raise → increment == full bet-to, `pot_before` == pot − bet-to (matches today's inline result);
  - checked-through street → increment 0.0, `pot_before` == full reconstructed pot;
  - multi-street history → current-street scoping correct (prior streets fully in `pot_before`).
- `./scripts/verify.sh` green; `ruff check .` clean; existing suites **byte-identical** (pure add, no consumers).

---

## Slice W0-b — Six harness metrics + Definition-of-Done gate

**Goal.** Extend the population harness (`backend/tests/test_personas_postflop.py`) with the six metrics the later
mechanics gate on, each **computed from what the harness observes** on today's engine, each emitting a real value.
Wire the **metric-DoD rule (D7)** as documentation each dependent slice references.

**Files to touch.** `backend/tests/test_personas_postflop.py` only (the harness *is* this file — no separate module).

**The six metrics (theory contract §6).** All are **harness-observable now** — the test holds full `HandState`, so it
derives the needed context itself; the sampler needing these inputs (W3-a) is a *separate* concern.
1. **CBet-flop-overall%** per persona — aggressor-side flop bet rate (today only fold-to-*first*-cbet exists).
2. **W$SD** — won-money-at-showdown, from `settlement.deltas` (`engine.py:66-69`, currently unused by stats).
3. **VPIP / PFR / gap** — needs a **new preflop logging path** (preflop actions are not in `log` today).
4. **Size-bucketed Fold-to-C-bet** (SMALL/MED/LARGE/OVERBET) — extends the first-responder logic with `size_bucket()`
   (`personas_postflop.py:62`) keyed on the first flop bet's size.
5. **CBet IP vs OOP** split — harness derives `in_position` per decision from public state (exclude FOLDED/ALLIN;
   **BB is IP vs SB**), independent of W3-a's sampler plumbing.
6. **Turn-barrel%** — P(bet turn | was flop aggressor), derived from the per-street action log.

**Design (most-grounded choice, documented).**
- Convert the per-decision `log` from a positionally-unpacked 3-tuple to a **named tuple**
  `PostflopDecision(seat, street, action, is_aggressor, in_position, amount_bb)` and update the ≤3 existing consumers
  (`test_personas_postflop.py:1563, 1575, 1581-1585`) to named access — eliminates the positional-unpack breakage /
  silent-AF-corruption risk the contract map flagged. Add a **separate preflop log** for metric #3.
- Compute the six in `_persona_stats` (or a sibling `_persona_stats_ext`) with the same **≥30-occurrence floor →
  `None`** convention and `_STATS_CACHE` discipline already in the file.
- **`in_position` derivation lives harness-side for now** (same rule W3-a will put in the domain); note the intended
  reconciliation when W3-a lands (switch the harness to the domain helper) — a documented, accepted duplication.
- **Metric-DoD (D7):** add a short block to the roadmap's W0-b entry / this spec stating: a downstream slice may not
  close on a HARD gate until its metric is live **and shows the expected direction**. W0-b only proves the metrics
  **compute and emit sane values on today's engine** — it does **not** assert any archetype direction (bots are
  unchanged; #5/#6 will read ~flat until W3 lands — that flatness is the correct pre-state, not a failure).

**Out of scope.** Any behavior change · any band re-anchor · asserting archetype target bands from theory contract §5
(those gates belong to the slices that move them) · adding `in_position`/`bet_prev_street` to the domain sampler (W3-a).

**Verify-by (pass/fail).**
- A new smoke test asserts each of the six metrics **computes and returns a numeric value** (or a documented `None`
  below the occurrence floor) for each persona on the existing fixture — no `NaN`, no exception, shapes correct.
- The three existing HARD gates (AF, fold-to-first-cbet, WTSD) and their bands remain **unchanged and green** (the
  `log`→named-tuple refactor must not shift any existing stat — byte-identical AF/FtC/WTSD values).
- `./scripts/verify.sh` green; `ruff check .` clean.

---

## Slice W0-c — Seeded node-trace realism pack + fit-loop doc

**Goal.** A lightweight seeded-replay pack that logs, per persona across a fixed spot set, the decision **node**
(bucket · draw class · candidate action merits · chosen action · intended prescription) so a later slice can catch
"right stat, WRONG node" (e.g. a maniac hitting its aggression number by over-valuing made hands instead of bluffing).
Plus a short fit-loop doc (D11).

**Files to touch.**
- `backend/tests/node_trace.py` (new) — the pack: a fixed list of seeded spots + a capture-rng runner.
- `backend/tests/test_node_trace.py` (new) — asserts the pack runs and logs the required fields for the seed set.
- `docs/ai-dlc/contracts/persona-realism-fit-loop.md` (new) — the measure→adjust-seed→re-measure loop + the
  single-end-of-cluster re-anchor rule, pointing at the existing fit-loop precedent (`test_personas_postflop.py:1337-1480`)
  and the metric-DoD rule.

**Design (most-grounded choice, documented).**
- **Get real merits via a capture-rng**, modeled on `range_estimate._CaptureRng` (`range_estimate.py:253-270`): its
  `choices()` records `(population, weights)` on the first call — the `weights` **are** the candidate-action merits
  passed to the action draw. So a capture pass over `sample_postflop_decision` yields the exact per-action merit
  vector **with no domain-code change and no byte-identity risk** (the sampler is called read-only). Chosen this over
  (a) instrumenting `personas_postflop.py` (touches a hotspot, risks byte-identity) and (b) N-sample empirical
  frequency (lossy) — the capture gives exact merits for free and reuses an established pattern.
- **Spot set** (fixed seeds, from the roadmap's named coverage): per persona × {IP flop, OOP flop, made pair + 1–2
  overcards, turn barrel spot, busted-draw river, multiway flop, high-commitment low-SPR}. Bucket + draw class come
  from the existing hole/board classifiers.
- **Reuse the sampler API directly** on hand-crafted hole/board/legal/history fixtures — **no dependency on
  `_play_hand`** (keeps W0-c file-disjoint from W0-b) and **no `range_estimate` dependency** (no parity risk).
- **Lightweight, no new framework:** the pack is a plain function returning a list of trace rows + a pytest asserting
  structure; no golden-file brittleness (assert fields present + non-empty + merits sum > 0, not exact values).

**Out of scope.** Any behavior change · asserting realism *thresholds* (that is each behavior slice's job — W0-c only
proves the trace is produced) · any domain-code edit · `range_estimate` changes.

**Verify-by (pass/fail).**
- `test_node_trace.py` green: the pack runs for the full seed set and every row carries
  `{persona, spot_id, bucket, draw_class, action_probabilities (non-empty, sum≈1 or single-action fallback),
  chosen_action, intended_prescription}`.
- `docs/ai-dlc/contracts/persona-realism-fit-loop.md` exists (self-standing; referenced from this spec).
- `./scripts/verify.sh` green; `ruff check .` clean; existing suites byte-identical (new files only).

---

## Review dispositions (fan-in 2026-07-24 — refuter + theory-reviewer + Codex Sol)

Theory-reviewer: **GO**. Refuter + Sol: **NEEDS-WORK**, all findings spec-precision (plan shape holds). Resolutions
below **govern implementation** where they refine a slice section above.

**W0-a**
- **[Sol#1 / Refuter#1, HIGH — amount_bb semantics]** `HistoryAction.amount_bb` is ALREADY the per-action
  contribution (verified `engine.py:288,304`; empirically `RAISE` bet-to-20-after-3 stores `17`). Helper = accumulate
  `amount_bb` directly; do NOT subtract prior street investment. Field named `latest_aggressor_contribution_bb`
  (= the contract's "latest aggressor increment"). `pot_before_bb = sum(amount_bb) − latest contribution`. **Done in
  the W0-a design above.**
- **[Sol#2 / Refuter#1, tests]** Build test histories by driving `start_hand`/`apply` (never hand-author amount_bb).
  Cases: fresh single raise, **self-re-raise (explicit numeric assertion vs a hand-computed value)**, checked-through
  street, multi-street, **blind-raiser (BB raise-to-4 stores 3)**, **incomplete all-in raise**, **short all-in call**,
  **multiway bet/call/raise**. Pin `pot_before_bb == live_pot − latest contribution`.

**W0-b**
- **[Refuter#4 / Sol — sibling fn, byte-identity]** Leave the existing postflop `log` 3-tuple AND `_persona_stats`
  (AF/FtC/WTSD) **untouched**. `_play_hand` returns a named tuple `HandResult(state, settlement, log, saw_flop,
  had_limper, had_3bet_plus, decisions, preflop_log)` (update its 3 callers to named access). New sibling
  `_persona_stats_ext` computes the six metrics from `decisions`/`preflop_log` and returns its own named tuple — zero
  risk to the existing positional consumers (`:1600`, `:1627`).
- **[Refuter#2 — drop is_aggressor]** `PostflopDecision` = `(seat, street, in_position, action, bet_fraction)` — **no
  is_aggressor field**. C-bet (#1) and turn-barrel (#6) lineage are derived from the per-street bet/raise events in
  the log itself (the harness has full history); do NOT thread the whole-hand `last_aggressor_position`.
- **[Refuter#2 — general IP/OOP]** Snapshot `in_position` at decision time (in `_play_hand`, has `state`) via the FULL
  rule (roadmap W3-a A2 verbatim): "no live not-folded/not-all-in opponent acts after me this street; exclude
  FOLDED/ALLIN; **BB is IP vs SB**; 3+-handed = last live seat." Not just the BB-vs-SB case.
- **[Sol#3, HIGH — preflop RNG safety]** Log ONLY the already-applied preflop `Decision` (the one passed to `apply` at
  `:1267`). Add **no** new `rng` draw; do NOT "clean up" the existing double-sample. VPIP/PFR/gap count once per
  seat-hand from applied actions.
- **[Sol#5 — size bucket]** Store `bet_fraction = decision.size_bb / pot_bb` (snapshot at decision, pot available at
  `:1271`); bucket via `size_bucket()`. Never bucket raw `amount_bb`.
- **[Sol#7 — W$SD definition]** Define exactly: `W$SD = (showdown seats that WON ≥1 pot) / (showdown seats)`, using
  settlement winners (verify shape), NOT net `deltas` (a side-pot winner can be net-negative).
- **[Sol#4 / Refuter#3 — golden byte-identity]** T-b1 Done adds a one-off exact-equality check: capture the six
  personas' `(af, ftc, wtsd)` at a fixed n before the refactor, assert `== pytest.approx(..., abs=1e-9)` after (not
  band membership — bands are too wide to prove identity).

**W0-c**
- **[Sol#8 — capture rng]** The capture rng WRAPS an inner seeded `random.Random`: on call 1, record
  `(population, weights)` AND delegate the draw to the seeded rng (a real chosen action); later calls delegate without
  overwriting. Assert call-1 population is `ActionType` values (so the sizing draw at `personas_postflop.py:567` can
  never be mistaken for the action draw).
- **[Sol#9 / theory#2 — naming + non-degenerate fixtures]** Capture is the NORMALIZED probability vector — name the
  field `action_probabilities`, not "merits" (raw pre-clamp merits would need domain instrumentation = out of scope).
  Choose the seeded spots so none hits the zero-total-merit fallback (`range_estimate.py:290`); assert
  `sum≈1 OR single-action fallback`.

**Cross-cutting**
- **[Sol#10 — packaging]** No roadmap edits in slice PRs; coverage-delta=0 stated per PR; fit-loop doc self-standing
  (see Packaging above).
- **[theory#1, LOW — doc paths]** `range_estimate` / `engine` references are under `backend/app/domain/table/`.
- **[Refuter#5, LOW — flake]** A pre-existing order-dependent flake exists in `test_sim_session.py`
  (`test_reveal_unavailable_on_live_hand_and_unknown_scope`) — unrelated to this wave (disjoint file); note it in a PR
  description only if it surfaces, do not bisect.

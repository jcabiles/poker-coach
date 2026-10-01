# Contracts — M2, retune the LAG at 6-max (plus the board-straight fix)

Mapped 2026-09-30 by a read-only contract scan (Sonnet). M2 is the slice of
`../roadmap/bot-realism-6max.md` that retunes the loose-aggressive (LAG) bot at 6 seats only.

## Bottom line
- **`spot_signature()` cannot change under either part of M2**, so spaced-repetition history is
  safe. It hashes only spot fields, never hole cards or hand strength.
- **The contracts most likely to break:**
  - the two golden decision digests in `test_bot_decisions_golden.py`, and the 9-max pinned stats
    goldens, which move on any bot decision change;
  - the frozen range-lint inventory, which also runs at 6-max and fails on any new row gap, dead
    token or weight interleaving in the new `unopened` ranges;
  - wholesale replacement of the nested `sizing` and `sizing_by_node` dicts by an override.
- **Raise size comes from the flat `postflop.sizing` block only.** `sizing_by_node.raise` is
  unreachable by bots.
- **No 6-max test guards post-flop dial changes** apart from the golden digest and the baseline
  tool, because the frozen stat bands are 9-max only.

## Invisible contracts

### A. LAG preflop content
- **Runtime source.** `content/personas/lag.json` `preflop[]` (hand-listed `combos` strings) is the
  only runtime source (`PERSONA_DIR` personas.py:25; `load_persona_packs` globs `*.json` at :61).
  `content/personas/ladders/lag.unopened.json` is a build-time curve spec, never read at runtime
  (rr_emit.py:7-9).
- **Generator and drift gate.** `backend/tools/rr_emit.py`
  (`python -m tools.rr_emit ../content/personas/ladders/lag.unopened.json`) generates the nine
  `unopened` nodes. `test_rr_emit.py:313-398` asserts the base `lag.json` equals the spec's output
  and pins `emits` to `content/personas/lag.json`. That gate covers the base pack only; a
  `six_max/lag.json` is outside it. The spec's strictly-increasing-toward-the-button check
  (test_rr_emit.py:~414) applies to the spec only.
- **Tier shape.** Spec tiers are a core (raise 1.0) plus a one-class slope edge (raise 0.4,
  fold 0.6) (ladder:118-130), which appear as two mixes per seat (lag.json:273-345).
- **Share-to-RFI mapping.** Raise-first-in (RFI, the share of hands opened when everyone before
  has folded) is approximately the combo-weighted share: pair 6 combos, suited 4, offsuit 12, out
  of 1326, times the raise weight. Authored versus measured: LJ 37.62 vs 37.7; HJ 47.63 vs 47.0;
  CO 48.6 vs 48.6; BTN 57.83 vs 56.9; SB 46.43 vs 51.9 (m1-baseline.md:46-50). `raise_pct` is an
  annotation only (rr_emit.py:21-22).
- **6-max seats.** BTN, SB, BB, LJ, HJ, CO (deck.py:34-46). An override for `unopened` must
  answer all six, BB included. The baseline tool measures RFI at LJ, HJ, CO, BTN, SB
  (sixmax_baseline.py:44).
- **Merge semantics** (personas.py:87-108):
  - A listed facing deletes every base node of that facing; override nodes are appended at the
    end of `pack.preflop`.
  - Override `preflop` is a dict keyed by facing; each node's `facing` must equal its key
    (persona_override.py:52-62).
  - The override model forbids extra keys (:18) and requires `domain: "persona_override"`,
    `table_size: 6`, and a non-empty change set (:64-68).
  - Unopened actions are fold, limp and raise only (models.py:85). Explicit-position nodes precede
    the single wildcard, with no position overlap (models.py:501-539).
- **Other facings are unaffected** (`vs_rfi`, `vs_3bet`, `vs_4bet`, `vs_limpers`). LAG VPIP and PFR
  still move with a tighter RFI: M1 measured 33.6% and 28.3%, inside the cited 24–40 and 20–35.

### B. Validators that run on a merged 6-max LAG
1. `test_persona_pack_invariants.py` (params 9 and 6, :41-48), including the merged-fixture test
   (:369):
   - post-flop sizes on the grid {0.33, 0.5, 0.75, 1.0, 1.5} (:54-73; sizing.py:58);
   - preflop size keys within the grader caps (:91-133);
   - a regular's open at most 3.0 outside the blinds (:181-215);
   - no open-size mix puts more than 0.90 on one size (:232-240);
   - no mix fully shadowed by earlier mixes, none expanding to nothing (:246-277);
   - every facing answers all seated positions for opener and cold roles (:293-363).
2. `test_pack_range_lint.py` (params 9 and 6, :291-295) compares computed defects to a frozen
   inventory (:146-288) by exact equality: row gaps (:118-125), inert tokens (:109-115; inventory
   empty), and weight interleaving (:126-136). Fixing a listed defect also fails, so the inventory
   is edited in the same commit.
3. `test_persona_range_edges.py` (params 9 and 6, :57-64): no non-fold action may carry more than
   15% of the deck deterministically per node (:37, :67-106); `("lag","unopened")` is exempt by
   name (:44).
4. `test_persona_size_ecology.py` (params 9 and 6, :185-192) bites only if sizing is overridden:
   - nodes scored: flat, cbet_dry, cbet_wet, cbet_mono, turn_barrel, river_value (:91);
   - class tell ≤ 0.667, persona tell ≤ 0.333, size posterior ≤ 0.70 (exempt: flat@1.5,
     cbet_wet@1.5), class posterior ≤ 0.85 (:134-157, :285-339);
   - each persona's flat block needs ≥ 0.10 on small (0.33), medium (0.5) and large (0.75 + 1.0)
     (:102, :492-518);
   - LAG preflop open/3-bet/4-bet pins are (3.0, 3.5, 2.4) (:537-559), so overriding
     `sizing.open_bb`, `threebet_mult` or `fourbet_mult` fails.
5. Model validators (`PersonaPostflop`, models.py:303-488): `aggression` > 0; `continue_ref` in
   [0.05, 8.0] and absent rather than null; `line_sensitivity` in [0, 2]; `late_street_bet`,
   `bluff_freq`, `multiway_bluff_damp`, `position_sensitivity` in [0, 1]; `spr_commit` > 0.
   `stickiness` must be authored while `call_looseness` or `size_elasticity` is unset (:420-444).
   Sizing distributions need float keys > 0, weights > 0, sum ≈ 1 (:285-299). Override keys must
   name `PersonaSizing` or `PersonaPostflop` fields (persona_override.py:38-50).
   **`postflop.sizing` and `postflop.sizing_by_node` are replaced wholesale** (personas.py:98-104);
   a partial `sizing_by_node` drops the other nodes, which then fall back to flat `sizing`
   (personas_postflop.py:904).
6. Runtime guards: out-of-range `continue_ref` or `line_sensitivity` raise at the bot's first
   decision (personas_postflop.py:2000-2006, 2161-2167).
7. Most other tests load packs at 9 seats and cannot see the 6-max LAG.
8. `persona_override_fixture.write_fixture_content` copies only top-level `*.json`, so a real
   `six_max/lag.json` does not collide with fixture tests.
9. `sim_session._packs` is cached per table size (sim_session.py:178-180); a running dev server
   needs a restart to pick up an edited override.

### C. Post-flop dials (personas_postflop.py unless stated)
- **`aggression`:** `agg_scale = min(aggression, 5.6)` (:1492, cap :781). Scales value and
  semi-bluff RAISE merit when facing a bet (:1766-1768) and BET merit when unopened (:1806-1808).
  Bluff cells ignore it. It also moves c-bet frequency and aggression factor.
- **`bluff_freq`:** `bluff_mass = bluff_freq * noise * multiway_bluff_damp^(opp-1)` (:1491). Sets
  air/ace-high bluff bets (:1780-1802) and bluff raises at 0.3 × the mass (:1752,
  `_BLUFF_RAISE_FACTOR` :480). Moves the air c-bet rate.
- **`call_looseness`** (falls back to `stickiness`, :1484): multiplies CALL merit (:1688-1695).
  `rscale = looseness/continue_ref` multiplies RAISE entries (:2161-2196), so raise-given-continue
  is independent of it (:2044).
- **`continue_ref`:** a divisor on facing-node RAISE merit (:2161-2196). Raising it lowers raises
  relative to calls and folds, at facing nodes only, so c-bets are unaffected. Documented as never
  re-synced to `call_looseness` (models.py:354-358).
- **`stickiness`:** for the LAG (no `size_elasticity`) it only sets the price exponent
  `2.2 * stickiness^-0.15` (:984-986).
- **`line_sensitivity`:** scales CALL and RAISE by `exp(-1.0 * sens)` when the aggressor also bet
  the prior street (:2000-2014).
- **`sizing_by_node.raise` is dead for bots.** `postflop_node_key` returns "raise" only if CALL is
  legal (sizing.py:143-145), `_sizing_dist` reads nodes only if `is_aggressor`
  (personas_postflop.py:902-904), and `is_aggressor` means this seat made the last bet or raise
  (play.py:260). Raises therefore draw from flat `sizing` (LAG: 0.33:0.2, 0.5:0.4, 0.75:0.29,
  1.0:0.11). The raise-to amount is `current_bet_to + f*(pot_bb + to_call)`, clamped to the legal
  bracket (:2217-2222; sizing.py:162-174). Bluff raises tilt larger via `_bluff_size_factor`
  (:892-896, 2214-2215). Flat `sizing` also sizes donk leads and check-raises, not c-bets or
  barrels. Hand arithmetic (not run): about 3.5× a 0.33-pot lead at f=0.5, about 4.8× at f=0.75.
- **`spr_commit`:** at stack-to-pot ratio at or below it, made hands and strong draws get the
  commit transform (`_COMMIT_AGG_BOOST` 3.0, :481, applied :1886-1932).
- **Opponent persona dependence: none.** The decision signature (:1411-1428) takes only opponent
  count and line context. Making the LAG raise the station specifically less needs a code change.
- **Frozen bands are 9-max only** (`BANDS`, test_personas_postflop.py:2994; `_GOLDEN_STATS_N200`
  :4397-4403).

### D. Board-straight bug blast radius
- **`spot_signature()` is unaffected.** It hashes spot fields only (srs.py:48-163); hole cards are
  excluded by design (srs.py:3-8); srs.py never imports personas_postflop.
  `sim_session._sim_signature` (:1136-1154) is also independent. No migration, no FE type change.
- **Callers.** `_made_bucket` has one production caller, `strength_bucket` (:221), which feeds
  `sample_postflop_decision` (:1485; bot play via play.py:29), `range_estimate.py:487` (villain
  range view, sim_session.py:1472-1534), `postflop_context.busted_draw_kind` (:225-236),
  `tools/export_analytics.py:256`, and two probes. Grading, providers, review, drill and srs do not
  consume it.
- **Side effects beyond bot decisions:**
  - the analytics export's Parquet `hand_class_bucket` column changes value for board-made hands
    (export_analytics.py:253-257; tools/poker_events.odcs.yaml:386-391), with no schema change;
  - `busted_draw_kind` requires a river AIR or ACE_HIGH bucket (postflop_context.py:229-230), so a
    demotion to a high-card bucket could newly create busted-draw river bluffs.
- **Where hands can differ.** A board-only hand needs five board cards, so only the river (and
  four-card board quads earlier) is affected. `_eval5` tuples: straight `(4, high)`, flush
  `(5, ranks)`, boat `(6, trips, pair)`, quads `(7, quad, kicker)`, straight flush `(8, high)`.
- **Existing rule to imitate.** `cat == 3` (:123-124) returns MONSTER only if the trips rank is in
  the hole, else a high-card bucket. Rank membership does not generalise to straights (a hole 6 on
  9-8-6-5-7 is "in" the straight but adds nothing). Comparing with the board-only best five is
  exact on the river.
- **Tests pinning MONSTER for board-only hands:** none found; existing straight tests use
  contributing hole cards (test_personas_postflop.py:97-103, 136-146).

### E. Golden fingerprint test (`backend/tests/test_bot_decisions_golden.py`)
- 360 hands per size (:16), seeds 20260927 (:17-18), digests pinned 2026-09-27 (:20-24). Each
  hand's fingerprint is SHA-256 of ordered (seat, position, street, action, amount_bb), blinds
  included (:27-42); the combined digest hashes the joined per-hand digests (:45-46).
- 9-max: lineup `DEFAULT_LINEUP[i % len]`, button `i % 9`, each hand seeded from one master rng
  (:49-61).
- 6-max: `run_baseline(360, seed)` (:73), LAG at seat 2. One changed LAG decision displaces the
  shared rng stream for later hands.
- `per_hand_digests(table_size)` (:64-76) returns the per-hand list. No script prints a per-hand
  diff today.

### F. Baseline tool (`backend/tools/sixmax_baseline.py`)
- **Run** (from `backend/`): `PYTHONPATH=. .venv/bin/python -m tools.sixmax_baseline --session
  <uuid> --max-hand-no <n> [--hands 6000] [--seed 20260926] [--db PATH]` (:19-21, 229-250). It
  needs the real session in the local SQLite database. `run_baseline(n, seed)` is database-free and
  deterministic (test_sixmax_baseline.py:91).
- **Setup:** seat 0 TAG stand-in, 1 nit, 2 LAG, 3 and 4 TAG, 5 station (:35-42); fresh 95–105bb
  stacks per hand (:9-12, 75).
- **Reports per bot** (:90-99): VPIP, PFR, RFI by LJ/HJ/CO/BTN/SB, flop c-bet, WTSD, with Wilson
  intervals, plus the VPIP/PFR fidelity check (:121-153).
- **Raise-when-facing-a-bet frequency:** exists in `table_stats.stats_for`
  (`{street}_raise_vs_bet`, `{street}_faced_bet`, table_stats.py:298-301), printed for real
  sessions by `tools/export_session.py:222-228`, but not surfaced by `measure()`.
- **Raise size as a multiple of the bet:** not computed anywhere. Replay rows carry `amount`,
  `to_call` and `street_inv_before` (table_stats.py:160-168), so it is derivable; the natural home
  is `stats_for`, then `measure()`.

## Integration points
- Loader: `load_persona_packs` (personas.py:45-84), `_apply_override` (:87-108).
- Live callers: `sim_session._packs` (:178-180, cached), `advance_to_hero` (sim_session.py:275,
  1091), `bot_decision` (play.py:234), the villain-range endpoint (api/v1/simulate.py:296).
- Tools: `export_analytics.play_one_hand`, `sixmax_baseline.run_baseline`, probes.
- Tests that load at 6 seats: `test_persona_pack_invariants`, `test_pack_range_lint`,
  `test_persona_range_edges`, `test_persona_size_ecology`, `test_bot_decisions_golden`,
  `test_persona_table_override`, `test_sim_session_table_size_packs`.
- Hotspots (`grading.py`, `alembic/versions/`, `frontend/src/api/types.ts`): none need edits.

## Risk notes
1. Both golden digests re-pin; the 6-max one moves for every hand after the LAG's first changed
   decision (rng displacement).
2. Fix-caused 9-max changes cannot be told apart from displacement without a purpose-built
   per-hand diff (none exists).
3. The range-lint inventory is exact-equality at 6-max: new gaps, dead tokens or interleavings in
   the new `unopened` ranges fail.
4. Wholesale replacement of `postflop.sizing` can break the size-ecology gates.
5. Tightening RFI lowers LAG VPIP and PFR toward the bottom of their cited ranges.
6. Post-flop dial changes at 6-max have no frozen-band guard.
7. Demoting board-made hands changes Parquet `hand_class_bucket` values (a data contract with the
   analytics repo) and, if demoted to a high-card bucket, can create new busted-draw river bluffs.
8. A running dev server caches packs per process; changes appear only after a restart.
9. `sizing_by_node.raise` is dead for bots; editing it changes nothing.

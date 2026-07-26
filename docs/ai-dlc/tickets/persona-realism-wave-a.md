# Tickets — persona-realism Wave A

Spec: `docs/ai-dlc/specs/persona-realism-wave-a.md` · Contracts: `docs/ai-dlc/contracts/persona-realism-wave-a.md`

> **Provenance.** T-ARR / T-TRACE / T-ANCHOR / T-STICKY / T-REJECT were drafted by the specialist
> analysts that personally verified each finding in the 181-hand review, while their analysis context
> was live. The **traps** sections are the most valuable content here — each is the specific way that
> analyst expects a competent worker to get the ticket wrong. Do not skip them.

## DAG

> ✅ **UNBLOCKED 2026-07-26.** PRs #121–#124 merged (main at `8bc96e1`); the suite went from
> **11 failed / 1054 passed** to **1071 passed / 1 skipped**. Every pinned constant below was
> re-measured against the merged baseline and **held** — T-ANCHOR ratios drift < 0.003, T-TRACE is
> bit-identical, T-ARR's arrival is BTN 8% / roster 36% (both bands still contain it). See the spec's
> resolved-blocker table for the full before/after. **T-STICKY's baseline digest still must be captured
> on merged `main` before any edit.**

```
        (merge #121–#124 first — main is red)
                      │
T-EXPORT ──┬──► T-REJECT            (T-EXPORT owns backend/tools/__init__.py)
           │                        (T-REJECT also BLOCKED on decision B1 below)
T-STACK ───┴──► T-ANCHOR ──► T-STICKY
   ▲              (serial spine; SHARED-FIXTURE ordering — see below)
   └── lands + re-records fixtures FIRST

T-TRACE        (fully independent — clean file, no contention)

T-ARR          (independent logic, but shares test_personas_postflop.py — merge after T-ANCHOR)

T-REVIEWER     (docs only, any time)
```

**Parallel-safe:** `{T-EXPORT, T-TRACE, T-REVIEWER}` may run concurrently. `T-REJECT` follows T-EXPORT.

**⚠️ T-STACK → T-ANCHOR is now FORCED (added post-review).** Both move the *same* seeded fixtures
(`_GOLDEN_STATS_N200`, `coverage_baseline.json`, limper belt) — T-STACK via the SPR-distribution shift,
T-ANCHOR via context threading on the live bot path. Run in parallel, the second re-records what the
first already moved and the anti-laundering delta becomes unattributable — **the exact failure that
produced today's red `main`** (#118 and #119 built concurrently, neither seeing the other). T-STACK
lands and re-records first; T-ANCHOR re-records on top; each reports its own delta separately.

**T-ANCHOR tripwire caveat while main is red:** the frozen golden
`test_persona_stats_byte_identical_after_log_refactor` is **already failing** (calling_station AF
`0.3973509933774834` vs golden `0.3788300835654596`), so its red/green state cannot discriminate "my
change broke it" from "already broken." The two *bluff-ordering* tests are unaffected — both reviewers
confirmed they currently pass and are mechanically immune, so the primary T-ANCHOR tripwire still holds.

**Wave-wide no-gos:** no `BANDS` edit · no Alembic migration (none needed) · no authored-strategy
change (no range or lever-value edits) · no mapper widening · no closing on "the constant is in the code."

---

## T-EXPORT — commit the session exporter as a repo tool

**Goal:** turn a stored sim session into per-persona hand packets plus tracking stats, so every later
ticket can say "run this and check X."

**Owned files:** `backend/tools/__init__.py` (NEW — **sole owner in this wave**) · `backend/tools/export_session.py` (NEW)

**Mechanism:**
- Reuse `app.db.session.engine` — do not hardcode a DB path, or the tool reads a different DB than the app writes.
- **Per-hand starting stack must be reconstructed** as `stack_bb + invested_total_bb` from that hand's
  `SimHand.state_json` (pattern: `sim_session.py:1188-1191`). `SimSeat.stack_bb` is a *current* value
  overwritten every settlement — there is no historical ledger.
- **Bot decisions are not in `SimDecision`** (hero rows only). Parse `state_json`'s `action_history`.
- Wrap `HandState.model_validate_json` in try/except-and-skip — `state_json` has no version field.

**Acceptance:** emits per-persona markdown packets (hole cards, position, per-street action annotated with
each actor's persona, made-hand category, showdown result) + a stats block (VPIP/PFR/3bet/limp/WWSF/WTSD,
per-street action mix, per-position VPIP/PFR).

**Done-condition:**
```
cd backend && python -m tools.export_session --session adaadc548d6f499c965821a617c900df
```
reproduces the review's per-persona table: nit VPIP 15.0/PFR 12.8 · tag 13.0/9.7 · lag 26/21 ·
maniac 25.4/16.0 · calling_station 46/0 · passive_fish 35/2 (±0.5pt).

**Trap:** `action_history` entries carry `position`, never `seat`, and the button rotates every hand.
A worker who assumes seat↔position stability **silently mis-attributes every hand after the first
rotation** and the stats will look plausible. Build a per-hand `position → seat` map from that hand's own
`state.seats` (pattern: `sim_session.py:1478-1479`), then join to `SimSeat.persona_type`.

---

## T-STACK — reset each seat to ~100bb per hand

**Goal:** stop the table drifting deep (median 130bb, 44% of seat-hands >150bb) so every SPR-dependent
behaviour is fitted against the 100bb game the content and grader are written for.

**Owned files:** `backend/app/services/sim_session.py` · `backend/tests/test_sim_session_buyin_cap.py` (**rewrite**)
· `backend/tests/test_sim_session.py` (**added post-review** — `test_bust_triggers_rebuy_and_2dp_ledger:211`
asserts the winner ends at `stack_bb=199.55, buyins_bb=100.0`; under an unconditional reset that becomes
≈`stack_bb=100.0, buyins_bb=0.45`) · `backend/tests/test_simulate_api.py` (**added post-review** — `:184`
explicitly documents carry-over; its assertion may pass by accident because blinds/bot actions already moved
hand-two stacks, so it no longer tests its stated contract and must be replaced with a true **pre-action
starting-stack** assertion)

**Mechanism:** make `_apply_settlement` (`:176-203`) unconditional — every seat targets
`_STARTING_STACK_BB` each hand, not just busted (<1bb) or over-cap (>200bb) seats.

**⚠️ This reverses part of W5-c3 (PR #117).** `test_cap_leaves_stacks_inside_band_untouched:107-118`
asserts a within-band stack is left **untouched** — the literal opposite. That file is rewritten, not
re-run. Owner adjudicated the deep-stack table a bug on 2026-07-25. Also update the now-stale W5-c3
rationale comment at `:119-127`.

**Acceptance:** every hand starts every live seat at ~100bb; `net_bb` still shows cumulative session P&L.

**Done-condition:** a fresh 20-hand session has, at every hand start, **every live seat's stack exactly
`100.0`** (median `== 100.0`, max `== 100.0`, min `== 100.0`); and the ledger invariants hold exactly —
for every seat `net_bb == stack_bb - buyins_bb` at all times, and `sum(net_bb) over all 9 seats == 0.0`
(±0.01 for 2dp rounding) after every settled hand; and at least one seat has `net_bb != 0` after 5 hands
(proves the reset did not also zero the P&L). `test_sim_session.py:219-228` (chip conservation) stays green.

**Trap:** **breaking the `net_bb` invariant.** `net_bb = stack_bb - buyins_bb` is rendered live in
`SimLedger.tsx:5-6`. The existing convention is that any correction moving `stack_bb` absorbs the same
delta into `buyins_bb`. A reset that skips this makes every seat's displayed net read ~0 after hand 1.

**Expected non-bug:** persona AF/WTSD will move even though no persona file is touched — `spr_commit` is a
step function with zero gradient, so changing the SPR distribution changes behaviour. **Do not re-tune a
lever to compensate.**

---

## T-ARR — node-occupancy counters

**Goal:** count, per persona × position × preflop facing-node, how often a seat's **first** preflop
decision lands in each node — so a reviewer can tell "the ladder is wrong" from "the ladder is unreachable."

**Owned files:** `backend/tests/test_personas_postflop.py` (additive only)

**Mechanism:**
- `_play_hand` already computes and discards both halves: `facing = _preflop_facing(state)` (~`:1809`) and
  `seat_state.position`. **Capture at that existing call site — do not re-derive.**
- Add `preflop_nodes` to `HandResult` (~`:1739`); append in the preflop branch guarded by a per-hand `set`
  of seats already recorded. **Do not change `preflop_log`'s 2-tuple shape** — `_preflop_aggressor` and
  `_hand_cbet_stats` unpack it positionally.
- In `_persona_stats_ext`, add `node_hits[(position, facing)]` and `node_opps[position]`; emit as a new
  `ExtStats` field `occupancy`. `ExtStats` is attribute-accessed everywhere with one all-keyword
  construction site (`:2489`) — appending is safe. **Do not confuse with `_persona_stats` (`:2155`), which
  IS unpacked positionally at `:2602`, `:2641`, `:2784`, `:2816`.**
- Facing keys are the five `PersonaFacing` literals; positions the nine `Position` values.
- **Denominator is first-decision-per-seat-hand.**

**Done-condition:**
```
cd backend && python -m pytest tests/test_personas_postflop.py -k "occupancy" -q
```
Assert on the **roster-pooled** vector: `occupancy["UTG"]["unopened"] == 1.000` exactly ·
`0.05 <= occupancy["BTN"]["unopened"] <= 0.12` · `0.33 <= roster_wide_unopened <= 0.43` · `unopened`
share monotone non-increasing UTG→BTN across the seven non-blind seats. Print the 9×5 grid on failure.

**No-gos:** no second simulation loop (breaks the frozen ≤12s budget) · no touching `_persona_stats`,
`_preflop_facing`, or anything under `app/domain/` · **zero new rng draws**, so the existing AF/FtC/WTSD
golden must stay byte-identical — if it moves, you added a draw.

**Traps:** (1) **Counting every preflop decision instead of the first.** UTG always acts first, so
`occupancy["UTG"]["unopened"]` must be exactly 1.000; a reading near 0.7 means you counted UTG's later
decisions after facing a 3-bet, and every cell is contaminated. (2) **Freezing exact goldens.** All six
personas share one rng stream, so sibling tickets shift occupancy a point or two with no preflop logic
change. Use bands.

---

## T-REJECT — mapper rejection-reason counters

**Goal:** when the Simulate→Spot mapper returns `None` postflop, record **why**, so the later `T-cover`
widening is prioritized off measured counts instead of anecdote.

**Owned files:** `backend/app/domain/table/grade_map_reject.py` (NEW) · `backend/tools/reject_counts.py`
(NEW) · `backend/tests/test_grade_map_reject.py` (NEW) · **`backend/app/domain/table/grade_map_postflop.py`
(added by owner decision B1 — the gate-diagnostic refactor)** · `backend/tests/test_domain_purity.py`
(add `grade_map_reject` to the module list). **Does not create `backend/tools/__init__.py`** — T-EXPORT owns it.

**⚠️ Taxonomy correction — `grade_map_postflop.py`'s own module docstring is STALE.** It claims "ONLY the
HU single-raised-pot continuation line," but HEAD ships **19 postflop mappers** including nine `map_mw_*`
multiway and two limped-**flop** shapes. **"Multiway" and "limped pot" are therefore NOT rejection
reasons** — they are supported shapes that reject for a further reason. Fix the docstring while in there.

**Reason taxonomy** (precedence-ordered, first match wins ⇒ mutually exclusive; catch-all ⇒ exhaustive):
`NO_MAPPER_FOR_STREET_SHAPE` (incl. every limped turn/river — those mappers are flop-only) ·
`PREFLOP_SHAPE_UNGATED` · `ALL_IN_IN_LINE` · `OPEN_SIZE_OFF_BAND` · `HERO_ROLE_UNGATED` ·
`STREET_ACTION_SHAPE_UNGATED` (donk/lead, probe, delayed c-bet) · `BET_FRACTION_OFF_GRID` ·
`STACK_TOO_SHALLOW` · `UNCLASSIFIED`.

**Mechanism:** a pure `classify_postflop_rejection(state, hero_seat) -> RejectReason` running as a
**second pass** — precondition is that the caller already got `None`. **Predicate reuse is mandatory:**
import and call the existing helpers (`_hu_srp_preflop`, `_is_canonical_bet`, `RECOGNIZED_BET_FRACS`, …).
Do not re-implement a gate. No schema change, no migration, no persistence.

**Done-condition:**
```
cd backend && python -m tools.reject_counts --session adaadc548d6f499c965821a617c900df
```
→ `postflop decision points: 66` · `mapped: 4` · `unmapped: 62` (flop 24 · turn 23 · river 15) ·
`sum(reason counts) == 62` · **`UNCLASSIFIED == 0`**. Record the observed street × reason matrix in the
completion note — `T-cover` is scoped off it.

**No-gos:** do not widen any mapper · **do not change any PUBLIC mapper signature** — `map_decision_point`
and every `map_*` keep returning `Spot | None`; the typed diagnostic is INTERNAL to the gate predicates ·
no `spot_signature()` contact · `app/domain/` purity must hold (and must now be *enforced* — add the new
module to `test_domain_purity.py`'s fixed list, or the check silently skips it).

**Trap:** coding the taxonomy from the prose instead of from HEAD, emitting `MULTIWAY` and `LIMPED_POT` as
reasons. That buckets ~all 62 into two useless bins and `T-cover` gets scoped off a fiction. **First commit
must be a read of the live mapper list, pasted into the PR description.**

**Purity enforcement gap (review finding, mechanical):** `test_domain_purity.py:12` uses a **fixed module
list**. It will not import `grade_map_reject.py` unless the name is added explicitly — so the "stays pure"
claim is unenforced by default. **Add the module to that list in this ticket.**

> ### ✅ B1 RESOLVED — OWNER DECISION 2026-07-26: refactor the gates to report a reason
>
> **Chosen shape:** change the shared gate predicates in `grade_map_postflop.py` to return a **typed
> internal diagnostic** consumed by *both* the live mappers and the new classifier, while every
> **public mapper signature stays `Spot | None`** so no caller changes. One source of truth ⇒ the reason
> counts cannot drift from what the grader actually does, which is the failure mode that would make this
> measurement worthless six months out.
>
> **Consequences to the ticket, applied below:**
> - **`backend/app/domain/table/grade_map_postflop.py` is now an OWNED file.** The earlier "edits no
>   existing file" no-go is **withdrawn** — it was incompatible with a no-drift classifier and also
>   contradicted this ticket's own instruction to fix the stale module docstring.
> - Byte-identity for existing callers is no longer structural; it must now be **test-enforced**. Add an
>   explicit assertion that `map_decision_point` returns exactly what it did before the refactor across
>   the 181-hand corpus (the B2 parity assertion below already supplies the vehicle).
> - Six test files reference these mappers (`test_grade_map_flop_facing.py`, `test_grade_map_turn_river.py`,
>   `test_mw_funnel_belt.py`, `test_mw_hero_seat_widening.py`, `test_apply_multiway_opp.py`,
>   `test_sim_postflop_sizing.py`). None should need edits — **if one does, the public contract moved and
>   the refactor is wrong.** That is this ticket's primary tripwire.
> - This becomes the second-largest ticket in the wave. It still parallelises safely: no other Wave A
>   ticket touches `grade_map_postflop.py` or anything under `app/domain/table/`.
>
> ### ⛔ B2 remains — a specification addition, not a fork (do this as part of the ticket)
>
> **B1 — "edits no existing file" is incompatible with no-drift classification.** The reusable gates
> discard the information the taxonomy needs: `_hu_srp_preflop` (`grade_map_postflop.py:191-221`) returns
> the *same* `None` for multiway/fold-out, wrong role, all-in players, malformed action history, wrong
> raise/call shape, **and** off-band opens; `map_flop_cbet` carries further inline gates (`:52`). A
> second-pass classifier can *call* those predicates, but the moment one returns `None` it must
> re-implement their internals to separate `ALL_IN_IN_LINE` from `OPEN_SIZE_OFF_BAND` from
> `HERO_ROLE_UNGATED`. So the design either duplicates gate logic (which drifts) or must refactor the
> gates to return an internal typed diagnostic consumed by both the mappers and the classifier — which
> means **owning `grade_map_postflop.py`**, contradicting this ticket's "edits no existing file."
> `UNCLASSIFIED == 0` on one 62-row sample does not prevent future drift.
> *(Note this also contradicts the ticket's own instruction to fix the stale docstring, which is an edit
> to an existing file.)*
>
> **B2 — historical decision-time states are not recoverable as specified.** The classifier's precondition
> needs the `HandState` **immediately before** each of the 66 hero decisions. `SimDecision` stores no state
> snapshot (`db/models.py:88-116`) and `SimHand.state_json` is the **terminal** state (`:72-84`). The
> terminal blob does contain the full `action_history`, so the intermediate states are *reconstructible* —
> but only by deterministic replay, which this ticket never specifies.
> **Required addition:** replay `action_history` up to each hero ordinal, then assert (i) replay yields
> exactly **66** postflop hero decision points, and (ii) `map_decision_point` reproduces **every** persisted
> `coverage` value (4 mapped / 62 unmapped) *before* any reason is counted. Without (ii) the reason matrix
> could be measuring a mis-replayed game.
>
> **Do not start T-REJECT until B1 is decided by the owner.** B2 is a specification addition, not a fork.

---

## T-TRACE — un-blind the D8 anti-degeneracy pack

**Goal:** pass `context=` and `facing_raise=` in `build_trace` so W3's position multiplier and busted-draw
river bluff stop resolving to identity in every trace spot.

**Owned files:** `backend/tests/node_trace.py` · `backend/tests/test_node_trace.py`. **No overlap with any
other ticket.**

**Mechanism:** add `in_position`, `bet_prev_street`, `facing_raise` to the `Spot` NamedTuple; pass
`context=PostflopContext(...)` with `busted_draw=busted_draw_kind(spot.hole, list(spot.board))` —
**derive it, never hardcode**. Add exactly one new spot, `flop_oop_toppair_dry`, byte-identical to
`flop_ip_toppair_dry` except `in_position=False`, so position is the only varying term.

**Done-condition:** `cd backend && python -m pytest tests/test_node_trace.py -q` green, asserting for
**nit** (exact — `action_probabilities` is a normalized merit vector, zero variance):
`flop_ip_toppair_dry` bet `== 0.4783` (±0.001) · `flop_oop_toppair_dry` bet `== 0.3548` (±0.001) — both
read `0.4231` today · `river_busted_draw` bet `> 0.30` (today `0.0156`).

**No-gos:** **do not touch `personas_postflop.py`** (owned by two other tickets; this is test-only) · no
spots beyond the one OOP twin · do not change `_TraceRng`, the seed default, or the existing three tests.

**Traps:** (1) **Passing `PostflopContext()` to mean "not applicable."** Its default is
`in_position=False`, which is not neutral — it applies the OOP damp. "Not applicable" is `context=None`.
(2) **Concluding the plumbing failed on the facing spots.** `_position_agg_mult` multiplies the BET
candidate on the unopened/matched-option path only, so four spots are correctly inert. A worker who
"fixes" that by editing `_position_agg_mult` has smuggled a behaviour change into a test-only ticket and
collided with T-ANCHOR. **Write the inertness into the test as a comment, do not repair it.**

---

## T-ANCHOR — restore the complement anchor W3-b broke

**Goal:** make `P(bet)` in the unopened bluff cell exactly equal the composed `bluff_mass` again for
nit/tag/lag, restoring `bluff_freq` as an exact-frequency lever.

**Owned files:** `backend/app/domain/personas_postflop.py` (**lines 825–871 only**) ·
`backend/tests/test_personas_postflop.py` (new test only)

**Mechanism:** in the `else:` branch at `:825`, hoist
`pos_mult = _position_agg_mult(pf, context) if agg_action is ActionType.BET else 1.0` (the BET gate is
load-bearing — the matched-with-option check-RAISE is outside W3-b's boundary). Inside `if bluff_cell:`,
multiply **then** complement: `bluff_mass *= pos_mult` → `agg_merit = bluff_mass` →
`check_merit = max(1.0 - bluff_mass, 0.0)` (keep the clamp). Replace the post-hoc block at `:868-869` so
the multiplier applies **only on the non-bluff path**. **Exactly once on each path.**

**Done-condition** — the observed IP:OOP bet-rate ratio must equal the authored position-multiplier ratio
to 1e-9 for all six personas (nit and tag `5/3`, lag `1.15/0.85`, station/fish/maniac exactly `1.0`).
**Fixture is pinned** — air hand `('7h','5d')` on dry board `['Kc','9s','3h']`, `Street.FLOP`,
`is_aggressor=True`, `current_bet_to=0.0`, pot `4.0`, stack `100.0`, 1 opponent, legal actions
`[CHECK, BET(min 1.0, max 60.0)]`, capture-rng seeded `1`, `PostflopContext(bet_prev_street=False,
busted_draw=0)` varying only `in_position`:

```
cd backend && python3 - <<'EOF'
import random
from app.domain.personas import load_persona_packs
from app.domain.personas_postflop import sample_postflop_decision
from app.domain.spot import ActionType, LegalAction, Street
from app.domain.table.postflop_context import PostflopContext
class C(random.Random):
    def __init__(s,*a,**k): super().__init__(*a,**k); s.c=None
    def choices(s,p,weights=None,**k):
        if s.c is None: s.c=(list(p),list(weights))
        return [p[0]]
P=load_persona_packs()
L=[LegalAction(action=ActionType.CHECK),LegalAction(action=ActionType.BET,min_bb=1.0,max_bb=60.0)]
def pb(n,ip):
    r=C(1); sample_postflop_decision(P[n],('7h','5d'),['Kc','9s','3h'],L,4.0,100.0,1,r,
        current_bet_to=0.0,is_aggressor=True,street=Street.FLOP,
        context=PostflopContext(in_position=ip,bet_prev_street=False,busted_draw=0))
    p,w=r.c; s=sum(w)
    return [x/s for a,x in zip(p,w) if a is ActionType.BET][0]
for n,exp in [('nit',5/3),('tag',5/3),('lag',1.15/0.85),
              ('passive_fish',1.0),('calling_station',1.0),('maniac',1.0)]:
    r=pb(n,True)/pb(n,False)
    print(f'{n:16s} IP/OOP={r:.10f} expect={exp:.10f} {"OK" if abs(r-exp)<1e-9 else "FAIL"}')
EOF
```

Expected: **all six `OK`**. Current broken readings from this exact fixture: nit `1.6394`, tag `1.5157`,
lag `1.2260`. Post-fix absolutes IP→OOP: nit `0.0444`→`0.0267`, tag `0.2373`→`0.1424`, lag
`0.3779`→`0.2793`; station `0.0259`, fish `0.1036`, maniac `0.6213` must be **bit-identical** at both.
Add as a parametrized test beside `test_bluff_ordering_across_personas_at_fixed_size`.

**No-gos:** do not touch the facing-chips branch (`:744-824`), especially `raise_merit` at `:804` · do not
touch `_position_agg_mult`, `_POSITION_AGG_DELTA`, or any `position_sensitivity` value · do not touch the
three pre-multipliers on `bluff_mass` at `:724-742`. **Legitimate:** seeded live-loop fixtures may move
(report the cumulative coverage delta vs the immutable baseline).

**Trap — the tripwire is inverted.** `test_bluff_ordering_across_personas_at_fixed_size` routes through
`_air_bet_weight` (`:880`), which passes **no context**, so the multiplier is identity and the test
**cannot** move. **Any movement proves double application** — the worker added the pre-complement multiply
and left `:868-869` live, giving `mult²·bluff_mass` against a `1 − mult·bluff_mass` complement. Never
re-anchor it. Secondary trap: hoisting `bluff_mass *= pos_mult` up to `:738` where the other multipliers
live silently applies position to the facing-node bluff-raise, which the theory contract's P1 row excludes.

---

## T-STICKY — resolve the dead `stickiness` lever

**Goal:** delete `stickiness` from the two packs where it is provably unread, and make the schema forbid
it wherever both split levers are authored, so the field can no longer lie about controlling behaviour.

**Owned files:** `backend/app/domain/content/models.py` (`:147-158`) ·
`content/personas/{passive_fish,calling_station}.json` · `backend/tests/test_personas_postflop.py`
(mechanical fixes only, ~`:204-210`, ~`:1136-1155`). **Does not touch `personas_postflop.py`.**

**Mechanism:** `stickiness: float | None = Field(default=None, gt=0.0)`; add a validator with **both**
directions — (i) if either split lever is absent, `stickiness` **must** be present (else the fallback reads
`None` and crashes at sample time); (ii) if both are authored, `stickiness` **must** be absent. Delete the
key from the two dead packs only.

**Done-condition:** a SHA256 over a **216-cell** captured merit grid (6 personas × 3 hands × 4 faced
fractions × 3 streets — *corrected from 648 during review; `6·3·4·3 = 216`*) is **identical before and
after**, and `verify.sh` is green with **zero band edits**. Byte-identity *is* the observed number — the
claim being proved is "removing this field changes no decision."

**Capture the pre-change digest FIRST, on `main`, and paste it into the ticket before editing anything** —
a digest computed only after the change proves nothing. Grid: personas sorted; hands
`('7h','5d')/['Kc','9s','3h']`, `('Kh','9d')/['Ks','7c','2h']`, `('Ah','Ad')/['Ks','7c','2h']`; faced
fractions `0.30/0.55/0.90/1.50` of a `20.0` pot; streets FLOP/TURN/RIVER (board sliced to 3/4/5 from
`bd + ['4d','3c']`); legal `[FOLD, CALL(min=bet), RAISE(min=2·bet, max=300)]`; capture-rng seeded `1`;
hash `repr((population, weights))` of the first `choices` call per cell.

Second leg: `PersonaPostflop.model_validate({...})` on a payload carrying `stickiness` **and** both split
levers must **raise** a validation error naming `stickiness`.

**No-gos:** **do not touch `nit.json`, `tag.json`, `lag.json`, `maniac.json`** — maniac reads `stickiness`
in **both** branches (it authors neither split lever) · do not touch `_price_exponent`,
`_PRICE_STICKINESS_DAMP`, `_PRICE_SENSITIVITY`, or the `looseness` resolution at `:702` · **do not author
`size_elasticity` for the remaining four packs** — that is band-moving and deferred.

**Trap: completing the job.** A worker sees four packs still carrying a vestigial lever and converts them
for consistency, computing `size_elasticity = stickiness ** -0.15` and rounding. Bit-exactness needs
17-significant-figure literals; rounding perturbs `_price_exponent` in the fourth decimal, flips knife-edge
`rng.choices` draws, and lands as an unexplained fixture re-record inside a ticket advertised as
byte-identical. **The deletion is safe only exactly where the field is unread.**

---

## T-REVIEWER — give the theory reviewer the realism question

**Goal:** close the structural blind spot in the one project reviewer — it asks "does this obey our
committed theory?", which cannot catch "our theory is wrong," the exact failure the 181-hand review found.

**Owned files:** `.claude/agents/persona-realism-theory-reviewer.md`

**Mechanism:** add a second review question — *"would a real player of this archetype actually do this?
If the committed theory says otherwise, say so and name the file/lever."* — plus pointers to
`backend/tests/node_trace.py` (the zero-variance probe, which all six analysts reinvented with ad-hoc
Monte Carlo) and `backend/tools/export_session.py` (once T-EXPORT lands).

**Done-condition:** the file names both tools and both questions; a fresh reader can state what this
reviewer owns that the generic `refuter` does not.

**No-gos:** do not create additional agent files · do not edit the user-global `refuter` (it is shared
across all projects and must stay domain-neutral).

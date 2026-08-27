# Review R1 (Claude, adversarial) — Spec: Two-mode Simulate (Training / Challenge)

**VERDICT: REJECT** — the plan's direction is sound, but four separate claims in it are wrong
against the current code, including the one arithmetic claim the whole 200-hand gate rests on.
Every fix is a contained edit to the spec text; none requires re-thinking the approach.

Reviewed 2026-08-26 against working tree `134cba4` (no code changes staged; `git status` shows
documentation-only modifications). Spec under review:
`docs/ai-dlc/specs/two-mode-simulate.md`. Contract map cross-checked:
`docs/ai-dlc/contracts/persona-label-toggle.md`.

## Deterministic baseline, run before reading anything

| Command | Result |
|---|---|
| `./scripts/verify.sh` | **RED** — `2 failed, 2189 passed` in 480s |
| `cd backend && ruff check .` | clean (`All checks passed!`) |
| `cd frontend && npm run typecheck` | clean (no output from `tsc --noEmit`) |

The two failures are pre-existing and unrelated to this feature
(`tests/test_detection_probe.py::TestStubEndToEnd::test_build_and_stub_judge` and
`::test_probe_deck_is_deterministic`, both raising
`tools.detection_corpus.CorpusBuildError: session 1ff221bc…: no complete hands`). See issue 10.

## Citation audit

Every `file:line` in both documents resolves to what it claims. I checked, and confirmed as
accurate: `SimTable.tsx:58,64,291-294,313,322-324` · `SimLedger.tsx:17,18,24,59,60` ·
`SimVillainRange.tsx:55,79` · `SimRangeChart.tsx:214` · `SimulateView.tsx:47-50,94-104,163,315,384,401` ·
`sim_session.py:155-158,188-194,284-288,745,1120-1144,1279-1348,1398-1421` ·
`models.py:45-56,67,130-136` · `schemas/simulate.py:21` · `types.ts:220-227`.

I also independently re-ran the "how many archetype display sites" sweep and reached the same
answer for on-screen archetype *strings*: four in Simulate. A case-insensitive grep for
`persona|archetype|villain_label|villain_type|maniac|calling.station` across all of
`frontend/src` returns only `SimTable.tsx`, `SimLedger.tsx`, `SimVillainRange.tsx`,
`SimRangeChart.tsx` (plus `PokerTable.tsx:70-71`, which is the Practice/Drill screen and carries
`Spot.villain_type`, not a Simulate seat). No CSS class is keyed on a specific archetype —
`.sim-persona-plate` (`app.css:2877`) and `.sim-vrange-persona` (`:4138`) are generic. I could not
find a fifth string site, and I looked hard: see issues 12 and 14 for the two things that are
adjacent to being one.

Two things I actively tried to break and could **not**:

- **The grader's prose is not a leak.** `content/preflop/exploit.json` does name archetypes in
  its rationale text, but that text only reaches an `EvaluationResult` through
  `HeuristicProvider._enrich_exploit`, which is gated on `spot.villain_type is not None`
  (`backend/app/domain/providers/heuristic.py:44-45`). Simulate's mapped `Spot` never sets
  `villain_type` (`_exploit_note`'s docstring at `sim_session.py:1124-1127`, and the field's only
  definition at `domain/spot.py:155` is commented "set for exploit drills"). So
  `SimDecision.reasoning_text`, the live verdict panel, the replayer and the coach endpoint all
  stay archetype-free. The contract map's §F conclusion is correct.
- **The coach endpoint is not a leak.** `CoachContext`
  (`backend/app/services/coach.py:62-79`) has no persona field, and its `reasoning` input is the
  archetype-free grader prose above.
- **A quizzed seat can never have busted or left.** `_rebuy_seats`
  (`sim_session.py:220-234`) tops every seat back to a fresh stack before every deal, so all nine
  seats are always live. That edge case in the review brief is answered by existing code.

---

## Issues

### 1. The completed-hand formula is wrong in exactly the state the feature needs — BLOCKING

**Claim:** §10's "Completed hands are `SimSession.hand_no - 1` while a hand is live; no new
counter column is added" is true only *while a hand is live*, and the unlock has to fire in the
one state where it is false: between hands.

**Evidence.** `create_session` (`backend/app/services/sim_session.py:817-841`) sets `hand_no=1`
and immediately deals hand 1. `deal_next_hand` (`:1398-1412`) increments `hand_no` only after an
early return:

```python
hand = _current_hand(db, session)
if hand is not None and hand.status == "in_progress":
    # Idempotent no-op: the current hand is still live — return it.
    ...
session.button_seat = (session.button_seat + 1) % 9
session.hand_no += 1
```

So there are two distinct resting states, not one:

- hand N **live** → completed = N − 1, and `hand_no - 1` = N − 1. Correct.
- hand N **complete, next not yet dealt** → completed = N, but `hand_no - 1` = N − 1. **Off by
  one.** This state is fully reachable and fully restorable: `apply_hero_action` sets
  `hand.status = "complete"` (`:926`), `_deal_and_advance` does the same when everyone folds to
  the hero's big blind (`:267`), and `restore_session` (`:844-858`) serves that completed hand
  back on reload.

**What breaks.** The between-hands state is precisely where §10 wants "the deal pauses once to
ask". With `hand_no - 1`, the predicate `completed >= 200` first becomes true only *after*
`deal_next_hand` has already dealt hand 201 and `advance_to_hero` has run the bots to the hero's
decision. The dialog therefore opens over a live hand with cards already out — it does not pause
a deal, it interrupts one. And §9's counter, which the current code renders as
`Hand {hand.hand_no}` (`frontend/src/components/SimulateView.tsx:749-756`), reads **"Hand 201 /
200"** at the moment the dialog appears.

**Fix, and its cost.** State the formula as `hand_no - (0 if hand_over else 1)` — both inputs are
already on the wire (`SimulateHandView.hand_no` and `.hand_over`,
`backend/app/schemas/simulate.py:147,158`), so this costs one clause in the spec and no schema
change. The contract map's alternative — counting `SimHand` rows with `status="complete"`
(`sim_session.py:1461` already does exactly this query for history) — is also correct and also
needs no column. The spec's headline conclusion ("no new hand-count column is needed") survives;
its stated derivation does not.

**Severity: blocking.** The central gate of the feature fires one hand late and the counter
displays a number greater than its own maximum.

### 2. Skipping the dialog has no persisted state, so the unlock un-does itself on reload — BLOCKING

**Claim:** §13 ("The dialog is skippable. Skipping opens the labels exactly as answering does;
only the stored result differs") and §14 ("Submitting scores the guesses … and stores the result
on the session") together leave the unlock predicate undefined, and make a skip non-durable.

**Evidence.** The only new persisted field is `blind_check_json` (§Backend,
`backend/app/db/models.py` bullet). §11 opens the dialog "when the gate fires and the check has
not yet been answered". A skip, by §13, is not an answer — it only "differs in the stored
result", and the spec never says a skip writes anything. So after a skip: `blind_check_json`
stays NULL, the gate condition is still true, and the next page load re-opens the dialog. If the
unlock predicate is "check answered", the labels also re-hide, directly contradicting §19 ("the
toggle's position survives a page reload within the session") and §3 ("a page reload never
re-asks").

**What breaks.** The reload-mid-dialog case, which is a first-class edge case for a local app the
owner leaves open across sessions. Either the player is asked forever, or the labels flicker back
to hidden.

**Fix.** Name the unlock predicate explicitly and make skip a persisted outcome — e.g.
`blind_check_json` is written on *both* submit and skip, with a discriminator
(`{"answered": false}` vs `{"answered": true, "guesses": …, "score": …}`), and the unlock
predicate is `blind_check_json is not None`. Gain: one durable state machine with no client-only
state. Cost: the skip button becomes a network call that can fail, so the spec must say what
happens if it does.

**Severity: blocking.** The spec's own reload guarantee is unsatisfiable as written.

### 3. §8's replacement for the ledger's Player column duplicates a column that already exists — BLOCKING

**Claim:** §8's "The ledger's Player column shows the seat's **position**" produces two identical
columns and destroys the ledger's only stable per-opponent identity.

**Evidence.** `frontend/src/components/simulate/SimLedger.tsx:59-60`:

```tsx
<td className="sim-led-seat">{seat.position}</td>
<td className="sim-led-who">{personaLabel(seat.persona_type)}</td>
```

The **Seat** column is *already* `seat.position`. Following §8 literally renders
`UTG | UTG | −12.5` on every row. Neither the spec nor the contract map records that the Seat
column exists — the contract map cites only `:60`.

**The deeper problem.** Position is not an identity. `deal_next_hand` advances the button every
hand (`sim_session.py:1407`, `session.button_seat = (session.button_seat + 1) % 9`), so a given
`seat_index`'s position cycles through all nine every nine hands. The ledger's whole value is the
*running* `net_bb` per opponent across the session (its own header comment at `SimLedger.tsx:4-8`
calls it "a ruled P&L book … running net_bb … a busted-and-rebought seat reads its true lifetime
P&L"). With the archetype hidden and only a rotating position shown, a Challenge player cannot
attribute a running total to any particular opponent — which is the exact faculty the 200-hand
read is supposed to train. Rows stay keyed and ordered by `seat_index` (`:28-31`), so the data is
stable; only the visible label is not.

**Fix.** Show a stable seat identifier in the Player column when labels are hidden — the pod's
own screen location is already stable, so something like `Seat 3` (from `seat.seat_index`) or
"the seat two to your left" restores attribution without naming an archetype. Gain: the ledger
keeps working and the blind check becomes answerable. Cost: one new label helper and a decision
on how seats are numbered relative to the hero.

**Severity: blocking.** As written the instruction is wrong against current code, and it removes
a working feature.

### 4. `frontend/src/api/client.ts` must change and is not in the file list — BLOCKING (trivially fixed)

**Claim:** the spec's Definition of Done says "nothing outside the files named in this spec has
changed", but the change is impossible without editing a file it does not name.

**Evidence.** `frontend/src/api/client.ts:106-107`:

```ts
export async function postSimulateSession(): Promise<SessionView> {
  return json(await fetch(`${BASE}/simulate/session`, { method: "POST" }));
}
```

It takes no argument, so it cannot carry the mode; and there is no wrapper for the new
blind-check route. Every other Simulate call goes through this module (`getSession:112`,
`postHeroAction:118`, `postNextHand:133`, `leaveSession:138`, `getVillainRange:200`), so
bypassing it inside a component would be convention drift.

**Fix.** Add `frontend/src/api/client.ts` to §"Files and interfaces to touch". One line.

**Severity: blocking** only because the DoD is written as an exhaustive-file gate; the remedy is
a one-line spec edit.

### 5. A lost session silently downgrades a Challenge player to Training — SHOULD-FIX

**Evidence.** `SimulateView.tsx:462-471`:

```tsx
try { adopt(await op(id)); }
catch (e) {
  if (isSessionNotFound(e)) { clearStored(); await startSession(); }
  else { throw e; }
}
```

and the same silent-create at `:443-449` ("No live session (first-visit race) — create one
instead"). `startSession` (`:394-396`) calls `postSimulateSession()` with no arguments. Combined
with the spec's own decision that `create_session()` defaults to `"training"` "so the existing
call shape keeps working" (§Backend), any 404 recovery drops a Challenge player into a fresh
Training table with every archetype plate visible — mid-run, with no notice, and their 200-hand
progress reset to zero.

**Fix.** Either carry the last known mode into the recovery `startSession(mode)`, or surface the
mode-choice screen instead of auto-creating. Gain: the mode-fixity promise in §2 holds under the
one failure path that already exists. Cost: `startSession` gains a parameter and the recovery
path gains a branch.

**Severity: should-fix.** Not blocking because the path is a failure path, but it is the *only*
way the two-mode invariant silently breaks, and the spec is silent on it.

### 6. With Watch off, the 200th hand deals the 201st before any dialog can interpose — SHOULD-FIX

**Evidence.** `SimulateView.tsx:492-508`. On a hero fold with Watch OFF, the client posts the
action and immediately calls `postNextHand(id)` inside the same `run()` closure, never adopting
the fold response:

```tsx
const folded = await postHeroAction(id, { action });
...
return postNextHand(id);
```

There is no render between the hand completing and the next hand being dealt. If completed hand
200 ends in a hero fold and Watch is off, the unlock's "the deal pauses once" cannot happen —
even with issue 1 fixed. Watch defaults ON (`readWatch()`, `:86-92`), so this needs the player to
have opted out, but it is a real one-click setting exposed in the topbar (`SimWatchToggle`,
`:787`).

**Fix.** State that the gate check happens on the fold-skip path too, before `postNextHand`.

### 7. The new route path contradicts every existing Simulate route — SHOULD-FIX

**Evidence.** The spec specifies `POST /api/v1/simulate/sessions/{session_id}/blind-check`
(plural `sessions`). Every existing route uses the singular:
`backend/app/api/v1/simulate.py:72` `@router.post("/session")`, `:76` `/session/{session_id}`,
and the action/hand/leave routes documented at `:3-8`. The spec's own golden-path table says "A
new endpoint → the existing routes in `backend/app/api/v1/simulate.py`".

**Fix.** `POST /simulate/session/{session_id}/blind-check`.

### 8. `mode` as a NOT NULL column contradicts the repo's add-column pattern and may fail on SQLite — SHOULD-FIX

**Evidence.** The spec asks for `mode` (`str`, not null). The repo's recorded convention is the
opposite — `backend/app/db/models.py:40-42`:

```python
# NOTE: DB column is intentionally nullable (migration 0010 add-column
# pattern) — readers must treat NULL as 'practice' (stats.py does).
source: str = Field(default="practice")
```

and the most recent migration, `backend/alembic/versions/0014_sim_decision_reasoning_parts.py`,
adds its column as "Additive nullable — existing rows read back with NULL, no backfill". On
SQLite, `op.add_column` with `nullable=False` and no `server_default` fails against a non-empty
table; making it work needs either an explicit `server_default="training"` or a
`batch_alter_table` rebuild (the 0012/0013/0014 downgrade precedent).

**Fix.** State the exact form. Gain: the migration runs first time on an existing local database.
Cost: either a `server_default` that then lives in the schema forever, or the repo's
nullable-plus-reader-default idiom. I would take the nullable idiom, because it is the pattern
`models.py:40-42` already documents and it makes issue 5's backfill question moot.

### 9. Double-submission and already-answered behaviour are unspecified — SHOULD-FIX

**Evidence.** §14 says only what a first submission does. The spec's test list (Verify by §4)
covers "rejects a submission before 200 completed hands" and nothing else. Every neighbouring
Simulate mutation is explicitly idempotent and says so in a comment:
`deal_next_hand` (`sim_session.py:1402-1405`, "Idempotent no-op") and `leave_session`
(`:1415-1421`, "idempotent: already gone/ended").

**Fix.** State: second submission returns the stored result unchanged (idempotent), or 409. Also
name the status code for the too-early rejection — the module's existing convention is
`SessionNotFound` → 404 and `ValueError` → 400 (`sim_session.py:163-166`).

### 10. The spec's verification gate is already red on `main` — SHOULD-FIX

**Evidence.** "Verify by" §1 requires `./scripts/verify.sh` to end in `BACKEND VERIFY OK`, and the
Definition of Done requires it to "exit clean". It does not, today, with no code changes in the
tree: `2 failed, 2189 passed`, both in `backend/tests/test_detection_probe.py`
(`test_build_and_stub_judge`, `test_probe_deck_is_deterministic`), both raising
`CorpusBuildError: session 1ff221bc7cbf48e297b9f2f6439a348c: no complete hands`.

**Fix.** Name the two as a known-red baseline in the spec (with a date), or fix them before this
slice starts. Gain: the builder can tell their own breakage from inherited breakage. Cost: if
named as baseline, someone must own un-naming them later. Without this the builder either stalls
or, worse, learns to read a red gate as normal.

### 11. The deterministic three-seat pick is under-specified in three ways — SHOULD-FIX

- **Distinctness is never required.** §12 says "three seats … drawn from the non-hero seats only"
  but never "three *distinct* seats". A hash-modulo-8 implementation repeated three times
  collides roughly 58% of the time.
- **The dialog has no way to name a seat to the player.** With the plate hidden and position
  rotating every hand (`sim_session.py:1407`), "name the archetype of this seat" has no referent
  in the player's own vocabulary. This is the same root cause as issue 3, and it needs the same
  fix — a stable seat identifier — before the dialog is answerable.
- **The prior is not uniform, and the spec's six options imply it is.** `LINEUP`
  (`backend/app/domain/table/play.py:44-54`) is a **fixed multiset**, shuffled across seats but
  never re-drawn: two `PASSIVE_FISH`, two `TAG`, one each of `CALLING_STATION`, `NIT`, `LAG`,
  `MANIAC`. A player who knows the roster composition — and after one Training session they do —
  scores meaningfully above 1-in-6 with no read at all. The spec should either say the score is
  deliberately uncalibrated (fine, it is a bit of colour), or state the baseline it is measured
  against. I verified the six option names in §11 map exactly onto `VillainType`
  (`backend/app/domain/archetypes.py:8-14`) and onto the seven files in `content/personas/`
  (six packs plus a `ladders/` directory), so no quizzed seat can carry an archetype absent from
  the option list. That part is sound.

### 12. §7's "the panel needs no change" holds before the unlock and not after — SHOULD-FIX

**Evidence.** §7 reasons that hiding the villain-range button makes the panel unreachable. That
is true pre-unlock. Post-unlock, §17 gives the player a Labels toggle that "governs all four
sites at will", and §15 ties the button's return to the same flag. Setting Labels back to Hidden
while a panel is open removes the button but leaves the panel mounted — `openRangeSeat` is
independent React state in `SimulateView` (its reset effect is at `:741-742`, keyed on
`openRangeSeat` itself, not on any label flag). The header string is suppressed (site 3), but the
weight grid stays on screen, and the grid identifies the archetype more precisely than the label
does.

**Fix.** One clause: hiding labels post-unlock also closes any open range panel
(`setOpenRangeSeat(null)`). Low impact — by then the player has already seen the answers — but it
is a one-line omission that turns §7's stated reasoning false.

### 13. The contract map is stale in two places the spec cites it as authority for — SHOULD-FIX

The spec's header names `../contracts/persona-label-toggle.md` as its contract map, so its errors
propagate:

- `persona-label-toggle.md:10` says "the **100-hand** unlock needs no database migration". The
  count is now 200 and there *is* a migration —
  `docs/ai-dlc/roadmap/bot-realism-flywheel.md:45-57` (rev 9, 2026-08-26) moves the count from
  100 to 200 and rules the mode onto the session row. The contract map is dated 2026-08-25, one
  day before.
- `persona-label-toggle.md:116-118` (§F) says `content/preflop/exploit.json` names an archetype
  in "three `lead` rationale lines". I counted **7 of its 12 entries** carrying an archetype word
  inside their rationale (leads at `content/preflop/exploit.json:53,67,81,95,109,123,166`). The
  §F conclusion ("a single-field decision, not a sweep") is still correct, because the whole note
  is suppressed as one unit — but the number is wrong and someone will cite it.

**Fix.** Add a stale-claims banner to the contract map, or correct the two lines. The repo's own
convention for this is well established (see the roadmap's superseded-text blocks).

### 14. `persona_type` stays on the wire in Challenge mode — OPTIONAL

Not a defect, but the spec should say it out loud. §Constraints commits to view-layer hiding, and
`_view()` copies `persona_type` into every `SeatView` unconditionally (`sim_session.py:745`,
schema at `backend/app/schemas/simulate.py:21`, FE type at `frontend/src/api/types.ts:223`). So a
Challenge player with the browser network tab open sees all eight archetypes on hand 1. For a
local single-user trainer this is the right trade — the alternative breaks two consumers, exactly
as the contract map's §C documents — but the spec currently reads as though nothing reaches the
screen, and "the screen" includes DevTools. One sentence: the blind is honour-based, enforced in
the view layer by design.

### 15. Two already-oversized files grow further — OPTIONAL

`frontend/src/components/SimulateView.tsx` is **941 lines** and `frontend/src/styles/app.css` is
**5,611 lines**; the spec adds mode-choice gating, toggle state and dialog state to the first and
"styles for the three new components" to the second. The global engineering standard is to flag
rather than silently grow an oversized file, so this is the flag. I am **not** recommending a
split as part of this slice — that would be exactly the defensive over-engineering the review
brief warns against. Recording it so the next person does not think nobody noticed.

### 16. Two smaller gaps, both optional

- **Mode value validation.** §Backend types `mode` as `str`. Nothing states it is a `Literal["training", "challenge"]`
  or that an unknown value is rejected, so a typo in a request body persists silently and the
  frontend falls through to whichever branch its `=== "challenge"` test picks.
- **Two tabs share one stored session id.** `STORAGE_KEY = "simulate.session_id"`
  (`SimulateView.tsx:47`) is a single global key. Opening Simulate in a second tab with no live
  session creates a new session and overwrites the key, so the first tab's Challenge session
  becomes unrestorable on reload. This is pre-existing behaviour, unchanged by this spec — but
  §3's promise ("Restoring an existing session restores its stored mode. A page reload never
  re-asks") is newly load-bearing, so it is worth one line acknowledging the limit rather than
  discovering it later.

---

## What I could not verify

- **Whether the design canvas ("Simulate — Training vs Challenge", five screens) agrees with the
  spec.** I have no access to it. Every claim above is checked against code and against
  `docs/ai-dlc/roadmap/bot-realism-flywheel.md` only.
- **End-to-end behaviour past 200 hands.** I did not run the app or play a session; the review
  brief scoped me to read-only verification commands. Issues 1 and 6 are derived from reading the
  control flow, not from observing the dialog fail to appear.
- **Whether the two pre-existing `test_detection_probe.py` failures are known to the owner.** They
  reproduce on an unmodified tree; I did not check git history for when they started.

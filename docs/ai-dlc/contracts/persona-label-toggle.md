# Contract map — persona-label toggle (Simulate)

Scanned 2026-08-25 by a read-only `contract-mapper` agent for the bot-realism-flywheel
roadmap slice "persona-label toggle". Every claim below carries a `file:line`. This is a
current-state map, not a plan.

## Bottom line

Hiding opponent archetype labels can be **pure frontend display logic**. The persona string
already reaches the browser on every session response, and only four render sites print it.
A per-session completed-hand count already exists (`SimSession.hand_no`), so the 100-hand
unlock needs **no database migration**. The closest existing pattern to imitate is the
grading toggle (`SimGradingToggle` / `coachMode`), whose own doc comment states the exact
invariant this feature needs: the underlying thing is still computed and recorded, the
toggle only gates what renders.

Two traps. `REVEAL_ENABLED` is **not** this feature's seam — it gates showdown *hole-card*
reveal and is unrelated. And hiding by nulling the persona field at the API would break two
consumers (details in §C), so hiding belongs in the view layer, not the wire.

## A. Every place an opponent's archetype reaches the screen

Four sites print the archetype string:

1. **Seat plate badge, text and `title=` tooltip** — `frontend/src/components/simulate/SimTable.tsx:291-294`, via a local `personaLabel()` helper at `:58-64`.
2. **Ledger "Player" column** — `frontend/src/components/simulate/SimLedger.tsx:60`, helper at `:17-24`.
3. **Villain-range panel header** — `frontend/src/components/simulate/SimVillainRange.tsx:55,79`, showing `VillainRangeView.persona_label`, which the backend fills from the persona pack's display name at `backend/app/services/sim_session.py:1344`.
4. **Preflop-chart exploit note** — `frontend/src/components/simulate/SimRangeChart.tsx:214` prints `"vs {villain_label}"`, sourced from `ExploitNoteView.villain_label` at `backend/app/services/sim_session.py:1141`, which is the raw persona key (`"nit"`), not the display name.

One near-miss, recorded so nobody re-derives it. The villain-range **button's** render gate is
`seat.persona_type && !folded && !hand.hand_over` (`SimTable.tsx:313`). It prints no name. Its
`aria-label` uses table position, not persona (`:322-324`). Because every non-hero seat in
Simulate is a bot, the button's presence tells the player nothing they do not already know —
so it is not itself a label leak. It matters only as a breakage risk (§C).

Swept and confirmed to carry no archetype reference: `HandReplay.tsx`, `HandReplayTable.tsx`,
`SimShowdown.tsx`, `SimRecap.tsx`, `SimStreetReport.tsx`, `SimDashboard.tsx`,
`SimEventLog.tsx`, `SimActionBar.tsx`, `SimPostflopChart.tsx`. A case-insensitive sweep for
`persona|villain_label|archetype` across every `.tsx` under `frontend/src/components`
returned exactly the four files above. The history and replay view models
(`HandReplayView`, `ReplayStepView` in `backend/app/schemas/simulate.py`) carry no persona
field at all.

## B. `REVEAL_ENABLED` is a different feature — do not reuse it

`backend/app/services/sim_session.py:155-158` defines `REVEAL_ENABLED = True` and
`_REVEAL_SCOPES = ("last-in", "all")`. It gates `reveal()` (`:1351-1395`) and `reveal_hand()`
(`:1658-1718`), which control whether a villain's **hole cards** become visible after a hand
— the mechanism specified in `docs/ai-dlc/specs/history-villain-reveal.md` and
`reveal-hands-r1.md`. Its comment "global (not per-session) by design — v1 has no
per-session hiding" is about card reveal.

`SessionView` and `SeatView`, which carry `persona_type`, are untouched by this flag. The
persona-label toggle needs its own seam. The roadmap's note that `REVEAL_ENABLED` is "a seam
for exactly this feature" is **wrong** and should not be carried into the spec.

## C. Where `persona_type` travels, and what breaks if it is omitted

Origin is `backend/app/db/models.py:67` (`SimSeat.persona_type: str | None`). It is copied
into `SeatView.persona_type` (`backend/app/schemas/simulate.py:21`) by `_view()`
(`sim_session.py:745`), and therefore rides on every `SessionView` returned by all four
Simulate endpoints — `create_session`, `restore_session`, `apply_hero_action`,
`deal_next_hand` (`backend/app/api/v1/simulate.py`). The hand-maintained frontend type is
`frontend/src/api/types.ts:220-227`.

If the field were nulled on the wire rather than hidden in the view layer:

- `SimTable.tsx:313` — the villain-range button disappears along with the badge, silently
  removing a working feature.
- `SimLedger.tsx:17-18,60` — `personaLabel(null)` returns `"You"`, so every villain row
  would read "You". This is a real defect, not a cosmetic one.
- `villain_range()` (`sim_session.py:1279-1348`) and `_exploit_note()` (`:1120-1144`) read
  `persona_type` server-side on independent paths, so nulling `SeatView.persona_type` would
  not hide sites 3 and 4 in §A anyway.

Never null the database column: `_seat_personas()` (`sim_session.py:188-194`) reads it to
build the persona-pack lookup that drives bot decision-making in `advance_to_hero`.

## D. Session identity and hand counting — no migration needed

A session is one `SimSession` row (`backend/app/db/models.py:45-56`): `id`, `owner_id`,
`button_seat`, `hand_no`, `status`, `created_at`. `create_session()`
(`sim_session.py:817-841`) starts it at `hand_no=1` with a fresh nine-seat lineup.
`leave_session()` (`:1415-1421`) sets `status="ended"`, after which `_get_session()`
(`:284-288`) returns nothing and `restore_session` returns 404.

There is no dedicated completed-hand column, and none is needed. `hand_no` is the current
hand's number, incremented in `deal_next_hand()` (`:1398-1412`) only once the current hand is
no longer in progress, so completed hands equal `hand_no - 1` while a hand is live. The count
of `SimHand` rows with `status="complete"` for that `session_id` is the equivalent query.

Because leaving a table always produces a new `SimSession` whose `hand_no` restarts at 1,
"per session, not lifetime" falls out of existing session identity for free.

## E. Existing session-scoped UI state

`frontend/src/components/SimulateView.tsx` holds all of it. `STORAGE_KEY =
"simulate.session_id"` (`:47`) is the only key tied to session identity: written on `adopt()`
(`:315-322`), read on mount to call `restore_session` (`:401-410`), cleared on 404 or leave
(`:384-391`). `SPEED_KEY`, `WATCH_KEY`, and `COACH_KEY` (`:48-50`, readers at `:73-104`) are
**lifetime** preferences on global keys — they show the toggle shape, not a per-session reset.

Best pattern to imitate: `SimGradingToggle`
(`frontend/src/components/simulate/SimGradingToggle.tsx`) with its `coachMode` state
(`SimulateView.tsx:94-104,163-168`). It is a two-way pill with a real `<button>`,
`aria-pressed`, and no colour-only cue, and its doc comment already asserts the invariant
this feature needs. Gain: no new interaction or accessibility design. Cost: its storage
idiom is global-lifetime, so it must be namespaced by session id or seeded from hand count
rather than copied verbatim.

Nothing in the codebase currently gates a control's DOM *presence* on a hand-count
threshold. That logic is new, though it is one conditional and matches how `SimTable.tsx`
already omits elements conditionally.

## F. Grader and review prose surface — one endpoint, fully gated

**Corrected 2026-08-26** after a blind Codex review checked the counts below and found them
wrong. The conclusion is unchanged and the correction makes the case stronger, not weaker.

`content/preflop/exploit.json` names an archetype in **seven** `"lead"` rationale lines, not
three, with further names in adjacent fields (`:53,55,67,69,81,95,109,123,166`). It is reached
exclusively through `ExploitNoteView` on the preflop chart (`preflop_chart()`,
`sim_session.py:1147-1176`, rendered at `SimRangeChart.tsx:214`). The postflop chart
(`postflop_chart()`, `:1199-1247`) never calls `_exploit_note`.

Because the **whole note** is gated as one unit, the number of lines inside it does not change
the work. It is recorded correctly here so that nobody later reads "three lines" and concludes
the name could simply be stripped from each: the bodies carry the read even without the label
("a LAG opens too many hands" still says LAG).

A second pack does name archetypes — `content/cards/preflop.json:106`, a concept card whose
body describes four of them. It is **not** a Simulate render site: Simulate never loads concept
cards, and a grep of `sim_session.py` for that pack returns nothing. It is listed only so the
next reader does not rediscover it and think it was missed.

The persisted review columns `SimDecision.verdict_tier_text`, `.reasoning_text`, and
`.reasoning_parts_json` (`backend/app/db/models.py:130-136`) carry no archetype reference, and
neither does the hand replayer.

`content/` is under the initiative's committed-pack-value freeze, so the answer must be a
display gate, never a pack edit.

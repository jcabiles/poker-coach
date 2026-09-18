# Merge review — Two-mode Simulate, 2026-09-18

Fresh dual review before merge, both blind to the build session: a Claude `refuter` (Opus, high effort) over the whole `origin/main...feat/two-mode-simulate` diff, and a Claude `design-reviewer` (Opus) driving the branch in a real browser. Gates re-run the same day on the branch: backend 2239 passed / 2 skipped, ruff clean; frontend typecheck, build, 60 tests. Adjudication of every finding: `../ledger/two-mode-simulate.md`, round 3.

---

## Part 1 — refuter (code)

# Adversarial review — `feat/two-mode-simulate` (tip 2bd72cf) vs `origin/main` (134cba4)

## Bottom line

**APPROVE-WITH-FIXES.** I found no blocking defect. The server-side deal barrier,
the completed-hand arithmetic, the blind-check endpoint's status contract, and
first-write-wins idempotency under a genuine two-thread race all hold when
attacked directly, and the archetype does not leak through any render site in
Challenge mode before the unlock. Two items are worth an owner decision before
merge, both about scope rather than correctness: the ledger's column header was
renamed in Training (a mode the spec says must be unchanged), and the
archetype-name transform now exists in three copies.

## Deterministic checks I ran

| Check | Result |
|---|---|
| `pytest tests/test_two_mode_simulate*.py tests/test_migration_0015_*.py tests/test_domain_purity.py` | 51 passed |
| `pytest tests/test_sim_session.py tests/test_coach.py tests/test_db.py tests/test_simulate_api.py` (regression) | 63 passed |
| `ruff check .` (backend) | All checks passed |
| `git diff --stat origin/main...HEAD` | nothing under `backend/app/domain/`, nothing under `content/` |
| New CSS custom properties resolve against `tokens.css` + `app.css` | 0 undefined |
| New CSS raw colour literals (`#rgb`, `rgba()`) | 0 |

## Probes I wrote (all in the scratchpad, none in the repo)

1. **Seat picker, 20 000 session ids.** `_blind_check_seats()` returned three
   distinct seats in every case, never seat 0 (the hero), always within 1–8, and
   the per-seat frequency spread was 7382–7611 — the documented low-index bias is
   real but under 3%. A fixed id reproduced its triple exactly.
2. **Real play through a lowered gate.** I set `BLIND_CHECK_HAND_GATE = 3` and
   played actual hands rather than renumbering rows, which is what the shipped
   tests do. The deal advanced normally at completed = 1 and 2, refused to
   advance the moment hand 3 settled (`hand_no` unchanged, the settled hand
   returned with its blind-check payload), and resumed to hand 4 after a skip was
   stored. This is the exact boundary the spec was rewritten at rev 2 to fix, and
   it is correct in live play, not just under the test fixture.
3. **Two-thread race on the endpoint.** Two threads with separate database
   sessions submitted contradictory answers through a barrier. Exactly one row was
   written and **both callers received the identical stored result** — the
   conditional `UPDATE … WHERE blind_check_json IS NOT DISTINCT FROM <observed>`
   does what its comment claims.
4. **Full HTTP contract through `TestClient`.** No body → 200 Training; `{}` →
   200 Training; `{"mode":"challenge"}` → 200 Challenge; `{"mode":"cheat"}` → 422.
   Blind check: 409 before the gate, 404 unknown session, 422 for an archetype
   outside the six, 422 for a skip carrying answers, 422 for two answers, 400 for
   seats the digest did not pick, 400 for a repeated seat, 200 on the skip, deal
   resumes to hand 201, duplicate submission returns the first stored result.
5. **Leak hunt.** I grepped every render of `persona_type`, `personaLabel`,
   `villain_label` and `archetype` across `frontend/src`. Four sites exist and all
   four are behind `labelsVisible`: the seat plate *and its `title=`*
   (`SimTable.tsx:302`), the range button (`SimTable.tsx:326`), the ledger's
   Player column (`SimLedger.tsx:96`), the exploit note
   (`SimRangeChart.tsx:221`), plus the villain-range panel itself, gated at its
   mount in `SimulateView.tsx:1379`. The range button's `aria-label` names
   `seat.position`, not the archetype. The hand-200 dialog receives every seat row
   but renders only seat number and net — no persona. The grader's own reasoning
   is villain-agnostic (`sim_session.py:1247` maps the spot with
   `villain_type=None`), and the coach service carries no persona at all, so the
   recap is not a fifth leak.
6. **Panel close on re-hide.** `changeLabelsShown` clears `openRangeSeat`, which
   runs the fetch effect's cleanup at `SimulateView.tsx:1113` (`cancelled = true`)
   and the data-clearing effect at `:1121`. The claim that the in-flight response
   is discarded is true.

## Findings

### 1. should-fix — the ledger header changes in Training
`frontend/src/components/simulate/SimLedger.tsx:68-71` renames the first column
from **Seat** to **Pos**. Spec §5 says Training is "identical to the app as it
stands" and that the mode stamp is "the only addition"; T7's acceptance mentions
only the Player column. The rename is defensible — the column shows
`seat.position` and would otherwise collide with the "Seat 3" identities the
hidden state prints — but it is a visible change to shipped Training behaviour
that no ticket asked for, and the spec itself refers to that column as "the
adjacent Seat column" (§9), so the spec is now stale in the same change.
*Gain of reverting: Training is byte-for-byte unchanged and the spec's own
wording stays true. Cost: two columns in Challenge both read as "seat"-ish, which
is the ambiguity the rename was fixing.*

### 2. should-fix — one transform, three implementations
`SimTable.tsx:58`, `SimLedger.tsx:22` and `blindCheck.ts:66` each convert a
SCREAMING_SNAKE archetype value to Title Case. T7 owns two of those three files,
so consolidating was in scope. The build flagged it as a follow-up in
`blindCheck.ts:63-64` and in the roadmap rather than doing it. The risk is
concrete: the three must agree character-for-character or the name a player picks
in the dialog stops matching the name that appears on the plate afterwards.
*Gain of consolidating: one place to change. Cost: a shared module import across
three components, roughly 15 lines moved.*

### 3. low — model and migration disagree on nullability
`backend/app/db/models.py:60` declares `mode: str` (non-optional) while
`backend/alembic/versions/0015_sim_session_mode.py:28` adds the column as
`nullable=True`. Harmless today: `server_default="training"` fills every
pre-existing row, and `_view()` normalises anything unexpected at
`sim_session.py:877`. But the repo has no migration-drift test, and the model's
own comment says readers must treat NULL as training — which the type says cannot
happen. The named golden path, `DrillAttempt.source`, is `str | None`.

### 4. low — the deal barrier has a documented escape hatch
`backend/app/services/sim_session.py:1533` skips the barrier when
`hand.state_json is None`, so such a row would deal one hand past the gate. The
comment states the reason (a null state cannot be returned and raising would
diverge from Training). Unreachable today — every other reader of that column
already assumes it is non-null — and self-limiting to a single extra hand,
because the next call is gated again.

### 5. low — "tab-local" is only true until a reload
Spec §23 calls the Labels toggle tab-local. `SimulateView.tsx:64-84` stores it in
`localStorage`, which is shared across tabs, so a second tab that reloads inherits
the first tab's choice. Live state genuinely differs per tab, so the spec's
operational test ("survives a reload, two tabs may differ") is met in the
ordinary case. `sessionStorage` would be exact.
*Gain of switching: matches the spec's word precisely. Cost: diverges from the
four existing Simulate keys, which all use localStorage — the golden path the
ticket named.*

### 6. optional — files outside the spec's named list
Two new frontend modules (`blindCheck.ts`, `handCount.ts`, plus their tests) and
seven documents (`plans/`, `reviews/` ×3, `specs/`, `tickets/`, `contracts/`,
`log.md`, `profile.md`) are outside **Files and interfaces to touch** and **Also
in scope**, which the definition of done says nothing may fall outside. Both
modules are pure extractions from components the spec does name, and extracting
them is the only way this repo can test logic at all — there is no
testing-library or jsdom dependency, and every existing frontend test is a pure
module test. This is the right call; it just was not authorised in writing.

### 7. optional — the roadmap slice is not ticked
`docs/ai-dlc/roadmap/bot-realism-flywheel.md` still reads `- [ ]` for this slice,
against a definition of done that requires it ticked. The branch states why (the
slice stays open pending an owner play session, the same rule that keeps slice 3
open), so this is a deliberate deviation rather than an oversight.

### 8. optional — the modal pre-empts the last hand's narration
With Watch on, hand 200's bot playback is still animating when the dialog mounts;
`showModal()` makes the page inert, so the player cannot watch the hand finish.

### 9. optional — small Training layout change
The hand counter is now wrapped in `.sim-hand-progress` (`app.css:2666`,
`inline-flex` column) in both modes. Training renders that wrapper with a single
child, which can shift the counter's baseline slightly in an otherwise unchanged
top bar.

### 10. optional — toggle keys accumulate
`simulate.labels.<sessionId>` adds one localStorage entry per Challenge session
and nothing prunes them.

### 11. optional, pre-existing — one gated site is already dead
Ledger entry B30 records that the preflop exploit note never fires in Simulate
at all, because `_exploit_note` keys its lookup on a non-null `spot.facing` while
all twelve authored entries are indexed under `facing_position: None`. So one of
the five display sites T7 gates is currently a no-op. Not this slice's defect and
correctly recorded rather than quietly fixed.

## Invariants — all verified

Domain core gained nothing and `test_domain_purity.py` passes · `persona_type` is
read but never written by `submit_blind_check` and is present on every seat row in
the Challenge wire response I captured · grading untouched · `content/` untouched ·
no raw hex or `rgba()` added to `app.css`, and every `var(--…)` resolves · the
schema change ships migration 0015 on head 0014, tested against a populated
database holding an active session · `spot_signature()` untouched ·
`frontend/src/api/types.ts` matches the backend schemas field-for-field
(`SimMode`, `BlindCheckView`, `BlindCheckGuess`, `BlindCheckAnswer`,
`BlindCheckSubmitRequest`, `SessionView.mode`, `SessionView.blind_check`).

---

## Part 2 — design-reviewer (browser)

# Design + accessibility review — Two-mode Simulate (Training / Challenge)

**Verdict: APPROVE-WITH-FIXES.** Every behaviour the spec's §1–§23 promises is present and
correct in the running app, in both themes: the sit-down screen with no pre-selection, the
archetype blackout at hand 1 (nothing leaks in text, attributes or the accessibility tree),
the server-barred deal at 200 completed hands, a real `<dialog>` modal with a working focus
trap and a non-destructive Escape, the one-time score, and a Labels toggle that is absent from
the DOM before the unlock and closes an open villain-range panel when re-hidden. No console
errors were produced by the feature. Contrast passes WCAG 2.2 AA everywhere measured, in both
themes, with the tightest reading at 4.62:1 (Challenge stamp, day). What is left is one
typography defect on the feature's own hero screen and a set of smaller, mostly pre-existing
issues.

Nothing found is blocking.

## How this was tested

Live browser (Chromium via Playwright) against the feature branch at http://localhost:7778,
backend at http://localhost:8018. The 200-hand gate was reached by driving a Challenge session
over the HTTP API (fold every hand, deal the next) with a throwaway script, then loading that
session id into `localStorage["simulate.session_id"]` and reloading. Screens captured at
1280×900 and 390×844, in both the Night (dark) and Day (light) rooms. Contrast was computed
from `getComputedStyle` with the real composited background, not eyeballed.

Screens live in `screens/`.

## Confirmed working (evidence)

- **Mode choice (§1–§4).** Two equal-size cards, no pre-selection, distinguished by four
  non-colour cues (eyebrow, corner numeral 1 vs 200, single vs double rule, terms line).
  Tab order is logical; the focus ring is 3px `--primary` at 2px offset. All four
  session-creation paths route here: first boot, Leave Table, the `run()` race guard, and the
  404 recovery (tested with a bogus session id — the view fell back to the choice screen and
  cleared the stored id).
- **Training (§5–§6).** App unchanged plus a quiet outlined `TRAINING` stamp; counter reads
  `Hand 1` with no target and no bar.
- **Challenge before unlock (§7–§10).** A full DOM sweep for `nit|TAG|LAG|maniac|calling
  station|passive fish` across text nodes and every non-class attribute returned zero hits.
  No seat plates, no `title=` tooltips, no villain-range buttons. The ledger's Player column
  reads `Seat 1`…`Seat 8` (hero row correctly still reads `You`). Gold `CHALLENGE` stamp,
  `HAND 1 / 200` with an outlined progress track beneath.
- **The gate (§11–§17).** The API refused to advance past 200 completed hands; the browser
  showed the dialog on load. `:modal` is true, so focus is trapped and the background is inert.
  Radio groups are operable by arrow key; the live "2 seats still to name." region updates;
  the primary button is disabled until all three are named and sits *before* Skip in the
  document. Skip asks twice once any seat is named. Escape dismisses without spending the
  check and hands focus to the "Open the check" button on the paused strip.
- **After unlock (§18–§23).** Score shown once ("You named 1 of 3.") with WRONG/RIGHT badges
  carrying words, not just colour. Counter drops `/ 200` and the bar. `Labels: Shown` appears
  in the control cluster with `aria-pressed="true"`, matching `SimGradingToggle` exactly
  (real `<button>`, gilt pressed state, state also in the word). Hiding labels closed the
  open BTN range panel, removed the range buttons and plates, and returned the ledger to
  `Seat N`.
- **Tokens and motion.** No raw hex, `rgb()` or `hsl()` in the new CSS or the new TSX; the
  only raw lengths are hairline/letter-spacing values the file already uses elsewhere. The
  card entrance animation is inside a `prefers-reduced-motion: no-preference` guard. The two
  `outline: none` rules are scoped to `[tabindex="-1"]` programmatic focus targets.
- **Console.** Zero errors and zero warnings across every screen. The only errors seen in the
  whole session were the browser's own logs for the deliberately bogus session id (two 404s,
  doubled by React's dev-mode double effect), which the app handled correctly.

## Issues

1. **should-fix — Mode-choice cards, both themes, both widths: the card prose renders in
   Arial, not the design's body face.** `.smc-lede`, `.smc-terms` and `.smc-cta` sit inside a
   `<button>`, which does not inherit `font-family`, and none of them sets one — computed
   `font-family` is `Arial`, while `.smc-intro` 40px above it at the identical 15px computes
   `"Source Sans 3"`. Two typefaces do the same job on one screen. Violates the "committed
   type system" rule on the feature's own hero screen. Fix: add `font-family: var(--font-body)`
   to `.smc-room` (`frontend/src/styles/app.css:5763`), which fixes all three at once.
   Gain: one consistent voice. Cost: none — the fallback is currently accidental.

2. **should-fix — the same Arial leak reaches the dialog's two buttons.** `.sbc-submit` and
   `.sbc-skip` compute `Arial` because `.btn` (`app.css:593`) sets no `font-family`. This one
   is **pre-existing and app-wide**, not introduced here, so fixing it at `.btn` touches every
   button in the app and belongs in its own change. Recorded so it is not mistaken for new.

3. **should-fix — every Simulate screen scrolls horizontally at 390px.**
   `document.scrollWidth` is 713 against a 390 viewport. The offenders are all app shell —
   `.masthead-right`, `.ev-ledger-widget`, and the section nav — and the poker table itself is
   unreadable at that width (seat plates overlap the community cards). **Pre-existing and out
   of this ticket's named files**; the new components are innocent (the choice screen collapses
   to one column at ≤720px, the dialog is 354px wide with 44×44 controls). Flagged because it
   is the first thing a reviewer will see on a phone.

4. **optional — the page `<h1>` is smaller than the `<h2>` beneath it.** On the choice screen,
   `h1.sim-heading` "Simulate" computes 20px and `h2.smc-title` "Choose a table" computes 22px.
   The real focal point is correct (the 33px card names), so this reads as an inherited quirk
   rather than a mistake, but the ladder is inverted. Pre-existing pattern.

5. **optional — the blind-check dialog's primary action is below the fold at 1280×900.**
   `scrollHeight` 1126 against `clientHeight` 866, so "Score my three" and the Skip control
   are 260px past the visible edge on open. The natural flow (answer three seats, scrolling)
   ends there anyway and the submit is disabled until then, so this costs little — but a
   sticky footer would remove the one moment a player can wonder where the button went.
   Gain: the action is always in view. Cost: ~90px of the card's reading height on short
   viewports.

6. **optional — the 404 recovery is silent.** A stored session that no longer exists drops the
   player on the choice screen with no line explaining that their table is gone. Correct per
   §4, and the code has an error panel for the creation-failure path; only the recovery case is
   wordless. Gain from a one-line notice: the player learns why they are being re-asked. Cost:
   one more string and one more state on a screen that is currently very clean.

7. **optional — `SimGradingToggle` fails WCAG 2.5.3 "Label in Name"; the new toggle does not.**
   Visible "Grading: Real play" is not contained in its accessible name "Grading feedback:
   real-play mode", so a voice-control user cannot say what they read. The new
   `SimLabelsToggle` correctly nests "Labels: Shown" inside "Opponent labels: shown". Noted
   because the spec names the grading toggle as the golden path to imitate — imitate its
   structure, not this detail.

## Measurements

Dark (Night) — `.smc-title` 16.89:1 · `.smc-intro` 8.79 · `.smc-eyebrow` 8.36 ·
`.sim-mode-stamp-challenge` 8.48 · `.sbc-opt-gloss` 7.86 · `.sim-net-down` 7.33.

Light (Day) — `.smc-intro` 5.49 · `.smc-eyebrow` 5.98 · `.sbc-lineup-note` 5.30 ·
`.sbc-opt-gloss` 5.30 · chosen plate (cream on gilt) 4.94 · `.sim-mode-stamp-challenge` 4.62
(tightest text reading; AA for 11px bold needs 4.5). Non-text: option-plate border 3.93,
progress track 5.49, card borders 3.61 / 3.96 — all clear of the 3:1 floor.

Targets — dialog close 32×32 at desktop and 44×44 at ≤720px; option plates 218×70 (desktop) /
156×70 (mobile); submit and skip 44px tall on mobile; the Labels pill 109×36, matching the
Watch and Grading pills beside it.

Focus indicators — 3px solid `--primary` at 2px offset everywhere, widened to 4px offset on a
chosen (gilt-filled) option plate so the ring does not merge with the fill.

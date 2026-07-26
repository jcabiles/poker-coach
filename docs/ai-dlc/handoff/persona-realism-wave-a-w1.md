# Handoff — persona-realism Wave A, wave 1 fan-in

**Written 2026-07-26, immediately before a context compaction.** This file is the resume point.
Read it first; it is self-contained. Plan docs: `docs/ai-dlc/{specs,tickets}/persona-realism-wave-a.md`.

---

## 1. Where the run is

| | |
|---|---|
| Branch | `feat/persona-realism-wave-a-w1` (5 commits ahead of `origin/main`) |
| Base | `origin/main` @ `8169c1b` — wave 0 (**PR #127**) is **MERGED** |
| Tree | clean, everything committed |
| Wave 0 | ✅ done + merged (T-REVIEWER + `backend/tools/__init__.py`) |
| Wave 1 | ⏳ built + committed + refuted; **fix rounds not yet dispatched** |
| Wave 2 | ⛔ not started — T-ANCHOR |
| Wave 3 | ⛔ not started — T-STICKY |

**Verified green on the quiesced tree before commit:** `./scripts/verify.sh` → `1089 passed, 1 skipped`,
`BACKEND VERIFY OK` · `ruff check .` clean · `cd frontend && npm run typecheck && npm run build` clean.

```
3262d56 T-EXPORT   de4d9bd T-TRACE   46071e2 T-ARR   6b59717 T-STACK   7e30eb1 T-REJECT
```

Delivery model: **stacked branches, 4 PRs, merged in order**, no mid-run stops.
`main → PR1 w0 (MERGED #127) → PR2 w1 → PR3 w2 → PR4 w3`.

---

## 2. ⚠️ Two operational hazards proven live this session

**(a) An agent moved the branch under me.** After I switched to `w1` and spawned reviewers, HEAD was
back on `main` and 5 commits landed there. Recovered via `git branch -f feat/... HEAD` → `git switch` →
`git branch -f main origin/main`. **Every worker and reviewer brief already says "run NO git commands" /
"read-only git only" — one ignored it.** Before *any* commit, run `git rev-parse --abbrev-ref HEAD` and
confirm. Never trust the branch to still be where you left it after a fan-out.

**(b) `git branch -f main origin/main` prints `error: unable to write upstream branch configuration`
and SUCCEEDS anyway.** The sandbox denies the config write only. Verify with
`[ "$(git rev-parse main)" = "$(git rev-parse origin/main)" ]`, not the exit code.

Other environment facts that cost time: `git push origin <branch>` needs **both** args explicit ·
`gh api` and `gh pr view --json files` fail with a TLS error while `gh pr list/create/view --json state`
work · `gh pr create` immediately after a push **races** GitHub's branch registration — retry once.

---

## 3. Owner decisions (binding, made 2026-07-26)

### Round 1 — orchestration
1. **Both reviewers on all 8 tickets** (`refuter` + `persona-realism-theory-reviewer`), T-REVIEWER first as wave 0.
2. **T-STACK runs parallel with a fingerprint tripwire** — my retraction of the forced `T-STACK → T-ANCHOR` chain was accepted. **The tripwire came back CLEAN** (digests `e23f8ff5…` / `f9b707c4…` identical before/after, green both sides). That dependency is retired, proven not assumed.
3. **Four PRs, stacked**, reviewed at the end, no mid-run merges.
4. **No Fable** — opus for the six substantive tickets, sonnet for T-REVIEWER/T-EXPORT.
5. **Stop-the-line:** retry twice, then continue — HALT only for (i) needing to widen a band/tolerance, (ii) fixtures moving where asserted they cannot, (iii) a pinned constant not reproducing, (iv) needing a file no ticket owns.
6. **Codex Sol** as third reviewer on **T-REJECT** and **T-ANCHOR** only.
7. **Research artifacts stay gitignored** — workers read them off disk (why the wave uses one shared working tree, no worktrees).

### Round 2 — arising from the fan-in
8. **T-STACK: fix the display AND restore side pots.** Move the reset to **deal time**, and make the target a **narrow spread (~95–105bb)** instead of a fixed 100.0. This deliberately changes the ticket's acceptance criterion from "exactly 100.0" to a band.
9. **T-EXPORT: fix the tool AND regenerate the analysis.** Re-run the corrected tool over the 181-hand session, regenerate the per-persona packets under `docs/ai-dlc/research/persona-realism-artifacts/hand-analysis-181/data/`, and add a correction note to `SYNTHESIS.md` saying which figures moved and why. **This is explicit authorization to edit those two research paths.**
10. **T-ARR: keep `[0.30, 0.36]`, document the bias.** Do **not** revert to `[0.33, 0.43]` and do **not** change the lineup.

---

## 4. Fan-in batch 1 — five `refuter` verdicts

**1 pass, 4 NEEDS-WORK. Two HIGH findings neither the workers nor I caught.**

Strong positive evidence worth not re-deriving: the T-REJECT refuter ran a **1.29M-call differential**
(HEAD vs refactor, across 950k random + 290k persona-distribution + 48k test-path mapper calls) →
**0 mismatches**, so the gate refactor is provably behaviour-identical. The T-ARR refuter independently
replayed 1200 hands' `action_history` and confirmed the first-decision guard is correct **at every
position**, not just UTG (7.1% of preflop decisions are re-entries that would otherwise contaminate).

### T-REJECT — NEEDS-WORK (worker `aed70bbc16cce8ec8`, refuter `a79697bfe6d3d4973`)

| Sev | Finding | Fix |
|---|---|---|
| MED | **`UNCLASSIFIED` is ranked DEEPEST**, so one twin's catch-all masks every correctly-named sibling reason. Reachable in legal play (open-limp → iso-raise → limper folds): `_mw_srp_preflop` mis-reads the folded limper as a cold-caller, `_map_mw_flop_cbet:1061`'s pot check fires `UNCLASSIFIED`, masking the correct `PREFLOP_SHAPE_UNGATED` all 8 siblings emit. 12 hits in 40,259 synthetic classifications, all one branch. Makes `reject_counts` exit 1. | In `classify_postflop_rejection`, select over `named = [r for r in reasons if r is not RejectReason.UNCLASSIFIED]`, falling back to `UNCLASSIFIED` only when `named` is empty. Add the seed-200 shape as a regression test. |
| MED | **69% of rejections (43/62; 81% at n=4841) land in `PREFLOP_SHAPE_UNGATED`, a bin that names no shape** — so `T-cover` cannot be scoped from it, which is the ticket's whole purpose. | Additive: have `reject_counts` print a **secondary breakdown** of those rows — preflop raise count, entrant count, whether a blind was an entrant, limp-then-X. That is the artefact `T-cover` needs. |
| MED | **The justification for substituting the combination rule is factually inverted.** Claim was that first-match is degenerate because wrong-role mappers "always emit `HERO_ROLE_UNGATED`". It cannot — `HERO_ROLE_UNGATED` is index 4, *behind* `PREFLOP_SHAPE_UNGATED` at index 1, so under first-match it never wins (measured: HERO_ROLE = 0, 55/62 collapse into PREFLOP_SHAPE). The *conclusion* (a literal scan over the per-mapper fan-out is degenerate) is right; the mechanism cited is wrong. Shipped rule is **deepest-stage-wins**; the two rules disagree on 12 of 62. | Correct the `RejectReason` docstring to the real reason. Refuter judges the substitution **safe** — it reproduces the ticket's *semantic* first-match reading on all 62 rows — but the owner should sign off against the correct argument. |
| LOW | B2 parity checks only the forward direction; a persisted row replay never reproduces is silently dropped while the banner still says OK. | Assert `len(persisted) == replayed_count`. |
| LOW | Output line leads with decision-point counts (`flop 28`) not unmapped counts (`flop 24`) — the exact string the done-condition greps. | Split onto two lines. |
| LOW | `_street_twins` has no PREFLOP guard; a precondition violation silently applies river mappers. | `raise ValueError`. |

**Measured deliverable (the point of the ticket), keep this:** 66 / 4 / 62 · flop 24 · turn 23 · river 15 ·
`UNCLASSIFIED == 0`. Reasons: `PREFLOP_SHAPE_UNGATED` 43 · `NO_MAPPER_FOR_STREET_SHAPE` 7 (100% limped
turn/river) · `HERO_ROLE_UNGATED` 7 (100% hero-as-opener in the no-BB 3-way family) ·
`STREET_ACTION_SHAPE_UNGATED` 4 (100% donk leads) · `ALL_IN_IN_LINE` 1 · **`OPEN_SIZE_OFF_BAND` 0 ·
`BET_FRACTION_OFF_GRID` 0 · `STACK_TOO_SHALLOW` 0**. Top three `T-cover` levers = 66% of all rejections:
multiway limped pots (25) · limp-then-iso-raise chain (9) · limped turn/river (7). **Zero rejections come
from bet sizing or stack depth.**

### T-STACK — NEEDS-WORK (worker `a273131faff06deaf`, refuter `ac59bc7cd769c2e27`)

| Sev | Finding | Fix |
|---|---|---|
| MED | **Display regression.** `_session_view:678-680` returns `row.stack_bb` once `complete`, which the reset pins at 100.0 — so every villain on the felt (`SimTable.tsx:332`) reads exactly 100bb the instant a hand ends, while `hand.hero.stack_bb:716` still comes from the engine. Same response, two bases. No test guards it. The `# (incl. rebuy)` comment now states the opposite of what the code does. | **Owner decision 8**: move the reset to **deal time** (inside `_deal_and_advance` before `stacks_bb=[...]` at `:204`), keeping `_apply_settlement` writing the true post-hand stack. |
| MED | **Side pots are now structurally impossible.** `engine.settle:337-347` builds pot levels from distinct `invested_total_bb`; a second level needs a live seat all-in for less than another, which needs unequal stacks. Measured **0 side pots in 150 hands** (245 seat-hand busts). A training product silently lost a poker situation. | **Owner decision 8**: reset target becomes a **narrow spread ~95–105bb**, not a constant. |
| MED | The new `test_simulate_api.py:201-208` assertion has **two flakes, 9/3000 measured**: (a) 8/3000 — hand 2 dealt already `hand_over` (a walk) still passes the `street == "preflop"` guard, and `_session_view` then reports `starting == 101.0`; (b) 1/3000 — a board-plays chop settles every seat to exactly 0.0, which `test_sim_session.py:119-124` already documents as a real outcome. | Guard on liveness, not street: loop until a non-complete preflop hand 2. Drop the `any(net_bb != 0)` leg — `test_sim_session_buyin_cap.py:154-157` already covers it over 20 hands. |
| LOW | Module docstring `:4` still says "carry-over stacks, auto-rebuy" — both deleted. | Rewrite. |
| LOW | `test_bust_triggers_rebuy_and_2dp_ledger` + its section header name a rebuy mechanism that no longer exists. | Rename. |

**Verified clean, do not re-derive:** ledger arithmetic exact — **0.0 drift over 120 real hands and 20k
synthetic 2dp settlements**, `sum(net_bb)` to 1.1e-13 through 245 busts · `_REBUY_FLOOR_BB` /
`_STACK_CAP_BB` have zero surviving references repo-wide · the rewritten cap test is **not** vacuous ·
the `199.55/100.0 → 100.0/0.45` change is arithmetically right · none of the 7 unnamed importers needed
edits and none silently lost its contract · **the `test_reveal_unavailable…` flake is PRE-EXISTING**
(~1/400 `create_session` returns an already-complete hand), proved by mechanism — `_deal_and_advance`
runs `start_hand` *before* `_apply_settlement`.

### T-ARR — NEEDS-WORK (worker `ac610dd4dff1e5f53`, refuter `a628fcb3145548939`)

**Refuter's headline: the recalibration to `[0.30, 0.36]` is JUSTIFIED — keep it.** It independently
reconstructed the ticket's own recipe (uniform lineup, all seats, n=600 → **5390 seat-decisions**, a 0.1%
match to the ticket's stated 5384) and got **0.3250, not 0.36**. The whole 9-rung ladder behind 36% is
unreproducible; 36% is just its unweighted mean (`320/9 = 35.56`). Every number in the provenance comment
reproduced to 4dp.

| Sev | Finding | Fix |
|---|---|---|
| **HIGH** | **The pooling is NOT roster-balanced**, contradicting its own docstring (`:2675-2677`) and provenance point 3. `lineup = ([persona]*3 + [fillers[i % len(fillers)] for i in range(6)])[:9]` walks 6 indices over 5 fillers, doubling `fillers[0]` = **`calling_station`** (loosest, VPIP 46%) in 5 of 6 runs. Real composition **13/9/8/8/8/8**. Arrival is determined entirely by seats acting ahead, so extra limpers suppress `unopened`. **Balanced pooling reads 0.3504 — inside the abandoned band.** | **Owner decision 10**: fix the *text* in both places, state the 13/9/8/8/8/8 composition and the 62% `calling_station` over-weighting, and record **0.3504** as the balanced counterfactual so Wave B reads the instrument with the bias known. **Do NOT change the lineup** — it is shared with `_persona_stats` and every seeded golden. |
| MED | The **BTN band `[0.05, 0.12]` is fragile** — under pure reseeding (no behaviour change) it spans **0.0417 … 0.1005**, below the floor on 1 of 6 seeds. Denominator is only 408 decisions. T-ANCHOR perturbs this stream next wave; when it trips it will be misread as "the BTN ladder collapsed." | Not a licence to widen. **Record the measured seed dispersion beside the assertion** and surface it as a known pre-existing fragility in a ticket-drafted band. |
| MED | Provenance point 1's "**converges** ~+0.001 per +200 hands" is wrong — n=200/400/600 are **nested samples off one hardcoded seed** (`random.Random(20260710)`), so agreement is autocorrelation, not convergence. At fresh n there is no trend (n=300 → 0.3268, n=500 → 0.3240, n=800 → 0.3244). | Replace with the honest claim: **stable to ±0.003 across n at the pinned seed, ±0.010 across seeds, so ±0.03 is ~3σ of resampling noise.** That is a *better* defence of the band. |
| LOW | "shows up here first and nowhere else" overclaims — SB+BB are 22% of the denominator at ~0 `unopened`, diluting the region it guards. Monotonicity does catch non-monotone collapses. | Soften, or compute over the seven non-blind positions. |
| LOW | `_FACINGS` duplicates `PersonaFacing` as literals; if the literal grows, shares silently stop summing to 1 with no failure. | `_FACINGS = list(get_args(PersonaFacing))`. |
| LOW | Single-quote `'unopened'` at `:2709` adds a `ruff format` hunk. Cosmetic — nothing gates on it. | Optional. |

**Verified clean:** byte-identity golden passes (zero new rng draws) · `_persona_stats` untouched, its
4 positional unpacks intact · `preflop_log` 2-tuple unchanged · no second sim loop · monotonicity not
vacuous · **the ≤12s budget call was CORRECT** — `budget_s = 9.5` sizes N and changing it is a
band-moving edit forbidden by the wave no-gos, so documenting rather than changing it was right.

### T-TRACE — **PASS** (worker `ab3377dd905bb72a6`, refuter `a839cc06528d5dce4`)

All three pins reproduced independently: `0.4783` / `0.3548` / `0.3657`. `personas_postflop.py` and
`postflop_context.py` byte-untouched. **Adjudication: my ticket's "four spots stay inert" was WRONG — it
is two.** `_position_agg_mult` is symmetric (±0.25 × sensitivity), so the two authored-OOP unopened spots
*move* (×0.75) rather than staying inert; "four" came from an IP-boost-only mental model. The worker did
not rationalise a miss.

| Sev | Finding | Fix |
|---|---|---|
| LOW | The busted-draw assertion uses an `in_position=True` spot, so `> 0.30` is **confounded with the position boost** — nit IP 0.3657 but **OOP 0.2570 fails the same assertion**; the W3-c term alone is 0.3156, clearing by only 0.0156. | Add a position-blind witness: also assert `calling_station` (0.3085; `position_sensitivity=None` → multiplier short-circuits to 1.0). |
| LOW | The inertness comment says "unopened / **matched-with-option** path" — self-contradictory, since the `agg_action is ActionType.BET` gate *excludes* matched-with-option (which sets RAISE at `:826`). Load-bearing: implies a check-raise node is position-live when it is not. Inherited verbatim from my ticket's trap wording. | Drop "/ matched-with-option". |
| LOW | The twin was inserted at **index 1**, and `build_trace` seeds each spot `seed + i`, so all six downstream spots' `chosen_action` silently changed. Probabilities unaffected (seed-independent). | **Append the twin as the last `SPOTS` entry.** |
| LOW | `facing_raise` is `False` in all 8 spots — byte-identical to the sampler default, so the damps at `personas_postflop.py:794/814` stay unexercised. A constant field gives the appearance of coverage. | No change (no-gos forbid new spots). **File as a Wave B follow-up.** |

**Forward note for wave 2:** `river_busted_draw` becomes **0.3945** once T-ANCHOR moves the multiply
pre-complement. The assertion is `> 0.30`, so it survives. The two exact pins are non-bluff-cell and
unaffected.

### T-EXPORT — NEEDS-WORK (worker `a8e7c665ffeadbc22`, refuter `a274c31fcc3d6dc3e`)

| Sev | Finding | Fix |
|---|---|---|
| **HIGH** | **WWSF counts hands that never reached a flop, and every such entry is also a forced numerator hit.** Root cause `:76`: `self.board = state.full_board` — the complete runout, populated even on a preflop fold-out — so `len(h.board) >= 3` at `:284` is **always true** and the guard collapses to `(not folded) and vpip`. A preflop steal scores as "saw a flop" AND "won after flop". **37 ghost entries vs 385 genuine.** Error is **aggression-correlated**: HERO 46.7→33.3 (13.4pt), maniac 44.2→32.6 (11.6pt), nit 37.9→28.0 (9.9pt), lag 59.2→50.0 (9.2pt), **calling_station 0.0pt** (never steals). Contradicts the repo's own canonical definition at `test_personas_postflop.py:1912`. | Add `self.revealed = list(state.board)` at `:76`; test `len(self.revealed) >= 3` at `:285`. **VPIP/PFR use independent counters, so the pinned done-condition table is unaffected.** |
| MED | **WTSD counts river fold-outs as showdowns** (`:314-319`) — bet the river, take it uncontested, scored as a showdown. 17/241 false (7.1%). The correct value is computed and thrown away: `settle()` returns `showdown_seats`, bound as `shows` at `:394`, but `stats_for:237` is passed only `nets`. | Pass `shows` in; test `seat in shows[h.hand_no]`. Repo canon: `test_personas_postflop.py:2322`. |
| MED | `settle_hand` returns `({}, [])` for `hand_over == False`, but `load()` still admits the hand — its preflop actions count toward denominators while every net is silently 0, a guaranteed WWSF loss. **10 such hands exist in the DB** (`state_json` is persisted mid-hand at `sim_session.py:845`). The pinned session has zero, which is why the clean run hid it. | Drop them into the existing skip counter and **report it** — silence is the defect, not the exclusion. |
| LOW | Summary column header `3bet` pools 4bet/5bet spots (52 of 626 = 8.3%); the per-persona packet is honest (`3bet+`), the summary is not. | Rename to `3bet+`. |

**Then, per owner decision 9:** regenerate the per-persona packets under
`…/hand-analysis-181/data/` and add a correction note to `SYNTHESIS.md`. **Authorized to edit those
paths.** `SYNTHESIS.md` cites WTSD only narratively (line 29), not as a table, so headline claims survive.

**Verified clean:** the position→seat trap is **correctly avoided** — proved by freezing hand 1's map and
re-running: 160/181 hands differ, and the broken map both trips the reconciliation assert and skews
`calling_station` 45.6→31.5 · the assert is **real, not vestigial** (1629 = 181×9 exact evaluations,
trips at 0.03) · the `settle()` substitution is **sound and an improvement** (0 net diffs, 0
`showdown_seats` diffs, never mutates state, deltas sum to exactly 0.0) · DB byte-identical after a run ·
both scope reductions justified.

---

## 5. What to do next, in order

1. **Dispatch 5 fix rounds** via `SendMessage` to the worker IDs in §4 (they retain full context — respawning loses it). Fold in owner decisions 8/9/10.
2. **Re-verify**: `./scripts/verify.sh`, `ruff check .`, `cd frontend && npm run typecheck && npm run build`.
3. **⛔ OWED, NOT YET RUN — fan-in batch 2:** five `persona-realism-theory-reviewer` passes, one per wave-1 ticket. This was in the approved protocol and was skipped when batch 1's volume forced triage. It asks a different question than `refuter` — *does this obey the grounded poker theory, and is that theory right here?* T-REJECT's taxonomy and T-STACK's new stack **spread** are exactly its territory.
4. **⛔ OWED — Codex Sol on T-REJECT**: `codex exec --sandbox danger-full-access -m gpt-5.6-sol "<brief>"` (the `codex:codex-rescue` companion EPERMs under this repo's nested sandbox). Sol is one input, never sole authority.
5. **Commit fixes, push `git push origin feat/persona-realism-wave-a-w1`, open PR 2** (base `main`, since w0 is merged).
6. **Wave 2 — T-ANCHOR**, alone. It is the wave's **sole fixture re-recorder**; nothing else may run while it does. Branch `feat/persona-realism-wave-a-w2` from w1. Reviewers: `refuter` + theory + **Codex Sol**.
7. **Wave 3 — T-STICKY.** Capture its 216-cell digest on the **w2 tip**, not `main` (already corrected in the ticket).

## 6. Cross-wave carry-forwards

- **T-ANCHOR will move `river_busted_draw` 0.3657 → 0.3945.** Expected; the assertion is `> 0.30`.
- **T-ANCHOR perturbs the shared rng stream**, which shifts T-ARR's occupancy a point or two. `[0.30, 0.36]` was sized for exactly that. **The BTN band `[0.05, 0.12]` was NOT** — see the T-ARR MED. If BTN trips in wave 2, it is band fragility, not a ladder collapse.
- **T-STICKY's grid is all facing spots**; T-ANCHOR touches only the non-facing branch (`:825-871`), so it should not move. A difference is itself a finding.
- **Wave B follow-ups filed here:** add a facing-raise spot to the trace pack · re-derive the real `test_personas_postflop.py` runtime budget (`budget_s = 9.5` is descended from a debunked ≤12s figure) · consider whether the roster-wide arrival figure should exclude the blinds.

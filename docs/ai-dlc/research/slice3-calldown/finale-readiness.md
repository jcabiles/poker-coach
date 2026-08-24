# Finale detection-run readiness packet (read-only survey)

**Bottom line: the finale is close but not yet fireable as documented.** The control
problem that killed the last attempt is SOLVED — a working, judge-tested control exists
in the code today — but the owner-facing execution checklist still describes the OLD
pre-screen procedure (one judge slot, not the four the ratified protocol now requires),
the live API keys still need rotation before anyone should trust the environment they'd
run in, and nobody has priced the run at today's token rates. None of that is a redesign;
it is one doc edit, one key rotation, and one pricing pass — all cheap, all fast, none of
them my call to make on this ticket. Once those three things are done and the owner
supplies fresh keys plus a go-ahead, the run can fire.

This packet is a survey, not a change: no code was edited, no paid API call was made, and
nothing here is committed.

---

## 1. The control question (the crux)

**Verdict: a control that passes the estimand contract's validity rule (§d.2 — "detection
protocol §d, clause 2": the finale batch is only valid if 4 of 4 judges label the planted
control bundle `bot`) exists in shipped code today, and it has already been judge-tested
once, successfully.** The control-redesign ticket's recommended design was built and
proven — the ticket file itself just never got its checkboxes ticked, which is why it
still reads as open work. Evidence, from source, not doc prose:

- **The pilot that failed:** `poker-analytics:docs/methods/detection-pilot-s6.md` §5+§7
  records that the old control (nicknamed **T1**, a "best-effort degenerate" persona-pack
  config) was judged `human` twice — once by a cost-throttled judge, once by the same
  judge at full effort — so the §d.2 pre-screen stopped the 2026-08-14 run before any
  spend on the full panel.
- **PR #184** (`3ca8dad`, merged 2026-08-15, "T-control — the deck's control stops
  fingerprinting the packs") rewired `backend/tools/detection_corpus.py` — the exact tool
  the execution checklist uses to build the finale deck — so the deck's one control
  bundle is now a **rule-breaking scripted bot**: engine-legal but strategically
  illogical play (calls with hopeless hands, bets into boards it cannot beat, identical
  bet sizing regardless of pot). Its identity is pinned by `CONTROL_POLICY_DIGEST`, a
  behavioural fingerprint over a fixed 12-hand replay (`detection_corpus.py:155-163,
  596-632`) — chosen specifically so that improving the persona packs (the whole point of
  the improvement phase) cannot silently invalidate the control, which is what killed the
  old T1 design the moment any pack changed (24 failing tests, per the PR body).
- **This is not a guess about scope** — the estimand contract's own amendment record
  says so directly. `poker-analytics:docs/methods/estimand-contract.md` **§g.5** (an
  amendment is a dated, ratified change to the contract; "§g.5" is its label, the 5th
  such amendment), clause **A**, states: *"the finale deck's single control bundle is a
  rule-breaking scripted bot ... The T1 dial config is demoted to an off-deck sensitivity
  diagnostic."* PR #184's commit message names implementing "amendment (g.5) §A"
  explicitly.
- **It has already been judge-tested, once, off-deck.** `docs/ai-dlc/ledger/phase3-probe.md`
  records a single-judge calibration probe run 2026-08-15 (5 paid calls, ~$0.10, under an
  owner-ratified agent-execution carve-out — §g.5 clause G): the rule-breaking control was
  judged **`bot` at confidence-human 3**, with the judge naming the exact mechanical tells
  ("every hand identical scripted line ... clearly synthetic"). For comparison, the old T1
  control still read `human` (62) on a fresh window in the same probe, and a genuine human
  anchor read `human` (62) — so the new control cleanly separates from both the human
  class and the thing it replaced. This one data point is a single judge, not the 4-of-4
  panel §d.2 requires — see §2 below for why that gap is expected to close, not open, at
  finale time.

**So: does a §d.2-passing control exist today, or is `flywheel-s6-control-redesign.md`
still open work?** The design that ticket recommended (its "candidate 1: rule-breaking
scripted control") is **built and shipped**, and single-judge evidence says it clears the
bar the old control failed. The ticket file's checkboxes are stale, not the code — do not
resume work on that ticket; if anything, it should be closed with a pointer to PR #184 and
§g.5 §A. What has **not** happened yet is the full-panel confirmation §g.5 clause C
requires (next section) — that is a launch-time step, not a design gap.

## 2. Checklist walk-through

Source: `docs/ai-dlc/specs/flywheel-s6-execution-checklist.md`. Governing panel size is
§g.3 (4 judges, 2 vendors) per this repo's `CLAUDE.md` note — the older
`docs/ai-dlc/tickets/flywheel-s6.md` predates that panel change and is not authoritative.

| # | Checklist item | Status | Evidence |
|---|---|---|---|
| §1 | S6 branch merged/checked out | **READY** | Already on `main`; `backend/tools/detection_{corpus,judge,analysis,render,probe}.py` all present (confirmed by directory listing). |
| §1 | `./scripts/verify.sh` green | **READY (evidence, not re-verified live)** | PR #184's own merge record: "Full suite 1987 passed, 3 skipped. ruff clean." Its reviewer ledger (`docs/ai-dlc/ledger/phase3-probe.md`) separately notes "refuter ran `./scripts/verify.sh` green twice." A fresh run was started for this packet but had not finished writing output at packet time — the two independent green runs above are the evidence of record; re-running before the finale costs nothing and is good practice. |
| §1 | The three §A amendments recorded in `estimand-contract.md` §g.2, committed | **READY** | `poker-analytics` git log shows §g.2 (2026-08-07-A) and the newer §g.5 (2026-08-15-A) both present in `docs/methods/estimand-contract.md`, working tree clean, latest commit `5c23173` on that file. |
| §2 | Build the protocol deck | **BLOCKED — OWNER-ONLY (by design)** | The command needs `data/poker_coach.db` (the owner's real Simulate session data) and writes owner hand data to a gitignored output tree; this ticket is read-only and does not touch it. No code defect found — the build path (`detection_corpus.py`) already carries the new control (see §1) and is exercised by the passing test suite above. |
| §2 | `non_protocol` = `false` check | **N/A until deck is built** | Mechanical check on the printed `_SUCCESS` body; nothing to evaluate ahead of a real build. |
| §3 | Credentials (`S6_JUDGE_ANTHROPIC_KEY`, `S6_JUDGE_OPENAI_KEY`) | **BLOCKED — OWNER ACTION REQUIRED** | Keys are an owner-supplied runtime input (see §4 below); the currently-live probe keys are scheduled for revocation, not reuse — see `CLAUDE.local.md`. |
| §3 | Pin the four model IDs (`S6_JUDGES`) | **OWNER-ONLY, cheap to confirm** | Checklist gives 2026-08-07 IDs (`claude-sonnet-5`, `claude-opus-5`) for the Anthropic slots and asks the operator to "confirm at execution time" — routine provider-drift check, not a blocker. |
| §4 | Preflight (4 cheap calls) | **BLOCKED on §3** | Runs automatically inside step 5/6; needs live keys. |
| §5 | Control pre-screen | **FIXED 2026-08-23 (was: checklist stale)** — the Director aligned checklist §5 to §g.5 clause C in the close-packet PR: all four slots, no `--only-slot`, stop on any miss | The checklist text still says *"Judge it with slot 0 only"* and pins `--only-slot 0`. But `estimand-contract.md` §g.5 clause **C** (ratified 2026-08-15, i.e. AFTER the checklist text was last edited by PR #184's 4-line diff, which only touched the `non_protocol` bullet) requires the pre-screen to run on **all four judge slots**, not slot 0 alone, and states those four calls **are** the finale's control checkpoints of record. Firing the checklist as currently written would under-run the ratified protocol. This is a one-paragraph doc fix, not a design question — the correct procedure is already fully specified in the amendment text (`estimand-contract.md` lines ~1658-1662), just not yet copied into the checklist. |
| §5 | Stop rule (control must be labelled `bot`) | **READY, mechanism sound** | Logic unchanged by the slot-count fix; single-judge probe evidence (§1) is favorable but is not the same as the required 4-of-4 result, which can only be produced by actually running the (corrected) pre-screen. |
| §6 | Full run (328 judged calls) | **BLOCKED on §3 + §5 fix** | No code or design gap found; gated only by keys and the pre-screen fix above. |
| §7 | Analysis | **READY (tooling exists, unexercised on real data)** | `backend/tools/detection_analysis.py` present; nothing to run without §6 output. |
| §8 | Write-up | **OWNER-ONLY (per repo convention)** | `docs/ai-dlc/CLAUDE.md`-style convention in this file family: judging and the resulting write-up are owner-run steps; not blocked, just not an agent task. |

**Net effect on readiness:** every genuine blocker left is either an owner action (keys,
go-ahead, running the owner-only steps) or a small documentation fix (the slot-count line
in §5) — there is no outstanding code or protocol-design gap.

## 3. Cost — parameterized, live prices left as variables

Restating the checklist's own §6 arithmetic (checklist step 6, "Cost band") as a table so
the Director can drop in current per-token prices without re-deriving the call/token
counts. **All token counts below are the checklist's own stale estimates, carried forward
unchanged — verify them against the actual deck before spending.**

**Call volume (fixed by protocol, not price-dependent):**

| Item | Count |
|---|---|
| Bundles per judge slot (81 deck+control + 1 own duplicate) | 82 |
| Judge slots | 4 (2 Anthropic: Sonnet + Opus · 2 OpenAI: gpt-5.6-terra + gpt-5.6-sol) |
| Judged calls total (82 × 4) | 328 |
| Preflight calls (1 per slot) | 4 |
| **Grand total paid calls** | **332** |

**Token estimate and cost formula, by vendor** (`cost = Σ (input_tokens × price_in/1e6) + (output_tokens × price_out/1e6)`):

| Vendor | Slots | Calls | Input tokens/call (checklist est.) | Total input tokens | Output tokens/call (checklist est.) | Total output tokens | `price_in` ($/Mtok) | `price_out` ($/Mtok) | Cost formula |
|---|---|---|---|---|---|---|---|---|---|
| Anthropic (Sonnet + Opus) | 2 | 164 | ~5.9k | ~0.97M | **~60 stated + ~1–2k thinking tokens now count as real output** (`max_tokens` raised to 4096 on 2026-08-14 for this reason) | ~0.97M–2.0M range → use **~1.5k/call, ~246k total** as a working midpoint, not a cap | **Sonnet 5: $3 ($2 intro through 2026-08-31) · Opus 5: $5** (Director-filled 2026-08-23 from the current pricing reference) | **Sonnet 5: $15 ($10 intro) · Opus 5: $25 — thinking tokens bill as ordinary output tokens under every display setting** | split per slot (82 calls, ~0.484M in, ~0.123M out each): Sonnet ≈ $3.30 ($2.20 intro) + Opus ≈ $5.50 → **Anthropic ≈ $8–10 at the working midpoint; ≈ $11 at the 2k/call output upper** |
| OpenAI (gpt-5.6-terra + gpt-5.6-sol) | 2 | 164 | ~5.9k | ~0.97M | ~60 (checklist sets no hard cap; **unconfirmed whether these models bill reasoning tokens the same way — check before pricing**) | ~10k (checklist estimate, likely an underestimate for reasoning-capable models) | `[FILL: OpenAI input $/Mtok]` | `[FILL: OpenAI output $/Mtok]` | `0.97M × price_in/1e6 + 0.010M × price_out/1e6` |
| **Total panel** | 4 | 328 | — | **~1.93M** | — | **~256k (Anthropic-dominated estimate; treat as floor, not ceiling)** | — | — | **sum of the two rows above** |

Preflight calls (4, ~10–40 tokens each) are negligible against the above and are omitted
from the formula.

**The checklist's own stale headline estimate:** "single-digit to low-tens of US dollars
for the whole panel, Opus-dominated." That was written before the 2026-08-14 adapter
change that raised Anthropic `max_tokens` to 4096 specifically because current Anthropic
models reason by default and **reasoning ("thinking") tokens count inside that cap and
are billed as real output tokens** — a cost line that did not exist when the original
band was written. The OpenAI side has an open question mark for the same reason (gpt-5.6
series may or may not bill reasoning tokens similarly; checklist text does not say). The
Director should re-derive the headline dollar figure from the table above using current
prices, not quote the checklist's original band as-is.

## 4. Keys

API keys are an **owner-supplied input at run time** — `S6_JUDGE_ANTHROPIC_KEY` and
`S6_JUDGE_OPENAI_KEY` are set via shell `export` immediately before judging and are never
written to a file, committed, or handled by an agent (checklist §3, §4). The keys used for
the 2026-08-15 calibration probe are **scheduled for revocation**, not reuse for the
finale — current status, fingerprints, and the one-command teardown live in
`CLAUDE.local.md` (gitignored, machine-local); this packet does not repeat any of that
material.

## 5. What remains, in order

1. **Build work: DONE 2026-08-23.** The execution checklist's §5 pre-screen now matches
   `estimand-contract.md` §g.5 clause C (all four judge slots, stop on any miss), and
   `flywheel-s6-control-redesign.md` is marked closed-superseded by PR #184 + §g.5 §A —
   both in the slice-3 close-packet PR.
2. **Owner decision:** confirm current model snapshot IDs for the two Anthropic slots
   (`claude-sonnet-5`, `claude-opus-5` as of 2026-08-07 — check for provider rotation).
   The Anthropic side of the §3 cost table is now filled (Director, 2026-08-23:
   Anthropic ≈ $8–10 for the run; Sonnet 5's intro pricing lapses 2026-08-31); the
   OpenAI prices and reasoning-token billing still need confirmation from vendor docs.
3. **Owner action:** revoke the scheduled-for-revocation probe keys (`CLAUDE.local.md`),
   supply fresh finale keys as environment variables, and give the go-ahead to run the
   checklist's remaining owner-only steps (§2 build, §3 credentials, §5 corrected
   pre-screen, §6 full run, §7 analysis, §8 write-up).

No step above requires new code, a new protocol amendment, or another research pass — the
control problem that stalled the last attempt is solved and evidenced from source.

# Finding ledger — phone access + 6-max roadmap

Round 1, 2026-09-18, on roadmap rev 1. One blind reviewer per the roadmap policy: Codex is
not runnable in this sandbox (see `sandbox-tooling` notes), so Claude `refuter` (Opus) ran as
the labeled same-family fallback. Verdict FAIL: 2 blocking, 9 should-fix, 3 optional.
Report: `../reviews/phone-and-6max-roadmap-r1-claude.md`. Every finding was checked against
the code before adjudication. All 14 accepted; rev 2 folds them. Three need the owner (D1–D3
in the roadmap).

| # | Finding | Claimed | Adjudicated | Evidence checked |
|---|---|---|---|---|
| F1 | S1 names only engine/deck; the seat count is also hardcoded in `sim_session.py` (button seed/rotate, seat rows, blind-check pool), `range_estimate.py`, `play.py::assign_lineup` | blocking | **ACCEPTED** — S1 "what" lists the full surface; ease 6→4; pass/fail adds blind-check and range-panel legs | `sim_session.py:358,931,947,1532`; `range_estimate.py:58,237`; `play.py:57-61`. Verified. |
| F2 | `spot_signature()` hashes `table_size`; every Simulate spot hardcodes 9, so 6-max history merges or splits by accident | blocking | **ACCEPTED** — owner decision D1, default key as 6; signature assertion in S1 pass/fail | `srs.py:63`; `grade_map_postflop.py:127,386,455,1708`; `spot.py:100`. Verified. |
| F3 | S1's riskiest assumption is bot feel; the load-bearing claim is the position mapping, which fails for the range estimator and limped pots | should-fix | **ACCEPTED** — mapping is now S1's assumption with a headless verdict-equivalence test; bot feel moves to NEXT research | `deck.py:19-29`; `scenarios.py:73`; `grade_map_preflop.py:209-226`. Verified. |
| F4 | Hands/week rises with 6-max on its own (shorter hands) | should-fix | **ACCEPTED** — north star is occasions/week (distinct days); hands/week secondary, split by table size | Reasoning; no code needed. |
| F5 | No target and "flat is fine" makes the outcome unfalsifiable | should-fix | **ACCEPTED** — decision rule written: no rise four weeks after P1+S1 → drop LATER phone bets, cut P3 | — |
| F6 | Backend bind + CORS + API-base work is unnecessary (relative `/api/v1` proxied by Vite) and puts the unauthenticated API on the wifi | should-fix | **ACCEPTED** — P1 passes `--host` to Vite only; backend stays loopback; negative leg added | `client.ts:32`; `vite.config.ts:14-19`; `main.py:29`; `serve.sh:116,126`. Verified. |
| F7 | P4's hazard is live from P1; the two-tab test is free today | should-fix | **ACCEPTED** — P1(c) runs it; P4 reorders ahead of S1 if it corrupts | `SimulateView.tsx:456,533,617`; `sim_session.py:968-975`; `models.py:79-90`. Verified. |
| F8 | The felt-readability measurement is deferred behind S1 for a weak reason | should-fix | **ACCEPTED** — P1(d) five landscape hands; P2 gate is conditional. Owner's LAN→6-max→prototype order kept | `SimTable.tsx:42,139`. Verified. |
| F9 | P3 sits in NOW while its own text says it cannot be spec'd | should-fix | **ACCEPTED** — P3 moved to NEXT | Ordering rule §A. |
| F10 | `specs/draft-mobile-responsive.md` still says "do not build"; `.claude/CLAUDE.md` banner disagrees with the profile | should-fix | **ACCEPTED** — P1 retires the draft spec; banner is owner decision D3 (outside roadmap write authority) | Draft spec header. Verified. |
| F11 | Eight personas for eight seats; which five sit at 6-max is undecided | should-fix | **ACCEPTED** — owner decision D2, default fixed subset in the S1 spec; pass/fail leg added | `play.py:45,58-61`. Verified. |
| F12 | The owner's 6-max verdict cannot separate bot feel from 9-max grading | optional | **ACCEPTED** — one static label on the 6-max felt, in S1 | — |
| F13 | Context strip says "9-max"; ring geometry was tuned for nine pods | optional | **ACCEPTED** — label in S1; geometry left to P2's design review | `SimTable.tsx:26-40,147`. Verified. |
| F14 | Two LATER bets lead with mechanism; baseline has no query | optional | **ACCEPTED** — bets restated problem-first; SQL recorded | — |

Rejected: none.

## Fidelity pass (Director, against the interview record)
- Added beyond what the owner said: the metric switch from sessions to occasions (sessions are
  week-long rows); the LATER bets on drills and on 6-max-as-default; the "acted elsewhere"
  acceptance detail in P4; all ICE scores; the three D1–D3 decisions the review surfaced.
- Said but not carried: nothing found.

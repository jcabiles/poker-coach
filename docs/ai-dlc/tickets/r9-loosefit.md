# Tickets — R9-LOOSEFIT (spec rev 2)

status: **BUILD HALTED at T1 (owner, 2026-08-03) — returns to spec for rev 3.**
Was: approved (owner, 2026-08-03, Gate 2 — serial single-agent build authorized).
T1 delivered the instrument (committed `7736156` on `feat/persona-realism-r9-loosefit`, verified
byte-neutral) and a measurement verdict: **no operating point satisfies the pre-registered criteria
together with the existing HARD gates.** Ten build findings B-1…B-10 in `ledger/r9-loosefit.md`;
full evidence in `reports/r9-loosefit-t1-measurement.md`. T2–T6 NOT started and must not be until
rev 3 lands. The three blockers, in one line each: R9-DEFENCE-a's ladder floors nit at ≈0.42 · two
stale gates pin tag at exactly 0.6 · the pre-registered T_sep and G-RS-ii thresholds need
n ≥ 53,800 and n ≈ 405,000 respectively.
spec: `specs/r9-loosefit.md` (rev 2) · ledger: `ledger/r9-loosefit.md` · base: origin/main = b63dfaa
Mostly SERIAL — T1/T3/T4 all own `backend/tests/test_personas_postflop.py` (single owner per
wave); only T6 could overlap and isn't worth a wave. Single agent T1→T6 is the intended shape.

## T1 — instrumentation + gate-posture fit (the big one)

Build the shares accessor (`_persona_stats_shares`, sibling of `_persona_stats` — shared loop +
extended memoized cache, existing 6-tuple and all call sites UNTOUCHED), then run the spec's T1
procedure: real pytest gates on the seeded packs (nit 0.08 / tag 0.63 / lag 0.62 as starting
point), explicit n=4,000 both-posture reads, fine-tune per fit-loop rules until ALL
pre-registered criteria hold (every gate green at its own posture; ordering margins ≥ 0.035;
tag/lag WTSD loose-edge margin ≥ 0.02; denominators ≥ 30), Rule-1 conditioning deliverable
(cross-persona coupling measured at gate posture, escalation rule stated), derive T_sep and
G-RS band widths by the spec's pre-registered rules.
- Owned: `backend/tests/test_personas_postflop.py` (accessor only), scratchpad, measurement log.
- Done-condition: measurement table (both postures) + final trio values + thresholds + margins,
  numbers in the ticket-completion report; NO pack edited yet; suite still green
  (accessor is additive — run unpiped, read from file).

## T2 — pack edits

Apply T1's final values to nit/tag/lag `call_looseness`; add nit `_doc` array; append `_doc`
entries for tag/lag; bump each pack's `version`; `continue_ref` byte-untouched (G9 will verify).
- Owned: `content/personas/{nit,tag,lag}.json`.
- Done-condition: `git diff` shows exactly the three files, only the fields named;
  G9 test green; band + ordering pytest green at their own postures (run unpiped).

## T3 — gates

Add G-SEP (named posture n=4,000/False, denominators asserted, T_sep from T1); G-RS-i/ii
(±3σ invariance per persona + nit absolute fall, widths from T1's σ); G-NODE facing
bluff-catcher probe (new crafted node in `node_trace.py`, assertions per spec files-to-touch 5);
amend N-LOGIT G3 docstring/name to "calibration anchor" (assertions unchanged).
- Owned: `backend/tests/test_personas_postflop.py`, `backend/tests/node_trace.py`,
  `backend/tests/test_node_trace.py`.
- Done-condition: all new gates green at fitted values; each gate's red/kill condition
  demonstrated per T5's protocol later; suite green unpiped.

## T4 — golden re-pin

Re-record `_GOLDEN_STATS_N200` (all six rows), "RE-RECORDED for R9-LOOSEFIT" block per the
documented protocol.
- Owned: `backend/tests/test_personas_postflop.py` (golden block only).
- Done-condition: golden test green; attribution proven by revert (T5 re-verifies).

## T5 — sensitivity + mutant proof (fan-in gate, independent agent)

Run by an agent that did NOT write T3's gates: (a) revert packs to 0.6/0.6/0.55 → G-SEP,
G-RS-ii, G-NODE red; G-RS-i green (the spec's deliberate asymmetry); golden reproduces old bytes
→ restore; (b) call-only misroute mutant (scale CALL, not RAISE, in a throwaway engine copy or
via the probe pattern) dies on G-RS-i; cl no-op mutant dies on G-SEP + G-RS-ii + G-NODE;
byte-for-byte restoration after each; (c) full `./scripts/verify.sh` + `ruff` + suite unpiped,
`test_price_tail.py` green WITHOUT edit.
- Owned: none (read/execute; temporary mutations byte-restored).
- Done-condition: per-mutant kill table + revert evidence in the report.

## T6 — docs

Roadmap: mark R9-LOOSEFIT built; W4-b lag-WTSD note; R9-DEFENCE-b rebaseline note. Feasibility
report: append the posture caveat (additive). 
- Owned: `docs/ai-dlc/roadmap/persona-realism.md`, `docs/ai-dlc/reports/r9-loosefit-feasibility.md`.
- Done-condition: greps for the three notes + caveat present.

## DAG

T1 → T2 → T3 → T4 → T5 (independent agent) → T6 → dual review + theory reviewer at fan-in.
No parallel waves — T1/T3/T4 share one file; the slice is measurement-bound, not typing-bound.

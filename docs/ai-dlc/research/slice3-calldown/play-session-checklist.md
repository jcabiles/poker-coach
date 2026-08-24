# Blind play session — slice 3 acceptance checklist

**Bottom line.** Your blind play session is what closes improvement slice 3
(calldown), per the standing 2026-08-17 ruling that your table impressions are
the primary acceptance evidence — they outrank the statistical gates. This
page is the whole procedure: what to run, what to write down before each
reveal, and what verdict closes the slice. Budget one normal session; nothing
here needs more than pen and paper alongside the app.

## Setup

- Build: `main` at `0561e8f` (S3-T1 through S3-T5 all merged; the engine has
  not changed since). Start with `poker-coach` or `./scripts/serve.sh start`.
- Persona labels stay VISIBLE — the table-controls lane (label hiding, table
  picker) is frozen until the finale by your 2026-08-23 ruling, and slice 2's
  acceptance session also played with labels visible, so the comparison is
  like-for-like.
- Your slice-2 session impressions are in `local/session-2026-08-19/`; skim
  them first so "different from last time" has a baseline.

## What slice 3 changed at the table — the three things to actually watch

1. **The nit and the TAG fold out of more hands they used to call down**
   (ticket S3-T2 retuned their calling dials: nit 0.45 → 0.32, TAG
   0.60 → 0.38). Watch: do they now feel appropriately tight, or do they feel
   like they give up too easily — folding hands a human regular would peel
   once with?
2. **The LAG bets more unopened turns and rivers** (ticket S3-T5's
   late-street lever — the LAG is the only persona that got it). Watch: do
   its late-street stabs feel like a live aggressive player probing, or like
   a bot that suddenly discovered the bet button? Also watch its river bets'
   mix — the lever raised bluffs proportionally more than value, on purpose.
3. **Fewer hands where everyone just checks to showdown** — the "boring
   check-down" feel. This should be noticeably rarer with the LAG at the
   table and roughly unchanged for the nit and TAG (their late-street lever
   was measured and withdrawn — a fact, not an oversight).

## Before each reveal, write down

- Which seats felt **passive-robotic** (check-down to showdown with no
  visible intent).
- Which seats folded ace-high or weak pairs on the river "**too cleanly**" —
  the invest-then-fold signature slice 2 worked on.
- Any moment a bet **size or timing** read as mechanical.
- (Optional but useful for the frozen table-controls lane later: a predicted
  archetype for three named seats, checked at reveal.)

## Verdict

Accept or reject **per persona**, plus one overall line: did the table feel
plausibly human, and did anything stand out as robotic that did not in the
slice-2 session? Acceptance closes slice 3 and the improvement phase's build
work; what remains after that is the single finale detection run (see
`finale-readiness.md` in this directory) and your rulings in
`owner-decisions.md`. A rejection reopens the slice with your notes as the
defect list — write down WHICH seat and WHICH behaviour, not just "felt off".

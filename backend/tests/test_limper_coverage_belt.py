"""M2 belt test (RES-G Slice A, pass/fail a): the missing vs_limpers coverage
fill (UTG2/LJ/HJ/SB x1, CO/SB x2) now maps on ORGANIC bot play.

Drives seeded hands through the REAL engine + REAL bot policy (same method as
`test_mw_funnel_belt.py`: hero seat 0 plays a persona-pack proxy, button
rotates, stacks reset to 100bb per hand, lineup shuffled per hand, one seeded
Random) and records, for each hero pre-decision preflop spot that
`map_preflop` grades, the (hero position, limper_count) pair. Before M2 these
six named pairs returned None (RES-G §1d/§5); after M2's content fill they
must each fire at least once over a large-enough organic sample.

Refuter correction (M2 post-review): RES-G §3a authored the EP faces-1 entry
as "UTG", but §1d's own measurement is UTG2 — and UTG structurally cannot
face a limper (it acts first preflop, `_before(UTG) == []`), which also broke
`scenarios.build_spot`'s Practice-mode path (empty seat-fill loop → incoherent
Spot). The entry was renamed UTG->UTG2 in content; asserted here accordingly.

Deterministic (seeded); a failure here means either the content fill regressed
or organic bot play stopped generating these decision shapes — investigate,
don't retune.
"""

from __future__ import annotations

import random

from app.domain.personas import load_persona_packs
from app.domain.table.deck import deal_hand
from app.domain.table.engine import apply, start_hand
from app.domain.table.grade_map_preflop import map_preflop
from app.domain.table.play import assign_lineup, bot_decision

HERO_SEAT = 0
SEED = 20260722
HANDS = 4000

_WANT_1 = {"UTG2", "LJ", "HJ", "SB"}
_WANT_2 = {"CO", "SB"}
# M3 (RES-G Slice B): the BB check-or-iso option node fires organically too.
_WANT_BB = {("BB", 1), ("BB", 2), ("BB", 3)}
# M3 regression pin: fire counts for every pair that mapped BEFORE M3, at this
# exact seed. Originally pinned to prove M3's BB-only builder/grader path
# moved no non-BB pair. RE-PINNED for P1 (persona-realism-p1, 2026-07-23):
# P1's own preflop content fixes — B1 (station premiums stop folding
# unopened), M3 (maniac/lag non-SB open-limps deleted) and N3 (maniac
# vs_4bet rebuild), plus A1's air-call drop — deliberately change bot
# preflop mixes, which shifts the shared-rng hand stream and therefore every
# organic fire count at this seed (old counts: UTG2¹ 99, LJ¹ 128, HJ¹ 142,
# CO¹ 139, CO² 39, SB¹ 102, SB² 54, BTN¹ 111, BTN² 56). Counts below are
# the re-measured post-P1 values; every coverage pair still fires (the
# _WANT_* assertions are the real belt). A future drift here again means a
# limped-shape-producing behavior changed — investigate, don't retune.
# RE-PINNED for P2a (persona-realism-p2a Q3, 2026-07-23): play.py now passes
# `street` to the postflop sampler, and river polarization (one-pair never
# raises the river, air never calls) changes bot RIVER decisions — which
# consume draws from the SAME shared rng that deals/plays every subsequent
# hand, shifting the whole organic stream at this seed (old post-P1 counts:
# UTG2¹ 94, LJ¹ 127, HJ¹ 140, CO¹ 133, CO² 29, SB¹ 101, SB² 43, BTN¹ 125,
# BTN² 48). No preflop content changed in P2a; the drift is stream
# displacement only.
# RE-PINNED for W1-a (persona-realism-w1, 2026-07-24 — slice-authorized): the
# middle-pair river BET floor (F6) changes bot RIVER decisions, again shifting
# the shared-rng organic stream at this seed (old post-P2a counts: UTG2¹ 84,
# LJ¹ 123, HJ¹ 142, CO¹ 131, CO² 31, SB¹ 95, SB² 42, BTN¹ 122, BTN² 49). No
# preflop content changed; every _WANT_* coverage shape still fires (verified) —
# stream displacement only, not a coverage regression.
# RE-PINNED for W1-b (persona-realism-w1, 2026-07-24 — slice-authorized): the
# faced_frac increment fix (F9) changes bot fold/call/raise on self-re-raise &
# back-raise postflop spots via play.py's production path, again displacing the
# shared-rng stream (old post-W1-a counts: UTG2¹ 97, LJ¹ 129, HJ¹ 154, CO¹ 140,
# CO² 32, SB¹ 107, SB² 50, BTN¹ 122, BTN² 49). Every _WANT_* shape still fires.
# RE-PINNED for W1-c (persona-realism-w1, 2026-07-24 — slice-authorized): the
# multiway made-value BET damp (F13) changes bot postflop betting, displacing the
# stream again (old post-W1-b counts: UTG2¹ 96, LJ¹ 132, HJ¹ 154, CO¹ 145, CO²
# 33, SB¹ 101, SB² 53, BTN¹ 124, BTN² 50). Every _WANT_* shape still fires.
# RE-PINNED for W2-a (persona-realism-w2, 2026-07-24 — slice-authorized): the
# calling_station/passive_fish elasticity split (size_elasticity) changes their
# faced-size fold decisions in the shared lineup, displacing the shared-rng stream
# again (old post-W1-c counts: UTG2¹ 86, LJ¹ 117, HJ¹ 139, CO¹ 128, CO² 45, SB¹
# 119, SB² 51, BTN¹ 127, BTN² 43). No preflop content changed; every _WANT_* shape
# still fires (verified) — stream displacement only.
# RE-PINNED for W2-b (persona-realism-w2, 2026-07-24 — slice-authorized): the
# commit/draw EV gate changes bot postflop play (STRONG draw folds to overbets;
# WEAK draw stops stacking off), displacing the shared-rng stream again (old
# post-W2-a counts: UTG2¹ 91, LJ¹ 122, HJ¹ 140, CO¹ 113, CO² 43, SB¹ 111, SB² 45,
# BTN¹ 134, BTN² 40). Every _WANT_* shape still fires (verified) — displacement only.
# RE-PINNED for W3-b/c/d (persona-realism-w3bcd, 2026-07-24 — slice-authorized): the
# position IP/OOP multiplier, the street aggression schedule + busted-river bluff, and
# the made-hand texture brakes all change villain postflop play, displacing the shared-
# rng organic stream again (old post-W2-b counts: UTG2¹ 87, LJ¹ 110, HJ¹ 134, CO¹ 141,
# CO² 33, SB¹ 96, SB² 69, BTN¹ 126, BTN² 44). No preflop content changed; every _WANT_*
# coverage shape still fires (verified) — stream displacement only, not a regression.
# RE-PINNED for W3R-1 (persona-realism-w3r1, 2026-07-24 — slice-authorized): a PURE
# preflop-content change (maniac `vs_rfi` 3-tier legit range replaces the any-two
# cold-call; maniac + lag SB open-limps deleted; maniac HJ/CO/BTN offsuit-ace opens
# trimmed) changes bot PREFLOP mixes directly, shifting the shared-rng hand stream at
# this seed (old post-W3-b/c/d counts: UTG2¹ 99, LJ¹ 107, HJ¹ 132, CO¹ 118, CO² 43,
# SB¹ 102, SB² 50, BTN¹ 130, BTN² 41). Every _WANT_* coverage shape still fires
# (verified) — stream displacement, not a coverage regression.
# RE-PINNED for W3R-2 (persona-realism-w3r2, 2026-07-24 — slice-authorized): a PURE
# persona-JSON postflop dial change (fish `call_looseness` 0.42; station
# `size_elasticity` 0.0 → 0.55 + `call_looseness` 4.0) changes how those two bots
# respond to a faced bet, so hands end differently and the shared-rng stream drifts at
# this seed (old post-W3R-1 counts: UTG2¹ 84, LJ¹ 124, HJ¹ 151, CO¹ 125, CO² 35,
# SB¹ 111, SB² 63, BTN¹ 122, BTN² 44). No preflop content changed; every _WANT_*
# coverage shape still fires (verified) — stream displacement, not a coverage regression.
# RE-PINNED for W3R-3 (persona-realism-w3r-3, 2026-07-24 — slice-authorized): the #4
# spr_commit ladder (fish 2.0 → 1.4, maniac 4.0 → 3.3) changes both bots' low-SPR
# stack-off decisions, so hands end differently and the shared-rng stream drifts at
# this seed (old post-W3R-2 counts: UTG2¹ 84, LJ¹ 121, HJ¹ 140, CO¹ 138, CO² 30,
# SB¹ 98, SB² 55, BTN¹ 129, BTN² 44). #12's `call_looseness` authoring is
# byte-identical; #5 was dropped by owner decision. No preflop content changed; every
# _WANT_* coverage shape still fires — stream displacement, not a coverage regression.
# RE-PINNED for W3R-4 (persona-realism-w3r-4, 2026-07-24 — slice-authorized): the #11
# `_CALL_BASE[MIDDLE_PAIR]` 0.60 → 0.52 trim changes every bot's naked-middle-pair
# response to a faced bet, so hands end differently and the shared-rng stream drifts at
# this seed (old post-W3R-3 counts: UTG2¹ 80, LJ¹ 117, HJ¹ 150, CO¹ 152, CO² 31,
# SB¹ 102, SB² 60, BTN¹ 126, BTN² 45). The #7 multiway busted-bluff damp contributes
# nothing here (preflop mapping, and the add-on is river-only). No preflop content
# changed; every _WANT_* coverage shape still fires — stream displacement, not a
# coverage regression.
# RE-PINNED for W3R-6 (persona-realism-w3r-6, 2026-07-24 — slice-authorized): the two
# facing-a-raise merit damps (#9 made one-pair stops re-raising into flop/turn action;
# #5 naked ace-high stops floating a raise) change bot postflop play at every
# facing-a-raise node, so hands end differently and the shared-rng stream drifts at this
# seed (old post-W3R-4 counts: UTG2¹ 90, LJ¹ 132, HJ¹ 151, CO¹ 126, CO² 40, SB¹ 113,
# SB² 53, BTN¹ 130, BTN² 37). No preflop content changed; every _WANT_* coverage shape
# still fires (verified) — stream displacement, not a coverage regression.
# RE-PINNED for W5-b1 (persona-realism-w5-b1, 2026-07-25 — slice-authorized): the
# nit/tag/lag `unopened` ladders were widened to 9-max full-ring widths (authored
# mean nit 8.0 → 28.5, tag 16.4 → 34.0, lag 22.6 → 43.2), a PURE preflop-content
# change that alters bot preflop mixes directly — so the shared-rng hand stream
# shifts at this seed (old post-W3R-6 counts: UTG2¹ 71, LJ¹ 132, HJ¹ 134, CO¹ 137,
# CO² 32, SB¹ 123, SB² 48, BTN¹ 125, BTN² 35). Wider opens ALSO mean fewer limped
# pots survive to hero, which is why the late-seat faces-1 counts fall while UTG2
# rises. Every _WANT_* coverage shape still fires (verified: UTG2¹ 109, LJ¹ 112,
# HJ¹ 98, SB¹ 90, CO² 38, SB² 47, BB¹ 58, BB² 35, BB³ 7) — stream displacement
# plus the intended range widening, not a coverage regression.
# RE-PINNED for T-ANCHOR (persona-realism-wave-a, 2026-07-29 — slice-authorized):
# the unopened air cell now applies the W3-b position multiplier BEFORE forming its
# CHECK complement, so nit/tag/lag c-bet/barrel air MORE in position and LESS out of
# position (exact-frequency anchor restored). Those villains' postflop decisions flip
# on a small share of nodes, so hands end differently and the shared-rng organic
# stream drifts at this seed (old post-W5-b1 counts: UTG2¹ 109, LJ¹ 112, HJ¹ 98,
# CO¹ 102, CO² 38, SB¹ 90, SB² 47, BTN¹ 93, BTN² 30). No preflop content changed;
# every _WANT_* coverage shape still fires (verified: UTG2¹ 111, LJ¹ 117, HJ¹ 88,
# SB¹ 89, CO² 40, SB² 46, BB¹ 55, BB² 34, BB³ 6) — stream displacement, not a
# coverage regression.
# RE-PINNED for R10-PRE1 (persona-realism-r10-pre1, 2026-07-30 — slice-
# authorized): the maniac's premium unopened carve-out (TT+/AQs+/AKo raise 1.0,
# was raise 0.7-0.85 with explicit fold) opens more pots, so the shared-rng
# organic stream drifts at this seed (old post-T-ANCHOR counts: UTG2¹ 111,
# LJ¹ 117, HJ¹ 88, CO¹ 103, CO² 40, SB¹ 89, SB² 46, BTN¹ 92, BTN² 29). No
# limper-belt content changed — stream displacement, not a coverage regression
# (BB¹ 56, BB² 30, BB³ 5 still fire).
# RE-PINNED for R10-PRE2 (persona-realism-r10-pre2, 2026-07-30 — slice-
# authorized): the maniac `unopened` ladder widened above the LAG's at every
# seat (authored seat-avg first-in raise 51.8%), so far more pots see a maniac
# open instead of folding around/limping and the shared-rng organic stream
# drifts at this seed (old post-R10-PRE1 counts: UTG2¹ 105, LJ¹ 121, HJ¹ 106,
# CO¹ 108, CO² 38, SB¹ 83, SB² 41, BTN¹ 96, BTN² 32). No limper-belt content
# changed — stream displacement plus genuinely fewer limp-fests surviving to
# hero in late seats (SB¹ 83 → 61), which is the intended direction of a table
# with a real maniac at it. Every _WANT_* coverage shape still fires
# (verified: BB¹ 64, BB² 39, BB³ 7) — not a coverage regression.
# RE-PINNED for W5-b4 (persona-realism-w5b4, 2026-07-31 — slice-authorized):
# the maniac vs_limpers/vs_rfi repair (positional iso toward ~60% late; the
# flat-call tier converted to 3bet/call/fold; light any-two cold-3bet) makes
# the maniac attack limped pots it used to ignore, so fewer limped pots
# survive to hero — a GENUINE texture change, the slice's stated intent, on
# top of stream displacement (old post-R10-PRE2 counts: UTG2¹ 85, LJ¹ 116,
# HJ¹ 122, CO¹ 97, CO² 27, SB¹ 61, SB² 41, BTN¹ 81, BTN² 40). No limper-belt
# content changed; every _WANT_* coverage shape still fires (verified:
# BB¹ 39, BB² 33, BB³ 5) — not a coverage regression.
# RE-PINNED for R10-3BET (persona-realism-r10-3bet, 2026-07-31 — slice-
# authorized): the six-pack vs_3bet rewrite changes every persona's response
# from the first re-raised pot onward (nit/tag/lag/station/fish continue where
# they used to auto-fold; maniac mixes calls into its old 4bet-1.0 tier), so
# hands end differently and the shared-rng organic stream drifts at this seed
# (old post-W5-b4 counts: UTG2¹ 89, LJ¹ 91, HJ¹ 117, CO¹ 94, CO² 36, SB¹ 65,
# SB² 28, BTN¹ 74, BTN² 40). No limper-belt content changed; every _WANT_*
# coverage shape still fires (verified: BB¹ 39, BB² 26, BB³ 2) — stream
# displacement, not a coverage regression.
# RE-PINNED for RR-HOLES (2026-07-31, slice-authorized): typo-hole cleanup
# (station/fish/tag/lag preflop membership additions) displaces the shared-rng
# organic stream at this seed (old post-R10-3BET counts: UTG2¹ 101, LJ¹ 105,
# HJ¹ 114, CO¹ 85, CO² 26, SB¹ 54, SB² 41, BTN¹ 86, BTN² 38). Every _WANT_*
# coverage shape still fires (verified: BB¹ 40, BB² 28, BB³ 5) — stream
# displacement, not a coverage regression.
# RE-PINNED for W5-b3 (persona-realism-w5b3, 2026-07-31 — slice-authorized):
# the nit nine-seat unopened ladder (7.54% UTG → 21.42% BTN, was 13.6/29.1
# flat) means a much tighter nit leaves far more pots unopened/limpable, so
# the organic stream shifts genuinely as well as by displacement (old
# post-RR-HOLES counts: UTG2¹ 96, LJ¹ 98, HJ¹ 99, CO¹ 101, CO² 30, SB¹ 68,
# SB² 40, BTN¹ 73, BTN² 36). Every _WANT_* coverage shape still fires
# (verified: BB¹ 56, BB² 25, BB³ 5) — not a coverage regression.
# RE-PINNED for R10-TAIL-a1 (2026-07-31, slice-authorized): the piecewise
# absolute-price tail (`_price_factor`: f > 1.5 ⇒ factor *= (f/1.5)**2.0)
# makes every persona fold more vs true overbets, so overbet pots end earlier
# and the shared-rng organic stream drifts at this seed (old post-W5-b3
# counts: UTG2¹ 84, LJ¹ 124, HJ¹ 116, CO¹ 117, CO² 24, SB¹ 57, SB² 51,
# BTN¹ 90, BTN² 44). No preflop or limper-belt content changed; every _WANT_*
# coverage shape still fires (verified: BB¹ 59, BB² 25, BB³ 5) — stream
# displacement, not a coverage regression.
# RE-PINNED for R10-TAIL-b1 (2026-07-31, slice-authorized): TOP_PAIR joined
# `_MW_CATCH_BUCKETS`, so bare top pair now folds more often facing multiway
# aggression — and limped family pots are exactly where that cell lives, so
# this belt's organic stream shifts genuinely (old post-R10-TAIL-a1 counts:
# UTG2¹ 75, LJ¹ 128, HJ¹ 117, CO¹ 118, CO² 22, SB¹ 54, SB² 54, BTN¹ 85,
# BTN² 43). The coverage-baseline and N200-golden streams are byte-identical
# under the same change (their samples hit no changed cell). Every _WANT_*
# coverage shape still fires (verified: BB¹ 52, BB² 25, BB³ 5) — not a
# coverage regression.
# RE-PINNED for N-3BSTRATA (2026-07-31, slice-authorized): the vs_3bet
# opener/cold split makes maniac/lag DEFEND their opens instead of folding,
# so 3-bet pots go multiway/showdown far more often and the shared-rng
# organic stream drifts at this seed (old post-R10-TAIL-b1 counts: UTG2¹ 86,
# LJ¹ 126, HJ¹ 115, CO¹ 119, CO² 25, SB¹ 51, SB² 47, BTN¹ 85, BTN² 41). No
# limper-belt content changed; every _WANT_* coverage shape still fires
# (verified: BB¹ 39, BB² 29, BB³ 5) — stream displacement plus genuinely
# longer 3-bet hands, not a coverage regression.
# RE-PINNED for R9-DEFENCE-a (2026-08-02 — slice-authorized, owner-ruled):
# T2's line-sensitivity mechanism makes every opted-in villain fold more to
# a same-seat second-street barrel, changing bot postflop decisions at
# facing-chips nodes across the shared organic rng stream (old post-N-3BSTRATA
# counts: UTG2¹ 84, LJ¹ 122, HJ¹ 98, CO¹ 99, CO² 33, SB¹ 70, SB² 29,
# BTN¹ 75, BTN² 36). ATTRIBUTION PROVEN, not assumed (the #160-entry method):
# at this tip, restoring ONLY this slice's changed files
# (personas_postflop.py, content/models.py, content/personas/*.json) to
# their base 8cc6c38 contents turned this test AND test_coverage_baseline.py
# green again unmodified; putting the current files back reproduced both
# failures — the slice is the sole cause. No limper-belt content changed;
# every _WANT_* coverage shape still fires (verified: HJ¹ 111, LJ¹ 125,
# SB¹ 65, UTG2¹ 78; CO² 31, SB² 30; BB¹ 40, BB² 25, BB³ 10) — stream
# displacement, not a coverage regression.
_PRE_M3_FIRES = {
    # RE-RECORDED for WAVE 3 COMBINED (persona-realism-wave3, 2026-07-31 —
    # wave-authorized, recorded once on the combined lane-B + lane-A tip):
    # nit CO/BTN pair opens + maniac vs_4bet pairs + the lag composition swap
    # compound their rng-stream displacement, so every pair moves (lane B
    # alone moved only (LJ,1) 116 -> 117).
    # RE-RECORDED for WAVE 4 COMBINED (persona-realism-wave4, 2026-08-01 —
    # wave-authorized, recorded once on the combined lane-C + lane-D tip):
    # N-M4BET + N-TAGCOMP preflop content compound the stream displacement;
    # every pair moves.
    # RE-RECORDED for N-LAGCOMP2 (persona-realism-wave5, 2026-07-31 —
    # wave-authorized, single-recorder landing): the lag CO/BTN/SB
    # offsuit→suited swap (width-neutral) changes which hands the lag opens
    # late, so the shared-rng organic stream drifts at this seed (old
    # post-WAVE-4 counts: UTG2¹ 105, LJ¹ 125, HJ¹ 133, CO¹ 102, CO² 26,
    # SB¹ 71, SB² 39, BTN¹ 80, BTN² 38). No limper-belt content changed;
    # every _WANT_* coverage shape still fires (verified: BB¹ 55, BB² 23,
    # BB³ 5) — stream displacement, not a coverage regression.
    # RE-PINNED for the WAVE-6 lane-A landing (persona-realism-wave6,
    # 2026-08-01 — wave-authorized, single-recorder): these counts were STALE
    # AT THE WAVE BASE b54fe6e — the wave-5 #152/#153 squash-merge chain lost
    # that wave's re-record, so main itself failed here (('UTG2',1) 87 != 92).
    # This belt runs PRODUCTION bot_decision (no harness), and lane A touches
    # no production code: the measured counts below are IDENTICAL on b54fe6e
    # and on this tip — pure restoration of the lost record, zero behavior
    # change (lost-record counts: UTG2¹ 92, LJ¹ 117, HJ¹ 122, CO¹ 99,
    # CO² 26, SB¹ 62, SB² 40, BTN¹ 93, BTN² 29). _WANT_* all fire
    # (BB¹ 45, BB² 39, BB³ 12).
    # RE-PINNED for the WAVE-6 #157 merge (chore repair, 2026-08-01): the
    # T-M4 maniac vs_4bet call-leg content displaces the shared organic rng
    # stream (maniac decisions consume different draws), moving 7 of 9 pairs
    # (old: UTG2¹ 87, LJ¹ 128, HJ¹ 114, CO¹ 99, CO² 36, SB¹ 69, SB² 28,
    # BTN¹ 78, BTN² 32); the wave-6 squash chain lost the final-tip
    # re-record, leaving main red (('UTG2',1) 91 != 87). No limper-belt
    # content changed; every _WANT_* coverage shape still fires (verified:
    # BB¹ 49, BB² 36, BB³ 8) — stream displacement, not a coverage
    # regression.
    # RE-PINNED for the #160 merge (chore repair, 2026-08-02): N-LAGWIDTH
    # trimmed lag's CO/BTN/SB offsuit opening width, so the lag opens fewer
    # hands late and the shared organic rng stream drifts at this seed,
    # moving 8 of 9 pairs (old: UTG2¹ 91, LJ¹ 118, HJ¹ 114, CO¹ 99, CO² 38,
    # SB¹ 72, SB² 35, BTN¹ 76, BTN² 30). The #160 squash chain lost this
    # pin's update, leaving main red (('UTG2',1) 84 != 91) — the FOURTH
    # occurrence of the lost-re-record pattern (see #159 and the two wave-6
    # entries above). ATTRIBUTION PROVEN, not assumed: reverting ONLY
    # content/personas/lag.json + ladders/lag.unopened.json to 8729e14 at
    # this tip turns this test AND the N200 golden green again, so the lag
    # pack change is the sole cause. No limper-belt content changed; every
    # _WANT_* coverage shape still fires (verified: BB¹ 45, BB² 34, BB³ 9)
    # — stream displacement, not a coverage regression.
    # RE-RECORDED for R9-LOOSEFIT (2026-08-04, slice-authorized): the nit
    # pack's `call_looseness` 0.6 -> 0.45 (ONE number; no engine, preflop or
    # limper-belt content changed) makes the nit fold more to a faced bet, so
    # hands end differently and the shared organic rng stream drifts at this
    # seed, moving 7 of the 9 pairs (old: UTG2¹ 78, LJ¹ 125, HJ¹ 111, CO¹ 105,
    # CO² 31, SB¹ 65, SB² 30, BTN¹ 77, BTN² 30; SB¹ and BTN² are unchanged).
    # ATTRIBUTION PROVEN, not assumed (the #160-entry method): at this tip,
    # reverting ONLY content/personas/nit.json to its b63dfaa contents
    # reproduces those old counts exactly, and restoring 0.45 reproduces the
    # counts below exactly — the pack change is the sole cause. Every _WANT_*
    # coverage shape still fires (verified: BB¹ 42, BB² 24, BB³ 10) — stream
    # displacement, not a coverage regression.
    # RE-RECORDED for N-DRAWLOOSE T5 (2026-08-04, slice-authorized): T1
    # floors the calling dial at 1.0 for strong draws (an engine change in
    # `personas_postflop.py`, not limper-belt content), so the first
    # strong-draw-facing decision on the shared organic rng stream resolves
    # differently and every hand dealt after it is displaced. All nine pairs
    # move at this seed (old: UTG2¹ 74, LJ¹ 122, HJ¹ 114, CO¹ 100, CO² 29,
    # SB¹ 65, SB² 32, BTN¹ 78, BTN² 30). No limper-belt content changed;
    # every _WANT_* coverage shape still fires (verified: BB¹ 42, BB² 34,
    # BB³ 11). ATTRIBUTION PROVEN, not assumed: this test and the N200
    # golden's _GOLDEN_STATS_N200 both pass unmodified, with their PRE-T5
    # recorded values, against the control worktree at base commit b0a6a4e
    # (old engine, no T1 change); the counts below only hold once T1's
    # branch lands.
    ("UTG2", 1): 70, ("LJ", 1): 133, ("HJ", 1): 109, ("CO", 1): 107,
    ("CO", 2): 30, ("SB", 1): 64, ("SB", 2): 47, ("BTN", 1): 87,
    ("BTN", 2): 29,
}


def _count_limper_coverage(proxy: str, seed: int, hands: int) -> dict[tuple[str, int], int]:
    packs = load_persona_packs()
    hero_pack = packs[proxy]
    rng = random.Random(seed)
    fires: dict[tuple[str, int], int] = {}
    for hand_no in range(hands):
        lineup = assign_lineup(rng)
        seat_packs = {s: packs[t.value] for s, t in lineup.items()}
        state = start_hand(
            deal_hand(rng), button_seat=hand_no % 9, stacks_bb=[100.0] * 9
        )
        guard = 0
        while not state.hand_over and state.to_act_seat is not None:
            guard += 1
            assert guard <= 500, "bot playout did not terminate"
            seat = state.to_act_seat
            if seat == HERO_SEAT:
                spot = map_preflop(state, HERO_SEAT)
                if spot is not None and spot.limper_count > 0:
                    key = (spot.to_act.value, spot.limper_count)
                    fires[key] = fires.get(key, 0) + 1
                dec = bot_decision(state, seat, hero_pack, rng)
            else:
                dec = bot_decision(state, seat, seat_packs[seat], rng)
            state = apply(state, dec)
    return fires


def test_limper_coverage_fires_on_organic_play():
    fires = _count_limper_coverage("calling_station", SEED, HANDS)
    for pos in _WANT_1:
        assert fires.get((pos, 1), 0) >= 1, f"faces-1 @ {pos} never fired: {fires}"
    for pos in _WANT_2:
        assert fires.get((pos, 2), 0) >= 1, f"faces-2 @ {pos} never fired: {fires}"
    for key in _WANT_BB:
        assert fires.get(key, 0) >= 1, f"BB x{key[1]} never fired: {fires}"
    for key, count in _PRE_M3_FIRES.items():
        assert fires.get(key, 0) == count, (
            f"pre-M3 pair {key} fire count moved: {fires.get(key, 0)} != {count}"
        )

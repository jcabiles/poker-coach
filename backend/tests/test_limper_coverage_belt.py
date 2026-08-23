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
    # RE-RECORDED for N-DRAWLOOSE (2026-08-05, slice-authorized, final engine
    # tip db1f278): T1 floors the calling dial at 1.0 for strong draws (an
    # engine change in `personas_postflop.py`, not limper-belt content), so
    # the first strong-draw-facing decision on the shared organic rng stream
    # resolves differently and every hand dealt after it is displaced. This
    # entry REPLACES the T5 entry it superseded rather than appending after
    # it — the T5 values were an intermediate reading against a
    # since-reformulated engine (R1/R2 rebuilt the floor twice more after
    # adversarial review) and never shipped. OLD side measured directly
    # against the control worktree at base commit b0a6a4e (this slice's only
    # engine file, `personas_postflop.py`, absent): UTG2¹ 74, LJ¹ 122,
    # HJ¹ 114, CO¹ 100, CO² 29, SB¹ 65, SB² 32, BTN¹ 78, BTN² 30 — this
    # matches the T5 entry's own "old" side exactly, since the base engine
    # (b0a6a4e) is unaffected by anything on this branch. All nine pairs
    # move again at this tip vs base. No limper-belt content changed; every
    # _WANT_* coverage shape still fires (measured at this tip: BB¹ 39,
    # BB² 25, BB³ 6; base measures BB¹ 42, BB² 24, BB³ 10 — both comfortably
    # clear the >=1 gate). ATTRIBUTION PROVEN, not assumed: this test and the
    # N200 golden's _GOLDEN_STATS_N200 both pass, unmodified, against the
    # control worktree at base commit b0a6a4e with their OLD (base) values;
    # the counts below only hold once this slice's engine change lands.
    # RE-RECORDED for the de-robotization slice (2026-08-15, slice-authorized):
    # `vs_rfi`, `vs_limpers` and `vs_3bet` are now answered per seat in all six
    # packs, so villains continue and isolate at different rates by position
    # and the shared organic rng stream drifts at this seed. All nine pairs
    # move (old: UTG2¹ 95, LJ¹ 111, HJ¹ 103, CO¹ 98, CO² 34, SB¹ 63, SB² 37,
    # BTN¹ 87, BTN² 42). No limper-belt content changed, and every _WANT_*
    # coverage shape still fires (measured at this tip: BB¹ 53, BB² 30,
    # BB³ 2 — the >=1 gate is what this belt actually guarantees, and it
    # holds). ATTRIBUTION: this slice touches only content/personas/*.json
    # and tests; no engine or limper-belt file is modified.
    #
    # ⚠️ These counts are a stream fingerprint, not a coverage measurement.
    # This is the eleventh re-record in this block, every one of them for the
    # same reason. Reading a coverage claim off the raw numbers is a mistake
    # the slice's own coverage work makes concrete: at 400 hands and one seed
    # the companion harness reported hero grading down 3.05pp, and at 2,000
    # hands across three seeds the same comparison reads 0.7pp with the
    # preflop component flat. Single-seed counts move far more than the
    # effects anyone wants to read out of them.
    # Re-recorded a second time in the same slice: range-edge softening
    # (commit 2) shifts the stream again on top of the seat split (commit 1).
    # Every _WANT_* shape still fires at this tip: BB1 61, BB2 29, BB3 7.
    # Re-recorded a third time in the same slice, for the review rework.
    # Every _WANT_* shape still fires: BB1 49, BB2 28, BB3 3.
    # RE-RECORDED for T5 (2026-08-16, slice-authorized): postflop bet sizes are
    # re-weighted across all six packs. No limper-belt content changed and no
    # preflop content changed — the bots bet different amounts, so hands end
    # differently and the shared organic stream drifts at this seed, moving all
    # nine pairs (old: UTG2¹ 101, LJ¹ 118, HJ¹ 115, CO¹ 98, CO² 37, SB¹ 68,
    # SB² 36, BTN¹ 77, BTN² 34). Every _WANT_* coverage shape still fires
    # (verified: BB¹ 46, BB² 23, BB³ 2) — stream displacement, not a coverage
    # regression. Recorded once, at the end of the ticket, with pack content
    # frozen; the three separate re-records above are what that discipline is
    # meant to avoid repeating.
    # RE-RECORDED for T5's SECOND review round (2026-08-17,
    # slice-authorized): the tag and lag gain a third-pot bet on wet flops and
    # lag loses the wet-flop overbet the first round gave it, so those packs
    # bet different amounts, hands end differently and the shared organic
    # stream drifts at this seed. All nine pairs move (old: UTG2¹ 96, LJ¹ 96,
    # HJ¹ 120, CO¹ 105, CO² 36, SB¹ 82, SB² 42, BTN¹ 86, BTN² 38).
    # ATTRIBUTION IS BY CONSTRUCTION rather than by a revert experiment, which
    # is stronger here because it is exhaustive: the round's whole content diff
    # is two `cbet_wet` blocks, two `version` strings and six `_doc` entries.
    # Neither of the last two can reach this belt — `_doc` is not a model field
    # at all, and a version string only enters `config_hash`, which only the
    # export digests read. No limper-belt content changed; every _WANT_* shape
    # still fires (verified: BB¹ 49, BB² 21, BB³ 3) — stream displacement, not
    # a coverage regression.
    # RE-RECORDED for T2b (2026-08-17, slice-authorized): PREFLOP raise sizes
    # are now drawn from a mix, keyed by seat for the three regulars. All nine
    # pairs move (old: UTG2¹ 100, LJ¹ 107, HJ¹ 126, CO¹ 93, CO² 32, SB¹ 68,
    # SB² 36, BTN¹ 86, BTN² 30).
    # Displacement, not an arrival change. An earlier version of this note said
    # the opposite — "opens are smaller, so calling one is cheaper and more
    # seats come along" — which cannot happen: `sample_preflop_action` takes no
    # size argument and `_preflop_facing` keys on the raise COUNT, so no bot's
    # calling frequency reads a bb amount. Measured with the rng stream held
    # aligned, seats per flop FELL 1.7%. What preflop sizing does reach is the
    # pot, and through it the stack-to-pot ratio the postflop commitment ramp
    # uses; hands go further rather than wider. The belt exists to prove every
    # shape is still REACHED, and every one still is.
    # RE-RECORDED for T1 (improvement slice 2, 2026-08-18, slice-authorized):
    # naked ace-high stops floating a BET with more than one opponent live on
    # the flop and turn (`personas_postflop._ACE_HIGH_FLOAT_RAISE_DAMP`,
    # predicate widened from `facing_raise` to `facing_raise or opponents > 1`).
    # No limper-belt content changed and no preflop content changed. All nine
    # pairs move (old: UTG2¹ 85, LJ¹ 121, HJ¹ 117, CO¹ 102, CO² 23, SB¹ 65,
    # SB² 34, BTN¹ 103, BTN² 39). Every _WANT_* coverage shape still fires
    # (verified: BB¹ 57, BB² 28, BB³ 5) — stream displacement, not a coverage
    # regression.
    # THESE ARE PREFLOP COUNTS MOVED BY A POSTFLOP CHANGE, which looks wrong
    # and is not. The belt plays whole hands on one shared rng stream, so
    # changing what a bot does on a multiway flop changes how many further
    # decisions that hand contains, which displaces the deal and the preflop
    # action of every hand after it. The displacement is the whole of the
    # effect here; nothing about limping, and nothing about arrival, changed.
    # NO NEW RANDOM DRAW WAS ADDED AND NONE PRECEDES THE ACTION DRAW. That is
    # slice 1's actual rule and it is intact — worth stating, because breaking
    # it would shift every seeded test in the repository rather than only the
    # exact-count pins.
    # THE NUMBER OF DRAWS IS NOT INVARIANT, and an earlier version of this note
    # wrongly said it was ("the same NUMBER of draws is taken and different
    # ACTIONS come out of them"). The damp only reweights an existing call
    # merit, but that changes which action is drawn, and the sizing draw is
    # conditional on the action — flip a CALL into a RAISE and a draw that did
    # not previously happen now fires. Displacement is therefore expected here,
    # not excluded.
    # RE-RECORDED for T3 (improvement slice 2, 2026-08-19, slice-authorized):
    # naked ace-high may call a river bet again, at a damped weight. The river
    # call zero used to be written on `bluff_cell`, which bundles ACE_HIGH with
    # AIR; it is now written on the made-hand bucket and refuses AIR only, and
    # the restored ace-high call merit is multiplied by
    # `personas_postflop._ACE_HIGH_RIVER_CALL_DAMP` = 0.06. Minimum-defence
    # arithmetic derives about 0.46; 0.06 is a round value inside the range
    # two frozen went-to-showdown bands admit with margin, and the owner ruled
    # that conflict in the bands' favour on 2026-08-19. No limper-belt content
    # changed and no preflop content changed. Seven of the nine pairs move;
    # ("HJ", 1) and ("BTN", 2) land on their old values (old: UTG2 98, LJ 112,
    # HJ 116, CO 98, CO x2 26, SB 80, SB x2 42, BTN 83, BTN x2 31). Every
    # _WANT_* coverage shape still fires (verified: BB 58, BB x2 27, BB x3 4)
    # — stream displacement, not a coverage regression.
    # The paragraphs above about WHY a postflop change moves preflop counts, and
    # about the draw count NOT being invariant, apply here unchanged: a river
    # fold flipping to a river call changes how many further decisions the hand
    # contains, which displaces the deal and the preflop action of every hand
    # after it. No new draw was added and none precedes the action draw.
    # RE-RECORDED for the lag vs-3-bet re-tune (2026-08-19,
    # slice-authorized): the lag's `vs_3bet` OPENER node folds more in its
    # three weakest tiers, so a lag that opened and got 3-bet now folds where
    # it used to call, the hand ends earlier, and the shared organic rng
    # stream drifts at this seed. All nine pairs move (old: UTG2 97, LJ 115,
    # HJ 116, CO 99, CO x2 25, SB 78, SB x2 40, BTN 85, BTN x2 31). No
    # limper-belt content changed, and every _WANT_* coverage shape still
    # fires (measured at this tip: BB 55, BB x2 27, BB x3 5) — stream
    # displacement, not a coverage regression. ATTRIBUTION: this slice's whole
    # content diff is three `weights` objects in one node of
    # content/personas/lag.json plus that pack's `version` and `_doc`; no
    # engine file and no limper-belt file is touched, and neither `version`
    # nor `_doc` can reach this belt (`_doc` is not a model field, and
    # `version` only enters `config_hash`, which only the export digests read).
    # RE-RECORDED for S3-T1 (improvement slice 3, 2026-08-21,
    # slice-authorized): a STRONG draw's call bonus is SPLIT under a calling
    # dial below 1.0 instead of being protected from it in full —
    # `personas_postflop._strong_draw_call_dial`, with
    # `_DRAW_CALL_PROTECTED_SHARE` = 0.7. Five of the six personas hold such a
    # dial, so they chase big draws slightly less, a hand that used to see a
    # turn now sometimes ends on the flop, and the shared organic rng stream
    # drifts at this seed. Eight of the nine pairs move; ("LJ", 1) lands on its
    # old value (old: UTG2 94, LJ 109, HJ 114, CO 106, CO x2 24, SB 82,
    # SB x2 37, BTN 86, BTN x2 28). No limper-belt content changed and no
    # preflop content changed.
    # ⚠️ ONE COVERAGE SHAPE IS NOW AT ITS MINIMUM: BB facing THREE limpers
    # fires once at this tip, against 5 before (BB x1 50, BB x2 27, BB x3 1).
    # The gate is >= 1 and it holds, but a shape sitting on 1 is one displaced
    # hand from a red belt, and the next slice to move this stream should
    # expect to have to say something about it. It is a rare shape at 4,000
    # hands, not a regression in what the belt reaches — nothing in this ticket
    # touches limping, preflop content, or the big blind's decision anywhere.
    # ⚠️ HISTORICAL — THIS RECIPE NO LONGER RUNS AS WRITTEN (marked 2026-08-22,
    # S3-T1b): `_DRAW_CALL_PROTECTED_SHARE` was deleted and
    # `_strong_draw_call_dial` takes two arguments now. The cache-free
    # equivalent is in the S3-T1b entry below. As written at the time: setting
    # the constant to 1.0 reproduced all nine OLD counts and the old BB shapes
    # (55/27/5) exactly, and restoring 0.7 reproduced THE NINE COUNTS S3-T1
    # SHIPPED. ⚠️ That second half is a FORWARD REFERENCE and it no longer
    # points at the counts below — those are S3-T1b's. The counts it meant are
    # UTG2 98, LJ 109, HJ 113, CO 94, CO x2 23, SB 80, SB x2 41, BTN 87,
    # BTN x2 27 (BB 50/27/1), which is exactly what forcing a flat 0.7 at the
    # current tip still reproduces — re-measured 2026-08-22.
    # The paragraphs above about WHY a postflop change moves preflop counts,
    # and about the draw count NOT being invariant, apply here unchanged. NO
    # NEW RANDOM DRAW WAS ADDED AND NONE PRECEDES THE ACTION DRAW: the split
    # only reweights an existing call merit.
    # RE-RECORDED for S3-T1b (improvement slice 3, 2026-08-22,
    # slice-authorized): the protected share of a STRONG draw's call bonus is
    # computed per node now — `personas_postflop._strong_draw_protected_share`,
    # from the faced price, the cards to come and the draw's out count —
    # instead of the flat 0.7 S3-T1 shipped. A well-priced big draw keeps the
    # protection the pre-S3-T1 floor gave it, a badly-priced one hands more of
    # the bonus to the dial, so hands end on different streets and the shared
    # organic rng stream drifts at this seed. All nine pairs move (old: UTG2 98,
    # LJ 109, HJ 113, CO 94, CO x2 23, SB 80, SB x2 41, BTN 87, BTN x2 27). No
    # limper-belt content changed and no preflop content changed.
    # ✅ OWNER SIGN-OFF ON THE BB-FACING-THREE-LIMPERS SHAPE AT n = 3,
    # 2026-08-22 (ruling R2). This is a decision on the record, not an
    # observation in passing, because S3-T1 left the same shape at n = 1 and
    # deferred it rather than adjudicating it, and a deferral repeated twice is
    # how a belt quietly stops covering something.
    # THE READING: BB facing three limpers fires 3 times at this tip
    # (BB x1 44, BB x2 28, BB x3 3), against 1 at the S3-T1 tip and 5 before it.
    # The gate is `>= 1` and it now holds with two to spare rather than none.
    # ⚠️ THE BELT STILL SITS NEAR ITS MINIMUM ON THIS SHAPE and the owner
    # accepted it in that knowledge: at 4,000 hands this shape's organic
    # frequency is low enough that any slice moving the shared rng stream will
    # keep walking it between roughly 1 and 5, and the next such slice should
    # expect to have to say something about it again. What is NOT true is that
    # coverage has regressed — nothing in this ticket or in S3-T1 touches
    # limping, preflop content, or the big blind's decision anywhere, so the
    # count is stream displacement. Raising `HANDS` for this belt would settle
    # it and would re-record all nine pinned counts; that is a change to the
    # belt's own sampling and belongs in a ticket that owns the belt, not
    # inside a postflop behaviour change.
    # ATTRIBUTION PROVEN, not assumed, and without a control worktree:
    # replacing `_strong_draw_protected_share` with one that returns 1.0 makes
    # `_strong_draw_call_dial(L, 1.0)` return exactly 1.0 for every dial, which
    # IS the `max(looseness, 1.0)` the engine carried before S3-T1. Doing that
    # at this tip reproduces the PRE-S3-T1 counts exactly (UTG2 94, LJ 109,
    # HJ 114, CO 106, CO x2 24, SB 82, SB x2 37, BTN 86, BTN x2 28, and BB
    # 55/27/5); the shipped share reproduces the counts below exactly.
    # The paragraphs above about WHY a postflop change moves preflop counts,
    # and about the draw count NOT being invariant, apply here unchanged. NO
    # NEW RANDOM DRAW WAS ADDED AND NONE PRECEDES THE ACTION DRAW: the split
    # only reweights an existing call merit.
    # RE-RECORDED for S3-T2 (improvement slice 3, 2026-08-22,
    # slice-authorized): the nit's `call_looseness` moves 0.45 -> 0.32 and the
    # tag's 0.6 -> 0.38, so both personas take a different action at facing
    # nodes, the shared organic rng stream displaces, and every pair moves (old
    # counts: UTG2 x1 85, LJ x1 101, HJ x1 120, CO x1 113, CO x2 37, SB x1 70,
    # SB x2 36, BTN x1 73, BTN x2 28). This belt runs PRODUCTION
    # `bot_decision`, so it sees the pack change directly.
    # ATTRIBUTION PROVEN, not assumed: with the two pack files reverted and
    # every other edit in this branch left in place, this test passes untouched
    # at the old counts; restoring the packs reproduces the new ones. No
    # limper-belt content changed and every _WANT_* coverage shape still fires
    # (verified: BB x1 47, BB x2 20, BB x3 6) — stream displacement, not a
    # coverage regression.
    # RE-RECORDED for S3-T5 (improvement slice 3, ticket 5 — the late-street
    # bet lever, 2026-08-22, slice-authorized): the LAG authors the new
    # `late_street_bet` pack field at 1.0, so it bets unopened turns and rivers
    # more often on both the value and the bluff side, the shared organic rng
    # stream displaces, and every pair moves (old counts: UTG2 x1 100, LJ x1
    # 110, HJ x1 115, CO x1 100, CO x2 22, SB x1 61, SB x2 34, BTN x1 87,
    # BTN x2 25). One persona moves, not three: the nit and the tag were dialled
    # in an earlier round of this ticket and did not clear its ship rule.
    # This belt runs PRODUCTION `bot_decision`, so it sees the pack change
    # directly.
    # ATTRIBUTION PROVEN, not assumed: with the LAG pack file reverted and every
    # other edit in this branch left in place, this test passes untouched at the
    # old counts; restoring the pack reproduces the new ones. No limper-belt
    # content changed and every _WANT_* coverage shape still fires (verified:
    # BB x1 49, BB x2 21, BB x3 4) — stream displacement, not a coverage
    # regression.
    ("UTG2", 1): 91, ("LJ", 1): 104, ("HJ", 1): 127, ("CO", 1): 90,
    ("CO", 2): 33, ("SB", 1): 70, ("SB", 2): 31, ("BTN", 1): 85,
    ("BTN", 2): 39,
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

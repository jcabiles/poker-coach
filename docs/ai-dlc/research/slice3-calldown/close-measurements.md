# Slice-3 (calldown) close packet — before/after measurement record

**Bottom line.** Across the whole slice-3 chain (S3-T1 through S3-T5, tickets that
retuned how often the nit, TAG and LAG bots call down to showdown), went-to-showdown
(WTSD — the share of hands a persona takes to a showdown, out of the hands where it
saw the flop) fell for five of six personas on both measuring instruments. The
TAG fell the most on both (band harness −4.01pp, 50,000-hand export −4.3pp); the
nit fell on both too, but by much less than the single S3-T2 ticket shipped in
isolation (−1.80pp there vs −0.44pp here), because the one later ticket that
changed live behaviour — S3-T5, which gave the LAG its late-street bet lever
(S3-T3's lever was withdrawn and shipped byte-identical; S3-T4 changed no
engine behaviour) — alters what every other seat faces, and that echoes back
onto the nit's dealt hands through table composition — the same coupling
mechanism the T2 and T5 reports both describe. The maniac, whose
pack was never edited in this chain, ticked slightly UP on the band harness
(+0.33pp) for the same reason. Nothing here contradicts the per-ticket reports;
it is the cumulative, chain-wide reading they didn't individually report.

## Instruments, tips, and pins

- **Instrument 1 — band harness.** `_persona_stats()` in
  `backend/tests/test_personas_postflop.py`, called directly (not through
  pytest) at the pinned seed `20260710` and the pinned sample size `_WTSD_ORDER_N
  = 4000`. This is the ticket-gating instrument for the whole slice.
- **Instrument 2 — 50,000-hand export.** `backend/tools/export_analytics.py`
  on the ratified nine-seat lineup
  `tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac`, seed
  `20260817`, read through
  `docs/ai-dlc/research/slice2-invest-then-fold/diagnose.py`'s "collision with
  slice 3" section. Diagnostic, not gating.
- **Baseline tip:** `d351150` (`d351150bfff8bc3d9d2bd4b9d9fb687c9b1c9de9`),
  pre-chain, measured read-only in the pre-existing worktree
  `/private/tmp/claude-501/pc-baseline-worktree/wt`. This is the exact commit
  `docs/ai-dlc/research/slice3-calldown/baseline-2026-08-21.md` measured, and
  every number below reproduces that report's table exactly (§"Sanity check"),
  which confirms the correct engine was measured (see the venv-trap warning in
  the ticket brief).
- **Tip:** `0561e8f` (`0561e8fd45066d6f92b3004fc9346e9dac7c1310`), current
  `main`, S3-T1 through S3-T5 merged. Measured read-only in the main checkout
  `/Users/johncabiles/Documents/Github/poker-coach`; only unrelated files
  (`.claude/agents/persona-realism-theory-reviewer.md`,
  `.claude/settings.json`, one new untracked plan doc) were dirty in that tree
  and none of them touch the domain/content code being measured.
- **Venv trap:** the only Python venv lives in the main checkout's
  `backend/.venv`. Baseline measurements below ran that binary with
  `PYTHONPATH=.` pointed at the *worktree's* `backend/` directory (never the
  worktree's own venv, which doesn't exist).

## 1. Summary table — went-to-showdown, both instruments

| persona | harness baseline | harness tip | harness Δ | export baseline | export tip | export Δ |
|---|---|---|---|---|---|---|
| nit | 0.6356 | 0.6312 | **−0.44pp** | 59.5% | 57.1% | **−2.4pp** |
| tag | 0.6133 | 0.5732 | **−4.01pp** | 54.2% | 49.9% | **−4.3pp** |
| lag | 0.5728 | 0.5639 | **−0.89pp** | 51.9% | 50.9% | **−1.0pp** |
| maniac | 0.5960 | 0.5993 | **+0.33pp** | 53.1% | 52.5% | −0.6pp |
| calling_station | 0.7105 | 0.7022 | **−0.83pp** | 66.4% | 66.2% | −0.2pp |
| passive_fish | 0.5403 | 0.5262 | **−1.41pp** | 49.1% | 47.8% | **−1.3pp** |
| **pooled** | **0.6180** | **0.6082** | **−0.98pp** | **54.9%** | **53.4%** | **−1.5pp** |

Pooled harness rows are the per-persona `showdown_hands`-weighted mean
(`Σ wtsd_i · saw_flop_n_i / Σ saw_flop_n_i`), computed from the same
`saw_flop_n` the harness reports per row (see §2 raw tables). This is the
same method `baseline-2026-08-21.md` used to report its own pooled figure
(61.81%, from 4-decimal per-persona inputs not shown in this packet); this
run's 4-decimal inputs (§2a) recompute to 0.6180, a one-hundredth-of-a-point
rounding difference from re-deriving the pooled figure off 2-decimal-percent
inputs rather than a discrepancy in the underlying measurement.

**Direction agrees on both instruments for five of six personas.** The maniac
is the one persona whose sign disagrees between instruments (+0.33pp harness,
−0.6pp export); both readings are small relative to the personas the chain
actually tunes (nit, TAG, LAG), and the maniac's pack was never edited across
S3-T1–T5.

## 2. Raw per-instrument tables and commands

### 2a. Band harness — baseline (`d351150`)

Command (run from the baseline worktree's `backend/`, using the main
checkout's venv per the venv trap above):

```
cd /private/tmp/claude-501/pc-baseline-worktree/wt/backend && \
PYTHONPATH=. /Users/johncabiles/Documents/Github/poker-coach/backend/.venv/bin/python \
  <scratchpad>/wtsd_band_harness.py .
```

`<scratchpad>/wtsd_band_harness.py` is a standalone script (not committed)
that loads `backend/tests/test_personas_postflop.py` by path with
`importlib.util` (the test dir has no `__init__.py`, so it can't be
imported as a package) and calls the module's own private `_persona_stats(packs,
persona, n)` for each of the six personas, with `packs = load_persona_packs()`
and `n = mod._WTSD_ORDER_N`. At `d351150` the function predates the
`_BAND_SEED` module constant (seed `20260710` was still inlined directly in
`_persona_stats`) and returns a 6-tuple, not the 8-tuple S3-T5 later added
(`never_faced_wager`, `checked_down`); the script detects tuple length and
handles both. **Exit code 0.**

```
_BAND_SEED=20260710 (inline, pre-_BAND_SEED-constant) _WTSD_ORDER_N=4000
persona                   af       ftc      wtsd  saw_flop_n   never_faced  checked_down
calling_station       0.3162    0.1884    0.7105        5499n/a (pre-S3-T5)n/a (pre-S3-T5)
lag                   2.6432    0.3381    0.5728        2437n/a (pre-S3-T5)n/a (pre-S3-T5)
maniac                3.2097    0.3182    0.5960        3998n/a (pre-S3-T5)n/a (pre-S3-T5)
nit                   1.4141    0.3586    0.6356         955n/a (pre-S3-T5)n/a (pre-S3-T5)
passive_fish          0.8706    0.4386    0.5403        4107n/a (pre-S3-T5)n/a (pre-S3-T5)
tag                   2.2399    0.2933    0.6133        1593n/a (pre-S3-T5)n/a (pre-S3-T5)
```

**Sanity check.** This reproduces `baseline-2026-08-21.md`'s own table
(nit 63.56%/n=955, tag 61.33%/n=1593, lag 57.28%/n=2437, calling_station
71.05%/n=5499, maniac 59.60%/n=3998, passive_fish 54.03%/n=4107, pooled
61.81%/n=18589) exactly, cell for cell — confirming the baseline worktree was
measured with the correct (`d351150`) engine and not silently against the
main checkout's tip engine.

### 2b. Band harness — tip (`0561e8f`)

Command (run from the main checkout's `backend/`):

```
cd /Users/johncabiles/Documents/Github/poker-coach/backend && \
PYTHONPATH=. .venv/bin/python <scratchpad>/wtsd_band_harness.py .
```

**Exit code 0.**

```
_BAND_SEED=20260710 _WTSD_ORDER_N=4000
persona                   af       ftc      wtsd  saw_flop_n   never_faced  checked_down
calling_station       0.3106    0.1788    0.7022        5501        0.2420        0.1701
lag                   2.6821    0.3376    0.5639        2378        0.4101        0.1365
maniac                3.1398    0.2987    0.5993        3933        0.4103        0.1646
nit                   1.5425    0.4152    0.6312         995        0.4920        0.3025
passive_fish          0.9170    0.4337    0.5262        4183        0.3557        0.2299
tag                   2.5262    0.3601    0.5732        1640        0.4628        0.1798
```

**Sanity check.** This reproduces `t5-report.md` §4's ordering-leg readings
exactly (calling_station 0.7022, lag 0.5639, tag 0.5732, maniac 0.5993,
passive_fish 0.5262) — confirming the tip engine matches the S3-T5 report's
own measurement at the same commit.

### 2c. 50,000-hand export — baseline (`d351150`)

Export command (run from the baseline worktree's `backend/`, main checkout's
venv):

```
cd /private/tmp/claude-501/pc-baseline-worktree/wt/backend && \
PYTHONPATH=. /Users/johncabiles/Documents/Github/poker-coach/backend/.venv/bin/python \
  -m tools.export_analytics --hands 50000 --seed 20260817 \
  --lineup tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac \
  --out <scratchpad>/sim50k_baseline --skip-contract-test
```

`_SUCCESS` manifest confirms `git_sha: d351150bfff8bc3d9d2bd4b9d9fb687c9b1c9de9`.
**Exit code 0.** Row counts: 50,000 hands, 450,000 seat_outcomes, 883,812
decisions.

Diagnosis command:

```
cd /Users/johncabiles/Documents/Github/poker-coach/backend && \
PYTHONPATH=. .venv/bin/python \
  docs/ai-dlc/research/slice2-invest-then-fold/diagnose.py \
  <scratchpad>/sim50k_baseline 50000
```

**Exit code 0.** "collision with slice 3" section:

```
persona            saw flop    WTSD  river hard-zero folds  WTSD if they called
maniac                18282   53.1%                    736                57.1%
calling_station       22409   66.4%                   1944                75.1%
passive_fish          33091   49.1%                   1742                54.3%
lag                    9579   51.9%                    442                56.6%
tag                   20788   54.2%                    892                58.5%
nit                    3486   59.5%                    154                63.9%
POOL                 107635   54.9%                   5910                60.4%
```

**Sanity check.** Matches `baseline-2026-08-21.md`'s §1 export column exactly
(nit 59.5%, tag 54.2%, lag 51.9%, calling_station 66.4%, maniac 53.1%,
passive_fish 49.1%, pool 54.9%).

### 2d. 50,000-hand export — tip (`0561e8f`)

Export command (run from the main checkout's `backend/`):

```
cd /Users/johncabiles/Documents/Github/poker-coach/backend && \
PYTHONPATH=. .venv/bin/python -m tools.export_analytics \
  --hands 50000 --seed 20260817 \
  --lineup tag,tag,calling_station,tag,passive_fish,lag,passive_fish,nit,maniac \
  --out <scratchpad>/sim50k_tip --skip-contract-test
```

`_SUCCESS` manifest confirms `git_sha: 0561e8fd45066d6f92b3004fc9346e9dac7c1310`.
**Exit code 0.** Row counts: 50,000 hands, 450,000 seat_outcomes, 880,281
decisions. (This command needed a background run — it exceeded the 2-minute
foreground shell timeout at both tips and completed in the background instead;
noted here because it is a departure from a single synchronous invocation, not
because anything about the run itself is unusual.)

Diagnosis command: same form as 2c, pointed at `sim50k_tip`. **Exit code 0.**
"collision with slice 3" section:

```
persona            saw flop    WTSD  river hard-zero folds  WTSD if they called
maniac                18318   52.5%                    651                56.1%
calling_station       22138   66.2%                   1939                75.0%
passive_fish          32920   47.8%                   1654                52.8%
lag                    9711   50.9%                    420                55.2%
tag                   20826   49.9%                    869                54.1%
nit                    3461   57.1%                    126                60.8%
POOL                 107374   53.4%                   5659                58.7%
```

**Sanity check.** Matches `t5-report.md` §2's export table exactly (lag
0.5088→50.9% rounds consistently, nit 0.5712→57.1%, tag 0.4988→49.9%, maniac
0.5252→52.5%, calling_station 0.6622→66.2%, passive_fish 0.4779→47.8%, pooled
0.5338→53.4%).

## 3. Anomalies

**The nit's chain-wide fall (−0.44pp harness, −2.4pp export) is much smaller
than the −1.80pp the S3-T2 report shipped for it in isolation on the harness.**
This is not a discrepancy in either report — S3-T2's own before/after was
measured with only the nit's and TAG's packs changed and nothing else; this
close packet measures the whole chain (S3-T1 through S3-T5). The only ticket
after T2 that changed live behaviour is S3-T5, which authored the LAG's
late-street bet lever (S3-T3's lever was withdrawn, leaving the engine
byte-identical; S3-T4 changed no engine behaviour), and per the composition
mechanism both the T2 and T5 reports describe (the calling dial scales the
whole continue side through the `rscale` coupling, so one persona's changed
betting alters how much aggression every OTHER seat at the table meets),
that later change partially echoes back onto the nit's dealt hands even
though its own pack was untouched after T2. The TAG shows the
same pattern in reverse direction of magnitude but same sign: its chain-wide
fall (−4.01pp harness) is smaller than the single-ticket T2 fall (−6.15pp)
it shipped, for the identical reason.

**The maniac — a persona whose pack was never edited anywhere in S3-T1
through S3-T5 — moves on both instruments anyway, and the two instruments
disagree on its sign** (+0.33pp harness, −0.6pp export). Both magnitudes are
small and this is the expected, previously-documented composition effect
(T2 report §3: "two personas whose packs were not touched moved anyway"), not
a new finding; it is noted here because a reader comparing only one instrument
could otherwise mistake it for a discrepancy between them.

No command in this packet failed or returned a non-zero exit code; no number
above is a substitute for a failed measurement.

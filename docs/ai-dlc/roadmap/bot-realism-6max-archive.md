# Bot Realism at 6-max — archived slices

Bottom line: these slices are finished. They moved out of `bot-realism-6max.md` on 2026-10-03 to keep the live roadmap under its size cap, and are kept verbatim for the record.

- [x] **M1 — Measure the 6-max baseline.** ICE 9·8·6.
  - **Problem:** every number we have comes from 200 hands, which is too few per bot and per seat
    to tune against.
  - **Outcome link:** it provides the stats half of the north star, and it checks that the
    simulator can stand in for the owner's play before any tuning relies on it.
  - **What it delivers:**
    - Teach the bot-vs-bot simulator (`backend/tools/export_analytics.py`, 9-max only today) to
      run the live 6-max lineup: nit, LAG, TAG, TAG and station, with a TAG as the stand-in for
      the hero seat.
    - Run 5,000 or more hands at the existing 95–105bb starting spread. Deep-stack effects belong
      to the deep-stack lane, not here.
    - Source the real 6-max ranges each stat is judged against, cited with the existing
      `(format, pool, source)` provenance rule. Reuse `docs/ai-dlc/research/rfi-seat-provenance.md`
      where it applies. Today's persona bands are 9-max.
    - Produce a per-bot stats table set against those ranges.
  - **Pass/fail:** the report exists at `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md`
    and does all of the following:
    - gives every stat above with its sample size and a 95% confidence interval, per bot;
    - cites a real 6-max range for each stat, or marks the stat unsourced;
    - reports the fidelity check below.
  - **Appetite:** a few days.
  - **No-gos:**
    - no change to any settings file;
    - no change to bot behaviour;
    - 9-max export output stays byte-identical (the existing default-path regression tests pass
      unchanged).
  - **Riskiest assumption:** simulated bot-vs-bot hands reproduce what the owner sees at the
    table.
  - **Cheapest test** (fixed before the run):
    - Compare each bot's VPIP, PFR and flop c-bet rate between the simulation and the 200 real
      hands in session `4b35736f`. That is up to 15 comparisons.
    - **Narrowed at spec time (owner ruling, 2026-09-26):** flop c-bet had too few real chances
      for most bots, so the pre-registered check is VPIP and PFR only, 10 comparisons. The one
      c-bet comparison that did reach 30 chances, the LAG's, would also have passed (real 50.0%,
      pass range 28.2–69.2%).
    - **A comparison is eligible only if the real hands gave it 30 or more chances** (owner ruling,
      2026-09-25).
    - **Fewer than 8 eligible comparisons: the result is "can't tell yet".** Tuning does not start.
      The owner plays more Challenge hands, up to the 500–1,000 already offered, and the check
      re-runs on the combined sessions.
    - **Passes** if at most one eligible real rate falls outside the simulated 95% confidence
      interval widened by the real sample's own interval (one miss is a pass: owner ruling,
      2026-09-26). **Fails** if two or more eligible comparisons fall outside it. On a failure M1 stops and reports, and nothing downstream starts.
    - Known limit: the owner, not a stand-in, sat in the real hero seat.
  - **Assumption status:** tested 2026-09-26 — held for pre-flop play (VPIP/PFR, 10 of 10 eligible, 0 misses); post-flop untested against real play.
  - **Report:** `docs/ai-dlc/research/bot-realism-6max/m1-baseline.md`.

- [x] **M1b — Let bot settings differ by table size.** ICE 6·8·7. Owner ruled it in, 2026-09-25.
  Can run alongside M1; M2 needs both. Built 2026-09-27 on `feat/m1b-table-size-settings`:
  - **Where values go:** a bot's 6-max values live in `content/personas/six_max/<bot>.json`, holding
    only what differs.
  - **What an override can replace:** all preflop rules for a situation, and any single dial (`null`
    deletes a dial).
  - **Where it is read:** the live table, the villain-range view and the M1 tool at 6 seats. 9-max
    never reads it.
  - **Specs:** `../specs/m1b-table-size-settings.md` and `../ledger/m1b-table-size-settings.md`.
  - **What it delivers:** a bot's settings can carry 6-max-specific values, while 9-max keeps
    reading exactly what it reads today.
  - **Pass/fail:**
    - 9-max bot decisions are byte-identical on a fixed seed set;
    - one 6-max override is proved live by a test.
  - **No-gos:** no settings values change in this slice.
  - **Riskiest assumption:** an override layer can be added without making settings hard to
    reason about.
  - **Cheapest test:** the byte-identical 9-max check.
  - **Assumption status:** held, 2026-09-27. Both pass/fail checks pass:
    - A golden fingerprint of every bot decision over 360 seeded hands, pinned before any code
      changed, is unchanged at 9-max and at 6-max.
    - A test-only override is proved live through the loader, played hands, both live-table call
      sites and the villain-range view. 9-max sessions are proved to ignore it.
    - "Easy to reason about" is judged by these facts:
      - one small file per bot holds only what differs;
      - one merge function applies it;
      - every settings safety check also runs on the merged 6-max result.
      - The real test comes when M2 authors the first override.

- [x] **R1 — Research how strategy changes with stack depth.** ICE 7·8·8. Runs in parallel with
  M1.
  - **Problem:** the bots are tuned for about 100bb, but live stacks now run from 50bb to 455bb.
    No committed source says how real players change strategy as stacks deepen.
  - **What it delivers:** a `/research` pass on expert and academic material:
    - how pre-flop ranges, commitment thresholds (stack-to-pot ratio, SPR) and post-flop
      aggression change from 100bb to 200bb and beyond;
    - any published studies, white papers or population metrics we can reuse, each dated and
      cited.
  - **Pass/fail:** `docs/research/deep-stack-strategy.md` exists and does all of the following:
    - opens with a plain summary;
    - gives numbers that the deep-stack lane can turn into settings, with sources;
    - labels every figure as sourced or approximate.
  - **Appetite:** one research pass.
  - **No-gos:** no solver tables (a global no-go). Sourced heuristics only.
  - **Riskiest assumption:** usable, citable numbers exist for deep-stack adjustments.
  - **Cheapest test:** the research itself.
  - **Built (2026-10-01):** report at `docs/research/deep-stack-strategy.md`; findings ledger
    `ledger/r1-deep-stack-research.md`. Result:
    - one pair stops being an automatic stack-off between SPR 3 and 6 (three sources); the
      two-pair (about 5) and set (about 10) cutoffs rest on one author;
    - opening, 3-bet and 4-bet changes with depth are direction-only, with no percentages;
    - no public population data by depth, and no source above 300bb.
  - **Assumption status:** partly held, 2026-10-01. Citable numbers exist for commitment
    thresholds and set-mining odds. They do not exist for opening, 3-bet, c-bet or barrel rates by
    depth, or for how real players behave by depth, so the deep-stack lane has to measure its own.


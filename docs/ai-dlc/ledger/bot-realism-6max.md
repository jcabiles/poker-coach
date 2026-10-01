# Findings — bot realism at 6-max
scheme: 2026-09-26

## Bottom line
- This is the roadmap's ledger (`../roadmap/bot-realism-6max.md`), the file the merge guard reads
  for the active initiative. It starts with slice M2 (retune the LAG at 6-max, plus the
  board-straight fix); M1 and M1b kept their own ledgers.
- Spec review, round 1: 26 findings from two blind reviewers. All are fixed in spec rev 2 or
  rejected with a reason; none is open. Three needed the project owner's ruling, given 2026-09-30
  and recorded in the spec.

## Passes
- **2026-09-30, spec round 1:** Claude `refuter` (Opus) and Codex `gpt-6-sol` (high), both blind,
  run in parallel. Checklist: goal coverage against the roadmap and the owner's requirements,
  contract breaks, pass/fail soundness, missed edge cases. Reports:
  `../reviews/m2-lag-6max-retune-r1-refuter.md`, `../reviews/m2-lag-6max-retune-r1-sol.md`.
  The two agreed on the main blocker (the shared random stream). They disagreed on one severity
  (C2 blocker vs R13 minor); adjudicated minor, since the fix is the same.
- whole-branch review (2026-10-01): ran on branch head ee93bd7. Gate first: `make check` green, test-weakening
  check clean against the merge base. Reviewers, in one message: a fresh Claude `refuter` (Opus, mode whole-branch),
  a fresh Claude `refuter` (Sonnet, mode standards) and Codex `gpt-6-sol` (high; both lenses). Reports:
  `../reviews/m2-lag-6max-retune-branch-refuter-interaction.md`,
  `../reviews/m2-lag-6max-retune-branch-refuter-standards.md` and `../reviews/m2-lag-6max-retune-branch-sol.md`
  (Codex, raw). Every finding is ledgered in the M2 whole-branch rows below.

## M2 spec, round 1

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| R1 | spec §4, §7 item 5 | blocker | The 9-max attribution check fails by construction: the golden harness passes one shared random stream into every bot decision, so one changed hand shifts every later hand. | `test_bot_decisions_golden.py:55-59`; `export_analytics.py:258`; in-memory run: 85 of 360 hands changed, only hand 275 genuine. | fixed: rev 2 §4 uses a matched replay (each hand its own stream, 4,000 hands). | Matched replay reports 0 unattributed hands. |
| C1 | spec §4, §7 | blocker | Same defect as R1; also the check can pass vacuously if no hand exposes the fix. | `test_bot_decisions_golden.py:55-60`. | fixed: rev 2 §4 matched replay on 4,000 hands and reports the count of changed hands. | Report shows changed hands > 0 and 0 unattributed. |
| R2 | spec §6 | major | "Commit 1 → 2 is the fix's share" at 6-max is mostly reshuffled hands: 4,983 of 6,000 hands differ and pre-flop stats move. | `sixmax_baseline.py:70-76`; in-memory run. | fixed: rev 2 §6 measures each part's share on the matched replay; commit-level deltas labelled noise-dominated. | Report's share table comes from the matched replay. |
| R3 | spec §7 item 4 | major | The median raise multiple is already 3.00×, inside the band, so the check cannot fail; the complaint is the tail (22.4% of raises ≥ 4×). | Baseline: n=272, median 3.00×, p90 4.77×. | fixed: owner ruling 2026-09-30 — add a tail target (share ≥ 4× falls to ≤ 10%, approximate); rev 2 §7 item 4. | Commit-3 run reports share ≥ 4× ≤ 10%. |
| R4 | spec §5 | major | Setting `raise_pct` equal to the targets breaks rr_emit's annotation contract (±0.005 of the emitted width); HJ 23, BTN 50, SB 43 are unreachable. | `rr_emit.py:19-22`; `test_rr_emit.py:427-436`. | fixed: rev 2 §5 sets `raise_pct` to the emitted width, records targets in `_doc`, extends the annotation and monotone tests. | Extended annotation test passes on the 6-max spec. |
| C4 | spec §5, §7 | major | SB instructions conflict: annotate 43 yet calibrate measured RFI to 43 despite a ~5-point authored-to-measured gap. | `m1-baseline.md:50`. | fixed: rev 2 §5 — the target is the measured RFI; the authored SB width may differ. | Commit-3 SB interval contains 43. |
| R5 | spec §7 items 1–2 | major | Hitting the opening targets projects PFR ≈ 19.4% and VPIP ≈ 24.7%, at the floors of 20 and 24. | Projection from `m1-baseline.md:44-50`. | fixed: owner ruling 2026-09-30 — openings win; a VPIP/PFR miss is reported as a known gap and does not block the PR (rev 2 §7). | Report states both values and the ruling. |
| C5 | spec §7 | major | Same projection as R5; also, interval overlap can call a below-floor rate "inside". | `m1-baseline.md:44-50`. | fixed: covered by the R5 ruling; rev 2 §7 reports the point estimate beside the overlap verdict. | Report shows point estimate and interval. |
| R6 | goal coverage (separation guard) | major | The spec never carries the separation guard, and the targets make the LAG open fewer hands than the unchanged TAG from LJ and HJ. | TAG RFI LJ 28.6, HJ 29.9 (`m1-baseline.md:60-62`). | fixed: owner ruling 2026-09-30 — accept the temporary inversion; rev 2 adds a LAG-vs-TAG table and puts type identification in the post-merge verdict record. | Report carries the table; PR "Not in this PR" names the verdict record. |
| C8 | goal coverage (separation guard) | major | The post-merge verdict never records whether the owner can still name each bot's type. | Roadmap north star. | fixed: rev 2 §7 "Not judged here" and §6. | As R6. |
| R7 | spec §5, §8 | major | The flat sizing block also sizes 419 LAG leads, probes and stabs, not only its 272 raises. | `personas_postflop.py:899-904`; `sizing.py:146-147`. | fixed: owner ruling 2026-09-30 — accept smaller leads; rev 2 §5 and §8 disclose it and §3 adds a non-aggressor bet-size stat. | Report shows non-aggressor bet size before and after. |
| C6 | spec §7 | major | The approximate-band checks have no minimum sample: Wilson is [0,1] at zero chances and a median of one raise passes. | `table_stats.py:182-186`. | fixed: rev 2 §7 — at least 300 faced bets and 100 raises, else inconclusive, which counts as a fail. | Report states the counts. |
| C7 | spec §4, §7 | major | The 9-max gate checks only action fingerprints, while the roadmap requires byte-identical output; exported `hand_class_bucket` values are unchecked. | Roadmap pass/fail; `export_analytics.py:251-257`. | fixed: rev 2 §4 — the matched replay also compares each hand's export rows; changed rows must lie in attributed hands. | Matched replay reports 0 unattributed export rows. |
| C3 | spec §5 | major | The override must cover BB; the spec named only the five measured seats, and the rr_emit command lacked its spec path. | `rr_emit.py:178-180,286-292`; `test_persona_pack_invariants.py:293-341`. | fixed: rev 2 §5 — seats LJ, HJ, CO, BTN, SB, BB; full command given. | 6-max coverage test passes. |
| C9 | goal coverage (supporting check) | minor | The roadmap's supporting check names c-bet and WTSD, but no LAG range is sourced for either. | `m1-baseline.md:51-52,136-138`. | fixed: rev 2 §7 reports both as unsourced and outstanding; the report may not claim the full supporting check passed. | Report wording. |
| C2 | spec §2, §5, §9 | minor | The spec promised three commits but scheduled four, and the sources section landed with the tuned values. Codex rated this blocker; adjudicated minor because the slice goal (fix in its own commit) is met either way. | Spec rev 1 §1, §9. | fixed: rev 2 §2 — three build commits; sources and frozen targets land in commit 1. | `git log` shows the three build commits in order. |
| R13 | spec §1, §5, §9 | minor | Same as C2; the target freeze left no trace in history. | Spec rev 1. | fixed: as C2. | As C2. |
| R8 | spec §5 | minor | Calibrating SB on the judged seed fits noise (~185 chances). | Seeds 1–5: SB 50.5% vs authored 46.43%. | fixed: rev 2 §5 — calibrate on pooled seeds 1–5, judge on seed 20260926. | Report states calibration seeds. |
| R9 | spec §3 | minor | `stats_for` returns float sums through a 2-tuple with four callers; it cannot carry a median. | `table_stats.py:196-210`. | fixed: rev 2 §3 — a separate `raise_multiples` function; `stats_for` and its callers unchanged. | Callers untouched in the diff. |
| R10 | spec §7 item 3 | minor | A sourced raise rate is likely a different statistic (raise c-bet, check-raise). | `table_stats.py:298-301`. | fixed: rev 2 §5 — a source counts only if its definition matches; otherwise flop-only or approximate. | Sources section states each definition. |
| R11 | spec §5 | minor | BB omitted; the nine-seat clause is moot and would break the monotone test. | `rr_emit.py:180`. | fixed: as C3; `monotone_seats` LJ through BTN, no UTG seats. | Extended monotone test passes. |
| R12 | spec header | minor | The named ledger did not exist and breaks the per-slice ledger naming. | `docs/ai-dlc/ledger/`. | fixed: this file is created by the slice. Per-slice naming kept aside on purpose: `merge-guard.py:242` reads `ledger/<active>.md`, and `active` is `bot-realism-6max`. | This file exists on the branch. |
| R14 | goal coverage (riskiest assumption) | minor | The spec dropped the roadmap caveat that a pass does not prove settings alone suffice. | Roadmap M2 riskiest assumption. | fixed: rev 2 bottom line carries it. | Spec wording. |
| R15 | spec §4 | minor | 360 hands hold only one genuine fix hand. | R1 run. | fixed: matched replay uses 4,000 hands. | As R1. |
| R16 | spec §4 | minor | "Four-card boards (flop, turn)" is wrong; near-tie cases that still classify as monster go unnamed. | `equity.py:46-53`. | fixed: rev 2 §4 wording and known limits; the report names them. | Spec and report wording. |
| R17 | spec §4 | minor | The must-stay-monster tests do not exist yet; a board full house case is missing. | Contract map §D. | fixed: rev 2 §4 says "add", with the full-house pair. | Tests present in commit 2. |

## M2 build, wave 1 (stats and frozen targets)

Fan-in: one fresh Claude `refuter` (Sonnet), verdict PASS-WITH-ISSUES, no blocker or major. `make check`, the
test-weakening check (0 failing) and the byte-identical judged run were all confirmed independently. Review
of the three minor fixes: Tier 0 (tests and a doc label), deterministic checks green, no second reviewer.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| W1-1 | `test_sixmax_baseline.py` measure test | minor | The test asserted only bounds, so a swapped street key or a wrong pooled sum stayed green. | Refuter, by reading. | fixed: the test now recomputes the flop and pooled pairs from `stats_for` directly. | `make check` green. |
| W1-2 | `test_table_stats.py` | minor | No test for a bet into an empty pot, the skip branch of `non_aggressor_bet_fractions`. | Refuter, by reading. | fixed: test added. | `make check` green. |
| W1-3 | `m2-lag-retune.md` labels | minor | The 22% baseline and the 10-20% band carried only "APPROXIMATE"; S7 was missing from the VPIP/PFR union rows. | Refuter. | fixed: baseline labelled DERIVED, band basis stated, S7 added with unchanged ranges. | Report text. |
| W1-4 | report, S3 format | optional | The LAG page S3 never states its format, so item 1's opening targets rest on M1's 6-max inference. | Refuter. | accepted: stated in the report; the targets are M1's frozen figures. | n/a |
| W1-5 | report, S12 | optional | S12 (format unstated) is not in the LAG union rows. | Fix worker. | rejected: M1 lets S12 widen a range only beside a 6-max source and its values (28, 24) sit inside the ranges, so the ranges would not move. | n/a |

## M2 build, wave 2 (the board-made-hand fix)

Fan-in: one fresh Claude `refuter` (Opus, behavior-touching), verdict PASS, no blocker, major or minor
finding. Independently confirmed: a brute-force comparison of the rule over 609,729 hands (0 mismatches),
`make check` green, the mutation copy (rule removed: 5 new tests, both digests and three other pins fail;
old tests pass, so every re-pin is caused by the fix alone), `check_test_weakening.py` clean, and the 9-max
matched replay reproduced byte for byte (4,000 hands, 13 changed, 13 attributed, 161 of 161 export rows
attributed, 0 unattributed). The 6-max share dump was not re-dumped by the reviewer.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| W2-1 | `personas_postflop.py:123` | optional | The `len(board) == 5` check is redundant because `_best5` returns `None` on a four-card board; the four-card guard test cannot tell the check apart. | Refuter, `_best5` at :87-96. | rejected: the explicit check states spec §4's rule and costs nothing. | n/a |
| W2-2 | scratch near-tie labels | optional | The "(higher)" label in the scratch near-tie script is misleading for a low flush card. | Refuter. | accepted: the report (T5) words that case with the spec's "low flush card" wording; classification is unchanged. | Report wording in T5. |
| W2-3 | design (spec §4) | optional | An unbeatable board-made chop, such as a royal flush on the board, is now a bluff-catcher and can fold to a bet. | Refuter; the one raise-to-fold hand (9-max #3210) was a correct fold to a higher straight. | accepted: the project owner chose the bluff-catcher class (2026-09-30). | n/a |
| W2-4 | ticket T2 owned files | minor | Two 9-max pins outside T2's owned list (`test_buyin_spread.py`, `test_limper_coverage_belt.py`) failed on the fix and were re-pinned. | Maker report; refuter mutation copy. | fixed: spec §4 allows it; the ticket's owned-files line now names both files. | Ticket text. |

## M2 build, wave 3 (the LAG's 6-max settings)

Fan-in: one fresh Claude `refuter` (Opus, behavior-touching), verdict PASS-WITH-ISSUES on the work, no blocker
or major issue. Independently confirmed: scope (two new content files, `test_rr_emit.py`, the 6-max digest line
only; the 9-max digest line has 0 diff), the override merges as written, the curve spec emits exactly the pasted
nodes, the new drift, `emits`, annotation and monotone tests fail when broken (throwaway-worktree mutations),
calibration reproduced on seeds 1-5 with the final spec dated before the judged run, the judged run
byte-identical to the saved output, and `make check` green. The reviewer did not judge the CO ruling below.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| W3-1 | spec §7 item 1, LAG CO opening rate | major | The frozen check misses at one seat: CO measured 28.5% [25.2, 32.1] against the 33 target on the judged seed. LJ, HJ, BTN and SB pass. | Judged run (seed 20260926, 6,000 hands); held-out seeds 1-5 give CO 33.5% [31.8, 35.2] and seeds 6-10 (never used to tune) give 33.5% [31.9, 35.2], and every seat contains its target on seeds 6-10. The maker stopped rather than tune on the judged seed. | waived: project owner 2026-10-01 — a low draw on one seed, since two sets of untouched seeds put CO on target; the frozen check stays as written, the CO fail is reported with the held-out seeds beside it. | Report's §7 table shows the fail, the waiver and the held-out numbers. |
| W3-2 | report, LAG vs TAG | minor | On the judged seed the LAG also opens less than the TAG at CO (28.5 vs 32.7), and its PFR is below the TAG's (18.5 vs 19.9; pooled seeds 1-5: 19.4 vs 19.6). The project owner accepted the inversion only at LJ and HJ. | Refuter, judged run. | fixed: ticket T5's report states this in the LAG-vs-TAG table and the post-merge verdict record. | Report table. |
| W3-3 | provenance of the judged run | minor | The judged run's header names commit c333e5a because it ran on the uncommitted tree; spec §6 wants runs at commit 3. | Refuter. | fixed: the run is repeated twice on the committed head and compared byte for byte (header SHA aside) before the PR. | `cmp` result in the report. |
| W3-4 | `test_rr_emit.py` size | optional | The file grew from 555 to 604 lines; it was already over ~500. | Refuter. | accepted: spec §1 names this file for the tests. | n/a |
| W3-5 | 6-max tests | optional | No test pins the 6-max spec's seat list or the postflop values; `continue_ref` 2.0 to 1.9 leaves the 360-hand digest unchanged. | Refuter. | accepted: the spec does not require it, and the judged run checks the values. | n/a |

## M2 build, wave 4 (results report and bookkeeping)

Fan-in: one fresh Claude `refuter` (Sonnet; documentation audit, no behavior change), verdict PASS-WITH-ISSUES,
no blocker or major issue. Every sourced figure and every spec §7 verdict was re-derived from the saved outputs
and matched; the frozen-target text above `## Results` was unchanged apart from one added outcome paragraph;
the appendix script is byte-identical to the scratch original; the name and path greps were clean. The three
minor fixes were re-checked deterministically (diff of the report, grep), Tier 0, no second reviewer.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| W4-1 | report §5, matched-replay row | minor | The row sat under a "Commit 1 / Commit 3" header though its "before" is commit 2. | Refuter. | fixed: the row has its own "Commit 2 / Commit 3" table. | Report text. |
| W4-2 | report §1, provenance | minor | The commit-1 judged run's header names the spec-revision commit `1676ac1`, not `09d25b0`, and the report did not say why. | Refuter. | fixed: one explanatory sentence added. | Report text. |
| W4-3 | report §6 and ledger W3-1 | minor | "About 2.6 standard errors" had no saved source (the reviewer gets 2.4-2.5). | Refuter. | fixed: the phrase is removed from the report and from W3-1. | grep finds none. |
| W4-4 | report, item 6 command | optional | The command adds `-uall`, which the spec's command lacks; it is needed to list files inside new folders. | Refuter. | accepted: same result, clearer output. | n/a |
| W4-5 | report, scratch sources | optional | The report cites scratch output files that are not in the repo. | Refuter. | accepted: the spec keeps the matched-replay script out of the tree (§13); the report inlines it and states each figure's conditions. | n/a |

## M2 whole-branch review (2026-10-01, branch head ee93bd7)

Reviewers: Claude `refuter` Opus (interaction lens): FAIL on one major (W5-1), otherwise clean; Claude `refuter`
Sonnet (standards lens): PASS-WITH-ISSUES, minors only; Codex `gpt-6-sol` (both lenses): FAIL against the frozen
CO check (W5-2, already ruled) plus two standards majors (W5-3, W5-4). Reviewers were briefed blind to the
interview, the spec review and this ledger; the project owner's 2026-10-01 waiver therefore reached them only as
text in the report.

| ID | Target | Severity | Finding | Evidence | Status | Resolution test |
|----|--------|----------|---------|----------|--------|-----------------|
| W5-1 | report §4, §9; roadmap M2 entry | major | The separation write-up covers only the pre-flop overlap. After the retune the LAG's post-flop raising is below the unchanged TAG's and level with the nit's (raise when bet into: LAG 18.1%, TAG 23.6%, nit 18.2%; raises of 4x or more: LAG 5.9%, TAG 25.9%). | Opus re-ran the judged simulation; the figures are in the report's per-bot table. | waived: project owner 2026-10-01 — disclose it and open the PR; the 200-hand verdict after merge records whether each bot's type is still nameable, and the remedy is a second settings change to the LAG file. Disclosure added to the report and roadmap. | Report §4 and §9 state the post-flop overlap and the owner's acceptance. |
| W5-2 | spec §7 item 1 (CO) | major | The judged CO interval does not contain 33. | Codex; same fact as W3-1. | waived: project owner 2026-10-01 (see W3-1); the report keeps the frozen check marked FAIL, shows the held-out seeds beside it, and states the waiver. | As W3-1. |
| W5-3 | `personas_postflop.py:121` | major | The retained comment "monster even on paired boards" sits above the new exception and is stale. | Codex (engineering standards: no stale claim left in place "corrected" by a second comment). | fixed: the comment now reads "straight or better: monster unless the board makes it alone (below)". | Diff is comment-only; `make check` green. |
| W5-4 | `test_limper_coverage_belt.py` | major | The re-pin grew an already oversized file (590 to 598 lines) without flagging it. | Codex. | accepted: eight lines of re-pin text, flagged here and in the PR; splitting oversized files is out of scope (spec §13). | PR "Review focus" names it. |
| W5-5 | `postflop.py:271-274` | minor | The hero-side grader `_hand_category` still calls any straight or flush across hole plus board "strong", even when the board makes it alone, so it disagrees with the bot rule now. It feeds the river graders. | Opus. | accepted: latent (the river graders are not reached yet per the project's coverage notes) and the roadmap bars other engine changes; named in the PR as a follow-up. | PR "Not in this PR". |
| W5-6 | tests (several) | minor | A never-failing assertion (`n >= 0`); re-pin comments that re-list old digests and counts; two bare internal labels in test comments. | Sonnet standards review. | fixed: assertion deleted (WEAKENED-OK note: a length cannot be negative), comments trimmed to the constraint, labels replaced with plain words. | `check_test_weakening.py` 0 failing, 1 exempt (judged fine); `make check` green. |
| W5-7 | `lag.json` `_doc` | optional | Dropping the 1.0 size lowers the bluff weighting on the LAG's leads and raises when it is not the aggressor (about 1.022 to 0.954); the notes did not say so. | Opus. | fixed: one sentence added to the `_doc`. | File text. |
| W5-8 | `sixmax_baseline.py` summaries | minor | Possible primitive obsession: tuples and dicts mix, a key sniff tells them apart, one type hint reads `dict[str, float]` yet returns `{"n": 0}`. | Sonnet. | accepted: matches the surrounding tool code; mypy and tests pass; not worth a refactor in this slice. | n/a |
| W5-9 | `table_stats.py` | minor | The definition of a raise into a bet exists in `stats_for` and in `raise_multiples`. | Sonnet. | accepted: the spec keeps `stats_for` and its four callers unchanged (spec §3); the two are tested against each other by the measure test. | n/a |
| W5-10 | `test_rr_emit.py` | minor | The 6-max tests repeat the base LAG tests and the file grows from 555 to 604 lines. | Sonnet. | accepted: the spec names this file for these tests and mirrors the base block; flagged here and in the PR. | n/a |
| W5-11 | `sixmax_baseline.py:435` | optional | `POSTFLOP_STREETS` repeats a street tuple that `stats_for` writes inline. | Opus. | rejected: touching `stats_for` is out of scope (spec §3). | n/a |
| W5-12 | `personas_postflop.py` and its test file | minor | Pre-existing oversized files grow by a few lines. | Sonnet. | accepted: flagged here and in the PR; splitting is the cleanup project's. | PR "Review focus". |
| W5-13 | `escapes.md` | minor | The placeholder `PR #TBD` is committed. | Sonnet. | accepted: the number exists only once the PR does; a follow-up commit on the PR branch records it right after opening, before the project owner merges. | `escapes.md` carries the number. |
| W5-14 | report length | optional | The report is about 580 lines, mostly the inlined script. | Sonnet. | accepted: the spec requires the script inlined; the repo keeps per-slice research files. | n/a |
| W5-15 | requirements | minor | Reviewers listed the CO miss and the LAG-below-TAG opens at CO as requirements the branch does not carry. | Opus, Sonnet, Codex. | accepted: both are disclosed in the report and ruled by the project owner (W3-1, W3-2); the roadmap's 200-hand verdict and the c-bet and WTSD ranges are expressly outstanding. | n/a |

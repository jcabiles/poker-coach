# Refuter review — slice 3 (calldown) close, wave 5

**Verdict: PASS-WITH-FIXES.** Both docs-only diffs — poker-coach commit `bf1f3cf`
(chore/slice3-close-packet, note: the brief cited `71b2323`, an earlier version of the
same commit message that the worktree has since superseded with an added §4 section;
I reviewed the current HEAD, which is a strict superset of disclosure, not a regression)
and poker-analytics commit `7ea9fac` — check out almost entirely. Every number in
close-packet.md §2 reproduces close-measurements.md §1 exactly and recomputes correctly
from the raw per-persona tables; every reproduction close-measurements.md claims against
baseline-2026-08-21.md and t5-report.md is byte-for-byte accurate; the checklist §5
rewrite is a faithful, in fact MORE correct, implementation of estimand-contract.md §g.5
clause C and §g.3's k=4 unanimity rule than the text it replaced; owner-decisions.md's
citations of the ledger's Filed 1–15 all check out on close inspection, including the
"0.305 → 0.325" band re-centre figure which I initially misread as wrong and confirmed
correct; the roadmap rev-6 PR numbers (#211–#218) match `git log` exactly; and the
control-redesign ticket's closure claim (PR #184 implementing candidate 1, judged `bot`
at confidence-human 3 in the phase3-probe ledger) is corroborated by the actual commit
and code (`CONTROL_POLICY_DIGEST`, the skip-if-artifacts-absent test guard, and the
`snapshot.session_id != pins["session_id"]` dangling-pin logic that plausibly explains
close-packet.md §4's disclosed 2 machine-local `verify.sh` failures). Both diffs are
docs-only (`git diff --stat` confirms only `.md` files touched in both repos).

One real defect found, MEDIUM severity — a false "merged" status claim in `profile.md`'s
new Resume block, which is exactly the class of claim this review was asked to hunt for
(status stronger than the evidence). Two LOW notes are informational only.

---

## Issues

- severity: MED
  where: `docs/ai-dlc/profile.md` (Resume block, `merged:` line, added by this diff)
  problem: The line reads `merged: coach #211–#218 (chain) + the wave-5 docs PR(s);
    analytics: pointer-refresh PR.` At the time this commit exists, the wave-5 docs work
    (this very diff) is NOT merged — it is sitting in a worktree on branch
    `chore/slice3-close-packet`, unpushed and unreviewed, with no PR number assigned yet
    (contrast with `#211–#218`, which cite real numbers because they really are merged).
    The plan doc committed in the SAME diff (`plans/slice3-chain-autonomy.md` §"Merges")
    correctly uses future/procedural framing ("squash-merged after review"), and even the
    `position:` field two lines above the offending one correctly says "committed" rather
    than "merged" for this same work — so the document contradicts itself internally.
    A fresh session reading `profile.md` before the actual merge happens (e.g., if this
    review requires a fix loop, or the PR sits open overnight) would be told a false fact
    about repo state in the one field whose entire job is to be that fact.
  evidence: `git -C <poker-coach wt> log --oneline -3` on the worktree shows the docs
    commit (`bf1f3cf` / `71b2323`) has no merge into `origin/main` (`origin/main` is still
    at `0561e8f`, the pre-docs tip). `plans/slice3-chain-autonomy.md` line ~82: "Merges:
    one coach docs PR + one analytics docs PR, squash-merged after review per the
    2026-08-23 merge-authority answer" (future tense, not yet done).
  fix: Change `merged:` to `open:` (or similar) and name the actual PR branch/number once
    one exists, e.g. "coach #211–#218 (chain) merged; wave-5 docs PR pending review/merge
    on chore/slice3-close-packet; analytics pointer-refresh PR pending." Update again once
    the PRs actually merge — do not pre-write completed status for work still in review.

- severity: LOW
  where: `docs/ai-dlc/research/slice3-calldown/t2-fix-round-report.md:79` vs
    `docs/ai-dlc/research/slice3-calldown/baseline-2026-08-21.md:63` (both pre-existing,
    not touched by this diff)
  problem: T2's own report gives the nit's pre-T2 harness WTSD as 0.6353, while the
    baseline report (and close-measurements.md, which correctly reproduces the baseline)
    gives 0.6356 for the same quantity at the same pinned seed. The 0.03pp gap is almost
    certainly because T2's "before" was measured after S3-T1/T1b (which touched the
    strong-draw call split engine-wide) rather than at `d351150` itself, but neither
    document says so, and close-measurements.md doesn't reconcile the two numbers because
    it only cites T2's ordering-leg figures, not this one.
  evidence: t2-fix-round-report.md:58,79 ("nit | ... | −1.80pp (0.6353 → 0.6173)");
    baseline-2026-08-21.md:63 ("nit | 59.5% | 63.56% (n=955)").
  fix: Not blocking — outside this diff's scope, and immaterial at 0.03pp. Worth a
    one-line footnote in a future edit of either report so a reader doesn't have to
    re-derive the explanation themselves.

- severity: LOW
  where: `docs/ai-dlc/research/slice3-calldown/close-packet.md:5` ("every gate is green
    at the tip `0561e8f`") vs `close-packet.md:70-81` (§4, added in the current HEAD,
    not present in the `71b2323` version the brief named)
  problem: Not a contradiction — §4 discloses 2 `verify.sh` failures on this machine and
    explains convincingly (with code-level corroboration I independently verified) that
    they are machine-local DB/artifact pin issues, not code defects, and that a clean
    checkout is fully green. But "every gate is green" at the top, read in isolation
    without reaching §4, could be misread as "verify.sh is fully green everywhere,"
    which is not quite what's true on this machine right now.
  evidence: close-packet.md:44 clarifies "gate" means HARD bands/ordering legs/the
    five-seed de-robotization gate — a different claim than "verify.sh passed" — and §4
    is transparent about the 2 failures. This is a documentation-clarity nit, not a
    factual error.
  fix: Optional: add a one-clause pointer from the bottom-line sentence to §4 ("gates" as
    distinct from `verify.sh`'s two machine-local failures, see §4) so the two claims
    can't be read as conflicting without opening the document.

## Deterministic checks performed (all passed except the MED item above)

1. close-packet.md §2 vs close-measurements.md §1 — exact match, all 7 rows, both
   instruments, harness pooled figure independently recomputed from raw `saw_flop_n`
   weights (0.6180946→0.6180 baseline, 0.6081583→0.6082 tip) and matches.
2. close-measurements.md's baseline table vs `baseline-2026-08-21.md` — exact cell-for-cell
   match (harness and export, all 6 personas + pool); the "0.6180 vs 61.81% quoted"
   rounding note is independently verified correct (18589-weighted sum → 0.61804, not
   0.6181, a real one-hundredth-point rounding artifact as claimed).
   Tip harness numbers vs `t5-report.md` §4 ordering legs — exact match (calling_station
   0.7022, lag 0.5639, tag 0.5732, maniac 0.5993, passive_fish 0.5262). Tip export numbers
   vs `t5-report.md` §2 — exact match on all 7 rows.
3. Checklist §5 rewrite vs `poker-analytics:docs/methods/estimand-contract.md` §g.5 clause
   C (line 1658) and §g.3 (line 1587-1592) — faithful. Re-derived the logic from §d.2's
   actual text (line 498-519, "the batch is invalid UNLESS confidence<50 AND ≥4-of-5
   label bot") and confirmed the new checklist text's claim — that a single control miss
   at k=4 alone guarantees invalidation regardless of confidence — is the CORRECT reading
   of the OR-of-failure-modes logic, which is in fact more accurate than the removed text.
4. owner-decisions.md vs ledger Filed 1–15 — spot-checked every numeric claim (Filed 1's
   "16 points short"/"0.89" air fold, Filed 2's headroom table, Filed 5's SPR-flat claim
   and 10→0.3 range, Filed 8's 4.05pp/5.41pp shortfalls, Filed 9's +0.27 to +0.64 breach
   range, Filed 10's "~60×"/"7.5×" figures, Filed 11's 51.5%/31.7% nit figures, Filed 13's
   0.83–0.99 value-cell range, Filed 14's commutativity note, Filed 15's registration-vs-
   ship-list mismatch) — all match the ledger's own text exactly.
5. Roadmap rev-6 PR numbers vs `git log` — #211, #212, #213, #215, #216, #217, #218 all
   confirmed against real merge commits with matching ticket labels; `d351150` confirmed
   an ancestor of the chain's first commit (pre-chain baseline, as claimed).
6. Control-redesign ticket closure — PR #184 (`3ca8dad`) confirmed real; its commit
   message and 4-line checklist diff (only the `non_protocol` bullet) match
   finale-readiness.md's characterization exactly, including the literal "Full suite 1987
   passed, 3 skipped. ruff clean." quote. `candidate 1` in the ticket body is indeed "Rule-
   breaking scripted control (recommended candidate)," matching the closure note's
   description. `phase3-probe.md`'s probe table confirms confidence-human 3 (bot) for the
   rule-breaker and 62 (human) for both T1 and the human anchor, exactly as cited in
   finale-readiness.md. `CONTROL_POLICY_DIGEST` / `CONTROL_POLICY_DIGEST_HANDS = 12` /
   the `control_policy_digest` and `assert_control_policy_pinned` functions all exist at
   the line numbers finale-readiness.md cites (~155-163, 596-632).
7. Both diffs are docs-only: `git diff origin/main...HEAD --stat` in both worktrees shows
   only `.md` files touched (10 files / 883 insertions in poker-coach, 1 file / 25 lines
   in poker-analytics). No code, pack, test, or CSS file appears in either diff.

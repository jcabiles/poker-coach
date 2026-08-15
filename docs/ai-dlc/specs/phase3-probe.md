# Delta spec — judge-bias probe (phase-3 gate input)

**Goal (one line): a standalone dev harness that sends four known-quality 30-hand
stimuli to one LLM judge and reports whether the judge can distinguish anything —
gating the phase-3 ruling for ≤40¢.**

Governing contracts: `docs/ai-dlc/contracts/phase3-probe.md` (all ten bind).
Preregistered interpretation + budget: `phase3-decision-matrix.md` §3.
Protocol authority for agent execution: amendment draft §G (owner-authorized 2026-08-15
in-session; formal ratification pending with the rest of the package).

## Files to touch

- **NEW `backend/tools/detection_probe.py`** — the whole probe: stimulus builders,
  probe-deck assembly, judge invocation, verdict report.
- **NEW `backend/tools/probe_policies.py`** — the rule-breaking action policy
  (engine-legal, strategically illogical), same call shape as `bot_decision`.
  Lives in `tools/`, NOT `app/domain/` — experiment code stays out of the product
  domain core, and the purity test's hardcoded module list stays untouched (both
  reviewers flagged the domain placement; resolved by relocation).
- **NEW `backend/tests/test_detection_probe.py`** — stub-vendor end-to-end test +
  policy legality tests + fail-closed path-guard tests.
- `docs/ai-dlc/ledger/phase3-probe.md` — every paid call + verdict logged.

## Behavior

1. Build four 30-hand stimuli, all OFF-deck, focus seats within the human phase set:
   rule-breaker self-play · T1 control self-play (config-hash re-asserted) ·
   current-production-pack self-play · owner human window — non-selected VALID
   candidate, re-derived EXACTLY as: read the snapshot, assert
   `snapshot.session_id == unblinding pins.human.session_id`, filter rows to
   `hand_no <= pins.human.n_pinned`, then run `enumerate_windows` +
   `validate_human_window` and assert the resulting candidate table matches the
   deck's recorded candidates before choosing deterministically from
   valid-minus-selected. (`read_human_snapshot` has no pin parameter — the filter
   happens on its output.)
1b. **Fail-closed path guard before any write or API call:** resolve all paths
   (realpath); refuse if probe deck/output resolve inside `$S6_ROOT/deck` or
   `$S6_ROOT/judging`, or if deck == out. Covered by tests.
2. Render via the real renderer; run the real leak audit with a probe-specific
   forbidden-token list; refuse label-bearing keys in probe manifests.
3. Judge each stimulus once with `anthropic:claude-sonnet-5` via the existing adapter,
   pinned prompt verbatim; parse with the strict parser.
4. Write verdicts + raw responses under a NEW `detection-s6/probe/` output tree —
   never `deck/` or `judging/`.
5. `--vendor stub` mode runs the identical path with the free deterministic stub —
   the mandatory dry-run before any paid call.

## Out of scope

No changes to `detection_{corpus,render,judge}.py` behavior (imports only), no changes
to `run_s6_owner.sh`, no pack/content changes, no full-deck builds, no panel judging,
no analysis-module changes.

## Verify-by

`./scripts/verify.sh` green (incl. domain-purity test) · `ruff` clean · stub-mode probe
produces 4 rendered, leak-audited stimuli and 4 parsed stub verdicts deterministically ·
paid run: 4 calls ≤ ~4¢, verdicts logged in ledger, interpretation per matrix §3.

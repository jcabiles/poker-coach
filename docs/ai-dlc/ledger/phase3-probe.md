# Finding ledger — phase-3 paperwork + probe spec (dual review, 2026-08-15)

Reviewers: Claude refuter (verdict: pass, 5 findings) · Codex gpt-5.6-sol (8 findings).
Adjudicator: main session. Every finding listed with adjudicated status.

| # | Source | Severity | Finding (compressed) | Status |
|---|---|---|---|---|
| 1 | both | high/med | Rule-breaking policy in app/domain: purity test's hardcoded list gives false confidence (refuter); experiment code pollutes product domain (Sol) | ACCEPTED — resolved by relocation to `backend/tools/probe_policies.py`; purity test untouched |
| 2 | Sol | high | No fail-closed path validation protecting the live experiment tree | ACCEPTED — spec §1b + P3 tests |
| 3 | both | high/med | Pinned human-window re-derivation unspecified; `read_human_snapshot` drifts with the live DB | ACCEPTED — exact mechanism in spec (assert session_id, filter to pinned n_pinned, assert candidate-table match) |
| 4 | Sol | high | Control ladder unbalances judge-visible deck composition | ACCEPTED — deck keeps exactly ONE control (rule-breaker); T1 demoted to off-deck pre-screen diagnostic |
| 5 | Sol | high | Fresh-human-hands ecology conflicts with shipped-pack bot backgrounds | ACCEPTED — one matched ecology pinned (shipped packs everywhere except judged seat); fresh hands calibration-only, never deck |
| 6 | Sol | high | 4-slot pre-screen ownership ambiguous vs immutable finale launch | ACCEPTED — pre-screen calls ARE the finale's control checkpoints in the finale's new tree |
| 7 | Sol | high | Play-test design unpinned (N, randomization, thresholds) | ACCEPTED — N=8, seeded concealed assignment, FAIL at ≥7/8 correct or repeated tell ≥2 sessions |
| 8 | Sol | high | "≈ chance" undefined; floor claim conflicts with invalid-batch suppression | ACCEPTED — CI-includes-0.5 definition; floor made non-inferential, conditioned on batch validity |
| 9 | refuter | low | §A disclosure not bolded per §g convention | ACCEPTED — bolded |
| 10 | refuter | low | §A–D lack "*Modifies:* §d.x" citations | ACCEPTED — citations added |
| 11 | refuter | low | Matrix probe bucket 3 non-exhaustive ("e.g.") | ACCEPTED — restated as catch-all |

No findings rejected. Both reviewers independently confirmed the named code entry
points exist with the claimed shapes; refuter ran `./scripts/verify.sh` green twice.

## Probe episode log (append-only; every paid call recorded)

**Episode 1 — 2026-08-15, vendor anthropic:claude-sonnet-5, 5 paid calls
(1 preflight + 4 judged), est. ~$0.10 of the $0.40 cap. Stub dry-run passed
first (free). Output tree: `detection-s6/probe/` (path-guarded off the live
experiment).**

| Stimulus | Known quality | Verdict | conf_human |
|---|---|---|---|
| rule-breaker | cartoonishly bad | **bot** | 3 |
| t1-control | weak-bad (failed shakedown control) | human | 62 |
| production bot | the range that matters | **human** | 65 |
| human anchor (non-deck owner window) | human | human | 62 |

Judge's rule-breaker reason: "Every hand identical scripted line: raise to 7.77,
all players call every street to showdown regardless of hand strength. Clearly
synthetic." — the exact mechanical tells the stimulus encodes.

**Preregistered interpretation (decision-matrix §3, branch 1):** the judge
separates the rule-breaker from the human anchor → the instrument has at least
cartoon-level sensitivity → **ruling A proceeds**. Calibration reading: the
discrimination threshold sits between "rule-breaker" and "T1" — T1 confirmed
too lifelike on a fresh window (62, matching both shakedown verdicts), and the
CURRENT production bots already read as human (65) at 30-hand exposure to this
judge. Consequences: (a) the rule-breaker is validated as the §d.2 control
stimulus; (b) a finale pass is plausible even pre-improvement — which is why
§8's "low detection is weak evidence" rule and the owner blind play-test carry
the believability claim, not the detection number alone.

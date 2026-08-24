# Improvement slice 3 (calldown) — close packet

**Bottom line.** Slice 3's build work is COMPLETE: all five tickets shipped
(two of them by deliberately withdrawing their lever and shipping the
instrument and findings instead), every slice gate — HARD bands, ordering
legs, the five-seed de-robotization gate — is green at the tip `0561e8f`
(§4 discloses two test failures on the owner's machine that are stale local
artifacts, not code), and chain-wide went-to-showdown fell for five of six personas on both
measuring instruments (pooled −0.98pp on the gating band harness, −1.5pp on
the 50,000-hand diagnostic export; the TAG most, −4.0/−4.3pp). **The slice is
NOT closed yet:** under the standing 2026-08-17 ruling it closes on the
owner's blind play session, not on these numbers. What the owner does next:
play the session (`play-session-checklist.md`), then rule on the filed
decisions (`owner-decisions.md`). The finale detection run is ready to fire
once the owner supplies keys and go-ahead (`finale-readiness.md`).

## 1. What shipped, ticket by ticket

| Ticket | PR | What actually shipped |
|---|---|---|
| S3-T1 + T1b | #211, #212 | The strong-draw calling floor is now tunable and price-conditioned: the protected share of the draw's call bonus is the share the draw's own equity pays for at the price it faces, and the rest moves with the calling dial. `calling_station` byte-identical. |
| S3-T2 | #215 | Nit and TAG calling dials retuned toward grounded showdown (nit 0.45→0.32, TAG 0.60→0.38; single-ticket effect −1.80pp / −6.15pp WTSD). The LAG's floor was withdrawn on owner ruling — its dial works only through cross-persona coupling (ledger Filed 3). First attempt was BLOCKED (#213, docs-only) and repaired under ruling 11. |
| S3-T3 | #216 | Lever WITHDRAWN after triple review converged on a design flaw (the stack-to-pot damp points the wrong way where it has leverage — ledger Filed 5/7). What shipped: the capped-composition probe instrument + theory-contract §3 limits. Engine byte-identical. |
| S3-T4 | #217 | α fold ceiling extended over naked ace-high on the river as a strict-xfail one-way tripwire — all 24 cells breach, filed for owner ruling rather than tuned around (Filed 9); the theory review then found the per-bucket obligation itself may be mis-specified (Filed 10). Damp re-derivation did not fire (ruling-7 headroom missed). No engine change. |
| S3-T5 | #218 | Late-street bet lever on the checked-down path. Per the pre-registered per-persona ship rule, **only the LAG ships it**; the nit and TAG were withdrawn (failed the falls-at-pinned-seed AND pooled-sign-agrees gate). |

## 2. Chain-wide measurements (the number the per-ticket reports don't show)

Full record with commands, seeds, and pins: `close-measurements.md`. Headline,
baseline `d351150` → tip `0561e8f`:

| persona | band harness Δ WTSD | 50k export Δ WTSD |
|---|---|---|
| nit | −0.44pp | −2.4pp |
| tag | **−4.01pp** | **−4.3pp** |
| lag | −0.89pp | −1.0pp |
| maniac (pack untouched) | +0.33pp | −0.6pp |
| calling_station | −0.83pp | −0.2pp |
| passive_fish | −1.41pp | −1.3pp |
| **pooled** | **−0.98pp** | **−1.5pp** |

Context for reading it honestly: the spec's own arithmetic said calldown is
the largest available lever on pooled went-to-showdown **and would not be
enough** — reaching the S5 cutoff needs roughly a twelve-point move. The
chain bought about one to one-and-a-half points while keeping every HARD
band, ordering leg, and the five-seed de-robotization gate green. The primary
justification for this slice was never that number alone: showdowns are what
make other tells visible to a judge at all.

## 3. The record, by document

- **Owner decisions filed:** `owner-decisions.md` — six items, each with a
  recommendation and its cost. The one that unblocks others: α per-range vs
  per-bucket.
- **Ledger (Filed 1–15, all adjudications):** `../../ledger/flywheel-slice3-calldown.md`.
- **Per-ticket reports:** `t2-fix-round-report.md`, `t3-report.md`,
  `t3-preregistration.md`, `t4-report.md`, and the T5 report in this directory.
- **Finale detection-run readiness:** `finale-readiness.md`. Crux verdict: the
  control problem that killed the S6 pilot is solved in shipped code (PR #184
  + estimand contract §g.5 A); the execution checklist's §5 was aligned to
  §g.5 clause C (all four judge slots) on 2026-08-23; what remains is
  owner-only — keys, model-ID/price confirmation, go-ahead.
- **Play-session checklist:** `play-session-checklist.md` — the acceptance
  procedure that actually closes this slice.
- **Wave plan and process record:** `../../plans/slice3-chain-autonomy.md`
  (waves 0–4 ran 2026-08-22; wave 5, this close packet, ran 2026-08-23 under
  the /ai-org:build ceremony — three Sonnet workers + Director synthesis,
  refuter-reviewed, no engine/pack/frontend change of any kind).

## 4. Verify status at close (measured 2026-08-23)

`./scripts/verify.sh` at tip `0561e8f`: **2,191 passed, 6 xfailed, 2 failed — and both
failures are machine-local, not code.** The two failures are
`tests/test_detection_probe.py::TestStubEndToEnd` end-to-end tests, which read the
gitignored S6 probe artifacts under
`docs/ai-dlc/research/persona-realism-artifacts/detection-s6/` and the owner's live app
database. The probe's pinned owner session (2026-08-14) no longer exists — the live DB now
contains only the owner's 2026-08-21 play session — so the pin dangles. In a clean checkout
without those gitignored artifacts the same tests SKIP and the suite is fully green
(verified in a worktree: 6 passed, 2 skipped). **Owner fix, one move:** the probe artifacts
are part of the same S6 probe residue as the keys already scheduled for revocation — running
the teardown and archiving/deleting the stale `detection-s6/probe` + `deck` directories
restores a green `verify.sh` on this machine. Filed rather than fixed here because the
artifacts are owner research material and wave 5 owns no code or research-artifact deletions.

## 5. Repo hygiene note (wave 5c)

Eleven fully-merged local branches were deleted. **No worktrees could be
removed from inside the session** — the sandbox denies writes under
`.git/worktrees/` — so ~40 stale worktrees remain on disk. The per-item
disposition log with ready-to-run removal commands is
`local/session-2026-08-23/prune-log.md` (machine-local); running those
`git worktree remove` commands in a plain terminal will succeed. Because this
repo ships by squash-merge, most old branch tips are not literal ancestors of
main and were conservatively kept.

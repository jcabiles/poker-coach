# Finding ledger — R10 preflop lane slice 1 (R10-COUNT)

Slice: conditional action-at-node counters (`NodeActions`) — the lane's instrument. Branch
`feat/persona-realism-r10-count` (rebased onto main post-#134/#135), commits `2b252d8` (build) +
`4c79803` (review folds). PR #136. Reviewers (git-READ-ONLY): `refuter`, `persona-realism-theory-reviewer`,
Codex `gpt-5.6-sol`.

## Done-condition

Seeded n=600: maniac first-in raise **0.236 aggregate** (corpus ≈0.27, band [0.18, 0.34]),
**0.197 EP** (corpus ≈0.18, band [0.12, 0.26]), EP < aggregate (R10-1a collapse shape) asserted.
Byte-identical (measurement only, zero fixture edits), `BACKEND VERIFY OK` 1129/1, ruff clean.

## Findings

| # | Source | Sev | Finding | Adjudication |
|---|--------|-----|---------|--------------|
| C-1 | Codex | MED | Aggregate band floor 0.22 seed-fragile — 60-seed sweep tripped it 2/60 (0.2185/0.2198); shared-rng-stream shifts act like reseeds | **ACCEPTED — FIXED** `4c79803`: bands widened to ~3σ binomial ([0.18,0.34] / [0.12,0.26]); coupling caveat documented |
| R-2 | refuter | MED | Corroborates C-1 independently (10-seed probe tripped the EP cap 1/10 at 0.241; aggregate floor margin only 0.9σ); test coupled to full pack set via shared rng | **ACCEPTED — same fix**; docstring states "a trip implicates the whole pack set, not the maniac pack" |
| R-1 | refuter | MED | Report printed three-decimal rates off n=6/12/20 with no ≥30 floor, contradicting the module's own policy | **ACCEPTED — FIXED**: rows below 30 print `--` |
| T-1 | theory | MED | Pooled `all_hits` vs_3bet rate mixes opener re-entrants with cold facers — not class-comparable to standard Fold-to-3bet (R10-3BET exit ③ must stratify) | **ACCEPTED — FIXED**: NodeActions docstring documents opener-conditioned stratum = `all_hits − first_hits` |
| R-3 | refuter | LOW | `check` action (BB walk edge) missing from report columns — a nonzero count would silently break row sums | **ACCEPTED — FIXED**: column enumerated |
| C-2 | Codex | LOW | "no second sim loop" comment overclaimed — cross-val pays one cold (maniac,600) run | **ACCEPTED — FIXED**: comment corrected (~4s cost stated) |
| T-2 | theory | LOW | "centred on instrument readings" wording inaccurate for the aggregate band | **ACCEPTED — FIXED** in the C-1 rewrite |

Verdicts: refuter PASS · theory PASS (0.236-vs-0.27 judged genuine agreement — per-position conditionals
are lineup-independent; gap direction matches the documented station-doubled pool bias; DIRECTIONAL
labeling correct per §5a) · Codex FAIL→resolved.

## Incident (process, not code)

Mid-review, a **second concurrent Claude session** committed its CI fix (`pytest pythonpath`) onto this
lane branch, **silently reverting the R10-COUNT diff inside that commit** (undeclared in its message),
and left HEAD on `main`. Recovered non-destructively: lane branch reset to the reviewed tip, foreign
commit preserved on `chore/ci-pytest-pythonpath-rescue`; the CI fix later landed cleanly as PR #135.
Lesson (adds to the W3 git-incident file): concurrent sessions in one working tree are a real hazard —
before committing after ANY pause, `git rev-parse --abbrev-ref HEAD` AND `git log --oneline -1`.

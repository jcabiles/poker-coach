# Ledger — flywheel-s1 spec dual review (2026-08-05)

Reviewers over spec rev 1: Claude `refuter` (sonnet/high) → **NEEDS-WORK** (3 MED / 3 LOW);
Codex `gpt-5.6-sol` (high) → **FAIL** (10 HIGH / 4 MED / 2 LOW). Heavy overlap; no
reviewer-vs-reviewer conflicts. Adjudicator: director; both repo-state claims (Sol-2, Sol-6)
independently verified before acceptance. All accepted findings folded into **spec rev 2**.
Sol's FAIL adjudicated as fold-and-revise (every defect maps to a concrete rev-2 change; none
attacks the slice direction) — same pattern the owner ratified for the roadmap review.

| # | src | sev | finding (compressed) | adjudication |
|---|-----|-----|---|---|
| 1 | sol | HIGH | Verify-by incompatible with worktree workflow: sim50k is gitignored (primary checkout only), sibling default resolves wrong from a worktree. | **ACCEPT.** Rev 2 Verify-by: explicit pre-merge procedure (worktree script + explicit data/env args), no-arg form re-run post-merge from primary checkout. |
| 2 | sol | HIGH | Worktree from HEAD discards owner-ratified uncommitted roadmap amendments (committed HEAD still `status: draft`). Verified via `git show HEAD`. | **ACCEPT.** Files-touched now explicitly authorizes committing THIS file's rider deltas (status flip, publication paragraph, header fix) with the S1 `[x]`; all other riders stay uncommitted. |
| 3 | sol | HIGH | Stub bypasses the authoritative ingestion gate; corrupt/truncated batch could "score". | **ACCEPT-NARROWED.** Stub adds cheap integrity checks (manifest keys, per-table row counts vs manifest, seats ⊆ lineup); full ODCS gate NOT rerun (stub bar stated in docstring + agreement); agreement rule: S3+ scorer runs sit behind `make validate`. |
| 4 | sol | HIGH | Verify-by can't prove the 9-seat→6-persona join (duplicate personas; wrong mapping could still sum to 884,745). | **ACCEPT.** Verify step 1 asserts the six EXACT per-persona counts (independently recomputed by both reviewers, matching). |
| 5 | sol | HIGH | Output pins violate PRD ✅Always (missing schema_path_version, scorer provenance, lockfile, checksums). | **ACCEPT-NARROWED.** Stub embeds full producer manifest verbatim + scorer_version + analytics_git_sha + duckdb_version; lockfile/checksum pins deferred to S4's batch-manifest extension and DECLARED as a gap in agreement §2 (not silent). |
| 6 | sol | HIGH | D5 leaves FLYWHEEL-STATUS's false claim ("batch manifest in slice S1") + stale approval line. Verified lines 13–14. | **ACCEPT.** D5 now names both corrections. |
| 7 | sol | HIGH | "S1 lands" has no cross-repo meaning; session R could launch against a half-landed S1. | **ACCEPT-NARROWED.** Agreement §6 defines landing = both repos' commits merged + owner confirmation; the R-brief carries it as launch precondition. No paired-OID machinery (owner is the sole launcher; overkill for a 2-repo doc slice). |
| 8 | sol | HIGH | Session R has no output-handoff path (R can't commit; F can't sweep foreign edits). | **ACCEPT.** Agreement §5 handoff clause: R writes a completion note; director reviews at fan-in and commits accepted dossiers from a worktree. |
| 9 | sol | HIGH | Plain `git diff` no-go check passes after forbidden changes are COMMITTED. | **ACCEPT.** Verify step 4 now requires both the merge-base range diff AND the working-tree diff over `backend/app/domain/` + `content/`. |
| 10 | sol | HIGH | "Owner performs pushes" contradicts CLAUDE.md's autonomous feat/* push authorization. | **ACCEPT-NARROWED.** Not an authority conflict — capability vs authorization: agreement §8 states pushes remain AUTHORIZED per CLAUDE.md; the sandbox currently cannot push, so local-commit + owner-push is the operational fallback. No CLAUDE.md edit needed. |
| 11 | both | MED | `--out`/stdout behavior undefined; stray output file could get swept into a commit; verify can't locate the JSON. | **ACCEPT.** D3 output contract: table→stderr, JSON→stdout, `--out` optional file, omitted = no file written; bridge passes args through. |
| 12 | both | MED | Manifest/join failure modes unspecified (invalid JSON, missing keys, unmapped seats, silent inner-join drops). | **ACCEPT-NARROWED.** Enumerated gate checks with clear exit-1 messages; anything beyond them (e.g. mid-file Parquet corruption) is accepted stub behavior, stated explicitly. |
| 13 | sol | MED | Bridge path/env contract incomplete (empty var, relative paths, only `.venv` dir checked, custom resolution untested). | **ACCEPT.** D4: empty var = unset; checks `.venv/bin/python` executable + stub file; cwd-relative `$1`; pre-merge procedure exercises the env-var path. |
| 14 | sol | MED | Completion gate omits D2/D5/exec-mode/mirror-equality/dual-review evidence. | **ACCEPT.** Verify step 5 added (mirror `diff`, brief precondition, D5 corrections, `test -x`); step 6 ties `[x]` to this ledger recording both reviews. |
| 15 | both | LOW | `score` missing from `.PHONY`. | **ACCEPT.** In D3. |
| 16 | sol | LOW | "Payload inherited verbatim" false — D2/D5 are scope additions with unstated authorization. | **ACCEPT.** Provenance line rewritten: D2 + D5 attributed to the owner's 2026-08-05 handoff instruction (both were explicit owner tips), core payload to the roadmap. |
| 17 | ref | MED | Two-session protocol covers F-vs-R only; roadmap schedules S6∥S5 = two concurrent CODE sessions. | **ACCEPT.** Agreement §5: concurrent code sessions only with disjoint declared file ownership + separate worktrees; roadmap/START-HERE/status docs are director-single-owner. |
| 18 | ref | MED | Vendored ODCS copy has no sync owner (advisory producer check only; copies currently byte-identical). | **ACCEPT.** Agreement §1: poker-coach owns the vendored copy, updated in the same change as any export-schema change; sync check = `diff`. |
| 19 | ref | LOW | Duplicate-seat pooling precedent undocumented for S3. | **ACCEPT.** Out-of-scope section carries the flag to S2a (pooled vs per-seat is an estimand decision, not S1's). |

## Build fan-in review (2026-08-05)

Reviewers over the T4+T5 implementation: Claude `refuter` (sonnet/high) → FAIL (2 real
findings + 1 sequencing); Codex `gpt-5.6-sol` (high) → NEEDS-WORK (2 real findings + same
sequencing observation). Both independently reproduced the exact per-persona counts
(tag 244555 · calling_station 138263 · passive_fish 230849 · lag 89439 · nit 71878 ·
maniac 109761), all gate failure modes, mirror byte-equality, and the empty no-go diffs;
Codex's row-mutation probe confirmed counts are genuinely computed, not hardcoded.

| # | src | sev | finding | adjudication |
|---|-----|-----|---|---|
| B1 | both | HIGH | Relative batch dir resolved against the analytics repo root, not the caller's cwd (spec D4 violation; cross-repo relative paths fail pointing at the wrong repo). | **ACCEPT → FIXED** by both owners: bridge absolutizes `$1` against `$PWD`; stub uses plain cwd-relative `Path` semantics. Re-verified by director (relative-path repro exit 0, exact counts). |
| B2 | ref | MED | Leading flag (`--out X`) swallowed as the batch-dir positional; usage comment documented an unimplemented `--` separator. | **ACCEPT → FIXED**: `""` / `--` / leading-dash all select the default batch dir and forward args; usage comment corrected. Re-verified (file written). |
| B3 | sol | MED | Non-UTF8 and non-object (JSON `null`/list) manifests leaked tracebacks where the spec promises one-line exit-1 messages. | **ACCEPT → FIXED**: UnicodeDecodeError/OSError join the invalid-JSON gate; `isinstance(dict)` check before the key scan. Re-verified (both cases: exit 1, one line). |
| B4 | both | HIGH/MED | Deliverables uncommitted, no `feat/flywheel-s1` worktree/branch. | **REJECT as defect** — sequencing by design: the ticket plan gates T6 (worktree commits) behind this very review. Executed immediately after. |

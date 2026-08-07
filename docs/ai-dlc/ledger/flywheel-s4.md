# Finding ledger — S4 spec review (Inception phase)

Reviewers (2026-08-07, spec rev 1): Claude `refuter` (Sonnet) + Codex `gpt-5.6-sol`
(high effort), parallel, read-only. Both verdicts: NEEDS-WORK. Every finding below
was verified by the director against code/contract before adjudication (files cited
were re-read; no finding accepted on reviewer authority alone). Spec rev 2 folds in
all ACCEPTED findings. R# = Claude refuter, C# = Codex.

| # | Sev | Finding (short) | Adjudication | Disposition in rev 2 |
|---|-----|-----------------|--------------|----------------------|
| R1=C1 | H | "Batch config_hash must equal covariance artifact's" contradicts §a.3 (Σ_sim measured once, reused wave-wide); exact-match would refuse every non-baseline config — the sweep could never score. Also: the pinned artifact is sentinel-keyed and old-engine-sha'd. | ACCEPTED — verified §a.3 (`estimand-contract.md:163-165`) and `validate_covariance_artifact` (`score_realism.py:149-186`). Director addition, verified: the engine-sha equality check ALONE forces an artifact rebuild at the S4 commit; and the artifact's hand-count equality binds the smoke sweep to 50k hands/config. | Design ruling: artifact config_hash = source identity, never compared to batch; batch config_hash recorded in payload; artifact rebuilt + re-pinned at S4 engine sha (spec items 6–8, acceptance 3). |
| C2 | H | `build_key`/`build_artifact` never thread a real config_hash from replicate manifests (`covariance.py:114` default sentinel); mixed-config replicate sets accepted silently. | ACCEPTED — verified. | Spec item 7: exactly-one-real-hash or all-absent-legacy; mixed sets refuse. |
| C3 | H | §c.6 requires config_hash as "the config's identity in every manifest, score row"; canonical `producer_run` (`score_realism.py:435-444`) omits it and the spec never put it there. | ACCEPTED — verified §c.6 + canonical dict. | Spec item 6: `producer_run.config_hash` when manifest carries it; omitted for legacy manifests (pre-S4 canonical bytes preserved). |
| C4 | H | Re-export byte-identity impossible: `exported_at = now()` stamped into every parquet row (`export_analytics.py:254-266`), raw parquet hash sits inside the score canonical (`gate.parquet_sha256`). Acceptance 1(i) and smoke-rerun as written were unachievable. | ACCEPTED — verified. Adjudicated fix differs from Codex's suggestion: rather than adding a logical-content hash to the gate (heavier, touches S3 tamper-evidence machinery), identity claims are SPLIT — re-scoring = full byte-identity; re-exporting = parquet equality excluding `exported_at` + canonical equality masking `gate.parquet_sha256` only. Codex's logical-hash alternative recorded as considered; revisit if the masked comparison proves awkward in practice. | Design ruling + acceptance 1(i)/3; producer-rerun check added to the runner (also closes S3's declared rule-5b gap). |
| C5 | H | ODCS ambiguity already resolvable: both copies document manifest keys (customProperties, `poker_events.odcs.yaml:428-433`) → bump required; but gate does EXACT `contract_version` equality (`ingest/validate.py:134-139`) → a 1.2.0 bump would refuse the committed 1.1.0 sample and all legacy batches, breaking CI. | ACCEPTED — verified both. Gate's own error text says "matching contract major" and the ODCS declares `compatibilityPolicy: BACKWARD` — the exact-equality code was already stricter than its documented intent. | Spec items 2/5/10: ODCS 1.2.0 additive in both copies + changelog; gate check relaxed to same-major + minor-window, with legacy-batch tests. |
| C6 | H | Pydantic default serialization materializes unset optional fields; §c.4 makes key-absence semantically load-bearing (e.g. `continue_ref`) — a naive merge would silently change pack semantics. | ACCEPTED — verified `models.py` optional fields + §c.4 text. | Spec item 1: `exclude_unset=True` serialization + presence-preservation test. |
| C7 | H | §a.2 axis 7: `continue_ref` is "never co-swept with #5 (call_looseness)"; the spec only required a probe declaration, so a declared probe could vary both. | ACCEPTED — verified axis table text. | Spec item 1: co-sweep = rejection. |
| C8 | M | Dotted-path parsing ambiguous for decimal sizing keys (`postflop.sizing.0.33`); `probe_declarations` had no schema. | ACCEPTED — verified §c shows dotted strings + empty array only. Deviating from dotted strings would need a contract amendment, so paths STAY dotted with a deterministic greedy-match parse rule instead. | Spec item 1: parse rule + frozen probe schema, unit-tested against authored keys. |
| C9 | H | §f (`estimand-contract.md:685-698`) makes the 5-worker parallel runner a REQUIREMENT (serial ≈ 53–144 h at program scale) and mandates raw-parquet deletion after scoring; spec had neither. | ACCEPTED — verified §f text. Sandbox note: ProcessPoolExecutor is blocked → threads driving export subprocesses. | Design ruling + spec item 3 (bounded 5 workers, delete-after-score, `--keep-raw`). |
| C10 | M | `_TIMING.json` schema unpinned; `constraints.py:544` reads the exact key `wall_seconds` — a naming drift fails every run closed. | ACCEPTED — verified. | Spec item 2: frozen schema validated against `_SUCCESS`. |
| C11 | M | Score collection via stdout parse is fragile (Make echo); manifest "config list order" underspecified vs paths-are-volatile. | ACCEPTED. | Spec item 3: always `OUT=`/`COV=` explicit; canonical = hashes/logical IDs only. |
| C12 | M | Scope exceeds the 2–3 day appetite once its own contracts are honored; suggested S4a/S4b split. | ACCEPTED as a real cost signal; disposition = OWNER DECISION at Gate 2 (re-cost vs formal split). Director lean: keep one slice, re-cost 4–6 days, sequence tickets config-layer-first (the natural S4a boundary falls between T1–T4 and T5–T7 anyway). | Put to owner at Gate 2. |
| R2 | M | ODCS `run_id` description string ("run-s<seed>-n<hands>") goes stale in both copies; no changelog planned. | ACCEPTED — folded into the C5 ODCS work. | Spec item 2. |
| R3 | M | Acceptance 1(i) risks vacuity: if the no-config path ALSO simulates canonicalized packs, the test compares two identical constructions and never proves canonicalization safety against current production behavior. | ACCEPTED. | Design ruling: default path simulates RAW packs; canonicalization is hash-side-channel only. |

Reviewer disagreements requiring owner arbitration: none — the reviewers were
disjoint-but-compatible (the refuter found R1/R2/R3; Codex found C1=R1 plus nine
more). The one owner call is C12 (appetite), surfaced at Gate 2.

---

# Finding ledger — S4 build, wave 1 (T1 config layer + T3 analytics compat)

Commits reviewed: coach 3348c11 (T1), analytics d885dbe (T3). Reviewers: Claude
`refuter` on Opus (high) + Codex `gpt-5.6-sol` (high), parallel, git-read-only,
2026-08-07. Both: NEEDS-WORK. All findings director-verified before adjudication.
Independent re-verification by reviewers: all §a.2 bounds match the contract table;
no pack aliasing/mutation; exclude_unset round-trip stable; cross-process hash
stable; legacy canonical payload bytes source-level unchanged; ODCS 1.2.0 additive,
changelog safe vs CI grep; both test suites reproduced green (64 + 105).

| # | Sev | Finding | Adjudication |
|---|-----|---------|--------------|
| W1-1 | H | (both reviewers) Pipeline split: ingest gate windows contract versions, scorer gate.py still exact-matches citing §g.1.7 — committed 1.1.0 sample gates but cannot score; spec acceptance 6 unreachable. | **OWNER RULING 2026-08-07: amend §g.1.7** — score invalid only when the ODCS version falls OUTSIDE the same-major window (batch minor ≤ contract minor); the estimand-contract CITATION stays exact (formula-identity-bearing). gate.py gets the window. Refuter's textual analysis (ODCS version not part of the status triple; score records the batch's OWN version; compatibilityPolicy BACKWARD) adopted. Fix → T3 worker. |
| W1-2 | M | (refuter) `_GATE_OK.json` records the REPO's contract version, not the batch's — post-window the marker asserts provenance the batch never had. | ACCEPTED — marker records the batch's declared version; gate compares marker↔manifest. → T3. |
| W1-3 | M | (Codex) Both repos' version parsers accept malformed strings ('1.2', '1.2-beta', '1.-1.0'…). | ACCEPTED — strict ^\d+\.\d+\.\d+$ both sides. → T1 + T3. |
| W1-4 | M | (Codex + refuter-L) `config_hash` never format-validated; covariance treats null-valued key as present, bare TypeError on mixed None/str. | ACCEPTED — ^[0-9a-f]{64}$ when present; clean refusals. → T3. |
| W1-5 | M | (Codex) "shortest-round-trip float repr" not literally met by json.dumps ('1e-07' vs '1e-7'); -0.0 vs 0.0 hash-differs. | PARTIAL — ruled: Python repr IS the canonical form (matches the scorer's existing canonical_bytes convention; pipeline consistency beats literal minimality), documented as the §c.6 reading; -0.0 normalized to 0.0. → T1. |
| W1-6 | M | (Codex; T1 worker's own assumption #2) sizing_by_node probe bounds invented (flat-sizing simplex rule inherited without contract basis). | ACCEPTED — assumption rejected; probe overrides enforce only pack-model validation until a contract amendment declares bounds. → T1. |
| W1-7 | L | (refuter) Single-key flat-sizing override dies with raw pydantic error; all-k-keys+sum≈1 rule unstated. | ACCEPTED — explicit §a.2 row-13 completeness rule + named error. → T1. |
| W1-8 | L | (refuter ×3) bare asserts (python -O unsafe); public apply_overrides skips bounds; probe ordering omits rationale from sort key. | ACCEPTED, all three. → T1. |
| W1-9 | L | (refuter vs Codex — DISAGREEMENT) probe `rationale` prose enters config_hash (re-wording renames the config/run identity). | ADJUDICATED with Codex: §c.6 hashes the complete document — rationale STAYS in the hash, documented as intentional + tested. Refuter's dedup/CRN concern recorded as the known cost. |
| W1-10 | L | (Codex) ODCS changelog claims bidirectional 1.1↔1.2 compatibility; window is one-directional. | ACCEPTED — reword. → T3. |

Fixes dispatched to the ORIGINAL ticket workers (ownership continuity); re-verified
at the wave-1 fix fan-in before wave 2 spawns.

**Wave-1 fix verification (refuter re-check, 2026-08-07):** all code findings FIXED
(reviewer reproduced: 1.1.0-sample acceptance at both gates, marker-forgery refusal,
all malformed config_hash refusals, python -O safety, private merge). Four residuals,
all accepted + fixed in follow-up commits: W1-11 (M) the rev-5 amendment omitted §g's
mandatory bold analyses-had-run disclosure — the FIRST post-results amendment must say
so (fixed, commit 9df141e, disclosure verified against validation artifacts before
writing); W1-12 (L) banner pointer + deliberate-citation-non-change note (fixed,
same commit); W1-13 (L) coach semver used match() not fullmatch + accepted leading
zeros — raw string enters config_hash → duplicate identities (fixed, 63c67f0; coach
now STRICTLY stricter than analytics on leading zeros — analytics int-converts so
harmless there; divergence documented in code); W1-14 (L) completeness rule
generalized to both bucket-dist families, keyed on resolved container path (fixed,
63c67f0). baseline_config_hash unchanged throughout:
9273b753b9de041a9750557f21c72d4a7482b344d73be7d378b3df56c21375f8.

---

# Finding ledger — S4 build, wave 2 (T2 export identity, commit 21ed0f7)

Reviewers: same dual pair (refuter/Opus continuation + Codex Sol), git-read-only.
Both NEEDS-WORK. **End-to-end VERIFIED by both:** fresh 1.2.0 coach export → analytics
ingest gate 156/156 → scorer require_gated OK → throughput reader 390 hands/s on a
200-hand batch; RAW-packs ruling holds (canonicalization never reaches simulated
packs — acceptance 1(i) stays non-vacuous); ODCS mirror byte-identical.

| # | Sev | Finding | Adjudication |
|---|-----|---------|--------------|
| W2-1 | H | (Codex) 50k export measured 333.6 hands/s < 350 floor. | REJECTED as code defect — measured under 4-agent concurrent load. Director re-ran the exact pinned-lineup 50k export on a quiet machine: **413.8 hands/s (120.82 s)**, matching S3's 413/s. Recorded as an operational caveat: T5's 5-way parallel exports will depress per-batch _TIMING numbers; rule 5(a) evidence must come from the serial one-config benchmark (T6), not from batches exported under parallel load. |
| W2-2 | M | (refuter) Supplied config_hash never validated at the producer — malformed hash baked into run_id + every row, fails only at the consumer gate; [:12] truncates short strings silently. | ACCEPTED → T2 fix. |
| W2-3 | M | (refuter) CONTRACT_VERSION constant and vendored ODCS version: are two unsynced literals; the new gate window makes drift silent in the dangerous direction. | ACCEPTED → derive from the yaml (or test-guard). |
| W2-4 | L | (refuter) No CLI door for packs/config_hash, but the sweep runner must drive exports as subprocesses (spec requirement). | ACCEPTED — settled now: `--config <path>` added in T2 (hotspot owner), resolving via counterfactual.load_config(). |
| W2-5 | L | (both) Test hardening: match() vs fullmatch in test regexes; _TIMING.json exact key set; write-order proven by call-order spy incl. parquet files, not mtimes. | ACCEPTED → T2 fix. |
| W2-6 | L | (refuter) ODCS mirror kept in sync by hand with no drift guard on either side; producer-side contract check silently no-ops (datacontract CLI absent). | ACCEPTED — sha256 pin test in coach; consumer gate remains authoritative (and was exercised for real). |

All W2 fixes landed in commit 2925be7 (supplied-hash validation, CONTRACT_VERSION
derived from the vendored yaml, `--config` CLI, write-order call spy, mirror sha pin);
scoped tests 108 green, full suite 1538 green.

---

# Wave 3 (T5 sweep runner) — build notes, pre-review

T5 commit landed (sweep_runner.py + 29 unit tests; full suite 1567 green). Real
end-to-end mini-sweep proved: upfront config validation, 5-worker parallel export,
serial gate+score wiring (scores read from OUT files only), fail-closed partial
labeling with captured stderr, and canonical-manifest byte-identity across two fully
independent driver runs.

**OPEN FINDING (environmental, being sized):** at n=300 hands / 5 replicates, the
analytics scorer crashes deterministically on this machine — numpy 2.5.1 + Apple
Accelerate LAPACK `SVD did not converge` in `sigma_star`'s condition-number check —
even scoring a baseline batch against its own artifact. S3 scored 50k batches on the
same machine, so the working hypothesis is small-sample covariance degeneracy, not a
50k-scale blocker. T5 worker re-running the e2e at n=3000 to size it; if it persists
there, it threatens the T6 acceptance sweep and escalates to the owner. Also fixed in
the follow-up: the sweep spec gains an identity-bearing `lineup` field (director's
brief had omitted it; without it T6 could not match the covariance artifact's lineup
key).

Known operational caveat carried from W2-1: per-batch _TIMING.json numbers produced
under 5-way parallel load run ~20% slower; rule-5(a) throughput evidence must come
from the serial one-config benchmark, never from parallel-sweep batches.

**T5 follow-up (f0fc72d):** SVD crash CONFIRMED small-sample-only — at n=3000 the
same recipe runs COMPLETE with populated score fields; re-SCORING the same batches
byte-identical 4/4. `lineup` added to the sweep spec + canonical (identity-bearing,
cross-checked per batch, fails closed on mismatch). Observed + correct-per-contract:
score_status resolves from the (formula, registry sha, statdef) triple — a throwaway
covariance artifact under the pinned registry still stamps `exploratory-surrogate`.
Also recorded: whole-sweep re-runs legitimately differ (re-export → fresh exported_at
→ different gate.parquet_sha256); re-SCORE is the byte-identity claim — T6 must not
chase a false "sweep isn't deterministic" alarm.

**Wave-3 dual review (commits 262e621+f0fc72d; refuter/Opus + Codex Sol, both
NEEDS-WORK):** reviewers converged, refuter proved findings with monkeypatched
probes. Cleared: lineup-wrap equivalence (line-by-line), thread-safety, canonical
purity + spec-order determinism, parquet compare + masking, subprocess hygiene.
Accepted (all → T5 fix commit): W3-1 (H, both) unhandled exceptions (worker crash,
bad analytics_repo path, empty-JSON score OUT) abort the sweep with NO manifest —
a typo'd spec path would burn the whole 25-min export phase; W3-2 (H, Codex) "ok"
assigned before payload usability — validate shape + recompute canonical sha; W3-3
(H, Codex) no identity cross-check of _SUCCESS/producer_run vs the requested arm;
W3-4 (H/M, both, probe-proven) failed rerun-check DELETES both evidence dirs; W3-5
(M, refuter) dup-run diagnostics dropped — make failures masquerade as engine
nondeterminism; W3-6 (M, Codex) stale score.json acceptable; W3-7 (M, Codex,
probed 1 vs 1.0) rerun compare used dict equality not canonical bytes; W3-8 (M/L,
both) cov_artifact optional vs spec's "always explicit COV" — now required; W3-9
(L, refuter) manifest schema_version was the spec's unvalidated user value entering
the canonical hash; W3-10 (L, refuter) dead SweepRunError + bare assert; W3-11 (L,
both) adversarial failure-path tests; W3-12 (M, Codex) analytics Makefile unquoted
DIR/OUT/COV expansions → analytics worker (ownership expanded to Makefile).
Codex aside noted, no action: score payloads' canonical section includes dependency
versions (S3 design), so score hashes are environment-sensitive transitively.

**Wave 3 CLOSED (re-check verdict OK, 2026-08-07):** all 12 fixes probe-verified in
commit b23c83c — reviewer re-ran its original crash probes (worker exception, bad
analytics path, empty score payload, forged hash, identity drift, failed rerun-check)
and each now yields a failed run + labeled partial manifest + retained evidence; the
n=3000 e2e re-proof still lands complete. Makefile quoting (a3d7ac1) verified
behavior-neutral incl. the deliberate BATCHES exception (nargs="+" interface). Fake
test payloads now carry real recomputed hashes — a strengthening. One cosmetic L
(dead SweepRunError class) deleted in e7c1b38 before T4, since T4's artifact pins
the final engine sha.

---

# Waves 4-5 (T4 artifact rebuild + T6 acceptance run) — pre-review record

**T4 (analytics 12884db):** baseline Σ_sim rebuilt at coach engine e7c1b38 from
5 serial 50k exports (seeds 601-605, ratified lineup): artifact
`cov-4a718ef1f6c30391`, key carries the REAL baseline config_hash 9273b753…375f8
(sentinel retirement proven live), DEFAULT_COVARIANCE_ARTIFACT re-pinned, old S3
artifact preserved as historical evidence. No-COV scoring proven (status
exploratory-surrogate as required). Serial timings 121.9-126.0 s (397-410 hands/s).
Worker self-caught + amended a commit trailer that had misattributed the work to
Fable (it is Sonnet).

**T6 (coach 645740d, report docs/ai-dlc/reports/flywheel-s4-acceptance.md):** ALL
acceptance sections PASS — §c(i) canonicalization safety (empty-override batch
parquet-equal minus exported_at to the raw-baseline batch, identical run_id +
config_hash, masked score-canonical equality); §c(ii) CLI-boundary rejection demo;
§c(iii) cross-process hash stability under differing PYTHONHASHSEED; 10-config 50k
smoke sweep complete (10 ok runs, distinct hashes, producer-rerun check passed,
10/10 re-score byte-identity); §f benchmark — measured worst 125.95 s/run →
~915 configs/night → hard-cap program ≈1.64 nights vs the 6-night threshold →
**escalation clause does NOT fire**; gap check — S3 gaps closed: config_hash
sentinel, producer-rerun check, run_id/config collision; remaining disclosed wart:
lineup still absent from run_id (and the exporter's DEFAULT_LINEUP ≠ ratified
lineup — callers must pass --lineup explicitly).

Observations for S5 planning: parallel-load per-batch timing degradation measured at
~55-73% (worse than the ~20% earlier estimate); serial timing is the only valid
throughput evidence. Process note for T7: the S4 planning docs (spec rev 2, tickets,
contracts, this ledger) live uncommitted in the MAIN checkout — T7 commits them to
the branch.

**Wave-5 dual review (T4 12884db + T6 645740d; both NEEDS-WORK on the REPORT only —
code + artifacts verified clean by both):** Codex independently REBUILT the
covariance artifact from the retained replicate batches — exact object + id match;
matrix structure verified (pool 10×10, personas 7×7, finite, symmetric, positive
diagonals, rank 4 as expected from 5 replicates, no degeneracy). Refuter cross-checked
the artifact's config_hash against its own wave-1 computation of
baseline_config_hash() — byte-identical (sentinel retirement proven by two
independent routes). Committed-sample refusal under the new default: unchanged in
kind, names all THREE mismatches (engine sha, hand count, lineup). §A/§D evidence
reproduced end-to-end by both (only-exported_at manifest diff, single canonical leaf
diff = gate.parquet_sha256, 10/10 re-score hashes re-derived). Stop-gate discipline
greps clean.

Report findings, all accepted → T6 correction commit: W5-1 (M, refuter — the
important one) §E's replacement capacity numbers applied §f's ×5 worker factor to a
SERIAL unloaded denominator, contradicted by the report's own loaded measurements
(per-worker efficiency 0.61 at 5 workers) — 1.7-2.3× optimistic; corrected primary
figures = 404.7 configs/night measured end-to-end, 3.71 nights at the 1,500 hard cap
(program 2.58-3.03 nights). **ESCALATION VERDICT UNAFFECTED** (3.71 < 6) — confirmed
independently by both reviewers. §f's own history (v1.0 false serial margins) makes
this exactly the error class the contract's "honest arithmetic" preamble exists to
prevent; T7 must NOT transplant §f's ×5-on-serial form with the serial t. W5-2 (L)
denominator omits gate+scorer (~3s) and cites a nonexistent manifest field
(wall_time_seconds → wall_seconds, which bundles gate+score). W5-3 (M, Codex) "~9%
of threshold" → 27.33% (→ 61.8% after W5-1). W5-4 (M, Codex) per-score traceability
mis-attributed to covariance_artifact.key.config_hash (the BASELINE source id) —
correct field is producer_run.config_hash. W5-5 (M, Codex) several claims lack their
reproducible commands. W5-6 (L, Codex) "can never collide" overclaims a 12-hex/48-bit
run_id prefix; full hash is the identity. W5-7 (L, refuter) run_id format typo
[:13]→[:12]. W5-8 (L, refuter) dangling spec citations called "pre-existing" — they
were authored in this slice; resolve when T7 commits the spec.

---

# T7 — closing section

Build phase complete 2026-08-07 — waves 1-5 closed, all reviewer findings
adjudicated + fixed; T7 committed the planning docs; final coach tip 4f52353,
analytics tip c5604e8. Remaining disclosed wart: lineup absent from run_id;
exporter DEFAULT_LINEUP ≠ ratified lineup (pass --lineup explicitly).

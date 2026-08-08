# Finding ledger — S6 detection-protocol pilot (spec phase)

Dual adversarial review of spec rev 1, 2026-08-07. Reviewers: Claude `refuter` (Sonnet)
verdict FAIL, 9 findings · Codex `gpt-5.6-sol` (effort high) verdict NEEDS-WORK, 19
findings. All 28 adjudicated by the director against §d text and cited code — **all 28
ACCEPTED** (heavy overlap between reviewers; zero conflicts). Spec rev 2 folds every one.
Notation: R# = refuter, C# = Codex.

| # | Sev | Finding (compressed) | Adjudication → spec rev 2 |
|---|---|---|---|
| R1 | HIGH | Renderer leaks absolute `hand_no` (human range ≈1–1,200+ vs bot run range) — a class tell missed by both docs | ACCEPTED — local 1–30 re-key; added to STRIPS + leak audit |
| R2 | HIGH | §d internal inconsistency: §d.2 pins "judges told 50/50" but §d.3's verbatim prompt never states it | ACCEPTED — pre-declared amendment §A.2 (pinned base-rate preamble) |
| R3/C4 | HIGH | Per-judge duplicate bundle never actually specified upstream (only its statistic) | ACCEPTED — seeded per-judge duplicate, fresh opaque ID, no adjacency, excluded from stats, schedule tested |
| R4 | MED | `--buyin-spread` deviates from §d-pinned "production policy" wording — unlabeled deviation | ACCEPTED — pre-declared amendment §A.1 |
| R5/C11 | MED | No checkpoint/resume, credential preflight, or min-judges rule for vendor failure mid-run | ACCEPTED — preflight, atomic per-(bundle,judge) checkpoints, idempotent resume, <3-usable-judges exclusion rule |
| R6/C19 | MED | 2–3 day appetite not credible for full scope; roadmap valve never invoked | ACCEPTED — re-cost proposal 4–5 days + pre-agreed cut order in spec (Gate 2 decision) |
| R7 | LOW | Contract-map citation `:66` → actual `:65` | ACCEPTED — fixed in contract map |
| R8 | LOW | Fold-heavy 30-hand windows could be near-content-free | ACCEPTED — disclosed as inherent-variance limitation; no filter (avoids selection bias) |
| R9 | LOW | "Biases WITH directions" overclaims — §d.4 pins direction for only one of four | ACCEPTED — reworded: direction where pinned, "unknown" where disclosed as such |
| C1 | HIGH | Human corpus uncapped: N≥1,230 yields >40 windows; no exactly-40 rule | ACCEPTED — seeded deterministic selection of exactly 40; candidates + selected recorded |
| C2 | HIGH | Bot bundles only per-seat non-overlapping — cross-seat bundles share the same hands (correlated pseudo-replicates; violates §d non-overlap) | ACCEPTED — 40 globally disjoint windows, ≥1,200-hand run, one focus seat per window by recorded scheme |
| C3 | HIGH | Single deck manifest holds class labels AND feeds the judge harness — blinding violation | ACCEPTED — split: blinded presentation manifest (harness input) vs secret unblinding manifest (analysis-only join); tested |
| C5 | HIGH | Deck + bot control + bot duplicate ⇒ judge-visible mix 42:40, contradicting pinned "50/50 … it is" | ACCEPTED — amendment §A.3: duplicate drawn from human class ⇒ 41/41 visible |
| C6 | HIGH | Degenerate control config may be unreachable via §c registered axes; control must share buy-in treatment | ACCEPTED — control pinned + validator-checked EARLY (ticket 1); alternative generator = further amendment; same spread/rendering |
| C7 | HIGH | Spread flag underspecified vs live semantics (integer cents 9500–10500, per-hand stream, nine-draw order) | ACCEPTED — exact semantics pinned + conformance test against `_rebuy_seats` |
| C8 | HIGH | Human slicing can silently break "30 consecutive complete hands" (no uniqueness constraint, in-progress row, skip-and-close-ranks loader) | ACCEPTED — fail-closed window validity rule in one read snapshot |
| C9 | HIGH | Control invalidation undefined under missing judge responses | ACCEPTED — usable-confidence denominator; missing counts against 4-of-5; fail closed → diagnostics only |
| C10 | MED | Malformed-output policy undefined (schema strictness, refusals, retry prompt identity) | ACCEPTED — strict no-coercion schema, raw preserved, identical-prompt retry, transport failures distinct |
| C12 | MED | Statistics formulas unpinned (positive class, BA/AUC/d′ definitions, ties, correction N, missing-response aggregation) | ACCEPTED — all pinned in spec |
| C13 | MED | Bootstrap unpinned (level, B, method, seed, within-class resampling design) | ACCEPTED — 95% percentile, B=10,000, seeded, 40+40 within-class, judge vectors fixed, controls/dups excluded |
| C14 | MED | Kish n_eff registered uses only partially carried; degenerate cases undefined | ACCEPTED — all four uses in acceptance criteria; degenerate → "unavailable", never imputed |
| C15 | MED | "Seeded" too vague — shared RNG streams/filesystem order break reproducibility | ACCEPTED — master seed + domain-separated derivations, canonical sorts, derived seeds + presentation order stored, payloads hashed |
| C16 | MED | Spread run can collide with default run_id (identity claim without identity change) | ACCEPTED — `-bspread-` mode token in run_id; conditional manifest fields; default shape unchanged |
| C17 | MED | Byte-identity tests impossible as written (`exported_at`, `_TIMING.json` volatile) | ACCEPTED — canonical comparison excluding declared-volatile fields (S4 convention); frozen-clock golden tests |
| C18 | MED | Leak audit too weak (string denylist + 1 manual bundle); predealt-board leak via `Hand.board` | ACCEPTED — canonical hand-record schema rendered for both sources; revealed-board only; golden cross-source fixtures; outbound-payload tests |

## Build wave 1 (T1 probe + T2 buy-in spread) — dual review 2026-08-07

Claude refuter: **PASS, 0 issues** (independently re-ran all acceptance commands, wrote
its own default-path determinism check, verified RNG-stream isolation structurally and
the `_rebuy_seats` oracle conformance line-by-line; full suite 1,619 green incl. domain
purity). Codex Sol: NEEDS-WORK, 2 findings, both ACCEPTED:

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| W1-1 | HIGH | Default-path identity test self-referential (modified vs modified; no pre-change oracle) | ACCEPTED. Director ran the decisive cross-implementation check: pre-change exporter (main checkout) vs flag-off worktree exporter, seed 777 / n 25 — **canonically IDENTICAL (4/4 artifacts)**, so no implementation bug; test-strength fix (pinned golden-fixture digests) returned to the T2 worker |
| W1-2 | MED | Probe measured control-config degeneracy at flat 100bb, but the control corpus runs with `--buyin-spread` — wrong runtime condition | ACCEPTED. Probe gains spread passthrough; degeneracy re-measured in spread mode; appendix updated. Returned to the T1 worker |

**Owner ruling (2026-08-07, mid-wave):** T1 found the §c axes cap decision degeneracy at
~0.54 (preflop mix tables are outside the axis registry) — the spec's 0.90
"near-deterministic" proxy is unreachable via registered dials. Owner ACCEPTED the
best-effort config (hash `3a64601c…`) with the 0.90 proxy RETIRED, replaced by a
**one-judge pre-screen**: before the full paid judging run, one vendor judges the control
bundle; if it isn't labeled "bot", stop and revisit. §d's own invalidation threshold
remains the in-protocol test. (Rejected alternatives: bespoke non-dial generator — extra
amendment + code; extending the axis registry — frozen registry + out of appetite.)

## Build wave 2 (T3 shared renderer) — dual review 2026-08-07

Claude refuter: **PASS** + 1 LOW. Its verification was substantive: traced the maker's
flagged reveal-depth deviation (read `HandState.board`, not action history) through
`engine._close_street` and BOTH producer paths — board is provably always exactly the
revealed streets at terminal state, deviation UPHELD; ran its own adversarial real-corpus
probe (real dev-DB human bundle read-only + real seeded self-play bundle): leak_check
clean, structural diff symmetric (formatting, vocabulary, positions, phrasing), preflop
fold-outs render zero board cards from both adapters. Its LOW ("out-of-scope edit to
test_buyin_spread.py") is **REJECTED — misattributed**: that edit was the T2 owner fixing
its own file (git_sha → volatile keys) on director routing, not the T3 maker.

Codex Sol: NEEDS-WORK, 3 findings:

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| W2-1 | HIGH | Malformed states don't fail fully closed — NaN money from a corrupt DB row would render "nan" (class tell); duplicate seat IDs accepted | ACCEPTED → full terminal-state invariant (unique seat/position permutations, finite non-negative money, valid globally-unique cards, board = full_board prefix, ledger consistency) + adversarial tests. Returned to T3 maker |
| W2-2 | MED | Renderer doesn't enforce the 30-hand payload grammar; leak_check misses `hand_no=`-style metadata forms and header order/uniqueness | ACCEPTED MODIFIED — maker's flexible size stays (6+6 dry run needs it); `expected_count` strict param added (judging path passes 30) + leak_check structural grammar + metadata-field patterns |
| W2-3 | MED | Cross-source identity test synthetic — never touches SQLite round-trip or the real playout | ACCEPTED MODIFIED — refuter's throwaway probe already demonstrated real-corpus convergence; converted to a permanent self-contained integration test (seeded real playout → model_dump_json TEXT round-trip vs live object; no dev-DB dependency) |

Also this wave: T3 maker FOUND a wave-1 branch defect (golden manifest digest included
`git_sha` — breaks every commit); fixed by the T2 owner (digest re-pinned `24a0b5f3…`).
Human session measured at 1,853 hands during T3's probe — ample for 40 windows.

## Build wave 3 (T4 corpus builder + blinding split) — dual review 2026-08-07

Refuter NEEDS-WORK (2) · Codex Sol NEEDS-WORK (5) → merged to 5 accepted items, all
returned to the T4 maker. Refuter's verification was decisive on two fronts: it
empirically tested the maker's admitted gap (control-config replay path: 120/120 hands
byte-match run_export at the real control seed) and independently rebuilt the real deck
twice (presentation.json byte-identical; real DB session `0650a019…`, N=1,853, 61 valid
candidate windows confirmed).

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| W3-1 | HIGH | **Focus-position trajectory side channel** (Codex; director-verified arithmetic): human bundles always focus seat 0 and tile by 30 (30 mod 9 = 3) → only 3 of 9 position-rotation phases; bot focus seats span all 9 → 6 phases are bot-only signatures in judge-visible position labels; the blinding assert can't see it | ACCEPTED — compute human phases from real data; constrain bot/control focus assignment into the human-observed phase set (blinding beats seat coverage if they conflict); payload-level no-single-class-phase test |
| W3-2 | MED | Missing first hand silently SHIFTS the window tiling (origin = min present row) — violates never-shift | ACCEPTED — authoritative canonical origin + reject-the-affected-window test |
| W3-3 | MED | Pinned T1 control hash not enforced; any config gets a normal _SUCCESS | ACCEPTED — protocol builds assert the full `3a64601c…` hash; explicit non-protocol flag marks dry-run decks in unblinding + _SUCCESS |
| W3-4 | MED | Replay↔export equivalence test too shallow (board/pot/street only, baseline path only) — the central "production policy" claim unguarded | ACCEPTED (merged refuter+Codex) — full per-hand field comparison + permanent control-path equivalence test (refuter's probe made repeatable) |
| W3-5 | LOW | derived_seeds["opaque-ids"] records a seed the build never uses directly (per-bundle key appended) — misleading for audit | ACCEPTED — per-bundle seeds or explicit derivation-rule record |

## Build wave 4 (T4-ext judge duplicates + T5 harness + T6 statistics) — refuter review 2026-08-07

Refuter (high pin, per approved plan — single reviewer this wave): NEEDS-WORK. It re-ran
all suites (153 wave tests; full suite 1,869 green), hand-re-derived every statistics
fixture (BA 5/6, AUC 31/36, d′ incl. extreme correction, the 3-judge Kish n_eff worked
example — all reproduce), and verified prompt fidelity byte-for-byte.

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| W4-1 | HIGH | **Harness never sends the hands.** `judge_pair` transmits only the pinned instruction template — `rendered_text` is used to extract the seat ID then dropped; no vendor would ever see a hand of poker; no test inspected the outbound prompt body. A full paid panel run would have judged nothing | ACCEPTED — rendered text appended after the verbatim template with a delimiter; tests now assert the wire prompt contains the bundle text. Returned to T5 maker |
| W4-2 | MED | Duplicate entries share their source's sha256 (byte-identical text) — a presentation.json holder can hash-collide their way to identifying up to 5 human bundles without unblinding.json | ACCEPTED MODIFIED — per-entry hashes salted with presentation_id (uniform rule); text-twin detection by direct comparison remains and is disclosed as inherent to the identical-stimulus design (judges never see the manifest). Returned to T4 maker |
| W4-3 | — | T6's two flagged formula ambiguities | RULED (refuter, director-confirmed): bootstrap pool = ≥3-usable bundles CORRECT (CIs must bracket the point estimates' population); n_eff over full deck ACCEPTABLE + one-line population disclosure added; ceil(4k/5) control-threshold generalization ACCEPTABLE (reproduces the pin at k=5) |

Verified clean: §d.3 prompt byte-verbatim; §A.2 preamble a separate system message in all
five adapter shapes; blinding guard recursive and real; control pre-screen needs no
unblinding data; resume idempotent; T5↔T6 interface seams match; vendor wire shapes
structurally correct (live-untested = disclosed limitation).

## Build wave 5 (T7 acceptance + renderer fix) — final gate 2026-08-07

During acceptance, T7 hit and correctly refused to route around a REAL defect: the
renderer's zero-chips test reused the 0.011 reconciliation tolerance, rejecting a legal
one-cent stack (1 occurrence per 1,500 spread hands; aborted ~26/30 master seeds incl.
the pinned 20260807). T7 refused seed-shopping (selection on content) and built a
clearly-labeled verification deck at an alternate seed instead. The T3 owner confirmed
engine semantics from source (engine _EPS=1e-9; a 0.01bb stack legally stays IN), fixed
the threshold (_ZERO_CHIPS=0.005), and caught two sibling instances — one of which had
been mislabeling the one-cent seat "(all-in)" in JUDGE-FACING text. Protocol deck then
built at the pinned seed: byte-identical twice, 86/86 payloads leak-clean, phase sets
matched, spread matched, the previously-aborting window selected and rendering correctly.

Final gate: refuter **PASS, 0 issues** (ran the dry run itself; live-tested every
execution-checklist command against the real protocol deck; amendments verified
character-for-character against §A and BASE_RATE_PREAMBLE). Codex Sol NEEDS-WORK, 8
findings, ALL ACCEPTED:

| # | Sev | Finding | Routed to |
|---|---|---|---|
| W5-1 | HIGH | Dry run builds 3+3 but spec Verify-by pins 6+6 | T7 (bump + rerun) |
| W5-2 | HIGH | Write-up requires per-judge balanced accuracy; analysis.json emits no per-judge deck statistics (§d.3 pins "per-judge statistics reported alongside") | T6 (per_judge section + tests) |
| W5-3 | MED | Scaffold says §§7.2–7.4 stay empty on invalid batch — but fail-closed EMITS diagnostics + completeness | T7 |
| W5-4 | MED | Three control-logic misstatements (weak-control direction asserted; pre-screen described as replacing the panel gate; slot-0 miss claimed to prove aggregate invalidity) | T7 |
| W5-5 | LOW | Checklist cwd is backend/ but names repo-root ./scripts/verify.sh | T7 |
| W5-6 | LOW | Dry-run report scrub drops the whole input_hashes line (masks nonvolatile hashes) | T7 (narrow) |
| W5-7 | LOW | Negative-money tightening unpinned by tests (-1.0 passes both thresholds); refuter independently noted the same gap | T3 (boundary cases) |
| W5-8 | LOW | Checklist claims a ~60-token output cap; only Anthropic has one (300), reason-length unenforced | T7 (reword) |

Process note: reviewer output adjudicated against `estimand-contract.md` §d and the cited
source files before acceptance; nothing folded on authority. The two independent reviewers
converged on the duplicate-bundle gap, the appetite problem, and the amendment-discipline
theme from different angles — consistent with prior slices' experience that convergent
findings are the real ones.

## Post-merge follow-on — panel amendment 2026-08-07-B (docs-only)

Owner ruling (2026-08-07, after both S6 PRs merged, BEFORE any judging): judge panel
recomposed from five one-per-vendor slots to **4 judges / 2 vendors** — Claude Sonnet +
Claude Opus (Anthropic), gpt-5.6-terra + gpt-5.6-sol (OpenAI). Recorded as estimand
contract **§g.3 amendment 2026-08-07-B** (poker-analytics), pre-judging, so full
preregistration validity is retained.

Verified before implementation (director, against code — not assumed):
- `detection_judge.parse_judges_arg` accepts repeated vendors; one key per vendor
  (`S6_JUDGE_<VENDOR>_KEY`) shared by same-vendor slots. **No code change needed.**
- `detection_analysis` generalizes to any k: control label conjunct `ceil(4k/5)` ⇒
  **4 of 4 (unanimous)** at k=4; the ≥3-usable bundle rule is an absolute §d pin ⇒ 3-of-4.
- `detection_corpus --judges 4` at build; default constant `JUDGE_SLOTS = 5` left
  untouched (historical), checklist passes the flag explicitly.
- Volume: 85 presentation entries, 82 per judge ⇒ 328 judged + 4 preflight = 332 calls.

Files touched (docs only): poker-analytics `estimand-contract.md` (§g.3),
`detection-pilot-s6.md` (panel §3.3, control rule, bias row 9, §7.1 row),
`FLYWHEEL-STATUS.md`; poker-coach `flywheel-s6-execution-checklist.md` (deck build flag,
2-key credentials, S6_JUDGES string, volume/cost, pre-screen note), `flywheel-s6.md`
(historical-reading banner), this ledger.

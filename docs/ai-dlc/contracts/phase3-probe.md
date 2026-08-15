# Contracts — phase-3 judge-bias probe (mapped 2026-08-15, contract-mapper)

**Bottom line: the probe is buildable by composing existing private functions, but it
must live entirely outside the live experiment's paths, its stimuli must satisfy the
renderer's engine-legality and the pinned 30-hand prompt, and the "no agent runs
judging" rule needs an explicit owner scoping ruling before an agent spends a cent.**

## The ten contracts that bind the implementation

1. **Live-experiment isolation (highest stakes).** `$S6_ROOT/judging/launch.json`
   (written 2026-08-15T00:40Z) and `responses/slot-0/B007.json` are live preregistered
   state. Same deck + same `--out` silently reuses the real immutable `launch.json` and
   writes real checkpoints. The probe uses its OWN `--deck` and `--out` directories,
   never `$S6_ROOT/deck` or `$S6_ROOT/judging`.
2. **Owner-only rule is unscoped.** `flywheel-s6.md` ("judging run = owner, real
   terminal") and the execution checklist ("judging is the one step no agent may run")
   literally cover any live judge call. Off-deck dev probes are an unaddressed gap —
   requires the owner ruling recorded in the phase-3 paperwork, not silent
   interpretation.
3. **No small-probe entry point exists.** `build_corpus()` is all-or-nothing. The probe
   composes `read_human_snapshot`, `enumerate_windows`, `validate_human_window`,
   `from_human`, `replay_run`, `from_bot`, `render_bundle`, `leak_check` directly.
4. **Non-deck human window must pin to the frozen snapshot.** `read_human_snapshot`
   computes `n_pinned` at call time and the owner's DB keeps growing; the probe must
   read `unblinding.json["pins"]["human"]` (`n_pinned`, `session_id`) and reproduce the
   deck's candidate enumeration, then select a VALID candidate NOT among the 40
   selected. Candidates (selected or not) are recorded in
   `unblinding.json["human_windows"]["candidates"]`.
5. **Position-phase constraint is manual outside `build_corpus`** (§3.2): human windows
   tile 30 hands over 9 seats → 3 rotation phases; an ad hoc bot focus seat outside the
   human phase set {BB, CO, UTG2} is a free class tell. Probe bot stimuli must use
   focus seats from the human phase set.
6. **"Rule-breaking" must stay engine-legal.** `detection_render._validate_terminal_state`
   raises `CanonicalHandError` on invalid hands. The control breaks poker *strategy*
   (hopeless calls, bets into unbeatable boards, fixed nonsense sizings via a custom
   action-selection function driving `apply()` in `app.domain.*`), never engine rules.
   A custom policy replaces `bot_decision(state, seat, pack, rng)` at the
   `detection_corpus.py:597` call shape; domain-core purity (no web/DB imports) applies.
7. **T1 identity re-asserted independently:** probe code must check
   `counterfactual.load_config(path).config_hash == PROTOCOL_CONTROL_CONFIG_HASH`
   itself; `build_corpus`'s check is unreachable from probe code.
8. **Leak audit is per-provenance.** `leak_check`'s forbidden-token list is built from
   real provenance (persona names, session_id, run ids, hashes). The probe builds an
   analogous list for its own stimuli before sending text to a vendor. Expect
   deliberate false positives (substring matching).
9. **Pinned texts are untouchable.** `JUDGE_PROMPT_TEMPLATE` + `BASE_RATE_PREAMBLE` are
   §d.3/§A.2-pinned verbatim and assert "30 consecutive hands" — probe stimuli are
   exactly 30 hands, prompt reused unmodified. `assert_no_label_bearing_keys` refuses
   any input with `class`/`label`/`is_control`/`source` keys — probe scratch manifests
   must avoid those names.
10. **Dry-run path exists free:** `call_stub` is deterministic and no-network — the
    probe's plumbing is verified end-to-end with the stub vendor before any paid call.
    `run_s6_owner.sh` is untouched; the probe is a separate entry point.

Full mapper narrative preserved in the session ledger; source of record for the live
state claims: the files themselves under
`docs/ai-dlc/research/persona-realism-artifacts/detection-s6/`.

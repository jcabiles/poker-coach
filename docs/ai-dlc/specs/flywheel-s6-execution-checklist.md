# S6 execution checklist — owner-run, real terminal

The S6 build (spec `flywheel-s6.md`) is finished; **judging is the one step no agent may
run.** API keys live in your environment only, never in a file, never in a repo, never in
an agent transcript. This is the exact sequence, copy-pasteable, in order.

Every command runs from the **real repo**, not a worktree:

```sh
cd ~/Documents/Github/poker-coach/backend
```

so the S6 branch must be merged (or checked out) in that clone first — `tools/detection_*`
and `tools/run_s6_dryrun.py` do not exist on `main` until then.

> ✅ **The protocol deck builds at the pinned master seed 20260807 — verified 2026-08-07,
> built twice, `presentation.json` byte-identical.** Historical note, kept because it
> explains a constant you will see in the renderer and a judgement call worth preserving:
> an earlier build ABORTED at this seed. `detection_render.py`'s "no chips behind" test
> reused the 2dp reconciliation tolerance `_EPS = 0.011`, which is larger than the smallest
> legal chip, so a seat holding exactly 0.01bb with status `in` — reachable under the §A.1
> integer-cent buy-in spread, occurring in 1 of the 1,500 bot hands — was rejected as
> malformed. Fixed by the renderer's owner (`_ZERO_CHIPS = 0.005`), which also corrected
> that same seat being mislabelled "(all-in)" in judge-facing text. **The seed was not
> changed to route around it** — picking a seed for the hands it excludes is a selection on
> content, exactly what the preregistration exists to prevent — and the deck built at
> 20260807 does contain that hand (bot window 8), rendered correctly.

---

## 1. Preconditions

- [ ] S6 branch merged/checked out in `~/Documents/Github/poker-coach`.
- [ ] **From the repo root** (`~/Documents/Github/poker-coach`, not `backend/` — every
      other command block in this file runs from `backend/`): `./scripts/verify.sh` green.
- [ ] The three §A amendments are recorded in
      `poker-analytics:docs/methods/estimand-contract.md` §g.2 **and committed**. They are
      pre-judging amendments; recording them after the first judged bundle destroys that
      property permanently.

## 2. Build the protocol deck (~5 seconds; no network, no API keys)

```sh
cd ~/Documents/Github/poker-coach/backend
export S6_ROOT="../docs/ai-dlc/research/persona-realism-artifacts/detection-s6"
.venv/bin/python -m tools.detection_corpus build \
  --master-seed 20260807 \
  --db-path data/poker_coach.db \
  --judges 4 \
  --out-dir "$S6_ROOT/deck"
```

**`--judges 4` is required** — the §g.3 panel amendment (four judges from two vendors)
changed the slot count; the tool's built-in default is still the historical 5.

**Pinned seeds — use these exact values, do not improvise:** master `20260807`,
per-judge order `20260807`, bootstrap `20260807`. The master seed is the deck's identity:
a different one selects different windows, which is a different experiment, not a retry.

Check the printed `_SUCCESS` body before going on:

- [ ] `counts` = `{"human": 40, "bot": 40, "control": 1}`
- [ ] `presentation_entries` = 85 (81 bundles + one duplicate per judge)
- [ ] `non_protocol` = `false` — `true` means the control config is not the pinned one and
      the deck is NOT the protocol deck
- [ ] `judge_slots` = 4

**Your deck may not be byte-identical to the acceptance build, and that is by design.**
The human corpus is re-pinned at build time (§d): if the Simulate session has grown since
2026-08-07, `n_pinned` rises, more candidate windows exist, and the seeded selection lands
elsewhere. A rebuild is only expected to be byte-identical to ITSELF — same seed, same DB
state. (For traceability, the acceptance build at this seed — made pre-amendment with the
then-current 5 judge slots, so your 4-slot build differs by design — was `n_pinned` 1853,
61 candidate human windows, `presentation.json` sha256
`da1990192232e02df18864a99a0bb54bd4fbee07c7e748128daa51a1545bdccc`.)

The deck directory is gitignored. It holds owner hand data and the unblinding key: never
push it, never paste its contents anywhere.

## 3. Credentials — two environment variables

**Panel per §g.3 amendment 2026-08-07-B** (recorded in
`poker-analytics:docs/methods/estimand-contract.md`, pre-judging): four judges from two
vendors — Claude Sonnet + Claude Opus (Anthropic) and gpt-5.6-terra + gpt-5.6-sol
(OpenAI). Both same-vendor slots share ONE key; the harness maps one key per vendor.

Set these in the shell you will run judging from. `export` only; nothing is read from a
file.

| Env var | Vendor (2 judge slots each) | Where the key comes from |
|---|---|---|
| `S6_JUDGE_ANTHROPIC_KEY` | Anthropic (Claude Sonnet + Claude Opus) | console.anthropic.com → API keys |
| `S6_JUDGE_OPENAI_KEY` | OpenAI (gpt-5.6-terra + gpt-5.6-sol) | platform.openai.com → API keys |

```sh
export S6_JUDGE_ANTHROPIC_KEY=...
export S6_JUDGE_OPENAI_KEY=...
```

(Both vendors also accept an optional `S6_JUDGE_<VENDOR>_BASE_URL` override and otherwise
use the vendor default. The Google/Meta/DeepSeek variables from the pre-amendment panel
are no longer used.)

Then pin the four model IDs you are actually buying. §d.3 declares this recording
amendment-exempt (providers rotate snapshots); **substituting a VENDOR or a MODEL FAMILY
is a further amendment — the current panel composition is itself the recorded §g.3
amendment.** Slot order is fixed by this string and must not change between the pre-screen
and the full run:

```sh
export S6_JUDGES="anthropic:<sonnet-model>,anthropic:<opus-model>,openai:gpt-5.6-terra,openai:gpt-5.6-sol"
```

(Confirm the current Anthropic model IDs at execution time — as of 2026-08-07 they are
`claude-sonnet-5` and `claude-opus-5`.)

## 4. Preflight (automatic, one cheap call per judge slot)

There is no separate preflight command — the first `run` invocation does it: every judge
slot is exercised once with an off-protocol one-word prompt (so each vendor's shared
credential is hit twice, once per model), and requested vs
provider-resolved model IDs are written to an immutable `launch.json`. It happens inside
step 5, so **a credential problem surfaces on 4 cheap calls, not 328 expensive ones.**

`launch.json` pins the deck's `presentation.json` hash. A later run against a different
deck at the same output directory is refused, not silently re-launched.

## 5. Control pre-screen — ONE bundle, ONE vendor, before any spend

Find the control bundle's presentation ID. It is in the **unblinding** manifest (the file
the judging harness cannot read), as the one bundle whose `is_control` is `true`:

```sh
.venv/bin/python -c "import json;d=json.load(open('$S6_ROOT/deck/unblinding.json'));print(next(b['presentation_id'] for b in d['bundles'] if b['is_control']))"
```

Judge it with slot 0 only:

```sh
.venv/bin/python -m tools.detection_judge run \
  --deck "$S6_ROOT/deck" \
  --judges "$S6_JUDGES" \
  --order-seed 20260807 \
  --out "$S6_ROOT/judging" \
  --only-slot 0 \
  --only-presentation-id <CONTROL_ID>
```

Read the verdict:

```sh
.venv/bin/python -c "import json;r=json.load(open('$S6_ROOT/judging/responses/slot-0/<CONTROL_ID>.json'));print(r['status'], r['parsed'])"
```

**STOP RULE — the control must be labelled `bot`.** If `parsed['label'] != 'bot'` (or the
status is not `ok`), **stop and revisit; do not run step 6.**

This stop is deliberately **stricter than the registered rule, and is not a prediction of
it.** §d.2 invalidates a batch only when the panel-aggregate confidence-human is < 50 AND
≥`ceil(4k/5)` judges label the control "bot" (4 of 4 at the amended k=4, §g.3) — a
conjunctive rule over the whole panel, which one slot's answer alone does not decide at
pre-screen time. What a slot-0 miss establishes is only that the cheapest available signal
came back wrong, which is enough to stop spending on the other 327 calls and look again.
It is an operational spend-stop, not evidence that the aggregate rule would have failed.
(One sharpening at k=4: checkpoints are per (bundle, judge) and terminal, so the
pre-screen's slot-0 control response IS the full run's slot-0 control response. With the
label conjunct now unanimous, a slot-0 "human" on the control would already guarantee
batch invalidation — at k=4 the pre-screen stop rule and the registered rule happen to
agree on that one slot, which was not true at k=5.)

If it does fire, record that it fired and everything you did next — the pilot write-up has
a slot for exactly this (`poker-analytics:docs/methods/detection-pilot-s6.md` §5), because
any decision made after seeing a judge's output is a researcher degree of freedom and has
to be visible.

## 6. Full run

```sh
.venv/bin/python -m tools.detection_judge run \
  --deck "$S6_ROOT/deck" \
  --judges "$S6_JUDGES" \
  --order-seed 20260807 \
  --out "$S6_ROOT/judging"
```

**Volume:** each judge sees all 81 deck+control bundles plus **its own** duplicate = 82
entries (not all four duplicates — each duplicate is routed to one slot). So
**82 × 4 = 328 judged calls**, plus 4 preflight calls = **332 total**.

**Cost band (recompute at today's prices — this is arithmetic, not a quote):** the rendered
30-hand bundles run ~21,000 characters ≈ **5.9k input tokens per call**. That is ~**0.48M
input tokens per judge slot**, ~**0.97M per vendor** (two slots each), ~**1.9M across the
panel**. At flagship input pricing, expect **single-digit to low-tens of US dollars for
the whole panel** — the most expensive model (Claude Opus) dominates.

Output is a small JSON object (label, confidence, a short reason), so **expect** ~60 tokens
per call, ~20k across the panel — negligible against input cost. Treat that as an
expectation, **not a cap**: only the Anthropic adapter sends a hard output limit
(`max_tokens: 4096` — raised from 300 on 2026-08-14 because current Anthropic models
think by default at provider-default effort and thinking tokens count inside the cap;
expect real output cost from thinking tokens, roughly 1–2k per Anthropic call), the
OpenAI adapter sets none, and the prompt's "≤50 words" reason
limit is instruction text that the response parser does not enforce. A verbose vendor
therefore costs more than the estimate rather than being truncated at it.

**Resume after a failure — just re-run the identical command.** Checkpoints are per
(bundle, judge) and atomic; `ok` and `malformed-final` are terminal and are skipped, so
you are never billed twice for a completed pair. `transport_failed` pairs are non-terminal
and are retried. Bundle order and duplicate selection are frozen in
`order/slot-*.json` on the first run and reused verbatim, so a resume cannot change the
schedule. Do **not** delete `launch.json` or the `order/` files to "start clean" — that
would re-randomize the design mid-experiment.

Sanity-check completion before analysis:

```sh
cat "$S6_ROOT/judging/judging_complete.json"
```

- [ ] each slot: `ok` = 82, `malformed` = 0, `transport_failed` = 0 (any shortfall is
      handled by the analysis module's completeness rules, but investigate first)

## 7. Analysis

```sh
.venv/bin/python -m tools.detection_analysis run \
  --deck "$S6_ROOT/deck" \
  --judging "$S6_ROOT/judging" \
  --bootstrap-seed 20260807 \
  --out "$S6_ROOT/analysis"
```

Writes `analysis.json` (machine-readable) and `report.txt` (plain-text tables). Both are
deterministic — no wall-clock field in either — so re-running the analysis on the same
judging output reproduces both byte for byte.

**Control invalidation runs first and fails closed.** If `batch_valid` is `false`, the
module emits diagnostics and completeness only, and **no deck statistic exists** — that is
the designed outcome, not a bug, and the pilot then reports a shakedown with no number.

## 8. Write-up

Fill `poker-analytics:docs/methods/detection-pilot-s6.md` §7 from `analysis.json` only —
never by reading rendered hand text, and never by hand-computing a number the module
already produces. Sections 1–6 and 8–10 of that document are already written and need no
edits. Then tick the roadmap's S6 box.

**Never pushed, ever:** the deck directory (`presentation.json`, `unblinding.json`, raw
responses) contains owner hand data and the unblinding key. What travels is the write-up
and the structured numbers in it.

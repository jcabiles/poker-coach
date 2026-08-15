# Phase-3 gate — decision matrix and ruling draft (DRAFT, awaiting owner ratification)

**Bottom line: the recommended ruling is "improve the bots for believability, steered by
cheap checks, with the detection test repaired once and run once as the finale" — but
the ruling is conditional on a 4-cent probe proving the judge can distinguish anything
at all. This document is the preregistered decision matrix the roadmap requires for
this gate; the owner ratifies or overrules it, and the outcome-recording section at the
bottom is filled at ratification time.**

## 1. The decision being made

The bot-realism flywheel reached its phase-3 gate (fix-versus-overhaul, owner-only).
Inputs available: the S5 close-out (reachability INCONCLUSIVE — ladder stages 2–3 never
ran), the S6 detection shakedown (instrument's control failed twice; sensitivity and
cost both in question), the 2026-08-05 re-measure (roster 4.8/10, adjudicated defect
list), and the owner's 2026-08-14 goal ruling: **portfolio is the priority, and the
portfolio hinges on bots that feel believable.**

## 2. The matrix

| Option | What it means | Delivers the goal (believable bots + defensible story)? | Cost / risk |
|---|---|---|---|
| **A. Fix current bots (RECOMMENDED)** | Keep the dial/pack architecture; fix the adjudicated believability defects in priority order (de-robotization first); cheap statistical checks steer; one repaired finale detection run | Yes, if the probe shows the judge can discriminate; the story arc (measure → shakedown → fix → finale) is complete and honest | 2–3 weeks part-time; residual risk the finale is unflattering — covered by the pre-written claim ladder |
| **B. Overhaul (new bot architecture)** | Rebuild decision-making beyond the dial space (the S5 evidence that dials may not reach the target was one trigger for this gate) | Maybe better bots eventually, but blows the appetite (multi-month), and the portfolio story stalls unfinished | Far exceeds 2–3 weeks; highest risk of an abandoned arc |
| **C. Re-aim at human-likeness without detection** | Drop the detection metric; steer by similarity to human aggregates + owner play only | Bots may improve, but the story loses its strongest proof point and its measurement chapter ends on a broken instrument | Cheapest; weakest portfolio close |
| **D. Stop here (shakedown is the ending)** | Close the initiative on the S6 shakedown; resume teaching features now | Honest but incomplete — "we built an instrument and it failed" without the redemption arc; bots stay at 4.8/10 | Zero further cost; goal explicitly unmet |

**Recommendation: A**, with C as the pre-declared fallback **if the probe fails** (see
§3): if the judge cannot separate even a rule-breaking bot from a human anchor, the
detection instrument is retired with evidence and the plan degrades to C plus the owner
blind play-test as the believability verdict.

## 3. The probe that gates the ruling (pre-registered here, before it runs)

One judge (claude-sonnet-5, cheapest slot), four 30-hand stimuli, all OFF-deck:

| Stimulus | Known quality | Expected verdict if judge works |
|---|---|---|
| Rule-breaking scripted bot (new) | cartoonishly bad | bot, high confidence |
| T1 dial control (the one that failed) | weak-bad | bot, at least weakly |
| Current production-pack bot | the quality range that matters | informative either way |
| Owner human window (non-deck candidate) | human | human |

Interpretation, fixed in advance:
- **Judge separates rule-breaker from human anchor** → instrument has ≥ cartoon-level
  sensitivity → ruling A proceeds; the T1 and production verdicts calibrate where the
  discrimination threshold sits.
- **Judge calls everything human (or everything bot)** → the §d.1-predicted bias is
  real at panel level too until proven otherwise → detection is retired as finale;
  fallback C+play-test activates. No further paid judging.
- **Any outcome not covered by the two branches above** (exhaustive catch-all: e.g.
  rule-breaker caught but human anchor also called bot, or mixed/malformed verdicts) →
  escalate to owner with the raw verdicts; no unilateral interpretation.
- Budget: ≤40¢ including iteration on probe plumbing. Every call logged; every verdict
  recorded in the ledger regardless of outcome.

## 4. Scope freezes this ruling activates (Option A)

- Improvement order: (1) de-robotization of deterministic tells (sizing jitter,
  whitelist removal), (2) invest-then-fold lines, (3) calldown — item 3 is the scope
  valve, cut first if the appetite runs out.
- **Cut entirely from this phase:** engine/stack-handling work (Track-E architecture;
  re-creates a class tell §g.2 amendment 1 exists to remove).
- Per-change gates (free): archetype-separation floor vs the frozen pre-fix roster +
  determinism check; owner sessions are a qualitative tell-finder, never a numeric
  target.
- Exactly ONE finale detection run. A second would require a recorded amendment
  disclosing why, written before it runs.
- Full preregistration rigor continues; all changes consolidate into ONE amendment
  (see `phase3-consolidated-amendment-draft.md`), then the protocol freezes until the
  finale.
- **Agent-execution scoping (owner ruling, closes the contract gap found 2026-08-15):**
  the preregistered deck judging remains owner-only in a real terminal; OFF-deck dev
  probes may be agent-run under a recorded deviation with an explicit budget cap. The
  key file `~/.config/s6-probe-keys.sh` is deleted and both keys rotated when probe
  work ends.

## 5. Ruling record (filled at ratification)

- Ruling: [x] **A** [ ] B [ ] C [ ] D — date: **2026-08-15** (owner, in-session,
  after reviewing the probe outcome below)
- Probe outcome attached: **RAN 2026-08-15 — branch 1 (proceed).** Rule-breaker
  caught (bot, conf_human 3, tells named); human anchor human (62); T1 human (62 —
  too-lifelike confirmed on a fresh window); production bot human (65). Full log:
  `docs/ai-dlc/ledger/phase3-probe.md`.
- Owner notes: ______

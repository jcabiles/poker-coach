> ⚠️ **CORRECTIONS from an independent audit (2026-08-03, director-commissioned; full adjudication
> in `ledger/r9-loosefit.md` rows B-8R, B-11, B-12, B-13, B-14). Read these BEFORE the body.**
>
> 1. **§8 surprise 2 and the §6 "load-bearing" sentence are WITHDRAWN.** The "gate-posture FtC
>    secant is −0.345, 2.3× the True-posture slope" is an n=4,000 artifact — its own 1σ is
>    ±0.1907, larger than the effect claimed. Re-measured over the same two lever points at
>    n=32,000: **−0.195 ± 0.064**, inside the feasibility study's −0.15…−0.19 band; the posture
>    difference is **0.91σ, not resolvable**. Anchor-seeded FtC steps are NOT shown to be unsafe
>    at the gate posture.
> 2. **The paired noise bands are ~1.18× too narrow** (corr(nit,tag) = −0.387 across 56 seeds;
>    the analytic σ is right per-persona). Every σ-unit figure below should be divided by ~1.18
>    and every extrapolated n multiplied by ~1.4: §5.3's 4.63σ → **3.9σ**, n ≥ 53,800 →
>    **≈75,000**; §5.5's n ≈ 405,000 → **≈566,000**. Direction of every conclusion is unchanged
>    and strengthened.
> 3. **§2's 4k/16k/32k series is a nested prefix of ONE run**, not three measurements. Independent
>    evidence (a second 32k seed plus a 56-seed ensemble) puts the base gap at
>    **+0.0087 ± 0.0063, 95% CI [−0.0035, +0.0210]** — the premise value −0.063 is 11.5σ away.
>    §8 surprise 5 stands and is strengthened.
> 4. **§5.3's "1.7σ below its own stable value" is wrong** — against the disjoint remainder of the
>    same 32k run it is **−3.17σ**. The over-read is larger than reported.
> 5. §5.3's n ≥ 53,780 is arithmetically 53,799.5 (0.04 % slip, immaterial). Both extrapolations
>    hold the measured effect fixed and n ∝ 1/effect², so a ±1σ revision of the gap alone swings
>    §5.3's n between **36,400 and 87,600** — quote them as ranges.
>
> Everything else re-ran byte-exact: every §2, §5.1 and §5.3 raw reading reproduced exactly, and
> both unreachability extrapolations are arithmetically sound. The blocking constraints in §4 were
> separately re-confirmed by real pytest (nit floor bracketed 0.38 FAIL / 0.42 pass, deterministic
> across repeat runs; the tag pin reproduced with a written-in-advance prediction).

# T1 — R9-LOOSEFIT instrumentation + gate-posture fit: MEASUREMENT REPORT

status: **instrument DELIVERED and verified · fit BLOCKED — no operating point satisfies the
spec's pre-registered acceptance criteria together with the existing HARD gates.**
worktree `/private/tmp/claude-501/wt-r9-loosefit` (branch `feat/persona-realism-r9-loosefit`,
base `b63dfaa`) · packs restored byte-for-byte · every reading below from a file, never a pipe.

---

## 0. Headline

1. The shares accessor is built, the six-tuple API is untouched, cache identity is preserved, and
   **every base reading is byte-identical** (full suite 1416 passed / 1 skipped, same as base).
2. The spec's seed **nit 0.08 is not merely off-target, it is illegal**: it fails a HARD gate the
   contract map never listed — `test_fold_to_bet_respects_alpha_ceiling[nit]`, measured by real
   pytest (`nit bluff-catcher fold 0.4128 vs α ceiling 0.2481` at ⅓-pot).
3. Four further HARD gates outside the contract's blast radius move under a nit/tag refit; two of
   them (`test_elasticity_split_faithful_decomposition_byte_identical`, four
   `test_one_pair_raise_damped_facing_raise_pre_river[…-tag]` pins) make **tag's
   `call_looseness` un-editable without a spec decision**, and one
   (`test_r9d_s5_fold_rate_rise_follows_the_defensible_ladder`, R9-DEFENCE-a, merged 5 days ago)
   **floors nit's `call_looseness` at ≈0.42**, far above the α floor of ≈0.32.
4. With tag frozen, the spec's own criteria 2b (`lag < tag` margin ≥ 0.035) and 2c (lag WTSD
   margin ≥ 0.02) are **mutually exclusive** — and *both already fail at HEAD*.
5. Even ignoring 3–4, the best gap reachable is **+0.077 FtC points = 4.6 σ_gap at n = 32,000**,
   and the pre-registered symmetric T_sep rule needs **≥ 6 σ_gap** → n ≈ 53,800 minimum
   (≈ +5 min of CI). **G-RS-ii is worse: the measured absolute-raise fall is 0.84 σ; 3 σ needs
   n ≈ 405,000.**

Numbers for all of this below. T2 should not be started against any value in this report until
the owner rules on §7.

---

## 1. The instrument

### 1.1 What was added (`backend/tests/test_personas_postflop.py`, only file touched)

| element | where | what |
|---|---|---|
| `HandResult.facing_nodes` | `:2043` region | `(seat, action, spr_committed)` per postflop decision at a FOLD-LEGAL node |
| recording block | in `_play_hand`'s postflop branch, right after `log.append` | 5 lines, no rng |
| `FacingShares` NamedTuple | above the cache | `raise_abs`, `raise_share`, `facing_n`, `continue_n` |
| `_persona_stats_record(packs, persona, n, context_aware)` | ex-`_persona_stats` body | one play loop, returns the 2-element record `(stats6, shares)` |
| `_persona_stats(...)` | new thin wrapper | returns `record[0]` — the **same object** every hit |
| `_persona_stats_shares(...)` | new sibling | returns `record[1]` |

### 1.2 The cache-identity decision (the trap)

`test_stats_caches_are_pack_content_keyed` asserts `_persona_stats(packs,"tag",n) is base` at
three points. The cached VALUE is therefore the record `(stats6, shares)` — **the six-tuple is
built once and stored as element 0**, and both accessors return a stored element, never a freshly
sliced tuple. A `record[:6]` design would have built a new tuple per hit and failed on identity.
`_STATS_CACHE.pop/restore` at `:3626` is unaffected (it round-trips the record).

Zero call-site edits: the five positional unpackers (`:5644,:5662,:5681,:5742,:5774`) and the
star-safe `:3551` still see exactly six values.

### 1.3 Committed-node predicate (disclosed in the accessor docstring)

Excluded on the **SPR leg alone** — `stack_bb / pot_bb <= pf.spr_commit`
(`personas_postflop.py:1080`) — evaluated on the same pot/stack the sampler was handed. The
engine additionally requires `value_commit` (made/draw) before applying `_commit_transform`, so
this is a **conservative superset**: it can under-state the lever's reach, never invent it. The
harness deliberately does not carry a second copy of the `value_commit` taxonomy.

**How much it drops** (base packs, gate posture, n = 3,000, tested seats only):

| persona | fold-legal decisions | SPR-committed | excluded fraction |
|---|---|---|---|
| nit | 592 | 165 | **0.2787** |
| tag | 1109 | 632 | **0.5699** |
| lag | 1650 | 1072 | **0.6497** |

That is a big number and it retro-justifies contract §4: the feasibility study's AF figures were
aggregated over a subset in which more than half of tag's and two-thirds of lag's facing
decisions are lever-inert.

### 1.4 Proof the base readings did not move

- `-k "byte_identical or caches_are_pack_content_keyed or postflop_bands or wtsd_ordering or
  fold_to_bet"` → **59 passed, 1 skipped, exit=0** (`t1-nomove.txt`) — `_GOLDEN_STATS_N200` and
  every band green with the accessor present and `content/` unmodified.
- Full backend suite → **1416 passed, 1 skipped, 274.04s, exit=0**
  (`t1-fullsuite-accessor.txt`), identical to the pre-branch base count.
- `ruff check .` → All checks passed.

### 1.5 Secondary instrument (decision-level replica)

A read-only replica of the `fold_by_size` / `catcher_fold_by_size` module fixtures (same spots,
same per-cell seeds). **Validated byte-exact against pytest**: at nit `call_looseness` 0.08 the
replica returns catcher-fold 0.4128 at ⅓-pot and pytest's failure message reports 0.4128. ~0.27 s
per persona-row, which is what made the constraint scan affordable.

---

## 2. Gate-posture base readings (`context_aware=False` — the posture every CI gate judges at)

| n | persona | AF | FtC (n) | WTSD (n) | raise_abs (facing_n) | raise_share (continue_n) |
|---|---|---|---|---|---|---|
| 4,000 | nit | 1.30342 | 0.25926 (135) | 0.66702 (943) | 0.13311 (586) | 0.19307 (404) |
| 4,000 | tag | 2.27675 | 0.32226 (301) | 0.60974 (1581) | 0.25741 (641) | 0.38372 (430) |
| 4,000 | lag | 2.59488 | 0.30417 (480) | 0.57877 (2374) | 0.29751 (763) | 0.45491 (499) |
| 16,000 | nit | 1.28155 | 0.29299 (628) | 0.65658 (3800) | 0.12602 (2452) | 0.18134 (1704) |
| 16,000 | tag | 2.25398 | 0.30495 (1151) | 0.59678 (6391) | 0.24680 (2581) | 0.36338 (1753) |
| 16,000 | lag | 2.65709 | 0.32117 (1918) | 0.57409 (9502) | 0.30971 (3006) | 0.46855 (1987) |
| 32,000 | nit | 1.28300 | 0.29823 (1301) | 0.65516 (7618) | 0.13231 (4996) | 0.19044 (3471) |
| 32,000 | tag | 2.24366 | 0.29537 (2309) | 0.60030 (12737) | 0.24427 (5146) | 0.35720 (3519) |

**Base gap FtC(nit) − FtC(tag):** −0.06300 (n=4k, 3σ 0.13904) · −0.01196 (16k, 3σ 0.06801) ·
**+0.00287 (32k, 3σ 0.04753)**. The ledger's "−0.063" is a small-n fluctuation; at stable n the
base is a **clean statistical tie**, matching the feasibility report's −0.0121 at 48k/True. Every
posture agrees that nit and tag are indistinguishable defenders today.

### Base at `context_aware=True`, n = 4,000 (the other posture)

| persona | AF | FtC (n) | WTSD (n) | raise_abs (n) | raise_share (n) |
|---|---|---|---|---|---|
| nit | 1.44719 | 0.29121 (182) | 0.62857 (945) | 0.13043 (598) | 0.19355 (403) |
| tag | 2.14538 | 0.27698 (278) | 0.61407 (1578) | 0.24730 (647) | 0.35088 (456) |
| lag | 2.45787 | 0.32979 (470) | 0.57313 (2434) | 0.31266 (758) | 0.47024 (504) |

### Two frozen-band facts that HEAD already violates

- **lag WTSD 0.57877 vs the 0.59 ceiling → margin 0.0112**, below the spec's own 0.02 rule (2c).
- **`lag < tag` fold margin 0.0224** on the ordering fixture, below the spec's 0.035 rule (2b).

Criteria 2b/2c are therefore not "keep what we have" — they are **repairs the fit must perform**.

---

## 3. Solo ladders at the gate posture (n = 4,000, `ca=False`, other two at anchor)

| persona | cl | AF | FtC (n) | WTSD (n) | raise_abs | raise_share | ½-pot fold (replica) |
|---|---|---|---|---|---|---|---|
| nit | 0.08 | **2.51980 ✗ band top 2.4** | 0.66242 (157) | 0.47639 (932) | 0.08813 | 0.25789 | 0.7640 |
| nit | 0.32 | 1.45060 | 0.42763 (152) | 0.60905 (972) | 0.12693 | 0.20904 | 0.5660* |
| nit | 0.34 | 1.40647 | 0.43373 (166) | 0.61452 (978) | 0.11667 | 0.18919 | 0.5536 |
| nit | 0.38 | 1.45833 | 0.42667 (150) | 0.62435 (961) | 0.10603 | 0.17737 | 0.5352 |
| nit | 0.45 | 1.33705 | 0.35862 (145) | 0.61241 (983) | 0.10169 | 0.16438 | 0.5064 |
| nit | 0.60 | 1.30342 | 0.25926 (135) | 0.66702 (943) | 0.13311 | 0.19307 | 0.4480 |
| tag | 0.52 | 2.38881 | 0.30717 (293) | 0.60815 (1595) | 0.24127 | 0.37717 | 0.4104 |
| tag | 0.56 | 2.40181 | 0.32423 (293) | 0.60491 (1587) | 0.24721 | 0.38462 | 0.3800 |
| tag | 0.60 | 2.27675 | 0.32226 (301) | 0.60974 (1581) | 0.25741 | 0.38372 | 0.3720 |
| tag | 0.63 | 2.16713 | 0.34007 (297) | 0.60655 (1558) | 0.25920 | 0.38584 | 0.3592 |
| tag | 0.70 | 2.34776 | 0.26316 (266) | 0.61742 (1550) | 0.26817 | 0.39241 | 0.3536 |
| lag | 0.40 | 2.78711 | 0.37768 (466) | 0.54066 (2410) | 0.28000 | 0.45781 | 0.4024 |
| lag | 0.47 | 2.70829 | 0.37168 (452) | 0.55728 (2383) | 0.26852 | 0.41770 | 0.3840 |
| lag | 0.50 | 2.74062 | 0.34012 (491) | 0.56265 (2442) | 0.30229 | 0.47458 | 0.3672 |
| lag | 0.55 | 2.59488 | 0.30417 (480) | 0.57877 (2374) | 0.29751 | 0.45491 | 0.3496 |
| lag | 0.62 | 2.50803 | 0.28421 (475) | 0.58709 (2354) | 0.31233 | 0.44297 | 0.3296 |

\* interpolated; every other ½-pot number is a direct replica reading. Fixture 1σ ≈ 0.0137.

**Key shape:** nit's FtC **saturates** — 0.4276 / 0.4337 / 0.4267 at cl 0.32 / 0.34 / 0.38 are one
value inside noise; the whole gain is spent by 0.38 and nothing is bought by going tighter.
Confirmed at n = 32,000 jointly: nit FtC 0.40016 at cl 0.32 vs 0.39583 at cl 0.38 (Δ = 0.0043,
σ ≈ 0.017). Tightening nit below ~0.38 buys **separation nothing** and **α margin nothing**.

---

## 4. The blocking constraints, each measured with the real gate

### 4.1 α ceiling — `test_fold_to_bet_respects_alpha_ceiling[nit]` (HARD, zero tolerance, 6 personas)

Not in `contracts/r9-loosefit.md` §1. It IS `call_looseness`-sensitive: the fold merit is
untouched while `looseness` scales CALL and `rscale` scales RAISE, so tightening drives the
bluff-catcher fold share straight at the ceiling.

Real pytest at the spec seed (nit 0.08 / tag 0.63 / lag 0.62):
`FAILED … α ceiling — nit bluff-catcher fold 0.4128 vs the balanced-villain α ceiling 0.2481`.

Replica scan of nit's minimum α margin over the four sizes:

| cl | 0.30 | 0.32 | 0.34 | 0.36 | 0.38 | 0.40 | 0.45 | 0.50 | 0.60 |
|---|---|---|---|---|---|---|---|---|---|
| min margin | **−0.0027** | +0.0197 | +0.0301 | +0.0381 | **+0.0437** | +0.0549 | +0.0653 | +0.0837 | +0.1077 |

**α floor: `call_looseness`(nit) ≳ 0.31.** (Binding cell is ½-pot at every point ≥0.30.)

### 4.2 R9-DEFENCE-a's ladder — `test_r9d_s5_fold_rate_rise_follows_the_defensible_ladder`

Asserts `nit > tag > {lag, fish, maniac} > station` on the **fold-rate RISE** the line damp
produces. Its own docstring explains why it is `call_looseness`-coupled: "probability-space
ordering differs from the λ ordering because **base continue rates differ**". Tightening nit cuts
its base continue rate, so the same multiplicative damp yields a smaller probability-space rise.

Real pytest, nit-only edits (tag/lag at anchor):

| nit cl | 0.38 | 0.40 | 0.42 | 0.45 | 0.50 | 0.55 | 0.60 (base) |
|---|---|---|---|---|---|---|---|
| verdict | FAIL | FAIL | pass | pass | pass | pass | pass |

At nit 0.38 the measured rise table is
`{station 0.0041, lag 0.0290, nit 0.0312, maniac 0.0347, fish 0.0414, tag 0.0856}` — nit has
fallen from its base 0.1463 to 0.0312 and is now **below tag**, inverting the ladder. It is also
within 0.0012 of the literal floor `_R9D_S5_NIT_RISE_FLOOR = 0.03` asserted by the companion gate.

**R9-DEFENCE-a floor: `call_looseness`(nit) ≳ 0.42, and ≥ 0.45 for any margin.** This dominates α.

### 4.3 tag is un-editable — two independent gates

- `test_elasticity_split_faithful_decomposition_byte_identical` (`:1321`) builds an "opted" copy
  of the **shipped tag pack** with `call_looseness = stickiness` and asserts a byte-identical
  normalized distribution. tag authors `stickiness: 0.6` and `call_looseness: 0.6`, so the test is
  a **hidden pin that tag's shipped `call_looseness` must equal tag's `stickiness`**. Measured at
  tag 0.52: `{CALL 0.08483, FOLD 0.91517} != {CALL 0.09662, FOLD 0.90338}`.
- `test_one_pair_raise_damped_facing_raise_pre_river[{flop,turn}-{mid,top}-tag]` ×4 — exact
  `abs=5e-4` pins on tag's shipped normalized P(RAISE) (0.1871 / 0.3078). Measured at tag 0.52:
  0.17813 and 0.30347. All four fail.

Attribution proven by single-persona pytest runs: these five fail on a **tag-only** edit and on
nothing else.

### 4.4 The remaining fallout is re-recordable, but the spec does not name it

Single-persona attribution (real pytest, three runs):

| gate | nit-only 0.38 | tag-only 0.52 | lag-only 0.50 | status |
|---|---|---|---|---|
| `test_limper_coverage_fires_on_organic_play` | FAIL | FAIL | FAIL | sanctioned re-record ("RE-RECORDED for <slice>" precedents) — **not in files-to-touch** |
| `test_coverage_never_regresses` | pass | pass | FAIL | documented `_record()` protocol — **not in files-to-touch** |
| `_GOLDEN_STATS_N200` | — | — | — | in files-to-touch (T4) |

### 4.5 The joint feasibility contradiction

With tag pinned at 0.6 by §4.3, and the fixture separable per persona:

- criterion 2b `lag < tag` margin ≥ 0.035 ⇒ lag ½-pot fold ≤ 0.3720 − 0.035 = 0.3370 ⇒ **lag ≥ ≈0.58**
- criterion 2c lag WTSD ≤ 0.59 − 0.02 = 0.5700 ⇒ (lag WTSD 0.5627@0.50, 0.5788@0.55) ⇒ **lag ≤ ≈0.50**

**Empty.** Only a tag move opens it (tag 0.52 ⇒ ½-pot fold 0.4104 ⇒ lag ∈ [≈0.47, ≈0.50]), and
tag cannot move. Both criteria also fail at HEAD, so this is not a regression introduced by a
candidate value — it is a pre-existing conflict the spec's criteria expose.

---

## 5. The best candidate measured, and why it still does not close

**nit 0.38 / tag 0.52 / lag 0.50** — the only point found that keeps every band, ordering, α,
WTSD-ordering and monotonicity gate green *and* satisfies criteria 2b/2c. Real full-suite pytest
at these values: **1407 passed, 9 failed** — the 9 being exactly `_GOLDEN_STATS_N200` (sanctioned),
the two re-recordable stream fixtures (§4.4), the five tag gates (§4.3) and the R9-DEFENCE-a
ladder (§4.2). Bands, ordering, α and WTSD-ordering **all passed**.

### 5.1 Both-posture table at the candidate (n = 4,000)

| posture | persona | AF | FtC (n) | WTSD (n) | raise_abs (facing_n) | raise_share (continue_n) |
|---|---|---|---|---|---|---|
| False | nit | 1.37799 | 0.42138 (159) | 0.60129 (928) | 0.11559 (571) | 0.18803 (351) |
| False | tag | 2.21507 | 0.24315 (292) | 0.60771 (1583) | 0.26818 (660) | 0.38646 (458) |
| False | lag | 2.56621 | 0.33742 (489) | 0.55982 (2399) | 0.28875 (800) | 0.45117 (512) |
| True | nit | 1.39485 | 0.34177 (158) | 0.58146 (1025) | 0.12275 (668) | 0.19903 (412) |
| True | tag | 2.28670 | 0.31183 (279) | 0.60912 (1645) | 0.23228 (663) | 0.34222 (450) |
| True | lag | 2.71460 | 0.32790 (491) | 0.54391 (2471) | 0.27214 (779) | 0.43443 (488) |

At n = 16,000 / 32,000 (False): nit FtC 0.40909 (638) / 0.39583 (1296); tag 0.31371 (1138) /
0.31852 (2295); lag 0.34997 (1883) at 16k. Every denominator ≥ 30 at every reading reported.

### 5.2 All pre-registered margins at the candidate

**Ordering legs** (½-pot replica; rule ≥ 0.035 on every leg touching nit/tag/lag):

| leg | margin | verdict |
|---|---|---|
| `tag < nit` | 0.1248 | ✓ |
| `fish − nit < 0.10` | 0.1536 | ✓ |
| `fish > tag` | 0.0712 | ✓ |
| `lag < tag` | **0.0432** | ✓ (HEAD: 0.0224 ✗) |
| `maniac < lag` | 0.0744 | ✓ |
| `station < lag` | 0.1912 | ✓ |
| `station < min(fish, maniac)` (untouched) | 0.1168 | ✓ |

**Band distances at the gate posture, n = 4,000:**

| persona | AF (band) | dist to nearest edge | FtC (band) | dist | WTSD (band) | dist to loose edge |
|---|---|---|---|---|---|---|
| nit | 1.37799 (0.6, 2.4) | 0.778 / 1.022 | 0.42138 (0.10, 0.90) | 0.321 / 0.479 | 0.60129 (0.37, 0.80) | **0.1987** |
| tag | 2.21507 (1.4, 3.6) | 0.815 / 1.385 | 0.24315 (0.0, 0.55) | 0.243 / 0.307 | 0.60771 (0.41, 0.65) | **0.0423** |
| lag | 2.56621 (1.5, 4.5) | 1.066 / 1.934 | 0.33742 (0.12, 0.64) | 0.217 / 0.303 | 0.55982 (0.37, 0.59) | **0.0302** |

tag 0.0423 and lag 0.0302 both clear the 0.02 rule (2c). lag at HEAD is 0.0112 — the fit repairs it.

**α margins at the candidate:** nit min +0.0437 (⅓/½/1/1.5-pot: +0.1017 / +0.0437 / +0.1024 /
+0.0840); tag and lag unchanged in sign and comfortably positive.

### 5.3 T_sep derivation — the pre-registered rule yields an EMPTY window at every affordable n

σ analytic binomial from the measured FtC denominators; σ_gap = √(σ²_nit + σ²_tag).

| n | FtC nit (n) | FtC tag (n) | gap | σ_gap | 3σ_gap | gap/σ_gap | window [3σ, gap−3σ] |
|---|---|---|---|---|---|---|---|
| 4,000 | 0.42138 (159) | 0.24315 (292) | 0.17823 | 0.046515 | 0.13955 | 3.83 | [0.1396, 0.0387] **EMPTY** |
| 16,000 | 0.40909 (638) | 0.31371 (1138) | 0.09538 | 0.023834 | 0.07150 | 4.00 | [0.0715, 0.0239] **EMPTY** |
| 32,000 | 0.39583 (1296) | 0.31852 (2295) | **0.07731** | 0.016707 | 0.05012 | **4.63** | [0.0501, 0.0272] **EMPTY** |

The n = 4,000 reading (0.178) is an **over-read**: tag's FtC there (0.24315) is 1.7 σ below its own
stable value, and the same lever set reads 0.077 at n = 32,000. Anyone who stopped at the spec's
named n would have pre-registered a threshold against a fluctuation.

The rule needs gap ≥ 6 σ_gap. Holding the measured gap 0.07731 fixed:
**n ≥ 32,000 × (0.016707 / (0.07731/6))² = 53,780** — and that is the break-even point with zero
margin; ~n = 80,000 for real headroom (window would be [0.0317, 0.0456]). At the measured
82 s per 32,000-hand call that is **+4 to +7 minutes of CI for one gate**, against a 274 s suite.

The nit-0.32 variant does not rescue it: gap 0.08064, 3σ 0.05083, **4.76 σ** — same verdict, and
it costs 0.024 of α margin for nothing.

**Directionally the fit does work**: the gap moves from +0.00287 (base, 32k) to +0.07731, a
+0.0744 shift = 4.5 σ of the joint noise, and the archetype sign inversion is genuinely repaired.
It is the *symmetric 6σ threshold rule*, not the direction, that is unreachable.

### 5.4 G-RS band widths (per persona) — the ±3σ formula, at the spec's named n = 4,000

Widths are **exactly** ±3·√(p(1−p)/N) on the BASE-pack conditional raise share at that n:

| persona | base raise_share | continue_n | σ | **band width ±3σ** | observed joint shift | verdict |
|---|---|---|---|---|---|---|
| nit | 0.19307 | 404 | 0.019638 | **±0.05891** | −0.00504 | ✓ inside (0.26 band) |
| tag | 0.38372 | 430 | 0.023450 | **±0.07035** | +0.00274 | ✓ inside (0.04 band) |
| lag | 0.45491 | 499 | 0.022292 | **±0.06688** | −0.00374 | ✓ inside (0.06 band) |

**G-RS-i is green and the invariance is real** — exactly as N-LOGIT theory predicts (both continue
merits carry one factor of `looseness`, which cancels out of the conditional share).

⚠️ **Disclosure for T3**: the invariance is exact *at a fixed node* but only approximate *in the
population*, because tightening a persona changes its arrival mix. At n = 32,000 nit's shift is
+0.01154 against a ±0.01999 band — 58 % of the band, 1.73 σ. A ±3σ band built at n ≳ 96,000 would
go red on a legitimate fit. **Build G-RS-i at n = 4,000 as specified; do not "strengthen" it with a
bigger n.**

### 5.5 G-RS-ii (nit's absolute raise probability must fall > 3σ) — NOT SATISFIABLE

| n | base raise_abs (facing_n) | candidate (facing_n) | fall | paired 3σ | in σ |
|---|---|---|---|---|---|
| 4,000 | 0.13311 (586) | 0.11559 (571) | +0.01752 | 0.05817 | 0.90 σ |
| 16,000 | 0.12602 (2452) | 0.12010 (2373) | +0.00592 | 0.02837 | 0.63 σ |
| 32,000 | 0.13231 (4996) | 0.12660 (4842) | +0.00571 | 0.02031 | **0.84 σ** |

Theory predicts more: rscale = 0.38/0.6 = 0.6333 scales both continue merits, which at nit's base
split (P(continue) 0.6948, P(raise|continue) 0.1904) predicts 0.1323 → 0.1124, i.e. −0.0199 ≈ 3σ
at 32k. The measured fall is **3.5× smaller** because the *arrival composition* moves the other
way: a tighter nit folds more marginal hands preflop and postflop, so the facing nodes it still
reaches are stronger and raise more. n needed for a 3σ fall at the measured effect size:
**≈ 405,000**. At nit 0.32 the fall is smaller still (0.12998 vs base 0.13231).

**This is the first production run at `rscale ≠ 1`, and it is the report's biggest surprise**
(§8).

---

## 6. Rule-1 conditioning deliverable (spec T1 step 3)

**Pairing statement (Rule 1a).** This fit moves exactly ONE lever per persona
(`call_looseness`), paired to the stat it dominates (**FtC**), on three personas. No 2×2 Jacobian
and no spectral radius ρ applies: ρ is defined for a two-lever/two-stat system and this is three
independent scalar fits sharing an environment. Rule 1b (target-pair conditioning) likewise does
not apply — there is one target stat per persona, so there are no near-parallel Jacobian rows.
Rule 2 was honoured: every step used a fresh secant from the last two measurements with the other
two personas held fixed, and **no anchor slope was extrapolated into the fit region** — which was
load-bearing, because the gate-posture FtC secant (nit 0.6→0.45: −0.345 per ln cl) is **2.3×
steeper** than the anchor value the feasibility report measured at the True posture (−0.152).
No sign flip was observed on any stat-vs-lever curve.

**Measured cross-persona coupling at the gate posture** (each persona measured with only its own
final value moved, then again at the full joint triple; n = 4,000, `ca=False`):

| observer | stat | solo | joint | Δ | paired 3σ | verdict |
|---|---|---|---|---|---|---|
| nit | FtC | 0.42667 (150) | 0.42138 (159) | −0.00528 | 0.16876 | inside |
| nit | AF | 1.45833 | 1.37799 | −0.08034 | 0.38683 | inside |
| nit | WTSD | 0.62435 (961) | 0.60129 (928) | −0.02306 | 0.06724 | inside |
| tag | FtC | 0.30717 (293) | 0.24315 (292) | **−0.06402** | 0.11049 | inside (1.74 σ) |
| tag | AF | 2.38881 | 2.21507 | −0.17374 | 0.44170 | inside |
| tag | WTSD | 0.60815 (1595) | 0.60771 (1583) | −0.00044 | 0.05196 | inside |
| lag | FtC | 0.34012 (491) | 0.33742 (489) | −0.00270 | 0.09071 | inside |
| lag | AF | 2.74062 | 2.56621 | −0.17440 | 0.43327 | inside |
| lag | WTSD | 0.56265 (2442) | 0.55982 (2399) | −0.00284 | 0.04279 | inside |

**Escalation criterion did NOT fire** — all nine deltas sit inside their own paired 3σ, so no
joint re-fit round of the trio is required. The largest (tag FtC, 1.74 σ) is nonetheless the
proximate cause of the n = 4,000 gap over-read in §5.3 and is exactly why the gap had to be
re-measured at stable n rather than certified at the gate's named n.

---

## 7. What the owner has to rule on before T2

1. **α ceiling vs nit's target tightness.** `test_fold_to_bet_respects_alpha_ceiling` is a HARD
   A1 guardrail asserting a bluff-catcher fold CEILING. "Make the nit measurably the tightest
   defender" pushes directly into it. Floor ≈ 0.31.
2. **R9-DEFENCE-a's ladder vs nit's target tightness.** Floor ≈ 0.42 (≥0.45 for margin) — it
   dominates α. Two slices five days apart want opposite things from the same number: R9-DEFENCE-a
   needs nit to have room to fold MORE under a barrel; R9-LOOSEFIT wants nit already folding more.
3. **tag's `call_looseness` is pinned by two gates** (§4.3). Either they are re-scoped
   (`test_elasticity_split_…` should build its "unset" baseline from a synthetic pack, not the
   shipped tag pack; the four `_W3R6_RAISE_DROP` literals would need a sanctioned re-record), or
   tag cannot move — and if tag cannot move, criteria 2b and 2c are jointly unsatisfiable (§4.5).
4. **T_sep's symmetric 6σ rule vs n.** Achievable gap 0.077 ⇒ n ≥ 53,800 (≈ +4–7 min CI), against
   the spec's named n = 4,000. Alternatives: accept a one-sided threshold, change the statistic,
   or pay the n.
5. **G-RS-ii is unreachable** at any admissible nit value (0.84 σ; needs n ≈ 405,000). Either the
   leg is dropped, or it moves to a fixed-node probe (like G-NODE) where the composition effect
   that cancels it does not exist.
6. **Files-to-touch is incomplete**: add `tests/fixtures/…` coverage baseline and the limper belt
   pins to T4's re-record list (§4.4).

---

## 8. Surprises (unexpected movement is signal)

1. **`rscale ≠ 1` in production behaves *less* like the theory than expected, in the direction
   that kills G-RS-ii.** The predicted absolute-raise fall (−0.0199) is 3.5× the measured
   (−0.0057). The mechanism is real and the conditional-share invariance holds exactly; what
   swamps the absolute leg is **arrival composition** — a tighter nit reaches a stronger facing
   population that raises more, restoring most of the mass rscale removed. Nothing in the
   N-LOGIT or feasibility work anticipated this; both measured at fixed nodes or at rscale = 1.
2. **The gate-posture FtC slope is 2.3× the True-posture slope** (−0.345 vs −0.152 per ln cl for
   nit near 0.5). The feasibility report's "∂FtC/∂ln cl is essentially constant, −0.15..−0.19 at
   every point measured, on every persona" is a **True-posture** statement and does not transfer
   to the posture CI judges at. Anchor-seeded FtC steps are NOT safe at the gate posture.
3. **nit's FtC saturates** at ≈0.40–0.43 for cl ∈ [0.32, 0.38] at the gate posture, while the
   feasibility ladder (True, 24k) showed it still climbing (0.4146 → 0.6081 over 0.30 → 0.08).
   The extra tightening the α ceiling forbids would have bought nothing anyway in [0.32, 0.38].
4. **Over half the lever's facing nodes are inert.** 57 % (tag) and 65 % (lag) of fold-legal
   decisions are SPR-committed under the conservative predicate. The lever has far less reach than
   any prior document assumed.
5. **The base gap is not −0.063.** That figure (quoted in the ledger as the CI-posture base) is an
   n = 4,000 fluctuation; the stable-n base gap is +0.00287 ± 0.0475 — a tie, not an inversion, at
   the gate posture. The *inversion* claim survives only at the feasibility report's True/48k
   posture (−0.0121, also a tie). **The slice's motivating "backwards" finding is, measured at
   stable n, a tie in both postures.** That does not weaken the case for separating them, but the
   spec's framing ("measurably folds less") is not supported at stable n and should be restated.

---

## 9. Verification (done-condition)

| check | result |
|---|---|
| full backend suite, accessor added, `content/` unmodified | `1416 passed, 1 skipped, 274.04s, exit=0` (`t1-fullsuite-accessor.txt`) |
| targeted no-movement (golden + caches + bands + ordering + α + WTSD) | `59 passed, 1 skipped, exit=0` (`t1-nomove.txt`) |
| `git status --porcelain content/` | empty (md5 round-trip verified after every temporary edit) |
| `ruff check .` | All checks passed |
| pack md5 after restore | nit `30520189…` tag `7ea08f2e…` lag `b258e4ea…` — authored bytes |

Temporary pack edits were made and restored 8 times (spec seed, candidate, 3 single-persona
isolations, 5 nit-only R9D brackets); `setcl.py` md5-verifies the restore each time.

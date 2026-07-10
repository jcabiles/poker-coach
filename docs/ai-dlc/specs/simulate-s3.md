# Delta spec — Simulate S3: persona packs + preflop bot play

> Slice S3 of `docs/ai-dlc/roadmap/simulate-table.md`. Contract scan:
> `docs/ai-dlc/contracts/simulate-s3-personas.md`. Stat bands: PRD §8.
> Gate decisions (2026-07-10): limp is a first-class action name in CONTENT, translated to
> `ActionType.CALL` on the wire · widen `VillainType` + decouple `test_exploits` via an
> explicit exploit subset (+ add the two leak categories now) · stat test runs unmarked in
> the default suite (add a slow marker only if measured > ~2s).

**Goal (one line):** six persona content packs with per-position weighted preflop ranges and
a pure-domain sampling engine that draws a frequency-mixed preflop action for any
(persona, position, facing, hand-class) — validated by a closed-loop VPIP/PFR/3-bet test.

## Frozen pack schema (all three tickets build to this)

New Pydantic models (in `backend/app/domain/content/models.py`, mirroring `ContentPack`):

```python
class PersonaActionMix(BaseModel):
    combos: str                      # range string, existing notation.parse_range() tokens ONLY
    # action-name → probability; names constrained per node facing (below); sum ≤ 1.0;
    # remainder is an implicit fold.
    weights: dict[str, float]

class PersonaNode(BaseModel):
    facing: str                      # "unopened" | "vs_limpers" | "vs_rfi" | "vs_3bet" | "vs_4bet"
    positions: list[Position] | None # None = wildcard (any position)
    mixes: list[PersonaActionMix]    # FIRST MATCH WINS; unmatched hand-class ⇒ fold 1.0

class PersonaPack(BaseModel):
    id: str                          # "persona_passive_fish" etc.
    version: str
    domain: Literal["persona"]
    persona: VillainType             # the acting identity
    display_name: str
    sizing: PersonaSizing            # {open_bb: float, threebet_mult: float, fourbet_mult: float}
                                     # authored now, CONSUMED in S4 (engine ignores it in S3)
    preflop: list[PersonaNode]
```

**Node lookup order (pinned — refuter fix):** scan `pack.preflop` in LIST ORDER; the first
node whose `facing` matches AND whose `positions` is `None` or contains the query position
wins. Authoring pattern: position-specific nodes first, one wildcard (`positions: null`)
fallback last per facing. Model validation enforces: per facing, at most ONE wildcard node,
all explicit-position nodes listed BEFORE the wildcard, and explicit-position nodes of the
same facing may not overlap positions (raise on violation). Explicit + wildcard overlap is
the intended override mechanism, not a duplicate.

**Cross-mix combos overlap within a node is ALLOWED by design** (first-match-wins): author
mixes narrow-to-wide with a catch-all last; a hand class in two mixes resolves to the first.
No load-time overlap error (it's the specificity mechanism, same as node lookup).

Action-name vocabulary per facing (validated by the model):
`unopened`: fold/limp/raise · `vs_limpers`: fold/limp/raise (limp = over-limp) ·
`vs_rfi`: fold/call/3bet · `vs_3bet`: fold/call/4bet · `vs_4bet`: fold/call/5bet_shove.
**Wire translation (engine-owned, content never sees ActionType):** limp→CALL, call→CALL,
raise/3bet/4bet/5bet_shove→RAISE, fold→FOLD.

Files: `content/personas/{passive_fish,calling_station,nit,tag,lag,maniac}.json` ·
generated doc `content/schema/persona.schema.json` (`PersonaPack.model_json_schema()`,
mirroring the loader's existing schema-dump idiom).

## Engine interface (frozen)

`backend/app/domain/personas.py`:

```python
class PersonaAction(NamedTuple):
    name: str                # the content-level action ("limp", "3bet", ...)
    action: ActionType       # wire translation

def load_persona_packs() -> dict[VillainType, PersonaPack]   # content/personas/*.json;
    # RAISES on duplicate persona or on duplicate (facing, position) node coverage —
    # addresses the registry silent-last-wins hazard (scan §pack anatomy).

def sample_preflop_action(
    pack: PersonaPack, position: Position, facing: str,
    hole_cards: tuple[Card, Card], rng: random.Random,
) -> PersonaAction
    # hand class via notation.hole_cards_to_class(); first matching mix; draw via
    # rng.choices() (challenge.py:184-213 precedent); no match ⇒ fold. NEVER deterministic
    # strength→action shortcuts; rng is INJECTED (per-hand instance), never module-level.
```

## Enum widening + decoupling (exact changes)

- `domain/archetypes.py`: `VillainType` += `TAG = "tag"`, `MANIAC = "maniac"`; add
  `EXPLOIT_ARCHETYPES: frozenset[VillainType]` = the original 4 (the exploit-drill roster).
- `domain/leaks.py`: `LeakCategory` += `TAG_EXPLOIT = 304`, `MANIAC_EXPLOIT = 305`.
- `domain/grading.py` `_EXPLOIT_LEAK`: map the two new types (kills the silent
  fall-back-to-CALLING_STATION_EXPLOIT hazard).
- `tests/test_exploits.py`: coverage assertion switches `set(VillainType)` →
  `EXPLOIT_ARCHETYPES`.
- `tests/test_api.py:66`: hardcoded 4-member set literal → `{v.value for v in VillainType}`.

## Closed-loop stat test (frozen protocol — refuter-corrected)

`tests/test_personas.py`, default suite, unmarked. **These are PROXY metrics, not tracker
VPIP** (true end-to-end VPIP needs full-hand simulation — that validation is S4's
table-texture loop; a one-line note goes in the PRD). Per persona, seeded `random.Random`:

**Sampling shape (pinned):** call `deal_hand` exactly 1,112 times; for each deal use ALL 9
seats' hole cards, seat `i` sampled at position `positions_for_button(0)[i]` → 1,112 samples
per position, ~10k total. (Within-deal card removal doesn't bias per-seat MARGGINAL
frequencies — each seat's two cards are marginally uniform — so this is unbiased for
frequency measurement and 9× cheaper than one-seat-per-deal.)

**Metrics + bands:**
- **open-freq** (proxy for VPIP): 1 − fold-freq on `unopened` — assert inside the PRD §8
  VPIP band (low-stakes players' first-in play range ≈ their play range; documented proxy).
- **first-in-raise-freq** (proxy for PFR): raise-freq on `unopened` — assert inside §8 PFR band.
- **3-bet%:** 3bet-freq on `vs_rfi` — assert inside §8 band.
- **vs_rfi continue%** (call+3bet on `vs_rfi`) — NEW, pins the station/fish-defining
  behavior the unopened proxy can't see. Derived bands (tune in-loop, note deviations):

| persona | open-freq (VPIP band) | first-in raise (PFR band) | 3-bet | vs_rfi continue |
|---|---|---|---|---|
| passive_fish | 28–45 | 3–9 | 0–2 | 35–55 |
| calling_station | 40–60 | 0–8 | 0–1 | 50–70 |
| nit | 7–14 | 2–9 | 1–2 | 5–15 |
| tag | 15–20 | 12–17 | 6–7 | 15–28 |
| lag | 24–36 | 18–24 | 8–12 | 25–42 |
| maniac | 45–60 | 30–40 | 12–20 | 45–70 |

Plus: schema validation of all 6 packs via the loader; same-seed determinism; a mixed-weights
draw actually mixes (both actions observed); duplicate/misordered-node fixture raises. If
measured runtime of the whole file exceeds ~2s, drop deal count to the smallest that keeps
bands tight and note it.

## Files / tickets

| Ticket | Files |
|---|---|
| T1 engine (heavy-worker) | `domain/content/models.py` (persona models) · `domain/personas.py` (new) · `domain/archetypes.py` · `domain/leaks.py` · `domain/grading.py` · `content/schema/persona.schema.json` (generated) · `content/schema/contentpack.schema.json` (REGENERATE — the baked VillainType enum goes stale on widening) · `tests/test_personas.py` (new) · `tests/test_domain_purity.py` (+`app.domain.personas`) · `tests/test_exploits.py` · `tests/test_api.py` (set literal) |
| T2 packs A (implementer) | `content/personas/{passive_fish,calling_station,nit}.json` |
| T3 packs B (implementer) | `content/personas/{tag,lag,maniac}.json` |

T2/T3 author to the frozen schema in parallel with T1; loader/tests land in T1 and validate
them at fan-in. Pack authoring guidance: doc-grounded low-stakes live profiles (PRD §8
research); position-aware (tighter early, wider late); station raises only premiums; nit
limps small pairs; maniac 3-bets wide. Weights are per-hand-class mixes — marginal classes
get genuine mixing (e.g. `{raise: 0.5, fold: 0.5}`), never all-1.0 rows everywhere.

## Out of scope (S3 no-gos)

No postflop behavior (S4) · no integration into the hand engine or Simulate API (S4/S9) ·
no persona-aware grading, no exploit-pack content for TAG/maniac · no ActionType/LegalAction
enum changes · no FE changes · no DB/migrations · sizing block authored but unconsumed ·
`drill.py`'s `_RNG` untouched.

## Constraints

Domain purity (allowlist entry required) · strategy in versioned `content/` only · frequency-
mixed always · rng injected per call · notation tokens limited to `_expand_token`'s supported
set (unsupported tokens raise — validate at load) · ruff clean · match surrounding style.

## Verify-by

`./scripts/verify.sh` → `BACKEND VERIFY OK` with `test_personas.py` green (stat bands hit for
all 6), `test_exploits.py` green via `EXPLOIT_ARCHETYPES`, purity green incl.
`app.domain.personas`, full suite no regressions. Measured runtime of `test_personas.py`
reported in the PR (marker decision evidence).

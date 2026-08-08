"""Blind-detection statistics module (flywheel S6 T6) — the pilot's number.

Computes the S6 detection-pilot results **from structured judge outputs only**
(`{label, confidence_human}` per `(judge, presentation_id)`) — NEVER by parsing
rendered hand text. Formulas are pinned by
`poker-analytics:docs/methods/estimand-contract.md` §d.2/§d.3 and restated in
`docs/ai-dlc/specs/flywheel-s6.md` ("Design rules -> Analysis"); this module
implements them exactly, including the four registered Kish `n_eff` uses.

Order of operations (fail closed):

1. **Control invalidation FIRST.** Panel mean over usable control confidences
   < 50 AND >=4-of-5 judges individually label the control "bot" (a missing or
   unusable control response counts AGAINST the 4-of-5 conjunct, never
   against nobody). If either conjunct cannot be established, the whole batch
   is INVALID and only diagnostics + a completeness report are emitted — deck
   statistics are never computed on an invalid batch.
2. **Deck statistics** (only if the control is valid): analysis deck = the
   corpus's non-control, non-duplicate bundles. Balanced accuracy, AUC
   (Mann-Whitney, half-credit ties), d' (extreme-rate corrected,
   class-specific N), human-misclassification rate, a stratified bootstrap
   (B=10,000, seeded, judges fixed per bundle), and Kish `n_eff` from
   pairwise judge-error correlations.

Producer field names may drift slightly while T4/T5 build concurrently — every
byte of the on-disk input contract is read by one of the small `load_*`
functions below, each with its own schema validation, so a producer-side
rename only touches a loader, never a statistics formula.

Usage (from backend/, as a module — repo convention):

    python -m tools.detection_analysis run \\
        --deck <corpus-out-dir> --judging <judging-dir> \\
        --bootstrap-seed 20260807 --out <analysis-out-dir>

Writes `analysis.json` (machine-readable) and `report.txt` (plain-text
tables). Both are deterministic given the same inputs + `--bootstrap-seed`:
no wall-clock field appears in either.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import NormalDist

SCHEMA_VERSION = "1.0.0"

LAUNCH_FILENAME = "launch.json"
JUDGING_COMPLETE_FILENAME = "judging_complete.json"
RESPONSES_DIRNAME = "responses"
UNBLINDING_FILENAME = "unblinding.json"
PRESENTATION_FILENAME = "presentation.json"
ANALYSIS_FILENAME = "analysis.json"
REPORT_FILENAME = "report.txt"

DEFAULT_BOOTSTRAP_B = 10_000

# Fixed disclosure strings (registered uses (iii) and the bootstrap
# understatement note; spec "Design rules -> Analysis").
AGREEMENT_CAVEAT = "agreement is reliability, not validity — never evidence of correctness"
BOOTSTRAP_DISCLOSURE = (
    "Bootstrap intervals resample bundles within class for THIS player and THIS "
    "judge panel only; they are conditional on this player and this panel and "
    "UNDERSTATE total uncertainty, because every human bundle comes from one "
    "human cluster (one player) — no across-player generalization is estimable."
)
# n_eff and the point estimates it sits beside (registered use (i)) are drawn
# from two DIFFERENT populations whenever any bundle is excluded: n_eff uses
# every pairwise-complete response over the full analysis deck, while the
# point estimates use only bundles with >=3 usable judges. Fixed disclosure,
# recorded beside n_eff everywhere it appears (analysis.json AND report.txt).
N_EFF_POPULATION_NOTE = (
    "n_eff is estimated from pairwise-complete responses over the FULL analysis "
    "deck; the point estimates beside it use only bundles with >=3 usable "
    "judges — the populations differ when exclusions occur."
)
# Per-judge deck performance (§d.3 "Per-judge statistics reported alongside")
# uses each judge's OWN usable responses over the full analysis deck — like
# n_eff, and for the same reason, it is NOT gated by the panel's >=3-usable
# inclusion rule (that rule gates the panel-AGGREGATE point estimates only).
PER_JUDGE_POPULATION_NOTE = (
    "Per-judge rows use each judge's OWN usable responses over the full "
    "analysis deck; they are not gated by the panel's >=3-usable-judges "
    "inclusion rule, which applies only to the panel-aggregate point estimates."
)

VALID_LABELS = ("human", "bot")
# NOTE: matches `detection_judge.py`'s actual on-disk status strings (its own
# internal completeness counter folds "malformed-final" to "malformed", but
# the per-response JSON file's "status" field is the terminal, unfolded value).
VALID_STATUSES = ("ok", "malformed-final", "transport_failed")


class AnalysisError(ValueError):
    """A producer artifact violates the frozen input contract."""


# ---------------------------------------------------------------------------
# Loaders — isolate ALL input reading here; statistics below never touch a
# raw file. Each loader validates its own slice of the contract and raises
# `AnalysisError` on anything outside it, so a T7 loader fix never has to
# touch a formula.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Judge:
    slot: int
    vendor: str
    requested_model: str
    resolved_model: str


def _read_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise AnalysisError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"{path}: not valid JSON ({exc})") from exc


def load_launch_manifest(judging_dir: Path) -> list[Judge]:
    """`launch.json`: `{"judges": [{slot, vendor, requested_model,
    resolved_model}, ...], ...}`. Returns judges sorted by slot; slots must be
    the contiguous range `0..k-1` with no duplicates.
    """
    doc = _read_json(Path(judging_dir) / LAUNCH_FILENAME)
    raw_judges = doc.get("judges")
    if not isinstance(raw_judges, list) or not raw_judges:
        raise AnalysisError("launch.json: 'judges' must be a non-empty list")
    judges: list[Judge] = []
    for entry in raw_judges:
        if not isinstance(entry, Mapping):
            raise AnalysisError(f"launch.json: judge entry {entry!r} is not an object")
        try:
            slot = entry["slot"]
            vendor = entry["vendor"]
            requested = entry["requested_model"]
            resolved = entry["resolved_model"]
        except KeyError as exc:
            raise AnalysisError(f"launch.json: judge entry missing {exc}") from exc
        if not isinstance(slot, int) or isinstance(slot, bool) or slot < 0:
            raise AnalysisError(f"launch.json: judge slot {slot!r} is not a non-negative int")
        if not all(isinstance(v, str) and v for v in (vendor, requested, resolved)):
            raise AnalysisError(f"launch.json: judge slot {slot}: non-string field")
        judges.append(Judge(slot, vendor, requested, resolved))
    judges.sort(key=lambda j: j.slot)
    slots = [j.slot for j in judges]
    if slots != list(range(len(slots))):
        raise AnalysisError(f"launch.json: judge slots {slots} are not 0..{len(slots) - 1}")
    return judges


def load_judging_complete(judging_dir: Path) -> dict:
    """`judging_complete.json` is a completion marker; only its presence and
    JSON-validity are contractually required here."""
    return _read_json(Path(judging_dir) / JUDGING_COMPLETE_FILENAME)


@dataclass(frozen=True, slots=True)
class JudgeResponse:
    slot: int
    presentation_id: str
    status: str
    label: str | None
    confidence: int | None

    @property
    def usable(self) -> bool:
        return (
            self.status == "ok"
            and self.label in VALID_LABELS
            and isinstance(self.confidence, int)
            and 0 <= self.confidence <= 100
        )


def load_responses(
    judging_dir: Path, judges: Sequence[Judge]
) -> dict[tuple[int, str], JudgeResponse]:
    """`responses/**/*.json` (`detection_judge.py` nests these under a
    per-slot subdirectory, e.g. `responses/slot-0/<presentation_id>.json`;
    this loader does not depend on that nesting shape), each `{slot,
    presentation_id, raw_response(s), parsed: {label, confidence_human,
    reason} | null, status}`.

    Indexed by the file's OWN `(slot, presentation_id)` fields (not by
    filename or directory) so a filename/nesting drift never desyncs the
    index; a `status == "ok"` response with an invalid/missing `parsed` block
    is a genuine contract violation (the retry rule should have already
    demoted it to a non-"ok" status) and raises, rather than being silently
    treated as unusable.
    """
    valid_slots = {j.slot for j in judges}
    responses_dir = Path(judging_dir) / RESPONSES_DIRNAME
    out: dict[tuple[int, str], JudgeResponse] = {}
    if not responses_dir.is_dir():
        raise AnalysisError(f"missing required directory: {responses_dir}")
    for path in sorted(responses_dir.rglob("*.json")):
        doc = _read_json(path)
        try:
            slot = doc["slot"]
            presentation_id = doc["presentation_id"]
            status = doc["status"]
        except KeyError as exc:
            raise AnalysisError(f"{path}: response missing {exc}") from exc
        if slot not in valid_slots:
            raise AnalysisError(f"{path}: response slot {slot!r} not in launch manifest")
        if status not in VALID_STATUSES:
            raise AnalysisError(f"{path}: response status {status!r} is not recognized")
        parsed = doc.get("parsed")
        label: str | None = None
        confidence: int | None = None
        if status == "ok":
            if not isinstance(parsed, Mapping):
                raise AnalysisError(f"{path}: status 'ok' but 'parsed' is missing/invalid")
            label = parsed.get("label")
            confidence = parsed.get("confidence_human")
            if label not in VALID_LABELS:
                raise AnalysisError(f"{path}: status 'ok' but parsed.label {label!r} invalid")
            if (
                not isinstance(confidence, int)
                or isinstance(confidence, bool)
                or not 0 <= confidence <= 100
            ):
                raise AnalysisError(
                    f"{path}: status 'ok' but parsed.confidence_human {confidence!r} invalid"
                )
        key = (slot, presentation_id)
        if key in out:
            raise AnalysisError(f"duplicate response for (slot={slot}, pid={presentation_id})")
        out[key] = JudgeResponse(slot, presentation_id, status, label, confidence)
    return out


@dataclass(frozen=True, slots=True)
class BundleRecord:
    presentation_id: str
    klass: str  # "human" | "bot" — the TRUE class
    is_control: bool


@dataclass(frozen=True, slots=True)
class DuplicateSlot:
    slot: int
    presentation_id: str
    source_presentation_id: str


@dataclass(frozen=True, slots=True)
class UnblindingData:
    bundles: list[BundleRecord]
    duplicates: list[DuplicateSlot]
    raw: dict


def load_unblinding(deck_dir: Path) -> UnblindingData:
    """`unblinding.json`: `{"bundles": [{presentation_id, class, is_control,
    ...}], "judge_duplicates": {"slots": [{slot, presentation_id,
    source_presentation_id, class: "human", ...}]}, ...}` (§A.3 duplicate
    mapping, drawn exclusively from the human class)."""
    doc = _read_json(Path(deck_dir) / UNBLINDING_FILENAME)
    raw_bundles = doc.get("bundles")
    if not isinstance(raw_bundles, list) or not raw_bundles:
        raise AnalysisError("unblinding.json: 'bundles' must be a non-empty list")
    bundles: list[BundleRecord] = []
    for entry in raw_bundles:
        try:
            pid = entry["presentation_id"]
            klass = entry["class"]
            is_control = entry["is_control"]
        except (KeyError, TypeError) as exc:
            raise AnalysisError(f"unblinding.json: bundle entry missing {exc}") from exc
        if klass not in VALID_LABELS:
            raise AnalysisError(f"unblinding.json: bundle {pid!r} class {klass!r} invalid")
        if not isinstance(is_control, bool):
            raise AnalysisError(f"unblinding.json: bundle {pid!r} is_control not a bool")
        bundles.append(BundleRecord(pid, klass, is_control))
    duplicates_doc = doc.get("judge_duplicates", {})
    raw_slots = duplicates_doc.get("slots", []) if isinstance(duplicates_doc, Mapping) else []
    duplicates: list[DuplicateSlot] = []
    for entry in raw_slots:
        try:
            slot = entry["slot"]
            dup_pid = entry["presentation_id"]
            src_pid = entry["source_presentation_id"]
            dup_class = entry["class"]
        except (KeyError, TypeError) as exc:
            raise AnalysisError(f"unblinding.json: judge_duplicates entry missing {exc}") from exc
        if dup_class != "human":
            raise AnalysisError(
                f"unblinding.json: duplicate slot {slot} class {dup_class!r} != 'human' (§A.3)"
            )
        duplicates.append(DuplicateSlot(slot, dup_pid, src_pid))
    duplicates.sort(key=lambda d: d.slot)
    return UnblindingData(bundles=bundles, duplicates=duplicates, raw=doc)


def load_presentation_hashes(deck_dir: Path) -> dict[str, str]:
    """`presentation.json`: presentation_id -> sha256, for cross-checking the
    unblinding manifest's own `sha256` field. NEVER used to read `rendered_text`
    (statistics never touch rendered text)."""
    doc = _read_json(Path(deck_dir) / PRESENTATION_FILENAME)
    raw_bundles = doc.get("bundles")
    if not isinstance(raw_bundles, list) or not raw_bundles:
        raise AnalysisError("presentation.json: 'bundles' must be a non-empty list")
    out: dict[str, str] = {}
    for entry in raw_bundles:
        try:
            pid = entry["presentation_id"]
            sha = entry["sha256"]
        except (KeyError, TypeError) as exc:
            raise AnalysisError(f"presentation.json: bundle entry missing {exc}") from exc
        out[pid] = sha
    return out


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Control invalidation (order of operations: FIRST, fail closed)
# ---------------------------------------------------------------------------


def _control_bot_threshold(k: int) -> int:
    """`ceil(4k/5)` — generalizes the pinned "4 of 5" to whatever panel size
    actually ran (the roadmap's cut order allows dropping to 3 judges;
    k=5 reproduces the literal "4 of 5" pin)."""
    return -(-(4 * k) // 5)


def evaluate_control(
    control: BundleRecord,
    judges: Sequence[Judge],
    responses: Mapping[tuple[int, str], JudgeResponse],
) -> dict:
    per_judge = []
    usable_confidences: list[int] = []
    bot_label_count = 0
    for judge in judges:
        response = responses.get((judge.slot, control.presentation_id))
        status = response.status if response else "missing"
        label = response.label if response and response.usable else None
        confidence = response.confidence if response and response.usable else None
        if response is not None and response.usable:
            usable_confidences.append(response.confidence)
            if response.label == "bot":
                bot_label_count += 1
        per_judge.append(
            {"slot": judge.slot, "status": status, "label": label, "confidence": confidence}
        )
    k = len(judges)
    threshold = _control_bot_threshold(k)
    mean_confidence = statistics.mean(usable_confidences) if usable_confidences else None
    mean_conjunct_ok = mean_confidence is not None and mean_confidence < 50
    majority_conjunct_ok = bot_label_count >= threshold
    valid = mean_conjunct_ok and majority_conjunct_ok
    reasons = []
    if not mean_conjunct_ok:
        reasons.append(
            "control mean confidence not established below 50"
            if mean_confidence is None
            else f"control mean confidence {mean_confidence:.2f} is not < 50"
        )
    if not majority_conjunct_ok:
        reasons.append(
            f"only {bot_label_count}/{k} judges labeled the control 'bot' "
            f"(need >= {threshold})"
        )
    return {
        "presentation_id": control.presentation_id,
        "k": k,
        "threshold_required": threshold,
        "usable_confidences": usable_confidences,
        "mean_confidence": mean_confidence,
        "mean_below_50": mean_conjunct_ok,
        "bot_label_count": bot_label_count,
        "majority_bot_ok": majority_conjunct_ok,
        "valid": valid,
        "reasons": reasons,
        "per_judge": per_judge,
    }


# ---------------------------------------------------------------------------
# Deck statistics
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DeckBundleStat:
    presentation_id: str
    klass: str
    n_usable: int
    panel_score: float | None
    aggregate_label: str | None
    included: bool  # n_usable >= 3


def compute_deck_bundle_stats(
    deck_bundles: Sequence[BundleRecord],
    judges: Sequence[Judge],
    responses: Mapping[tuple[int, str], JudgeResponse],
) -> list[DeckBundleStat]:
    out = []
    for bundle in deck_bundles:
        confidences = [
            response.confidence
            for judge in judges
            if (response := responses.get((judge.slot, bundle.presentation_id))) is not None
            and response.usable
        ]
        n_usable = len(confidences)
        panel_score = statistics.mean(confidences) if confidences else None
        aggregate_label = None
        if panel_score is not None:
            aggregate_label = "human" if panel_score >= 50 else "bot"
        out.append(
            DeckBundleStat(
                presentation_id=bundle.presentation_id,
                klass=bundle.klass,
                n_usable=n_usable,
                panel_score=panel_score,
                aggregate_label=aggregate_label,
                included=n_usable >= 3,
            )
        )
    return out


def _human_recall(sample: Sequence[DeckBundleStat]) -> float | None:
    human = [s for s in sample if s.klass == "human"]
    if not human:
        return None
    return sum(1 for s in human if s.aggregate_label == "human") / len(human)


def _bot_recall(sample: Sequence[DeckBundleStat]) -> float | None:
    bot = [s for s in sample if s.klass == "bot"]
    if not bot:
        return None
    return sum(1 for s in bot if s.aggregate_label == "bot") / len(bot)


def balanced_accuracy(sample: Sequence[DeckBundleStat]) -> float | None:
    hr, br = _human_recall(sample), _bot_recall(sample)
    return None if hr is None or br is None else (hr + br) / 2


def human_misclassification_rate(sample: Sequence[DeckBundleStat]) -> float | None:
    hr = _human_recall(sample)
    return None if hr is None else 1 - hr


def auc_mann_whitney(sample: Sequence[DeckBundleStat]) -> float | None:
    """AUC on panel-mean confidence, half-credit for ties (M3.2)."""
    human_scores = [s.panel_score for s in sample if s.klass == "human"]
    bot_scores = [s.panel_score for s in sample if s.klass == "bot"]
    if not human_scores or not bot_scores:
        return None
    total = 0.0
    for h in human_scores:
        for b in bot_scores:
            if h > b:
                total += 1.0
            elif h == b:
                total += 0.5
    return total / (len(human_scores) * len(bot_scores))


def _correct_extreme_rate(rate: float, n: int) -> float:
    if n <= 0:
        raise AnalysisError("extreme-rate correction requires n > 0")
    if rate <= 0:
        return 1 / (2 * n)
    if rate >= 1:
        return 1 - 1 / (2 * n)
    return rate


def d_prime(sample: Sequence[DeckBundleStat]) -> float | None:
    """d' = z(P(labeled human|human)) - z(P(labeled human|bot)), extreme rates
    corrected to 1/(2N)/1-1/(2N) with CLASS-SPECIFIC usable N."""
    hr = _human_recall(sample)
    br = _bot_recall(sample)
    if hr is None or br is None:
        return None
    n_human = sum(1 for s in sample if s.klass == "human")
    n_bot = sum(1 for s in sample if s.klass == "bot")
    p_human = _correct_extreme_rate(hr, n_human)
    p_bot_false_positive = _correct_extreme_rate(1 - br, n_bot)
    z = NormalDist().inv_cdf
    return z(p_human) - z(p_bot_false_positive)


# ---------------------------------------------------------------------------
# Bootstrap (stratified, judges fixed per bundle)
# ---------------------------------------------------------------------------

METRIC_FUNCS = {
    "balanced_accuracy": balanced_accuracy,
    "human_misclassification_rate": human_misclassification_rate,
    "auc": auc_mann_whitney,
    "d_prime": d_prime,
}


def _percentile(sorted_values: Sequence[float], p: float) -> float:
    if not sorted_values:
        raise AnalysisError("percentile of an empty sample")
    idx = p * (len(sorted_values) - 1)
    lo, hi = math.floor(idx), math.ceil(idx)
    if lo == hi:
        return sorted_values[lo]
    frac = idx - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def bootstrap_deck(
    stats: Sequence[DeckBundleStat], seed: int, b_iterations: int = DEFAULT_BOOTSTRAP_B
) -> dict:
    """Stratified-by-class bootstrap over the INCLUDED (>=3-usable-judges)
    bundles — the same pool the point-estimate inferential statistics use;
    excluded bundles never enter the resample. Judges are never resampled:
    each resampled bundle keeps the fixed per-judge/aggregate results it
    already has."""
    included = [s for s in stats if s.included]
    human = [s for s in included if s.klass == "human"]
    bot = [s for s in included if s.klass == "bot"]
    rng = random.Random(seed)
    replicate_values: dict[str, list[float]] = {name: [] for name in METRIC_FUNCS}
    for _ in range(b_iterations):
        sample = (
            (rng.choices(human, k=len(human)) if human else [])
            + (rng.choices(bot, k=len(bot)) if bot else [])
        )
        for name, func in METRIC_FUNCS.items():
            value = func(sample)
            if value is not None:
                replicate_values[name].append(value)
    out = {}
    for name, values in replicate_values.items():
        values.sort()
        out[name] = {
            "ci_95": [_percentile(values, 0.025), _percentile(values, 0.975)] if values else None,
            "n_replicates": len(values),
        }
    return out


# ---------------------------------------------------------------------------
# Kish n_eff — registered uses (i)-(iv)
# ---------------------------------------------------------------------------


def _judge_error(
    bundle: BundleRecord, slot: int, responses: Mapping[tuple[int, str], JudgeResponse]
) -> bool | None:
    """Per-(judge,bundle) error indicator: the judge's OWN parsed label
    (never the panel aggregate rule) compared to the bundle's true class."""
    response = responses.get((slot, bundle.presentation_id))
    if response is None or not response.usable:
        return None
    return response.label != bundle.klass


def kish_n_eff(
    deck_bundles: Sequence[BundleRecord],
    judges: Sequence[Judge],
    responses: Mapping[tuple[int, str], JudgeResponse],
) -> dict:
    """n_eff = k/(1+(k-1)*phi_bar), phi_bar = mean pairwise correlation of
    judge error indicators over pairwise-complete bundles (both judges
    usable). Degenerate (zero-variance error vector, <2 shared bundles, or a
    non-positive denominator) -> "unavailable", never imputed."""
    k = len(judges)
    correlations: list[float] = []
    pairs_used = 0
    for i in range(len(judges)):
        for j in range(i + 1, len(judges)):
            slot_i, slot_j = judges[i].slot, judges[j].slot
            errors_i: list[int] = []
            errors_j: list[int] = []
            for bundle in deck_bundles:
                ei = _judge_error(bundle, slot_i, responses)
                ej = _judge_error(bundle, slot_j, responses)
                if ei is not None and ej is not None:
                    errors_i.append(int(ei))
                    errors_j.append(int(ej))
            if len(errors_i) < 2:
                continue
            if len(set(errors_i)) < 2 or len(set(errors_j)) < 2:
                continue  # zero-variance error vector — correlation undefined
            correlations.append(statistics.correlation(errors_i, errors_j))
            pairs_used += 1
    if not correlations:
        return {
            "n_eff": "unavailable",
            "k": k,
            "phi_bar": None,
            "pairs_used": 0,
            "n_eff_low": None,
            "population_note": N_EFF_POPULATION_NOTE,
        }
    phi_bar = statistics.mean(correlations)
    denominator = 1 + (k - 1) * phi_bar
    if denominator <= 0:
        return {
            "n_eff": "unavailable",
            "k": k,
            "phi_bar": phi_bar,
            "pairs_used": pairs_used,
            "n_eff_low": None,
            "population_note": N_EFF_POPULATION_NOTE,
        }
    n_eff = k / denominator
    return {
        "n_eff": n_eff,
        "k": k,
        "phi_bar": phi_bar,
        "pairs_used": pairs_used,
        "n_eff_low": (n_eff / k) < 0.5,
        "population_note": N_EFF_POPULATION_NOTE,
    }


def judge_agreement_rate(
    deck_bundles: Sequence[BundleRecord],
    judges: Sequence[Judge],
    responses: Mapping[tuple[int, str], JudgeResponse],
) -> float | None:
    """Raw pairwise label-agreement rate over pairwise-complete (judge, judge,
    bundle) triples. Diagnostics-only: reliability, not validity (M5.7)."""
    total = 0
    agree = 0
    for bundle in deck_bundles:
        labels = {
            judge.slot: response.label
            for judge in judges
            if (response := responses.get((judge.slot, bundle.presentation_id))) is not None
            and response.usable
        }
        slots = sorted(labels)
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                total += 1
                if labels[slots[i]] == labels[slots[j]]:
                    agree += 1
    return (agree / total) if total else None


def per_judge_deck_stats(
    deck_bundles: Sequence[BundleRecord],
    judges: Sequence[Judge],
    responses: Mapping[tuple[int, str], JudgeResponse],
) -> dict:
    """§d.3 "Per-judge statistics reported alongside": for each judge, over
    its OWN usable responses on the analysis deck (non-control,
    non-duplicate) — n_usable, balanced accuracy, human/bot recall, human
    misclassification rate, and mean `confidence_human` by true class.
    Inferential (deck-performance), so this belongs under the valid-batch
    branch only; ordered deterministically by slot."""
    rows = []
    for judge in sorted(judges, key=lambda j: j.slot):
        human_hits = human_total = 0
        bot_hits = bot_total = 0
        human_confidences: list[int] = []
        bot_confidences: list[int] = []
        n_usable = 0
        for bundle in deck_bundles:
            response = responses.get((judge.slot, bundle.presentation_id))
            if response is None or not response.usable:
                continue
            n_usable += 1
            if bundle.klass == "human":
                human_total += 1
                human_confidences.append(response.confidence)
                if response.label == "human":
                    human_hits += 1
            else:
                bot_total += 1
                bot_confidences.append(response.confidence)
                if response.label == "bot":
                    bot_hits += 1
        human_recall = (human_hits / human_total) if human_total else None
        bot_recall = (bot_hits / bot_total) if bot_total else None
        balanced = (
            (human_recall + bot_recall) / 2
            if human_recall is not None and bot_recall is not None
            else None
        )
        human_misclass = (1 - human_recall) if human_recall is not None else None
        rows.append(
            {
                "slot": judge.slot,
                "vendor": judge.vendor,
                "n_usable": n_usable,
                "balanced_accuracy": balanced,
                "human_recall": human_recall,
                "bot_recall": bot_recall,
                "human_misclassification_rate": human_misclass,
                "mean_confidence_human": {
                    "human": (
                        statistics.mean(human_confidences) if human_confidences else None
                    ),
                    "bot": statistics.mean(bot_confidences) if bot_confidences else None,
                },
            }
        )
    return {"population_note": PER_JUDGE_POPULATION_NOTE, "rows": rows}


# ---------------------------------------------------------------------------
# Duplicate consistency (diagnostics only)
# ---------------------------------------------------------------------------


def duplicate_consistency(
    duplicates: Sequence[DuplicateSlot],
    responses: Mapping[tuple[int, str], JudgeResponse],
) -> dict:
    per_judge = []
    label_matches = []
    abs_deltas = []
    for dup in duplicates:
        dup_response = responses.get((dup.slot, dup.presentation_id))
        src_response = responses.get((dup.slot, dup.source_presentation_id))
        label_match = None
        confidence_delta = None
        if dup_response and src_response and dup_response.usable and src_response.usable:
            label_match = dup_response.label == src_response.label
            confidence_delta = abs(dup_response.confidence - src_response.confidence)
            label_matches.append(label_match)
            abs_deltas.append(confidence_delta)
        per_judge.append(
            {
                "slot": dup.slot,
                "duplicate_presentation_id": dup.presentation_id,
                "source_presentation_id": dup.source_presentation_id,
                "duplicate_status": dup_response.status if dup_response else "missing",
                "source_status": src_response.status if src_response else "missing",
                "label_match": label_match,
                "confidence_delta": confidence_delta,
            }
        )
    return {
        "per_judge": per_judge,
        "summary": {
            "n_comparable": len(label_matches),
            "label_match_rate": (
                sum(label_matches) / len(label_matches) if label_matches else None
            ),
            "mean_abs_confidence_delta": (
                statistics.mean(abs_deltas) if abs_deltas else None
            ),
        },
    }


# ---------------------------------------------------------------------------
# Completeness
# ---------------------------------------------------------------------------


def completeness_report(
    judges: Sequence[Judge],
    control: BundleRecord,
    deck_bundles: Sequence[BundleRecord],
    duplicates: Sequence[DuplicateSlot],
    responses: Mapping[tuple[int, str], JudgeResponse],
    deck_stats: Sequence[DeckBundleStat] | None,
) -> dict:
    per_slot_status: dict[int, dict[str, int]] = {
        judge.slot: dict.fromkeys(VALID_STATUSES, 0) for judge in judges
    }
    for response in responses.values():
        per_slot_status[response.slot][response.status] += 1

    dup_by_slot = {d.slot: d for d in duplicates}
    missing_pairs = []
    for judge in judges:
        expected = {b.presentation_id for b in deck_bundles} | {control.presentation_id}
        if judge.slot in dup_by_slot:
            expected.add(dup_by_slot[judge.slot].presentation_id)
        present = {pid for (slot, pid) in responses if slot == judge.slot}
        for pid in sorted(expected - present):
            missing_pairs.append({"slot": judge.slot, "presentation_id": pid})

    excluded_bundles = []
    if deck_stats is not None:
        for stat in deck_stats:
            if not stat.included:
                excluded_bundles.append(
                    {
                        "presentation_id": stat.presentation_id,
                        "class": stat.klass,
                        "n_usable": stat.n_usable,
                        "reason": "n_usable < 3",
                    }
                )

    return {
        "per_slot_status": {str(slot): counts for slot, counts in per_slot_status.items()},
        "excluded_bundles": excluded_bundles,
        "missing_pairs": missing_pairs,
    }


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def _cross_check_presentation_hashes(unblinding: UnblindingData, presentation_hashes: dict) -> None:
    for entry in unblinding.raw.get("bundles", []):
        pid, sha = entry["presentation_id"], entry.get("sha256")
        if pid not in presentation_hashes:
            raise AnalysisError(f"presentation.json is missing bundle {pid!r}")
        if sha is not None and presentation_hashes[pid] != sha:
            raise AnalysisError(f"{pid}: unblinding sha256 != presentation.json sha256")
    for dup in unblinding.duplicates:
        if dup.presentation_id not in presentation_hashes:
            raise AnalysisError(
                f"presentation.json is missing duplicate bundle {dup.presentation_id!r}"
            )


def run_analysis(
    *,
    deck_dir: Path,
    judging_dir: Path,
    bootstrap_seed: int,
    out_dir: Path,
    bootstrap_b: int = DEFAULT_BOOTSTRAP_B,
) -> dict:
    """Full pipeline: load -> control-invalidation -> (deck stats) -> write.
    Returns the `analysis.json` body (before it is written) so tests and the
    CLI share one code path."""
    deck_dir, judging_dir, out_dir = Path(deck_dir), Path(judging_dir), Path(out_dir)

    judges = load_launch_manifest(judging_dir)
    load_judging_complete(judging_dir)  # presence/validity only
    responses = load_responses(judging_dir, judges)
    unblinding = load_unblinding(deck_dir)
    presentation_hashes = load_presentation_hashes(deck_dir)
    _cross_check_presentation_hashes(unblinding, presentation_hashes)

    control_bundles = [b for b in unblinding.bundles if b.is_control]
    if len(control_bundles) != 1:
        raise AnalysisError(
            f"expected exactly one control bundle in unblinding.json, found "
            f"{len(control_bundles)}"
        )
    control = control_bundles[0]
    deck_bundles = [b for b in unblinding.bundles if not b.is_control]

    control_diag = evaluate_control(control, judges, responses)
    duplicate_diag = duplicate_consistency(unblinding.duplicates, responses)
    agreement_rate = judge_agreement_rate(deck_bundles, judges, responses)

    input_hashes = {
        JUDGING_COMPLETE_FILENAME: _sha256_file(judging_dir / JUDGING_COMPLETE_FILENAME),
        UNBLINDING_FILENAME: _sha256_file(deck_dir / UNBLINDING_FILENAME),
        PRESENTATION_FILENAME: _sha256_file(deck_dir / PRESENTATION_FILENAME),
    }

    diagnostics = {
        "judge_agreement": {"rate": agreement_rate, "caveat": AGREEMENT_CAVEAT},
    }

    if not control_diag["valid"]:
        completeness = completeness_report(
            judges, control, deck_bundles, unblinding.duplicates, responses, None
        )
        analysis = {
            "schema_version": SCHEMA_VERSION,
            "batch_valid": False,
            "reason": "; ".join(control_diag["reasons"]) or "control invalidation failed",
            "control": control_diag,
            "diagnostics": diagnostics,
            "duplicate_consistency": duplicate_diag,
            "completeness": completeness,
            "input_hashes": input_hashes,
            "bootstrap_seed": bootstrap_seed,
        }
        _write_outputs(out_dir, analysis)
        return analysis

    deck_stats = compute_deck_bundle_stats(deck_bundles, judges, responses)
    included = [s for s in deck_stats if s.included]
    n_eff_info = kish_n_eff(deck_bundles, judges, responses)
    bootstrap = bootstrap_deck(deck_stats, bootstrap_seed, bootstrap_b)

    def _table(name: str, value: float | None) -> dict:
        return {
            "value": value,
            "k": n_eff_info["k"],
            "n_eff": n_eff_info["n_eff"],
            # n_eff is drawn from the FULL analysis deck (pairwise-complete
            # responses); `value`/`ci_95` are drawn from only the >=3-usable
            # bundles. Same disclosure repeated per row so a reader of any one
            # table row sees it without having to consult `n_eff` separately.
            "n_eff_population_note": N_EFF_POPULATION_NOTE,
            "ci_95": bootstrap[name]["ci_95"],
        }

    counts = {
        "human": sum(1 for s in deck_stats if s.klass == "human"),
        "bot": sum(1 for s in deck_stats if s.klass == "bot"),
        "included_human": sum(1 for s in included if s.klass == "human"),
        "included_bot": sum(1 for s in included if s.klass == "bot"),
    }
    deck = {
        "counts": counts,
        "n_eff_population_note": N_EFF_POPULATION_NOTE,
        "balanced_accuracy": _table("balanced_accuracy", balanced_accuracy(included)),
        "human_misclassification_rate": _table(
            "human_misclassification_rate", human_misclassification_rate(included)
        ),
        "auc": _table("auc", auc_mann_whitney(included)),
        "d_prime": _table("d_prime", d_prime(included)),
    }

    evidential_weight = {
        "basis": "n_eff",
        "value": n_eff_info["n_eff"],
        "note": (
            "panel evidential weight is stated in n_eff (effective independent "
            "judges), never raw k"
        ),
    }

    completeness = completeness_report(
        judges, control, deck_bundles, unblinding.duplicates, responses, deck_stats
    )
    per_judge = per_judge_deck_stats(deck_bundles, judges, responses)

    analysis = {
        "schema_version": SCHEMA_VERSION,
        "batch_valid": True,
        "control": control_diag,
        "deck": deck,
        "per_judge": per_judge,
        "bootstrap": {
            "seed": bootstrap_seed,
            "b_iterations": bootstrap_b,
            "stratified_by": "class",
            "disclosure": BOOTSTRAP_DISCLOSURE,
        },
        "n_eff": n_eff_info,
        "evidential_weight": evidential_weight,
        "diagnostics": diagnostics,
        "duplicate_consistency": duplicate_diag,
        "completeness": completeness,
        "input_hashes": input_hashes,
        "bootstrap_seed": bootstrap_seed,
    }
    _write_outputs(out_dir, analysis)
    return analysis


def render_report(analysis: Mapping) -> str:
    """Plain-text rendering of `analysis.json`. Deterministic (no wall-clock)."""
    lines = [
        f"S6 detection-pilot analysis (schema {analysis['schema_version']})",
        "=" * 60,
        "",
        f"batch_valid: {analysis['batch_valid']}",
    ]
    control = analysis["control"]
    lines += [
        "",
        "Control bundle",
        "-" * 60,
        f"  presentation_id:   {control['presentation_id']}",
        f"  mean_confidence:   {control['mean_confidence']}",
        f"  bot_label_count:   {control['bot_label_count']}/{control['k']} "
        f"(need >= {control['threshold_required']})",
        f"  valid:             {control['valid']}",
    ]
    if not analysis["batch_valid"]:
        lines += ["", f"reason: {analysis['reason']}"]
    else:
        deck = analysis["deck"]
        lines += [
            "", "Deck statistics (n_eff shown beside k, never used alone)", "-" * 60,
            f"  {deck['n_eff_population_note']}",
        ]
        for name in ("balanced_accuracy", "human_misclassification_rate", "auc", "d_prime"):
            table = deck[name]
            lines.append(
                f"  {name:32s} value={table['value']!r} k={table['k']} "
                f"n_eff={table['n_eff']!r} ci_95={table['ci_95']!r}"
            )
        lines += [
            "",
            f"evidential_weight (n_eff, never k): {analysis['evidential_weight']['value']!r}",
            f"n_eff_low: {analysis['n_eff'].get('n_eff_low')!r}",
            "",
            "Bootstrap",
            "-" * 60,
            f"  {analysis['bootstrap']['disclosure']}",
        ]
        per_judge = analysis["per_judge"]
        lines += [
            "",
            "Per-judge deck performance (§d.3 \"reported alongside\")",
            "-" * 60,
            f"  {per_judge['population_note']}",
        ]
        for row in per_judge["rows"]:
            lines.append(
                f"  slot={row['slot']} vendor={row['vendor']:16s} n_usable={row['n_usable']} "
                f"balanced_accuracy={row['balanced_accuracy']!r} "
                f"human_recall={row['human_recall']!r} bot_recall={row['bot_recall']!r} "
                f"human_misclassification_rate={row['human_misclassification_rate']!r} "
                f"mean_confidence_human={row['mean_confidence_human']!r}"
            )
    lines += [
        "",
        "Diagnostics",
        "-" * 60,
        f"  judge_agreement.rate: {analysis['diagnostics']['judge_agreement']['rate']!r}",
        f"  ({analysis['diagnostics']['judge_agreement']['caveat']})",
        "",
        "Duplicate consistency",
        "-" * 60,
        f"  {analysis['duplicate_consistency']['summary']}",
        "",
        "Completeness",
        "-" * 60,
        f"  excluded_bundles: {len(analysis['completeness']['excluded_bundles'])}",
        f"  missing_pairs:    {len(analysis['completeness']['missing_pairs'])}",
        "",
        f"input_hashes: {analysis['input_hashes']}",
        f"bootstrap_seed: {analysis['bootstrap_seed']}",
        "",
    ]
    return "\n".join(lines)


def _write_outputs(out_dir: Path, analysis: dict) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / ANALYSIS_FILENAME).open("w", encoding="utf-8") as fh:
        json.dump(analysis, fh, indent=2, sort_keys=True)
        fh.write("\n")
    (out_dir / REPORT_FILENAME).write_text(render_report(analysis), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="compute the S6 detection-pilot analysis")
    run.add_argument("--deck", type=Path, required=True, help="detection_corpus out-dir")
    run.add_argument("--judging", type=Path, required=True, help="detection_judge out-dir")
    run.add_argument("--bootstrap-seed", type=int, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--bootstrap-b", type=int, default=DEFAULT_BOOTSTRAP_B)
    args = parser.parse_args(argv)

    analysis = run_analysis(
        deck_dir=args.deck,
        judging_dir=args.judging,
        bootstrap_seed=args.bootstrap_seed,
        out_dir=args.out,
        bootstrap_b=args.bootstrap_b,
    )
    print(json.dumps({"batch_valid": analysis["batch_valid"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

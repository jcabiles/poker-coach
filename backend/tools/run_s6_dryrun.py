"""S6 acceptance dry run (flywheel S6 T7) — the whole pipeline, twice, on a stub judge.

Spec `docs/ai-dlc/specs/flywheel-s6.md` Verify-by item 2: build a small deck
through the SAME code paths the protocol deck uses, judge it with the
deterministic stub vendor over all five slots, analyse it, and prove the run is
reproducible — same master/order/bootstrap seeds ⇒ byte-identical canonical
outputs.

    detection_corpus.build_corpus  ->  deck/{presentation,unblinding}.json + _SUCCESS
    detection_judge.run            ->  judging/{launch,judging_complete}.json
                                        + order/slot-k.json + responses/slot-k/*.json
    detection_analysis.run_analysis->  analysis/{analysis.json,report.txt}

Two independent passes are written to `pass-a/` and `pass-b/` and then compared
file by file. Files are compared as BYTES except for the small, explicitly
declared set of volatile fields listed in `VOLATILE_FIELDS` below — those are
scrubbed before comparison and the reason each one is volatile is recorded
there. Anything else that differs is a determinism failure.

Deck shape — **the spec's Verify-by item 2 pins "6+6 + control + duplicates"**, so
the counts below are the pin, not a convenience. Only the SIZES are scaled:
every other §d pin is unchanged, including the rule-breaking control policy
((g.5) §A), so `non_protocol` is false in both manifests and this is the same
code path the real deck takes.

    6 human + 6 bot bundles of 5 hands + 1 control bundle + 5 judge duplicates
    = 18 presentation entries, of which each judge sees 14 (the 13 bundles plus
    ITS OWN duplicate — not the other four judges') => 14 x 5 = 70 judged pairs.

`DRY_MASTER_SEED` is chosen, not arbitrary. The stub judge's verdict is a
hash of `(presentation_id, slot)`, so whether the control bundle clears §d's
invalidation rule (mean confidence < 50 AND >= 4 of 5 "bot" labels) is a
property of the seed. This dry run needs the VALID branch, because the thing
being verified is that a full statistics block is produced; 20260808 is the
first seed in the S6 date family that yields it at this deck shape. The run
does not take that on trust: `_expected_stub_control` recomputes the stub's
five verdicts from first principles and asserts the analysis module's control
diagnostics match them.

Usage (from backend/, as a module — repo convention):

    python -m tools.run_s6_dryrun [--db-path ...] [--work-dir ...]

Exits 0 only if every assertion AND the two-pass comparison pass; any failure
prints the reason and exits non-zero.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import sys
from collections.abc import Sequence
from pathlib import Path

from app.domain.archetypes import VillainType
from tools import detection_analysis, detection_corpus, detection_judge
from tools.detection_render import leak_check

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORK_DIR = (
    _REPO_ROOT / "docs/ai-dlc/research/persona-realism-artifacts/detection-s6/dryrun"
)

# --- dry-run deck shape (sizes only; every other §d pin is the module default)
DRY_MASTER_SEED = 20260808
DRY_ORDER_SEED = 20260808
DRY_BOOTSTRAP_SEED = 20260808
DRY_BUNDLE_SIZE = 5
# 6 + 6 is the spec's Verify-by item 2 pin, not a tunable.
DRY_HUMAN_BUNDLES = 6
DRY_BOT_BUNDLES = 6  # must be >= the number of human position phases (deck audit)
DRY_BOT_HANDS = 60
DRY_CONTROL_HANDS = 60
DRY_JUDGES = 5
DRY_BOOTSTRAP_B = 10_000  # the pinned B — the dry run exercises the real value

PASSES = ("pass-a", "pass-b")

# Declared-volatile fields, with the reason each one cannot be deterministic.
# A JSON entry is a key PATH into the document (a tuple, not a dotted string —
# one of the keys is itself a filename containing a dot); the text entries below
# are VALUE-level substitutions. Everything else is compared byte for byte —
# including every other character of the lines those substitutions touch.
VOLATILE_FIELDS: dict[str, tuple[tuple[tuple[str, ...], str], ...]] = {
    "deck/_SUCCESS": (
        (("built_at",), "wall clock at build time"),
        (
            ("artifacts", "unblinding.json"),
            "sha256 OF a file that contains the volatile built_at — transitively volatile "
            "(presentation.json's hash, right beside it, is NOT excluded and is the "
            "determinism check that actually matters)",
        ),
    ),
    "deck/unblinding.json": ((("built_at",), "wall clock at build time"),),
    "judging/launch.json": ((("started_at",), "wall clock at preflight time"),),
    "analysis/analysis.json": (
        (
            ("input_hashes", "unblinding.json"),
            "sha256 OF a file that contains the volatile built_at — transitively volatile",
        ),
    ),
}
# Text files: replace only the volatile VALUE, never the line that carries it.
# `report.txt` prints the whole `input_hashes` dict on one line — dropping that
# line would also stop comparing the presentation.json and judging_complete.json
# hashes, which are NOT volatile and are exactly the digests a determinism check
# should be watching. So only the unblinding.json hash value is normalized.
VOLATILE_TEXT_PATTERNS: dict[str, tuple[tuple[re.Pattern[str], str, str], ...]] = {
    "analysis/report.txt": (
        (
            re.compile(r"('unblinding\.json': ')[0-9a-f]{64}(')"),
            r"\1<volatile>\2",
            "the unblinding.json hash inside the input_hashes line — transitively "
            "volatile; the other two hashes on that line stay byte-compared",
        ),
    ),
}


class DryRunFailure(AssertionError):
    """Any assertion or determinism check that must fail the run."""


def check(condition: bool, message: str) -> None:
    if not condition:
        raise DryRunFailure(message)


# ---------------------------------------------------------------------------
# One pass
# ---------------------------------------------------------------------------


def _judges_arg(n: int) -> str:
    return ",".join(f"stub:s6-dry-{slot}" for slot in range(n))


def run_pass(pass_dir: Path, db_path: Path) -> dict:
    """Build -> judge -> analyse into `pass_dir`; return the three documents."""
    deck_dir, judging_dir, analysis_dir = (
        pass_dir / "deck", pass_dir / "judging", pass_dir / "analysis"
    )
    success = detection_corpus.build_corpus(
        master_seed=DRY_MASTER_SEED,
        db_path=db_path,
        out_dir=deck_dir,
        bot_hands=DRY_BOT_HANDS,
        control_hands=DRY_CONTROL_HANDS,
        bundle_size=DRY_BUNDLE_SIZE,
        human_bundles=DRY_HUMAN_BUNDLES,
        bot_bundles=DRY_BOT_BUNDLES,
        judges=DRY_JUDGES,
    )
    completion = detection_judge.run(
        deck_dir,
        _judges_arg(DRY_JUDGES),
        DRY_ORDER_SEED,
        out_dir=judging_dir,
        env={},  # the stub needs no credential; hermetic by construction
        sleep=lambda _seconds: None,
    )
    analysis = detection_analysis.run_analysis(
        deck_dir=deck_dir,
        judging_dir=judging_dir,
        bootstrap_seed=DRY_BOOTSTRAP_SEED,
        out_dir=analysis_dir,
        bootstrap_b=DRY_BOOTSTRAP_B,
    )
    return {"success": success, "completion": completion, "analysis": analysis}


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------


def _expected_stub_control(control_presentation_id: str, judges: int) -> dict:
    """Recompute the stub judge's control verdicts independently of the harness.

    The point of the dry run is the plumbing, so the control's expected outcome
    is derived here from the stub adapter itself rather than read back out of
    the analysis it is supposed to be checking."""
    confidences = []
    for slot in range(judges):
        raw, _model = detection_judge.call_stub(
            "s6-dry", "", "", "", None, 0.0,
            context={"presentation_id": control_presentation_id, "slot": slot},
        )
        confidences.append(detection_judge.parse_judge_response(raw)["confidence_human"])
    labels = ["human" if c >= 50 else "bot" for c in confidences]
    return {
        "confidences": confidences,
        "bot_label_count": labels.count("bot"),
        "mean_confidence": statistics.mean(confidences),
    }


def assert_manifests(pass_dir: Path) -> None:
    deck = pass_dir / "deck"
    success = json.loads((deck / "_SUCCESS").read_text(encoding="utf-8"))
    check(success["counts"] == {
        "human": DRY_HUMAN_BUNDLES, "bot": DRY_BOT_BUNDLES, "control": 1,
    }, f"deck counts {success['counts']} are not 3 human / 3 bot / 1 control")
    check(success["non_protocol"] is False,
          "dry deck is stamped non_protocol — it should use the pinned control policy")
    check(success["judge_slots"] == DRY_JUDGES, "judge slot count mismatch in _SUCCESS")
    expected_entries = DRY_HUMAN_BUNDLES + DRY_BOT_BUNDLES + 1 + DRY_JUDGES
    check(success["presentation_entries"] == expected_entries,
          f"{success['presentation_entries']} presentation entries, expected {expected_entries}")

    presentation = json.loads((deck / "presentation.json").read_text(encoding="utf-8"))
    unblinding = json.loads((deck / "unblinding.json").read_text(encoding="utf-8"))
    pins = unblinding["pins"]
    forbidden = sorted(
        {
            *(v.value for v in VillainType),
            *pins["bot"]["lineup"].values(),
            pins["human"]["session_id"], pins["bot"]["run_id"],
            pins["control"]["run_id"], pins["bot"]["config_hash"],
            pins["control"]["control_policy"],
            pins["control"]["control_policy_source"], pins["git_sha"],
        } - {""}
    )
    for entry in presentation["bundles"]:
        pid = entry["presentation_id"]
        check(set(entry) <= {"presentation_id", "rendered_text", "sha256",
                             "duplicate_for_slot"},
              f"{pid}: unexpected key in the judge-facing manifest")
        violations = leak_check(entry["rendered_text"], forbidden=forbidden)
        check(not violations, f"{pid}: leak audit failed — {violations}")
        check(entry["sha256"] == detection_corpus.payload_digest(pid, entry["rendered_text"]),
              f"{pid}: sha256 is not the salted digest of its rendered_text")

    slots = unblinding["judge_duplicates"]["slots"]
    check(len(slots) == DRY_JUDGES, f"{len(slots)} duplicate slots, expected {DRY_JUDGES}")
    check(all(s["class"] == "human" for s in slots),
          "a judge duplicate is not drawn from the HUMAN class (§A.3)")
    phases_human = {
        p["phase_id"] for p in unblinding["position_phases"] if p["human_bundles"]
    }
    phases_bot = {p["phase_id"] for p in unblinding["position_phases"] if p["bot_bundles"]}
    check(phases_human == phases_bot,
          f"position phases differ between classes: {phases_human} vs {phases_bot}")


def assert_judging(pass_dir: Path, completion: dict) -> None:
    launch = json.loads((pass_dir / "judging" / "launch.json").read_text(encoding="utf-8"))
    check(len(launch["judges"]) == DRY_JUDGES, "launch manifest judge count mismatch")
    check(all(j["resolved_model"] for j in launch["judges"]),
          "launch manifest is missing a provider-resolved model id")
    # Each judge sees every deck bundle + the control + ONLY ITS OWN duplicate
    # — not the other judges' duplicates.
    per_judge_entries = DRY_HUMAN_BUNDLES + DRY_BOT_BUNDLES + 1 + 1
    expected_pairs = per_judge_entries * DRY_JUDGES
    check(completion["total"] == expected_pairs,
          f"{completion['total']} judged pairs, expected {expected_pairs}")
    for slot, counts in completion["per_slot"].items():
        check(counts["ok"] == per_judge_entries,
              f"slot {slot} judged {counts['ok']} entries, expected {per_judge_entries}")
    for slot, counts in completion["per_slot"].items():
        check(counts["malformed"] == 0 and counts["transport_failed"] == 0,
              f"slot {slot} has non-ok responses: {counts}")


def assert_analysis(pass_dir: Path, analysis: dict) -> None:
    control = analysis["control"]
    expected = _expected_stub_control(control["presentation_id"], DRY_JUDGES)
    check(sorted(control["usable_confidences"]) == sorted(expected["confidences"]),
          "analysis control confidences do not match the stub's own output")
    check(control["bot_label_count"] == expected["bot_label_count"],
          "analysis control bot-label count does not match the stub's own output")
    check(analysis["batch_valid"] is True,
          f"batch is INVALID — control diagnostics: {control['reasons']} "
          f"(the dry-run seed is chosen so the stub clears the control gate)")

    deck = analysis["deck"]
    check(deck["counts"]["human"] == DRY_HUMAN_BUNDLES
          and deck["counts"]["bot"] == DRY_BOT_BUNDLES,
          f"analysis deck counts {deck['counts']} do not match the built deck")
    for metric in ("balanced_accuracy", "human_misclassification_rate", "auc", "d_prime"):
        table = deck[metric]
        check(table["value"] is not None, f"statistics block: {metric} has no value")
        check(table["ci_95"] is not None, f"statistics block: {metric} has no bootstrap CI")
        check("n_eff" in table and "k" in table, f"statistics block: {metric} lacks n_eff/k")
    check(analysis["bootstrap"]["b_iterations"] == DRY_BOOTSTRAP_B, "bootstrap B mismatch")
    check(not analysis["completeness"]["missing_pairs"],
          f"completeness reports missing pairs: {analysis['completeness']['missing_pairs']}")
    check(not analysis["completeness"]["excluded_bundles"],
          "a bundle was excluded for < 3 usable judges in an all-ok stub run")


# ---------------------------------------------------------------------------
# Two-pass determinism
# ---------------------------------------------------------------------------


def _scrub(relative: str, raw: bytes) -> bytes:
    """Normalize ONLY the declared-volatile values in one file's bytes."""
    if relative in VOLATILE_FIELDS:
        document = json.loads(raw)
        for path, _reason in VOLATILE_FIELDS[relative]:
            node = document
            for part in path[:-1]:
                node = node[part]
            node.pop(path[-1], None)
        return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    patterns = VOLATILE_TEXT_PATTERNS.get(relative)
    if patterns:
        text = raw.decode("utf-8")
        for pattern, replacement, _reason in patterns:
            text, count = pattern.subn(replacement, text)
            if count != 1:
                raise DryRunFailure(
                    f"{relative}: expected exactly one volatile value matching "
                    f"{pattern.pattern!r}, found {count} — the report format moved and "
                    f"the comparison would silently stop covering it"
                )
        return text.encode("utf-8")
    return raw


def compare_passes(work_dir: Path) -> list[str]:
    """Byte-compare both passes' output trees; return the list of differences."""
    a, b = work_dir / PASSES[0], work_dir / PASSES[1]
    files_a = {str(p.relative_to(a)) for p in a.rglob("*") if p.is_file()}
    files_b = {str(p.relative_to(b)) for p in b.rglob("*") if p.is_file()}
    differences = [f"only in {PASSES[0]}: {name}" for name in sorted(files_a - files_b)]
    differences += [f"only in {PASSES[1]}: {name}" for name in sorted(files_b - files_a)]
    for name in sorted(files_a & files_b):
        if _scrub(name, (a / name).read_bytes()) != _scrub(name, (b / name).read_bytes()):
            differences.append(f"differs: {name}")
    return differences


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db-path", type=Path, default=detection_corpus.DEFAULT_DB_PATH,
                        help="owner Simulate SQLite DB (opened read-only)")
    parser.add_argument("--work-dir", type=Path, default=DEFAULT_WORK_DIR,
                        help="output root (gitignored); wiped and rebuilt on every run")
    args = parser.parse_args(argv)

    work_dir = Path(args.work_dir)
    shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    print("S6 dry run — master/order/bootstrap seed "
          f"{DRY_MASTER_SEED}/{DRY_ORDER_SEED}/{DRY_BOOTSTRAP_SEED}")
    print(f"  deck: {DRY_HUMAN_BUNDLES} human + {DRY_BOT_BUNDLES} bot bundles of "
          f"{DRY_BUNDLE_SIZE} hands + control + {DRY_JUDGES} judge duplicates")
    try:
        for name in PASSES:
            pass_dir = work_dir / name
            documents = run_pass(pass_dir, Path(args.db_path))
            assert_manifests(pass_dir)
            assert_judging(pass_dir, documents["completion"])
            assert_analysis(pass_dir, documents["analysis"])
            deck = documents["analysis"]["deck"]
            print(f"  {name}: OK — {documents['completion']['total']} judged pairs, "
                  f"batch_valid={documents['analysis']['batch_valid']}, "
                  f"balanced_accuracy={deck['balanced_accuracy']['value']}")
    except Exception as exc:  # noqa: BLE001 — any failure fails the run
        print(f"DRY RUN FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("  declared-volatile values normalized before comparison "
          "(everything else is byte-compared):")
    for relative, fields in VOLATILE_FIELDS.items():
        for path, reason in fields:
            print(f"    {relative}::{'.'.join(path)} — {reason}")
    for relative, patterns in VOLATILE_TEXT_PATTERNS.items():
        for pattern, _replacement, reason in patterns:
            print(f"    {relative}::/{pattern.pattern}/ — {reason}")

    differences = compare_passes(work_dir)
    if differences:
        print("DRY RUN FAILED: the two passes are not byte-identical:", file=sys.stderr)
        for difference in differences:
            print(f"  {difference}", file=sys.stderr)
        return 1
    file_count = sum(1 for p in (work_dir / PASSES[0]).rglob("*") if p.is_file())
    print(f"  determinism: OK — {file_count} files byte-identical across both passes")
    print("S6 DRY RUN PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

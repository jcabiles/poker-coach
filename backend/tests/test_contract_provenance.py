"""W5-a1 — the target-provenance gate, as a tripwire rather than a convention.

No gate validated a TARGET. D7 (contract §6) validates the *instrument*; §7's
anti-laundering rule gives the *measured comparator* immutability and an audit
trail. The §5 keystone table had neither — and §2's softmax law CONSUMES a
target, so against a wrong one the engine converges confidently onto wrong
behavior and reports success.

Ledger #14 is the proof: a 6-max VPIP/PFR band sat in §5 through the whole
preflop program. It was never load-bearing in CI (metric #3 is never compared to
§5 — its only assertion is `0.0 <= pfr <= vpip <= 1.0`), so the harm channel was
human and agent judgement. This test closes the loop the only way a test can:
it makes an un-sourced row impossible to LAND, which is what makes W5-a2's audit
mechanically verifiable rather than a promise.

What it enforces: every data row of a `<!-- provenance-gate: keystone -->` table
in §5 has an entry in the §5a registry carrying either a
`(format, pool/stakes, source)` triple or the literal `[UNVERIFIED]`.

What it deliberately does NOT enforce (checklist-gated via §11 item 15 instead,
because neither is decidable from the contract text alone): that a citing ticket
actually quotes the triple, and that no HARD gate rests on an `[UNVERIFIED]` row.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

CONTRACT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "ai-dlc"
    / "contracts"
    / "persona-realism-theory-contract.md"
)

_KEYSTONE_MARKER = "<!-- provenance-gate: keystone -->"
_UNVERIFIED = "[UNVERIFIED]"
# A registry row must name a format, a pool and a source. Three non-empty cells
# beyond the label; an em-dash or a bare "-" reads as EMPTY, so a row cannot be
# waved through with placeholder punctuation.
_EMPTY_CELL = re.compile(r"^[\s\-–—]*$")


def _text() -> str:
    if not CONTRACT.exists():  # pragma: no cover - repo layout guard
        pytest.fail(f"theory contract not found at {CONTRACT}")
    return CONTRACT.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    """The slice of `text` between two `## ` headings, end-exclusive."""
    i = text.find(start)
    if i < 0:  # pragma: no cover - guarded by test_sections_exist
        pytest.fail(f"contract section {start!r} not found")
    j = text.find(end, i + len(start))
    return text[i:j] if j > 0 else text[i:]


def _cells(line: str) -> list[str]:
    """Markdown table row -> its cells, outer pipes stripped."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|[\s:\-|]+\|", line.strip()))


def _normalise(label: str) -> str:
    """Registry key from a table label.

    Strips markdown emphasis and any trailing `[...]` status tag, so
    `Fold-to-C-bet aggregate [**HARD-today**]` and the registry's
    `Fold-to-C-bet aggregate` are the same key.
    """
    label = re.sub(r"\[[^\]]*\]", " ", label)  # drop [HARD-today], [DIR, #6], ...
    label = label.replace("*", "").replace("`", "")
    label = label.replace("†", " ").replace("‡", " ").replace("⚠", " ")
    return re.sub(r"\s+", " ", label).strip().casefold()


def _keystone_rows(section5: str) -> list[str]:
    """Labels of every gated data row in §5.

    A row is gated when it sits in a table introduced by the keystone marker.
    Skipped: the header row, the `---|---` separator, and any label wrapped in
    asterisks — italics mark an OBSERVATION (e.g. the live 150-hand read), not a
    target, and observations carry no provenance obligation.
    """
    rows: list[str] = []
    in_table = False
    seen_header = False
    for line in section5.splitlines():
        stripped = line.strip()
        if _KEYSTONE_MARKER in stripped:
            in_table, seen_header = True, False
            continue
        if not in_table:
            continue
        if not stripped.startswith("|"):
            in_table = False  # blank line or prose ends the table
            continue
        if _is_separator(stripped):
            continue
        if not seen_header:
            seen_header = True  # first pipe row after the marker is the header
            continue
        label = _cells(stripped)[0]
        if not label or label.startswith("*"):
            continue  # observational row, not a target
        rows.append(label)
    return rows


def _registry(section5a: str) -> dict[str, list[str]]:
    """§5a registry -> {normalised row key: [format, pool, source, status]}.

    Reads the FIRST table in §5a and stops there (W5-a2-g). The original version
    tracked `seen_header` once for the whole section and consumed every pipe-row
    in it, so a *second* §5a table — a source list, say — had its rows AND its
    header parsed as registry entries (`s1`, `s2`, `source`), which then tripped
    `test_registry_has_no_orphan_rows` and blocked a legitimate edit. W5-a2 hit
    exactly that and had to work around it with a bulleted list. A tripwire that
    fires on correct edits trains people to route around it, so the fix is worth
    more than the bug it prevented.
    """
    out: dict[str, list[str]] = {}
    seen_header = False
    in_table = False
    for line in section5a.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            # A non-pipe line ends the table. Once the first table has been
            # read, everything after it in §5a is prose or another table --
            # neither is the registry.
            if in_table:
                break
            continue
        in_table = True
        if _is_separator(stripped):
            continue
        cells = _cells(stripped)
        if not seen_header:
            seen_header = True
            continue
        if len(cells) < 5:
            continue
        out[_normalise(cells[0])] = cells[1:5]
    return out


def test_registry_reads_only_the_first_table():
    """W5-a2-g regression pin. §5a may carry a second table (a source list, a
    confidence key) below the registry; those rows are NOT registry entries.

    Before the fix, every pipe-row in §5a was consumed and the second table's
    header leaked in as a row named `source`, so adding a source table made the
    orphan check fail. Guard the parser, not just the current document, because
    the document is exactly what a future slice will edit.
    """
    section = (
        "## 5a. Registry\n"
        "| Row | Format | Pool | Source | Status |\n"
        "|---|---|---|---|---|\n"
        "| VPIP | 9-max | micro NL | specialist | VERIFIED |\n"
        "\n"
        "Prose, then a second table that is NOT the registry:\n"
        "\n"
        "| Source | Author | Formats | Stats | Tier |\n"
        "|---|---|---|---|---|\n"
        "| S1 | some author | both | 15 | strong |\n"
        "| S2 | another | both | WTSD | independent |\n"
    )
    reg = _registry(section)
    assert set(reg) == {"vpip"}, f"second table leaked into the registry: {sorted(reg)}"


def test_contract_sections_exist():
    """§5a and §11 item 15 are the non-executable half of W5-a1; if either is
    deleted the gate is decorative, so pin their existence too."""
    text = _text()
    assert "## 5a. Target provenance registry" in text, "contract §5a missing"
    assert "[Target provenance — §5a]" in text, "§11 item 15 (provenance) missing"
    assert _KEYSTONE_MARKER in text, "no §5 table is marked as provenance-gated"


def test_every_keystone_row_has_provenance():
    """The tripwire: no §5 keystone row may exist without a triple or [UNVERIFIED].

    This is what makes W5-a2's audit mechanically verifiable — it cannot land a
    row without provenance, and it cannot quietly drop one either.
    """
    text = _text()
    rows = _keystone_rows(_section(text, "## 5. ", "## 5a. "))
    registry = _registry(_section(text, "## 5a. ", "## 6. "))

    assert rows, "found no gated §5 rows — the keystone marker or parser is broken"

    missing: list[str] = []
    incomplete: list[str] = []
    for label in rows:
        entry = registry.get(_normalise(label))
        if entry is None:
            missing.append(label)
            continue
        fmt, pool, source, status = entry
        if _UNVERIFIED in fmt or _UNVERIFIED in status:
            continue  # explicitly, auditably unsourced — allowed, never HARD-gatable
        if any(_EMPTY_CELL.match(c) for c in (fmt, pool, source)):
            incomplete.append(
                f"{label}: format={fmt!r} pool={pool!r} source={source!r}"
            )

    assert not missing, (
        "§5 keystone rows absent from the §5a provenance registry "
        f"(add a (format, pool, source) triple or mark {_UNVERIFIED}): {missing}"
    )
    assert not incomplete, (
        "§5a registry rows claiming provenance but missing part of the triple "
        f"(all three of format/pool/source must be non-empty): {incomplete}"
    )


def test_registry_has_no_orphan_rows():
    """A registry entry with no matching §5 row means a target was renamed or
    deleted and its provenance was left behind — the audit trail silently
    decays. Catch it while the rename is still fresh."""
    text = _text()
    rows = {_normalise(r) for r in _keystone_rows(_section(text, "## 5. ", "## 5a. "))}
    registry = _registry(_section(text, "## 5a. ", "## 6. "))
    orphans = sorted(set(registry) - rows)
    assert not orphans, (
        f"§5a registry entries with no matching §5 keystone row: {orphans}"
    )


def test_format_sensitivity_lists_are_declared():
    """§5a must state which stats may cross table sizes and which may not.
    Ledger #14 happened because that distinction lived only in a reviewer's
    head; a transfer is legitimate ONLY against a written list."""
    section5a = _section(_text(), "## 5a. ", "## 6. ")
    assert "Format-SENSITIVE" in section5a, "§5a must list format-SENSITIVE stats"
    assert "Format-INVARIANT" in section5a, "§5a must list format-INVARIANT stats"
    for stat in ("VPIP", "PFR", "fold-to-c-bet", "WTSD"):
        assert stat in section5a, f"format-sensitivity lists omit {stat}"


def test_w3r1_infeasibility_rule_is_stated():
    """The second obligation. Three slices hit the alpha wall and each escaped by
    node-scoping rather than re-opening the target; the rule that names that
    anti-pattern has to be findable in the contract, not just the roadmap."""
    section5a = _section(_text(), "## 5a. ", "## 6. ")
    assert "W3R-1 rule" in section5a
    assert "provenance" in section5a.casefold()

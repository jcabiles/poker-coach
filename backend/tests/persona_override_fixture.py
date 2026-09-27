"""Shared test helper: a temp copy of the real persona packs plus 6-max override files.

`write_fixture_content(tmp_path)` returns a folder usable as
`load_persona_packs(folder, table_size=...)`'s `content_dir` (or as a
monkeypatched `PERSONA_DIR`). It holds a copy of every shipped
`content/personas/*.json` and, under `six_max/`, one override file per entry
of `overrides` (file stem -> file body). With no `overrides`, it writes the
default `six_max/lag.json` below, whose LAG opens ONLY AA when the pot is
unopened: one wildcard node whose single mix is AA -> raise 1.0, so every
other hand class folds with no random draw.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

PERSONAS_DIR = Path(__file__).resolve().parents[2] / "content" / "personas"

# The shipped LAG's aggression is 3.2; the override's value must differ so a
# merged pack is distinguishable from the base.
OVERRIDE_AGGRESSION = 1.0

DEFAULT_LAG_OVERRIDE: dict = {
    "id": "override_lag_6max",
    "version": "1",
    "domain": "persona_override",
    "_doc": ["test fixture: at 6-max the LAG opens only AA when the pot is unopened"],
    "persona": "lag",
    "table_size": 6,
    "preflop": {
        "unopened": [
            {
                "facing": "unopened",
                "mixes": [{"combos": "AA", "weights": {"raise": 1.0}}],
            }
        ]
    },
    "postflop": {"aggression": OVERRIDE_AGGRESSION},
}


def write_fixture_content(tmp_path: Path, overrides: dict[str, dict] | None = None) -> Path:
    """Copy the real persona packs into `tmp_path/personas` and write each
    override as `six_max/<stem>.json`. Returns the personas folder."""
    folder = tmp_path / "personas"
    folder.mkdir()
    for path in PERSONAS_DIR.glob("*.json"):
        shutil.copy(path, folder / path.name)
    six_max = folder / "six_max"
    six_max.mkdir()
    if overrides is None:
        overrides = {"lag": DEFAULT_LAG_OVERRIDE}
    for stem, body in overrides.items():
        (six_max / f"{stem}.json").write_text(json.dumps(body))
    return folder

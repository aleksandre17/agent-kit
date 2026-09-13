"""Gate kind that holds a drawn tree to its floor (ADR-015, amendment 1).

The blueprint's Part VI drawing states, for one side, the fixed set of paths that must exist in
their drawn place by their drawn name -- "what is on the drawing must be at least like that"
(amendment 1). This module knows neither the drawing nor a single path of it: it reads a LAYOUT
declaration (`kit/schemas/layout.schema.json`) and reports, generically, which drawn paths are
missing.

A path whose real content belongs to a later link is named `pending` IN THE DECLARATION, never
guessed here -- the gate prints every pending entry and fails only on a path that is neither
present nor declared pending. That is the honesty rule this gate exists to hold: a drawn path with
no content and no `pending` entry is a defect, and a fabricated placeholder would hide it, not fix
it.

`side` in params narrows the reading to one box of the drawing when a declaration ever carries
both (it does not yet -- L2 adds the host side as a document of its own, read the same way).
"""

from __future__ import annotations

import json
from pathlib import Path

import validation

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "layout.schema.json"


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def evaluate(workspace, declaration_rel: str, side: str | None = None):
    """Pure: given a workspace and a layout declaration path, return `(failures, pending)`.

    Exposed apart from the KIND entry so a caller outside `check` -- a unit test, a future host
    wiring -- can read the same report without a `check`-shaped `ctx`."""
    if not workspace.exists(declaration_rel):
        return [f"{declaration_rel}: the layout declaration itself is absent"], []
    doc = workspace.read_json(declaration_rel)
    errors = validation.validate(doc, _schema())
    if errors:
        return [f"{declaration_rel}: {e}" for e in errors], []

    failures, pending = [], []
    for entry in doc["entries"]:
        if side is not None and doc.get("side") != side:
            continue
        if "pending" in entry:
            pending.append(entry)
            continue
        if not workspace.exists(entry["path"]):
            failures.append(f"{entry['path']}: drawn path is missing ({entry.get('drawn_as', entry['path'])})")
    return failures, pending


def _layout_floor_present(ctx, params):
    failures, _pending = evaluate(ctx.workspace, params["declaration"], params.get("side"))
    return failures


KINDS = {"layout-floor-present": _layout_floor_present}

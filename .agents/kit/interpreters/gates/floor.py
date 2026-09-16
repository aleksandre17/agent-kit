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

A row whose `capability` names a capability id is installed by that capability alone -- read from
`kit/capabilities/<id>/capability.json`'s own `installs`, never guessed here. On a host that has
not enabled it, the row's path simply does not exist yet, by that host's own declared choice, and
that is not a floor failure: the row is SKIPPED and printed as `NOT ENABLED`, so it is named rather
than silently dropped (Cardinal V). A row with no `capability` always applies. The enabled set is
supplied by the caller (`ctx.enabled_capabilities()`, the one reading every gate uses); a caller
that passes none gets the old, unfiltered behaviour -- every entry is checked regardless of any
`capability` it names.

The rows are governance's `host_layout` DOCUMENT -- read from the kit that speaks, which on a host
running its own pinned copy is the in-tree file -- plus the `floor` rows of every capability. A
capability's own rows carry that capability as their condition, so they bite exactly when a host
has enabled it (link L3a: a runtime adapter declares the directory its product reads, and kit/
stays free of product names). `side` narrows the reading to one box of the drawing.
"""

from __future__ import annotations

import json
from pathlib import Path

import validation

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "layout.schema.json"


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _entry_schema() -> dict:
    """The shape of ONE drawn row -- the `entries` item of the layout schema, its one home. A
    capability's own `floor` rows are held to exactly this, never to a second copy of it."""
    return _schema()["properties"]["entries"]["items"]


def evaluate_rows(workspace, rows, enabled=None):
    """Pure: `(failures, pending, not_enabled)` for a list of drawn rows already read.

    `enabled`, when given, is an iterable of enabled capability ids. A row naming a `capability`
    not in that set is skipped -- it is neither a failure nor a `pending` entry, it is reported in
    `not_enabled` instead. `enabled=None` checks every row regardless of any `capability` it
    names, which is the behaviour a caller with no host context gets."""
    enabled_ids = None if enabled is None else set(enabled)
    failures, pending, not_enabled = [], [], []
    for entry in rows:
        if enabled_ids is not None and entry.get("capability") and entry["capability"] not in enabled_ids:
            not_enabled.append(entry)
            continue
        if "pending" in entry:
            pending.append(entry)
            continue
        if not workspace.exists(entry["path"]):
            failures.append(f"{entry['path']}: drawn path is missing ({entry.get('drawn_as', entry['path'])})")
    return failures, pending, not_enabled


def evaluate(workspace, declaration_rel: str, side: str | None = None, enabled=None):
    """Pure: given a workspace and a layout declaration path, return
    `(failures, pending, not_enabled)` -- `evaluate_rows` over that declaration's entries.

    Exposed apart from the KIND entry so a caller outside `check` -- a unit test reading the
    upstream drawing -- can read the same report without a `check`-shaped `ctx`."""
    if not workspace.exists(declaration_rel):
        return [f"{declaration_rel}: the layout declaration itself is absent"], [], []
    doc = workspace.read_json(declaration_rel)
    errors = validation.validate(doc, _schema())
    if errors:
        return [f"{declaration_rel}: {e}" for e in errors], [], []
    if side is not None and doc.get("side") != side:
        return [], [], []
    return evaluate_rows(workspace, doc["entries"], enabled)


def host_rows(capabilities, document: str, side: str | None = None) -> tuple:
    """(rows, errors): the drawn floor a host is held to -- the rows of the layout DOCUMENT a
    capability ships under that id, plus the `floor` rows of every capability handed in, each
    carrying the capability that declared it as its condition. The kit that speaks is the one read:
    on a host running its own pinned copy, that is the in-tree file, never a vendored second copy."""
    rows, errors = [], []
    for capability in capabilities:
        doc = capability.documents.get(document)
        if doc is not None and (side is None or doc.get("side") == side):
            rows.extend(doc["entries"])
    entry = _entry_schema()
    for capability in capabilities:
        for row in capability.raw.get("floor", []):
            found = validation.validate(row, entry)
            if found:
                errors.extend(f"capability {capability.id!r} floor row {row!r}: {e}" for e in found)
                continue
            rows.append({**row, "capability": capability.id})
    return rows, errors


def _layout_floor_present(ctx, params):
    capabilities = ctx.enabled_capabilities()
    rows, errors = host_rows(ctx.manifest.capabilities, params["document"], params.get("side"))
    if not rows and not errors:
        return [f"no enabled capability ships a layout document named {params['document']!r}"]
    failures, pending, not_enabled = evaluate_rows(
        ctx.workspace, rows, enabled={c.id for c in capabilities})
    for entry in pending:
        print(f"        PENDING  {entry['path']}  (link {entry['pending']}"
              + (f", {entry['capability']}" if entry.get("capability") else "") + ")")
    for entry in not_enabled:
        print(f"        NOT ENABLED  {entry['path']}  ({entry['capability']})")
    return errors + failures


KINDS = {"layout-floor-present": _layout_floor_present}

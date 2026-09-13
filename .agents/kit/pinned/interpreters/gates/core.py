"""Gate kinds that hold the kit's own four-class seam.

A gate KIND is a generic evaluator: it takes the context and its params as DATA and returns a
list of failures, never a verdict about anything it was not handed. Which gates run against which
paths is declared by capabilities; this module knows no capability, path, stack or runtime.

These five were the whole registry until it stopped being a hand-edited dict in `check`. They are
unchanged: a gate module is DISCOVERED now, so a capability that brings new kinds brings its own
file and the verb is never edited. An interpreter that must be modified to admit a new kind was
never open (Cardinal II).
"""

from __future__ import annotations

import re

import render as render_verb


def _schema_valid(ctx, params):
    target = params["file"]
    if not ctx.workspace.exists(target):
        return [f"{target}: declared BINDING file is absent"]
    return [f"{target}: {e}" for e in ctx.manifest.validate(ctx.workspace.read_json(target), params["schema"])]


def _path_class_total(ctx, params):
    """Every file the kit produced must resolve to exactly ONE declared class."""
    declared = ctx.class_declarations()
    failures = []
    for rel in ctx.workspace.files_under(params["root"]):
        classes = {
            klass for prefix, klass in declared
            if rel == prefix or rel.startswith(prefix)
        }
        if len(classes) != 1:
            failures.append(f"{rel}: resolves to {sorted(classes) or 'no'} class")
    return failures


def _projection_reproducible(ctx, params):
    """The plane on disk must be exactly what VENDOR + BINDING imply -- byte for byte."""
    expected = render_verb.projections(ctx)
    failures = []
    for rel, body in expected.items():
        if not ctx.workspace.exists(rel):
            failures.append(f"{rel}: projected path is missing")
        elif ctx.workspace.read_text(rel) != body:
            failures.append(f"{rel}: on disk differs from what the declaration renders")
    plane = next(p["root"] for p in ctx.manifest.planes if p["class"] == "projection")
    for rel in ctx.workspace.files_under(plane):
        if rel not in expected:
            failures.append(f"{rel}: present in the projection plane but nothing renders it")
    return failures


def _reading_current(ctx, params):
    """A second reading of one reality is isolated and dated, never merged into the first."""
    recorded = ctx.workspace.read_json(params["file"])
    fresh = ctx.take_reading()
    if recorded["facts"] != fresh["facts"]:
        return [
            f"{params['file']}: the reading taken at {recorded['taken_at']} says "
            f"{recorded['facts']}, a reading taken at {fresh['taken_at']} says {fresh['facts']}"
        ]
    return []


def _title_claim_within_authority(ctx, params):
    """A NAME is a claim; a LOCATION is a grant. This gate compares the two and never reads a
    word of the content, because authority was never a property of prose.

    Both halves arrive as data: which locations grant declaring authority, and which name shapes
    claim it. The interpreter knows no kind, no prefix and no document. A file that claims nothing
    is not judged at all -- the gate exists to catch a claim that outruns its grant, not to
    police what a host may keep on its shelves.
    """
    grants = {k["path"].rstrip("/"): k["declares"] for k in params["kinds"]}
    claims = [(c["id"], re.compile(c["pattern"])) for c in params["claims"]]
    failures = []
    for rel in ctx.workspace.files_under(params["root"]):
        name = rel.rsplit("/", 1)[-1]
        claimed = [cid for cid, pattern in claims if pattern.search(name)]
        if not claimed:
            continue
        granting = [
            path for path in grants
            if rel.startswith(path + "/") and grants[path]
        ]
        if granting:
            continue
        located = sorted(path for path in grants if rel.startswith(path + "/"))
        where = f"kind {located[0]!r}, which cannot declare" if located else "no declared kind"
        failures.append(
            f"{rel}: the name claims DECLARING authority ({', '.join(sorted(claimed))}), "
            f"but it lives in {where}. Move it, promote it, or rename it -- "
            f"a rule whose location cannot grant its claim binds no one, and the reader cannot tell."
        )
    return failures


KINDS = {
    "title-claim-within-authority": _title_claim_within_authority,
    "schema-valid": _schema_valid,
    "path-class-total": _path_class_total,
    "projection-reproducible": _projection_reproducible,
    "reading-current": _reading_current,
}

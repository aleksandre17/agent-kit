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

import json
import re

import projection


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
    expected = projection.projections(ctx)
    failures = []
    for rel, body in expected.items():
        if not ctx.workspace.exists(rel):
            failures.append(f"{rel}: projected path is missing")
        elif ctx.workspace.read_text(rel) != body:
            failures.append(f"{rel}: on disk differs from what the declaration renders")
    plane = ctx.manifest.plane("projection")
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
            f"{recorded['facts']}, a reading taken at {fresh['taken_at']} says {fresh['facts']}. "
            f"If the host moved on purpose, its owner replaces the reading: `retake --plan`, then "
            f"`retake --approve <who>`"
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


def _calibrate_schema_valid(host):
    """A binding file that does not honour its schema is flagged; one that does is admitted."""
    params = {"file": "declared.json", "schema": "arbitration"}
    stated = {"schema_version": host({}).manifest.version_of(params["schema"])}  # the schema's own
    specimen = host({"declared.json": json.dumps(stated)})
    lookalike = host({"declared.json": json.dumps(dict(stated, window_minutes=0))})
    return _schema_valid(specimen, params), _schema_valid(lookalike, params)


def _calibrate_path_class_total(host):
    """A file no class declaration covers is flagged; one exactly one covers is admitted."""
    declared = {"class_declarations": lambda: [("plane/kept/", "vendor")]}
    params = {"root": "plane"}
    specimen = host({"plane/kept/a.txt": "a", "plane/stray.txt": "b"}, **declared)
    lookalike = host({"plane/kept/a.txt": "a"}, **declared)
    return _path_class_total(specimen, params), _path_class_total(lookalike, params)


KINDS = {
    "title-claim-within-authority": _title_claim_within_authority,
    "schema-valid": _schema_valid,
    "path-class-total": _path_class_total,
    "projection-reproducible": _projection_reproducible,
    "reading-current": _reading_current,
}

#: Each kind's calibration: the specimen it must flag and the lookalike it must admit.
CALIBRATIONS = {
    "schema-valid": _calibrate_schema_valid,
    "path-class-total": _calibrate_path_class_total,
}

#: A projection renders the governed records (the board among them): it may never prove one (ADR-025 decision 16).
READS_THE_RECORDS = {"projection-reproducible": True}

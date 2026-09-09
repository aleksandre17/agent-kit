"""check -- run the declared gates, report, never repair.

The gates are not listed here. Each capability DECLARES the gates that hold its own installs, and
this verb interprets gate KINDS: an open registry of generic evaluators, each taking its params as
data. A new gate is a row in a capability declaration; a new gate KIND is one registration. Nothing
here knows the name of any capability, path, stack or runtime.
"""

from __future__ import annotations

import render as render_verb
from errors import KitError

SUMMARY = "run the declared fitness functions and report"


class GateError(KitError):
    """A declaration named a gate kind this interpreter cannot evaluate."""


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


GATE_KINDS = {
    "schema-valid": _schema_valid,
    "path-class-total": _path_class_total,
    "projection-reproducible": _projection_reproducible,
    "reading-current": _reading_current,
}


def run(ctx, args) -> int:
    failed = 0
    for capability in ctx.enabled_capabilities():
        for gate in capability.gates:
            kind = gate["kind"]
            if kind not in GATE_KINDS:
                raise GateError(
                    f"capability {capability.id!r} declares gate kind {kind!r}; "
                    f"registered kinds are {sorted(GATE_KINDS)}"
                )
            failures = GATE_KINDS[kind](ctx, gate.get("params", {}))
            print(f"  {'FAIL' if failures else 'PASS'}  {gate['id']}  ({kind})")
            for failure in failures:
                print(f"        {failure}")
            failed += 1 if failures else 0
    print(f"check: {failed} gate(s) failed")
    return 1 if failed else 0

"""Context held to its budget -- what every served surface makes a runtime read, measured (ADR-024).

Every token a runtime reads is paid for again on every later call of the run. So what the kit serves
is MEASURED, per surface and per context LAYER, on every `check`:

  * `always` -- loaded on every turn (an entry file, whole: the product loads the host's text around
    the kit's span too). It should carry laws and pointers only;
  * `indexed` -- a member loaded by its name and description on every turn and by its body only when
    activated (a skill, a delegated role): the index is what every turn pays, the body what one
    activation pays;
  * `on-demand` -- read when something points at it (a scoped briefing, a page a section points to,
    a skill's supporting file).

The layers are this module's: each is a way of COUNTING, published below beside the measure it
yields, and a render row names the one its file is loaded into. A new layer is a row here. What a
layer may cost is never spelled here: the kit's DEFAULT ceiling for each measure, and the estimator
that turns bytes into tokens, are declared in the `context` document; a product's own hard limit is
declared on its surface; and a host's own number is a budget row in its corpus map, held by the
ratchet (one home for a host's number, ADR-019 decision 9). Where the host has budgeted a measure, its
row binds and the default is silent.

A section a briefing INLINES that is larger than the declared inline limit is REPORTED as one a pointer
would carry on demand -- advice, never a failure: what binds on every turn is the host's call.
"""

from __future__ import annotations

import json
import math

import corpus
import declared
import gatekinds
import projection
import serving
from errors import KitError

KIND = "context-held"
CONTEXT = {declared.CONTRACT: "context"}
SURFACES = ({declared.CONTRACT: "runtime-surface"}, "surfaces")


def _files(rows, produced, layer):
    return [(r["path"], len(produced.get(r["path"], "").encode("utf-8")), r) for r in rows if r.get("layer") == layer]


def _always_total(rows, produced, pages):
    found = _files(rows, produced, "always")
    return sum(size for _p, size, _r in found), ", ".join(p for p, _s, _r in found)


def _index_total(rows, produced, pages):
    found = [r for r in rows if r.get("layer") == "indexed"]
    return sum(r.get("index_bytes", 0) for r in found), f"{len(found)} indexed member(s)"


def _largest(layer):
    def count(rows, produced, pages):
        found = _files(rows, produced, layer) + (pages if layer == "on-demand" else [])
        if not found:
            return 0, "nothing"
        path, size, _row = max(found, key=lambda f: f[1])
        return size, path
    return count


#: measure -> (layer, how it is counted). The registry this module PROVIDES: a measure is a way of
#: counting one layer, and the ratchet holds a host's budget row over it like any other measure.
COUNTS = {
    "always_loaded_tokens": ("always", _always_total),
    "indexed_tokens": ("indexed", _index_total),
    "activated_body_tokens": ("indexed", _largest("indexed")),
    "on_demand_page_tokens": ("on-demand", _largest("on-demand")),
}
#: The layers this module measures, each with its counting -- a layer a render row may name.
LAYERS = {layer: count for layer, count in COUNTS.values()}


class ContextError(KitError):
    """The `context` document is missing or declared twice, or a surface renders into a layer this
    kit does not measure."""

    code = "KIT0076"


def document(ctx) -> dict:
    found = declared.sources(ctx, declared.named(ctx.enabled_capabilities(), CONTEXT))
    if len(found) != 1:
        raise ContextError(f"exactly one document must keep the `context` contract; {len(found)} do")
    return next(iter(found.values()))


def _ceilings(ctx) -> dict:
    """measure -> the ceiling this HOST budgeted (its corpus map's row), read through the module that
    owns those rows. A host that maps no corpus has budgeted nothing."""
    found = {}
    readers = gatekinds.registry("CEILINGS")
    for capability in ctx.enabled_capabilities():
        for gate in capability.gates:
            if gate["kind"] in readers:
                try:
                    found.update(readers[gate["kind"]](ctx, gate.get("params", {})))
                except KitError as exc:  # its row holds no ceiling here: said, so a default is never misread
                    print(f"        UNREAD  {gate['id']}: this host's budget row could not be read ({exc}) -- "
                          f"the kit's default holds where it would have")
    return found


def readings(ctx) -> dict:
    """surface -> measure -> (tokens, bytes, where), plus each surface's inlined sections."""
    capabilities = ctx.enabled_capabilities()
    produced = projection.projections(ctx, capabilities)
    estimator = document(ctx)["estimator"]
    surfaces = {row["id"]: row for row in declared.rules(ctx, *SURFACES)}
    rows = []
    for item in serving._records(capabilities):
        if item["target"] in produced:
            rows += json.loads(produced[item["target"]]).get("served", [])
    out = {}
    # A surface that loads nothing into a context layer (a commit hook, a CI runner) spends nothing.
    for surface in sorted({r["surface"] for r in rows if r.get("layer")}):
        mine = [r for r in rows if r["surface"] == surface]
        unknown = sorted({r["layer"] for r in mine if r.get("layer") and r["layer"] not in LAYERS})
        if unknown:
            raise ContextError(f"surface {surface!r} renders into the layer(s) {unknown}, which this kit "
                               f"does not measure (it measures {sorted(LAYERS)})")
        pages = []
        for row in mine:
            for page in row.get("points", []):
                text = produced.get(page)
                if text is None and ctx.workspace.exists(page):
                    text = ctx.workspace.read_text(page)
                if text is not None:
                    pages.append((page, len(text.encode("utf-8")), row))
                else:  # pointed to and not there: no bytes to count, and that is said, not summed as zero
                    print(f"        NOT COUNTED  {page}: pointed to by the context map and not there")
        per_token = (surfaces.get(surface, {}).get("tokens") or estimator)["bytes_per_token"]
        measured = {}
        for measure, (_layer, count) in COUNTS.items():
            size, where = count(mine, produced, pages)
            measured[measure] = (math.ceil(size / per_token), size, where)
        inlined = [(row["path"], section["id"], math.ceil(section["bytes"] / per_token))
                   for row in mine for section in row.get("inlined", [])]
        out[surface] = {"measured": measured, "inlined": inlined}
    return out


def _held(ctx, params) -> list:
    surfaces = {row["id"]: row for row in declared.rules(ctx, *SURFACES)}
    return verdict(document(ctx), _ceilings(ctx), readings(ctx), surfaces)


def verdict(context: dict, host: dict, taken: dict, surfaces: dict) -> list:
    """The failures of these readings against the host's budget rows, the kit's defaults and each
    product's own limits -- printed as it goes, so a host sees what every surface spends."""
    defaults = context.get("default_ceilings", {})
    limit = context.get("inline_limit_tokens")
    failures = []
    if not taken:
        print("        NOTHING SERVED -- no surface is served on this host, so no context is spent")
    for surface, reading in taken.items():
        hard = {row["measures"]: row for row in surfaces.get(surface, {}).get("limits", [])}
        for measure, (tokens, size, where) in reading["measured"].items():
            if measure in host:
                bound, by = host[measure], "this host's budget row (held by the ratchet)"
            else:
                bound, by = defaults.get(measure), "the kit's default"
            print(f"        CONTEXT {surface}: {measure} = {tokens} token(s), {size} B ({where}); "
                  f"ceiling {bound} by {by}")
            if measure not in host and bound is not None and tokens > bound:
                failures.append(f"{surface}: {measure} is {tokens} token(s) against the kit's default of "
                                f"{bound} -- carry the rest on demand (a pointer), or budget your own "
                                f"number in the corpus map")
            if measure in hard and tokens > hard[measure]["ceiling"]:
                failures.append(f"{surface}: {measure} is {tokens} token(s), over the product's own limit of "
                                f"{hard[measure]['ceiling']} ({hard[measure]['says']})")
        for path, section, tokens in reading["inlined"]:
            if limit is not None and tokens > limit:
                print(f"        ADVICE  {path}: the section {section!r} is inlined at {tokens} token(s), over "
                      f"the inline limit of {limit} -- a pointer would carry it on demand")
    return failures


def _measure(name):
    def measured(ctx, params):
        # The measures' shared rule: a budget lives in a corpus map, and a host that maps none is
        # answered with nothing, never with a number nobody asked for.
        if corpus.read(ctx, params).nothing_read():
            return None
        taken = readings(ctx)
        return max((r["measured"][name][0] for r in taken.values()), default=None)
    return measured


def _calibrate(host):
    """A surface over the kit's default is flagged; the same surface at it is admitted."""
    def judged(tokens):
        taken = {"s": {"measured": {m: (tokens if m == "always_loaded_tokens" else 0, 0, "-") for m in COUNTS},
                       "inlined": []}}
        return verdict({"default_ceilings": {"always_loaded_tokens": 10}}, {}, taken, {})
    return judged(11), judged(10)


KINDS = {KIND: _held}
CALIBRATIONS = {KIND: _calibrate}
MEASURES = {name: _measure(name) for name in COUNTS}

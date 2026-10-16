"""The `served` projection shape -- the files a runtime PRODUCT reads, computed from what the host
already declared (ADR-013).

It is the Language Server Protocol's shape turned outward: ONE shape, many clients. It states what
the kit can hand any runtime -- a document assembled from sections the host already owns, and one
file per record of a composed view -- and each product is an ADAPTER that is pure DATA: a SURFACE
row naming the paths it reads and the template that gives each file the form it parses. No surface,
product, path or view is named in this module. A third runtime is a row in a surface registry and
costs no edit here -- which is the test this module is held to.

It runs at stage 1, after every shape that projects from the bindings alone: a served file is
assembled from this render's own projections. The record it writes beside the files, and every
rule that reads that record, belong to `serving`.
"""

from __future__ import annotations

import json

import collection
import declared
import derivation
import serving
import template
from shaping import Shape

def _quoted(value: str) -> str:
    """A string in the one form both sides provably read the same way: a JSON string literal is
    a valid YAML double-quoted scalar and a valid TOML basic string, whatever it carries. A value
    that crosses a boundary is carried in a form both sides read identically, or not at all."""
    return json.dumps(value, ensure_ascii=False)


def _served(ctx, spec: dict, view: dict) -> list:
    """(runtime row, surface) for every runtime this host SERVES: a composed runtime whose
    enabling field names a declared surface. A runtime naming an undeclared surface is served
    nothing -- the gate that owns that reference reports it, and nothing is guessed here."""
    surfaces = {row[collection.IDENTITY]: row for row in
                declared.rules(ctx, spec["surfaces"]["sources"], spec["surfaces"]["list"])}
    enabled = spec["enabled_by"]
    pairs = []
    for row in view.get(enabled["over"]) or []:
        surface = surfaces.get(row.get(enabled["field"]))
        if surface is not None:
            pairs.append((row, surface))
    return pairs


def _views(spec: dict) -> dict:
    return {v["id"]: v for v in spec["views"]}


def _plural_path(capabilities, over: str, record_id: str) -> "str | None":
    """Where this host already renders the projection FOR one record of `over` -- found by the
    declaration that iterates it, never by a path spelled here."""
    for capability in capabilities:
        for item in capability.installs_of_class("projection"):
            each = item.get("each")
            if each and each["over"] == over:
                return f"{item['target'].rstrip('/')}/{record_id}{each.get('suffix', '')}"
    return None


def _sections(ctx, view_spec: dict, produced: dict, record: "dict | None" = None) -> list:
    """A document view: each section is a file the host already owns -- read from this render's
    own projections when it is one of them, from the workspace otherwise. Absent is a declared
    state that renders in words, never a silent gap. A section of a SCOPED view names the field
    of its scope that holds the file, so one section grammar serves the root and every scope."""
    rows = []
    for section in view_spec.get("sections", []):
        source = record[section["from_field"]] if "from_field" in section else section["from"]
        if source in produced:
            text, present = produced[source], True
        elif ctx.workspace.exists(source):
            text, present = ctx.workspace.read_text(source), True
        else:
            text, present = "", False
        if present and section.get("points"):
            # A page a runtime reads WHEN a question arises is named, not inlined: the always-loaded
            # text stays the size of what binds on every turn (ADR-021 decision 5).
            # It ends its line as a file's text does, so the next section opens on its own paragraph.
            text = f"Read `{source}` for {section['points']}.\n"
        rows.append({**section, "from": source, "present": present, "text": text})
    return rows


def _members(view_spec: dict, view: dict, produced: dict, capabilities) -> list:
    """A collection view: one member per record of a composed view, carrying the body this host
    already renders for that record. A member whose body was not rendered is not served --
    a definition file with no instructions in it would read as a complete, empty role."""
    members = []
    for record in view.get(view_spec["over"]) or []:
        identity = record[collection.IDENTITY]
        path = _plural_path(capabilities, view_spec["over"], identity)
        if path is None or path not in produced:
            continue
        description = record.get(view_spec.get("describes", "")) or view_spec.get("undescribed", "")
        fields = {"id": identity, "description": description, "body": produced[path]}
        members.append({**fields, "quoted": {k: _quoted(v) for k, v in fields.items()}})
    return members


def _scopes(ctx, view_spec: dict) -> list:
    """(directory, scope row) for every scope a SCOPED view places a file in. A directory is
    measured, never assumed: it must be a plain host-relative path that exists, is not the host
    root (the root is the unscoped briefing), and lies in no kit plane -- a pinned or taken copy
    is not the host's to govern, and a file placed there would be rebuilt by nobody who reads it."""
    spec = view_spec["scopes"]
    found = []
    for row in declared.rules(ctx, spec["sources"], spec["list"]):
        rel = row[spec["at"]]
        parts = rel.split("/")
        why = None
        if not rel or rel.startswith("/") or ":" in rel or "\\" in rel or any(p in ("", ".", "..") for p in parts):
            why = "is not a plain path inside this host"
        elif serving.in_a_plane(ctx, rel):
            why = "lies inside a kit plane, which is not the host's to govern"
        elif not ctx.workspace.path(rel).is_dir():
            why = "is not a directory on this host"
        if why:
            raise serving.ScopeRefused(
                f"scope {row[collection.IDENTITY]!r} places laws at {rel!r}, which {why}. Nothing "
                f"has been written. Name an existing directory of the host's own tree, or remove "
                f"the scope -- the root of the host is served by the unscoped briefing.")
        found.append((rel, row))
    return found


def _targets(ctx, item: dict, view: dict, produced: dict, capabilities) -> list:
    """(path, template, frame) for every file served. Two claims on one path are refused,
    both named -- never ordered."""
    spec = item["serves"]
    views = _views(spec)
    found, owner = [], {}
    for row, surface in _served(ctx, spec, view):
        # `vendor` is where this host carries its pinned kit -- the manifest's own plane, so a
        # served setting that runs a vendored interpreter never spells that path a second time.
        base = {"kit_version": view["kit_version"], "runtime": row[collection.IDENTITY],
                "surface": surface[collection.IDENTITY],
                "vendor": ctx.manifest.plane("vendor")}
        for rendered in surface["renders"]:
            view_spec = views.get(rendered["view"])
            if view_spec is None:
                raise serving.ServeConflict(
                    f"surface {surface['id']!r} renders the view {rendered['view']!r}, which "
                    f"{item['target']!r} does not offer; it offers {sorted(views)}")
            if collection.kind_of(rendered) == "collection":
                root = rendered["target"].rstrip("/")
                for member in _members(view_spec, view, produced, capabilities):
                    found.append((f"{root}/{member['id']}{rendered.get('suffix', '')}",
                                  rendered["template"], {**base, **member}, rendered))
            elif "scopes" in view_spec:
                for rel, scope in _scopes(ctx, view_spec):
                    found.append((f"{rel}/{rendered['target']}", rendered["template"],
                                  {**base, "scope": rel, "scope_id": scope[collection.IDENTITY],
                                   "says": scope.get("says", ""),
                                   "sections": _sections(ctx, view_spec, produced, scope)}, rendered))
            else:
                found.append((rendered["target"], rendered["template"],
                              {**base, "sections": _sections(ctx, view_spec, produced)}, rendered))
    for path, _template, frame, _rendered in found:
        claimant = f"{frame['runtime']} through {frame['surface']}"
        if path in owner and owner[path] != claimant:
            raise serving.ServeConflict(
                f"{path!r} is served twice -- to {owner[path]} and to {claimant}. One path, one "
                f"writer: serve one of them, or declare a surface whose paths do not collide.")
        owner[path] = claimant
    return found


def project(ctx, item: dict, view: dict, produced: dict, capabilities) -> dict:
    """Every served file and the record of them, as bytes in memory. Pure: VENDOR + BINDING and
    this render's own plane projections in, text out, nothing read from the wall clock."""
    out, record = {}, []
    for path, source, frame, rendered in _targets(ctx, item, view, produced, capabilities):
        text = template.render(ctx.manifest.payload_text(source), frame)
        row = {"path": path, "runtime": frame["runtime"], "surface": frame["surface"]}
        if rendered.get("span"):
            seed = template.render(ctx.manifest.payload_text(rendered["seed"]), frame)
            text = derivation.spliced(_host_file(ctx, path, rendered, seed), rendered["span"], text)
            row.update({"span": rendered["span"],
                        "span_sha256": serving.digest(derivation.span(text, rendered["span"])),
                        "seed_sha256": serving.digest(derivation.withdrawn(seed, rendered["span"]))})
        out[path] = text
        # A spanned file is the HOST's: only the span is the kit's, and only the span is recorded.
        # A whole-file digest here would move every time the host edited its own text, and the
        # record -- a projection -- would then fail to reproduce over an edit nobody may refuse.
        record.append(row if rendered.get("span") else {**row, "sha256": serving.digest(text)})
    out[item["target"]] = json.dumps(
        {"schema_version": serving.RECORD_VERSION, "served": sorted(record, key=lambda r: r["path"])},
        indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return out


def _host_file(ctx, path: str, rendered: dict, seed: str) -> str:
    """The text a span is placed into: the host's own file where it marks out the span; the seed
    where there is no file, or where the file is still exactly what the kit last served WHOLE (a
    file served before spans existed, the kit's own bytes to replace -- `admit` tells the two
    apart by the record). Anything else is somebody else's file: the seed is returned, and
    `admit` refuses the write by name."""
    if ctx.workspace.exists(path):
        existing = ctx.workspace.read_text(path)
        if derivation.span(existing, rendered["span"]) is not None:
            return existing
    return seed


def foresee(ctx, item: dict, view: dict, capabilities) -> list:
    """The paths a plan can honestly name without rendering a byte. A member's body is only
    known once rendered, so a member is foreseen when its record has a rendering declaration."""
    produced = {}
    for capability in capabilities:
        for other in capability.installs_of_class("projection"):
            each = other.get("each")
            for record in (view.get(each["over"]) or []) if each else []:
                produced[_plural_path([capability], each["over"], record[collection.IDENTITY])] = ""
    return sorted({path for path, _s, _f, _r in _targets(ctx, item, view, produced, capabilities)}
                  | {item["target"]})




SHAPES = {serving.SHAPE: Shape(stage=1, project=project, foresee=foresee, reads_view=True,
                               departing=serving.departing_planned, unforeseeable=True)}

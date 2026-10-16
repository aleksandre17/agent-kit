"""The Runtime port -- how a host's declarations reach the tool that actually runs its agents.

A runtime product reads its instructions at FIXED paths the kit does not choose: a file at the
repository root, a directory of agent definitions beside it. Those paths lie outside the kit's
four planes, and a product will read nothing anywhere else. This port is the one place that
crosses that boundary (ADR-013).

It is the Language Server Protocol's shape turned outward: ONE port, many clients. The port
states what the kit can hand any runtime -- a document assembled from sections the host already
owns, and one file per record of a composed view -- and each product is an ADAPTER that is pure
DATA: a SURFACE row naming the paths it reads and the template that gives each file the form it
parses. No surface, product, path or view is named in this module. A third runtime is a row in a
surface registry and costs no edit here -- which is the test this module is held to.

Three rules make a file outside the planes a PROJECTION rather than a fifth class:

  * it is computed with every other projection, from VENDOR + BINDING only, so `check` holds it
    to the same byte-for-byte reproduction as the plane itself;
  * every path served is RECORDED, with the digest of what was written, in the projection plane
    -- the record is the class declaration of the path, and it is written in the same render;
  * a path is written only if it is absent, or holds exactly the bytes the kit would write now,
    or exactly the bytes the kit's own record says it last wrote there. Anything else is somebody
    else's file, and the whole render is REFUSED before a byte moves -- Home-Manager's refusal to
    clobber a file it does not manage, not chezmoi's overwrite-on-apply.

A render row that names a `span` serves less than a file (ADR-021 decision 5): the file is the
HOST's, written once from the row's `seed`, and the kit owns only the text between its two
markers. Every rule above then reads the SPAN: what is reproduced, what counts as the kit's bytes,
what is withdrawn when the surface stops being served. A host writes its own instructions around
the span, and nothing here reads them for writing.
"""

from __future__ import annotations

import hashlib
import json

import collection
import declared
import derivation
import template
from errors import KitError

#: The shape name a projection install declares to be served through this port. Registered in
#: the render interpreter's open shape registry; the declaration names it, never the reverse.
SHAPE = "served"

RECORD_VERSION = 1


class ServeCollision(KitError):
    """A path a runtime reads is held by bytes the kit did not write."""

    code = "KIT0039"


class ServeConflict(KitError):
    """One path a runtime reads is claimed by two served files."""

    code = "KIT0040"


class ScopeRefused(KitError):
    """A scope names a directory no served file may be placed in."""

    code = "KIT0046"


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_digest(ctx, rel: str) -> str:
    """Measured at the bytes, never through a decoding: a line ending is exactly the kind of
    translation a comparison of text would hide."""
    return hashlib.sha256(ctx.workspace.read_bytes(rel)).hexdigest()


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
        elif _in_a_plane(ctx, rel):
            why = "lies inside a kit plane, which is not the host's to govern"
        elif not ctx.workspace.path(rel).is_dir():
            why = "is not a directory on this host"
        if why:
            raise ScopeRefused(
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
                "vendor": next(p["root"] for p in ctx.manifest.planes if p["class"] == "vendor")}
        for rendered in surface["renders"]:
            view_spec = views.get(rendered["view"])
            if view_spec is None:
                raise ServeConflict(
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
            raise ServeConflict(
                f"{path!r} is served twice -- to {owner[path]} and to {claimant}. One path, one "
                f"writer: serve one of them, or declare a surface whose paths do not collide.")
        owner[path] = claimant
    return found


def project(ctx, item: dict, view: dict, produced: dict, capabilities) -> dict:
    """Every served file and the record of them, as bytes in memory. Pure: VENDOR + BINDING and
    this render's own plane projections in, text out, nothing read from the wall clock."""
    out, record = {}, []
    last = prior_rows(ctx, capabilities)
    for path, source, frame, rendered in _targets(ctx, item, view, produced, capabilities):
        text = template.render(ctx.manifest.payload_text(source), frame)
        row = {"path": path, "runtime": frame["runtime"], "surface": frame["surface"]}
        if rendered.get("span"):
            seed = template.render(ctx.manifest.payload_text(rendered["seed"]), frame)
            text = derivation.spliced(_host_file(ctx, path, rendered, seed), rendered["span"], text)
            row.update({"span": rendered["span"],
                        "span_sha256": _digest(derivation.span(text, rendered["span"])),
                        "seed_sha256": _digest(derivation.withdrawn(seed, rendered["span"]))})
        out[path] = text
        record.append({**row, "sha256": _digest(text)})
    out[item["target"]] = json.dumps(
        {"schema_version": RECORD_VERSION, "served": sorted(record, key=lambda r: r["path"])},
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


def _spans(produced: dict, capabilities) -> dict:
    """path -> (span id, span digest) for every spanned file this render serves, read from the
    record this same render produced."""
    found = {}
    for item in _records(capabilities):
        record = produced.get(item["target"])
        for row in (json.loads(record).get("served", []) if record else []):
            if row.get("span"):
                found[row["path"]] = (row["span"], row["span_sha256"])
    return found


def withdrawals(ctx, capabilities, produced: dict) -> dict:
    """path -> what is left of a spanned file whose surface is no longer served and whose span still
    holds the kit's last bytes: the host's own text, without the span. A file whose remaining text
    is still exactly the seed the kit wrote holds nobody's words, and is removed instead (None)."""
    out = {}
    for rel, row in prior_rows(ctx, capabilities).items():
        if rel in produced or not row.get("span") or not ctx.workspace.exists(rel):
            continue
        text = ctx.workspace.read_text(rel)
        held = derivation.span(text, row["span"])
        if held is not None and _digest(held) == row.get("span_sha256"):
            rest = derivation.withdrawn(text, row["span"])
            out[rel] = None if _digest(rest) == row.get("seed_sha256") or not rest.strip() else rest
    return out


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


def _records(capabilities) -> list:
    return [item for capability in capabilities for item in capability.installs
            if item["class"] == "projection" and item.get("shape") == SHAPE]


def prior_rows(ctx, capabilities) -> dict:
    """path -> the row the kit's own record holds for it, span and all."""
    rows = {}
    for item in _records(capabilities):
        if ctx.workspace.exists(item["target"]):
            for row in ctx.workspace.read_json(item["target"]).get("served", []):
                rows[row["path"]] = row
    return rows


def prior(ctx, capabilities) -> dict:
    """path -> digest the kit's own record says it last served. Read BEFORE the plane is rebuilt:
    the record is the only evidence of which bytes outside the planes are the kit's."""
    return {path: row["sha256"] for path, row in prior_rows(ctx, capabilities).items()}


def reach(ctx, capabilities) -> list:
    """(path, who) for every path OUTSIDE the planes that is the kit's surface through this port:
    every target a surface from these capabilities declares -- whether or not this host enables
    it, because a prior system at one of those paths is exactly what a later render would refuse
    to clobber -- and every path the kit's own record says it served. One home for the answer to
    *what outside the planes is ours*, read by every verb that must account for it."""
    found = {}
    for item in _records(capabilities):
        spec = item["serves"]["surfaces"]
        for name in declared.named(capabilities, spec["sources"]):
            for capability in capabilities:
                document = capability.documents.get(name)
                for surface in (document or {}).get(spec["list"], []):
                    for rendered in surface["renders"]:
                        found.setdefault(rendered["target"].rstrip("/"),
                                         f"served through the surface {surface['id']} "
                                         f"(declared by {capability.id})")
    for rel in prior(ctx, capabilities):
        found.setdefault(rel, "served, by the kit's own record")
    return sorted(found.items())


def served_rows(ctx, capabilities) -> dict:
    """path -> a row in the ESTATE's shape for every file the kit's record says it served: the
    class and mode of the install that recorded it and the capability that owns it. A served file
    is a path this host WAS given, and a verb that reads only the estate would say it was not."""
    rows = {}
    for capability in capabilities:
        for item in capability.installs_of_class("projection"):
            if item.get("shape") != SHAPE or not ctx.workspace.exists(item["target"]):
                continue
            for row in ctx.workspace.read_json(item["target"]).get("served", []):
                rows[row["path"]] = {"path": row["path"], "class": item["class"], "mode": item["mode"],
                                     "capability": capability.id, "served": True}
    return rows


def _in_a_plane(ctx, rel: str) -> bool:
    return any(rel == p["root"].rstrip("/") or rel.startswith(p["root"].rstrip("/") + "/")
               for p in ctx.manifest.planes)


def admit(ctx, capabilities, produced: dict) -> list:
    """The collision rule, applied before ANY write. Returns the served paths that are departing
    -- recorded last time, rendered by nothing now, and still holding the kit's own bytes -- so
    the caller can remove them. Refuses the whole render if any path outside the planes holds
    bytes the kit did not write, naming every one."""
    last = prior(ctx, capabilities)
    rows = prior_rows(ctx, capabilities)
    spans = _spans(produced, capabilities)
    withdrawing = withdrawals(ctx, capabilities, produced)
    held, departing = [], []
    # A projection a capability DECLARES as an install target outside the planes is the kit's own
    # path from the moment it was installed -- first contact with a prior file there is judged by
    # adoption, and a hand edit since by `check`, which reproduces it -- so only a SERVED path, whose place a
    # product chose, is judged here against the record.
    declared_targets = {i["target"] for c in capabilities for i in c.installs_of_class("projection")}
    for rel, text in sorted(produced.items()):
        if _in_a_plane(ctx, rel) or not ctx.workspace.exists(rel) or rel in declared_targets:
            continue
        if rel in spans:
            # The host owns the file; the kit owns the span. Where the host's file marks the span
            # out, only the span is judged: the kit's bytes are what it would serve now or what its
            # record says it last served there, and the host's text around it is never in question.
            on_disk = derivation.span(ctx.workspace.read_text(rel), spans[rel][0])
            if on_disk is not None:
                if _digest(on_disk) not in (spans[rel][1], rows.get(rel, {}).get("span_sha256")):
                    held.append(rel)
                continue
        found = _file_digest(ctx, rel)
        if found not in (_digest(text), last.get(rel)):
            held.append(rel)
    for rel, recorded in sorted(last.items()):
        if rel in produced or rel in withdrawing or not ctx.workspace.exists(rel):
            continue
        if _file_digest(ctx, rel) == recorded:
            departing.append(rel)
        else:
            held.append(rel)
    if held:
        raise ServeCollision(
            f"{held} would be written or removed, and each holds bytes this kit did not write -- "
            f"neither what it would render now nor what its record says it last served. A "
            f"projection is rebuilt, never merged, so writing would destroy them; nothing has "
            f"been written. Move them aside, carry a prior agent system over with `inherit` or "
            f"`takeover`, or stop serving the surface -- then render again.")
    return departing


def departing_planned(ctx, capabilities, targets) -> list:
    """For a plan: every path the record names outside the planes that nothing renders now."""
    return sorted(rel for rel in prior(ctx, capabilities)
                  if rel not in targets and not _in_a_plane(ctx, rel) and ctx.workspace.exists(rel))


def served_surfaces(ctx, capabilities) -> set:
    """Every surface the kit's own record says it served on this host -- the record, because a
    declared surface this host never rendered serves nothing yet."""
    return {row["surface"] for item in _records(capabilities) if ctx.workspace.exists(item["target"])
            for row in ctx.workspace.read_json(item["target"]).get("served", []) if "surface" in row}

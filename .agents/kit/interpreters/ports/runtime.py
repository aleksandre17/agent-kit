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
"""

from __future__ import annotations

import hashlib
import json

import collection
import declared
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


def _sections(ctx, view_spec: dict, produced: dict) -> list:
    """A document view: each section is a file the host already owns -- read from this render's
    own projections when it is one of them, from the workspace otherwise. Absent is a declared
    state that renders in words, never a silent gap."""
    rows = []
    for section in view_spec.get("sections", []):
        source = section["from"]
        if source in produced:
            text, present = produced[source], True
        elif ctx.workspace.exists(source):
            text, present = ctx.workspace.read_text(source), True
        else:
            text, present = "", False
        rows.append({**section, "present": present, "text": text})
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
                                  rendered["template"], {**base, **member}))
            else:
                found.append((rendered["target"], rendered["template"],
                              {**base, "sections": _sections(ctx, view_spec, produced)}))
    for path, _template, frame in found:
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
    for path, source, frame in _targets(ctx, item, view, produced, capabilities):
        text = template.render(ctx.manifest.payload_text(source), frame)
        out[path] = text
        record.append({"path": path, "runtime": frame["runtime"], "surface": frame["surface"],
                       "sha256": _digest(text)})
    out[item["target"]] = json.dumps(
        {"schema_version": RECORD_VERSION, "served": sorted(record, key=lambda r: r["path"])},
        indent=2, sort_keys=True, ensure_ascii=False) + "\n"
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
    return sorted({path for path, _s, _f in _targets(ctx, item, view, produced, capabilities)}
                  | {item["target"]})


def _records(capabilities) -> list:
    return [item for capability in capabilities
            for item in capability.installs_of_class("projection") if item.get("shape") == SHAPE]


def prior(ctx, capabilities) -> dict:
    """path -> digest the kit's own record says it last served. Read BEFORE the plane is rebuilt:
    the record is the only evidence of which bytes outside the planes are the kit's."""
    last = {}
    for item in _records(capabilities):
        if ctx.workspace.exists(item["target"]):
            for row in ctx.workspace.read_json(item["target"]).get("served", []):
                last[row["path"]] = row["sha256"]
    return last


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
    held, departing = [], []
    for rel, text in sorted(produced.items()):
        if _in_a_plane(ctx, rel) or not ctx.workspace.exists(rel):
            continue
        found = _file_digest(ctx, rel)
        if found not in (_digest(text), last.get(rel)):
            held.append(rel)
    for rel, recorded in sorted(last.items()):
        if rel in produced or not ctx.workspace.exists(rel):
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

"""Serving -- the RECORD of what the kit served outside its planes, read by every verb that must
account for it (ADR-013).

A runtime product reads its instructions at FIXED paths the kit does not choose. How those files are
COMPUTED is the `served` projection shape (`shapes/serve.py`); what this module holds is the other
half, which more than one layer needs and none may own: the record the shape writes into the
projection plane -- every path served, with the digest of what was written -- and the rules that
read it. A verb that writes (`render`), a verb that leaves (`eject`), the succession that hands a
host over, the activation that points a product at what is served and the probe that tells the
kit's own bytes from a host's all read it here, so there is one answer to *what outside the planes
is ours*.

Three rules make a file outside the planes a PROJECTION rather than a fifth class:

  * it is computed with every other projection, from VENDOR + BINDING only, so `check` holds it
    to the same byte-for-byte reproduction as the plane itself;
  * every path served is RECORDED, with the digest of what was written, in the projection plane
    -- the record is the class declaration of the path, and it is written in the same render;
  * a path is written only if it is absent, or holds exactly the bytes the kit would write now,
    or exactly the bytes the kit's own record says it last wrote there. Anything else is somebody
    else's file, and the whole render is REFUSED before a byte moves -- Home-Manager's refusal to
    clobber a file it does not manage, not chezmoi's overwrite-on-apply (`admit`).

A render row that names a `span` serves less than a file (ADR-021 decision 5): the file is the
HOST's, and the kit owns only the text between its two markers -- so every rule above then reads
the SPAN.
"""

from __future__ import annotations

import hashlib
import json

import declared
import derivation
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


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_digest(ctx, rel: str) -> str:
    """Measured at the bytes, never through a decoding: a line ending is exactly the kind of
    translation a comparison of text would hide."""
    return hashlib.sha256(ctx.workspace.read_bytes(rel)).hexdigest()


def _spans(produced: dict, capabilities) -> dict:
    """path -> (span id, span digest) for every spanned file this render serves, read from the
    record this same render produced."""
    found = {}
    for item in _records(capabilities):
        record = produced.get(item["target"])
        for row in (json.loads(record).get("served", []) if record else []):
            if row.get("span"):
                found[row["path"]] = (row["span"], row["span_sha256"], row.get("comment"))
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
        held = derivation.span(text, row["span"], row.get("comment"))
        if held is not None and digest(held) == row.get("span_sha256"):
            rest = derivation.withdrawn(text, row["span"], row.get("comment"))
            out[rel] = None if digest(rest) == row.get("seed_sha256") or not rest.strip() else rest
    return out


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
    return {path: row["sha256"] for path, row in prior_rows(ctx, capabilities).items() if "sha256" in row}


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


def in_a_plane(ctx, rel: str) -> bool:
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
        if in_a_plane(ctx, rel) or not ctx.workspace.exists(rel) or rel in declared_targets:
            continue
        if rel in spans:
            # The host owns the file; the kit owns the span. Where the host's file marks the span
            # out, only the span is judged: the kit's bytes are what it would serve now or what its
            # record says it last served there, and the host's text around it is never in question.
            on_disk = derivation.span(ctx.workspace.read_text(rel), spans[rel][0], spans[rel][2])
            if on_disk is not None:
                if digest(on_disk) not in (spans[rel][1], rows.get(rel, {}).get("span_sha256")):
                    held.append(rel)
                continue
        found = _file_digest(ctx, rel)
        if found not in (digest(text), last.get(rel)):
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
    return sorted(rel for rel in prior_rows(ctx, capabilities)
                  if rel not in targets and not in_a_plane(ctx, rel) and ctx.workspace.exists(rel))


def served_surfaces(ctx, capabilities) -> set:
    """Every surface the kit's own record says it served on this host -- the record, because a
    declared surface this host never rendered serves nothing yet."""
    return {row["surface"] for item in _records(capabilities) if ctx.workspace.exists(item["target"])
            for row in ctx.workspace.read_json(item["target"]).get("served", []) if "surface" in row}

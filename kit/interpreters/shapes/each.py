"""The `collection` projection shape -- one template, one file PER RECORD of a view.

A target ending in `/` names a collection. Its home is projected as one declared marker (`space`)
whether or not the host has filled it, because a repository carries files and a directory holding
no record simply is not there after the next checkout.
"""

from __future__ import annotations

import space
import template
from shaping import RenderError, Shape

def _project_each(ctx, item, view) -> dict:
    """One template, one file PER RECORD -- a surface FOR each member of a set.

    The two are told apart by the shape of the declared target, which is the same rule
    `collection` already uses to decide whether a readable is one document or many: a target
    ending in `/` is a plural. Declared once, read here, and never a second convention.

    The record is pushed as the innermost frame, so a template reaches the record's own fields
    directly and still sees everything the whole view carries -- which is what lets a line
    declared ONCE, for every record, be RENDERED INTO each of them rather than referenced from
    them. A reference can be left unfollowed. A rendered line cannot.
    """
    body = ctx.manifest.payload_text(item["source"])
    produced: dict[str, str] = {}
    for target, record in targets(ctx, item, view):
        shadowed = sorted(set(record) & set(view))
        if shadowed:
            raise RenderError(
                f"a record of {item['each']['over']!r} carries {shadowed}, which the view "
                f"already means something else by. A name that resolves to two things is not a "
                f"name, and the "
                f"record would silently win -- refused rather than ordered."
            )
        produced[target] = template.render(body, {**view, **record})
    # A collection HAS a home whether or not the host has filled it, and that home must survive a
    # clone -- a repository carries files, so a directory holding no record simply is not there
    # after the next checkout. The home is therefore projected as one declared marker (`space`),
    # UNCONDITIONALLY: written for a full collection exactly as for an empty one. Making it
    # conditional was tried and the two-host boundary test refused it within the hour -- a file
    # that appears in one host and not another is a VARIATION, and its cause was readable only by
    # knowing what each host happened to have authored. It is a projection like any other, planned
    # before it is written, because a path the plan did not promise is a path nothing renders.
    produced[space.marker_in(ctx.manifest, item["target"])] = space.TEXT
    return produced


def targets(ctx, item, view) -> list:
    """(path, record) for every file a plural projection would write. Computed WITHOUT rendering
    a byte, so a plan can state the write set without producing the content of it."""
    each = item.get("each")
    if not each:
        raise RenderError(
            f"{item['target']!r} is declared as a plural projection -- its target names a "
            f"collection -- but it says nothing about what it is one of. A projection per record "
            f"needs `each`, naming the view it iterates and the field that names each file."
        )
    rows = view.get(each["over"])
    if rows is None:
        raise RenderError(
            f"{item['target']!r} projects one file for each {each['over']!r}, which this view "
            f"does not carry; it carries {sorted(view)}"
        )
    root = item["target"].rstrip("/")
    found = []
    for record in rows:
        name = record.get(each["named"])
        if not isinstance(name, str) or not name or "/" in name or name in (".", ".."):
            raise RenderError(
                f"{item['target']!r} names each file by {each['named']!r}, and one record "
                f"answers {name!r} -- which is not a single path segment. A name that is not a "
                f"referent is how a write lands somewhere nobody chose."
            )
        found.append((f"{root}/{name}{each.get('suffix', '')}", record))
    return found




def _foresee(ctx, item, view, capabilities) -> list:
    return sorted([space.marker_in(ctx.manifest, item["target"])]
                  + [target for target, _record in targets(ctx, item, view)])


SHAPES = {"collection": Shape(stage=0, project=lambda ctx, item, view, produced, capabilities:
                              _project_each(ctx, item, view), foresee=_foresee)}

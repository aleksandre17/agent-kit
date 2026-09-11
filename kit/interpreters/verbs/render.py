"""render -- recompute every projection from scratch.

A projection has no history. It is deleted and rebuilt, never merged and never diffed against its
old self, so there is nothing for it to drift FROM. Its inputs are VENDOR + BINDING only; the wall
clock is deliberately not one of them, which is what makes the output byte-reproducible.

It MUTATES, so it can be asked for a plan; and it runs only on an APPROVED host, because a
projection of an answer nobody accepted would be a surface stating a decision as settled.
"""

from __future__ import annotations

import collection
import composition as composition_module
import hostlock
import lifecycle as lifecycle_module
import plan as plan_module
import template
from errors import KitError

SUMMARY = "recompute every projection from VENDOR + BINDING"
MUTATES = True
REQUIRES_APPROVED_HOST = True


class RenderError(KitError):
    """A projection cannot be rendered without a name resolving to two things, or a plural
    projection does not declare soundly what it iterates and how each file is named."""

    code = "KIT0028"


def view_model(ctx, capabilities=None) -> dict:
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    project = ctx.host_answers()
    profile = ctx.binding(ctx.install_of_mode("reading")["target"], "profile")
    described = []
    for capability in capabilities:
        described.append({
            "id": capability.id,
            "version": capability.version,
            "summary": capability.summary,
            "installs": [dict(item) for item in capability.installs],
            "gates": [dict(gate) for gate in capability.gates],
        })
    view = {
        "kit_version": ctx.manifest.version,
        "project": project,
        "capabilities": described,
        "facts": [{"key": k, "value": v} for k, v in sorted(profile["facts"].items())],
        "documents": {},
    }
    # What the capabilities DECLARE and what the host AUTHORED both reach the view model by the
    # same generic route: a shipped document by its id, a readable install by its `reads_as` name,
    # and a governed collection as the columns its lifecycle declares. No capability, path or
    # state is named here -- a new board is a declaration, not an edit to this function.
    readings = collection.read_all(ctx, capabilities)
    view["reads"] = {name: reading.value for name, reading in readings.items()}
    for capability in capabilities:
        for identity, document in capability.documents.items():
            _claim(view["documents"], identity, document, capability.id)
        governed = lifecycle_module.governed_of(capability, readings)
        if governed:
            _claim(view, governed.spec["board"], lifecycle_module.columns(governed), capability.id)
        # A COMPOSITION reaches the view by the same generic route as everything else: the
        # declaration names the readable holding the instances and the sources holding the bases,
        # and this line neither knows nor asks what is being composed. A second kind of composed
        # thing is another `composes` block, and this function is not touched.
        composed = composition_module.composed_of(ctx, capability, readings)
        if composed:
            _claim(view, composed.spec["id"], composed.rows, capability.id)
            _claim(view, composed.spec["census"], composed.census, capability.id)
    return view


def _claim(where: dict, name: str, value, owner: str) -> None:
    """One name, one meaning. Two capabilities claiming one name in the view model is the same
    defect as two capabilities installing to one path, and gets the same answer: refused, both
    named -- never last-writer-wins, which would leave the loser's declaration reading as true."""
    if name in where:
        raise RenderError(
            f"capability {owner!r} claims the view-model name {name!r}, which is already taken; "
            f"a name that resolves to two things is not a name"
        )
    where[name] = value


def _plane(ctx) -> str:
    return next(p["root"] for p in ctx.manifest.planes if p["class"] == "projection")


def _project_one(ctx, item, view) -> dict:
    """One template, one file. The ordinary projection: a surface ABOUT a set."""
    return {item["target"]: template.render(ctx.manifest.payload_text(item["source"]), view)}


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
    for target, record in _each_targets(ctx, item, view):
        shadowed = sorted(set(record) & set(view))
        if shadowed:
            raise RenderError(
                f"a record of {each['over']!r} carries {shadowed}, which the view already means "
                f"something else by. A name that resolves to two things is not a name, and the "
                f"record would silently win -- refused rather than ordered."
            )
        produced[target] = template.render(body, {**view, **record})
    return produced


def _each_targets(ctx, item, view) -> list:
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


#: How a projection is SHAPED, keyed by the shape its own declared target states. An open
#: registry: a third shape is a row here and a function beside these two, and nothing that
#: dispatches to it is ever edited.
PROJECTION_SHAPES = {"document": _project_one, "collection": _project_each}


def projections(ctx, capabilities=None) -> dict:
    """Every projected path and its bytes, computed in memory. `check` uses this to prove the
    plane on disk is exactly what the declaration implies."""
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    view = view_model(ctx, capabilities)
    produced: dict[str, str] = {}
    for capability in capabilities:
        for item in capability.installs_of_class("projection"):
            produced.update(PROJECTION_SHAPES[collection.kind_of(item)](ctx, item, view))
    return produced


def _foreseen(ctx, item, capabilities) -> list:
    """Which paths this projection would write, as far as a PLAN can honestly know.

    A singular projection's target is stated in the declaration, so a plan can name it before a
    single binding exists. A PLURAL one's targets are a function of a binding, and that is a real
    difference rather than an inconvenience: how many files there will be is a question only the
    host's own content answers.

    Where that content is readable the plan expands to the exact set. Where it is not -- an
    install being planned before the bindings it would read have been created -- the answer is
    NOTHING, and nothing is what is planned. The temptation is to name the collection instead, so
    the operator sees that something is there; that was tried and it is a LIE: the apply writes no
    such path, and a plan whose promise the apply does not keep is worse than no plan, because it
    is believed exactly once. It is also, in the only case that reaches here, the wrong number --
    a host with no records genuinely gets no files, so the empty plan is not a gap in the reading
    but the reading itself.
    """
    if collection.kind_of(item) == "document":
        return [item["target"]]
    try:
        return sorted(target for target, _record
                      in _each_targets(ctx, item, view_model(ctx, capabilities)))
    except KitError:
        return []


def plan_entries(ctx, capabilities=None) -> list:
    """The write set, as DATA and without rendering a single byte of content. A plan must be
    computable before the bindings it would project from exist -- otherwise the one moment an
    operator most needs to see what would happen is the one moment nothing can be shown."""
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    targets, writes = [], []
    for capability in capabilities:
        for item in capability.installs_of_class("projection"):
            for target in _foreseen(ctx, item, capabilities):
                targets.append(target)
                writes.append(plan_module.Write(
                    "replace" if ctx.workspace.exists(target) else "create",
                    item["class"], item["mode"], capability.id, target, item))
    # The plane is rebuilt wholesale, so anything in it that nothing renders is REMOVED. A plan
    # that lists only what it writes is not a plan: deletion is the effect an operator most
    # needs to have seen coming.
    orphans = [
        plan_module.Write("remove", "projection", "projection", "-", rel)
        for rel in ctx.workspace.files_under(_plane(ctx)) if rel not in targets
    ]
    return orphans + writes


def run(ctx, args, capabilities=None) -> int:
    hostlock.arrive(ctx, args)
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    writes = plan_entries(ctx, capabilities)
    if getattr(args, "plan", False):
        print(plan_module.report("render", writes))
        return 0

    def write() -> int:
        ctx.workspace.unscoped().remove_tree(_plane(ctx))
        produced = projections(ctx, capabilities)
        scopes = {c.id: ctx.workspace.scoped(c.targets()) for c in capabilities}
        for entry in writes:
            if entry.disposition != "remove":
                scopes[entry.capability].write_text(entry.target, produced[entry.target])
            print(f"  {entry.accomplished:<9}  {entry.target}")
        return 0

    return hostlock.held(ctx, args, write)

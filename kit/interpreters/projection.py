"""projection -- what the declaration implies, computed in memory and without writing a byte.

The computation a projection IS: the view model every template reads, each projection shape's
bytes, and the write set a plan names. It lives in the shared core because more than one layer
needs it -- the `render` verb writes it, and a gate proves the plane on disk equals it. A judge
that had to call the verb it judges would depend on the thing it judges; both depend on this
instead.
"""

from __future__ import annotations

import collection
import composition as composition_module
import consumption as consumption_module
import criteria as criteria_module
import lifecycle as lifecycle_module
import plan as plan_module
import resolution
import space
import shaping
from errors import KitError
from shaping import RenderError  # noqa: F401 -- raised here, declared with the shapes

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
            _claim(view, governed.spec["board"],
                   lifecycle_module.columns(governed, _counted(ctx, governed)), capability.id)
        # A COMPOSITION reaches the view by the same generic route as everything else: the
        # declaration names the readable holding the instances and the sources holding the bases,
        # and this line neither knows nor asks what is being composed. A second kind of composed
        # thing is another `composes` block, and this function is not touched.
        composed = composition_module.composed_of(ctx, capability, readings)
        if composed:
            _claim(view, composed.spec["id"], composed.rows, capability.id)
            _claim(view, composed.spec["census"], composed.census, capability.id)
        # A CONSUMED fact reaches the view by the same generic route: the declaration names the
        # documents holding the rows and the field of a row that names the fact, and this line
        # neither knows nor asks WHICH fact or what it will be used to say. The reading joined
        # against is the recorded one this function already read -- never a second probe, which
        # would be a second reading of one reality taken at a moment nobody stated.
        consumed = consumption_module.consumed_of(ctx, capability, profile)
        if consumed:
            _claim(view, consumed.spec["id"], consumed.rows, capability.id)
        # A READING of the host's own tree reaches the view by the same generic route: the
        # declaration names the id it will be known by, the KIND of resolver that can produce it,
        # and the params that configure it -- and this line neither knows nor asks what is being
        # read. A second kind of reading is another `resolves` row, and this function is not
        # touched. What arrives is data; nothing here judges it, and the gates that do stand on
        # the same resolution rather than on this one (Cardinal III).
        for resolved in resolution.resolved_of(ctx, capability):
            _claim(view, resolved.spec[resolution.ID], resolved.value, capability.id)
    return view


def _counted(ctx, governed):
    """What a board may show about one record beyond the record's own fields, as a FUNCTION the
    lifecycle is handed.

    The field the numbers are counted over is named by the declaration that governs the
    collection, never spelled here: a collection that declares none is counted about by nothing,
    which is a complete state and not a missing feature. The numbers are computed at the moment
    the projection is, from the records themselves, so the surface cannot carry a count that was
    true when somebody last typed it.
    """
    field = governed.spec.get("criteria")
    if field is None:
        return None
    return lambda record: criteria_module.tally(ctx, record, field)


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
    return ctx.manifest.plane("projection")


def _shape_of(item) -> str:
    return shaping.name_of(item)


def _staged(capabilities) -> list:
    items = [item for capability in capabilities for item in capability.installs_of_class("projection")]
    return sorted(items, key=lambda item: shaping.shape_of(item).stage)


def projections(ctx, capabilities=None) -> dict:
    """Every projected path and its bytes, computed in memory. `check` uses this to prove the
    plane on disk -- and every path a runtime reads that this host serves -- is exactly what the
    declaration implies."""
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    view = view_model(ctx, capabilities)
    produced: dict[str, str] = {}
    for item in _staged(capabilities):
        produced.update(shaping.shape_of(item).project(ctx, item, view, produced, capabilities))
    return produced


def _foreseen(ctx, item, capabilities) -> list:
    return _foresight(ctx, item, capabilities)[0]


def _foresight(ctx, item, capabilities) -> tuple:
    """(paths, whether they could be READ) -- `_foreseen` with the second half kept, so a caller can
    tell a plan that read nothing from a plan that read an empty set."""
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
    shape = shaping.shape_of(item)
    if not shape.reads_view:
        return shape.foresee(ctx, item, None, capabilities), True
    try:
        return shape.foresee(ctx, item, view_model(ctx, capabilities), capabilities), True
    except KitError:
        # A shape whose own target names ONE file writes that file whatever the bindings say --
        # a served projection always writes its record, and the record of nothing is still
        # written -- so the plan names it; a target naming a collection has nothing to promise.
        # A target naming a COLLECTION promises the one path it writes in exactly the case that
        # reaches here -- a host whose records cannot be read has none, and a collection with no
        # records is projected as its declared emptiness (`space`). The promise the apply keeps,
        # rather than the silence that let the apply write a path the plan never showed.
        if item["target"].endswith("/"):
            return [space.marker_in(ctx.manifest, item["target"])], False
        return [item["target"]], False


def plan_entries(ctx, capabilities=None, moving=()) -> list:
    """The write set, as DATA and without rendering a single byte of content. A plan must be
    computable before the bindings it would project from exist -- otherwise the one moment an
    operator most needs to see what would happen is the one moment nothing can be shown."""
    capabilities = ctx.enabled_capabilities() if capabilities is None else capabilities
    targets, writes, unread = [], [], []
    for capability in capabilities:
        for item in capability.installs_of_class("projection"):
            found, read = _foresight(ctx, item, capabilities)
            if not read:
                unread.append(item)
            for target in found:
                targets.append(target)
                writes.append(plan_module.Write(
                    "replace" if ctx.workspace.exists(target) else "create",
                    item["class"], item["mode"], capability.id, target, item))
    moving = tuple(moving)

    def fate(rel: str) -> str:
        # A path an owed relocation moves is shown by that relocation, never as a deletion; one a
        # projection whose foresight could not be read may still write is UNFORESEEN.
        if any(rel == m or (m.endswith("/") and rel.startswith(m)) for m in moving):
            return None
        if any(shaping.shape_of(i).unforeseeable or rel.startswith(i["target"]) for i in unread):
            return "unforeseen"
        return "remove"
    # The plane is rebuilt wholesale, so anything in it that nothing renders is REMOVED. A plan
    # that lists only what it writes is not a plan: deletion is the effect an operator most
    # needs to have seen coming.
    orphans = [
        plan_module.Write(fate(rel), "projection", "projection", "-", rel)
        for rel in ctx.workspace.files_under(_plane(ctx)) if rel not in targets and fate(rel)
    ]
    # A path a runtime reads lies outside the plane, so the wholesale rebuild never reaches it:
    # one the kit served last time and serves no longer is named here, from the kit's own
    # record, because deletion is still the effect an operator most needs to see coming.
    orphans += [
        plan_module.Write(fate(rel), "projection", "projection", "-", rel)
        for shape in shaping.registry().values() if shape.departing
        for rel in shape.departing(ctx, capabilities, targets) if fate(rel)
    ]
    return orphans + writes

"""Where weighing reads from -- the catalogue, the host's areas and its cards, found by CONTRACT (ADR-025).

`weighing` is pure; this module is its one door to a host. Both declarations are found by the schema
they keep, never by a capability's name or a document's: a catalogue nobody ships is a host that
does not weigh, which is a state and not a failure -- and two catalogues are two answers to one
question, which is refused.
"""

from __future__ import annotations

import json

import declared
import lineage
from errors import KitError

CATALOGUE, AREAS = {declared.CONTRACT: "work-classes"}, {declared.CONTRACT: "delivery-areas"}


class WorkClassError(KitError):
    """A host whose work classes cannot be read honestly: two catalogues, or a change git could not list."""

    code = "KIT0087"


def _one(ctx, contract: dict):
    names = declared.named(ctx.enabled_capabilities(), contract)
    if not names:
        return None
    if len(names) > 1:
        raise WorkClassError(f"{len(names)} sources keep the contract {contract[declared.CONTRACT]!r} "
                             f"({', '.join(names)}): one question, one answer")
    return declared.sources(ctx, names)[names[0]]


def declarations(ctx):
    """(catalogue, areas), or None on a host that does not weigh. Areas absent -- a host installed
    before the seed existed -- read as no area at all: every path at the cheapest undo cost."""
    catalogue = _one(ctx, CATALOGUE)
    if catalogue is None:
        return None
    try:
        areas = _one(ctx, AREAS)
    except declared.DeclarationError:
        areas = None
    if areas is None:
        areas = {"default_undo": catalogue["undo"][0]["id"], "max_areas": {}, "areas": []}
    return catalogue, areas


def cards(ctx) -> dict:
    """Every card this host holds, by id -- the governed collection, read through its one door."""
    return lineage.by_identity(lineage.among(ctx) or [])



def paths(found: tuple, what: str) -> list:
    """The paths a port answered with, or the refusal of a question git could not answer."""
    listed, why = found
    if listed is None:
        raise WorkClassError(f"git could not say {what} -- {why}")
    return listed


def _install(ctx, contract: dict):
    return next((item for capability in ctx.enabled_capabilities() for item in capability.installs
                 if item.get(declared.CONTRACT) == contract[declared.CONTRACT] and item.get("mode") == "seed"), None)


def areas_target(ctx):
    """The host path the areas are declared at, or None -- the install that seeds them says where."""
    item = _install(ctx, AREAS)
    return None if item is None else item["target"]


def accepted_areas(ctx, fallback: dict) -> dict:
    """The areas as the last commit holds them: a change is weighed by the scale that stood before it,
    never by the scale it rewrites. Before the first commit, or where it is new, the working one."""
    target = areas_target(ctx)
    if target is None:
        return fallback
    text, _why = ctx.workspace.accepted_text(target)
    if text is None:
        return fallback
    try:
        return json.loads(text)
    except ValueError:
        return fallback


def governed_field(ctx, name: str):
    """The card field the governing capability declares under `name` (`criteria`, `lesson`), or None --
    so no interpreter has to know the word."""
    for capability in ctx.enabled_capabilities():
        spec = getattr(capability, "governs", None)
        if spec:
            return spec.get(name)
    return None


def card_space(ctx):
    """Where the governed cards live -- the install that reads them, found by the collection's name."""
    for capability in ctx.enabled_capabilities():
        spec = getattr(capability, "governs", None)
        if spec:
            return next((i["target"] for i in capability.installs if i.get("reads_as") == spec["collection"]), None)
    return None


def _parsed_any(text):
    try:
        found = json.loads(text) if text else None
    except ValueError:
        return None
    return found if isinstance(found, dict) else None


def _parsed(text):
    try:
        found = json.loads(text) if text else None
    except ValueError:
        return None
    return found if isinstance(found, dict) and found.get("id") else None


def reshaped_cards(ctx, paths, staged_text=None) -> tuple:
    """(before, after): every card the change touches, BY PATH -- as the last commit holds it and as the
    change records it (`staged_text`: the index), None where the change removes it. Matched by path, so
    a card cannot be lightened by changing its id or replaced by a lighter one."""
    space = card_space(ctx)
    before, after = {}, {}
    if space is None:
        return before, after
    for rel in paths:
        if not (rel.startswith(space) and rel.endswith(".json")):
            continue
        was = _parsed(ctx.workspace.accepted_text(rel)[0])
        if was is None:
            continue
        before[rel] = was
        now = staged_text(rel) if staged_text else (ctx.workspace.read_text(rel) if ctx.workspace.exists(rel) else None)
        after[rel] = _parsed(now[0] if isinstance(now, tuple) else now)
    return before, after


def staged_cards(ctx, staged_text) -> dict:
    """Every card as the index holds it, by id -- the cards a commit is judged against are the cards it
    records, never the working tree's."""
    space = card_space(ctx)
    held = {}
    for rel, _card in _records(ctx):
        staged = _parsed(staged_text(rel)[0]) if space else None
        if staged is not None:
            held[staged["id"]] = staged
    return held


def _records(ctx):
    capabilities = ctx.enabled_capabilities()
    for capability in capabilities:
        spec = getattr(capability, "governs", None)
        if spec:
            import collection
            import lifecycle as lifecycle_module
            governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
            return governed.members.records
    return []


def lifecycle_flags(ctx) -> tuple:
    """(door states, closed states): the states only a door opens, and the states marked closed."""
    capabilities = ctx.enabled_capabilities()
    if not any(getattr(c, "governs", None) for c in capabilities):
        return frozenset(), frozenset()
    import collection
    import lifecycle as lifecycle_module
    governed = lifecycle_module.the_governed(capabilities, collection.read_all(ctx, capabilities))
    doors = frozenset(t["to"] for t in governed.doc.get("transitions", []) if t.get("door"))
    closed = frozenset(s["id"] for s in governed.states if s.get("closed"))
    return doors, closed


def places_holding(capabilities, kind: str) -> list:
    """The places a capability's layout declares hold records of `kind` (`holds`), as path prefixes --
    found by what a place holds, never by its name."""
    out = []
    for capability in capabilities:
        for doc in capability.documents.values():
            for row in (doc.get("entries") if isinstance(doc, dict) else None) or []:
                if isinstance(row, dict) and row.get("holds") == kind and row.get("path"):
                    out.append(str(row["path"]))
    return out


def decided(ctx):
    """A reader of whether a card's reference is the KIND of record its row requires: a document IN A
    PLACE THE HOST'S LAYOUT SAYS HOLDS THAT KIND, whose front matter declares it (`kind: decision`). A
    decision some other repository made -- a vendored kit's own ADR -- is that repository's, not this
    host's (ADR-025 amendment 3). Any non-empty pointer -- the card a finding was captured from -- is not
    a decision. Where no place declares the kind, the front matter alone is read, and that is said."""
    places = {}

    def held_in(kind: str) -> list:
        if kind not in places:
            places[kind] = places_holding(ctx.enabled_capabilities(), kind)
        return places[kind]

    def read(card, holder):
        reference = card.get(holder["field"]) or {}
        ref = reference.get("ref") if isinstance(reference, dict) else None
        if not ref or not ctx.workspace.exists(ref):
            return False
        where = held_in(holder["kind_of_record"])
        if where and not any(ref == p.rstrip("/") or ref.startswith(p if p.endswith("/") else p + "/") for p in where):
            return False
        lines = ctx.workspace.read_text(ref).splitlines()
        if not lines or lines[0].strip() != "---":
            return False
        end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
        # Only the front matter -- between its two fences -- says what a document is: a body line that
        # reads `kind: decision` is prose about one.
        return end is not None and any(line.strip() == f"kind: {holder['kind_of_record']}" for line in lines[1:end])
    return read

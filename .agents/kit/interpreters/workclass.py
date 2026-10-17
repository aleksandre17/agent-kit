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


def reshaped_cards(ctx, paths) -> tuple:
    """(before, after): every card the change touches, as the last commit holds it and as the change
    leaves it -- the two readings a demotion is judged between."""
    space = card_space(ctx)
    before, after = {}, {}
    if space is None:
        return before, after
    held = cards(ctx)
    for rel in paths:
        if not (rel.startswith(space) and rel.endswith(".json")):
            continue
        text, _why = ctx.workspace.accepted_text(rel)
        try:
            was = json.loads(text) if text else None
        except ValueError:
            was = None
        if isinstance(was, dict) and was.get("id"):
            before[was["id"]] = was
            if was["id"] in held:
                after[was["id"]] = held[was["id"]]
    return before, after


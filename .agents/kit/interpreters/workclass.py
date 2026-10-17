"""Where weighing reads from -- the catalogue, the host's areas and its cards, found by CONTRACT (ADR-025).

`weighing` is pure; this module is its one door to a host. Both declarations are found by the schema
they keep, never by a capability's name or a document's: a catalogue nobody ships is a host that
does not weigh, which is a state and not a failure -- and two catalogues are two answers to one
question, which is refused.
"""

from __future__ import annotations

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

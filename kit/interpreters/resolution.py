"""resolution -- a READING reaches the view model by DECLARATION, resolved by whoever owns it.

Three blocks already carry something into a projection's view: `governs` a board, `composes` a set
of instances, `consumes` a measured fact. Each is generic, each names no subject, and none of them
can carry a READING of the host's own tree -- a resolution some interpreter performs, configured by
declared params, whose shape only that interpreter knows.

This is the fourth and it is the same shape as the other three. A capability declares WHAT it wants
in its view, by the id it will be known by and the KIND of resolver that can produce it; the
resolver is found in an open registry the resolvers themselves fill; and the params travel from the
declaration to the resolver untouched. No place, no plane, no class and no product is spelled here
(Cardinals II and IV): the day a second kind of reading is projected, this file is not edited.

Why a projection may consume a reading at all: the alternative is a page maintained by hand beside
the machinery that already knows the answer, which is two homes for one truth and the exact defect
ADR-019 decision 4 exists to remove. And why the resolver -- never this module -- owns the shaping:
a reading re-shaped by its consumer is a second traversal of the same reality, written by someone
who cannot see the first, and the two stay in agreement precisely until one of them is fixed
(Cardinal III).

It resolves and it never judges. What comes back is data: rows, counts and the reading's own
sentences. A refusal belongs to a gate, which stands on the same reading and is not this.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

import kinds
from errors import KitError


class ResolutionError(KitError):
    """A capability declared a view resolved by a kind no resolver answers for."""

    code = "KIT0054"


#: Where a resolver may be declared: each module in `resolvers/` publishes `RESOLVES`, the kinds it
#: answers for. A new kind of resolved reading is a module; nothing that dispatches over it is
#: touched, and no kind is spelled in this file.
RESOLVERS = Path(__file__).resolve().parent / "resolvers"


@functools.lru_cache(maxsize=None)
def registry() -> dict:
    return kinds.registry(RESOLVERS, "RESOLVES", "resolved view", ResolutionError)

#: The block's own field names. The `capability` schema is their home; these are the three this
#: module reads: what the view will call it, who can produce it, and what it is configured with.
ID, KIND, PARAMS = "id", "kind", "params"

#: The block itself, as the schema names it.
BLOCK = "resolves"


@dataclass(frozen=True)
class Resolved:
    """One declared view and the value its resolver produced for this host."""

    spec: dict
    value: object


def resolved_of(ctx, capability) -> list:
    """Every reading this capability declares for its view, resolved -- an empty list where it
    declares none, which is the ordinary answer for every capability that projects no reading."""
    found = []
    for spec in capability.raw.get(BLOCK, []):
        resolve = registry().get(spec[KIND])
        if resolve is None:
            raise ResolutionError(
                f"capability {capability.id!r} declares the view {spec[ID]!r} resolved by "
                f"{spec[KIND]!r}, which no resolver answers for; the kinds declared are "
                f"{sorted(registry())}"
            )
        found.append(Resolved(spec, resolve(ctx, spec[PARAMS])))
    return found

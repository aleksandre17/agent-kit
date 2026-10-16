"""Projection shapes -- the ONE discovery of how a declared projection is SHAPED into bytes.

A projection install names a shape (`shape`), or its own target states one: a target ending in `/`
is a collection, anything else one document (`collection.kind_of`, the one convention). A module in
`shapes/` answers each. Each shape says, as data the caller dispatches over:

  * its STAGE -- a shape that projects FROM this render's own projections (a runtime's served files
    are assembled from the plane) runs after every shape that does not, whatever order the
    capabilities arrive in;
  * how it PROJECTS (bytes in memory) and how a plan FORESEES its paths without rendering a byte --
    and whether that foresight needs the view at all;
  * the paths it leaves behind that nothing renders now (`departing`), where it keeps a record
    outside the plane, and whether an unreadable foresight leaves every such path UNFORESEEABLE.

The table these rows replace lived in `projection` beside the functions it named, and every caller
that needed to know one more thing about a shape branched on its name (ADR-023 amendment 4). A new
shape is now a module, and nothing that dispatches over the set is edited (Cardinals II, IV).
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

import collection
import kinds
from errors import KitError

#: Where a projection shape may be declared. One directory, read by name, never a list kept by hand.
SHAPES = Path(__file__).resolve().parent / "shapes"
ENTRY = "SHAPES"


class RenderError(KitError):
    """A projection cannot be rendered without a name resolving to two things, or a plural
    projection does not declare soundly what it iterates and how each file is named."""

    code = "KIT0028"




@dataclass(frozen=True)
class Shape:
    """One projection shape. `project(ctx, item, view, produced, capabilities)` -> {path: text};
    `foresee(ctx, item, view, capabilities)` -> [path] (`view` is None where `reads_view` is false);
    `departing(ctx, capabilities, targets)` -> [path] outside the plane that nothing renders now."""

    stage: int
    project: object
    foresee: object
    reads_view: bool = True
    departing: object = None
    unforeseeable: bool = False


@functools.lru_cache(maxsize=None)
def registry() -> dict:
    """Every projection shape, by the name each `shapes/` module declares it under."""
    return kinds.registry(SHAPES, ENTRY, "projection shape", RenderError)


def name_of(item) -> str:
    return item.get("shape") or collection.kind_of(item)


def shape_of(item) -> Shape:
    found = registry().get(name_of(item))
    if found is None:
        raise RenderError(
            f"{item['target']!r} declares the projection shape {name_of(item)!r}, which no shape "
            f"answers for; the shapes declared are {sorted(registry())}"
        )
    return found

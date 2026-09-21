"""consumption -- a DECLARED fact of the host's reading, resolved into what a surface may say.

A detector emits; until now nothing consumed. The two halves were built a year apart and the gap
between them is the exact shape of a system that measures and then does nothing with the
measurement: every fact in the profile was produced, recorded, dated -- and read by no one.

This module is the generic half of the join and holds no fact, no capability and no subject. It
is handed a capability's `consumes` block, which names the documents carrying the rows, the field
those rows live under, and the field of a row that NAMES the fact it consumes. Every one of those
words belongs to the schema that declares them; none of them is spelled here, and the day a
capability consumes something else, nothing in this file is edited (Cardinal II, IV).

What it produces is a reading and says so: each row carries the fact it named, whether the
recorded reading CARRIES that fact, the value if it does, and the moment the reading was taken.
A row that is not bound carries no value at all -- not an empty string, not a plausible default --
so the surface has nothing to print but the absence its own declaration authored (Cardinal V).

It never probes. The reading it resolves against is the RECORDED one, taken at a stated moment,
which is what makes a later disagreement with a fresh probe detectable rather than invisible: a
resolver that re-measured would silently agree with the tree forever and no drift could exist to
be reported (Cardinal III).
"""

from __future__ import annotations

from dataclasses import dataclass

import declared


@dataclass(frozen=True)
class Consumed:
    """A capability's consumption block and the rows it resolves to, against one reading."""

    spec: dict
    rows: list


def consumed_of(ctx, capability, profile):
    """The rows this capability consumes from `profile`, or None where it consumes nothing --
    which is the ordinary answer for every capability that reads no fact, and most do not."""
    spec = capability.raw.get("consumes")
    if spec is None:
        return None
    facts, taken_at = profile["facts"], profile["taken_at"]
    rows = []
    for row in declared.rules(ctx, spec["sources"], spec["list"]):
        fact = row[spec["names"]]
        bound = fact in facts
        rows.append({
            **row,
            "fact": fact,
            "bound": bound,
            "taken_at": taken_at,
            # Present exactly when something was read. A key carrying None would render as the
            # word `null` beside a meaning, which reads like a measurement of nothing rather
            # than like a host that declared nothing.
            **({"value": facts[fact]} if bound else {}),
        })
    return Consumed(spec, rows)

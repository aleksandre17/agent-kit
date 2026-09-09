"""The plan -- a mutating verb's write set, computed as DATA before a byte is touched.

A plan is not a preview and it is not a second implementation of the apply. It is the SAME
value: the verb computes the write set once, `--plan` prints it, and the apply consumes it
entry by entry without deciding anything again. That is the only construction under which a
plan cannot drift from its apply, and a plan that can drift is worse than no plan -- it is a
promise the operator will believe exactly once.

The disposition vocabulary is declared HERE and nowhere else. The plan prints the intention
(`create`) and the apply prints the accomplished fact (`created`), which are two projections of
one word. A test that wants to compare them reads this table rather than keeping its own copy;
a second home for a vocabulary is how two correct readings begin to disagree (Cardinal III).
"""

from __future__ import annotations

#: intention -> accomplished fact. The one home of the disposition vocabulary.
DISPOSITIONS = {
    "create": "created",
    "keep": "kept",
    "replace": "replaced",
    "remove": "removed",
}


class Write:
    """One planned effect on the host. Data only: it states what would happen, and cannot act."""

    __slots__ = ("disposition", "klass", "mode", "capability", "target", "item")

    def __init__(self, disposition: str, klass: str, mode: str, capability: str,
                 target: str, item=None) -> None:
        if disposition not in DISPOSITIONS:
            raise KeyError(f"undeclared disposition {disposition!r}")
        self.disposition = disposition
        self.klass = klass
        self.mode = mode
        self.capability = capability
        self.target = target
        self.item = item

    @property
    def accomplished(self) -> str:
        return DISPOSITIONS[self.disposition]

    def as_row(self) -> tuple:
        return (self.disposition, self.klass, self.mode, self.capability, self.target)


def report(verb: str, writes) -> str:
    """The plan as the operator reads it. Every column comes from a declaration: the class and
    the mode from the install statement, the owner from the capability that declared it."""
    writes = list(writes)
    lines = [
        f"plan: {verb} would touch {len(writes)} path(s) in this host; nothing has been written.",
        f"  {'ACTION':<8}{'CLASS':<12}{'MODE':<13}{'OWNER':<13}PATH",
    ]
    for write in writes:
        lines.append(
            f"  {write.disposition:<8}{write.klass:<12}{write.mode:<13}"
            f"{write.capability:<13}{write.target}"
        )
    lines.append("plan: run the same command without --plan to apply exactly this set.")
    return "\n".join(lines)

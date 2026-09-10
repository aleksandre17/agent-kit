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


#: The columns of the plan, in order, and where each one's value comes from. A new column is a
#: row here; nothing below knows how many there are or what any of them is called.
COLUMNS = (
    ("ACTION", lambda write: write.disposition),
    ("CLASS", lambda write: write.klass),
    ("MODE", lambda write: write.mode),
    ("OWNER", lambda write: write.capability),
    ("PATH", lambda write: write.target),
)

#: The gap between one column and the next. One space would still separate the columns; two make
#: the table readable, and neither is ever zero -- which is the whole point of measuring.
GUTTER = 2


def report(verb: str, writes) -> str:
    """The plan as the operator reads it. Every column comes from a declaration: the class and
    the mode from the install statement, the owner from the capability that declared it.

    The column widths are MEASURED from the values, never fixed. A hard-coded width is a boundary
    with an assumption in it: the day a declared name is longer than somebody once guessed, two
    columns run together, the row still reads as a plausible row, and every reader -- human and
    machine -- parses one field where there were two. It cost this project a green suite the first
    time a capability had a longer name than the ones the width was chosen for.
    """
    writes = list(writes)
    rows = [[read(write) for _title, read in COLUMNS] for write in writes]
    widths = [
        max(len(title), *(len(row[index]) for row in rows)) if rows else len(title)
        for index, (title, _read) in enumerate(COLUMNS)
    ]

    def line(values) -> str:
        cells = [value.ljust(widths[index]) for index, value in enumerate(values)]
        return "  " + (" " * GUTTER).join(cells).rstrip()

    lines = [
        f"plan: {verb} would touch {len(writes)} path(s) in this host; nothing has been written.",
        line([title for title, _read in COLUMNS]),
    ]
    lines += [line(row) for row in rows]
    lines.append("plan: run the same command without --plan to apply exactly this set.")
    return "\n".join(lines)

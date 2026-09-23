"""A declared limit on the work, and the reading that says whether it has been spent.

A record may declare an APPETITE: how much this host is willing to spend on it, as an amount and
the unit the amount is counted in (ADR-020 decision 9). The amount is always the HOST's. Nothing
in this file carries a number, no default is supplied anywhere, and there is no ceiling here for
an amount to be measured against -- a limit a framework chose is a limit nobody undertook, which
is exactly the defect a framework that answers its host's questions keeps producing.

What has been SPENT is never written down beside the limit. It is read, passively, from the
records of spend the system already writes, and nothing is run a second time to measure it. That is what
lets the grammar of a limit stay closed at two fields: there is nowhere to type a consumption,
nowhere to record that a limit was raised, and no field a principal under pressure could edit into
agreement with the work.

WHICH units can be read is an OPEN registry, discovered exactly as a kind of proof is: a module
publishes the units it answers and it is found because it is there, never because a list here
mentions it. So the units a host may DECLARE and the units this host can READ are two different
truths with one home each -- a vocabulary, and the modules installed beside this one -- and the
gap between them is said out loud rather than smoothed over: a limit nothing can measure reads
exactly like a limit that is being kept, and that is the one failure invisible from where the
reader stands.

Nothing here raises a limit, ends a piece of work, or moves anything. A limit found spent is
REPORTED, with the exit NAMED: what happens next is a decision by the owner, taken on the record.
A mechanism that decided it would be answering the one question no machine may answer -- whether
work is worth finishing -- and a mechanism that quietly extended the limit instead would be the
silent extension with a paper trail that every unbinding budget in the field degenerates into.
"""

from __future__ import annotations

from pathlib import Path

import collection
import kinds
from errors import KitError

#: Where a unit may be answered, and the entry a module publishes there. One home each.
SPEND = Path(__file__).resolve().parent / "spend"
ENTRY = "READINGS"

#: The field a record declares its limit in, and the two fields that limit carries. Read at both
#: ends of every boundary this crosses: the grammar that judges a record, and the reading below.
APPETITE, AMOUNT, UNIT = "appetite", "amount", "unit"

#: Who the record says it belongs to. Named here because a report about a limit that did not name
#: the door it stops at would be telling an operator that something is wrong and nothing about who
#: may answer it.
OWNER = "owner"


class AppetiteError(KitError):
    """Two modules claim one unit of spend."""

    code = "KIT0062"


def registry() -> dict:
    """Every unit this host can read a spend in, by the name each module declares."""
    return kinds.registry(SPEND, ENTRY, "unit of spend", AppetiteError)


class Spend:
    """How much has been consumed of one unit, and the reading that produced it.

    `amount` is None where no reading was taken at all -- never 0. A world that could not be read
    has not spent nothing; it holds a question nobody asked, and a zero there would report a
    record nobody looked at as a record saying the work has so far cost nothing. The reading is
    carried beside the number because a quantity a reader cannot audit is testimony again, and
    because a number that does not say when and from what it was taken cannot be contradicted.
    """

    __slots__ = ("amount", "reading")

    def __init__(self, amount, reading: str) -> None:
        self.amount = amount
        self.reading = reading

    @classmethod
    def unreadable(cls, reading: str) -> "Spend":
        """No reading was taken. Never a zero, and never a limit kept."""
        return cls(None, reading)

    def __repr__(self) -> str:
        return f"Spend({self.amount!r}, {self.reading!r})"


def declared_by(record: dict):
    """The limit this record declares, or None where it declares none -- which is ordinary."""
    return record.get(APPETITE)


def spent(ctx, record: dict, unit: str) -> Spend:
    """What this record has consumed of one unit, read through the module registered for it."""
    answering = registry()
    if unit not in answering:
        return Spend.unreadable(
            f"nothing installed here reads a spend counted in {unit!r}; this host can read "
            f"{sorted(answering)}. Nothing was observed, so nothing is claimed in either direction"
        )
    return answering[unit](ctx, record)


def _who_decides(record: dict) -> str:
    owner = record.get(OWNER)
    return f"its owner, {owner!r}" if owner else "its owner, whom this record does not name"


def _past_it(record: dict, limit: dict, reading: Spend) -> str:
    return (
        f"record {record[collection.IDENTITY]!r} declared a limit of {limit[AMOUNT]} "
        f"{limit[UNIT]!r} and {reading.reading} -- which is past it. The line stops here, and what "
        f"happens next is a decision by {_who_decides(record)}, taken on the record as a passage "
        f"like any other. Nothing here raises the limit and nothing here ends the work: a limit "
        f"raised by the principal spending it is not a limit, and a machine that ended the work "
        f"would be deciding it was not worth finishing"
    )


def _cannot_be_measured(record: dict, limit: dict, reading: Spend) -> str:
    return (
        f"record {record[collection.IDENTITY]!r} declares a limit of {limit[AMOUNT]} "
        f"{limit[UNIT]!r}, and {reading.reading}. A limit nothing can measure reads exactly like a "
        f"limit that is being kept, which is why it is said here rather than left for a reader to "
        f"discover -- install a reading for that unit, or declare the limit in one this host reads"
    )


def unkept(ctx, records) -> list:
    """Every declared limit this reading cannot stand behind, in the words of what was found.

    Two different facts, and they stay two. A limit measurably spent is a fact about the WORK and
    the report names the door it stops at. A limit nothing here can measure is a fact about the
    DECLARATION, and the cure is a reading or a different unit. One sentence for both would send
    the reader to the wrong file.

    A record that declares no limit is passed over in silence, and that is not forbearance: there
    is nothing to read, nothing was undertaken, and a reading that said something about it would
    be inventing a limit on the record's behalf.
    """
    said = []
    for record in sorted(records, key=lambda r: r[collection.IDENTITY]):
        limit = declared_by(record)
        if limit is None:
            continue
        reading = spent(ctx, record, limit[UNIT])
        if reading.amount is None:
            said.append(_cannot_be_measured(record, limit, reading))
        elif reading.amount > limit[AMOUNT]:
            said.append(_past_it(record, limit, reading))
    return said

"""A criterion's status, COMPUTED by resolving the proof it names (ADR-020 decision 7).

Nothing here is ticked and no status is read off a document. A criterion DECLARES what would prove
it -- a kind of reference and the referent -- and this module hands that reference to the module
registered for its kind, which comes back with a reading: it held, it did not hold, or it could not
be read at all. Those three are different facts about the world and they stay three. A referent
nobody can find is not a refutation, and a refutation is not an absence; collapsing either into the
other makes a broken path read as broken work and trains the reader to ignore both.

The kinds of reference are an OPEN registry, discovered exactly as the kinds of rule are. A new way
of proving something is a MODULE that publishes what it answers, never a branch here: the day a
signature, a walked journey or a receipt becomes readable, this file is not the file that changes
(Cardinal II). A kind nothing installed here answers is not an error either -- it is a reading
nobody can take, which is one of the three.

And it holds no word of the status vocabulary. The words are rows of a declaration a host reads,
each carrying the machine fact that says which reading it is the word for; the mapping is made from
that fact, handed in as a value. A fourth reading is therefore a row plus a resolver, and still not
an edit here (Cardinal IV).
"""

from __future__ import annotations

from pathlib import Path

import collection
import kinds
from errors import KitError

#: Where a kind of reference may be answered. One directory, read by name, never a list by hand.
PROOFS = Path(__file__).resolve().parent / "proofs"

#: The entry a resolver module publishes, and the fields a reference carries. One home each.
ENTRY = "RESOLVERS"
PROOF = "proof"
KIND = "kind"
REFERENT = "ref"
PARAMS = "params"

#: The machine fact a status row carries: which of the three readings that word is the word for.
HOLDS = "holds"


class CriterionError(KitError):
    """Two modules claim one kind of proof, or a reading the status vocabulary has no word for."""

    code = "KIT0060"


def registry() -> dict:
    """Every kind of reference this host can read, by the name each resolver declares."""
    return kinds.registry(PROOFS, ENTRY, "kind of proof", CriterionError)


class Verdict:
    """What a reference resolved to, and the reading that produced it.

    `holds` is three-valued on purpose and is never flattened to a boolean: true is a proof that
    was taken and held, false is a proof that was taken and did not, and None is no reading at all.
    The text is carried beside it because a verdict a reader cannot audit is testimony again.
    """

    __slots__ = ("holds", "reading")

    def __init__(self, holds, reading: str) -> None:
        self.holds = holds
        self.reading = reading

    @classmethod
    def unreadable(cls, reading: str) -> "Verdict":
        """No reading was taken. Never a pass, and never a failure."""
        return cls(None, reading)

    def __repr__(self) -> str:
        return f"Verdict({self.holds!r}, {self.reading!r})"


class Request:
    """What a resolver is handed: the context it may read the world through, the reference it was
    asked about, the record the reference is about, and the way back in for a reference that is
    about other references -- carrying the trail, so a reference that stands on itself is caught."""

    __slots__ = ("ctx", "proof", "subject", "seen")

    def __init__(self, ctx, proof: dict, subject, seen: frozenset) -> None:
        self.ctx = ctx
        self.proof = proof
        self.subject = subject
        self.seen = seen

    @property
    def ref(self):
        return self.proof.get(REFERENT)

    @property
    def params(self) -> dict:
        return self.proof.get(PARAMS) or {}

    def about(self, proof: dict, subject=None) -> Verdict:
        """One more reference, resolved from inside this one, with the trail carried forward."""
        return resolve(self.ctx, proof,
                       self.subject if subject is None else subject, self.seen)


def _trail(proof: dict, subject) -> tuple:
    identity = subject.get(collection.IDENTITY) if isinstance(subject, dict) else None
    return (proof.get(KIND), proof.get(REFERENT), identity)


def resolve(ctx, proof: dict, subject, seen: frozenset = frozenset()) -> Verdict:
    """One typed reference, resolved by the module registered for its kind.

    Three things end here as an unreadable verdict rather than as a refusal, because each of them
    is an honest state of a young declaration and none of them is a fact about the work: a
    reference whose kind nothing installed answers, a reference that carries no kind at all, and a
    reference that has arrived back at itself.
    """
    if not isinstance(proof, dict) or proof.get(KIND) is None:
        return Verdict.unreadable(
            f"this reference carries no {KIND!r}, so nothing can be asked to read it"
        )
    answering = registry()
    kind = proof[KIND]
    if kind not in answering:
        return Verdict.unreadable(
            f"no resolver installed here reads a proof of kind {kind!r}; this host can read "
            f"{sorted(answering)}. Nothing was observed, so nothing is claimed"
        )
    trail = _trail(proof, subject)
    if trail in seen:
        return Verdict.unreadable(
            f"a proof of kind {kind!r} about {proof.get(REFERENT)!r} has arrived back at itself; "
            f"a reference that stands on its own reading proves nothing and is not followed"
        )
    return answering[kind](Request(ctx, proof, subject, seen | {trail}))


def read(ctx, record: dict, field: str) -> list:
    """Every criterion the record declares in `field`, each with the verdict its own proof
    resolved to. A record that declares none reads as an empty list, which is a complete state:
    nothing was stated, so nothing is unmet and nothing is proved."""
    return [(item, resolve(ctx, item.get(PROOF), record)) for item in (record.get(field) or [])]


#: What a surface may COUNT about the criteria a record declares, and the names it counts under.
#: Two numbers and no word: the word for a reading belongs to the host's vocabulary, and a name
#: spelled here would be a second home for it.
HELD, DECLARED = "criteria_held", "criteria_declared"


def tally(ctx, record: dict, field: str) -> dict:
    """How many of a record's criteria were PROVED by the reference each names, out of how many
    the record declares. Computed at the moment the surface is, from the records themselves --
    never read off a field, because there is no field to read it off and there will not be one.

    A record that declares nothing counts 0 of 0. That is the honest reading of a record nobody
    has shaped: nothing was stated, so nothing is proved and nothing is unmet.

    A criterion that could not be read at all is NOT among the held. It is not counted as refuted
    either -- the count simply does not claim it -- because a tally that promoted an absence to a
    proof would be lying in the one place this whole mechanism exists to stop it (Cardinal V).
    """
    readings = read(ctx, record, field)
    return {HELD: sum(1 for _item, verdict in readings if verdict.holds is True),
            DECLARED: len(readings)}


def status_of(verdict: Verdict, rows: list) -> str:
    """The WORD for a reading, taken from the vocabulary handed in -- never spelled here.

    The rows are the host's declaration; each carries the machine fact that says which reading it
    names. A reading no row names is refused rather than labelled with the nearest word: a surface
    that printed an approximate status would be lying in the one place the whole mechanism exists
    to stop it (Cardinal V).
    """
    for row in rows:
        if row.get(HOLDS) is verdict.holds:
            return row[collection.IDENTITY]
    raise CriterionError(
        f"a proof resolved to {verdict.holds!r} and the status vocabulary declares no word for "
        f"that reading; it declares {[row.get(collection.IDENTITY) for row in rows]}. The reading "
        f"stands and is unnamed -- declare the row rather than print the nearest word"
    )

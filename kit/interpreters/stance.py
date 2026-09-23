"""The stance a gate stands in -- RESOLVED from declarations, never decided here (ADR-006).

A gate's failure is a fact; what that fact DOES to `check` is a stance, and a stance is data with
three possible authors, read in one order: the host's own row in its answers file, else the stance
the gate's publisher ships it in, else the vocabulary's declared `unanswered` stance. There is no
fourth rung and no default held in this module -- the last rung is itself a declaration.

This module knows no gate id, no capability and no stance by name. What a stance MEANS is its row:
`fails` says whether a failure fails `check`, `rank` orders the rows so a publisher's FLOOR can be
compared without a name ever being spelled here. A floor is Rust's `forbid`: an inner scope -- the
host -- may not lower it, and an attempt is refused rather than clamped, because a stance silently
raised back is a declaration the surface would then misreport.

Every refusal here is one question answered twice or not at all. Ambiguity resolves to NOTHING.
"""

from __future__ import annotations

from errors import KitError

#: The schema a stance vocabulary honours. The vocabulary is FOUND by the contract it keeps,
#: exactly as an answers file is found by its install mode -- never by a path or an owner's name.
VOCABULARY_SCHEMA = "stance"


class StanceError(KitError):
    """A gate's stance cannot be honoured as declared: a stance no vocabulary row names, a host
    lowering a gate below its publisher's floor, one gate answered twice, or no single vocabulary
    to read. Refused rather than resolved, because any resolution here would be a guess."""

    code = "KIT0030"


class Resolved:
    """One gate's stance, with WHO put it there. A stance without its source is a verdict whose
    authority nobody can check -- which is the whole difference between observing and ignoring."""

    __slots__ = ("stance", "row", "source")

    def __init__(self, stance: str, row: dict, source: str) -> None:
        self.stance, self.row, self.source = stance, row, source

    @property
    def fails(self) -> bool:
        return self.row["fails"]

    def label(self) -> str:
        return f"[{self.stance}: {self.source}]"


def vocabulary(manifest) -> tuple[dict, str]:
    """Stance id -> its row, and the unanswered stance. Exactly one vocabulary, always: zero would
    leave every gate's consequence undeclared, two would give one stance two meanings."""
    found = [(c.id, c.documents[d["id"]]) for c in manifest.capabilities
             for d in c.raw.get("documents", []) if d["validates"] == VOCABULARY_SCHEMA]
    if len(found) != 1:
        raise StanceError(
            f"this kit declares {len(found)} stance vocabularies "
            f"({sorted(owner for owner, _doc in found)}); exactly one is required, because what "
            f"a failing gate does to `check` must have exactly one meaning"
        )
    document = found[0][1]
    rows: dict = {}
    for row in document["stances"]:
        if row["id"] in rows:
            raise StanceError(f"the stance vocabulary declares {row['id']!r} twice")
        rows[row["id"]] = row
    if document["unanswered"] not in rows:
        raise StanceError(
            f"the stance vocabulary names {document['unanswered']!r} as the stance of an "
            f"unanswered gate, and declares no such stance; stances are {sorted(rows)}"
        )
    return rows, document["unanswered"]


def _row(rows: dict, stance: str, where: str) -> dict:
    if stance not in rows:
        raise StanceError(f"{where} names stance {stance!r}; the vocabulary declares {sorted(rows)}")
    return rows[stance]


def resolve(manifest, answers: dict, enabled, matured: "dict | None" = None) -> tuple[dict, list]:
    """(capability id, gate id) -> Resolved for every gate an ENABLED capability declares, and the
    host rows that bind no such gate. Every gate the kit declares is checked for a sound floor,
    enabled or not: a stance that lowers a floor is illegitimate whether or not the gate runs.

    `matured` carries the gate kinds whose concession the HOST'S OWN undertaking has spent -- the
    fact is read elsewhere, by whoever owns those rows, and arrives here already taken. What it
    does is the narrowest thing that can be called a maturation: a rung that does not fail is a
    CONCESSION, a concession rests on an undertaking, and when the undertaking is finished the gate
    stands where a gate nobody answered for stands. It can only ever REMOVE a concession -- a
    declaration that already ranks at or above that rung is untouched, so nothing here can lower
    what a publisher or a host declared, and no stance is written into any document by anyone.
    The surface names the maturation and the row that caused it, because a consequence whose origin
    a reader cannot check is the same thing as a machine that decided (Cardinal V).
    """
    rows, unanswered = vocabulary(manifest)

    declared: dict = {}
    for capability in manifest.capabilities:
        for gate in capability.gates:
            declared.setdefault(gate["id"], []).append((capability.id, gate))
            published = gate.get("stance", {})
            where = f"capability {capability.id!r}, gate {gate['id']!r}"
            floor = _row(rows, published["floor"], where) if "floor" in published else None
            ships = _row(rows, published["ships"], where) if "ships" in published else None
            if floor and ships and ships["rank"] < floor["rank"]:
                raise StanceError(f"{where} ships in {ships['id']!r}, below its own floor {floor['id']!r}")

    host: dict = {}
    for entry in answers.get("stances", []):
        gate_id = entry["gate"]
        if gate_id in host:
            raise StanceError(
                f"the host answers gate {gate_id!r} twice ({host[gate_id]['stance']!r} and "
                f"{entry['stance']!r}); one gate has one stance"
            )
        chosen = _row(rows, entry["stance"], f"the host's stance for gate {gate_id!r}")
        publishers = declared.get(gate_id, [])
        if len(publishers) > 1:
            raise StanceError(
                f"the host's stance names gate {gate_id!r}, which "
                f"{sorted(owner for owner, _g in publishers)} all declare; a stance needs one referent"
            )
        for owner, gate in publishers:
            floor_id = gate.get("stance", {}).get("floor")
            if floor_id and chosen["rank"] < rows[floor_id]["rank"]:
                raise StanceError(
                    f"the host declares gate {gate_id!r} {entry['stance']!r} (by {entry['by']} at "
                    f"{entry['at']}), below the floor {floor_id!r} its publisher {owner!r} declared. "
                    f"A floor holds the kit's own promise about itself; only its publisher may "
                    f"lower it, never a host"
                )
        host[gate_id] = entry

    resolved: dict = {}
    for capability in enabled:
        for gate in capability.gates:
            published = gate.get("stance", {})
            if gate["id"] in host:
                entry = host[gate["id"]]
                stance, source = entry["stance"], f"declared by {entry['by']} at {entry['at']}"
            elif "ships" in published:
                stance, source = published["ships"], f"shipped so by capability {capability.id!r}"
            else:
                stance, source = unanswered, "unanswered -- the vocabulary's declared default"
            grown = (matured or {}).get(gate["kind"])
            if grown is not None and rows[stance]["rank"] < rows[unanswered]["rank"]:
                stance, source = unanswered, grown.says()
            resolved[(capability.id, gate["id"])] = Resolved(stance, rows[stance], source)

    running = {gate_id for _cap, gate_id in resolved}
    unbound = [entry for gate_id, entry in host.items() if gate_id not in running]
    return resolved, unbound

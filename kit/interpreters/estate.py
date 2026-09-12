"""The ESTATE -- what a host RECEIVED from the kit, stated by the kit, read at a stated moment.

`kit.lock.json` says what the kit IS. This says what a host WAS GIVEN, and it is the same idea
applied to the other side of the boundary. It exists because of one fact that has no workaround:

    a tree cannot state what it was GIVEN -- only what it IS, and from inside the tree those two
    readings are indistinguishable.

Everything an upgrade must decide turns on telling apart *the host edited this* from *upstream
changed this*, and neither is visible in the bytes on disk. Recovering the first reading by
looking at the second is an inference from the tree about something a declaration should have
stated -- the defect this project has now paid for twice. So it is DECLARED: every path the kit
wrote, with the class and mode that wrote it, the capability that owns it, and the digest of the
bytes as they went down. Plus a moment, and the NAME of whoever accepted the writes.

Three things this module refuses to do:

  * it never decides what a state MEANS. Who owns a path's bytes, and what each cell of a
    three-way reading implies, is `stewardship.json`. This measures; `reconcile` looks up.
  * it never invents a digest. Where a digest would measure nothing -- a directory the host
    fills, the estate's own file -- the steward declares `not-taken` and the row carries null.
    Null is a declared absence of a measurement and is never read as a value.
  * it never writes outside a declared install. The estate's own path is an `installs` entry like
    any other, so the write permission is the one every capability already has, and this verb
    invents no authority `init` did not have.
"""

from __future__ import annotations

import hashlib

from errors import KitError
from plan import DISPOSITIONS

ALGORITHM = "sha256"
NEWLINE = "lf"

#: The install mode whose target IS the estate. Found through the declarations, never by a path
#: constant: a path spelled in an interpreter is a second home for a truth a capability states,
#: and it is the home nobody can change.
MODE = "estate"

#: The id under which some capability ships the stewardship declaration.
STEWARDSHIP = "stewardship"

#: What a steward says about measuring its paths.
RECORDED = "recorded"
NOT_TAKEN = "not-taken"

#: What happens to a ROW, as the stewardship schema enumerates it. A row's fate is a separate
#: axis from its file's: a path can be left untouched on disk and still have its digest advance,
#: or be kept on disk and dropped from the account. Collapsing the two erases the one thing this
#: record exists to hold -- a divergence measured back onto the row is a divergence forgotten.
ADVANCE = "advance"
CARRY = "carry"
ORPHAN = "orphan"

#: The row field that records a signed TRANSFER of a path to the host (ADR-010). Named here, the
#: one module that reads and writes rows; its shape is the estate schema's.
CEDED = "ceded"


class EstateError(KitError):
    """The host's record of what it received is absent, or cannot be honestly taken."""

    code = "KIT0008"


class Stewardship:
    """The stewardship declaration, read once and asked questions. It holds no behaviour, and
    this class adds none: every answer here is a lookup that REFUSES when the declaration is
    silent. A default would be a rule nobody declared, arriving the day a new mode does."""

    def __init__(self, raw: dict) -> None:
        self._raw = raw
        self._by_mode = {}
        for row in raw["modes"]:
            if row["mode"] in self._by_mode:
                raise EstateError(
                    f"install mode {row['mode']!r} is given two stewards -- a mode whose owner "
                    f"resolves to two answers has no owner"
                )
            self._by_mode[row["mode"]] = row["steward"]
        self._stewards = {}
        for steward in raw["stewards"]:
            self._stewards[steward["id"]] = steward
            for row in steward["cells"]:
                # The disposition vocabulary has ONE home and it is the plan's. A declaration may
                # consume a word from it and may not invent one beside it: a steward naming an
                # effect the plan cannot carry out would read perfectly and mean nothing.
                if row["file"] not in DISPOSITIONS:
                    raise EstateError(
                        f"steward {steward['id']!r} answers the cell {row['cell']!r} with "
                        f"{row['file']!r}, which is not something a plan can do; the "
                        f"dispositions are {sorted(DISPOSITIONS)}"
                    )
        undeclared = sorted((set(self._by_mode.values())
                             | {s["transfers_to"]["steward"] for s in raw["stewards"]
                                if s.get("transfers_to")}) - set(self._stewards))
        if undeclared:
            raise EstateError(
                f"stewardship names {undeclared} as owners and declares none of them; a steward "
                f"that is only ever referred to has stated nothing about what it owns"
            )

    @property
    def stewards(self) -> list:
        return [dict(s) for s in self._raw["stewards"]]

    def of_mode(self, mode: str) -> str:
        if mode not in self._by_mode:
            raise EstateError(
                f"install mode {mode!r} declares no steward, so nothing states who owns the bytes "
                f"it writes. A reconciliation cannot be attempted over a path whose owner is "
                f"unknown -- declare it in stewardship.json rather than defaulting it here"
            )
        return self._by_mode[mode]

    def measures(self, steward: str) -> bool:
        return self._steward(steward)["digest"] == RECORDED

    def transfer(self, steward: str):
        """Where a path this steward holds goes when a host takes it over -- `{steward, class}` --
        or None where the declaration offers no transfer. None is an answer, not a default: it is
        the declaration saying there is nothing here for a host to take (ADR-010)."""
        return self._steward(steward).get("transfers_to")

    def named(self, steward: str) -> bool:
        """Whether every path this steward holds is printed on every reading, whatever its cell."""
        return bool(self._steward(steward).get("named"))

    def answering(self, mode: str, recorded=None) -> str:
        """The steward that answers for a path NOW: its mode's, unless the row it was recorded on
        carries a signed transfer, in which case the one that steward declares it transfers to.
        A row claiming a transfer its steward does not offer is refused -- the record would then
        be stating an ownership no declaration ever made possible."""
        steward = self.of_mode(mode)
        if not (recorded or {}).get(CEDED):
            return steward
        transfer = self.transfer(steward)
        if transfer is None:
            raise EstateError(
                f"{recorded['path']}: the record says this path was taken over by "
                f"{recorded[CEDED]['signed_by']} at {recorded[CEDED]['signed_at']}, and its "
                f"steward {steward!r} declares no transfer. An ownership nothing could have "
                f"granted is not read as one"
            )
        return transfer["steward"]

    def verdict(self, steward: str, cell: str) -> dict:
        for row in self._steward(steward)["cells"]:
            if row["cell"] == cell:
                return row
        raise EstateError(
            f"steward {steward!r} says nothing about a path in the cell {cell!r}. This reading is "
            f"real and the declaration does not answer it; a reconciliation that always finds a "
            f"safe answer certifies rather than measures, so it is refused instead"
        )

    def _steward(self, steward: str) -> dict:
        if steward not in self._stewards:
            raise EstateError(f"no steward named {steward!r} is declared by this kit")
        return self._stewards[steward]


def stewardship(ctx) -> Stewardship:
    """The one stewardship declaration this kit ships. Two would be two homes for one truth;
    zero means the kit cannot say who owns anything it writes, and neither is survivable."""
    found = [c.documents[STEWARDSHIP] for c in ctx.manifest.capabilities
             if STEWARDSHIP in c.documents]
    if len(found) != 1:
        raise EstateError(
            f"this kit ships {len(found)} stewardship declarations; exactly one is required, "
            f"because a path has exactly one owner"
        )
    return Stewardship(found[0])


def target(ctx, required: bool = True):
    """Where the estate lives, asked of the declarations."""
    item = ctx.install_of_mode(MODE, required=required)
    return item["target"] if item else None


def is_root(path: str) -> bool:
    """A declared target naming a COLLECTION rather than a document -- the same '/' rule the rest
    of this kit reads, never a second convention."""
    return path.endswith("/")


def _shipping(ctx, path: str, incoming: dict):
    """The bytes this run leaves at a path: the payload's where one is being written, and
    whatever is there otherwise."""
    item = incoming.get(path)
    if item is not None:
        return hashlib.sha256(
            ctx.manifest.payload_text(item["source"]).encode("utf-8")).hexdigest()
    return _digest(ctx.workspace, path)


def _digest(ws, path: str):
    if not ws.exists(path) or ws.path(path).is_dir():
        return None
    return hashlib.sha256(ws.read_bytes(path)).hexdigest()


def rows(ctx, capabilities, stewards: Stewardship, recorded=None, decided=None,
         writes=()) -> list:
    """Every path this kit accounts for in this host, and what the kit GAVE at each one.

    Measuring the disk is right only where this run actually delivered something. Where a
    reconciliation decided to CARRY a row -- a file the host changed and the kit left alone --
    measuring would write the host's own bytes into the record as though the kit had shipped
    them, and the divergence would be gone by the next run: erased by the act of recording it.
    So the outcome for the row arrives as data, from the declaration that decided it, and an
    absent decision means this run gave what it says it gave.
    """
    prior = {row["path"]: row for row in (recorded or {}).get("files", [])}
    decided = decided or {}
    #: What the FORESEEN writes will leave at a path, where a declaration can say so before the
    #: byte is written: a source's payload is the bytes, verbatim. Reading the disk instead would
    #: make this record depend on WHEN it was taken relative to the writes it describes -- the
    #: plan would foresee one document and the apply would leave another, over the one file whose
    #: whole job is to say what happened.
    incoming = {write.target: write.item for write in writes
                if write.disposition != "keep" and (write.item or {}).get("source")}
    found = {}
    for capability in capabilities:
        for item in capability.installs:
            steward = stewards.of_mode(item["mode"])
            path = item["target"]
            if path in found:
                raise EstateError(
                    f"{path}: installed by {found[path]['capability']!r} and by "
                    f"{capability.id!r} -- one path with two owners is not a path"
                )
            taken = (stewards.measures(steward) and not is_root(path))
            outcome = (decided.get(path) or {}).get("record", ADVANCE)
            held = prior.get(path)
            # A row the host has TAKEN OVER is carried whatever this run decided about the path:
            # the kit rebuilding it would re-measure the host's bytes as though the kit had
            # shipped them and erase the signature that says whose they are (ADR-010).
            if held is not None and (outcome == CARRY or held.get(CEDED)):
                found[path] = dict(held)
            else:
                found[path] = {
                    "path": path,
                    "class": item["class"],
                    "mode": item["mode"],
                    "capability": capability.id,
                    "digest": _shipping(ctx, path, incoming) if taken else None,
                }
            # An acceptance is carried ONTO the row it is about. A record of what was overwritten,
            # kept anywhere other than beside the thing overwritten, is a record nobody reading
            # that path will ever find.
            found[path].update(ctx.adopted.get(path, {}))
    return [found[path] for path in sorted(found)]


def document(ctx, entries: list, moment: str, signed_by: str, taken=()) -> dict:
    """The reading, as it is stored. No count stands beside `files`: an empty list is already a
    declared zero, and a derived number is a thing no host was ever told -- the honest place for a
    count is the surface that prints it, in front of the reader who can see it computed."""
    return {
        "schema_version": ctx.manifest.version_of(ctx.install_of_mode(MODE)["validates"]),
        "kit_version": ctx.manifest.version,
        "algorithm": ALGORITHM,
        "newline": NEWLINE,
        "taken_at": moment,
        "signed_by": signed_by,
        "files": list(entries),
        # What this host TOOK from outside the kit, each pinned at the door that took it
        # (ADR-008). It lives here because it is the same proposition as `files` read one step
        # further upstream: what this host was GIVEN, stated rather than inferred. Built and
        # judged by `provenance`; this module only carries it.
        "taken": list(taken),
    }


def read(ctx):
    """The recorded estate, or None where this host has never had one taken. The absence is
    returned rather than filled in: what a host was given is not a thing that can be guessed."""
    path = target(ctx, required=False)
    if path is None or not ctx.workspace.exists(path):
        return None
    return ctx.binding(path, ctx.install_of_mode(MODE)["validates"])


def restates(recorded, ctx, entries: list, signed_by: str, taken=None) -> bool:
    """Whether a fresh reading would say exactly what the recorded one already says.

    `taken_at` is the moment this host RECEIVED these bytes -- not the moment somebody ran the
    command again. Rewriting the document because a run happened would move that moment forward
    over an install that never occurred, and the record would then date a delivery to a day
    nothing was delivered. So an unchanged reading is KEPT, and the moment it states goes on
    being true. That is the same rule the rest of this kit follows for every host-owned path,
    arrived at from the other side: a reading is not restated by being re-taken.
    """
    if recorded is None:
        return False
    return (recorded["files"] == entries
            and recorded["kit_version"] == ctx.manifest.version
            and recorded["signed_by"] == signed_by
            and (taken is None or recorded.get("taken", []) == list(taken)))


def take(ctx, capabilities, moment: str, signed_by: str, entries=None, writes=(),
         taken=None) -> dict:
    """Measure this host and record what it holds. Written through a workspace scoped to the
    declaring capability's own targets -- `installs` is the write permission, and an estate is
    not a way around it."""
    stewards = stewardship(ctx)
    path = target(ctx)
    owner = next(c for c in capabilities for i in c.installs if i["target"] == path)
    if entries is None:
        entries = rows(ctx, capabilities, stewards, read(ctx), ctx.decided, writes)
    if taken is None:
        # A writer that did not come through the provenance door CARRIES the pins it found. A
        # record rewritten without them would declare, with a fresh moment on it, that this host
        # took nothing -- and the next reading would call every pinned capability a stranger.
        taken = (read(ctx) or {}).get("taken", [])
    record = document(ctx, entries, moment, signed_by, taken)
    errors = ctx.manifest.validate(record, ctx.install_of_mode(MODE)["validates"])
    if errors:
        raise EstateError("the estate reading does not honour its own schema:\n  "
                          + "\n  ".join(errors))
    ctx.workspace.scoped(owner.targets()).write_json(path, record)
    return record

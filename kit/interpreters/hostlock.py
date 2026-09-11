"""The hold one runtime takes on one host, so that two of them cannot install into it at once.

A lock is not a mutex and it is not a heuristic. It is a DECLARATION, on disk, in the plane that
holds what a run leaves behind, saying: this owner, on this machine, in this process, took this
host at this moment, and has not said it finished. Everything about it follows from two facts a
lock file cannot escape:

  * a process that is KILLED never releases anything, so the hold it took stays on disk forever;
  * no reader can tell, from the file alone, whether the holder is dead or merely slow.

Which is why this module contains no timeout, no age limit and no "it looked old". A lock broken
because it was old silently resurrects a run that was still working, and puts two writers in one
tree -- the exact failure the lock was installed to prevent, now arriving with a reassuring
message. So a held lock is a DOOR: the run is refused, the hold is described in full -- who, which
machine, which pid, since when, and how long that has been -- and a HUMAN breaks it by name. Age
is REPORTED because a person needs it to decide; it is never ACTED on, because a machine may not.

Releasing does not delete. A lock that vanished at the end of a run leaves a host that cannot say
whether it was ever held, and the acts of breaking one would vanish with it. The hold is CLOSED
instead -- rewritten once, in a `finally`, with its ending and its moment -- exactly as a run's
receipt is. A document with no ending is a hold that is still standing, and that is the only test
there is.
"""

from __future__ import annotations

import getpass
import os
import platform

import doors
from errors import KitError

#: The record's shape version. This module writes the document, so it names the contract it
#: writes to. There is deliberately no kit schema for it yet -- see the report accompanying this
#: slice; a validated shape is the missing half and it is named rather than implied.
SCHEMA_VERSION = 1

#: The document's name inside the plane that holds observed state. The kit's vocabulary; the
#: PLACE it resolves to is the manifest's declaration and is never written here.
NAME = "init.lock"

#: The one field that answers "is this hold still standing". Its ABSENCE is the held state, which
#: is why the field is never written at open: a hold that declared its own ending in advance would
#: be a record certifying something that has not happened.
RELEASED_AT = "released_at"


class LockError(KitError):
    """A lock document exists and cannot be read as one. Refused rather than overwritten: a hold
    nobody can read is still a hold somebody may be standing behind."""

    code = "KIT0010"


def who() -> str:
    """The owner, measured at the boundary rather than assumed. A hold with no name on it is a
    hold no one can be asked about, and it is the reason a person breaking it has to guess."""
    try:
        return getpass.getuser()
    except Exception:  # noqa: BLE001 -- a host with no resolvable user is a reading, not a crash
        return "-"


def read(ctx, rel: str):
    """The lock document, or None where there has never been one."""
    if not ctx.workspace.exists(rel):
        return None
    try:
        value = ctx.workspace.read_json(rel)
    except ValueError as exc:
        raise LockError(
            f"{rel} exists and is not readable as a lock -- {exc}. It is not overwritten: a hold "
            f"nobody can read may still have somebody standing behind it. Move it aside by hand."
        ) from exc
    if not isinstance(value, dict):
        raise LockError(f"{rel} is not a lock document")
    return value


def standing(lock) -> bool:
    """A hold is standing while it has declared no ending. Nothing here looks at a clock."""
    return bool(lock) and not lock.get(RELEASED_AT)


class Hold:
    """One taken hold, carried by the run that took it, closed exactly once."""

    __slots__ = ("workspace", "clock", "rel", "value")

    def __init__(self, workspace, clock, rel: str, value: dict) -> None:
        self.workspace = workspace
        self.clock = clock
        self.rel = rel
        self.value = value

    @property
    def broke(self):
        """The hold this one superseded, where a human declared it broken -- so that the caller
        can put that declaration somewhere it will OUTLIVE this lock."""
        return self.value.get("broke")

    def release(self, code: int, message: str = None) -> None:
        self.value[RELEASED_AT] = self.clock.now()
        self.value["exit_code"] = code
        if message:
            self.value["ended_because"] = message
        self.workspace.write_json(self.rel, self.value)


def _refuse(existing, rel: str, verb: str, now: str) -> None:
    doors.refuse(
        what=(f"this host is already held: {existing.get('owner','-')} took it at "
              f"{existing.get('started_at','-')} on machine "
              f"{existing.get('machine','-')} as pid {existing.get('pid','-')} running "
              f"{existing.get('verb','-')}, and that hold has never declared an ending "
              f"(reading taken at {now}). It is EITHER still running OR it was killed, and "
              f"nothing on this disk can tell you which -- so nothing on this disk is allowed "
              f"to decide. Check the process before you answer"),
        who_may="person who can see whether that run is alive",
        how=f"{verb} --root <host> --break-lock <who>",
        because=f"The hold is written in full at {rel}.",
    )


def guard(ctx, rel: str, *, verb: str, now: str, break_by: str = None) -> None:
    """A READ, taken before anything else this run does, and the earliest point at which a held
    host can be named as the CAUSE it is.

    It writes nothing, on purpose. A run that is going to be turned away must leave the host
    exactly as it found it, and a hold written by a run that never earned the right to write is
    itself a mutation of a host somebody else may be inside of. The authoritative check is still
    `take`, which re-reads the document at the moment it means to write: this is the report that
    arrives first, so that a host held by a dying installer is not described to its operator as a
    tree full of unaccounted paths -- which is the consequence, and not the cause.
    """
    existing = read(ctx, rel)
    if standing(existing) and not break_by:
        _refuse(existing, rel, verb, now)


def take(ctx, rel: str, *, run_id: str, verb: str, now: str, break_by: str = None) -> Hold:
    """Take the hold, or refuse at the door.

    `break_by` is the whole stale-lock mechanism: a NAME, typed by a person who has looked at the
    hold this run just described to them and decided it is dead. There is no other way past a
    standing hold, and there is deliberately no argument this function accepts that means
    *probably*."""
    existing = read(ctx, rel)
    if standing(existing) and not break_by:
        _refuse(existing, rel, verb, now)
    value = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "verb": verb,
        "owner": who(),
        "machine": platform.node(),
        "pid": os.getpid(),
        "started_at": now,
        "kit_version": ctx.manifest.version,
    }
    if break_by and standing(existing):
        #: Recorded at BOTH ends: here, so the hold says what it replaced, and in the journal,
        #: which outlives every hold. A break that left no trace is indistinguishable from a
        #: lock that was never taken.
        value["broke"] = {"by": break_by, "at": now, "previous": existing}
    elif break_by:
        value["broke"] = {"by": break_by, "at": now, "previous": None,
                          "note": "no hold was standing; nothing was broken"}
    from ephemeral import scope  # local: the plane is resolved where it is used, never cached
    workspace = scope(ctx)
    workspace.write_json(rel, value)
    return Hold(workspace, ctx.clock, rel, value)

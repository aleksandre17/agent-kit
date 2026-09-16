"""The hold one runtime takes on one host, so that two of them cannot write into it at once.

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
machine, which pid, which verb, which run, since when -- and a HUMAN breaks it by name. Age is
REPORTED because a person needs it to decide; it is never ACTED on, because a machine may not.

Releasing does not delete. A lock that vanished at the end of a run leaves a host that cannot say
whether it was ever held, and the acts of breaking one would vanish with it. The hold is CLOSED
instead -- rewritten once, in a `finally`, with its ending and its moment -- exactly as a run's
receipt is. A document with no ending is a hold that is still standing, and that is the only test
there is.

WHICH RUNS HOLD (ADR-007). Every verb that declares it MUTATES, and declares no SUBJECT other
than the tree `--root` names, holds it. The set is
READ from those declarations and never listed here. What such a verb does is identical in every
case: it is GUARDED on arrival (a pure read, so a held host is named as the cause before anything
else is said), and it TAKES the hold at the moment it becomes a writer -- never on arrival, because
a hold written by a run that is about to be refused is itself a mutation of the host it protects.
A write nested inside another verb's write (a render carried out by a move, an install carried out
by an upgrade) belongs to the same run and shares its one hold: a process holds a host once.

The document's SHAPE lives in the kit schema named by `SCHEMA`. This module writes through it and
reads through it, and declares no version of its own.
"""

from __future__ import annotations

import getpass
import importlib
import os
import platform
import uuid
import weakref

import doors
from errors import KitError

#: The kit schema that is the ONE home of this document's shape. The version a hold is written at
#: is read from it, so no docstring or constant here can become a second declaration of it.
SCHEMA = "hold"

#: The document's name inside the plane that holds observed state. It is the HOST's hold, not any
#: one verb's: every writer of the host takes the same one. The kit's vocabulary; the PLACE it
#: resolves to is the manifest's declaration and is never written here.
#: Named `init.lock` per the Part VI drawing (`runtime/init.lock`) -- ADR-007 named it `host.lock`
#: before the drawing existed; ADR-015 amendment 1 retires that name so the drawn tree has one lock
#: under one name, never two for one truth.
NAME = "init.lock"

#: The one field that answers "is this hold still standing". Its ABSENCE is the held state, which
#: is why the field is never written at open: a hold that declared its own ending in advance would
#: be a record certifying something that has not happened.
RELEASED_AT = "released_at"

#: The hold THIS PROCESS has taken, per run. A write nested inside another verb's write is the
#: same run: it must neither refuse its own holder nor take the host a second time.
_STANDING = weakref.WeakKeyDictionary()


class LockError(KitError):
    """A lock document exists and cannot be read as one, or this run was about to write one that
    is not one. Refused rather than overwritten: a hold nobody can read is still a hold somebody
    may be standing behind."""

    code = "KIT0010"


def holds(module) -> bool:
    """Whether a verb holds the host -- read from what the verb DECLARES and from nothing else:
    it mutates, and it declares no SUBJECT other than the tree `--root` names. A verb that writes
    somewhere else says where by declaring its subject, and this module never needs its name."""
    return bool(getattr(module, "MUTATES", False)) and not getattr(module, "SUBJECT", None)


def version(ctx) -> int:
    """The shape version this kit writes, as its schema declares it."""
    return ctx.manifest.version_of(SCHEMA)


def _honoured(ctx, rel: str, value: dict, moment: str) -> dict:
    errors = ctx.manifest.validate(value, SCHEMA)
    if errors:
        raise LockError(f"{rel} {moment} does not honour the kit schema {SCHEMA!r}, and a hold "
                        f"that is not a hold is not overwritten:\n  " + "\n  ".join(errors))
    return value


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
    return _honoured(ctx, rel, value, "as it stands on disk")


def standing(lock) -> bool:
    """A hold is standing while it has declared no ending. Nothing here looks at a clock."""
    return bool(lock) and not lock.get(RELEASED_AT)


class Hold:
    """One taken hold, carried by the run that took it, closed exactly once."""

    __slots__ = ("ctx", "workspace", "rel", "value")

    def __init__(self, ctx, workspace, rel: str, value: dict) -> None:
        self.ctx = ctx
        self.workspace = workspace
        self.rel = rel
        self.value = value

    @property
    def broke(self):
        """The hold this one superseded, where a human declared it broken -- so that the caller
        can put that declaration somewhere it will OUTLIVE this lock."""
        return self.value.get("broke")

    def release(self, code: int, message: str = None) -> None:
        self.value[RELEASED_AT] = self.ctx.clock.now()
        self.value["exit_code"] = code
        if message:
            self.value["ended_because"] = message
        try:
            self.workspace.write_json(
                self.rel, _honoured(self.ctx, self.rel, self.value, "as this run closes it"))
        finally:
            _STANDING.pop(self.ctx, None)


class Borrowed:
    """The hold as seen by a write NESTED inside the run that took it. It closes nothing: the run
    that took the hold is the one that ends it, exactly once."""

    __slots__ = ()
    broke = None

    def release(self, code: int, message: str = None) -> None:
        pass


def _refuse(existing, rel: str, verb: str, now: str) -> None:
    doors.refuse(
        what=(f"this host is already held: {existing.get('owner','-')} took it at "
              f"{existing.get('started_at','-')} on machine "
              f"{existing.get('machine','-')} as pid {existing.get('pid','-')} running "
              f"{existing.get('verb','-')} (run {existing.get('run_id','-')}, kit "
              f"{existing.get('kit_version','-')}), and that hold has never declared an ending "
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
        "schema_version": version(ctx),
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
    workspace.write_json(rel, _honoured(ctx, rel, value, "as this run takes it"))
    hold = Hold(ctx, workspace, rel, value)
    _STANDING[ctx] = hold
    return hold


# -- the one entrance every host-writing verb uses -------------------------------------------------
def _declared(args):
    """The verb THIS RUN is, as the entry point resolved it -- so a write nested inside another
    verb is held under the name of the run it belongs to, not the name of the step."""
    return importlib.import_module(args.verb)


def _where(ctx) -> str:
    from ephemeral import place  # local: the plane is resolved where it is used, never cached
    return place(ctx, NAME)


def arrive(ctx, args) -> None:
    """The guard, for any verb, decided by its declarations: a pure READ, first thing -- and
    nothing at all for a verb that does not hold the host, or for a run that already holds it."""
    if ctx in _STANDING or not holds(_declared(args)):
        return
    guard(ctx, _where(ctx), verb=args.verb, now=ctx.clock.now(),
          break_by=getattr(args, "break_lock", None))


def writer(ctx, args, run_id: str = None):
    """Called at the moment a run becomes a WRITER, and at no earlier one. Takes the hold -- or,
    for a write nested inside a run that already holds this host, borrows it. A verb that does not
    declare that it holds the host is handed nothing to release, never a hold it did not declare."""
    if ctx in _STANDING or not holds(_declared(args)):
        return Borrowed()
    return take(ctx, _where(ctx), run_id=run_id or uuid.uuid4().hex, verb=args.verb,
                now=ctx.clock.now(), break_by=getattr(args, "break_lock", None))


def held(ctx, args, work):
    """Carry out `work` -- the part of a verb that writes -- as the host's one writer, and close
    the hold in a `finally` with the run's own ending. A killed process never reaches the close,
    and its hold stands until a person breaks it by name. That is the mechanism working."""
    hold = writer(ctx, args)
    code, message = 1, None
    try:
        code = work()
        return code
    except KitError as refusal:
        code, message = refusal.exit_code, str(refusal)
        raise
    except BaseException as unforeseen:  # noqa: BLE001 -- re-raised; only the record is added
        message = f"{type(unforeseen).__name__}: {unforeseen}"
        raise
    finally:
        hold.release(code, message)

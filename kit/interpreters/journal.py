"""The init journal -- every phase written BEFORE it runs and again AFTER it concludes.

This is the L7-life mechanism applied to the INSIDE of a single run. A receipt says a run fired;
it cannot say how far it got, and "how far it got" is the only question worth asking about a host
that was being installed into when the power went out. So the same ordering is applied one level
down: the phase list is externalized the moment the run begins, each phase is stated as ENTERED
before a byte of its work happens, and stated again as concluded after. A process that is killed
never reaches the second write, so its journal says -- permanently -- which phase it was inside
and which phases it had never reached. That is the mechanism working.

Why this is not the run receipt, since it is plainly the same identity (Cardinal III, answered
rather than assumed):

  * a receipt is opened BY A CAPABILITY the host has already accepted. The run this journal exists
    for is the run that CREATES that acceptance -- at first contact there is no answers file, no
    enabled set and therefore, by the observation layer's own deliberate rule, no observer at all.
    A journal carried by that mechanism would be absent in exactly the case it was built for.
  * a receipt records ONE ending. A journal records a SEQUENCE, and is READ BACK by the next run.
  * a receipt is written into a space its capability declared it owns; a journal is written before
    anything is known about what this host owns.

What IS shared is shared, and not copied: the status vocabulary below is IMPORTED from the
observer that first declared it, because two homes for the word UNSET is the drift this whole
project exists against. (Its proper home is a module both sides import; the observer is where it
currently lives, and moving it is a separate slice -- named here rather than duplicated here.)

Two things this module refuses to decide. WHICH PHASES EXIST: they arrive as data, from the verb
that declares them, and nothing here reads, matches or branches on a phase's id. WHETHER A PHASE
MAY BE SKIPPED ON RESUME: this module reports what a prior run concluded and what it did not; it
never re-orders, never re-plans and never silently drops work. Resume here means the next run
starts knowing what the dead one had finished and says so out loud -- not that a machine quietly
decided some work no longer needs doing.
"""

from __future__ import annotations

import uuid

from errors import KitError

#: OpenTelemetry's span statuses, imported from their one declaration in this kit rather than
#: restated. UNSET is not "unknown": it is the declared state of something that has concluded
#: nothing yet -- which is what a phase that was interrupted will say forever.
from receipt import ERROR, OK, UNSET  # noqa: F401

#: The one word this kit adds, because OpenTelemetry has no need of it: a phase that was DECLARED
#: by the run and never entered. It is written at open, for every phase, so that a dead run's
#: journal distinguishes "never started" from "started and concluded nothing" -- and so that no
#: phase is ever represented by a silent blank.
PENDING = "PENDING"

#: The kit schema that is the ONE home of this document's shape. The version a journal is written
#: at is read from it; nothing here declares a second one.
SCHEMA = "journal"

#: The document's name inside the plane that holds observed state. The kit's own vocabulary; the
#: PLACE is resolved from the manifest's plane declaration, never written here.
NAME = "init.journal"


class JournalError(KitError):
    """A journal document exists and cannot be read as one, or this run was about to write one
    that is not one. Refused rather than overwritten: the record of a dead run is the only account
    of how far it got, and a run that replaced it would be destroying the evidence it came for."""

    code = "KIT0031"


def _honoured(ctx, rel: str, value, moment: str) -> dict:
    errors = ctx.manifest.validate(value, SCHEMA) if isinstance(value, dict) else ["not an object"]
    if errors:
        raise JournalError(f"{rel} {moment} does not honour the kit schema {SCHEMA!r}. It is not "
                           f"overwritten; move it aside by hand once it has been read:\n  "
                           + "\n  ".join(errors))
    return value


class Silent:
    """The journal of a run that writes nothing. A plan touches no byte, so it leaves no record
    and says so by being this -- rather than by leaving an empty document, which would read as a
    run that did nothing when it is a run that was never asked to do anything."""

    resumed_from = None

    def enter(self, phase_id: str) -> None:
        pass

    def conclude(self, phase_id: str, status: str = OK, message: str = None) -> None:
        pass

    def close(self, code: int, message: str = None) -> None:
        pass


class Journal:
    """One run's phase record, held open and rewritten at every transition.

    Every transition is FLUSHED. Batching the writes and saving them for the end would make this
    document exactly the thing it exists to refute: a record that proves nothing about a run which
    never reached the end.
    """

    __slots__ = ("ctx", "workspace", "clock", "rel", "value")

    def __init__(self, ctx, workspace, rel: str, value: dict) -> None:
        self.ctx = ctx
        self.workspace = workspace
        self.clock = ctx.clock
        self.rel = rel
        self.value = value

    # -- reading the dead ----------------------------------------------------------------------
    @staticmethod
    def interrupted(prior) -> bool:
        """A prior run was INTERRUPTED if its record declares no ending. A refusal is an ending;
        a failure is an ending; only a run that never came back leaves none."""
        return bool(prior) and not prior.get("ended_at")

    @staticmethod
    def resumption(prior) -> dict:
        """What the next run inherits from a dead one: which phase it was inside, what it had
        already concluded, and the whole record it is superseding -- carried, never discarded."""
        phases = prior.get("phases") or []
        return {
            "run_id": prior.get("run_id"),
            "started_at": prior.get("started_at"),
            "interrupted_in": [p["id"] for p in phases if p.get("status") == UNSET],
            "never_reached": [p["id"] for p in phases if p.get("status") == PENDING],
            "concluded": [p["id"] for p in phases if p.get("status") in (OK, ERROR)],
            "record": prior,
        }

    # -- the life of a run ----------------------------------------------------------------------
    @staticmethod
    def opened(ctx, rel: str, *, verb: str, phases, now: str, run_id: str = None,
               broke: dict = None, concluded: dict = None) -> "Journal":
        import hostlock
        from ephemeral import scope

        workspace = scope(ctx)
        prior = None
        if ctx.workspace.exists(rel):
            try:
                prior = ctx.workspace.read_json(rel)
            except ValueError as exc:
                raise JournalError(f"{rel} exists and is not readable as a journal -- {exc}. It "
                                   f"is not overwritten; move it aside by hand.") from exc
            _honoured(ctx, rel, prior, "as it stands on disk")
        value = {
            "schema_version": ctx.manifest.schema(SCHEMA)["properties"]["schema_version"]["const"],
            "run_id": run_id or uuid.uuid4().hex,
            "verb": verb,
            "status": UNSET,
            "started_at": now,
            "owner": hostlock.who(),
            "kit_version": ctx.manifest.version,
            "phases": [dict({"id": p["id"], "does": p["does"], "status": PENDING},
                             **(concluded or {}).get(p["id"], {})) for p in phases],
        }
        if Journal.interrupted(prior):
            value["resumed_from"] = Journal.resumption(prior)
        if broke:
            #: The other end of a broken hold. The lock itself is released and superseded; this
            #: document is what remains, so the declaration that broke a hold is recorded where it
            #: will outlive the hold it broke.
            value["broke_lock"] = broke
        workspace.write_json(rel, _honoured(ctx, rel, value, "as this run opens it"))
        return Journal(ctx, workspace, rel, value)

    @property
    def resumed_from(self):
        return self.value.get("resumed_from")

    def _phase(self, phase_id: str) -> dict:
        for phase in self.value["phases"]:
            if phase["id"] == phase_id:
                return phase
        raise KeyError(phase_id)

    def _flush(self) -> None:
        self.workspace.write_json(
            self.rel, _honoured(self.ctx, self.rel, self.value, "as this run rewrites it"))

    def enter(self, phase_id: str) -> None:
        """Stated BEFORE the work. This write is the entire guarantee and it is the one that
        cannot be added afterwards."""
        phase = self._phase(phase_id)
        phase["status"] = UNSET
        phase["started_at"] = self.clock.now()
        self._flush()

    def conclude(self, phase_id: str, status: str = OK, message: str = None) -> None:
        phase = self._phase(phase_id)
        phase["status"] = status
        phase["ended_at"] = self.clock.now()
        if message:
            phase["message"] = message
        self._flush()

    def close(self, code: int, message: str = None) -> None:
        """The end of the run, in the same act as its moment. Any phase still open at this point
        ended with the run: a refusal and a failure are both ENDINGS, and a phase left saying
        UNSET beside a run that declared an ending would be a contradiction nobody could resolve.
        Only a killed process leaves that state, and only because it never arrives here."""
        ended = self.clock.now()
        for phase in self.value["phases"]:
            if phase.get("status") == UNSET:
                phase["status"] = ERROR
                phase["ended_at"] = ended
                if message:
                    phase["message"] = message
        self.value["status"] = OK if code == 0 else ERROR
        self.value["ended_at"] = ended
        self.value["exit_code"] = code
        if message:
            self.value["status_message"] = message
        self._flush()

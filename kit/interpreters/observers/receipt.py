"""The record a run leaves behind: opened before the work, closed once when the work reports an end.

This is the LIFE half of observation and deliberately only that half. It records that a run
FIRED. It never records that the run HIT -- whether the work was any good is a question about a
host's own subject matter, judged against cases and standards the host owns, and nothing here has
an opinion about it.

The order is the entire mechanism, and it is worth stating plainly because it is the one thing
that cannot be added later: the record is written the moment the run begins, holding a status that
means *nothing has been concluded yet*, and rewritten exactly once when the run declares its end.
A record written only at the end proves nothing about a run that never reached the end -- and a
run that dies mid-way is precisely the case that needs recording, because everything it left on
disk reads exactly like the output of a run that finished.

So a process that is killed leaves its record holding the unset status forever. That is the record
working, not failing, and it is why closing happens in a `finally` and opening does not.

Its vocabulary is OpenTelemetry's wherever OpenTelemetry has a word -- a span carries a name, a
status of UNSET, OK or ERROR, and a status message. A collector is not built and not implied: we
wrap the field's vocabulary, we do not replace its tooling. Where this kit's own contract wins,
the schema says so rather than leaving it to be discovered.

Two things this module does not decide. WHICH runs get a record: that is the `when` of the
declaration that opened it. WHERE the record goes: that is the install the declaration names,
which already stated the path once when it declared that it owns it.
"""

from __future__ import annotations

import uuid

from errors import KitError

#: The shape version of the record this observer writes. It writes the document, so it names the
#: contract it writes to -- naming what you produce is a promise, not a policy.
SCHEMA_VERSION = 1

#: OpenTelemetry's span statuses, adopted rather than re-invented. UNSET is not "unknown": it is
#: the declared state of a run that has concluded nothing yet, which is exactly what a run that
#: has only just started has done, and exactly what a run that died will have done forever.
UNSET, OK, ERROR = "UNSET", "OK", "ERROR"


class ReceiptError(KitError):
    """A declaration asked for a record to be written into a readable this capability does not
    declare. Refused rather than defaulted: a record written somewhere nobody reads is worse than
    no record, because its absence from the report reads as nothing having happened."""

    code = "KIT0014"


def _space(capability, watch):
    """The install that owns the place these records live. The path is read from the declaration
    that already states it, never held here: a path in an interpreter is a second home for a truth
    a capability states, and it is the home a host cannot change."""
    wanted = watch["params"]["into"]
    for item in capability.installs:
        if item.get("reads_as") == wanted:
            return item
    raise ReceiptError(
        f"capability {capability.id!r} declares that a run's record is written into "
        f"{wanted!r}, which it does not declare readable; the names it does declare are "
        f"{sorted(i['reads_as'] for i in capability.installs if i.get('reads_as'))}"
    )


class Receipt:
    """One run's record, held open. It carries the workspace it may write through, so that the
    close is bounded by exactly the scope the opening was."""

    __slots__ = ("workspace", "clock", "rel", "value", "in_flight")

    def __init__(self, workspace, clock, rel: str, value: dict, in_flight: set) -> None:
        self.workspace = workspace
        self.clock = clock
        self.rel = rel
        self.value = value
        self.in_flight = in_flight

    @staticmethod
    def opened(ctx, capability, watch, asked) -> "Receipt":
        item = _space(capability, watch)
        identity = uuid.uuid4().hex
        value = {
            "schema_version": SCHEMA_VERSION,
            "id": identity,
            "name": asked["verb"],
            "status": UNSET,
            "started_at": ctx.clock.now(),
            "kit_version": ctx.manifest.version,
        }
        #: Written through the declaring capability's own scope, like every other write in the
        #: kit. An observer that wrote unscoped would be the one write in the design that nobody
        #: granted -- and it would be the write that happens on every run.
        workspace = ctx.workspace.scoped(capability.targets())
        rel = f"{item['target'].rstrip('/')}/{identity}.json"
        workspace.write_json(rel, value)
        ctx.in_flight.add(identity)
        return Receipt(workspace, ctx.clock, rel, value, ctx.in_flight)

    def close(self, code: int, message: str = None) -> None:
        """The end, stated in the same act as its moment. A status without a moment goes on
        certifying -- or accusing -- for as long as it sits there, and cannot be contradicted.

        A refusal is an ENDING. A run that was turned away finished, said why, and is not a run
        that vanished; a record unable to tell those apart would be the one lie this exists to
        prevent. The exit code is recorded BESIDE the status and never in place of it, because an
        exit code is not a result.
        """
        self.value["status"] = OK if code == 0 else ERROR
        self.value["ended_at"] = self.clock.now()
        self.value["exit_code"] = code
        if message:
            self.value["status_message"] = message
        self.workspace.write_json(self.rel, self.value)
        self.in_flight.discard(self.value["id"])


#: What this module PROVIDES: one way of observing a run. A new way is another class and another
#: row -- here or in a file beside this one -- and nothing that dispatches to it is ever edited.
KINDS = {"run-receipt": Receipt}

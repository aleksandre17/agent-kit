"""The door -- the one mechanism in this kit by which a machine hands a decision to a human.

There are two places a human must stand: the install's answer (nobody may be installed into by a
machine that also approved itself) and a lifecycle transition the declaration marks as a door
(`shaped -> bet`: work is not accepted because a machine had capacity). They are the SAME
mechanism and they live here once. What differs between them is only the SUBJECT -- an answers
file in one case, a card in the other -- and the subject is passed in, never known here.

The vocabulary is declared here and nowhere else: the two statuses, the two fields that record an
acceptance, and the exit code that means *waiting for a human* rather than *broken*. A second
home for any of them is how one half of a system goes on saying `accepted` while the other reads
`approved` and both remain internally correct (Cardinal III).
"""

from __future__ import annotations

from errors import PendingApproval

#: The two statuses a subject standing at a door may hold.
DRAFT = "draft"
ACCEPTED = "accepted"

#: The two fields that record an acceptance. Written by `record`, read by everyone.
SIGNED_BY = "signed_by"
SIGNED_AT = "signed_at"


def record(who: str, when: str) -> dict:
    """An acceptance: a NAME and a MOMENT. Nothing else is a record -- a status with no name
    cannot be contradicted, and a name with no moment cannot be placed against anything."""
    return {SIGNED_BY: who, SIGNED_AT: when}


def walked(subject: dict) -> bool:
    return subject.get("status") == ACCEPTED


def refuse(what: str, who_may: str, how: str, because: str = "") -> None:
    """A door that was not walked through. Not a failure: a DECLARED STATE, carrying its own exit
    code, so an operator can tell a stalled thing from a broken one."""
    raise PendingApproval(
        f"{what} — this is a DOOR: only the {who_may} may open it, and no machine ever may."
        + (f" {because}" if because else "")
        + f" Walk it with: {how}"
    )

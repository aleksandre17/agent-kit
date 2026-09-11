"""Observation -- opening and closing whatever a capability declared should watch a run.

This module knows no observer, no record and no plane. It knows that a capability may DECLARE
that it observes runs, that each such declaration names a KIND and the condition under which it
applies, and that an observer is opened before the work and closed after it. Which kinds exist is
discovered from `observers/`, exactly as verbs are discovered from `verbs/` and gate kinds from
`gates/`: a new way of observing a run is a FILE plus a row in a declaration, never an edit here
and never an edit to the CLI.

Two things this module refuses to decide, both of which look like they belong here:

  * **Which runs are worth observing.** That is a condition in the declaration, matched against
    what the run already is -- what it was asked to do, whether it writes, whether this host has
    accepted its kit. A rule spelled here would be the framework holding an opinion about a host's
    runs in the one place a host cannot reach.
  * **What a host's own truth means.** If the answers file is missing or unreadable, nothing is
    observed and nothing is said about it, because the verb that is about to run will report that
    same fact as the CAUSE it is. A layer of judgement added above another must not answer first;
    this project has paid for that twice, and this is the layer that would most easily do it a
    third time.

And the ordering is the point of the whole slice: an observer is opened BEFORE the verb runs, so
that a run which never comes back has already said that it started. A record written only at the
end proves nothing about a run that never reached the end.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import predicate
from errors import KitError

#: The field by which a capability declares what watches its runs. Schema vocabulary, one home:
#: the capability schema declares the shape, this reads it, and no observer is named in either.
DECLARED = "observes"

OBSERVERS = Path(__file__).resolve().parent / "observers"


class ObservationError(KitError):
    """A declaration named an observer kind no discovered module provides, or two modules claim
    one kind -- which is a name resolving to two meanings, refused rather than ordered."""

    code = "KIT0013"


def registry() -> dict:
    kinds: dict = {}
    owners: dict = {}
    for path in sorted(OBSERVERS.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = importlib.import_module(path.stem)
        for kind, observer in getattr(module, "KINDS", {}).items():
            if kind in kinds:
                raise ObservationError(
                    f"observer kind {kind!r} is provided by both {owners[kind]!r} and "
                    f"{path.stem!r}; a name that resolves to two things is not a name"
                )
            owners[kind] = path.stem
            kinds[kind] = observer
    return kinds


def reading_of(ctx, args, module, verb: str) -> dict:
    """What this run IS, as a flat reading a declaration can be matched against. Every field is
    something the run already knows about itself before it does anything: what was asked for, what
    the verb declares about its own effects, and what this host has answered so far."""
    try:
        answers = ctx.host_answers(required=False)
    except KitError:
        answers = None  # not this layer's to report; the verb names the cause in a moment
    return {
        "verb": verb,
        "mutates": bool(getattr(module, "MUTATES", False)),
        "plan": bool(getattr(args, "plan", False)),
        "approving": bool(getattr(args, "approve", None)),
        "host_status": (answers or {}).get("status"),
    }


def opened(ctx, args, module, verb: str) -> list:
    """Every observation the enabled capabilities declared for a run like this one, opened.

    A host that has not answered yet is watched by nothing, and that is not an oversight: an
    observation is declared BY a capability, a capability is enabled only by the host's own
    answer, and writing a record on a host that has approved nothing would be the kit taking a
    write it was never granted.
    """
    try:
        capabilities = ctx.enabled_capabilities() if ctx.host_answers(required=False) else []
    except KitError:
        return []
    asked = reading_of(ctx, args, module, verb)
    kinds = registry()
    watching = []
    for capability in capabilities:
        for watch in getattr(capability, DECLARED):
            if not predicate.matches(watch["when"], asked):
                continue
            if watch["kind"] not in kinds:
                raise ObservationError(
                    f"capability {capability.id!r} declares observer kind {watch['kind']!r}; "
                    f"the provided kinds are {sorted(kinds)}"
                )
            watching.append(kinds[watch["kind"]].opened(ctx, capability, watch, asked))
    return watching


def closed(watching, code: int, message: str = None) -> None:
    """The end of the run, handed to every observer that saw its beginning. This is where a
    refusal is as much an ending as a success: a run that was turned away FINISHED, and a record
    that could not tell that from a run that vanished would be the one lie this slice exists to
    prevent."""
    for observer in watching:
        observer.close(code, message)

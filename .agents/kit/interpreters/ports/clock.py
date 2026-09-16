"""Clock port -- so every reading can state when it was taken.

A reading that does not carry its moment cannot be contradicted, only believed. The port exists so
the moment is injected, never reached for: a verb that calls the wall clock directly is a verb that
cannot be replayed, and an acceptance test needs replay.
"""

from __future__ import annotations

from datetime import datetime, timezone


class Clock:
    """The real clock. UTC, second resolution, ISO-8601 with an explicit offset."""

    def now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class FixedClock:
    """A clock that always reports one stated moment. For tests and for replay."""

    def __init__(self, moment: str) -> None:
        self._moment = moment

    def now(self) -> str:
        return self._moment


#: The environment variable that holds time still. Named after the mechanism it copies:
#: Reproducible Builds' `SOURCE_DATE_EPOCH`, where a build that must be replayable is handed its
#: moment rather than reaching for one. A time-dependent rule that can only be tested by WAITING
#: is a rule nobody tests; a rule whose clock is injected at the boundary is tested in a
#: millisecond, and the same injection is what makes a run replayable a year later.
MOMENT_VARIABLE = "KIT_NOW"


def from_environment(environment) -> "Clock":
    """The clock, MEASURED at the boundary like the console encoding and the path separator --
    not reached for in the middle of a verb. If the environment states the moment, that is the
    moment; otherwise the wall clock, which is what a real host has."""
    stated = environment.get(MOMENT_VARIABLE)
    return FixedClock(stated) if stated else Clock()

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

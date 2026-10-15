"""A gate is trusted only after it has been seen to bite (ADR-022 decision 8).

A gate that has never failed proves nothing about itself: it may hold a tree with nothing to catch, or
be unable to catch anything at all, and the two read identically. The prior system paid for that twice
-- a parity gate green over an empty set, a law gate that printed its violation and exited
non-blocking -- and its rule became: a gate ships only after it was seen RED on a real defect.

So a gate module may publish, beside its `KINDS`, the CALIBRATION of each kind: a function that builds
a SPECIMEN the kind must flag and a LOOKALIKE it must admit, through a host fixture it is handed, and
returns both findings. The kit's own suite holds every calibrated kind to it. A kind with no
calibration is not refused -- it is COUNTED: `uncalibrated_gate_kinds` is a measure a host budgets
through its corpus map, so the number can only fall (ADR-019 decision 9). The kit ships the count and
never a ceiling.
"""

from __future__ import annotations

import corpus
import gatekinds

UNCALIBRATED = "uncalibrated_gate_kinds"


def uncalibrated() -> list:
    """Every registered gate kind that publishes no calibration."""
    calibrated = gatekinds.registry("CALIBRATIONS")
    return sorted(set(gatekinds.registry()) - set(calibrated))


def _uncalibrated(ctx, params) -> "int | None":
    """`None` where this host maps no corpus: a budget lives in a corpus map, and a count answered
    where nothing was read would be a number nobody asked for (the measures' shared rule)."""
    if corpus.read(ctx, params).nothing_read():
        return None
    return len(uncalibrated())


KINDS = {}

#: What this module can be held to a BUDGET on (ADR-019 decision 9).
MEASURES = {UNCALIBRATED: _uncalibrated}

"""The tree audited -- `check`'s reading of what `audit` finds (ADR-024 decision 20).

Every calibrated edit gate in force runs over the full text of every tracked file it reaches; a
violation standing in the tree that no acknowledgement covers (or whose acknowledgement's `until` has
passed) fails this gate. Whether that failure fails `check` is the gate's STANCE: it ships `observe`,
so a host sees its counts on every check and raises it to `enforce` by its own declaration. The
counts are reported on every check, pass or fail; `audit` names each finding.
"""

from __future__ import annotations

import standing

KIND = "tree-audited"


def _failures(found) -> list:
    if not (found.open or found.expired):
        return []
    return [f"{found.counts()} -- run `audit` for each path:line and gate"]


def _held(ctx, params):
    try:
        return _failures(standing.audit(ctx))
    except standing.AuditError as exc:
        return [f"the tree could not be audited -- {exc}"]


def _report(ctx, params) -> str:
    try:
        return "audit: " + standing.audit(ctx).counts()
    except standing.AuditError:
        return "audit: not taken (named above)"


def _calibrate(host):
    """A violation standing in a file is flagged; the same violation acknowledged is admitted."""
    gate = {"id": "g", "paths": "^src/", "forbids": "forbidden", "because": "b"}
    texts = [("src/a.txt", "fine\nforbidden here\n")]
    flagged = standing.judge(texts, [gate], {}, "2026-01-01")
    admitted = standing.judge(texts, [gate], {("g", "src/a.txt"): {"gate": "g", "path": "src/a.txt",
                                                                  "tracking": "T-1"}}, "2026-01-01")
    return _failures(flagged), _failures(admitted)


KINDS = {KIND: _held}
CALIBRATIONS = {KIND: _calibrate}
#: A line `check` prints under this gate whatever its verdict: the counts are the reading.
REPORTS = {KIND: _report}

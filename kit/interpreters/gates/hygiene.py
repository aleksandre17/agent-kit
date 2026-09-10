"""Gate kinds for RESIDENCE -- a genre that has no home, named where it sits.

This module knows no genre. It knows the SHAPE of a residence document -- a list of rules, each
carrying one pattern and its own calibration -- and nothing about what any of them say. Which
documents it reads arrives as params; what those documents contain is the declaration's business.

It reports and never removes. That is the whole posture of the capability and it is enforced here
by omission: there is no write, no port that could write, and no branch that could reach one. A
deletion is a decision, a decision has an author, and no machine may be that author.

And it refuses to scan on the word of an uncalibrated sensor. Every rule states one path it MUST
see and one lookalike it MUST tolerate; both are checked before a single file is read, and a rule
that fails either is itself the failure. A detector believed before it was measured is how a
system acquires confident readings of a world it was never pointed at.
"""

from __future__ import annotations

import re

import declared
from errors import KitError

#: The field by which a residence document carries its rules. Schema vocabulary, one home: the
#: schema declares the shape, this reads it, and no genre is named in either.
RULES = "genres"


class ResidenceError(KitError):
    """A residence rule carries a pattern that is not a pattern. Where the RULES come from -- and
    the two ways that resolution can be ambiguous -- is not this module's question: it is the same
    question for every sensor, so it is asked once, in `declared`."""


def _compiled(rule):
    try:
        return re.compile(rule["pattern"])
    except re.error as exc:
        raise ResidenceError(
            f"residence rule {rule['id']!r} declares {rule['pattern']!r}, which is not a "
            f"pattern -- {exc}"
        ) from exc


def _calibration(rules: list) -> list:
    """What the sensor can prove about itself, before it is pointed at anything."""
    failures = []
    for rule in rules:
        pattern = _compiled(rule)
        if not pattern.search(rule["proves"]):
            failures.append(
                f"{rule['id']}: UNCALIBRATED -- its pattern does not see {rule['proves']!r}, the "
                f"very thing it declares it catches. A sensor that cannot prove what it sees is "
                f"not evidence, and nothing was scanned on its word."
            )
        if pattern.search(rule["admits"]):
            failures.append(
                f"{rule['id']}: UNCALIBRATED -- its pattern also catches {rule['admits']!r}, which "
                f"it declares legitimate. A rule with no measured edge eventually names "
                f"everything, and nothing was scanned on its word."
            )
    return failures


def _residence_declared(ctx, params):
    rules = declared.rules(ctx, params["sources"], RULES)
    uncalibrated = _calibration(rules)
    if uncalibrated:
        return uncalibrated
    failures = []
    for rel in ctx.workspace.files_under(params["root"]):
        for rule in rules:
            if _compiled(rule).search(rel):
                failures.append(
                    f"{rel}: {rule['id']} -- {rule['because']} It belongs {rule['instead']} "
                    f"Nothing was removed: this names a resident, and the move is yours."
                )
    return failures


KINDS = {
    "residence-declared": _residence_declared,
}

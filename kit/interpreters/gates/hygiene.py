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

import collection
from errors import KitError

#: The field by which a residence document carries its rules. Schema vocabulary, one home: the
#: schema declares the shape, this reads it, and no genre is named in either.
RULES = "genres"


class ResidenceError(KitError):
    """A declared source of residence rules is missing, claims a name twice, or carries a pattern
    that is not a pattern."""


def _sources(ctx, names: list) -> dict:
    """The named residence documents, wherever they were declared: SHIPPED by a capability, or
    AUTHORED by the host in a path a capability declared readable. Both arrive by name, and a name
    that resolves to two documents is refused rather than ordered -- the loser would go on reading
    as true while the value came from somewhere else."""
    found: dict = {}
    owners: dict = {}

    def claim(name, value, owner):
        if name in found:
            raise ResidenceError(
                f"capabilities {owners[name]!r} and {owner!r} both declare residence rules named "
                f"{name!r}; a name that resolves to two things is not a name"
            )
        owners[name] = owner
        found[name] = value

    for capability in ctx.enabled_capabilities():
        for identity, document in capability.documents.items():
            if identity in names:
                claim(identity, document, capability.id)
        for item in capability.installs:
            if item.get("reads_as") in names:
                claim(item["reads_as"], collection.read(ctx, item).value, capability.id)

    missing = [name for name in names if name not in found]
    if missing:
        raise ResidenceError(
            f"this gate was declared over residence rules named {missing}, which no enabled "
            f"capability ships or declares readable; a source that cannot be found is not an "
            f"empty source"
        )
    return found


def _rules(ctx, params) -> list:
    found = _sources(ctx, params["sources"])
    rules, owners = [], {}
    for name in params["sources"]:
        for rule in found[name][RULES]:
            if rule["id"] in owners:
                raise ResidenceError(
                    f"residence rule {rule['id']!r} is declared by both {owners[rule['id']]!r} and "
                    f"{name!r}; two rules under one name is two homes for one judgement"
                )
            owners[rule["id"]] = name
            rules.append(rule)
    return rules


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
    rules = _rules(ctx, params)
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

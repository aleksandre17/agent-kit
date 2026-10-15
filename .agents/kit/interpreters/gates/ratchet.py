"""The BUDGET RATCHET -- the one gate over this corpus that turns a count into a verdict (ADR-019 9).

Every other gate here REPORTS. This one refuses, and it ships at `enforce` on the day it arrives,
which is the opposite order from the substantive gates beside it: they start at `observe` because
a corpus reaches two thousand documents before anything asks one of them what it is, and a gate
that failed on that legal state would be switched off within a day. The ratchet starts enforcing
because it CANNOT fail on the first run -- the first run compares a number the host just wrote with
itself, and with a measurement that same number was taken from. Nothing is red on day one; nothing
can get worse after it. That asymmetry is the adoption mechanism and not a nicety of sequencing.

**What a budget is.** A row of the host's corpus map naming a MEASURE the kit publishes, the
CEILING this host declares for it, and the date the number was taken. Not a target, not a deadline
and not a ratio: a ratio improves when its denominator grows, and a corpus can improve by acquiring
documents. The measures themselves are declared by the gate modules that already own the readings
they come from, discovered exactly as gate kinds are -- so a new budgetable fact about this corpus
is a row in the module that can measure it, never an edit here (Cardinals II and IV).

**Where the PREVIOUS ACCEPTED STATE is read, and why there.** From `HEAD`, through git, and never
from the working tree. A ratchet compares what is declared now with what was last ACCEPTED, and in
this repository an edit in the tree is not accepted by anybody: reading the previous value from a
file on disk would let the very change under judgement supply its own baseline, and the gate would
approve every raise it was shown. HEAD is the nearest thing to an accepted state a gate standing at
an edit can measure -- it is what review and CI both stand on. It costs this gate one dependency,
which is declared rather than assumed: where there is no git, no HEAD, or no map in HEAD, the gate
says so in those words and applies the half of its verdict that needs no history (Cardinal VII --
the boundary is measured, never assumed; Cardinal V -- an absence is declared, never a silent pass).

**What it refuses, and what it will not pretend to judge.** A ceiling raised above the accepted
one; a budget row that was accepted and is now gone, which is a raise to infinity written as a
deletion; and a measured count standing above the ceiling that was supposed to cap it. It refuses
nothing else. A first-ever budget row is its own baseline and is PRINTED as one, because a host
that has just begun measuring has done the thing this gate exists to encourage.

**The terminal value, and why this module answers for it.** A ceiling can fall until it is nothing
left to spend, and at that value the host has undertaken that the count it caps does not exist here
at all. Which budgets stand there is a reading of the same rows, from the same map, located the
same way -- so it is answered HERE, published for the one discovery that already finds everything
else this module publishes, and never located a second time by whoever needs it. What that fact
then COSTS is no business of this gate: this module reports an undertaking, and what a judgement's
failure does to a run is settled where every other stance is (ADR-006), out of declarations this
gate neither reads nor owns.
"""

from __future__ import annotations

import json

import corpus
import accepted as accepted_state
import gatekinds
from errors import KitError

#: The gate kind this module judges, and the corpus map's own budget field names (schema
#: `corpus-map`). `MEASURE` names a published measure; no measure's name is spelled here, because
#: the instant an interpreter knows which counts exist, a host that budgets a different one needs
#: the framework's permission to be judged.
KIND = "budget-ratchet"
BUDGETS, MEASURE, CEILING, MEASURED = "budgets", "measures", "ceiling", "measured"

#: The value below which a ceiling cannot fall and at which it has nothing left to concede. It is
#: arithmetic and not a threshold: the kit ships no number that decides anything (ADR-001 point 4),
#: and this one is the end of the scale the host chose to count on, not an opinion about where a
#: host should be.
TERMINAL = 0

#: The registry entry a gate module publishes its MEASURES under -- read by the one discovery that
#: already finds gate kinds, so which module can measure what is answered in a single place.
REGISTRY = "MEASURES"


class RatchetError(KitError):
    """A budget was declared over a measure nothing in this kit can take, so the row can never be
    compared with anything and the gate would pass it forever."""

    code = "KIT0055"


# -- the previous accepted state ----------------------------------------------------------------
def _accepted(ctx, space: str) -> tuple:
    """`(the budgets of the previous accepted state, None)` or `(None, the absence in its own
    words)`.

    The whole MAP SPACE is read at HEAD, not the files that happen to be in the tree now: a budget
    whose file was deleted or renamed since the last accepted state is exactly the row a ratchet
    must still see, and enumerating the tree's own files would lose it in the one case that matters.
    """
    root = ctx.workspace.path(".")
    listing, why = accepted_state.listing(root, space)
    if listing is None:
        return None, (
            f"THERE IS NO PREVIOUS ACCEPTED STATE FOR {space!r}: {why}. Every budget below is read "
            f"as FIRST DECLARED -- a first row is its own baseline, and a first commit, a fresh "
            f"clone and a host that is no repository at all are states this gate is met in "
            f"legitimately. No row is refused for its DIRECTION here, because there is no direction "
            f"to read; the measured half of the verdict needs no history and is applied in full."
        )

    budgets: dict = {}
    for name in sorted(filter(None, listing.split("\n"))):
        if not name.endswith(".json"):
            continue
        rel = f"{space}/{name}"
        text, why = accepted_state.text(root, rel)
        if text is None:
            return None, (
                f"THE PREVIOUS ACCEPTED STATE COULD NOT BE READ: {rel} is in HEAD and its content "
                f"is not -- {why}. Nothing below is compared with a direction, because a baseline "
                f"read in part is a baseline that passes whatever it failed to load."
            )
        try:
            document = json.loads(text)
        except ValueError as exc:
            return None, (
                f"THE PREVIOUS ACCEPTED STATE COULD NOT BE READ: {rel} at HEAD is not readable as "
                f"JSON -- {exc}. It is named rather than skipped: a baseline that failed to parse "
                f"is not a baseline of zero budgets, and treating it as one would let the next edit "
                f"raise anything it liked."
            )
        for row in document.get(BUDGETS, []):
            budgets.setdefault(row[MEASURE], (rel, row))
    return budgets, None


# -- what the tree declares now -------------------------------------------------------------------
def _declared(records: list) -> tuple:
    """The budget rows of the map as it stands, by measure -- and the one contradiction a merged
    map can contain: two files capping one measure. Two ceilings for one count are not a tie; they
    are a corpus whose limit depends on which file a reader opened first (Cardinal III)."""
    rows: dict = {}
    findings: list = []
    for rel, document in records:
        for row in document.get(BUDGETS, []):
            name = row[MEASURE]
            if name in rows:
                first, seen = rows[name]
                findings.append(
                    f"{rel}: it declares a budget for {name!r} at {row[CEILING]}, and {first} "
                    f"already caps the same measure at {seen[CEILING]}. One measure has one "
                    f"ceiling: two of them leave every later reading free to quote whichever "
                    f"number it was standing nearest, and the ratchet free to compare against "
                    f"either. Delete one."
                )
                continue
            rows[name] = (rel, row)
    return rows, findings


def _ratchet(ctx, params) -> list:
    """Every declared budget, held against the previous accepted state and against the tree.

    An absence is PRINTED and never returned. A host that has budgeted nothing has not failed at
    anything -- it has not started -- and a gate that went red there would be red on every fresh
    install of the capability that ships it (ADR-019 decision 2, ADR-006).
    """
    space, records = corpus.declaration(ctx, params)
    rows, findings = _declared(records)
    if not rows:
        # The accepted state is still read. A host that declares no budget TODAY may have declared
        # one yesterday, and deleting the last row -- or the whole map -- is the one evasion that
        # would otherwise walk straight through the absence branch of this gate.
        accepted, absent = _accepted(ctx, space)
        gone = _deletions(rows, accepted)
        print(f"        {_nothing_budgeted(space, records, gone)}")
        if absent:
            print(f"        {absent}")
        return findings + gone

    measures = gatekinds.registry(REGISTRY)
    for name in sorted(rows):
        if name not in measures:
            rel, _row = rows[name]
            raise RatchetError(
                f"{rel}: a budget is declared for {name!r}, and no module of this kit publishes a "
                f"measure by that name; the measures published are {sorted(measures)}. It is "
                f"refused rather than skipped: a ceiling over a count nobody can take is a row that "
                f"passes this gate on every run for the rest of its life, and reads exactly like a "
                f"budget that is being honoured (Cardinal V). Name a published measure, or delete "
                f"the row."
            )

    accepted, absent = _accepted(ctx, space)
    against = ("no previous accepted state" if accepted is None else
               f"{len(accepted)} budget row(s) in the previous accepted state (HEAD)")
    print(
        f"        READ {len(rows)} budget row(s) over {len(records)} corpus-map file(s), against "
        f"{against}. A budget may be LOWERED in an ordinary edit and may never be raised; each one "
        f"is stated below with the count it caps, measured now."
    )
    if absent:
        print(f"        {absent}")

    for name in sorted(rows):
        rel, row = rows[name]
        findings.extend(_verdict(ctx, params, measures, accepted, name, rel, row))
    findings.extend(_deletions(rows, accepted))
    return findings


def _verdict(ctx, params, measures, accepted, name, rel, row) -> list:
    """One budget row: its direction since the accepted state, and the count it claims to cap."""
    ceiling = row[CEILING]
    taken = measures[name](ctx, params)
    before = None if accepted is None else accepted.get(name)

    stood = "no baseline" if accepted is None else (
        f"previously {before[1][CEILING]}" if before else "first declared here"
    )
    reads = "not measurable on this host" if taken is None else f"measures {taken}"
    print(f"          BUDGET {name}: ceiling {ceiling} (taken {row[MEASURED]}), {stood}, {reads}.")

    findings = []
    if before is not None and ceiling > before[1][CEILING]:
        findings.append(
            f"{rel}: the budget for {name!r} is raised from {before[1][CEILING]} to {ceiling}. A "
            f"budget falls or it stands still; raising one is the single thing this gate refuses "
            f"with no override, because a ceiling that can move up is not a ceiling and the quality "
            f"it caps is then free to degrade one accepted edit at a time. Put the ceiling back to "
            f"{before[1][CEILING]} or below and bring the corpus under it; a raise is settled "
            f"where a person decides it, and never by this row."
        )
    if taken is not None and taken > ceiling:
        findings.append(
            f"{rel}: {name!r} measures {taken} against a declared ceiling of {ceiling}, taken "
            f"{row[MEASURED]}. The corpus is over its own budget: either the work that raised it is "
            f"the thing to undo, or the number in this row was already out of date when it was "
            f"written. Lowering the ceiling will not answer this one -- the measurement is what it "
            f"is, and this is the refusal that makes a budget a cap rather than a wish."
        )
    return findings


def _deletions(rows: dict, accepted) -> list:
    if accepted is None:
        return []
    findings = []
    for name in sorted(accepted):
        if name in rows:
            continue
        rel, row = accepted[name]
        findings.append(
            f"{rel}: the budget for {name!r}, accepted at {row[CEILING]}, is no longer declared "
            f"anywhere in this map. A deleted budget is a raise to infinity written as an absence: "
            f"it reads, to every later run, exactly like a measure this host never undertook to "
            f"hold. A budget is retired by reaching zero and maturing its gate (ADR-006), never by "
            f"being removed from the row that carried it."
        )
    return findings


def _nothing_budgeted(space: str, records: list, gone: list) -> str:
    """The honest absence, in this gate's own words. It is NOT the corpus reading's sentence: the
    subject here is what the host undertook to hold, and a gate that borrowed the reading's absence
    would report on documents it never opened.

    An absence that follows a set of accepted budgets is NOT green and does not say it is: the
    sentence a reader is shown is the one that matches the verdict being returned beside it, or
    this gate would be reporting a clean corpus in the same breath as it refused one (Cardinal V).
    """
    if gone:
        return (
            f"NOTHING IS BUDGETED IN {space!r} AND SOMETHING WAS: {len(gone)} budget row(s) stood "
            f"in the previous accepted state and not one is declared now. That is not an absence "
            f"to report -- it is the refusal below, once for each row, because a budget that "
            f"disappears takes with it every count it was holding."
        )
    if not records:
        return (
            f"NOTHING WAS RATCHETED: this host declares no corpus map in {space!r}, so it has "
            f"budgeted nothing and nothing was compared. That is a legal state and it is green. "
            f"What was NOT judged: every count this kit can take. A budget is a number a human "
            f"writes about their own corpus; until one exists there is nothing to hold anyone to."
        )
    return (
        f"NOTHING WAS RATCHETED: {len(records)} corpus-map file(s) are declared in {space!r} and "
        f"not one of them carries a budget row, so no count was compared with a ceiling and none "
        f"was compared with the previous accepted state. Green, and not a corpus that was found "
        f"within its budgets."
    )


def _exhausted(ctx, params) -> dict:
    """Every measure this host has undertaken at the terminal value, and the file it wrote it in.

    A DECLARATION is read and NO count is taken. The two are not interchangeable and the difference
    is the whole safety of this answer: a ceiling is what the host undertook, a measurement is what
    the world happens to hold this minute, and a measure that cannot be taken answers `None` rather
    than nothing-is-wrong. An undertaking read from the world would therefore lapse on the day the
    world became unreadable -- quietly, and on a green surface. Read from the row, it stands until
    the host restates it, and the only restatement this gate will accept is a lowering.

    The previous accepted state is not consulted either, and deliberately: what a host undertakes
    TODAY is what binds it today. HEAD is this gate's answer to *which direction did this move*,
    which is a different question and stays where it is asked.
    """
    _space, records = corpus.declaration(ctx, params)
    rows, _findings = _declared(records)
    return {name: rel for name, (rel, row) in rows.items() if row[CEILING] <= TERMINAL}


#: What this module PROVIDES. One kind, and no measure of its own: what can be budgeted is
#: published by the modules that already read it, and arrives here through the same discovery that
#: finds a gate kind.
KINDS = {KIND: _ratchet}

#: What this module can tell a reader about the host's UNDERTAKINGS, keyed by the kind of declared
#: row that says where they live -- so the answer is reached the way every gate is reached, from a
#: declaration, and a host that has declared no such row is asked nothing. Published here because
#: this is where those rows are already read; a second reader of them is the drift Cardinal III
#: forbids, and it would go on agreeing with this one until the day one of the two was fixed.
EXHAUSTED = {KIND: _exhausted}

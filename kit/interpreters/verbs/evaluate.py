"""evaluate -- open a judgement for every pair that needs one, and state the measure. No verdict.

This verb judges nothing. It cannot: a good answer is a property of a domain, and this framework
has never met a domain. What it does is the one thing a framework CAN do honestly about quality --
it makes the absence of judgement countable.

An absence cannot be counted. A blank can. So for every pair of a case and a rubric the host said
must judge it, this verb opens a judgement holding `verdict: UNJUDGED` and the moment it was
opened, and leaves the judging to whatever the host trusts to judge. `never judged` stops being a
silence and becomes a record with a date on it, which is the only form in which anyone has ever
chased one.

The order is a run receipt's order, and the reason is the same: the record is written BEFORE the
judging, so that a judging which never happens is still visible afterwards. A surface built the
other way round -- one that shows the verdicts it has -- reports that everything is fine on a host
where nothing has ever been read, and that is the exact lie this project exists to prevent.

Three things this verb refuses to decide, all of which would look at home here:

  * **What is worth judging.** The cases are the host's, in a document seeded empty.
  * **What a good answer is.** The rubrics are the host's, and no criterion of any kind ships.
  * **How much is enough.** There is no threshold and no coverage number, because a number would
    have to come from somewhere and there is nowhere for it to come from. The measure is stated;
    what to do about it is a decision with an author.

It re-opens nothing: a pair that already has a judgement is left exactly as it is, verdict and
all. This verb may create a blank and may never overwrite a verdict -- a machine that could
rewrite a judgement is a machine that could quietly clear a failing one.
"""

from __future__ import annotations

import uuid

import collection
import plan as plan_module
from errors import KitError

SUMMARY = "open a judgement for every declared pair that has none, and state the measure"
MUTATES = True
REQUIRES_APPROVED_HOST = True

#: The shape version of the record this verb writes. It writes the document, so it names the
#: contract it writes to -- naming what you produce is a promise, not a policy.
SCHEMA_VERSION = 1

#: The vocabulary of a verdict, as far as this verb is concerned: the one word that means nothing
#: has judged yet. Every other word in the vocabulary is put on a record by a judge, never here.
UNJUDGED = "UNJUDGED"

#: The fields this verb writes, declared by the schema it writes to. One home for each.
CASE, RUBRIC, VERDICT, OPENED_AT = "case", "rubric", "verdict", "opened_at"


class EvaluationError(KitError):
    """No enabled capability declares anything to judge, or two of them do -- which is two homes
    for one question and is refused rather than ordered."""


def _judging(capabilities):
    """The one capability that declares something judged. Found by DECLARATION: this verb knows no
    capability's name and no path, exactly as the mover knows no board's."""
    declaring = [c for c in capabilities if c.evaluates]
    if len(declaring) != 1:
        raise EvaluationError(
            f"{len(declaring)} enabled capabilities declare something to judge "
            f"({sorted(c.id for c in declaring)}); exactly one may, because a host has one answer "
            f"to the question of what it judges and a second home for it would drift the moment "
            f"either was edited"
        )
    return declaring[0]


def _pairs(spec: dict, declaration: dict) -> list:
    """Every (case, rubric) the host said must be judged, in a stable order. The field names are
    the capability's declaration, never this module's: what a case is called and what its rubrics
    are called is a word a host's schema invented, and an interpreter that spelled it would be a
    second home for a judgement the host thought it owned."""
    declared_rubrics = {row[collection.IDENTITY] for row in declaration[spec["rubrics"]]}
    pairs = []
    for case in declaration[spec["cases"]]:
        for rubric in case[spec["judged_by"]]:
            if rubric not in declared_rubrics:
                raise EvaluationError(
                    f"case {case[collection.IDENTITY]!r} is declared to be judged by rubric "
                    f"{rubric!r}, which this host does not declare. A case pointed at a question "
                    f"nobody wrote cannot be judged, and a blank opened for it would read as one "
                    f"waiting for a judge that can never come. Declared rubrics: "
                    f"{sorted(declared_rubrics)}"
                )
            pairs.append((case[collection.IDENTITY], rubric))
    return sorted(set(pairs))


def _blank(ctx, case: str, rubric: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        collection.IDENTITY: uuid.uuid4().hex,
        CASE: case,
        RUBRIC: rubric,
        VERDICT: UNJUDGED,
        OPENED_AT: ctx.clock.now(),
        "kit_version": ctx.manifest.version,
    }


def _measure(pairs: list, records: list) -> str:
    """What is true right now, said in words that cannot be mistaken for a score.

    A zero is stated as a zero. This is the sentence the whole capability exists for: a surface
    that says nothing because nothing was declared reads exactly like one saying that everything
    is fine, and only one of those is honest.
    """
    if not pairs:
        return ("THE MEASURE IS ZERO: this host declares nothing to judge, so nothing here has "
                "been judged. That is not a good score and not a bad one -- it is the absence of "
                "a measure. The framework ships no case and no rubric on purpose: a good answer "
                "is a property of a domain, and it has never met yours.")
    #: A pair counts as READ only where something actually put a verdict on it. A pair with no
    #: record at all and a pair whose record still says UNJUDGED are the same state -- nobody has
    #: read it -- and counting the second while ignoring the first is how a coverage number
    #: becomes flattering. This is counted over the DECLARED pairs, never over the records that
    #: happen to exist, because the records are the half that is easy to be complete about.
    read = {(r[CASE], r[RUBRIC]) for r in records if r[VERDICT] != UNJUDGED}
    unread = [pair for pair in pairs if pair not in read]
    return (f"measure: {len(pairs)} declared pair(s), {len(pairs) - len(unread)} carrying a "
            f"verdict, {len(unread)} never judged. A pair nobody has read is not a failing score "
            f"and not a passing one; it is counted here so that it cannot be mistaken for either.")


def run(ctx, args) -> int:
    capabilities = ctx.enabled_capabilities()
    capability = _judging(capabilities)
    spec = capability.evaluates
    readings = collection.read_all(ctx, capabilities)
    declaration = readings[spec["declaration"]].value
    held = readings[spec["judgements"]]
    root = next(item["target"].rstrip("/") for item in capability.installs
                if item.get("reads_as") == spec["judgements"])

    pairs = _pairs(spec, declaration)
    already = {(record[CASE], record[RUBRIC]) for _rel, record in held.records}

    # The write set is DECIDED here, once. `--plan` prints it and the apply consumes it; there is
    # no second computation to drift from this one.
    opening = [_blank(ctx, case, rubric) for case, rubric in pairs if (case, rubric) not in already]
    writes = [plan_module.Write("create", "ephemeral", "space", capability.id,
                                f"{root}/{blank[collection.IDENTITY]}.json", blank)
              for blank in opening]

    if getattr(args, "plan", False):
        print(plan_module.report("evaluate", writes))
        print(f"  {_measure(pairs, [r for _rel, r in held.records])}")
        return 0

    workspace = ctx.workspace.scoped(capability.targets())
    for write in writes:
        workspace.write_json(write.target, write.item)
        print(f"  {write.accomplished:<9}  {write.target}  "
              f"{write.item[CASE]} / {write.item[RUBRIC]}  {write.item[VERDICT]}")

    on_disk = [record for _rel, record in held.records] + opening
    print(f"  {_measure(pairs, on_disk)}")
    return 0

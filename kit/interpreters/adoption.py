"""ADOPTION -- the kit meeting a tree it has NEVER TOUCHED, where every path either resolves to a
declared class or HALTS.

`upgrade` met a tree the kit created and a human had since edited. This meets a repository written
by people and tools that never heard of this kit, whose provenance is unknown and unknowable from
inside the tree. Two things about that host are different, and only two: there is no record of
what it received, and there are paths -- some exactly where this kit ships something, some inside
a plane this kit governs entirely.

The question this module answers was left open by the blueprint: what CLASS does such a path have?
The answer, settled in ADR-003, is that it has none, and that this is the seam working:

    a class is a WRITE PERMISSION, conferred by a declaration -- an `installs` entry, or a plane
    root. A `foreign` class would be a permission over bytes nobody declared, conferred by the
    ABSENCE of a declaration, which is a class inferred from the tree.

So `foreign` is not a fifth class. It is the DECLARED ABSENCE of a class, read at a stated moment
and written down as a ROSTER -- and the roster is produced by the machine, from declarations,
never by judgement and never by a heuristic over filenames.

The whole reading is the EXISTING three-way reconciliation with one reading known to be empty:

    S = ∅   -- this host was given NOTHING. Empty, and never `absent`: an absent record is a
               question nothing can answer and is refused (that is `upgrade`'s situation); an
               empty one is a declared zero that is true by construction of a host the kit has
               never installed into.

Not one new cell was needed. `collision` (the kit ships a path the host already authored) and
`unaccounted` (a path in a governed plane that no reading explains) were already refusals, already
declared by stewards, already named with the path and the moment. What was missing was never the
answer -- it was reaching that answer on a host that has never been installed into.

Three things this module refuses to do:

  * it never writes. A reading whose whole subject is *paths this kit has no permission to touch*
    may not begin by writing into the host it is surveying.
  * it never infers first contact from the shape of the tree. A host is at first contact when it
    has never ANSWERED -- a declaration's absence, not a tree's appearance.
  * it never refuses a path. It refuses the OPERATION, naming every foreign path at once: a
    partial adoption leaves a tree in a state no version describes.
"""

from __future__ import annotations

import estate as estate_module
import reconcile
from errors import KitError

#: Whose name is on a record of nothing. An empty estate is signed by NOBODY, and says so in
#: words: a name here would attribute a delivery to someone, and no delivery occurred. It is a
#: declared absence, never a placeholder that reads like a value.
NOBODY = "nobody -- this host has never been installed into"

#: The install modes whose targets identify a host AS a host. Asked of the declarations, never
#: spelled as paths: a path written into an interpreter is a second home for a truth a capability
#: states, and it is the home nobody can change.
IDENTIFYING = ("declaration", "estate")


class AdoptionRefused(KitError):
    """Paths this kit has no permission to touch stand where it must install. Every one is named,
    and the OPERATION stops -- never the path."""

    code = "KIT0001"


def nothing(ctx, moment: str) -> dict:
    """The record of a host that received nothing: EMPTY, at a stated moment, signed by nobody.

    This is the one honest way to reconcile an unadopted host, and the distinction it rests on is
    the whole of ADR-003 §2. `upgrade` meets a record that is ABSENT -- a question nothing can
    answer, refused. Adoption meets one that is EMPTY, which is not a guess about the tree but a
    fact about the kit: it has never installed here, so it gave nothing, so the list is [].
    """
    return estate_module.document(ctx, [], moment, NOBODY)


def at_first_contact(ctx) -> bool:
    """Whether this host has never answered this kit.

    Read from a DECLARATION and never from the shape of the tree. The answers file is this host's
    own statement that it has answered; its absence is that statement's absence. A rule that said
    *this tree looks untouched* would be the inference this entire system exists to prevent, and
    it would be wrong in both directions -- an empty repository can already have answered, and a
    crowded one may never have.
    """
    return ctx.host_answers(required=False) is None


def enclosing(ctx) -> list:
    """Every ancestor directory of this host that already holds a host declaration of this kit.

    A host has always been ASSUMED to be a whole repository and nobody ever declared it, which is
    survivable right up to the moment a monorepo part with its own law is met -- and adoption is
    exactly where that is met. Measured at the boundary, upward, once, before anything is trusted;
    the ancestor is looked for at the paths the DECLARATIONS state.

    This closes the silence, not the grammar: WHAT a nested host would inherit and what it may
    contradict is `GAP-NESTED-HOST-GRAMMAR`, declared open in ADR-003 §5. A refusal is not an
    answer to that question, and it is not offered as one -- it is the difference between a named
    refusal with a remedy and two hosts each internally right.
    """
    targets = [item["target"] for item in
               (ctx.install_of_mode(mode, required=False) for mode in IDENTIFYING)
               if item is not None]
    return [f"{parent.as_posix()}/{target}"
            for parent in ctx.workspace.root.parents
            for target in targets
            if (parent / target).exists()]


def require_unenclosed(ctx) -> None:
    found = enclosing(ctx)
    if not found:
        return
    raise AdoptionRefused(
        f"{ctx.workspace.root.as_posix()} is INSIDE a host this kit already holds:\n  "
        + "\n  ".join(found)
        + "\nEvery verb here takes one --root and installs one surface, and nothing states what a "
        "host inside a host inherits from the one around it or what it may contradict. Installing "
        "anyway would leave two hosts, each internally right, and no reader able to tell which "
        "law governs a path. Install at the outer root, or wait for the grammar "
        "(GAP-NESTED-HOST-GRAMMAR)"
    )


def survey(ctx, enabled, moment: str) -> tuple:
    """(the empty record, every row it produces). The reconciliation is the EXISTING one, called
    with one reading known to be empty -- no second table, no adoption-only cell. A second
    reconciler would hold the same knowledge as the first and would be correct beside it only for
    as long as somebody kept them in step."""
    recorded = nothing(ctx, moment)
    stewards = estate_module.stewardship(ctx)
    return recorded, reconcile.survey(ctx, enabled, recorded, stewards)


def roster(ctx, rows, moment: str) -> None:
    """The migration list, PRODUCED BY THE MACHINE and never by judgement.

    Every row exists because a DECLARATION put it there: a `collision` because some capability's
    `installs` states that this kit writes that exact path, an `unaccounted` because a PLANE ROOT
    states the path sits in a plane this kit governs and nothing explains it. No filename is
    matched, no directory is guessed at, nothing is adopted because it looked like the sort of
    thing this kit ships. A human decides what happens to each row -- and no human hand can add
    one either, which is the half of that requirement easiest to forget.
    """
    print(f"adoption: kit {ctx.manifest.version} against a host it has never installed into, "
          f"read at {moment} -- the record of what this host received is EMPTY, not absent")
    reconcile.report(estate_module.stewardship(ctx), rows, reconcile.INTRODUCED)


def require_adoptable(ctx, rows) -> None:
    """Every foreign path at once, and the operation stops.

    Not the path skipped and the rest installed: a partial adoption leaves a tree in a state no
    version describes, and nothing afterwards can say what it is. The remedies are stated because
    none of them is *class this path* -- a hand-written declaration about provenance is precisely
    the roster-by-judgement this design refuses. Each remedy changes what a FRESH READING
    measures, and adoption is then simply re-taken.
    """
    refusals = reconcile.refused(rows)
    if not refusals:
        return
    lines = "\n  ".join(f"{row['state']}  {row['path']}  --  {row['why']}" for row in refusals)
    raise AdoptionRefused(
        f"{len(refusals)} path(s) in this host have no class, and this kit has no permission to "
        f"touch any of them:\n  {lines}\n"
        f"None of these can be classed by hand -- a declaration about where bytes came from, "
        f"written by whoever ran this, is the one thing the record may never carry. Move or "
        f"remove the path; or declare a capability that legitimately ships it; or disable the "
        f"capability that wants it. Then take this reading again"
    )

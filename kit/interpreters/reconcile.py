"""Three readings of one path, and which CELL they fall in. It decides nothing else.

    S -- what the kit SHIPPED into this host, from the estate, at the moment that was taken
    H -- what the host HAS now, measured from disk, at this moment
    N -- what the NEW kit SHIPS, computed from its declarations, at this moment

Each can be absent, present-and-as-shipped, or present-and-changed, and the cell is the name for
the combination. That name is ALL this module produces. What a cell MEANS -- what happens to the
file, what happens to the row, whether it is a refusal, and whether a named human may accept it --
is `stewardship.json`, because it is policy, and policy inside an interpreter is a judgement in
the one place a host cannot reach.

Three things it will not do:

  * it will not infer S. A host with no estate is REFUSED, by name, with the remedy stated. The
    temptation is to treat a pristine-looking tree as though it had just been installed; that is
    an inference from the tree about something a declaration should have stated, and it makes
    every reading below a fiction dressed as a measurement.
  * it will not manufacture a difference it could not measure. Where either side's digest is
    absent -- a directory, a projection, the record itself -- the two are not reported as
    differing. An unmeasurable comparison resolves to nothing, never to a guess.
  * it will not find a safe answer. A path whose owner changed, a path nothing explains, a path
    the host authored where the kit now wants one: each is a refusal that names the path and both
    moments. A reconciliation that always finds a way through certifies rather than measures.
"""

from __future__ import annotations

import hashlib

import estate as estate_module
from errors import KitError

#: The cells. Named here because this module COMPUTES them -- naming what you produce is a
#: promise; the words are the contract the stewardship schema enumerates, and the meanings live
#: only there.
INTRODUCED = "introduced"
COLLISION = "collision"
FORGOTTEN = "forgotten"
RESTORED = "restored"
RETIRED = "retired"
RETIRED_DIVERGED = "retired-diverged"
UNCHANGED = "unchanged"
ADVANCED = "advanced"
DIVERGED_KEPT = "diverged-kept"
CONFLICTED = "conflicted"
CONVERGED = "converged"

#: Two readings that no steward answers for, because they are not about a path's CONTENT.
#: `unaccounted` has no owner at all -- nothing declares the path, so there is nobody to ask.
#: `re-stewarded` has two, which is worse: the bytes were one party's and are now another's, and
#: no upgrade may quietly hand them over. Both are refusals stated in the surface's own words.
UNACCOUNTED = "unaccounted"
RE_STEWARDED = "re-stewarded"


class ReconcileError(KitError):
    """The three readings cannot be reconciled, or one of them cannot honestly be taken."""


def _same(left, right) -> bool:
    """Whether two digests say the same thing. A comparison one side cannot answer is NOT a
    difference: a directory has no bytes and a projection is rebuilt before anyone could look."""
    if left is None or right is None:
        return True
    return left == right


def cell(was: bool, shipped, present: bool, here, will: bool, incoming) -> str:
    """The name for one path's three readings. Pure: no port, no policy, no clock.

    Presence and digest are carried SEPARATELY on purpose. A reading, an answer and a space are
    shipped by declarations that carry no source, so their content cannot be known before the
    host is written -- and folding that into presence would report every one of them as a path
    this kit no longer ships. An unknown content is not an absent path.
    """
    if not was:
        return INTRODUCED if not present else COLLISION
    if not present:
        return RESTORED if will else FORGOTTEN
    if not will:
        return RETIRED if _same(shipped, here) else RETIRED_DIVERGED
    if _same(shipped, here):
        return UNCHANGED if _same(shipped, incoming) else ADVANCED
    if _same(shipped, incoming):
        return DIVERGED_KEPT
    return CONVERGED if _same(here, incoming) else CONFLICTED


def _incoming_digest(ctx, item):
    """What the new kit would put at this path, where that is knowable BEFORE writing it.

    Only a declaration carrying a SOURCE can answer: the bytes are the payload's, verbatim. A
    reading, an answer, a space and a projection have no such source -- their content is a
    function of this host -- and the honest answer for them is that no comparison can be made,
    which `_same` then declines to call a difference.
    """
    if not item.get("source"):
        return None
    return hashlib.sha256(ctx.manifest.payload_text(item["source"]).encode("utf-8")).hexdigest()


def _covered(path: str, roots) -> bool:
    """Whether some declared target accounts for this path -- itself, or the collection it sits
    in. A root is a target ending in '/', which is the same rule the rest of this kit reads."""
    return any(path == root or (estate_module.is_root(root) and path.startswith(root))
               for root in roots)


def survey(ctx, capabilities, recorded, stewards, adoptions=None) -> list:
    """Every path any of the three readings knows about, with its cell and the verdict its
    steward gives that cell. Sorted by path: a report is read by people, and by tests."""
    adoptions = adoptions or {}
    ws = ctx.workspace
    was = {row["path"]: row for row in recorded["files"]}
    will = {item["target"]: (item, capability)
            for capability in capabilities for item in capability.installs}

    rows = []
    for path in sorted(set(was) | set(will)):
        shipped, ahead = was.get(path), will.get(path)
        item = ahead[0] if ahead else None
        mode = item["mode"] if item else shipped["mode"]
        if shipped and item and shipped["mode"] != item["mode"]:
            held, taking = stewards.of_mode(shipped["mode"]), stewards.of_mode(item["mode"])
            if held != taking:
                rows.append(_refusal(
                    path, RE_STEWARDED, taking,
                    f"shipped as {shipped['mode']!r} and owned by {held!r} in a record taken at "
                    f"{recorded['taken_at']}, and this kit ships it as {item['mode']!r}, owned by "
                    f"{taking!r} -- an upgrade may not hand one party's bytes to another"))
                continue
        steward = stewards.of_mode(mode)
        taken = stewards.measures(steward) and not estate_module.is_root(path)
        present = ws.exists(path)
        here = hashlib.sha256(ws.read_bytes(path)).hexdigest() if (present and taken) else None
        found = cell(shipped is not None, shipped["digest"] if shipped else None,
                     present, here,
                     item is not None, _incoming_digest(ctx, item) if item else None)
        verdict = stewards.verdict(steward, found)
        if verdict.get("refuse") and path in adoptions:
            found = verdict["adoptable"]
            verdict = stewards.verdict(steward, found)
        rows.append({
            "path": path, "cell": found, "state": verdict["state"], "steward": steward,
            "mode": mode, "file": verdict["file"], "record": verdict["record"],
            "refuse": bool(verdict.get("refuse")), "adoptable": verdict.get("adoptable"),
            "here": here, "shipped": shipped["digest"] if shipped else None,
            "why": _why(found, recorded["taken_at"], shipped, here),
        })

    # Anything in a governed plane that none of the three readings explains. It is not deleted --
    # the kit did not put it there -- and it is not ignored: an unexplained path in a plane whose
    # whole premise is that every path resolves to a declared class is the defect this refuses.
    roots = set(will) | set(was)
    for plane in ctx.manifest.planes:
        for path in ws.files_under(plane["root"]):
            if not _covered(path, roots):
                rows.append(_refusal(
                    path, UNACCOUNTED, None,
                    f"is in the {plane['class']!r} plane and nothing accounts for it: no install "
                    f"declares it and the record taken at {recorded['taken_at']} does not carry "
                    f"it. The kit did not put it here and will not take it away"))
    return sorted(rows, key=lambda row: row["path"])


def _refusal(path, found, steward, why) -> dict:
    """A reading with no verdict to look up. It carries the same fields as any other row so that
    a surface never has to ask which kind of row it is holding."""
    return {"path": path, "cell": found, "state": found, "steward": steward, "mode": None,
            "file": "keep", "record": "carry", "refuse": True, "adoptable": None,
            "here": None, "shipped": None, "why": why}


def _why(found, moment, shipped, here) -> str:
    """Both moments, always. A digest reads afterwards exactly like a permanent property of a
    file, and two readings of one file disagreeing is not a property of the file."""
    if shipped and here and shipped["digest"] != here:
        return (f"a record taken at {moment} says {shipped['digest'][:12]}, this reading says "
                f"{here[:12]}")
    return f"against a record taken at {moment}"


def refused(rows) -> list:
    return [row for row in rows if row["refuse"]]


def report(stewards, rows, ordinary: str) -> None:
    """The survey, as the operator reads it: the census first -- every state, zeros included --
    then every row whose reading was not the ORDINARY one for this operation.

    It lives here, beside the reading it prints, because `upgrade` and `adoption` are ONE
    reconciliation seen with a different number of readings, and two printers for one reading
    would be two homes for the vocabulary it speaks (Cardinal III). Exactly two things differ
    between the callers, and both arrive as DATA: the HEADLINE, which is about the record rather
    than the rows and is stated by each verb; and which cell is unremarkable -- `unchanged` when a
    host is being carried forward, `introduced` when one is being installed into for the first
    time. A printer that knew which caller it had would be the policy this module refuses to hold.
    """
    for state, count in census(stewards, rows):
        print(f"  {count:>4}  {state}")
    for row in rows:
        if row["refuse"] or row["cell"] != ordinary:
            print(f"  {row['state']:>16}  {row['path']}  --  {row['why']}")


def census(stewards, rows) -> list:
    """(state, count) for EVERY state any steward can produce, including the ones with none.
    A surface that lists only what it found reads identically to a survey that found nothing --
    a zero nobody printed is not a declared zero."""
    words = {row["state"] for steward in stewards.stewards for row in steward["cells"]}
    words |= {UNACCOUNTED, RE_STEWARDED}
    seen = {}
    for row in rows:
        seen[row["state"]] = seen.get(row["state"], 0) + 1
    return [(word, seen.get(word, 0)) for word in sorted(words)]

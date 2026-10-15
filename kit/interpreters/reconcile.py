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
import space
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

    code = "KIT0019"


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


def survey(ctx, capabilities, recorded, stewards, adoptions=None, moved=None) -> list:
    """Every path any of the three readings knows about, with its cell and the verdict its
    steward gives that cell. Sorted by path: a report is read by people, and by tests.

    `moved` is `{to: from}` for every relocation about to be carried out (ADR-021): the record is
    read at the new names and the host's bytes at the old ones, so the reconciliation is the one
    the tree will be in after the moves -- and a plan stays a plan."""
    adoptions = adoptions or {}
    moved = moved or {}
    ws = ctx.workspace
    back = {old: new for new, old in moved.items()}

    def rename(path):
        for old, new in back.items():
            if path == old or (old.endswith("/") and path.startswith(old)):
                return new + path[len(old):]
        return path

    was = {rename(row["path"]): {**row, "path": rename(row["path"])} for row in recorded["files"]}
    will = {item["target"]: (item, capability)
            for capability in capabilities for item in capability.installs}

    rows = []
    for path in sorted(set(was) | set(will)):
        shipped, ahead = was.get(path), will.get(path)
        item = ahead[0] if ahead else None
        # A path this host was given on its own, which the new kit no longer declares on its own
        # but which now lies INSIDE a collection the new kit declares, is not retired: it is
        # ABSORBED, and the collection's steward answers for it (link L3a -- an older host whose
        # vendored pages and pinned copy sat inside what is now the pinned tree). Saying `retired,
        # kept` would promise a file the delivery of that collection is about to replace.
        home = None if item or not shipped else next(
            (root for root in will if estate_module.is_root(root) and path != root
             and path.startswith(root)), None)
        mode = item["mode"] if item else (will[home][0]["mode"] if home else shipped["mode"])
        if shipped and item and shipped["mode"] != item["mode"]:
            held, taking = stewards.of_mode(shipped["mode"]), stewards.of_mode(item["mode"])
            if held != taking:
                rows.append(_refusal(
                    path, RE_STEWARDED, taking,
                    f"shipped as {shipped['mode']!r} and owned by {held!r} in a record taken at "
                    f"{recorded['taken_at']}, and this kit ships it as {item['mode']!r}, owned by "
                    f"{taking!r} -- an upgrade may not hand one party's bytes to another"))
                continue
        # Who answers for the path NOW -- its mode's steward, or, where the row carries a signed
        # transfer, the steward that one declares it transfers to. Read from the record and the
        # declaration; this module privileges no steward and no path (ADR-010).
        steward = stewards.answering(mode, None if home else shipped)
        taken = stewards.measures(steward) and not estate_module.is_root(path)
        read_at = moved.get(path, path)
        # A space is there when a clone would receive it, which is its marker (space.carried).
        present = (space.carried(ctx.manifest, ws, read_at) if mode in space.MODES
                   else ws.exists(read_at))
        here = hashlib.sha256(ws.read_bytes(read_at)).hexdigest() if (present and taken) else None
        found = cell(shipped is not None, shipped["digest"] if shipped else None,
                     present, here,
                     item is not None or home is not None,
                     _incoming_digest(ctx, item) if item else None)
        verdict = stewards.verdict(steward, found)
        if verdict.get("refuse") and path in adoptions:
            found = verdict["adoptable"]
            verdict = stewards.verdict(steward, found)
        rows.append({
            "path": path, "cell": found, "state": verdict["state"], "steward": steward,
            "mode": mode, "file": verdict["file"], "record": verdict["record"],
            "refuse": bool(verdict.get("refuse")), "adoptable": verdict.get("adoptable"),
            "here": here, "shipped": shipped["digest"] if shipped else None,
            "why": ((f"inside {home}, which this kit now delivers whole as {mode!r} -- " if home
                     else _transferred(shipped))
                    + _why(found, recorded["taken_at"], shipped, here)),
            "named": stewards.named(steward),
            # Where the row was ABSORBED into a collection the new kit delivers whole: always
            # printed, whatever its cell, because the path is about to change hands.
            "absorbed": home,
        })

    # Anything in a governed plane that none of the three readings explains. It is never deleted --
    # the kit did not put it there -- and it is never hidden. Whether it REFUSES is the plane's own
    # declaration (`unaccounted`), read as data: a plane whose premise is that every path resolves
    # to a declared class refuses, and a plane the kit disclaims reports. Nothing in a region the
    # kit owns nothing in can obstruct a write the kit was never going to make (ADR-003 §6, met on
    # HOST #2, where 81 session receipts made a real repository unadoptable). The interpreter does
    # not know which plane is which and must not learn.
    roots = set(will) | set(was) | set(moved.values())
    for plane in ctx.manifest.planes:
        refuses = plane["unaccounted"] == "refuse"
        for path in ws.files_under(plane["root"]):
            if not _covered(path, roots):
                rows.append(_refusal(
                    path, UNACCOUNTED, None,
                    f"is in the {plane['class']!r} plane and nothing accounts for it: no install "
                    f"declares it and the record taken at {recorded['taken_at']} does not carry "
                    f"it. The kit did not put it here and will not take it away"
                    + ("" if refuses else f". The {plane['class']!r} plane declares that what it "
                       f"does not account for is REPORTED and does not refuse"),
                    refuse=refuses))
    return sorted(rows, key=lambda row: row["path"])


def _refusal(path, found, steward, why, refuse: bool = True) -> dict:
    """A reading with no verdict to look up. It carries the same fields as any other row so that
    a surface never has to ask which kind of row it is holding -- including whether it refuses,
    which for an unaccounted path is the PLANE's declaration and not this function's opinion."""
    return {"path": path, "cell": found, "state": found, "steward": steward, "mode": None,
            "file": "keep", "record": "carry", "refuse": refuse, "adoptable": None,
            "here": None, "shipped": None, "why": why, "named": False}


def _transferred(shipped) -> str:
    """The signature on a path the host took over, stated on every reading of it. What the kit
    no longer vouches for is said in those words, with the name and the moment that made it so."""
    signed = (shipped or {}).get(estate_module.CEDED)
    if not signed:
        return ""
    return (f"taken over by {signed['signed_by']} at {signed['signed_at']}; this kit no longer "
            f"writes, restores or vouches for it -- ")


def _why(found, moment, shipped, here) -> str:
    """Both moments, always. A digest reads afterwards exactly like a permanent property of a
    file, and two readings of one file disagreeing is not a property of the file."""
    if shipped is None and here is not None:
        # The kit wants this path and nothing says it ever gave it. Saying only *against a record
        # taken at X* would leave the reader to work out WHICH of the three readings was the
        # surprising one -- and on a host being adopted, that is the only question there is.
        return (f"this host already holds bytes here ({here[:12]}) and the record taken at "
                f"{moment} accounts for nothing at this path")
    if shipped and here and shipped["digest"] != here:
        return (f"a record taken at {moment} says {shipped['digest'][:12]}, this reading says "
                f"{here[:12]}")
    return f"against a record taken at {moment}"


def taken_over(ctx, capabilities) -> dict:
    """path -> this reading's verdict, for every path the record says the host TOOK OVER.

    Any writer that has not been handed a reconciliation's verdict asks this before it writes, so
    that `init` run again on a host is not a way around a signed transfer: a vendor mode replaces
    because it cannot tell whether the host touched a file, and here the record says -- with a name
    on it -- that the file is no longer the kit's to replace (ADR-010). Empty where there is no
    record or nothing in it was taken over, and then no survey is taken at all.
    """
    recorded = estate_module.read(ctx)
    ceded = {row["path"] for row in (recorded or {}).get("files", [])
             if row.get(estate_module.CEDED)}
    if not ceded:
        return {}
    rows = survey(ctx, capabilities, recorded, estate_module.stewardship(ctx))
    return {row["path"]: row for row in rows if row["path"] in ceded}


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
        if row["refuse"] or row["cell"] != ordinary or row.get("named") or row.get("absorbed"):
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

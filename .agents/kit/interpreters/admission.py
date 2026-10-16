"""Admission on return -- what a worker's isolated tree came back with, judged before it may enter.

ADR-017 decision 5 states the asymmetry plainly: a runtime without a pre-write block cannot be
stopped mid-command, so its worker writes only inside its own leased tree, and its change is
admitted to the host only after this host's gates have passed on it. "Verification at return
replaces prevention at write" is a sentence that is only true if the verification actually happens;
C2 built the isolation and left this half declared and unbuilt, which meant that in practice a
worker's tree was neither prevented nor verified -- it was simply somewhere else. This module is
that half.

The shape of it:

  1. ASK THE TREE what changed, through the argv its PROVIDER declared. How a tree reports its own
     change is the same product fact as how it was made, so it is declared beside `isolate` in the
     workspace provider and this module names no program (Cardinal II, IV). A provider that cannot
     say what came back cannot be dispatched through -- refused by the port, never admitted blind.
  2. READ THE TEXT out of the tree, per path. The whole file, not only the lines a diff would call
     introduced: a worker's tree is judged on what it now CONTAINS, which is a stricter reading
     than a patch gives and a deliberate one -- text moved into a file by a worker that rewrote it
     is text that entered.
  3. JUDGE with the ONE judge. The same gate registry a runtime's hook meets before a write, so
     the two cannot hold different rule sets.
  4. SAY SO. `admitted` or `refused`, with the moment it was read, every path judged, and every
     gate that could not be applied NAMED. There is no third verdict and there is no silence:
     a change that could not be read is REFUSED, because an unjudged write is not an allowed one,
     and a path the tree reports outside the tree it was given is refused as what it is.

What this module does NOT do is move anything. Admission is a READING -- it neither merges the
worker's work into the host nor withdraws its tree. Both are acts with an owner, and this is the
evidence they are taken on (ADR-017 amendment 6, GAP-D1).
"""

from __future__ import annotations

import re
from pathlib import Path

import judgement
import placement
from errors import KitError

#: The provider's own words for the block that reports a returned change. One home: the schema.
RETURNED = "returned"
ARGV, NAMES = "argv", "names"

#: The two verdicts, and no third. `not measured` is deliberately not among them: a reading that
#: did not happen is a refusal here, not a state a change can sit in on its way into a host.
ADMITTED, REFUSED = "admitted", "refused"


class NotAdmitted(KitError):
    """What a worker left in its isolated tree is not admitted to this host: a declared gate
    refused it, or it could not be read and therefore could not be judged at all."""

    code = "KIT0052"


def declares(provider: dict) -> bool:
    """Whether this provider can say what a worker's tree came back with. Asked by the port before
    anything is leased, so a host that cannot verify a return never starts a worker it could not
    have verified -- the refusal belongs at the door, not after the writing."""
    return RETURNED in provider


def _named(provider: dict, output: str) -> list:
    """Every path one line of the provider's report names, by the grammar it declared. A line the
    pattern does not match names nothing -- silence about a line, never a guess at a path."""
    grammar = re.compile(provider[RETURNED][NAMES])
    found = []
    for line in output.splitlines():
        matched = grammar.match(line)
        if matched and matched.group(1).strip():
            found.append(matched.group(1).strip())
    return found


def of(ctx, provider: dict, tree: Path, argv: list, run) -> dict:
    """The verdict on what this tree came back with, as the `task` schema's `admission` block.

    `argv` is the provider's report command already filled by the port -- this module fills no
    declaration, because the placeholders are the PORT's to provide and a second filler would be a
    second answer to what `{workspace}` means.
    """
    at = ctx.clock.now()
    reported = run(argv, cwd=tree, stdin=None)
    if reported.returncode != 0:
        why = (reported.stderr or reported.stdout or "").strip() or f"exit {reported.returncode}"
        return {"verdict": REFUSED, "at": at, "judged": [],
                "because": f"this tree could not say what changed in it -- {why}; a change that "
                           f"cannot be read cannot be judged, and an unjudged write is not an "
                           f"allowed one"}

    judged, unreadable, deleted, edits = [], [], [], []
    for raw in _named(provider, reported.stdout or ""):
        try:
            rel = placement.host_relative(tree, raw)
        except placement.Unplaceable:
            rel = None
        if rel is None:
            unreadable.append(raw)  # a change the tree reports OUTSIDE the tree it was given
            continue
        judged.append(rel)
        target = tree / rel
        if not target.is_file():
            deleted.append(rel)
            continue
        try:
            edits.append((rel, target.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):
            unreadable.append(rel)

    refused, unjudged = judgement.refusals(ctx, edits)
    verdict = {
        "verdict": REFUSED if (refused or unreadable) else ADMITTED,
        "at": at,
        "judged": judged,
    }
    if refused:
        verdict["refusals"] = [
            dict({"path": path, "gate": rule_id, "because": because},
                 **({"instead": instead} if instead else {}))
            for path, rule_id, because, instead in refused]
    if unjudged:
        verdict["unjudged"] = sorted(set(unjudged))
    if unreadable:
        verdict["unreadable"] = unreadable
    if deleted:
        verdict["deleted"] = deleted
    return verdict


def said(verdict: dict) -> str:
    """The verdict in one line, for whoever is watching the dispatch rather than reading records."""
    if verdict["verdict"] == ADMITTED:
        return (f"admission: ADMITTED -- {len(verdict['judged'])} returned path(s) pass every edit "
                f"judgement this host declares")
    parts = [f"admission: REFUSED -- what this worker's tree came back with does not enter this host"]
    if verdict.get("because"):
        parts.append(f"  {verdict['because']}")
    for row in verdict.get("refusals", []):
        parts.append(f"  {row['path']}  {row['gate']} -- {row['because']}"
                     + (f" Instead: {row['instead']}" if row.get("instead") else ""))
    for path in verdict.get("unreadable", []):
        parts.append(f"  {path} could not be read here, so no gate could judge it")
    if verdict.get("unjudged"):
        parts.append(f"  NOT APPLIED (uncalibrated): {', '.join(verdict['unjudged'])}")
    parts.append("  the tree, its lease and its record are left standing: they are the only "
                 "account of what was refused")
    return "\n".join(parts)

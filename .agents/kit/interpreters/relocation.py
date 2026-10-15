"""Relocation -- an install that MOVED, carried across verbatim (ADR-021 decision 3).

A capability that moves one of its installs says so beside the install it moved: a row of its
`relocations`, `{from, to, decision, referenced_by?}`. `to` is one of that capability's OWN install
targets -- a relocation never declares a place, it names where a truth already declared used to
live -- and the move is written through a scope of exactly those two names (`scope`), never the
capability's install targets widened: those stay the one-owner reading the resolver holds. This module knows no
path and no capability; it reads the rows and the host.

One reading, two callers. `upgrade` takes it to reconcile the host AS IF the moves had happened
(`view`), so the plan it prints is the plan carried out; `init` carries it out, as its own phase,
under the run's one hold and journal, before anything is foreseen -- so a plain `init` against a
kit that moved a place can never seed a blank beside the host's own file at the old one.

A move is a RENAME of bytes, never a rewrite of them. Where a host DOCUMENT -- binding, the host's
own authorship, which no upgrade reads for writing -- still names a path inside `from`, the move
is refused and the exact restatement is printed: the owner edits their own file, and the move
then proceeds. A relocation that rewrote it would be the kit writing the host's words.
"""

from __future__ import annotations

import provenance
from errors import KitError

MOVE, REFUSED, RESTATE = "move", "refused", "restate"


class RelocationRefused(KitError):
    """A declared relocation this host cannot take: both places hold something, a host document
    still points into the old place, or the declaration names a target its capability does not
    install."""

    code = "KIT0068"


def declared(capabilities) -> list:
    """Every relocation row of every capability handed in, each carrying its capability -- and a
    row whose `to` is not one of that capability's install targets is refused at the reading: it
    would be a place declared by a second mechanism."""
    rows = []
    for capability in capabilities:
        targets = set(capability.targets())
        for row in capability.raw.get("relocations", []):
            if row["to"] not in targets:
                raise RelocationRefused(
                    f"capability {capability.id!r} relocates {row['from']!r} to {row['to']!r}, which "
                    f"it does not install -- a relocation names where an install used to live, never "
                    f"a new place (its targets are {sorted(targets)})")
            rows.append({**row, "capability": capability.id})
    return rows


def scope(ctx, row):
    """The workspace one move is written through: its two names and nothing else."""
    return ctx.workspace.scoped((row["from"], row["to"]))


def _documents(capabilities) -> dict:
    """{reads_as: install} over the capabilities handed in -- where a named host document lives."""
    return {i["reads_as"]: i for c in capabilities for i in c.installs if i.get("reads_as")}


def _stale_references(ctx, capabilities, row, view) -> list:
    """Every `(document, value)` of a declared host document that still points into `from`."""
    found = []
    homes = _documents(capabilities)
    for reference in row.get("referenced_by", []):
        install = homes.get(reference["document"])
        if install is None:
            continue
        place = view.get(install["target"], install["target"])
        if not ctx.workspace.exists(place):
            continue
        value = ctx.workspace.read_json(place)
        for record in value.get(reference["list"], []):
            pointed = record.get(reference["field"])
            if isinstance(pointed, str) and pointed.startswith(row["from"]):
                found.append((install["target"], reference, pointed))
    return found


def planned(ctx, capabilities) -> list:
    """Pure: one row per declared relocation whose `from` this host still holds, with a `state` --
    `move`, `restate` (a host document still names the old place) or `refused` (both places hold
    something, and nothing can tell which is the truth). A `from` the host does not hold is no row:
    a host installed after the move, or one already moved, has nothing to carry."""
    rows = [r for r in declared(capabilities) if ctx.workspace.exists(r["from"])]
    view = {r["to"]: r["from"] for r in rows}
    moves = []
    for row in rows:
        if ctx.workspace.exists(row["to"]):
            moves.append({**row, "state": REFUSED,
                          "why": f"{row['to']} exists too: two homes for one truth, and nothing here can "
                                 f"tell which one is it"})
            continue
        stale = _stale_references(ctx, capabilities, row, view)
        if stale:
            restated = "; ".join(f"{doc}: {ref['list']}[].{ref['field']} {old!r} -> "
                                 f"{row['to'] + old[len(row['from']):]!r}" for doc, ref, old in stale)
            moves.append({**row, "state": RESTATE,
                          "why": f"this host's own document still names the old place -- restate it, "
                                 f"then run again: {restated}"})
            continue
        moves.append({**row, "state": MOVE, "why": row["decision"]})
    return moves


def view(moves) -> dict:
    """{to: from} for every move about to happen: a reading taken before them, taken as if after."""
    return {m["to"]: m["from"] for m in moves if m["state"] == MOVE}


def report(moves) -> None:
    for move in moves:
        print(f"  relocate  {move['state']:<8} {move['from']}  ->  {move['to']}  "
              f"({move['capability']}; {move['why']})")


def refuse(moves) -> None:
    """Every refusal at once, before a byte moves: a host half-moved is in no state any version
    describes."""
    stopped = [m for m in moves if m["state"] != MOVE]
    if stopped:
        raise RelocationRefused(
            f"{len(stopped)} declared relocation(s) this host cannot take yet:\n  "
            + "\n  ".join(f"{m['state']}  {m['from']} -> {m['to']}  --  {m['why']}" for m in stopped))


def measure(ctx, rel: str) -> str:
    """h1 of the bytes at `rel`, spelled relative to `rel` itself -- so the same bytes read the same
    at either name, and a move is verified by measuring twice."""
    if rel.endswith("/"):
        lines = [(p[len(rel):], ctx.workspace.read_bytes(p)) for p in ctx.workspace.files_under(rel)]
    else:
        lines = [("", ctx.workspace.read_bytes(rel))]
    return provenance.h1(lines)


def carry_out(ctx, moves, capabilities, moment: str) -> list:
    """Rename each move, verify its bytes, and return the account of it -- `{capability, decision,
    from, to, digest, at}` -- for the estate to carry. Written through each capability's own scope."""
    done = []
    for move in moves:
        before = measure(ctx, move["from"])
        written = scope(ctx, move)
        written.relocate(move["from"].rstrip("/"), move["to"].rstrip("/"))
        parent = move["from"].rstrip("/").rsplit("/", 1)[0]
        ctx.workspace.scoped((parent + "/",)).prune(parent, parent)
        after = measure(ctx, move["to"])
        if before != after:
            raise RelocationRefused(f"{move['from']} -> {move['to']}: the bytes read {before} before the "
                                    f"move and {after} after it")
        print(f"  relocated  {move['from']}  ->  {move['to']}  {after}")
        done.append({"capability": move["capability"], "decision": move["decision"], "from": move["from"],
                     "to": move["to"], "digest": after, "at": moment})
    return done


def rekeyed(files: list, moves) -> list:
    """The estate's `files`, with every row recorded at a moved place carried to its new name --
    same digest, same mode, same steward: the host was given these bytes, and still holds them."""
    carried = {m["from"]: m["to"] for m in moves}
    out = []
    for row in files:
        path = row["path"]
        for old, new in carried.items():
            if path == old or (old.endswith("/") and path.startswith(old)):
                row = {**row, "path": new + path[len(old):]}
                break
        out.append(row)
    return sorted(out, key=lambda r: r["path"])

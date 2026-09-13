"""A SUCCESSION ACT -- a signed roster, carried out (ADR-012).

`succession` READS: it takes the census and prints what the host's map assigns. This module is the
other half, and the most destructive thing this kit does: it moves paths a host authored into the
kit's spaces and moves the rest OUT of the host's tree. Everything here follows from one fact:

    the roster a person signed and the roster the machine carries out must be PROVABLY the same
    value -- and the map's digest alone does not prove it, because the TREE can move between the
    reading that was signed and the moment of the act.

So the door accepts the digest of the whole ROSTER: the map's own digest, and every path with the
digest of its bytes, its disposition, its effect and where it goes. The act re-reads the host at
the moment it becomes a writer and computes that digest again; a different value is refused
whole, before a byte moves (terraform's stale saved plan, Flyway's changed checksum).

Four things this module refuses to do:

  * DESTROY bytes. Every effect is ONE rename: a relocated path is renamed into a space; a removed
    path is renamed ASIDE into the observed plane, where the host deletes it by an ordinary act
    once it is satisfied. A kit that deletes on the strength of a map row has made the one
    mistake nobody can review afterwards.
  * act on a path this kit installed, or on the map itself. Succession answers for a PRIOR
    system; what the kit gave is answered for by the estate, `upgrade` and `cede`.
  * move a path somewhere nothing accounts for. A destination lies under a space whose install
    mode the vocabulary declares may RECEIVE paths, and does not already exist.
  * forget. The act is written to the observed plane BEFORE the first rename, so a killed run
    leaves a record the next run RECONCILES against the tree -- a rename is atomic, so every path
    is whole at exactly one of its two names -- and, once complete, the act is appended to the
    estate: every path with its digest and where its bytes went.

This module names no disposition, no effect, no plane root and no runtime. Effects come from the
vocabulary through `succession.EFFECTS`; places come from the manifest's planes.
"""

from __future__ import annotations

import hashlib
import json
import os

import ephemeral
import succession
from errors import KitError

#: The kit's own name, inside the observed plane, for where acts are recorded and where removed
#: paths are set aside. Vocabulary, not a path: the plane's root is the manifest's.
PLACE = "succession"

#: The kind of document an act is, as the kit schema that is its one home names it.
SCHEMA = "succession-act"


class ActRefused(KitError):
    """The act cannot be carried out whole as read. Every fault is named; nothing moves."""

    code = "KIT0037"


class RosterMoved(KitError):
    """The roster read now is not the roster that was accepted. Nothing further moves."""

    code = "KIT0038"


# -- digests ---------------------------------------------------------------------------------------
def digest_of(host, path: str):
    """sha256 of what stands at `path`: the bytes of a file, the TARGET TEXT of a link (one path,
    never followed), or None where nothing measurable stands."""
    whole = host / path
    if succession._is_link(whole):
        return hashlib.sha256(("link:" + os.readlink(whole)).encode("utf-8")).hexdigest()
    if whole.is_file():
        return hashlib.sha256(whole.read_bytes()).hexdigest()
    return None


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def seal(roster: dict) -> str:
    return hashlib.sha256(canonical(roster)).hexdigest()


# -- composing the act from a fresh reading --------------------------------------------------------
def compose(ctx, reading: dict, recorded: dict) -> dict:
    """The roster this reading would carry out, or a WHOLE refusal naming every fault. Pure: it
    reads the host and decides; it writes nothing, so `--plan` and the act are this one value."""
    words, mapped = reading["words"], reading["map"]
    home = succession.residence(words)
    declared = {d["id"]: d for d in words["dispositions"]}
    host = ctx.workspace.root
    map_digest = hashlib.sha256(mapped["file"].read_bytes()).hexdigest()
    aside_root = ephemeral.place(ctx, f"{PLACE}/{map_digest[:16]}")
    kit_paths = {row["path"] for row in recorded["files"]}
    installs = succession.targets(ctx)
    receiving = [i["target"] for c in ctx.enabled_capabilities() for i in c.installs
                 if i["mode"] in words["receives"] and i["target"].endswith("/")]
    undecided = words["undecided"]["id"]
    faults, paths, outside = [], [], 0
    for entry in reading["entries"]:
        path = entry["path"]
        if entry["state"] == undecided:
            if any(succession._under(path, root) for root in mapped["prior"]):
                faults.append(f"{path}: {undecided} -- no row answers it, and an act is carried out "
                              f"whole or not at all")
            else:
                outside += 1
            continue
        row = succession.answer(mapped["rows"], path)
        effect = declared[row["disposition"]].get("effect")
        if effect is None:
            faults.append(f"{path}: {row['disposition']!r} declares no effect, so it is read and "
                          f"never carried out -- an absent effect is not a default one")
            continue
        if path in kit_paths or succession._on_target(path, installs):
            faults.append(f"{path}: this kit installed it; succession answers for a prior system, "
                          f"and what the kit gave is answered for by the estate")
            continue
        if path == home:
            faults.append(f"{path}: the map itself -- an act may not remove its own authority")
            continue
        destination, relocates = succession.EFFECTS[effect]
        to = destination(row, path, aside_root)
        if relocates:
            if not any(to.startswith(space) for space in receiving):
                faults.append(f"{path}: its destination {to} lies in no space that may receive a "
                              f"path {receiving}; it would be a path nothing accounts for")
                continue
        if os.path.lexists(host / to):
            faults.append(f"{path}: {to} already exists, and nothing here is ever overwritten")
            continue
        paths.append({"path": path, "row": row["path"], "disposition": row["disposition"],
                      "effect": effect, "digest": digest_of(host, path), "to": to})
    if paths and not (mapped["declared_by"] and mapped["declared_at"]):
        faults.append(f"{home}: the map is signed by nobody (no declared_by / declared_at); an "
                      f"unsigned judgement is read, and is never carried out")
    if faults:
        raise ActRefused(f"{len(faults)} fault(s); the succession is carried out whole or not at "
                         f"all, so nothing moves:\n  " + "\n  ".join(faults))
    roster = {"map": map_digest, "residence": home, "paths": paths}
    return {"roster": roster, "digest": seal(roster), "outside": outside}


# -- the record an act leaves in the observed plane -------------------------------------------------
def record_path(ctx, digest: str) -> str:
    return ephemeral.place(ctx, f"{PLACE}/{digest}.json")


def honoured(ctx, value: dict, moment: str) -> dict:
    faults = ctx.manifest.validate(value, SCHEMA)
    if faults:
        raise RosterMoved(f"a succession act {moment} does not honour the kit schema {SCHEMA!r}:\n  "
                          + "\n  ".join(faults))
    if seal(value["roster"]) != value["digest"]:
        raise RosterMoved(f"a succession act {moment} does not hash to the digest it states "
                          f"({value['digest']}); a record that was edited proves nothing")
    return value


def open_act(ctx):
    """The act a killed run left open, or None. More than one is refused: one writer per host
    means at most one act can ever have been interrupted."""
    folder = ephemeral.place(ctx, PLACE)
    found = []
    for rel in ctx.workspace.files_under(folder):
        if rel.endswith(".json") and rel.count("/") == folder.count("/") + 1:
            value = honoured(ctx, ctx.workspace.read_json(rel), f"at {rel}")
            if not value.get("carried_at"):
                found.append(value)
    if len(found) > 1:
        raise RosterMoved(f"{len(found)} succession acts are open in this host "
                          f"{[v['digest'] for v in found]}; a person must say which is true")
    return found[0] if found else None


def reconcile(ctx, act: dict) -> tuple:
    """(pending, carried, conflicts) -- each path of the act read against the tree NOW. A rename
    is atomic, so a path is whole at exactly one of its two names; anything else is a tree that
    moved under the act, and a person reads it before any machine acts on it again."""
    host = ctx.workspace.root
    pending, carried, conflicts = [], [], []
    for item in act["roster"]["paths"]:
        here, there = digest_of(host, item["path"]), digest_of(host, item["to"])
        if here == item["digest"] and there is None and not os.path.lexists(host / item["to"]):
            pending.append(item)
        elif there == item["digest"] and here is None and not os.path.lexists(host / item["path"]):
            carried.append(item)
        else:
            conflicts.append(f"{item['path']} -> {item['to']}: the source reads "
                             f"{here or 'nothing'}, the destination {there or 'nothing'}, and the "
                             f"act signed {item['digest']}")
    return pending, carried, conflicts


def scope(ctx, act: dict):
    """The one workspace an act writes through: exactly the paths its roster names, their
    destinations, and the rows whose emptied directories it may remove. Nothing else."""
    items = act["roster"]["paths"]
    return ctx.workspace.scoped({p for item in items for p in (item["path"], item["to"], item["row"])})


def carry(ctx, act: dict, pending: list, say) -> None:
    """Rename every pending path, each re-measured immediately before it moves. A path whose
    bytes changed since the roster was read stops the act where it stands; the record stays
    open, and the next run names the path for a person rather than guessing."""
    ws, host = scope(ctx, act), ctx.workspace.root
    for index, item in enumerate(pending):
        now = digest_of(host, item["path"])
        if now != item["digest"]:
            raise RosterMoved(
                f"{item['path']} changed while the act was under way (signed {item['digest']}, "
                f"reads {now or 'nothing'}); {index} of {len(pending)} path(s) were carried by this "
                f"run and the act stays OPEN -- read it again with --plan")
        ws.relocate(item["path"], item["to"])
        parent = item["path"].rsplit("/", 1)[0] if "/" in item["path"] else ""
        if parent and item["row"] != item["path"]:
            ws.prune(parent, item["row"])
        say(item)

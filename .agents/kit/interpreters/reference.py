"""reference -- a host that holds the kit in its OWN tree at a pinned commit runs it from there, and keeps
no copy (ADR-024 decision 18).

A host that carries the kit as a git submodule (or any nested checkout) already pins it: the commit is
recorded by the host's own repository. Vendoring a second copy beside it (`.agents/kit/`, the taken
capabilities under `.agents/taken/`) makes two sources for one pin, and the two can disagree. So such a
host may be REFERENCED: its lock -- at the seat the pinned-lock install declares -- carries one more
block, `reference`: where the kit's payload sits in the host (`path`), the repository holding it and
the commit it pins (`repository`, `commit`), and where each taken capability is read from (`takes`).
The lock's `files` stay what they always were -- the digest of every path of the kit -- so the
referenced tree is judged against the very reading a vendored copy is judged against.

What this module owns, and nothing else: reading the block, saying which directory a host's hooks
run (`runs_from`), and judging the referenced kit -- present, at the pinned commit, equal to the lock.
A taken capability's digest keeps its one home, the provenance pin in the estate; the `taken-intact`
gate holds the referenced source to it exactly as it holds a copy. A vendored host has no block, and
every answer here is then the vendored one: nothing changes for it.
"""

from __future__ import annotations

import json
from pathlib import Path

import lockfile
import pin
from errors import KitError

#: The field of the host's lock that makes a host referenced. One word, one home.
FIELD = "reference"
#: The command that brings an uninitialised or missing submodule back -- what a person runs.
RESTORE = "git submodule update --init"
#: The install modes governance declares the take plane and the take statement under (ADR-018) --
#: their one home, which the manifest port reads (a port may stand on the core, never the reverse).
TAKEN, TAKEN_DECLARATION = "taken", "taken-declaration"


class ReferenceRefused(KitError):
    """A referenced host whose kit or taken capability is absent, at another commit, or no longer
    equal to the lock -- or a migration to referenced mode that cannot be made honestly."""

    code = "KIT0083"


def of_host(manifest, host_root) -> "dict | None":
    """The `reference` block of the host's lock, or None for a vendored host (or one with no lock)."""
    seats = pin.seats(manifest)
    if seats is None:
        return None
    lock = Path(host_root) / seats[1]
    if not lock.is_file():
        return None
    try:
        return json.loads(lock.read_text(encoding="utf-8")).get(FIELD)
    except ValueError:
        return None


def of(ctx) -> "dict | None":
    return of_host(ctx.manifest, ctx.workspace.root)


def runs_from(ctx) -> str:
    """The host-relative directory of the kit this host's hooks and served settings run: the
    referenced payload, or the vendor plane where the host carries a copy."""
    held = of(ctx)
    return held["path"].rstrip("/") if held else ctx.manifest.plane("vendor")


def absent(held: dict, what: str) -> str:
    return (f"{what} -- this host references the kit in its own tree, and that tree is not there (an "
            f"uninitialised or removed submodule). Run: {RESTORE} {held['repository']}")


def homes(held: "dict | None", host_root) -> dict:
    """take id -> the directory a referenced take is read from (absolute), for the manifest port."""
    if not held:
        return {}
    return {row["id"]: Path(host_root) / row["path"] for row in held.get("takes", [])}


def roots(ctx) -> list:
    """Every host-relative directory holding a PUBLISHER's bytes in a referenced host: the kit's
    payload and each referenced take. Judged by their digests, never by the host's text policy."""
    held = of(ctx)
    if not held:
        return []
    return [held["path"].rstrip("/") + "/"] + [row["path"].rstrip("/") + "/" for row in held.get("takes", [])]


def verify(ctx, held: dict) -> list:
    """Every way the referenced kit is not the one the lock pins: absent, at another commit, or with
    bytes that differ from the lock (an uncommitted edit is never run as the pinned kit)."""
    ws, path = ctx.workspace, held["path"].rstrip("/")
    if not ws.exists(f"{path}/MANIFEST.json"):
        return [absent(held, f"{path}/: no kit")]
    failures = []
    commit, _top, why = ws.revision(path)
    if commit is None:
        failures.append(f"{path}/: the commit it stands at cannot be read ({why}), so nothing says it is "
                        f"the commit the lock pins ({held['commit']})")
    elif commit != held["commit"]:
        failures.append(f"{held['repository']}: stands at {commit[:12]} and the lock pins {held['commit'][:12]} -- "
                        f"return it (`{RESTORE} {held['repository']}`) or pin the new commit "
                        f"(`upgrade --root . --mode referenced --approve <who>` from the kit at {path})")
    lock = pin.seats(ctx.manifest)[1]
    drift, _pinned = pin.verify(ctx.manifest, ws, path + "/", lock)
    failures += drift
    return failures


def drifted(ctx) -> list:
    """The integrity half of `verify`, for the entry point: where THIS run's kit is the referenced one,
    every (state, path) on which it differs from the host's lock -- read with the manifest the run
    already holds, so the guard costs one survey and no second reading of the kit. Empty for a
    vendored host, or a run whose kit is not the referenced tree."""
    held = of(ctx)
    if not held:
        return []
    if ctx.workspace.path(held["path"].rstrip("/")).resolve() != ctx.manifest.root.resolve():
        return []
    lock = ctx.workspace.read_json(pin.seats(ctx.manifest)[1])
    rows = lockfile.survey(ctx.manifest, ctx.manifest.files())
    return [(state, path) for state, path, _why in lockfile.compare(lock, rows)]


def refuse_drift(ctx) -> None:
    """Refuse to run a referenced kit that is not the one the lock pins: an edit to it, committed or
    not, is never run as the pinned kit. `upgrade --mode referenced` is how a new state is pinned."""
    drift = drifted(ctx)
    if drift:
        held = of(ctx)
        raise ReferenceRefused(
            f"the kit at {held['path']}/ is not the kit this host's lock pins -- {len(drift)} path(s) "
            f"differ: " + ", ".join(f"{p} ({s})" for s, p in drift[:6])
            + f". An edit to a referenced kit is never run as the pinned one: restore it (`git -C "
            f"{held['repository']} checkout -- .`, or `{RESTORE} {held['repository']}`), or commit it "
            f"and pin it (`upgrade --root . --mode referenced --approve <who>`)")


def _relative(ctx, path) -> "str | None":
    try:
        return Path(path).resolve().relative_to(ctx.workspace.root.resolve()).as_posix()
    except ValueError:
        return None


def pinning(ctx, moment: str) -> tuple:
    """(the lock a referenced host is given, the copies it then no longer needs, the takes whose source
    now holds a NEWER version and are taken again in this walk) for the kit THIS run is -- refused, by
    name, wherever the reference could not be honest: a kit outside the host's tree, one not in a
    repository, one with uncommitted changes or differing from its own lock, a take whose source is not
    in the host's tree or was never pinned -- and, by provenance (KIT0032), a take whose bytes changed
    under the version pinned or whose version is older than it."""
    import estate as estate_module
    import provenance

    ws, root = ctx.workspace, ctx.manifest.root
    path = _relative(ctx, root)
    if path is None or path in ("", "."):
        raise ReferenceRefused(f"the kit running this upgrade is at {root.as_posix()}, outside this host's tree; a "
                               f"referenced host runs the kit it holds in its OWN tree (a submodule). Run this "
                               f"upgrade with that kit: python <its path>/interpreters/cli.py upgrade --root . "
                               f"--mode referenced")
    commit, repository, why = ws.revision(path)
    if commit is None:
        raise ReferenceRefused(f"{path}/: no repository states its commit ({why}); a reference pins a commit")
    changed, why = ws.changes(path)
    if changed is None or changed:
        raise ReferenceRefused(f"{path}/: " + (f"its changes cannot be read ({why})" if changed is None else
                               f"{len(changed)} uncommitted change(s), e.g. {changed[0].strip()}")
                               + " -- an uncommitted kit is never pinned; commit it first")
    seen = pin.reading(ctx.manifest)
    if not seen["intact"]:
        raise ReferenceRefused(f"{path}/: the kit differs from its own lock ({len(seen['drift']) + len(seen['unresolved'])} "
                               f"path(s)); lock and commit it first")
    # The take plane and the statement of what was taken, by the modes governance declares them under.
    plane = ctx.install_of_mode(TAKEN, required=False)
    statement = ctx.install_of_mode(TAKEN_DECLARATION, required=False)
    rows = ws.read_json(statement["target"])["takes"] if statement and ws.exists(statement["target"]) else []
    pins = {p["capability"]: p for p in (estate_module.read(ctx) or {}).get("taken", [])}
    declared = {c.id: c.raw for c in ctx.manifest.capabilities}
    takes, copies, retaken = [], [pin.seats(ctx.manifest)[0]], []
    for row in rows:
        given = Path(row["source"])
        source = _relative(ctx, given if given.is_absolute() else ws.path(row["source"]))
        if source is None or not ws.path(source).is_dir():
            raise ReferenceRefused(f"{row['id']}: taken from {row['source']}, which is not a directory in this host's "
                                   f"tree; take it again from the kit this host holds, then upgrade")
        signature = ((declared.get(row["id"]) or {}).get(provenance.CLAIM) or {}).get("signature")
        measured = provenance.tree_digest(ws.path(source), f"{plane['namespace']}{row['id']}/", signature)
        held = pins.get(row["id"])
        if held is None:
            raise ReferenceRefused(f"{row['id']}: {source}/ measures {measured}, and no provenance pin holds it -- "
                                   f"nothing says this host took these bytes; take it from {source}, then upgrade")
        if held["digest"] != measured:
            # A NEWER version at the referenced source is a re-release the advanced submodule brought:
            # it is taken again in this walk, at the door the upgrade walks. The same version with other
            # bytes, or an older one, is refused by the one judge of a pin (KIT0032), and no name opens it.
            version = (declared.get(row["id"]) or {}).get("version", "")
            provenance.arrival(ctx, row["id"], version, measured, "<who>", moment, held)
            retaken.append({"id": row["id"], "version": version, "digest": measured, "prior": held})
        takes.append({"id": row["id"], "path": source})
        copies.append(f"{plane['target']}{row['id']}/")
    lock = json.loads(pin.lock_text(ctx.manifest, seen, moment))
    lock[FIELD] = {"path": path, "repository": repository, "commit": commit, "takes": takes}
    errors = ctx.manifest.validate(lock, "lock")
    if errors:
        raise ReferenceRefused("the referenced lock would not honour the lock schema:\n  " + "\n  ".join(errors))
    return lock, copies, retaken

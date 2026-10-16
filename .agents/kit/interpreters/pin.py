"""What a RELEASE of the kit is, how a host is given one, and how it proves it still holds it
(ADR-016).

A release is not a folder and it is not a version string. It is a kit whose bytes EQUAL its own
lock -- the reading `lock` takes, which enumerates every path the kit is made of with its digest --
and its identity is the digest of that lock. Two kits that agree on that digest are one release,
whatever their paths; two that disagree are two, whatever their `kit.version` claims.

A host carries its kit the way a lockfile-driven package manager carries a dependency -- a vendored
tree plus the lock it was checked against (`go mod vendor` + `go.sum`, `npm ci` + the lockfile):
the WHOLE payload the lock enumerates, verbatim, at one declared target in the vendor plane, and
the lock itself at a second declared seat beside the host's other statements. From then on the host runs every verb from that copy, and the copy is judged
against the lock it CARRIES -- never against the kit that installed it, never against a working
source. The kit that delivered it may be gone; that is the point.

Two readings are kept apart because they answer different questions:

  * INTEGRITY -- does the pinned tree equal the lock it carries? Measured, byte for byte, by the
    same survey `lock` takes. A changed file is named with its state; nothing here repairs it.
  * AUTHENTICITY -- is that lock the one upstream published? Only a signature can say, and the
    kit's own lock is not signed (ADR-008 names it not built; ADR-016 keeps it an owner door). So
    it is printed `authenticity NOT ESTABLISHED`, every time, and never implied by a green
    integrity check.

A kit whose bytes do NOT equal its own lock is a working tree, not a release. It can still be
delivered -- every fixture kit, every host that took an adapter, every uncommitted change is one --
but the lock it leaves in the host is a fresh reading whose version carries the local label
`+unreleased` (PEP 440 local version / SemVer build metadata: the field's one mark for "built from
something that is not the release"). The state is written INTO the pinned lock, so it is nameable
long after the terminal that printed it has closed.

What this module refuses, all deliberately:

  * to pin a kit that cannot state what it is -- a path missing, unaccounted, or carrying a
    carriage return. A pinned copy that silently lacked a file would run until the day it needed
    it; the refusal is the `lock` verb's, applied at the only other place a kit is copied;
  * to re-deliver a pinned kit over ITSELF once it no longer equals its own lock. Re-stamping it
    would launder a change into a fresh reading; a release must be delivered over it instead;
  * to call a source a release when it is not one: a release source is read at a REVISION, and a
    revision whose tree differs from its own lock is refused by name.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

import lockfile
from errors import KitError

#: The install mode whose target IS the pinned kit. Found through the declarations, never by a
#: path constant -- the same rule the estate's own mode follows.
MODE = "pinned"

#: The install mode whose target is the SEAT of the lock the host was given (the drawn
#: `project/kit.lock.json`). The pinned tree and its lock are two declared targets of ONE act:
#: the tree lives in the vendor plane, the statement of what the host was given lives beside the
#: host's other statements, and neither location is spelled in an interpreter.
LOCK_MODE = "pinned-lock"

#: The local label a delivery from a working tree carries on its version. One word, stated here.
UNRELEASED = "unreleased"

#: What the surface says about authenticity until the kit's own lock carries a signature. One
#: sentence, one home: every surface that states a release identity prints exactly this.
UNSIGNED = "authenticity NOT ESTABLISHED (the kit's own lock carries no signature)"

class ReleaseError(KitError):
    """A kit that cannot state what it is was asked to be pinned, a pinned kit was asked to
    re-deliver itself while it no longer equals its own lock, or a source that claims to be a
    release is not one or cannot be read."""

    code = "KIT0041"


def digest_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# -- where a pinned kit and its lock sit ---------------------------------------------------------
def seats(manifest):
    """(tree target, lock target) as governance DECLARES them, or None for a kit that pins
    nothing. Both are host-relative; neither is ever spelled in an interpreter."""
    found = {item["mode"]: item["target"] for c in manifest.capabilities for item in c.installs
             if item["mode"] in (MODE, LOCK_MODE)}
    if MODE not in found or LOCK_MODE not in found:
        return None
    return found[MODE], found[LOCK_MODE]


def lock_file(manifest) -> Path:
    """The lock THIS kit is judged against, as a path on disk.

    An upstream kit carries its lock inside its own tree (`ships.lock`). A PINNED copy does not:
    the host was given the lock at the declared seat beside its other statements, so a kit whose
    root IS the declared tree target of some host reads the lock at that host's seat. Which of the
    two applies is read from the declaration and the measured root, never from which file happens
    to exist -- an absent seat is then named as absent, not quietly replaced by another file."""
    seat = seats(manifest)
    if seat is not None:
        tree = PurePosixPath(seat[0].rstrip("/")).parts
        root = manifest.root.parts
        if len(root) > len(tree) and tuple(root[-len(tree):]) == tuple(tree):
            return manifest.root.parents[len(tree) - 1] / seat[1]
    return manifest.root / manifest.raw_ships()["lock"]


# -- reading a kit -----------------------------------------------------------------------------
def reading(manifest) -> dict:
    """The kit as it stands against the lock it is judged by. Pure over the kit's own tree and
    the one lock `lock_file` names.

    `unresolved` are the survey's own non-`matched` rows: paths the kit cannot ship at all.
    `drift` is the comparison with the recorded lock: paths on which this tree and its lock
    disagree. A kit is a RELEASE only when both are empty."""
    kit = manifest.files()
    lock = lock_file(manifest)
    rows = lockfile.survey(manifest, kit)
    unresolved = [row for row in rows if row["state"] != lockfile.MATCHED]
    text = lock.read_text(encoding="utf-8") if lock.is_file() else None
    recorded = json.loads(text) if text is not None else None
    drift = (lockfile.compare(recorded, rows) if recorded is not None
             else [(lockfile.MISSING, lock.as_posix(), "the kit carries no lock")])
    intact = recorded is not None and not drift and not unresolved
    return {"lock_path": lock.as_posix(), "lock_text": text, "rows": rows,
            "unresolved": unresolved, "recorded": recorded, "drift": drift, "intact": intact,
            # A tree can equal a lock that SAYS it is no release: a copy pinned from a working
            # tree carries its own fresh reading, labelled. Equality with that lock is integrity;
            # it is never promotion to the release the label says it is not.
            "released": intact and recorded["kit_version"] == manifest.version}


def identity(manifest) -> str:
    """One line that says what this kit IS as a release, for every surface that must say it."""
    seen = reading(manifest)
    # What the host TOOK is stated beside the release, never folded into it (ADR-018 decision 5).
    taken = f" + taken: {', '.join(manifest.taken)}" if manifest.taken else ""
    if seen["released"]:
        return (f"release {manifest.version}{taken} · lock sha256:{digest_of(seen['lock_text'])} · "
                f"{UNSIGNED}")
    if seen["intact"]:
        text = seen["lock_text"]
        return (f"kit {seen['recorded']['kit_version']}{taken} · lock sha256:{digest_of(text)} -- "
                f"pinned from a working tree and intact against that reading, so it is no release")
    return (f"kit {manifest.version}+{UNRELEASED}{taken} -- a working tree: "
            f"{len(seen['drift']) + len(seen['unresolved'])} path(s) differ from its own lock, "
            f"so it is no release")


def _require_shippable(manifest, seen: dict) -> None:
    if seen["unresolved"]:
        raise ReleaseError(
            f"{manifest.root.as_posix()}: this kit cannot state what it is, so it cannot be "
            f"pinned -- " + ", ".join(f"{row['path']} ({row['state']})"
                                      for row in seen["unresolved"][:8])
            + ". A pinned copy lacking a file runs until the day it needs it; fix the kit, "
            "then deliver it again")


def lock_text(manifest, seen: dict, moment: str) -> str:
    """The lock a delivery leaves beside the pinned tree. A release carries its OWN lock verbatim
    (its identity is that text); a working tree carries a fresh reading labelled `+unreleased`,
    validated against the lock schema like any reading the kit writes down.

    What the fresh reading must NOT do is widen what the kit ISSUED. A path the source's own lock
    did not issue -- a capability the host took, a file the working tree added -- is carried and
    digested, and accounted `not-issued`, so provenance run from the pinned copy still sees a taken
    capability as taken (and never as withdrawn)."""
    if seen["released"]:
        return seen["lock_text"]
    doc = lockfile.document(manifest, seen["rows"], moment)
    doc["kit_version"] = f"{manifest.version}+{UNRELEASED}"
    issued = lockfile.issued(seen["recorded"]) if seen["recorded"] is not None else set()
    for entry in doc["files"]:
        if entry["path"] not in issued:
            entry["accounted_by"] = lockfile.NOT_ISSUED
    errors = manifest.validate(doc, "lock")
    if errors:
        raise ReleaseError("the pinned reading does not honour the lock schema:\n  "
                           + "\n  ".join(errors))
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# -- the install modes: foresee, apply ---------------------------------------------------------
def _same_root(manifest, ws, tree: str) -> bool:
    return manifest.root.resolve() == ws.path(tree).resolve()


def foresee(manifest, ws, tree: str, lock: str) -> str:
    """What delivering this kit to the host's `tree` and lock seat would do -- decided ONCE,
    before any byte moves, so a refusal lands in the plan and never half-way through an install.
    The tree and its lock are one act, so both modes ask this one question.

    `keep` where the host already holds exactly this kit, intact: the same paths, the same
    digests, the same version (the moment of a working-tree reading is not part of what a kit IS).
    `create` where nothing is pinned, `replace` otherwise -- including a tree of an OLDER SHAPE (a
    pinned copy one level down, beside vendored pages), which is not a kit at this target and is
    therefore replaced whole, in the plan, by one that is."""
    seen = reading(manifest)
    _require_shippable(manifest, seen)
    if _same_root(manifest, ws, tree):
        if not seen["intact"]:
            raise ReleaseError(
                f"{tree}: the pinned kit is delivering ITSELF and no longer equals its own lock "
                f"({len(seen['drift'])} path(s): "
                + ", ".join(f"{p} ({s})" for s, p, _ in seen["drift"][:5])
                + "). Re-stamping it would launder the change into a new reading; deliver a "
                "release over it instead: `upgrade --root <host> --kit <release>`")
        return "keep"
    if not ws.exists(tree.rstrip("/")):
        return "create"
    failures, _pinned = verify(manifest, ws, tree, lock)
    if failures:
        return "replace"
    held = ws.read_json(lock)
    fresh = json.loads(lock_text(manifest, seen, "the moment does not decide sameness"))
    same = (held["kit_version"] == fresh["kit_version"]
            and held["files"] == fresh["files"])
    return "keep" if same else "replace"


def foresee_lock(manifest, ws, tree: str, lock: str) -> str:
    """The seat's disposition follows the tree's -- one act, one decision -- except that a seat is
    created where none stood."""
    if foresee(manifest, ws, tree, lock) == "keep" and ws.exists(lock):
        return "keep"
    return "replace" if ws.exists(lock) else "create"


def deliver(manifest, ws, tree: str, moment: str) -> dict:
    """Replace `tree` of the host WHOLE with this kit: every path its survey accounts for,
    verbatim. The tree is the release; a stray file in it would make the pinned copy something no
    release describes, so the swap leaves nothing else behind. The lock is the other half of the
    same act, written at its own declared seat by `deliver_lock`."""
    seen = reading(manifest)
    _require_shippable(manifest, seen)
    if _same_root(manifest, ws, tree):
        return {"released": seen["released"], "count": len(seen["rows"]),
                "lock": digest_of(seen["lock_text"])}
    source = manifest.files()
    text = lock_text(manifest, seen, moment)
    ws.write_tree(tree, {row["path"]: source.read_bytes(row["path"]) for row in seen["rows"]})
    return {"released": seen["released"], "count": len(seen["rows"]), "lock": digest_of(text)}


def deliver_lock(manifest, ws, tree: str, lock: str, moment: str) -> str:
    """Write the lock the host was given at its seat, and return its digest. A release leaves its
    own lock verbatim; a working tree leaves its labelled fresh reading."""
    seen = reading(manifest)
    _require_shippable(manifest, seen)
    text = lock_text(manifest, seen, moment)
    if not _same_root(manifest, ws, tree):
        ws.write_text(lock, text)
    return digest_of(text)


def verify(manifest, ws, tree: str, lock: str) -> tuple:
    """(failures, pinned manifest or None): the pinned tree against the lock the host was given."""
    if not ws.exists(tree.rstrip("/") + "/MANIFEST.json"):
        return [f"{tree}: no pinned kit -- this host cannot run a verb by itself"], None
    try:
        pinned = manifest.kit_at(ws.path(tree))
        if not ws.exists(lock):
            return [f"{lock}: the host holds no lock for its pinned kit, so nothing states what "
                    f"it is"], pinned
        recorded = ws.read_json(lock)
        rows = lockfile.survey(pinned, pinned.files())
    except (KitError, ValueError) as broken:
        return [f"{tree}: the pinned kit cannot state what it is -- {broken}"], None
    return ([f"{tree}{path}: {state} -- {why}"
             for state, path, why in lockfile.compare(recorded, rows)], pinned)



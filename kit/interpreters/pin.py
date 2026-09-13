"""What a RELEASE of the kit is, how a host is given one, and how it proves it still holds it
(ADR-016).

A release is not a folder and it is not a version string. It is a kit whose bytes EQUAL its own
lock -- the reading `lock` takes, which enumerates every path the kit is made of with its digest --
and its identity is the digest of that lock. Two kits that agree on that digest are one release,
whatever their paths; two that disagree are two, whatever their `kit.version` claims.

A host carries its kit the way a lockfile-driven package manager carries a dependency -- a vendored
tree plus the lock it was checked against (`go mod vendor` + `go.sum`, `npm ci` + the lockfile):
the WHOLE payload the lock enumerates, verbatim, beside the lock itself, at one declared target in
the vendor plane. From then on the host runs every verb from that copy, and the copy is judged
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
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

import lockfile
from errors import KitError
from manifest import Manifest
from workspace import Workspace

#: The install mode whose target IS the pinned kit. Found through the declarations, never by a
#: path constant -- the same rule the estate's own mode follows.
MODE = "pinned"

#: The local label a delivery from a working tree carries on its version. One word, stated here.
UNRELEASED = "unreleased"

#: What the surface says about authenticity until the kit's own lock carries a signature. One
#: sentence, one home: every surface that states a release identity prints exactly this.
UNSIGNED = "authenticity NOT ESTABLISHED (the kit's own lock carries no signature)"

#: A release source naming a revision of a repository, in the form the Python packaging field
#: standardised for exactly this (PEP 508 / pip's VCS form): `git+<repo>@<rev>#subdirectory=<dir>`.
_VCS = re.compile(r"^git\+(?P<repo>.+)@(?P<rev>[^@#]+)(#subdirectory=(?P<sub>[^#]+))?$")


class ReleaseError(KitError):
    """A kit that cannot state what it is was asked to be pinned, a pinned kit was asked to
    re-deliver itself while it no longer equals its own lock, or a source that claims to be a
    release is not one or cannot be read."""

    code = "KIT0041"


def digest_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_source(text: str) -> bool:
    """Whether a `--kit` value names a release SOURCE (a revision) rather than a directory."""
    return bool(_VCS.match(text or ""))


# -- reading a kit -----------------------------------------------------------------------------
def reading(manifest: Manifest) -> dict:
    """The kit as it stands against the lock it carries. Pure over the kit's own tree.

    `unresolved` are the survey's own non-`matched` rows: paths the kit cannot ship at all.
    `drift` is the comparison with the recorded lock: paths on which this tree and its lock
    disagree. A kit is a RELEASE only when both are empty."""
    kit = Workspace(manifest.root)
    lock_path = manifest.raw_ships()["lock"]
    rows = lockfile.survey(manifest, kit)
    unresolved = [row for row in rows if row["state"] != lockfile.MATCHED]
    recorded = kit.read_json(lock_path) if kit.exists(lock_path) else None
    drift = (lockfile.compare(recorded, rows) if recorded is not None
             else [(lockfile.MISSING, lock_path, "the kit carries no lock")])
    intact = recorded is not None and not drift and not unresolved
    return {"lock_path": lock_path, "rows": rows, "unresolved": unresolved,
            "recorded": recorded, "drift": drift, "intact": intact,
            # A tree can equal a lock that SAYS it is no release: a copy pinned from a working
            # tree carries its own fresh reading, labelled. Equality with that lock is integrity;
            # it is never promotion to the release the label says it is not.
            "released": intact and recorded["kit_version"] == manifest.version}


def identity(manifest: Manifest) -> str:
    """One line that says what this kit IS as a release, for every surface that must say it."""
    seen = reading(manifest)
    if seen["released"]:
        text = Workspace(manifest.root).read_text(seen["lock_path"])
        return f"release {manifest.version} · lock sha256:{digest_of(text)} · {UNSIGNED}"
    if seen["intact"]:
        text = Workspace(manifest.root).read_text(seen["lock_path"])
        return (f"kit {seen['recorded']['kit_version']} · lock sha256:{digest_of(text)} -- "
                f"pinned from a working tree and intact against that reading, so it is no release")
    return (f"kit {manifest.version}+{UNRELEASED} -- a working tree: "
            f"{len(seen['drift']) + len(seen['unresolved'])} path(s) differ from its own lock, "
            f"so it is no release")


def _require_shippable(manifest: Manifest, seen: dict) -> None:
    if seen["unresolved"]:
        raise ReleaseError(
            f"{manifest.root.as_posix()}: this kit cannot state what it is, so it cannot be "
            f"pinned -- " + ", ".join(f"{row['path']} ({row['state']})"
                                      for row in seen["unresolved"][:8])
            + ". A pinned copy lacking a file runs until the day it needs it; fix the kit, "
            "then deliver it again")


def lock_text(manifest: Manifest, seen: dict, moment: str) -> str:
    """The lock a delivery leaves beside the pinned tree. A release carries its OWN lock verbatim
    (its identity is that text); a working tree carries a fresh reading labelled `+unreleased`,
    validated against the lock schema like any reading the kit writes down.

    What the fresh reading must NOT do is widen what the kit ISSUED. A path the source's own lock
    did not issue -- a capability the host took, a file the working tree added -- is carried and
    digested, and accounted `not-issued`, so provenance run from the pinned copy still sees a taken
    capability as taken (and never as withdrawn)."""
    if seen["released"]:
        return Workspace(manifest.root).read_text(seen["lock_path"])
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


# -- the install mode: foresee, apply ----------------------------------------------------------
def _same_root(manifest: Manifest, ws: Workspace, root: str) -> bool:
    return manifest.root.resolve() == ws.path(root).resolve()


def foresee(manifest: Manifest, ws: Workspace, root: str) -> str:
    """What delivering this kit to `root` would do -- decided ONCE, before any byte moves, so a
    refusal lands in the plan and never half-way through an install.

    `keep` where the host already holds exactly this kit, intact: the same paths, the same
    digests, the same version (the moment of a working-tree reading is not part of what a kit IS).
    `create` where nothing is pinned, `replace` otherwise."""
    seen = reading(manifest)
    _require_shippable(manifest, seen)
    if _same_root(manifest, ws, root):
        if not seen["intact"]:
            raise ReleaseError(
                f"{root}: the pinned kit is delivering ITSELF and no longer equals its own lock "
                f"({len(seen['drift'])} path(s): "
                + ", ".join(f"{p} ({s})" for s, p, _ in seen["drift"][:5])
                + "). Re-stamping it would launder the change into a new reading; deliver a "
                "release over it instead: `upgrade --root <host> --kit <release>`")
        return "keep"
    if not ws.exists(root.rstrip("/")):
        return "create"
    failures, pinned = verify(ws, root)
    if failures or pinned is None:
        return "replace"
    held = Workspace(ws.path(root)).read_json(pinned.raw_ships()["lock"])
    fresh = json.loads(lock_text(manifest, seen, "the moment does not decide sameness"))
    same = (held["kit_version"] == fresh["kit_version"]
            and held["files"] == fresh["files"])
    return "keep" if same else "replace"


def deliver(manifest: Manifest, ws: Workspace, root: str, moment: str) -> dict:
    """Replace `root` of the host WHOLE with this kit: every path its survey accounts for,
    verbatim, and the lock. The tree is the release; a stray file in it would make the pinned
    copy something no release describes, so the swap leaves nothing else behind."""
    seen = reading(manifest)
    _require_shippable(manifest, seen)
    if _same_root(manifest, ws, root):
        return {"released": seen["released"], "count": len(seen["rows"]),
                "lock": digest_of(Workspace(manifest.root).read_text(seen["lock_path"]))}
    source = Workspace(manifest.root)
    text = lock_text(manifest, seen, moment)
    files = {row["path"]: source.read_bytes(row["path"]) for row in seen["rows"]}
    files[seen["lock_path"]] = text.encode("utf-8")
    ws.write_tree(root, files)
    return {"released": seen["released"], "count": len(seen["rows"]), "lock": digest_of(text)}


def verify(ws: Workspace, root: str) -> tuple:
    """(failures, pinned manifest or None): the pinned tree against the lock it carries."""
    if not ws.exists(root.rstrip("/") + "/MANIFEST.json"):
        return [f"{root}: no pinned kit -- this host cannot run a verb by itself"], None
    try:
        pinned = Manifest(ws.path(root))
        tree = Workspace(ws.path(root))
        lock_path = pinned.raw_ships()["lock"]
        if not tree.exists(lock_path):
            return [f"{root}{lock_path}: the pinned kit carries no lock, so nothing states what "
                    f"it is"], pinned
        recorded = tree.read_json(lock_path)
        rows = lockfile.survey(pinned, tree)
    except (KitError, ValueError) as broken:
        return [f"{root}: the pinned kit cannot state what it is -- {broken}"], None
    return ([f"{root}{path}: {state} -- {why}"
             for state, path, why in lockfile.compare(recorded, rows)], pinned)


# -- a release source --------------------------------------------------------------------------
def fetch(source: str, into: Path) -> Path:
    """A release, read from a DECLARED revision into `into`, and returned only if it IS one.

    `git+<repo>@<rev>#subdirectory=<dir>` is read with `git archive` at exactly that revision --
    never a working tree, and with nothing the standard library and git cannot stand behind."""
    vcs = _VCS.match(source)
    if vcs is None:
        raise ReleaseError(f"release source {source!r}: not of the form "
                           f"git+<repo>@<rev>#subdirectory=<dir>")
    repo, rev, sub = vcs["repo"], vcs["rev"], (vcs["sub"] or ".").strip("/")
    archive = into / "release.tar"
    done = subprocess.run(["git", "-C", repo, "archive", "--format=tar", "-o", str(archive),
                           rev, sub], capture_output=True, text=True)
    if done.returncode != 0:
        raise ReleaseError(f"release source {source!r}: git archive refused -- "
                           f"{done.stderr.strip()}")
    with tarfile.open(archive) as tar:
        tar.extractall(into / "tree", filter="data")
    kit = (into / "tree" / sub).resolve()
    if not (kit / "MANIFEST.json").is_file():
        raise ReleaseError(f"release source {source!r}: no MANIFEST.json at {sub!r}")
    seen = reading(Manifest(kit))
    if not seen["released"]:
        raise ReleaseError(
            f"release source {source!r} is not a release: {len(seen['drift'])} path(s) differ "
            f"from its own lock -- " + ", ".join(f"{p} ({s})" for s, p, _ in seen["drift"][:5]))
    return kit


def fetched(source: str) -> tuple:
    """(kit, scratch): `fetch` into a fresh directory OUTSIDE every host. The caller removes
    `scratch` when the run ends, refused or not."""
    scratch = Path(tempfile.mkdtemp(prefix="kit-release-"))
    try:
        return fetch(source, scratch), scratch
    except BaseException:
        shutil.rmtree(scratch, ignore_errors=True)
        raise
